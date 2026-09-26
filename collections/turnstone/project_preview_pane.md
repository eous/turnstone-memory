---
name: project_preview_pane
description: "open_preview or the preview pane (PR #800/#801, 2026-07-07): descriptor rides tool-turn meta, blobs are salted kind='preview' attachments; settled design."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-20T17:02:08.334Z
---

# Preview pane — **PR #800** (2026-07-07; branch feat/preview-pane, 6 commits)

**What**: `open_preview(target, kind?, title?)` built-in + a `"preview"` PaneManager
type that opens BESIDE the conversation (`openPaneBeside`). Kinds: web (sandboxed
iframe) / pdf (browser viewer) / image / table (sortable, ragged-safe) / text /
markdown. Full build passed review + gates: 8703 tests green, mypy/ruff clean,
32-assertion headless-chrome harness.

## Durable architecture (don't relitigate)
- **Descriptor rides the TOOL turn's meta side channel** (`Turn.meta.extra["preview"]`,
  `_preview` dict key, `_tool_turn_meta` envelope — renamed from `_effect_status_meta`),
  ONE shape on live SSE `tool_result`, `conversations.meta`, and `/history`. NOT a
  system turn (no wire fence noise).
- **Blobs are content-addressed attachments with `kind="preview"`** — refcounted/GC'd
  via ref-lists, served by new GET `{ws}/attachments/{id}/preview` (read scope, same
  `_resolve_served_blob` gate), but (a) skipped by `_reconstruct_attachment_refs` so
  they can NEVER become wire content, and (b) excluded from the history bulk fetch
  at the query (`get_attachments(exclude_kinds=)`).
- **Serving CSP is per-MIME** (`preview_response_headers`): text/html → bare `sandbox`
  (renders, scriptless, opaque origin); application/pdf → NO CSP (Chromium's viewer
  refuses sandboxed contexts); else `default-src 'none'; sandbox`. Filenames now go
  through shared `latin1_safe_filename()` (web_helpers) — wire-safe, see
  [[reference_http_header_wire_safety]] (PR #803).
- **`core.web.fetch_with_ssrf_guard`** — manual redirect walk, `check_ssrf` per hop
  BEFORE requesting; adopted by open_preview AND web_fetch (web_fetch previously
  followed redirects into private space unchecked). URL userinfo stripped before
  descriptor/base-href. `<base href>` injected doctype-safely (quirks-mode trap).
- **Approval posture**: url targets `needs_approval=True` (like web_fetch);
  path/attachment run unprompted (like read_file). Not in task_agent, not coordinator.
- **Persist race** (descriptor SSE at exec, blob commit at batch fold): pane-side
  authFetch HEAD preflight + backoff auto-retry 0.9→7.2s + manual Retry card.
  Cancelled batches COMMIT an already-announced preview with the synthesized turn.
- **Frontend seams**: host adapter `onPreview(descriptor)` (onConsentDetected pattern)
  → `TS_SHELL.openPreview(descriptor, {base, wsId})`; auto-open gated on
  `isFocused` (background sessions must not commandeer the split); transcript chip
  (`buildPreviewChip`, credential-redacted) = reopen/replay affordance; pane meta
  persists last view for reload.
- Console `/node/{id}` `_proxy_get` now forwards CSP/nosniff/disposition/cache-control
  (was dropping ALL headers — review found previewed HTML would execute on the
  console origin if opened top-level).

## Second commit a7246567 (implementer-agent round, 2026-07-07; amended from torn 22bffccc)

**Race lesson**: the user resumed the implementer agent (via a direct message to it)
while the orchestrating session was running gates + committing — the agent's
post-completion edits (a false-alarm removal of the md vendor post-pass; it misread
mermaid's `isConnected` gate as detached-element breakage) half-landed in the commit.
Caught by the user + the restored guard test failing; fixed by restoring the call
attach-first and amending. Before committing agent work, check the agent is STOPPED
and diff the tree against its report immediately before `git add`.
- **Probe preflight**: pane preflights `GET ?probe=1` → 204 + real hardening headers
  (HEAD dragged the blob through the console proxy twice). Probe honors `assets`.
- **Legacy charsets**: table/text/markdown transcode at store time
  (`transcode_text`: declared charset → utf-8 → cp1252-replace); ladder ONLY for
  DECLARED text kinds (mime/ext/override) — bare-bytes fallback stays strict UTF-8,
  NUL always rejects. `.txt` deliberately NOT in the extension map.
- **Remote assets DEFAULT OFF**: web previews serve CSP `sandbox; default-src 'none';
  style-src 'unsafe-inline'; img-src data:; font-src data:` (renders, no network);
  per-pane sticky "Load remote images & styles" checkbox → `?assets=1` → bare
  `sandbox`. Not persisted in pane meta.
- **Markdown vendor parity**: `postRenderMarkdown(doc)` after setSafeHtml (hljs +
  lazy mermaid, same as conversation pane); `.preview-markdown` carries its own
  code-block/KaTeX chrome (conversation theme is `.msg.assistant`-scoped;
  hljs TOKEN colors are global).

## PR-review round (commits 5–6)
- **f8d5c96a** (bot feedback on the open PR): Copilot caught a REAL divergence —
  the URL lane's flat 10 MB pre-check made the 32 MiB pdf kind cap unreachable
  for URL targets (path lane honored it via stat pre-check). Fixed: pre-check
  removed, guard call passes `max_bytes=max(PREVIEW_SIZE_CAPS.values())`; per-kind
  caps after resolution are the single authority across all 3 lanes. + redundant
  test-local asyncio import dropped (code-quality bot).
- CI all-green incl. claude-review (no findings); threads replied + resolved
  (resolveReviewThread GraphQL). NOTE: replies via `gh api .../replies` post as
  the USER's account and show up as new "reviews" by them — don't mistake own
  replies for fresh human feedback.

## Third + fourth commits (2026-07-07)
- **7944596e**: `tools.allow_private_network` settings-registry opt-in (detail in
  [[feedback_runtime_toggles_settings_registry]]) — `_screen_tool_url` gate, approval
  card "(private network)" tag, guard's `allow_private_origin` only for private-NAMED
  origins; public→private redirects blocked regardless.
- **05c42826** (adversarial pre-push review fixes):
  - `fetch_with_ssrf_guard` STREAMS under `max_bytes` budget (default
    `FETCH_BYTE_CEILING` 32 MiB, decoded bytes) — was `client.get()` buffering
    unbounded bodies before any cap; redirect-hop bodies never read; realized
    response drops stale framing headers (content-encoding/length/transfer-encoding —
    a surviving content-encoding would make .text re-gunzip). Callers' product caps
    (web_fetch 10 MB truncate, preview per-kind) unchanged; ceiling is the backstop.
  - Preview blob ids SALTED: `sha256(b"preview:" + body)` — uploads use bare
    sha256(body) and save_attachment is INSERT-OR-IGNORE freezing `kind` at first
    insert, so byte-identical preview/upload shared a row (upload silently vanishes
    from model context via exclude_kinds, or preview turn materializes bytes).
  - Adversarial single-agent review verdict: security surfaces (opt-in gate, CSP,
    blob isolation, route auth, proxy pass-through, XSS lane) traced CLEAN.

## Pane/tab desync fix — **PR #801** (2026-07-07, branch worktree-fix-pane-tab-desync)
Live-testing found: dismissing the preview's split cell ran `closeCell()` (hide,
keep tab) → orphan tab, since preview's reopen is the transcript chip not the tab.
Fix = new `ephemeral` flag on `ShellPane` (only preview sets it): the cell chip
AND `unsplit()` route to `close()` (destroy pane+tab) for ephemeral panes, chip
glyph flips to destructive ✕/"Close pane" via `destroys = !multi || pane.ephemeral`.
`unsplit()` SPARES the focused survivor even if ephemeral ("keep the focused
pane"); all-conversation splits unchanged (`doomed` empty → prior `_exitLayout`).
- **DELIBERATELY LEFT** (not a bug — don't "fix" it): `activate()` swap-eviction
  (a 3rd pane swapped into the preview's focused cell) backgrounds the preview as
  a still-FUNCTIONAL tab (click swaps it back, content intact) — not the dead
  orphan the chip/unsplit paths produced. Covering it means reaping in the hot
  `activate()` path, which ALSO runs during preview open (`splitFocused`) → too
  risky for the payoff. Fable review (Opus-driven session) approved this call.

## Follow-ups (not built)
- Coordinator-pane parity (chip + open path in coordinator.js; tool is interactive-only).
- ✓ DONE (PR #803, 2026-07-07): get_content's non-latin-1 500 fixed AND the whole
  class closed — control bytes (h11/httptools-rejected) + backslash (quoted-pair
  break-out) — via shared `latin1_safe_filename()` (web_helpers), now used by
  get_content, preview_response_headers, and the workstream export handler.
  [[reference_http_header_wire_safety]]
- diff kind; charts-as-kind (image covers bash-rendered charts).
- CLI renders nothing for previews (confirmation line only) — [[project_cli_origins_forgotten_child]].

Local brief: `docs/design/preview-pane-brief.md` (worktree
`<worktree>`, gitignored).

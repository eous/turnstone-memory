---
name: project-copy-affordances
description: "Copy-to-clipboard (copy_actions.js, renderer raw-span masks, .msg-body tabindex): SHIPPED PR #944; whole-source and idle-only copy rulings are settled."
metadata: 
  node_type: memory
  type: project
  modified: 2026-08-02T13:02:05.073Z
---

Copy-to-clipboard for the chat UIs: SHIPPED — branch `feat/copy-affordances` → PR #944, one commit, 14 files (status is gh's job, [[feedback_no_pr_status_in_memories]]). Three affordances in shared `turnstone/shared_static/copy_actions.js` (side-effect-imported by renderer.js so all three surfaces get it): per-bubble copy button, pointer-only floating block button, Enter-on-focused-block keyboard copy. CHANGELOG entry deliberately deferred at ship time — check whether it happened before assuming.

**Owner rulings (settled — do not re-litigate):**
- WHOLE-SOURCE copy for message AND block copy (over-wide cells, non-rendered syntax included; copy-what-you-see was tried and reversed). Empty-resolved source is COPIED (empty write, transport verdict flashed) — never a manufactured ✗.
- IDLE-ONLY: every activation path gates on pane-level `closest('[data-busy="true"]')` INCLUDING the mouseover fast path; no per-bubble `.is-streaming` (deleted; a pin asserts absence). Busy refusals ANSWER (✗ + "Copy is available when the reply finishes"); no aria-disabled toggling (needs a busy-edge observer — ruled out-of-scope complexity).
- No toast: outcomes button-local (flash + title + one aria-live line via utils.js `makeAnnouncer`; coordinator's two announcers stay LOCAL — its degrade lane holds zero module dependencies).
- Floating button POINTER-ONLY (`tabindex="-1"`, permanent body mount); keyboard = plain single Enter on the focused block (chords/repeat ignored; Space must keep scrolling). Consequence: EVERY pointer-copyable block inside `.msg-body` must carry `tabindex="0"` — renderer fences/tables/mermaid, coordinator renderToolOutput pres (pinned per-exit), mcp_error raw-payload pre. New pre-in-msg-body surfaces inherit this obligation.
- Scroll dismissal follows CONTAINMENT (document or ancestor holding the block dismisses; pan inside the block or unrelated scroller keeps) — replaced the memoized-scroller allowlist, which failed at both extremes.
- FAB box constants mirror the CSS box, pinned by a test requiring width/height in exactly ONE `.block-copy-btn` rule (runtime rect read races stylesheet load — measured).

**Why:** rounds 1–6 plateaued at 3–6 correctness findings in the keyboard-owned-reveal state machine → simplification pivot ([[feedback_nonconverging_reviews_mean_simplify]]); rounds 7–9 converged 6→1 correctness with fix sites holding.

**Renderer facts (outlive the branch):**
- Table copy reads render-time `data-md-source`. Raw-twin arrays are pushed UNCONDITIONALLY (index-aligned by construction — the pipe-presence gate was reversed as fragile). Restore runs via the `rawSpanPasses` table in REVERSE mask order (IM, MB, IC): a later mask's twin swallows earlier masks' sentinels (math wrapping code). A NEW span mask needs a table row or copied tables silently lose that span.
- Footnote-definition bodies are collected POST-span-mask and MUST be `restoreRawSpans()`d before their recursive render (same recipe the details pass uses for fences); otherwise recursive-frame stashes silently drop cell content under a ✓. Details/blockquote recursion is safe (runs pre-span-mask).
- The attribute escape IS `escapeHtml` now (the four-replacement chain was reversed; the attribute-context lint exempts `escapeHtml(` and `safe[A-Z]` names). Tables restore BEFORE inline spans (display-math-in-cell fix).
- `_streamingRenderApply` stashes `el._copySource = buffer` unconditionally per applied frame (`_lastRenderedBuffer` stays unset on render-throw by design — copying it was a truncation trap).

**Verification instruments:** `tests/test_copy_actions_js.py` node harness (delegated-listener recording, geometry/selection stubs; gotchas: Node ≥21 `navigator` is a no-setter accessor — `Object.defineProperty` via `setNavigator`; stub Ranges need recursive `cloneRange`; stub focus gated on focusability). `scripts/livepass.py` copy harness `/copy/livepass.html`: `?x=1` → `COPY-READY-3-3` byte-exact verdicts, `?kbd=1` → `COPY-KBD-READY`, `&flash=1`/`&bare=1` visual; dark headless captures can omit FAB pixels on position-revisit (stale compositor tile — judge dark from `&bare=1`); ALWAYS curl a marker in the served module before judging verdicts — stale-server false-greens happened twice. Pane-seam stubs shared via `PANE_STUB_JS`. Shared demodulize/node_skip in `tests/_js_harness_helpers.py`.

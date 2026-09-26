---
name: project_paste_to_attachment
description: "#930 paste-to-attachment chip in composers: designed 2026-07-27, NOT implemented; local-only docs/design/paste-to-attachment-brief.md is the contract."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-27T21:36:56.413Z
---

Feature #930: text pasted above a threshold into any attachment-capable
composer becomes a `text/plain` attachment chip instead of inline text.
Designed 2026-07-27 (scout + planner passes, citations verified that day);
implementation deliberately deferred. THE BRIEF IS THE CONTRACT:
`docs/design/paste-to-attachment-brief.md` (local-only, never committed) —
surfaces map, decisions D1–D11, test plan T1–T7, risk register R1–R13.

Durable decisions (won't be re-derivable from git until it ships):

- New setting `interface.paste_attachment_chars` (int, default 2000 anchored
  to INTERJECTION_CAP_CHARS, 0=off, max 100000); threshold in CHARS, the
  512 KiB TEXT_DOC_SIZE_CAP ceiling in BYTES; oversize pastes fall through
  to inline (never preventDefault-then-413).
- No backend attachment changes — `classify_upload` already text-falls-back;
  filename is the constant `pasted-text.txt` because ids are content hashes
  (a counter suffix would contradict dedup).
- Console has NO permission-ungated `interface.*` read route → add
  authenticated `GET /api/admin/settings/interface` (response-side filter;
  the existing gated route untouched). Node keeps its existing route;
  threshold load is PAGE-BOOT-OWNED (3 boot sites pass their own URL), the
  shared composer reads a module var synchronously.
- Empty-message guards STAY — relaxing `/send`'s empty check poisons the
  trajectory (empty text part persists + replays; see brief R5). Instead:
  info message "Add a message to send with this attachment." Bundled fix:
  port the home launcher's orphan guard to the two node-UI create paths
  (server resolves attachments only inside `if initial_message`).
- Product calls: no per-paste un-convert in v1; console route yes (no
  half-surface knobs); orphan guard rides in the same PR.
- Shared logic: new ESM `shared_static/composer_paste_text.js` + window
  bridge (repo's documented pattern); Family B passes its EXISTING cap
  constants — no fourth mirrored cap table.

Related: [[project_attachments_subsystem]] (text kind, dedup, caps),
[[feedback_no_partial_unknown_effect_badges]] (the half-surface rejection),
[[feedback_runtime_toggles_settings_registry]].

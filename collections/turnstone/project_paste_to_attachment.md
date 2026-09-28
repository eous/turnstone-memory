---
name: project_paste_to_attachment
description: "#930 paste-to-attachment (built in PR #1012): pastes over 2000 code points become a pasted-text.txt attachment; fixed client threshold, not the designed setting; design decisions."
metadata: 
  node_type: memory
  type: project
  modified: 2026-09-28T19:29:12.000Z
---

Feature #930: text pasted above a threshold into any attachment-capable
composer becomes a `text/plain` attachment chip instead of inline text.
Designed 2026-07-27 (scout + planner passes, citations verified that day) in
`docs/design/paste-to-attachment-brief.md` (local-only, never committed) —
surfaces map, decisions D1–D11, test plan T1–T7, risk register R1–R13.
Built in PR #1012.

What the code does (verified 2026-09-28):

- `shared_static/composer_paste_text.js` (ESM plus a `window.TurnstonePasteText`
  bridge) decides for all five attachment-capable composers: text longer than
  `PASTE_ATTACHMENT_CHARS = 2000` Unicode code points becomes
  `pasted-text.txt`. Exactly 2000, or more than `TEXT_ATTACHMENT_MAX_BYTES`
  (512 KiB, mirroring `TEXT_DOC_SIZE_CAP`), stays inline. Clipboard files
  still win, and identical pastes dedupe.
- The threshold is a fixed client constant. PR #1012 left out the designed
  setting and its console settings/auth route to avoid a new permission
  surface.
- A companion message is still required. Attachment-bearing turns wait for
  an idle retry instead of joining the text-only interjection queue. Kinds
  that carry no files (the Scheduled launcher, #1093) keep a large paste
  inline via `isPastedTextFile`.
- Models see a long paste as an attachment named `pasted-text.txt`, so it
  inherits attachment framing; small models used to look for it on disk
  ([[project_attachment_framing_small_models]]).

Design decisions from the brief:

- Superseded by the fixed threshold: the setting
  `interface.paste_attachment_chars` (int, default 2000 anchored to
  INTERJECTION_CAP_CHARS, 0=off, max 100000); the authenticated
  `GET /api/admin/settings/interface` console route (response-side filter,
  because the console has no permission-ungated `interface.*` read route);
  and page-boot-owned threshold loading. Revisit them together if the
  threshold ever needs to be configurable.
- Threshold in CHARS, the 512 KiB TEXT_DOC_SIZE_CAP ceiling in BYTES;
  oversize pastes fall through to inline (never preventDefault-then-413).
- No backend attachment changes — `classify_upload` already text-falls-back;
  filename is the constant `pasted-text.txt` because ids are content hashes
  (a counter suffix would contradict dedup).
- Empty-message guards STAY — relaxing `/send`'s empty check poisons the
  trajectory (empty text part persists + replays; see brief R5). Instead:
  info message "Add a message to send with this attachment." Bundled fix:
  port the home launcher's orphan guard to the two node-UI create paths
  (server resolves attachments only inside `if initial_message`).
- Product calls: no per-paste un-convert in v1; orphan guard rides in the
  same PR.
- Shared logic: new ESM `shared_static/composer_paste_text.js` + window
  bridge (repo's documented pattern); Family B passes its EXISTING cap
  constants — no fourth mirrored cap table.

Related: [[project_attachments_subsystem]] (text kind, dedup, caps),
[[feedback_no_partial_unknown_effect_badges]] (the half-surface rejection),
[[feedback_runtime_toggles_settings_registry]].

---
name: project_1522_guard_json_documents
description: "Output guard on framework-encoded JSON (#1522, 2026-11-05/06): inspect results read by their strings via ControllerJSON; rulings, documented limits, follow-ups #1574/#1575."
metadata:
  type: project
---

Issue #1522: the output guard scanned `inspect_workstream`'s JSON encoding, so every child system
turn matched the role-injection marker `{"role":"system"` while escaped text inside messages was
missed. The maintainer's rulings (2026-11-05, design approved; 2026-11-06, the fix round's
direction "fix what we need to without expanding scope too much"):

- **Read the decoded strings of framework-encoded JSON.** `ControllerJSON(str)` in
  `core/output_guard.py` marks the result at the producer (`_exec_inspect_workstream`); the batch
  drain notes marked ids before admission rebuilds strings (as it does `_controller_ids`), and
  `evaluate_output(..., json_document=True)` evaluates every string value on its own, merges one
  assessment, and re-encodes only when a string changed. Keys are not read; one structural rule
  keeps parity with the text scan: a string of 8+ decoded characters under a secret-named key is
  redacted whole. A text that doesn't parse (the fold cut it) gets the plain-text scan.
- **An inspect with `include_provider_content` stays unmarked**: provider-native content holds keys
  a model wrote, and the walk doesn't read keys. A tool-name table instead of the mark was
  considered and declined; the mark is per result for this reason.
- **Documented limits, accepted rather than fixed**: a coordinator inspecting itself reads its
  stored inspect results as text (#1575); no rule runs across two strings (a cut-off private key
  ended in a later message, see #1555; line 2 of an env value whose line 1 was redacted); one time
  budget, strings read in order, the rest unread past the deadline (unreachable at measured sizes,
  about 8 ms for 36 KB against a 1 s floor); the secret-key floor counts decoded characters.
- **Credential detection skips a value that is exactly a `[REDACTED:...]` marker** (env line, JSON
  secret, connection string), detection only, so re-read redacted text stays quiet. In configurable
  mode the complex checks detect in the tool's own text and redact the registry-redacted text
  (`redact_text=`); both modes give the same flags, pinned by
  `test_both_modes_flag_and_redact_a_secret_alike`.
- Follow-ups: #1574 (`wait_for_workstream` adopting the mark), #1575 (inspect results the fold cuts,
  and the self-inspect case).

**Why:** later reviews may report the limits above, unread keys, or the mark-versus-name-table
choice as defects; they are rulings with tests and docs (docs/judge.md's output guard section).

**How to apply:** treat these as settled when reviewing or extending the guard; a change to one is a
design question for the maintainer. A new producer adopting the mark must have framework-written
keys only (or repeat model-written keys in a string the walk reads). Related:
[[project_output_guard_llm_merge]], [[project_three_facet_validation]],
[[feedback_redaction_regex_design]], [[project_wait_message_sizing]].

---
name: project_wait_message_sizing
description: "wait_for_workstream message sizing (2026-11-05 rulings): fit once at admission, fewest cut first, message_chars, wait_ended states only, no wait-specific constant."
metadata:
  node_type: memory
  type: project
  modified: 2026-11-05T11:28:05.101Z
---

On 2026-11-05 the maintainer ruled how `wait_for_workstream` sizes its children's messages. The
fixed per-message cut (raised 4 -> 6 -> 10 KiB over time) kept forcing a follow-up
`inspect_workstream` that put each long report's head in the context twice, and on small contexts
the generic fold cut the JSON mid-way and dropped children's entries.

- The executor returns the result whole. The batch drain's admission fits it to the exact limit
  the fold applies (`_ADMISSION_REFITS` -> `_refit_wait_result` -> `_fit_wait_result`), and the
  post-guard re-cut fits it again when redaction lengthens it. No estimate taken when the wait
  returns: a mid-turn compaction, the batch's earlier results and the 2,048-char floor all move
  the cap after that.
- Allocation is "fewest cut first": as many messages whole as fit, status texts first and then
  the smallest; the rest share what is left. Similar-size long reports therefore come back partly
  whole and partly as stubs rather than in even shares; accepted, because every cut message can
  cost a follow-up read. Even shares were rejected after 32 one-line answers just over the room
  all came back cut.
- A cut message carries `truncated: true` and `message_chars`, its whole length. A re-fit keeps
  an earlier fit's value, and a message already cut stays cut.
- `wait_ended` carries the children's states only; the tool result carries the text.
- No wait-specific size constant: what enters the context is bounded by the session's per-result
  ceiling, like any tool result. The escaping cost of non-ASCII text is #1565.

**Why:** a later review may report "partly whole, partly stubs" or "no wait constant" as defects.
These are rulings, pinned by tests in tests/test_coordinator_client.py and
tests/test_coordinator_tools.py.

**How to apply:** treat these as settled when reviewing or extending the wait; take a proposed
change to the maintainer as a design question, not a bug fix. Related:
[[feedback_context_shares_conservative]], [[project_eval_headless_loop_no_admission]].

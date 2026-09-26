---
name: re-check-stable-cut-dates-on-memory-entries-citing-before-x-y-stable-urgency
description: "Citing a memory's 'must land before vX.Y stable' urgency: run git tag -l vX.Y* first; if stable already cut the deadline is phantom; reframe, fix the memory."
metadata: 
  node_type: memory
  type: feedback
---

Memory entries that frame work as "must land before vX.Y stable" carry
an implicit assumption: the deadline holds. When the deadline fails
(stable cuts before the mandate is satisfied), the memory keeps the
"before stable" framing and reads as urgent for an unbounded time
afterwards. Future sessions citing the memory inherit a phantom urgency
that no longer applies — and worse, the actual urgency framing (e.g.,
"this is now backfill work / institutional-memory fragility") goes
unstated until someone notices.

**Why:** 2026-05-11 session on Turnstone — I argued PR 3 sequencing on the strength of
`project_unification_before_stable.md`'s "must land before v1.5.0 stable" framing. User corrected:
stable was already well under way, 1.5.13 was the most recent version, and this verb had been missed
completely and was only remembered by accident. The mandate had failed two months earlier; the
memory hadn't been updated; I'd inherited a phantom deadline as load-bearing. Three memory entries
(`project_unification_before_stable.md`, `project_command_verb_lift.md` (then named `_unlifted`),
`project_coord_completion_stack.md`) all carried the same stale framing. Updated all three
in-session to reflect the post-stable reality.

**How to apply:**

- Before invoking a "before vX.Y stable" framing as load-bearing in
  a recommendation, run `git tag -l "vX.Y*" | sort -V | tail`. If
  stable already cut, the urgency is something else (institutional-
  memory fragility, double-port tax, hygiene cost — frame
  accordingly).
- If you find a memory entry with stale deadline framing, update it
  in the same turn — don't just work around it. The next session
  will inherit the same trap otherwise.
- This is a specific instance of the general "memory is point-in-time"
  reminder, but it's worth flagging separately because schedule-based
  framings are particularly prone to silent staleness: the deadline
  passes invisibly, and there's no automatic prompt to revisit.
- Pattern recognition: any memory whose claim depends on "before X
  happens" should be re-verified against "did X happen?" — applies to
  release cuts, feature freezes, EOL deadlines, etc.

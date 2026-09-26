---
name: feedback_dont_delete_a_derivation_to_resolve_disagreement
description: "Two code paths derive the same fact and disagree: make both read one shared memoised derivation, never delete one (idle-nudge seam, wrong 4x)."
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-07-26T18:54:57.473Z
---

When a review finds that two places compute the same fact and can disagree,
the reflex fix is to delete one of them. That reflex was wrong four times in
a row on the coordinator idle-nudge seam, and each time the deleted path was
load-bearing for a case I had not enumerated.

**Why:** "these two disagree" is a symptom of two derivations, not of one
being redundant. The second derivation usually exists because it observes
something the first cannot — a different moment (enqueue vs drain), a
different failure mode, a different lifetime. Deleting it silently drops
that coverage, and the resulting hole is *harder* to find than the original
disagreement because nothing contradicts anything any more.

The concrete instances, all one seam:
- Two children snapshots per IDLE event disagreed → I shared one snapshot.
  Correct.
- Two drain-time children reads disagreed → I deleted the advice one. WRONG:
  it was the only thing observing a condition change during an entry's
  queued lifetime. The fix was one *memoised* read both predicates call, so
  they cannot disagree while both still run.
- Body / card / predicate each derived "what this nudge asserts" → I unified
  them into one asserted set. Correct.

**How to apply:** when two derivations disagree, ask what each one observes
that the other doesn't, then make them read one shared computation. Only
delete a derivation after enumerating the cases it uniquely covers and
confirming another path covers each. If a proposed deletion would make a
guard fire "only when X also happens", that is the `if X_fired` shape — it
is a narrower condition than the one being replaced, and it is a deletion
wearing a refactor's clothes.

Detector that caught this: an at-site comment in the same file explicitly
forbade the shape ("the yield is to the CONDITION, not to whether the
sibling actually fired — Do NOT fix this into `if idle_children_fired`"),
and my plan reimplemented exactly that shape one layer down, at the queue
instead of the gate. **Grep the file's own rulings before proposing a
simplification to it** — see [[feedback_symmetry_expansion_via_documentation]].

Related: [[project_idle_tasks_nudge]],
[[feedback_review_convergence_methodology]].

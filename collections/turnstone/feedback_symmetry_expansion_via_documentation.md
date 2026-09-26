---
name: feedback_symmetry_expansion_via_documentation
description: "Review flags a sibling surface your fix could cover: file an issue, never a deferral comment (RETRACTED); re-verify preconditions before expanding."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-07-29T07:37:18.364Z
---

**Retracted clause (the maintainer, 2026-07-29): "foreclose a next-round
sibling re-find with a deferral comment + tracking issue."** Stop
writing deferral comments. File the issue; annotate nothing.

The maintainer's objection: such comments must stop appearing in code, and the recent tendency
toward feature creep had been carried over into rules like this one, which are plainly wrong.

**Why the clause was wrong.** It was written as an anti-creep measure
and its actual effect is the opposite: it licenses editing files the
fix would otherwise never have opened, so the scope grows in the name
of discipline. Worse, the comment is addressed to a review bot rather
than a reader — it freezes one PR's scope decision, made on one day,
into a permanent artifact with no force that ever removes it. Issue
numbers churn, get closed, get superseded; the comment rots on
contact and the tooling re-finds the thing anyway. A tracking issue
already lives in a system built for status
([[feedback_no_pr_status_in_memories]] is the same principle: status
is gh's job, not the artifact's).

Rule of thumb: a comment earns its place by explaining the code a
reader is looking at. If it explains a *different* code path, or a
process state, or what was out of scope, it does not belong in the
file.

## What still holds

**Mechanism.** Review tooling and the sanity design pass are
**expansionary by construction** — completeness is their job, so they
reward "you left a sibling unfixed" and "an adjacent surface is also
affected." There is **no symmetric contracting force** in the tooling;
scope discipline is the operator's alone. Absent an explicit "should
this be in THIS PR?" gate at each expansion, scope ratchets out — and
every expansion enlarges the review surface, which manufactures the
next round's findings. That is the cascade.

**Why the `_run` propagation misfired.** The sanity pass said: new
primitive (`ensure_error_recorded`) on `_run_initial` → `_run` is a
sibling with the same defects → apply it there too. The symmetry was
**surface-level** (both `except Exception` send-worker arms, same
defects) but the **context differed**: `_run_initial` runs on a FRESH
session (the idempotency guard reflects only this turn); `_run` on a
REUSED one (the guard is stale across turns). The propagated
primitive's correctness precondition silently didn't hold → a swallow
regression. The heuristic matched on SHAPE, not on the INVARIANT.

**How to apply:**

1. Default to the MINIMAL scope for the STATED bug. Treat
   review-surfaced *adjacent surfaces* as deferred-by-default
   candidates, not automatic inclusions.
2. Defer by filing an issue and stopping there. Do not mark the
   boundary in the source.
3. Treat every symmetry/sibling expansion as a NEW fix that must
   re-verify its preconditions in the TARGET context (fresh-vs-reused
   session was the missed one). A symmetry sweep names candidates; it
   does not license uniform application.
4. Reviews and the sanity design pass are advisory; the scope call is
   the operator's. Running the check is not the same as owning the
   boundary.

Related: [[feedback_minimal_scope_first]] (the active counterweight to
expansionary tooling), [[feedback_pattern_propagation_sequencing]],
[[feedback_review_convergence_methodology]],
[[feedback_no_pr_status_in_memories]].

---
name: feedback_caution_proportional_to_deployment
description: "Working on an unmerged, gated branch (even security-sensitive code): match caution to how live the code is; big coherent chunks, heavy gates once at merge."
metadata: 
  node_type: memory
  type: feedback
---

Match caution to how LIVE the code is, not how sensitive it looks in the abstract. On an
unpushed/unmerged feature branch — gated behind a final `/review` + live-backend pass before
anything ships — intermediate states don't need to be independently shippable or maximally safe;
they only need to be correct at the merge gate. The user's metaphor (2026-06-06): **the branch is an
aircraft grounded in the hangar that cannot take off until every stage is done, so this is not an
engine change in mid-flight.** So even security-sensitive code (e.g. the human-in-the-loop approval
gate) on a grounded branch does NOT warrant per-step production-grade ceremony.

**Why:** subdividing work into ever-smaller chunks + per-chunk ceremony (a designer review + a
harness + an "OK to proceed?" check between each micro-slice) burns velocity for safety the
end-of-branch verification already provides. The user values velocity; per-step ceremony on a
grounded branch slows the whole arc without adding safety.

**How to apply:** execute in substantial coherent chunks — e.g. a full vocabulary
cutover across BOTH emitters + the deletions as ONE push, not coord/int/del slices each
with its own review + a proceed-check. Verify holistically at natural boundaries
(does the whole card render in both panes?), not per-micro-step. Reserve the heavy
gates — a designer pass on the finished result, `/review`, the live-backend pass — for
the merge gate and run them once. Don't stop to ask "keep going?" mid-arc when the work
is already queued; just finish it. Refines [[feedback_minimal_scope_first]]; nuances
[[feedback_pre_commit_gates]] (its "/review incrementally" means at real boundaries,
not per-micro-step). Context: [[project_frontend_lshell_renovation]].

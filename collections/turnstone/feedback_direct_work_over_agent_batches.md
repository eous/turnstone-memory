---
name: feedback-direct-work-over-agent-batches
description: "When applying review fix batches or design-sensitive changes: do them in-session with Read+Edit, never via delegated fix agents (the maintainer, #955, 2026-08-04)."
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-08-04T09:59:07.714Z
---

During the #955 review cycle the maintainer stopped two delegated fix-batch agents and ruled that
the work happens directly instead of through launched agents, because subtle errors kept propagating
into their output.

**Why:** Delegated batch agents repeatedly introduced defects the next review
round had to catch — round 3's agent duplicated the mismatch-warn loop verbatim
and mis-keyed an over-length check; round 4's batch shipped my mis-specified
purge. A spec written for an agent transmits my misunderstanding at full
fidelity; working directly, the code contradicts me while I read it (the
re-key session surfaced the freshness-gate/overwrite windfall only because I
was reading the mint internals myself).

**How to apply:** For review fix batches and design-sensitive changes in this
repo, do the work in-session with Read+Edit. Delegation stays fine for
read-only fan-out (searches, review finder/verify workflows) and mechanical
sweeps with no design content. Related: [[feedback_fresh_briefing_vs_agent]],
[[feedback_nonconverging_reviews_mean_simplify]].

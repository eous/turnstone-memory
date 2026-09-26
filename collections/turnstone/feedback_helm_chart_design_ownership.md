---
name: feedback-helm-chart-design-ownership
description: "Chart-shaped design questions in deploy/helm/turnstone: Claude owns the call (delegated 2026-08-02); decide and implement, PR still states the trade-off."
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-08-02T21:37:40.780Z
---

The maintainer handed over design ownership of the Helm chart (`deploy/helm/turnstone/`) on
2026-08-02, leaving the design to the agent, who owns the chart from then on.

**Why:** they were asked to choose between competing designs for the bundled-PostgreSQL password
(read the subchart Secret vs. require an explicit password vs. change the migrate-hook lifecycle)
and declined to arbitrate. The implementing agent owns these design calls within the agreed scope.

**How to apply:** for chart-shaped questions, decide and implement rather than
presenting options and waiting. Still open a PR and still state the trade-off you
took and what you left alone — the delegation is about who chooses, not about
skipping review or narrowing scope silently. Escalate only what genuinely leaves
the chart: anything touching application behaviour, release process, or a
published interface.

Note this is chart-specific and does not generalise. Elsewhere the standing rules
still hold — [[feedback_push_back]], [[feedback_minimal_scope_first]], and design
calls on the application itself remain their.

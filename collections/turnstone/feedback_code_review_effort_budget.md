---
name: feedback_code_review_effort_budget
description: "Choosing a /code-review effort level: default to high, not max; reserve max for net-new high-stakes code."
metadata: 
  node_type: memory
  type: feedback
---

Default `/code-review` (and Workflow-backed reviews) to **`high`**, not `max`.

**Why:** a `max` multi-agent review spawns ~24–29 subagents; `high` gives broad finder/verify
coverage with a much lighter run.

**How to apply:** default to `high` for reviews, especially verification / re-review passes on
focused diffs. Reserve `max` for net-new, high-stakes, or concurrency-heavy code where the extra
breadth clearly earns its place — and give a heads-up / reason when choosing it. Lighter first line
of defense: my own manual review + running the gates (ruff/mypy/pytest), then a `high` workflow as
the adversarial backstop. (The health-loop `max` reviews DID earn their place — 13 real concurrency
bugs — so this is "default lower," not "never max.") Relates to [[project_design_constraints]] and
[[feedback_large_review_orchestration]].

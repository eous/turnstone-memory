---
name: project_plan_agent_removed
description: "Tempted to add a planner agent: plan_agent REMOVED (2026-07-01), a planning skill on task_agent or native planning beat it; ship planning as a skill."
metadata: 
  node_type: memory
  type: project
---

Turnstone removed the dedicated `plan_agent` (confirmed 2026-07-01: gone from `core/` and `api/`; only `tests/test_prompts.py` + `tests/test_session.py` still reference the name, as naming-constraint fixtures). Reason (user-reported eval outcome): a **planning skill handed to a task_agent**, or simply the model's **own native planning**, outperformed a dedicated planning agent. `task_agent` is now the sole `_run_agent` sub-harness.

**Why:** a dedicated planner is another plant call at the same provenance rank — plan-writes are middle-rank (HYPOTHESIS.md two-rank control) whether written by a dedicated agent or the model inline — so the component bought zero certificate strength; its only possible payoff was capability, and evals said that was negative. Shaping the plant through trusted lowered content (a skill) beat adding architecture — same lesson as [[project_eval_optimization]] (tool descriptions > prompts).

**How to apply:** don't reintroduce a dedicated planner component; deliver planning discipline as a skill, or rely on the model. Orthogonal and still open: CaMeL-style plan *pinning* (fix the plan from the trusted query before any untrusted read — top-derived rank, provable-security mode for specific flows) is a π/γ discipline, not a planner agent, and plan_agent's removal does not foreclose it. Related: [[project_task_agent_modernization]], [[project_harness_hypothesis_doc]], [[project_tool_naming_constraints]].

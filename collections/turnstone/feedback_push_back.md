---
name: push_back
description: "When the maintainer proposes a plan, priority order or design (issue text included): challenge it and voice better sequences or alternatives directly instead of silently executing."
type: feedback
---

Be pushy — challenge priorities, suggest alternatives, push back on design decisions when there's a better path. Don't just execute silently.

**Why:** The user values collaborative thinking over pure execution. Challenging assumptions leads to better outcomes (e.g., the compaction nudge simplification, BM25 vs embeddings discussion, user scope plumbing).

**How to apply:** When the user proposes a plan or priority order, consider whether there's a better sequence, a missing dependency, or an unnecessary step. Voice it directly rather than just agreeing and executing.

**Issue text is a proposal too (#1325, 2026-10-09).** The issue said "the state stays `attention`"
with a fail-safe argument, and I treated the line as a ruling: the judge-evaluating marker became a
derived `judge_evaluating` flag carried through ~30 sites (schemas, both SDKs, collector, adapter,
both servers, three display-state helpers), reviewed twice. Asked "why not a new state?", the
maintainer chose `evaluation`; production code halved (~460 to ~225 lines) and the flag's
consistency rules disappeared. **How to apply:** at scoping, when a new fact must reach every
surface the workstream state already reaches, put "make it a state (or an existing field's value)"
next to the issue's design as an explicit option, with the issue's argument for its own shape,
before building either. Related: [[feedback_surface_scope_questions_at_design]],
[[feedback_nonconverging_reviews_mean_simplify]].

---
name: feedback_surface_scope_questions_at_design
description: "Writing an issue's out-of-scope list or offering \"fix in this PR\": raise inherited adjacent problems as an explicit decision at design time, with the blast radius checked first."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-01T07:26:44.709Z
---

When a design step finds a pre-existing problem the change will inherit, put it to the maintainer as
a decision before implementing ("this row inherits X; in scope or not?"), not only as a line in the
issue's out-of-scope list. Before offering "fix in this PR" for anything in shared code, grep the
callers and state the real blast radius in the option itself.

**Why:** in the #1245 model-row run, the effort knob's `none` mapping was noted as out of scope at
design time but never raised. A review round brought it back mid-loop, the "fix in this PR" option
said only "touches Astra", and the shared resolver turned out to reach the Gemini, xAI and local
lanes. Three review rounds of redesign followed before the work was split out (#1248). Planned for
at the design step, the same work could have fit; arriving mid-loop, it did not.

**How to apply:** at the design step, list inherited adjacent problems for the maintainer with a
one-line blast radius each. When a review finding reopens one, map the shared function's callers
before presenting options, and give the split-out option first when the radius crosses providers or
lanes. Related: [[feedback_minimal_scope_first]], [[feedback_nonconverging_reviews_mean_simplify]],
[[feedback_designs_that_need_no_memory]].

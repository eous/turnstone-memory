---
name: feedback_measure_before_accepting_a_finding
description: "Before accepting or fixing a review finding reasoned from code reading: probe the real path first, and ask what the probe shows with no bug present."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-07-27T05:35:00.115Z
---

The maintainer, on a review report: ask whether the finder reached its result by reading the code or
by measuring; if it did not measure, measure before accepting the finding, then pass the plan to the
dataflow-mapper.

**Why:** review finders reason from source. A plausible-looking
derivation can be right, wrong, or right-for-the-wrong-path, and all
three read identically in a report. Measuring converts an argument into
a fact before it becomes a code change — and the fix plan that follows
is only as good as the diagnosis under it.

**How to apply.** For every falsifiable claim, write the smallest probe
that exercises the real path (a pytest reusing the module's own
fixtures, a direct call, a scripted client) and record the observed
value in the commit message. Then hand the plan to `dataflow-mapper`
before implementing ([[feedback_dont_delete_a_derivation_to_resolve_disagreement]]
is why: the graph catches fixes that introduce new defects).

**The trap that caught me:** my first probe for a cooldown-burning
finding exhausted the cap, which makes the cheap peek return EARLY —
so the code under test never ran and the probe "refuted" a real bug.
The finding's actual claim was about a LOST RACE past that peek;
forcing the authoritative gate to refuse confirmed it. **Ask what the
probe would show if the bug did not exist** — if the answer is "the
same thing", the probe is measuring the wrong path.

Measuring also paid the other way: it confirmed six of seven findings
verbatim, including exact failure strings, which made the fixes
uncontroversial and the commit messages self-evidencing.

Related: [[feedback_review_convergence_methodology]],
[[reference_code_review_workflow_recovery]],
[[feedback_harness_scripted_events_not_verification]].

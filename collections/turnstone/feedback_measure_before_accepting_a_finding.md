---
name: feedback_measure_before_accepting_a_finding
description: "Review finding reasoned from reading: probe the real path first (what would it show with no bug?). A fix the reviewer wrote is a draft: test it before applying."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-11-10T03:00:00.000Z
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

**A fix the reviewer wrote is a draft too (2026-11-09).** In the end-to-end review of
HYPOTHESIS.md ([[project_harness_hypothesis_doc]]) the reviewer supplied replacement wording with
its findings. Applied and sent back for closure, that wording was where most of the remaining
faults were, by the reviewer's own closure report; a later pass rejected a phrase from one of its
original fixes ("this description", which had nothing to refer to at that point in the text). A
finding can be right while its fix overreaches, or collides with a passage the reviewer was not
reading when it wrote the fix.

How to apply: test supplied text against every passage it must agree with before it goes in — for
prose, the lines it cites and the lines that cite it; for code, the probe above. Apply it verbatim
only if it passes. Where you depart from it, list each departure with its reason and ask the
reviewer to test the applied result, not the intent. Check every quoted phrase against the file.
A fault in supplied text is an ordinary fix round; patches that keep needing new machinery are
[[feedback_nonconverging_reviews_mean_simplify]].

Related: [[feedback_review_convergence_methodology]],
[[reference_code_review_workflow_recovery]],
[[feedback_harness_scripted_events_not_verification]].

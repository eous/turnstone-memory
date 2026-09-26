---
name: feedback_docs_are_not_review_immunity
description: "Review finding refuted only by a docstring or 'deliberate' comment: still report it as a design question; only a pinning test or cited ruling settles it."
metadata:
  node_type: memory
  type: feedback
---

Documentation may explain INTENT; it must never SETTLE correctness in a review.
A verifier refutation has to cite an enforcing artifact (a test, a type, a
guard) or independently derive the behavior's safety. "The docstring says this
is deliberate" converts a bug hypothesis into an OPEN DESIGN QUESTION — which
must still be surfaced, not dropped.

**Why:** The maintainer, 2026-08-03: treating documentation as a defense against code review lets
dangerous or bad patterns spread through the code base. Immediately validated on the #950 branch:
two review instruments refuted a hypothesis against a docstring that called the profile checks
"row-validity/always-run" — re-examination showed that placement violated the branch's OWN hostage
principle and diverged from the MCP sibling it claimed to mirror (whose profile check is inside the
posture guard). The doc was wrong, confident, and quoted verbatim as refutation evidence by the
verifier.

The propagation mechanism is the sharp part: a justifying comment TRAVELS with
copy-paste into contexts where the justification is false, carrying its review
immunity along. A pinning test does not travel silently — copied code arrives
naked and gets re-reviewed.

**How to apply:**
- Every "by design" a reviewer could trip over gets a pinning test whose NAME
  states the design (`test_base_url_edit_skips_posture_on_unchanged_pair`).
  No test → it is not settled design, it is an assertion.
- "Deliberate/deliberately/by design" in comments must cite the ruling — an
  issue number, a measurement, a named decision. Unsourced deliberateness is
  an immunity token; treat it as a smell in review, not a shield.
- When MY verify pass meets a doc-based refutation: downgrade to
  design-question and report it in the findings anyway (its own lane), and
  check the doc's claim against the enforcing artifacts before accepting.
- Defects never get comments at all — they get issues
  ([[feedback_symmetry_expansion_via_documentation]]). This rule covers the
  complement: DESIGNS get comment + cited ruling + pinning test.
- Kin: [[feedback_measure_before_accepting_a_finding]] (probe the real path;
  a doc is not a probe), [[feedback_harness_scripted_events_not_verification]].

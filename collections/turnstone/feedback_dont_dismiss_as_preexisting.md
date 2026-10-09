---
name: feedback_dont_dismiss_as_preexisting
description: "Bug found in code you are already editing: verify it is truly pre-existing, then fix it in place if bounded; the label is not a reason to skip."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-05T19:40:18.399Z
---

When a bug surfaces in code you are already editing, do not classify it as
"pre-existing" and move on. Fix it. The label is not a reason to skip — it is
usually just an observation about when the bug was introduced.

**Why:** The maintainer, 2026-08-02: be careful about casually waving things away as pre-existing;
it is often easier to fix a bug while it is in front of you than to let it come back and bite later,
or worse, to extend the broken pattern. Two costs: the bug returns later at full re-investigation
price (nobody has the context loaded any more), and worse, new code written next to it inherits the
broken shape — the structural pull described in [[feedback_pattern_propagation_sequencing]], which
no comment or issue can neutralize.

**How to apply:**

- Before calling anything pre-existing, *verify* that it is
  ([[feedback_measure_before_accepting_a_finding]]). In the session that
  produced this rule I dismissed "the disabled audience select still submits
  its stored value, so `obo_audience` can no longer be cleared" as pre-existing
  behaviour. It was not pre-existing at all — the old free-text input could be
  emptied; I had introduced the regression in that same diff. The label was
  doing the work of an excuse.
- "Pre-existing" is a fact about *origin*, never a verdict about *whether to
  fix*. Decide fix-vs-defer on cost and blast radius, and say which one you
  used.
- Default to fixing in place when the code is already open and the fix is
  bounded. Escalate to the user only when the fix is genuinely large or would
  change behaviour beyond the current task — and then say so out loud rather
  than burying it.
- If it truly must wait, file the issue; do not annotate the code
  ([[feedback_symmetry_expansion_via_documentation]]).
- This does NOT license scope sprawl. [[feedback_minimal_scope_first]] governs
  how much *feature* to build; it is not a licence to decline a bug fix in code
  you are touching. Keep the two separate.
- **Wire-correctness bugs are P0 (the maintainer, 2026-10-05).** If a provider
  request can be rejected or malformed, fix it in the current branch even when it
  predates the branch; do not file it for later or ask whether to include it. This
  came up when review found that the Anthropic converter drops `tool_search_tool_result`,
  which the API requires to be passed back
  ([[project_anthropic_deferred_server_tool_calls]]).

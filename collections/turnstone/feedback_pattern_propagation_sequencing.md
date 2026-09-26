---
name: pattern-propagation-trumps-memory-holing-for-sequencing
description: "Hygiene PR vs feature PR on the same surface: land hygiene first; new code copies its neighbours and no doc fixes that, whereas forgetting is doc-fixable."
metadata: 
  node_type: memory
  type: feedback
---

When advising sequencing between a hygiene-style PR (establishes / cleans
up a pattern) and a feature PR (adds new code that will sit near the
existing pattern), prefer hygiene first if the new code would otherwise
land into a dirty environment. Reason: new code follows neighbor code
through reviewer + author cognition, and that cognitive pull can't be
neutralized by documentation. If the dominant local pattern is dirty
when the feature PR lands, the feature's new code reads as the exception
rather than the new norm, regardless of how many docs assert it's the
new norm.

**Why:** 2026-05-11 session on Turnstone — sequencing PR 3 (`/command` verb lift) vs the interactive
frontend DOM-cleanup PR. I argued PR 3 first on memory-holing grounds (the verb lift was missed once
already and could be missed again). User pushed back empirically: larger changes tend to follow
established patterns, so doing the cleanup now sets a better (or at least more modern) pattern for
them to match. The right call was hygiene first because:

1. Memory-holing risk can be mitigated by heavy documentation (scope
   docs + multiple memory entries). I had already done that in the
   same session — the verb lift had a paper trail.
2. Pattern propagation is structural — even with extensive docs telling
   reviewers "the new module is the new norm, ignore the surrounding
   dirty pattern," human reviewers still pattern-match against the
   bulk. One clean module in a dirty codebase reads as the exception.

So the trade was: a mitigable risk (memory-holing, handled by docs) vs
an unmitigable one (pattern propagation, no doc fixes it). Hygiene
first.

**How to apply:**

- When sequencing a hygiene PR ahead of a feature PR, check: does the
  feature PR's new code land into the same surface as the hygiene PR
  touches? If yes, structural reasons favor hygiene first.
- When tempted to recommend "ship the load-bearing thing first," check
  whether you're anchoring on schedule urgency. If the load-bearing
  feature has no hard deadline, the pattern-propagation argument
  often dominates.
- Make biases explicit when re-opening a decision. List the steelman
  for both sides honestly. Users often spot the missing weight when
  prompted — see also [[feedback_push_back]].
- See also [[feedback_sdk_boundary_testing]] (its "spike before planning"
  rule) for the pattern that uncovered the structural details (e.g., one
  frontend is essentially pre-2015 JavaScript, the other is ES6+ —
  measurable from the same grep that surfaced the `innerHTML` asymmetry).

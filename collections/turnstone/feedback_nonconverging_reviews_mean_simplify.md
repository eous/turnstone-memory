---
name: feedback-nonconverging-reviews-mean-simplify
description: "Review rounds keep finding bugs in the prior fixes (guards fighting guards): stop grinding and propose deleting the mechanism, capability included."
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-08-02T09:42:21.078Z
---

When the confirmed-correctness finding count refuses to fall across unprimed review rounds AND the findings concentrate in interactions among the previous rounds' fixes (guards fighting guards), that is a design-complexity signal, not a review-diligence problem. Stop the fix-review grind, name the mechanism that keeps generating the bugs, and propose deleting it — including the capability it powered.

**Why:** On the copy-affordances branch (2026-08), six rounds held at 3–6 confirmed correctness findings each; rounds 4–6 were almost entirely bugs in rounds 3–5's fixes, clustered in one stateful mechanism (a singleton floating button with module pins, focus semantics, and geometry policy over a per-frame-rebuilt DOM). When I presented the trend and a simplification that deleted ~150 lines of the densest surface, the maintainer chose it immediately — and then simplified FURTHER than I proposed (asking whether disallowing copy until streaming completes would simplify things), trading a designer-endorsed capability (copy earlier replies during busy) for the deletion of an entire gate mechanism.

**How to apply:**
- Track confirmed-correctness counts per round and WHERE they land; "new bugs are in old fixes" is the trigger, not the absolute count.
- When triggered, present: the trend data, the mechanism at fault, a concrete deletion-first proposal with what capability it costs, and the grind-another-round alternative. Recommend the simplification.
- Expect the maintainer to bid the simplification UP (their instinct: user-expectation-simple beats clever — see also the toast removal and whole-source rulings this same arc). Offer the more aggressive cut when one exists.
- Large reworks of this kind go to a delegated agent with a complete brief (rulings, findings mapped fix-or-dissolve, house rules, gates); the session owner stays free for review orchestration.

Related: [[feedback_review_convergence_methodology]] (the 2+ clean rounds rule this pattern overrides), [[feedback_minimal_scope_first]], [[feedback_push_back]].

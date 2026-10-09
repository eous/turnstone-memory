---
name: feedback_relay_every_review_option
description: "Asking the maintainer to decide a review finding: wait for the sanity pass's option list, or relay every option any stage named; asking early hid a cheaper fix in #1291."
metadata:
  type: feedback
---

In #1291's round 5 I asked the maintainer to decide the hosted-search residual (document it, or
clean it after a paid live probe) before the sanity report arrived. Its third option, one
sentence in the trust declaration with no probe and about 15-20 tokens, reached the maintainer
only when a side agent flagged it, and the maintainer then chose it.

**Why:** late in a long review loop, a decision-maker picks from what is offered; an option left
out is a decision made for them.

**How to apply:** put review decisions to the maintainer after the sanity pass (or include every
option any finder, verifier or sanity stage listed), recommendation first, each with its cost.
Related: [[feedback_ask_before_declining_capability]], [[feedback_surface_scope_questions_at_design]].

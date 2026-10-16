---
name: feedback_relay_every_review_option
description: "Asking the maintainer to decide a review finding: wait for the sanity option list or relay every option any stage named, each with its cost, including what a tightening option breaks."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-12T20:44:12.286Z
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

**The cost includes what a tightening breaks (2026-10-12, #1373).** Twice an option that refused
or narrowed something went to the maintainer without its cost: doctor's backend probe sending a
placeholder key (key-protected servers then look broken) and refusing a `${VAR}` key that expands
to nothing (a local-server entry that worked with the placeholder stops loading). A side agent and
a later verify pass surfaced them, and the second had to be asked again. When an option refuses,
blocks or swaps a credential, say in its text which working setups it drops and what it makes look
broken, before the maintainer picks.

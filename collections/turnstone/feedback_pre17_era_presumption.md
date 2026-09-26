---
name: feedback-pre17-era-presumption
description: "Unexplained behavior blamed before the 1.7 cycle (~mid-June 2026), no ruling in code/memory/issues: presume accident; fix or simplify, name the delta."
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-08-05T19:28:28.107Z
---

Ruled by the maintainer 2026-08-05 while opening the #832 main-loop fold (the oldest code in
turnstone touched so far): **if a behavior has no good discoverable reason, nothing in memory
explains it, and its blame predates the 1.7 era, presume it was written before the project knew what
it was doing — simplify, fix, delete, or improve it rather than preserving it.** Initially ruled for
~March-2026 commits; the maintainer bumped the cutoff to 1.7 age the same day, because that is when
HYPOTHESIS.md began to solidify and the project had enough experience to make judgement calls
instead of improvising its way through. Concretely: v1.7.0 was cut 2026-07-05, so blame dates before
the 1.7 development cycle (≈ before mid-June 2026) are presumption-of-accident territory; the 1.7
cycle and everything after keeps the normal preserve-then-ask posture.

**Why:** the pre-1.7 core predates HYPOTHESIS.md, the Turn-IR redesign, and the
review-convergence disciplines; behaviors from that era are as likely accident as
intent. Preserving them byte-for-byte (and writing parity pins for them) launders
accidents into contracts — the inverse of [[feedback_docs_are_not_review_immunity]]
("deliberate" needs a cited ruling; absent one, age is evidence of accident, not of
wisdom).

**How to apply:** on hitting an oddity: (1) reason in code/docstring? keep or follow
it; (2) reason in memory/issues/design docs? same; (3) neither → `git log -L` /
blame the lines; if blame predates the 1.7 era and the message records no rationale,
improve it. Improvements are still NAMED — they go in the campaign's behavior-delta
table / PR text as deliberate changes, never slipped in silently. Parity harnesses
pin the improved behavior, not the fossil. Does not override explicit rulings (a
ruled behavior of any age stays).

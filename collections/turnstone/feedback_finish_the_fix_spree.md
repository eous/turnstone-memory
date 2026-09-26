---
name: feedback-finish-the-fix-spree
description: "Bug-fix branch (the maintainer 2026-09-05, mid-#1099): one review round after the fix, no follow-up issues from the branch, ship; supersedes 2-clean-rounds."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-09-25T18:30:00.320Z
---

The maintainer, 2026-09-05, mid-#1099: this was the longest multi-session bug-fix spree the project
had had; each session fixed one to three bugs and then filed one to three follow-ups, so at that
rate the work would never finish.

**Why:** the review pipeline plus the file-every-finding rule turns each fix
into a generator of new issues; the backlog grows faster than it shrinks, and
the sessions never reach "done".  On #1099 three review rounds and one
follow-up (#1102) preceded the PR.

**How to apply:**
- One review round per fix, run after the fix is complete.  Fix confirmed
  correctness bugs *in the diff*; inline or drop quality items; open the PR.
  A further round only when a fix changed behaviour.  This supersedes
  [[feedback_review_convergence_methodology]] (2+ consecutive clean rounds)
  for bug-fix branches.
- The ship gate is still a round with ZERO correctness findings (the maintainer 2026-09-19, #1188:
  ship only after a clean review round with no correctness findings).  When the one round returns
  correctness findings and their fixes change behaviour (a latch moved, a guard deleted, bounds
  added), the fix round gets its own unprimed round before the push; a round that returns only
  quality items ships.  Run the full pipeline EVERY round, before any fix: finders, verify, dedupe,
  sanity.  No exceptions for findings that look self-evident or for late rounds (the maintainer had
  to say it twice on 2026-09-19 that sanity is the minimum, the second time when I started editing
  straight from round-4 finder reports).  Verify and sanity also refute: on #1188 they refuted four
  finder claims across four rounds and caught a wrong remedy (a ratio band that broke pinned
  calibrations) before it was written.  The `/code-review high` skill itself is 8 inline angles +
  dedup with NO verify stage: spawn code-review-verify → code-review-dedupe → code-review-sanity on
  its JSON output (2026-09-25 OAuth round 3: verify refuted 5 of 8 using measurements handed over as
  raw facts; sanity confirmed the 3 declines).
- An issue the maintainer asks for is filed regardless of the no-follow-ups rule
  (2026-09-19: #1197, delete the in-process fork copy, their call after I
  called it a "legacy path" and they asked why we keep one).
- Do not file follow-up issues from a fix branch.  A pre-existing finding
  gets one line in the PR body.  File an issue only for something that would
  block a release.  This narrows [[feedback_symmetry_expansion_via_documentation]]
  ("no deferral comments, file the issue") to the release-blocking case.
- Decide design questions the issue leaves open in one pass with the
  simplest bounded option ([[feedback_minimal_scope_first]]); do not iterate
  designs through review rounds.

---
name: feedback_review_brief_rulings_vs_own_calls
description: "Briefing review agents (finders, verifiers, designer): list only maintainer-confirmed decisions as rulings; mark your own calls as open to challenge, or reviewers skip them."
metadata:
  type: feedback
---

A review brief that calls decisions "maintainer rulings, treat as intended" makes reviewers skip
them. Only decisions the maintainer actually confirmed belong in that list. Claude's own calls go
in a separate list marked open to challenge: defaults it stated without asking, the variant it chose
of a relayed suggestion, mechanisms it added in response to side notes, process choices.

**Why:** #997 /review (2026-10-13): the brief listed the existing-user colour backfill, setup's
`username` change, the API-token write rule and the upload limits as maintainer rulings. A side
agent caught it, the maintainer relayed the note, and the six running finders had to be corrected
mid-run.

**How to apply:** before sending any review brief, check each "ruling" against the maintainer's own
words in the scope note or memory; anything Claude stated as a default, or decided after the last
confirmation, is a call. Give verify and sanity the same split. Related:
[[feedback_large_review_orchestration]], [[feedback_docs_are_not_review_immunity]].

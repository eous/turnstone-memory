---
name: feedback_review_brief_rulings_vs_own_calls
description: "Briefing review agents (finders, verifiers, designer): list only maintainer-confirmed decisions as rulings; mark your own calls as open to challenge, or reviewers skip them."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-19T08:26:18.028Z
---

A review brief that calls decisions "maintainer rulings, treat as intended" makes reviewers skip
them. Only decisions the maintainer actually confirmed belong in that list. Claude's own calls go
in a separate list marked open to challenge: defaults it stated without asking, the variant it chose
of a relayed suggestion, mechanisms it added in response to side notes, process choices.

**Why:** #997 /review (2026-10-13): the brief listed the existing-user colour backfill, setup's
`username` change, the API-token write rule and the upload limits as maintainer rulings. A side
agent caught it, the maintainer relayed the note, and the six running finders had to be corrected
mid-run.

Again in #1389 round 2 (2026-10-19): the maintainer approved fixing a pre-existing finding in
passing and called it a nit. The brief turned that into a ruling that the class is a nit and that
the author's fix design was settled. A verifier then downgraded a confirmed finding citing that
supposed ruling, and Claude repeated it to the maintainer, who corrected it.

**How to apply:** before sending any review brief, check each "ruling" against the maintainer's own
words in the scope note or memory; anything Claude stated as a default, or decided after the last
confirmation, is a call. Give verify and sanity the same split. An approval to fix a finding is a
ruling on scope only, not on its severity (the finder's label) or on the fix's design: quote the
maintainer's words verbatim in the rulings block, never a paraphrase. A verifier's
severity_override that cites a ruling gets checked against those words before it is relayed. Related:
[[feedback_large_review_orchestration]], [[feedback_docs_are_not_review_immunity]].

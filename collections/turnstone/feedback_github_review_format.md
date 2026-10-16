---
name: feedback_github_review_format
description: "GitHub PR reviews and replies: decision line, findings table, per-finding what/impact/fix, collapsible low-severity, path-forward checklist; never a narrative."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-09-26T01:13:54.437Z
---

The maintainer, 2026-09-25, on the #1201 reply: the reply read as a story instead of an actionable
review; keep it structured like the code-review result, adapted into a natural GitHub markdown
format.

**Why:** a narrative buries the actionable parts; maintainers and contributors scan a review for
findings, locations and next steps.

**How to apply:** lead with a bold one-line decision; then a findings table (#, severity, type,
location as a permalink to the PR head commit, one-line finding); short **What happens / Impact /
Evidence / Fix direction** entries for High and Medium; Low severity inside `<details>`; a `- [ ]`
path-forward checklist; caveats in a Scope section at the end. Use reference-style permalinks
(`blob/<head sha>/path#Lnn`) so the raw markdown stays readable; check each line at the head SHA and
render through `gh api markdown` (mode gfm, repo context) before posting. Related:
[[feedback_artifact_cleanliness]], [[feedback_finish_the_fix_spree]].

**Severity mapping.** The review pipeline rates findings critical/major/minor/nit; in the GitHub
table, critical becomes High, major becomes Medium, and minor and nit become Low.

**Keep it short (maintainer, 2026-10-12, #1351).** The first draft of the #1351 review was 5,500
characters; the maintainer said it was a bit long, and the posted version was 2,500. One or two
sentences per What happens / Impact / Evidence; a code snippet only for the fix; permalinks only
where the text points at code; Scope in one short paragraph; optional Low items that are one line
can live in the table alone. A review that asks for a change is posted as request-changes.

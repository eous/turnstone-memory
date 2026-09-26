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

---
name: feedback_contributor_commits_keep_authorship
description: "Merging a contributor PR: merge commit, not squash, so their commit stays; re-author an agent-authored commit to their GitHub noreply address first (maintainer, 2026-11-08, #1589)."
metadata:
  type: feedback
---

The maintainer, 2026-11-08 on #1589: merge a contributor's PR without squashing, so the
contributor keeps their own commit in main's history.

**Why:** a squash replaces the contributor's commit with one the merger shapes. A merge commit keeps
their work as theirs. A commit made in a hosted coding-agent session arrives authored as
`Claude <noreply@anthropic.com>`, with `Co-Authored-By` and session trailers. Kept as is, history
would credit that account instead of the contributor.

**How to apply:**
- Before merging, re-author such a commit to the contributor with
  `<id>+<login>@users.noreply.github.com` (the id comes from `gh api users/<login>`).
  - Keep its tree, parent and author date.
  - Drop the tool trailers.
  - Recreate the commits above it from their recorded trees, so nothing is replayed.
  - Since the contributor's commit gets a new hash anyway, rebase it onto current main at the same
    time instead of keeping a "Merge branch 'main'" commit on the branch. On #1589 a merge of main
    made early (for a CHANGELOG section main had also edited) was kept through the rewrite and
    landed on main; it wasn't needed once the commit was being rewritten. This lesson is mine,
    not a maintainer ruling.
  - Force-push with a lease on the old head.
  - Say so in the PR comment. Once the commit is authored by the contributor, the CLA check can go
    green.
- Merge with `gh pr merge --merge --match-head-commit <sha>`. When the maintainer says so, don't
  wait for CI, since waiting raises the chance of racing another merge.
- When pushing to a contributor's fork through maintainer edits, the git-lfs pre-push hook fails
  with "You must have push access to verify locks", because the fork's LFS lock API doesn't honor
  maintainer edits. If the PR changes no LFS files, push once with
  `git -c lfs.locksverify=false push ...`.
- Related: [[feedback_git_workflow]].

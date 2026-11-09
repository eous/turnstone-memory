---
name: reference_contributor_fork_push
description: "Pushing maintainer commits to a contributor's fork PR: the git-lfs pre-push lock check fails on the fork; skip it per push when no LFS file moves; CI then waits for approval."
metadata:
  type: reference
---

Measured on 2026-11-08 while pushing a merge from main and review corrections to a first-time
contributor's PR (#1572), whose author allowed edits by maintainers (`maintainerCanModify: true`).

- Work in a detached worktree at the PR head and push by URL:
  `git push git@github.com:<owner>/turnstone.git HEAD:refs/heads/<branch>`. Check the branch head
  with `git ls-remote` first, so a push the contributor made in between can't be lost; a plain
  (non-force) push then fast-forwards.
- The repository's git-lfs `pre-push` hook verifies LFS locks against the fork and fails with
  "Authentication required: You must have push access to verify locks". Edit access to a PR
  branch doesn't cover the fork's LFS lock API.
- Only `*.png` is LFS-tracked. When `git diff --name-only <old>..HEAD | xargs git check-attr
  filter --` shows no `lfs`, skip the check for that one push with
  `git -c lfs.https://github.com/<owner>/turnstone.git/info/lfs.locksverify=false push ...`.
  Don't persist the setting, and don't reach for `--no-verify`, which skips LFS uploads too.
- The CI run for that push came back `action_required`: it waited for a maintainer to approve it
  in the Actions tab, although a maintainer made the push.
- The repository's squash merge builds its default message from every commit message
  (`squash_merge_commit_message: COMMIT_MESSAGES`). When maintainer commits change what a
  contributor's commit says, rewrite the message in the merge box.

**Why:** on #1572 the first push failed on the lock check, and the default squash message would
have recorded behavior the final code no longer has.

**How to apply:** use these steps when finishing a contributor's PR on their branch. The push and
the PR comment still need the maintainer's go ([[feedback_git_workflow]]).

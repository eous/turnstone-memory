---
name: feedback_autosquash_fold_verification
description: Folding review fixes into earlier commits (fixup!/amend! + autosquash): verify each commit, not just the final tree; guard conflict staging; pause with --exec
metadata:
  type: feedback
---
Review fixes written at the branch tip conflict when `git rebase --autosquash` moves them back,
and a resolution can put a fix in the wrong commit or leave a commit that only works with a later
one. On the #1408 branch (2026-10-29) a fold used a constant only the next commit defined; the
final tree matched while that commit could not stand alone.

**Why:** a zero final-tree diff proves only the end state. The maintainer keeps one commit per
fix (a relayed side-agent note: check each commit on its own) so each stands alone and
cherry-picks cleanly.

**How to apply:** after every autosquash:
- `git diff <pre-rebase tip> HEAD` must be empty.
- Each commit's net added/removed lines per file must equal its old commit plus its folds;
  explain any deliberate move (an import a fold now needs earlier).
- Run lint, mypy and the wide suites at every commit in detached worktrees, with PYTHONPATH set
  to the worktree and an import check.

While rebasing:
- Resolve diff3 hunks as ours + (theirs − base), in final-tree order.
- Never chain `git add` / `rebase --continue` after a resolver with `;`. Use a guard that refuses
  files still holding markers (one marker-laden commit forced an abort).
- To edit a commit the rebase won't stop at, pass `--exec` with a hook that fails once, not `-i`.

Related: [[feedback_git_workflow]], [[feedback_mutation_control_hygiene]].

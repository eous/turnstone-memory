---
name: Worktree safety — checkout before delete
description: "Moving a branch out of a worktree or briefing a worktree agent: checkout in the main repo before worktree remove; state and verify the base commit."
type: feedback
modified: 2026-07-28T23:49:45.419Z
---
When the user wants to move a branch from a worktree back to the main working directory (or
equivalent), the safe sequence is:

1. In the worktree: `git checkout --detach` — releases the branch so another worktree can claim it.
2. In the main repo: `git checkout <branch>` — verify the commit is present.
3. Only then: `git worktree remove <path>` — safe because the branch pointer is preserved in the main repo's HEAD.

**Why:** `git worktree remove` of a worktree that is the only place with the branch checked out is safe in principle (the branch ref persists), but if there's any accidental state (uncommitted changes, wrong branch detached, etc.) the user loses it. Doing the checkout first proves the branch is in the main repo before any destructive step, and the user gets to verify commit + file contents before deletion.

**How to apply:** Any time a branch lives only in a secondary worktree and the user wants it back in the main repo. Never go straight to `git worktree remove` without confirming the branch has been checked out elsewhere.

**Agent-worktree base gotcha (2026-07-28):** the Agent tool's
`isolation: "worktree"` can deliver the worktree at the WRONG BASE
COMMIT — observed once delivering main's tip instead of the feature
branch HEAD the session was on (the bad ref matched a branch an
accidental mid-session checkout had created earlier, so stale state is
the suspected mechanism). The agent caught it only because its brief
named the expected commit and the cited symbols were absent. Two
rules: (1) every worktree-agent brief STATES the expected base commit;
(2) the agent's first action is `git log -1` and a hard reset of its
scratch branch to the stated base if it disagrees — and the harvest
step re-verifies the base before applying any diff.

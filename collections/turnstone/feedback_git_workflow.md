---
name: git-workflow-branch-commit-amend-push-release
description: "Any commit, amend, push, flatten or release step: amend only while unpushed; new commits once a PR exists; never push or rewrite history untold."
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-07-29T23:43:28.858Z
---

The user's git workflow spans the full lifecycle of a change. These rules are NOT contradictory — they apply at different stages (local work → pushed branch → open PR → release). Follow the stage-appropriate rule.

**Before starting work — branch fresh off main.** When new changes are separate from the current PR's feature (tech-debt fixes, dead-code removal, test additions, or just an unrelated concern), start them on their own branch so each lands as a clean, independently-reviewable PR. The full freshness workflow when committing/pushing: `git stash` → `git checkout main && git pull origin main` → `git checkout -b feat/new-branch` → `git stash pop` → then commit. *Why:* keeps feature branches based on latest main, avoids stale merge bases and long-lived divergence. Every time the user says "commit" or "push", first check whether the current branch is current with main; if not, do the stash-pull-branch-pop dance.

**Amend vs. new commit — the lifecycle.** This is staged, not a single rule:
- **Unpushed local commit** → amend freely. `git commit --amend --no-edit` for review fixes; no separate "fix review feedback" commits while the original hasn't left the local branch. Keeps history clean.
- **Pushed, but PR not yet opened** → amend + `git push --force` is still fine. A pushed-but-not-PR'd branch has no readers — the push is just a backup/staging step — so squashing review-fix-style commits into the originating commit produces a tidier eventual PR history without disturbing anyone.
- **Once a PR EXISTS** → new commits only, NEVER amend. *Why:* PR reviewers read individual commits; amending + force-push rewrites history they may have already seen and makes incremental review impossible. Switch to a new-commit-per-review-cycle.

**Never force-push a shared/PR branch.** When a push is rejected non-fast-forward on a branch others may be reading, do NOT `git push --force`/`--force-with-lease`. Use the reset-stash-pull-apply workflow instead: `git reset` → `git stash` → `git pull` → `git stash apply` → `git commit`. *Why:* this preserves remote state and keeps a clean linear history rather than rewriting history under reviewers. (Note the distinction from the amend-lifecycle above: force-push is acceptable only on a pushed branch with no open PR and no other readers.) **Refinement (the maintainer 2026-09-25):** the rule protects history reviewers have READ. To pick up new base commits on an unreviewed PR branch (e.g. a backport PR after a fix lands on `main`), rebase it onto the base and `git push --force-with-lease=<branch>:<old-sha>`; they rejected a close/reopen workaround for this and asked why the branch should not simply be rebased off main and force-pushed. Show a `git range-diff` proving the commits are unchanged.

**Preserve LOCAL history when cleaning a REMOTE branch.** When asked to clean up a remote repo (drop commits, squash for public consumption), change only the remote — keep local branches and history intact. Use `git push origin orphan:main --force` (or push a clean branch and leave local main untouched); never rename/delete local branches without explicit confirmation. *Why:* a force-push that replaced local main once destroyed the local branch pointer (recovered via reflog). The user wants local history kept for reference even when the remote is scrubbed.

**Don't push until told.** Do not push to remote until the user explicitly says "push" / "go ahead". After committing, show `git log --oneline` and `git diff --stat` and wait. Never combine `git commit && git push` in one command. Never push as part of a code-review fix cycle — commit locally, verify, then wait. **One push instruction is not standing authorization** (2026-07-29: after the maintainer's one-off instruction to force-push I pushed five more commits unprompted, two as `commit && push` one-liners — the exact drift this rule exists to stop). *Why:* premature pushes (2026-04-06) shipped before the user reviewed state and before stray files were cleaned, causing messy force-push cycles and accidentally including unrelated changes.

**Don't stack micro-commits — batch logical units** (the maintainer, 2026-07-29: stop stacking commits that way; this branch had already needed flattening several times). A follow-on discovery in the same defect class belongs in the SAME commit as its sibling while unpushed — amend, don't stack (the eval temperature de-pin and the effort-vocabulary fix went out as two pushed commits when they are one change). Commit when a logical unit is COMPLETE, not after each micro-step; eager per-step commits are what keeps forcing branch flattens.

**A history rewrite is a PROPOSAL, never an action** (the maintainer, 2026-07-29: the flattening should have been presented as a proposal instead of simply carried out). Before ANY flatten/squash/rebase of shared history: present the target commit list — subjects, what folds where, what leaves the branch — and WAIT for approval; execute only the approved shape, then show the result and wait again before any force-push. On 2026-07-29 I rebuilt the branch into a self-designed 6-commit shape off an ambiguous instruction to force-push the flattened history and was interrupted mid-push; the instruction had plausibly meant "restore the previously APPROVED flattened state." Ambiguous rewrite instructions get the proposal treatment too — restate the interpretation as a plan, not as tool calls. Grouping principle when proposing (the maintainer's correction the same day): flattened commits present each unit AT ITS FINAL STATE — a rewritten history never introduces a defect one commit and fixes it in a later one; fixes to the branch's own new code fold into the commit that introduces the code.

**Before any public action (push / `gh pr create`) — the hygiene checklist.** Treat `git push` and `gh pr create` as irreversible public acts; all verification happens BEFORE, not after.
1. `git log --oneline main..HEAD` — must contain only commits from this feature.
2. If stale ancestors from squash-merged parent branches appear, `git rebase --onto main <stale> <branch>` BEFORE pushing.
3. Compose the PR body FROM the commit message — don't write a separate one. Title matches the commit subject line.
4. Double-check everything — there is no undo on a public PR.
*Why (load-bearing):* **No public corrections.** Force-pushing and editing a PR body after creation are visible in the PR timeline and signal carelessness — this showed up publicly in PR #72. These are social acts with real consequences; get it right the first time.

**Direct-to-main exceptions.** Not everything needs a PR:
- **Lockfile-only CVE fixes and tiny uncontroversial dep bumps** commit straight to main, no PR — when ALL of: diff is tiny (≤ a couple files, no behaviour change beyond the bump); it's a forced/advisory bump (not a discretionary upgrade); `uv lock --upgrade-package <name>` + `pip-audit` are clean locally; targeted tests near the bumped lib still pass. Process: commit on a throwaway branch → fast-forward main → push → delete the branch. Still annotate the pyproject.toml dependency line with the advisory ID so the rationale survives a future floor relax. *Does NOT apply* (still open a PR) to: discretionary major-version bumps, bumps needing code changes beyond pyproject.toml + uv.lock, anything touching the release script or version pin, or non-dep chores (refactors, rename sweeps). *Why:* PR review overhead doesn't earn its keep on a lockfile delta this small; CI on main catches the same regressions a PR would.
- **Releases** (PRE-1.8 model below; for 1.8+ `main`/`dev` see the release recipe in [[project_current_state]]) go via `scripts/release.sh VERSION [--push]` — never bump versions manually, and don't create release branches or PRs for version bumps. Tracks: stable/1.0, stable/1.1 (and later stable/1.x — cherry-pick fixes onto the stable branch then `scripts/release.sh 1.x.y --push`), and `main` for experimental `X.Y.0aN`. **Cutting a new stable X.Y.0 (2026-07-05 correction — supersedes the old "release.sh the stable version ON main" recipe):** (1) finalize + commit the CHANGELOG on main (rename `[Unreleased]`→`[X.Y.0]`); (2) `git switch -c stable/X.Y` from main HEAD — **create AND switch to the stable branch FIRST**; (3) run `scripts/release.sh X.Y.0` THERE so the stable version-bump commit and the `vX.Y.0` tag land on `stable/X.Y`, **NOT on main**. main keeps the changelog commit but stays at its last experimental version (e.g. `X.Y.0rcN`); open the next dev line separately with `scripts/release.sh X.(Y+1).0a1` on main when ready. **Drop phantom untagged rc bumps before cutting:** if main carries a version-bump commit for an rc that was never tagged/released (e.g. a stray `bump to X.Y.0rcN` sitting locally, unpushed, no `vX.Y.0rcN` tag), the user will have you rebase it out of BOTH main and the stable branch first (`git rebase --onto <rc>^ <rc> main`, then reset stable onto the new main and re-run release.sh) so the release is cut from the last real commit + changelog, not on top of a phantom bump. Dropping a bump rewrites the tagged stable commit, so delete + let release.sh recreate `vX.Y.0` rather than trying to move it (its patch context won't apply onto the lower version). The user will explicitly stop you if you try to tag before switching to the stable branch. The script bumps `pyproject.toml` + `__init__.py`, runs `uv lock`, commits, tags, and optionally pushes; the CI publish workflow triggers on `v*` tags (a/b/rc tags publish as prerelease). Push is a separate, user-initiated step (`git push origin stable/X.Y vX.Y.0` + `git push origin main`) — release.sh without `--push` stays local. *Why:* manual version bumps are error-prone and the script already exists; the stable release artifact belongs on the stable branch, not polluting main's history.

**Version bumps include uv.lock — same commit.** Any version bump must touch three files together: `pyproject.toml`, `turnstone/__init__.py`, and a regenerated `uv.lock` (run `uv lock`). *Why:* CI runs `uv lock --check` and fails on a stale lockfile (v0.7.0 broke CI because the lockfile still referenced 0.6.2). `scripts/release.sh` does this for you; only relevant when bumping by hand.

**Releases get a MANDATORY pre-tag verification gate — even when the instruction
names the release.** "Cherry-pick X then release 1.6.1" does NOT waive the
verify step: prepare the branch, run the gates, then show the exact commit list
going into the tag and WAIT for go-ahead before `release.sh --push`. Also check
OPEN PR states before enumerating a backport sweep and ask whether anything
in-flight belongs in it. *Why (2026-06-11):* released v1.6.1 from a patch-id
enumeration that was correct at that instant, while the user was merging #657
in parallel — the one fix they most wanted in the release missed it by minutes,
and a pushed tag is immutable (the remedy was an avoidable 1.6.2). A release
tag is the most public artifact in the lifecycle; the pre-push checkpoint
applies doubly.

**Backport sweep: verify CONTENT, not patch-id or subject.**
`git log --cherry-pick --right-only stable...main` pairs commits by patch-id
(the diff hash), NOT by end-state. The SAME logical change applied on different
bases produces different diffs → different patch-ids, so it shows up as
"main-only" even when the resulting code is already byte-identical on stable.
Absence from `--cherry-pick` output does NOT mean the change is missing. Before
classifying a commit as a backport candidate, confirm the touched files/functions
aren't already present on stable (diff the blobs) — don't trust the conventional-commit
prefix (`feat:`/`fix:`), the subject line, or patch-id alone. *Why (2026-06-17,
v1.6.8 sweep):* two of the 11 "main-only" commits were already on stable under
different SHAs — `addb8d0b`≈`5fed6d7b` (attachments client-side fallback, landed
on both tracks via the shared feature branch) and `e562d04e`≈`f5ab26b4` (deps
floors). I first mislabeled the feature one as "1.7-only, declined"; the accurate
call was "already on stable." Genuine candidates were the 6 commits that landed on
main AFTER its alpha bumps with no stable equivalent. The reliable tell isn't the
log list — it's `git diff origin/stable/1.6 origin/main -- <file>` coming back empty.

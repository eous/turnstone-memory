---
name: feedback_ultraplan_behavior
description: "Using ultraplan or writing an ExitPlanMode plan: ultraplan executes remotely in a sandbox seeing only repo + plan file; write plans fully self-contained."
metadata: 
  node_type: memory
  type: feedback
---

`◇ ultraplan` (Claude Code CLI, first used 2026-07-02): user-triggered like ultrareview — I
cannot launch it. It takes the current plan-mode plan to a Claude Code on the web session;
browser approval is an EXECUTION trigger, not a refine-and-return step. The user expected
refine→verify→hand back for local implementation and was surprised it executed remotely.

The cloud environment had ONLY the repo checkout + the plan file: no user CLAUDE.md, no
project memories, no local-only briefs (docs/design/*), no house rules. It also could not
open a PR from its sandbox — it delivered `~/personas-handoff.tar.gz` (a DOUBLE-gzipped
tar: gzip of a .tar.gz — `zcat` once, then `tar -tzf`) containing git format-patches + a
git bundle (bundle prerequisite was a generous old boundary, so the branch base was really
current main — check `git merge-base`, not the bundle prerequisite line).

**Why:** plan-approval gates can hand work to context-poor executors; whatever isn't in the
plan file does not exist for them.

**How to apply:** write ExitPlanMode plan files fully self-contained (locked decisions,
verified seams w/ line numbers, guard-test list, prompt copy). When ultraplan output comes
back, land it via `git bundle verify` + fetch to a holding ref, scan authorship/trailers
for [[feedback_artifact_cleanliness]], fast-forward a local branch, then run the full
local review with memories/brief context ([[feedback_large_review_orchestration]]). Expect
the user to want this reviewed EXTRA carefully.

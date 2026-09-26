---
name: feedback_freeze_tree_during_review
description: "While any review finder/agent is in flight against the tree: no edits, commits, rebases or test runs until the last one returns; check branch after."
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-08-06T10:58:57.564Z
---

While a /code-review workflow (or any review agents) is in flight against the working tree, make NO edits to reviewed files — not even "trivial" test-assertion fixes. The maintainer enforced this mid-#817 when I started fixing two stale log-name assertions during round 5.

**Why:** verifier agents re-read the cited file:line evidence during the run; concurrent edits shift line numbers and content under them, producing findings against code that no longer exists (or missing the code that now does), and making the round's verdicts unreliable.

**How to apply:** queue diagnosed fixes (note them explicitly) and apply them in a batch after the review completes; if a fix can't wait, stop the review first and re-run it after. Memory files, scratchpad drafts, and gitignored local docs are fine to edit — they're outside `git diff HEAD`, which is the review's scope.

**The freeze covers TEST RUNS too, and the failure looks like an unrelated flake (2026-08-06).** A comment-only edit to `session.py` during a running full suite made `tests/test_coordinator_tools.py::test_prepare_tasks_imports_honest_truncate_once` fail with a bare `assert 0 == 1`. Mechanism: that test does `inspect.getsource(ChatSession._prepare_tasks)`, which resolves the code object's line numbers against the file **on disk at call time** — removing three lines upstream shifted every offset below it, so `getsource` returned a misaligned slice with the expected import outside it. It passed in isolation and pointed at a module I had not touched, so it reads exactly like an order-dependent flake. **Any `inspect.getsource` / `linecache` test in the suite turns a mid-run edit into a false failure somewhere else entirely.** Re-run on a frozen tree before diagnosing.

**The freeze cuts BOTH ways — review agents can mutate the repo (incident, 2026-07-13).** During the #827 pre-push xhigh, the sweep agent ran `git checkout main` in its final seconds (~52 min into a 62-min run) and never switched back: the two verifiers that started after it verified against MAIN, and the session's file-state notes showed phantom "reverts." The branch itself was intact — `git reflog` gave the exact switch timestamp, `git checkout <branch>` restored everything. **After every review workflow completes: check `git branch --show-current` (and `git status`) BEFORE trusting late-stage verdicts or diagnosing "reverted" files; cross-reference the switch time against each verifier's startedAt/lastProgressAt to find contaminated verdicts, and re-verify those by hand.** Durable fix to consider: worktree isolation for review-workflow agents.

**The freeze is per FINDER, not per round — and it includes rebases (the maintainer, 2026-09-05,
#1091).** Three of four round-5 finders had reported; I applied their fixes, made fixup commits and
ran `git rebase --autosquash` while the fourth (bug) finder was still computing `git diff
main..HEAD` from the working tree. It noticed ("HEAD moved from 2760a062 to fe6fe084") and its run
had to be killed and restarted on the frozen tree. The maintainer asked why the tree was being
modified while a finder was still active. Rule: while ANY review agent is in flight, no edits, no
commits, no rebases — batch everything until the last one returns; a finder that reads the repo
itself is even more exposed than one handed a diff file, because a rebase changes HEAD under it.

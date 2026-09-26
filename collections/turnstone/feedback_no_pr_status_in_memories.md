---
name: feedback_no_pr_status_in_memories
description: "Writing a memory that mentions a PR or issue: never record lifecycle status (OPEN/MERGED); numbers are pointers, decisions are facts; check gh at read time."
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-07-20T16:47:44.403Z
---

Do NOT record PR/issue lifecycle status (OPEN / review-converged / MERGED-at-commit / awaiting-merge) in durable memories, and do not spend turns updating such statuses. The maintainer's ruling (2026-07-20): status tracking has always been distracting noise and has never been a signal that led to meaningful action.

**Why:** status is one `gh pr view` / `git log` away, with git as the authority; a memory copy is a hand-maintained mirror that decays. Live failure the day of the ruling: memory said PR #879 was OPEN after it had merged — a session ran a stale-branch overlap analysis and reported "no collision risk" against a PR that no longer existed, then burned another turn on OPEN→MERGED maintenance edits. The harness memory guidance already excludes this ("don't save what the repo already records — git history"); the drift came from writing end-of-session state-of-play into project memories.

**How to apply:**
- PR/issue NUMBERS stay — they're provenance pointers ("the parity rulings live in #879"), which is `reference`-type value.
- Decisions, rationale, rulings, gotchas, follow-ups stay — not derivable from git.
- A blocker WITH an owner ("blocked on the maintainer's sec-1 adjudication") is allowed while it encodes a non-derivable decision point; a bare status roster ("OPEN PRs: #x #y") is not.
- When a memory mentions a PR and its state matters to the task, check `gh`/git at read time instead of trusting or updating the memory.
- Existing memories still carry status idioms (including [[project_current_state]] and MEMORY.md's Current State block); don't imitate them, and strip status incidentally when editing a file for other reasons. Related staleness rule: [[feedback_stable_deadline_memory_staleness]].

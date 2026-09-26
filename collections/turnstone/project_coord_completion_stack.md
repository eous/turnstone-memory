---
name: project_coord_completion_stack
description: "Coord completion stack #505/#506/#598 ALL SHIPPED; stacking dependent PRs: branch each off its parent PR, expect brief LOC estimates to run 3-4x low."
metadata: 
  type: project
---

**COMPLETE — all three PRs shipped.** Briefed in `docs/design/coord-completion-stack.md`
(local-only). Each PR retired a specific duplication/polling gap that existed only
because the right primitive wasn't built yet, surfaced during the PR #503 scoping
conversation:
1. **PR #505** — Postgres `notify`/`listen` API + console `NotifyDispatcher` +
   services-trigger migration (053); replaced the cluster collector's 60s services
   poll.
2. **PR #506** — `ChildEventBus` (per-ws_id `threading.Event`); replaced
   `wait_for_workstream`'s 0.5s Postgres poll with event-driven wakeup.
3. **PR #598** — `/command` (rewind/retry) lifted to path-keyed shared session
   handlers (2026-05-29); superseded/detailed in [[project_command_verb_lift]].

Original framing was "must land before v1.5.0 stable" — that slipped (stable cut
without it); the stack finished as backfill work on the 1.5.x track instead. Nothing
outstanding.

**Durable lessons (the reason to keep this file):**
- **Stack dependent PRs as branches, not off `main`**: PR 2 branched from PR 1's
  branch, PR 3 from PR 2's — each absorbs review-driven changes without forcing
  downstream PRs to redo work or wait for upstream merge. Re-target to `main` once
  the parent merges; rebase downstream if the parent branch shifts during review.
- **Brief LOC estimates ran ~3-4× low** across this whole stack because
  review-driven additions land in-PR (PR 1 briefed ~1607 LOC came in at that
  multiple over its original estimate once per-channel coalescing, reconnect
  handling, and config plumbing were added during review). Plan calendar time
  accordingly — a "~1 day" brief estimate means one focused session *including*
  review fixes, not one session of clean coding.
- **`/review` → fix-then-recheck → push**, per PR, catches drift that a
  first-pass review misses (docstring drift, test-ordering bugs, doc
  inconsistency) — worth the second pass even when every commit was already
  reviewed once.
- Each brief's "pre-implementation spike" section (re-verify citations against
  current HEAD before writing code) should target the actual branch-cut point, not
  a frozen brief-authoring commit — briefs go stale within the same stack as
  upstream PRs land.

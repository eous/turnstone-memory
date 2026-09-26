---
name: project_856_command_slot_bypass
description: "Issue #856 (slash commands 409 busy on worker slot): DEFERRED, branch dropped; off-slot dispatch failed review; revive only via REST endpoints."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-20T16:55:41.299Z
---

**Issue #856** (filed by eous, follow-up from compaction-visibility review round 5):
`/v1/api/command` runs every slash command on the worker slot and answers 409
busy while a turn/command holds it — over-broad for commands that don't touch
conversation state (e.g. `/name` refused during a minutes-long manual `/compact`).

**Audit (posted on the issue 2026-07-17):** classified handle_command's commands.
Phase-1 safe set = `/name /history /workstreams /help /creative /raw /debug`.
The audit's hazard model was INCOMPLETE — see [[feedback_worker_slot_mutual_exclusion_scope]].

**Phase 1 attempt — FAILED review (2026-07-17), branch `feat/856-safe-command-slot-bypass` (1 commit
2c8f6206 over main).** Ran the safe set off-slot via `asyncio.to_thread` without claiming the slot.
A high review (16 agents) returned **5 CONFIRMED + 1 PLAUSIBLE correctness findings, all valid**
(reasoned through each — not #840-style false positives):
1. to_thread default-executor exhaustion (wedged thread not reclaimed past the 25s backstop).
2. `/raw`/`/debug` flip show_reasoning/debug the turn loop READS mid-stream → render corruption.
3. off-slot on_info/on_error/on_rename splices into the live token stream (hits even read-only cmds).
4. no abandoned-worker guard → late completion injects into a successor turn.
5. thread-spawn failure → 200 ok (slot path answers loud 503).
6. (PLAUSIBLE) off-slot /name vs on-slot /resume ws_id race — NOT degenerate: two
   participants in a SHARED workstream can't serialize it; alias lands on wrong ws.
Plus 2 cleanup (bypass branch duplicates the slot envelope; allowlist is a decoupled
2nd source of truth vs handle_command's if/elif). 1 refuted (post-/name resync
spurious-error — get_workstream_display_name swallows its own exceptions).

**Root:** off-slot execution breaks the slot's broader mutual exclusion. Findings
3 (UI interleave) + 6 (identity race) have NO clean fix inside the off-slot model.

**Recommendation to the maintainer (their direction call, pending):** do NOT patch the
off-slot carve-out. The clean fix is the /rewind//retry precedent — lift the
read-only/metadata ops to REST endpoints (GET /history, GET /workstreams, PATCH
name operating on the URL ws_id) rendered out-of-band, and make /raw//debug
client-side toggles; that resolves all six findings by construction. But it's
bigger than #856 scoped (minor-severity annoyance), so the real options are
(A) do the REST lift, (B) defer #856 + drop the branch. Awaiting the maintainer.

**RESOLVED 2026-07-17: the maintainer chose (B).** Posted a deferral comment on #856
(records the failed off-slot attempt + the correct REST-lift path so nobody
re-treads it; issue deferred). Dropped branch feat/856-safe-command-slot-bypass
(`git branch -D`, was 2c8f6206, never pushed — recoverable via reflog ~90d if
ever wanted). main untouched at 515d372a. If #856 is ever revived, do the REST
endpoints, NOT off-slot dispatch.

---
name: project_background_shells_817
description: "Background shells (#817, PR #819 SHIPPED; core/background_shells.py) or notice rail: a new _source must register in BOTH SYSTEM_TURN_SOURCES and _NUDGE_MAP."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-20T16:57:26.327Z
---

# Background shells (#817) — shipped in PR #819 (2026-07-10, `ab7d56e0` + exit-code follow-up `dc647f4d`)

Confirmed working end-to-end in live test; model-side ergonomics validated in-harness. Follow-up spike for `task_agent(run_in_background)` done same day → [[project_background_task_agents]].

**Surface:** `bash(run_in_background=true)` → `bash_N` handle immediately (approval gate unchanged; `is_background` + string/number booleans accepted — one lenient dialect via `_is_truthy_flag`); `bash_output(id, filter?)` → delta since last read + status/exit code (auto-approved); `kill_shell(id)` → group kill (auto-approved; argument space closed). TDD (~120 feature tests).

**Architecture** (`turnstone/core/background_shells.py`):
- Per-ChatSession `BackgroundShellRegistry` — per-workstream isolation is structural (instance attr, no module state). Owner-scoped handles for task_agents (contextvar like `_active_read_files`; reaped in `_exec_task` finally; no notices for owned shells — sub-loop polls; start message says shell dies with the agent).
- #816 rule extended: leader exit (natural or kill) → `killpg` whole group; liveness-guarded (`poll()` under shell lock) so a stale pgid is NEVER signalled (cross-tenant SIGKILL hazard). `spawn_group_leader()` + `drain_pipe_lines()` shared with foreground `_exec_bash` so the two variants can't drift.
- Buffer: capped rolling line deque, drop-oldest with gap accounting; exited records pruned by EXIT order (`_exit_seq`) so a shell never self-evicts its own notice; `unread_lines` excludes evicted lines. Reads serialize per shell (`read_serial`) or a parallel batch double-delivers.
- Filter = killable SUBPROCESS ([[feedback_regex_timeout_needs_subprocess]]): scrubbed env + pinned UTF-8; `FilterTimeoutError` vs `FilterExecError` honest taxonomy; failed filter never commits the cursor; per-line 4096 match window with explicit clipping note; mid-truncation of an oversized delta is flagged as non-re-readable.
- Lifecycle: shells survive generation-`cancel()`, die in `ChatSession.close()` (every teardown path funnels there); `signal_all()` = instant half for multi-session frontends; CLI `_close_all_sessions` + server lifespan close-all (signal-first, Ctrl-C-safe) — the CLI-forgotten-child pattern struck here ([[project_cli_origins_forgotten_child]]).
- Notices: `_notify_external_event` shared rail (watch fires + shell exits): sanitize → soft-cap channel=None → enqueue "any" + `valid_until` → wake. NudgeQueue grew: `"quiet"` channel (cancel demotes "any"→quiet: delivers at next seam, excluded from `WAKE_PENDING` so Stop never self-resumes), `Entry.seq` chronology, `drain_entries`/`requeue` (seq+predicate-preserving give-back). Failed wake: external notices requeue as quiet, user advisories DROP (else zero-backoff wake-respawn hot loop); `_emit_pending_user_nudges` re-stashes the un-emitted tail. **New `_source` types must be registered in BOTH `SYSTEM_TURN_SOURCES` and `_NUDGE_MAP`** — missing registration made notices raise ValueError at every delivery seam and survived 6 rounds because tests asserted queue state, never real emission (end-to-end emission test now exists).

**Judge:** `run_in_background` rides the bash func_args projection ([[project_judge_func_args_projection]] — recurred here, the maintainer caught it). `bash_output` is repeat-warning-EXEMPT but still recorded (exempting record() broke other tools' streak-reset).

**Follow-ups (in PR body):** async `task_agent(run_in_background)` (reuses handle/registry/rail primitives); operator live-shells UI pane (`shells()` hook); TTL; parent hand-off of sub-agent shells; in-process filter fast path if volume grows.

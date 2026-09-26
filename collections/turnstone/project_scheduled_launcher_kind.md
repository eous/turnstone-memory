---
name: project_scheduled_launcher_kind
description: "Scheduled launcher kind (#1090 SHIPPED) or zone-aware schedules (#1091, console/schedule_timing.py): wall-clock plus stored zone, never client-convert to UTC."
metadata: 
  node_type: memory
  type: project
  modified: 2026-09-05T05:09:09.600Z
---

The maintainer's idea (2026-09-04): create a scheduled task from the dashboard launcher as a third
kind next to Coordinator | Interactive. Ruled the one feature of the next 1.8 patch, alongside
refactoring and extraction work plus a small amount of front-end work. Built the same day on
`feat/1090-scheduled-launcher-kind` (issue #1090).

**Shape shipped**: `_LAUNCHER_KINDS` registry (kind, radio id, perm) drives
the toggle, arrow cycle, visibility and the submit gate; the admin shelf's
Runs builder became `console/static/schedule_builder.js` (classic script,
`window.TurnstoneScheduleBuilder`) cloning `<template id="schedule-when-template">`
with `when-` ids scoped per instance; the When block sits between the toggle
and the composer; post-submit is an inline confirmation in the message row
(no pane, no toast); Name derives from the task's first line.

**Rulings to keep**
- Colour: `--blue` (system-operation hue). Magenta/purple is RESERVED FOR
  MCP (the maintainer live, and chat.css says so) — do not reuse it for kinds.
- Recurring inputs are wall-clock in a ZONE (#1091, built 2026-09-04 on
  `feat/1091-schedule-timezone`): never convert local→UTC client-side (drifts across DST, shifts
  weekly/monthly days). The zone lives on the row (`scheduled_tasks.timezone`, migration 073,
  default `UTC` = the old meaning); `_next_cron_runs` walks croniter from a zone-aware start and
  stores `next_run` as naive UTC. The builder detects `browserZone()`, labels the time inputs with
  it, and `stateFromSaved` KEEPS a saved zone (an edit never re-zones to the editor's browser). Next
  runs / confirmation still show browser-local (`formatLocal`). croniter fires twice inside the
  repeated fall-back hour — documented, not fought. `tzdata` is a direct dep because browsers report
  legacy keys (`Asia/Calcutta`) Debian ships only in tzdata-legacy. Zone PICKER filed as #1101
  (09-05) — supportedValuesOf list, detected zone default, saved zone on edit; storage/API/scheduler
  need nothing. The maintainer RULED (09-05): #1096/#1097/#1098 go in the SAME PR as stacked
  commits, not as follow-ups — filed-alongside bugs in the same seam ride along. #1096 = fold
  at_time offset into naive-UTC next_run + migration 074 rewrites stored rows (round-3 catch: a
  create-time fix alone leaves pending rows wrong); #1097 = `_cron_names_a_time` (literal
  minute+hour fields OR @daily-style alias, decided from the RAW expr since croniter expands steps)
  + `_is_second_occurrence(fire)`: PEP 495 fold — the fold=0 and fold=1 readings of the naive local
  time differ in offset only inside the repeated hour, and the candidate equals the fold=1 instant.
  Compare as UTC: aware datetimes sharing a tzinfo compare by NAIVE fields. A "compare with the
  previous firing" version FAILED review (`0,30 1 * * *` interleaves EDT/EST). #1098 =
  `_without_nulls` on BOTH create and update (one rule, 15 fields). Null contract DISPUTED in review
  (security finder: 400 so a restrictive intent can't 200 no-op; verify: refuted, admin caller,
  documented contract) — kept not-sent, flagged to the maintainer. Rebase lesson: a fixup touching
  CHANGELOG lines adjacent to a LATER commit's entry conflicts twice under autosquash; resolve by
  hand, then check `git diff <pre-rebase> HEAD` is empty. `croniter>=3.0` floor was BELOW the
  DST-correct release — measured 5.0.1/6.0.0 fail all four zone cases (hour-after on fall-back,
  skipped half-hours), 6.1.0+ pass → floor `croniter>=6.1`. Lesson: when new behaviour leans on a
  dependency's bug fix, bisect released versions with a scratch venv and raise the floor; uv.lock
  does not protect pip installs. Round 4 (09-05): "retire silently with next_run=''" for an
  unresolvable zone FAILED review (shows active with no next run) → DISABLE the schedule +
  `_record_failure("Schedule disabled: <reason>")` so the run history says why; PUT treats a resent
  unchanged zone as no change (persona/project pattern) and re-validates stored timing on ANY
  re-enable (was at-only); `record_task_run` failure after create is logged, not raised, so the
  advance still happens. Round 5: the null contract FLIPPED to a 400 naming the field on
  create/update/preview (`_null_field`) after security raised the silent-no-op point a second time —
  "documented contract" was a circular defence; loud beats lenient for ambiguous input. Disabled-at-
  dispatch gets its OWN run status `disabled` (not `failed`: the firing succeeded) styled
  `sched-disabled` in the runs list; the reason text lives in server.py beside `_next_cron_runs`
  (producer and explainer adjacent). Review rounds: 7→4→6→5→4 findings; majors 1,0,1,1,0. Hunk-level
  staging for fold-ins: `git diff -- file` split on `@@`, keep hunks matching a regex, `git apply
  --cached --recount` (scratch helper stage_hunks.py); expect a conflict wherever a fixup inserts
  before a line a later commit also inserts before — resolve to ours+theirs. Round 5 bug
  (frozen-tree rerun after the maintainer caught me editing under a live finder): (a) in the disable
  branch the STATE CHANGE goes first, the history write second and guarded — the state change is
  what stops the re-dispatch; (b) the shelf resends EVERY timing field, so "changed" must mean
  value-differs-from-stored for schedule_type/cron_expr/at_time/ timezone (one loop), or a stale
  zone blocks name edits; (c) blank zone on UPDATE is refused (on create blank=UTC, nothing to
  lose); (d) request model docstrings say null is refused (schema ≠ server otherwise). Review
  rounds: 7→4→6→5→8→8 findings; majors 1,0,1,1,2,0. Round 6 = first 0-major round; its minors:
  range-form fixed times (`0 1-2` → widened literal regex to allow `a-b` without a step), a cron
  that NEVER fires is refused on create + re-enable (was stored dormant; preview already said so),
  one guarded `_write_run` for every history row, and the timing helpers EXTRACTED to
  `console/schedule_timing.py` (public names; server + scheduler import at module scope; tests
  import from it). The maintainer RULED 09-05: FLATTEN to one commit (stacked fold-ins were not
  worth their cost) — done via `git reset --soft main` + one commit from the drafted message; the
  stacked-commit ruling earlier the same day is superseded. Round 7: the shelf resends `enabled` on
  EVERY edit, so "enabled in body and true" ≠ re-enable — diff-gate `enabled` against the stored
  value like the timing fields (only a transition validates/recomputes; a name edit must not advance
  an overdue next_run either). Also: catch `CroniterError` (base) in the walk so a stored expression
  the newer parser rejects disables with a reason instead of raising past the guard; `_write_run`
  takes typed kwargs (`**row: Any` hid typos from mypy); ranges-without-step are times of day in the
  DOCS too (reviewer caught doc/impl drift). Lesson: any field the shelf resends unconditionally
  must be diff-gated on the server, and every "presence means intent" gate is suspect. Round 8:
  at_time is diff-gated AS AN INSTANT (`_same_timing_value`) because the shelf re-spells it (+00:00,
  minute precision); the other resent-value compares are string. Filed #1099 (pre-existing:
  `dispatched = True` before knowing the node call succeeded → a failed firing still advances
  next_run; retry semantics need a deliberate call). Stopped after round 8 (0 majors in rounds 6 and
  8; round 7's major was the enabled gate). Final: ONE commit, ~29 files. Browser placeholders are
  REAL: empty TZ → ICU "Etc/Unknown", POSIX "GMT+3" → bare "+03:00"; `browserZone()` screens both
  (formatter round-trip + offset regex) and falls back to UTC visibly. Interval mode stays zoned
  (one column per row; Cron mode would disagree otherwise); hours intervals name the zone ("from
  midnight <zone>"), minutes intervals don't (cadence holds in any zone). Review: 2 unprimed rounds
  (7 findings → 1 major fixed; 4 minors, all fixed); the maintainer asked whether a migration was
  needed and about multi-zone teams — answered per-schedule zone is the standard (GitLab/Cloud
  Scheduler/k8s CronJob); zone PICKER is the natural follow-up for mixed-zone teams.
- Interval bound is ONE predicate (`intervalStepOk`) used by compile,
  reverse-parse and the read-out; saved out-of-range crons open in Cron mode
  unchanged (refusing them stranded them — my round-3 regression).
- Uneven steps (`*/7`) stay accepted; the read-out says "restarting at
  midnight / each hour".
- `admin.schedules` is admin-only and the list is unfiltered → operator
  ownership model is a separate governance follow-up.

**Review campaign**: 8 unprimed rounds; correctness 4,2,2,2(1 major fix-era),
3,1,2,2 — minor-only after round 4, all shallow launcher edges; stopped at the
round-8 wall with a classification (see [[feedback_review_convergence_methodology]]
lessons 7/8). Designer agent review was worth it (5 majors, all taken).

## #1099 failed-dispatch retry (2026-09-05, PR #1103)

Dispatch outcomes are created / certainly-not-created / unknown. Certain
non-creation (no node, request never left, any 4xx, client that could not be
built) is held and retried about once a minute for five minutes after the
first failure, judged after an attempt; unknown (lost reply, 5xx) is never
retried and the failed row says so. Holds live in the `scheduler_holds`
system_settings row, written once per tick only while the lock is still
held. Fan-out granularity is per firing. Filed #1102 for a tick outliving
the 60 s lock (sequential fan-out, 30 s SDK timeout).

**Do not retry the caller-chosen `ws_id` idempotency design.** Built and
rejected in review: the node writes its routing pin only when the create
request carries no id (`turnstone/server.py` ~2956), so scheduled
workstreams went unpinned and console-routed calls landed on the wrong
node; auto/pool can pick a different node on retry; the node answers 409
for creates it later rolls back. Fixing all three needs node-side commit
semantics, not a scheduler change.

The shelf reads a one-shot as completed only when `last_run` is at or
after `at_time`'s instant (`_schCompleted` in admin.js); nothing but a
dispatch writes `last_run`.

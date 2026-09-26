---
name: project_concurrent_approval_cycles
description: "Approval cycles, sub-agent judge gating or pending_approval_details wire: SHIPPED PR #773/#775; a cycle adopts verdicts only from its own judge generation."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-20T17:02:11.106Z
---

**SHIPPED — branch `feat/concurrent-approval-cycles` → PR #773 (2026-07-05)**
(8 commits `d5d07eef..3d784f1a`) fixed the two last 1.7 release blockers: (1) smart
approvals never fired for task_agent sub-agent tool calls (gate was judge-blind);
(2) manual webui approvals broke under parallel task agents (singleton pipeline
multiplexed by N gates → cross-approval, lost-wakeup 3600s hangs, wrong-batch Always
whitelist). **Same-day follow-up PR #775** — "fix send
button stuck disabled by pruning orphaned approval cycles" — a direct postscript
catching a regression the #773 landing introduced (stale/orphaned `ApprovalCycle`
entries left the UI's send affordance permanently disabled); fold into this project's
history rather than treating as separate.

**Shape:** `ApprovalCycle` registry keyed by cycle_id in SessionUIBase (per-cycle
event/result/decision/verdict-park; oldest-first FIFO for selector-less;
`resolve_all_approvals` sweep; `_pending_approval` kept as maintained oldest-cycle
VIEW). Sub-agent gates run `_evaluate_intent(conversation=agent_turns,
agent_gate=True)` — own generation, never touches main supersede slot; all
generations in `_judge_cancel_events` (exact via judge `done_callback`), fired by
`close()`.

**Generation-exactness invariant** (the durable design rule): a cycle may only
adopt/stamp/replay verdicts from its OWN judge generation (`_judge_event` identity).
Enforced at: entry purge (`keep_origin` — spares the batch's own pre-delivered
verdicts, else fast judge → smart-wait stall), registration eviction (purge→register
window), delivery owner-check, Smart-Approvals origin check, and gen-tagged
`_recent_decisions` (cross-gen late verdict stamps `superseded`, never steals a
reused call_id's decision). #775's orphan-pruning fix is an extension of this same
invariant family — a cycle whose generation is gone must not linger and block the UI.

**Wire (BREAKING 1.7):** singular `pending_approval_detail` REMOVED everywhere
(dashboard, ws detail, node snapshot, cluster live) → `pending_approval_details`
list, one entry per cycle with cycle_id. approve POST takes cycle_id/call_id, 409s
stale with current ids, pins selector-less to the lookup's cycle, applies
Always-names only after the pinned cycle actually resolved. stable/1.6 keeps old
shape.

**Durable gotchas:**
- `unittest.mock.patch` start/stop of the SAME target from concurrent threads
  corrupts the patcher restore stack (second stop can reinstall the first thread's
  mock as "original", leaking into later tests). Tests spawning gate threads use ONE
  shared patch pair (`_gate_harness` in test_session_ui_base.py) — never per-thread
  patches.
- A main-thread `approve_tools` call in a test that falls through to the human gate
  hangs the suite 3600s; set instance `ui._APPROVAL_WAIT_TIMEOUT` small as a
  regression guard.
- Channel adapters: (ws_id, cycle_id) keyed entries + legacy ""-fallback centralized
  in `channels/_routing.py` (`get_cycle_entry`/`pop_cycle_entry`/`pop_ws_entries`).

**Review outcome (2026-07-05):** 9 findings validated on #773 — 8 fixed, 1 refuted
(resolve_all rescan loop is correct; snapshot-fix would be worse). Sweep-3
(Always-whitelist misalignment) was the real major. Found beyond review:
generation-blind purge (production smart-stall + test hang), `_ui_cleanup` dropped
legacy single-slot unblock for external UIs (restored as elif).

**Open (unresolved, low stakes):** cancel/close sweeps audit-stamp `denied` with
feedback "Cancelled by user"/"Workstream closed" — user asked whether a distinct
`cancelled` decision label is warranted (see [[feedback_push_back]]). Pre-existing
unrelated: 3 stale TS SDK tests expect legacy `/v1/api/send` (main moved to
path-keyed send in the Stage-2 verb lift, [[project_command_verb_lift]]).

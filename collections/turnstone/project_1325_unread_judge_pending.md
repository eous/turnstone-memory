---
name: project_1325_unread_judge_pending
description: "#1325 unread marker, unread-aware eviction, judge-evaluating marker: the 10-09 scope rulings."
metadata:
  node_type: memory
  type: project
  modified: 2026-10-10T16:37:56.393Z
---

#1325 bundles three gaps: no unread marker on workstreams, idle eviction dropping unread work, and
judge-pending approvals looking the same as "Approval required" (the closed #1273 PR tried a
setting). Scoped 2026-10-09 on branch
`feat/1325-unread-judge-pending`; the LOCAL design note is `docs/design/1325-unread-judge-pending.md`.

**Rulings (the maintainer, 2026-10-09):**
1. Read state is **shared**: any viewer's read clears the marker for everyone (not per-viewer, not
   owner-only). One read cursor per workstream; eviction keys on it.
2. Capacity: idle close skips unread workstreams; capacity eviction takes read idle rows first
   (least recently active first), then the oldest unread ones. Creating a workstream never fails
   because of unread rows. The orphan reap is unchanged.
3. Fix in this work: `attention` was emitted for every tool batch (before the gate, with no
   needs-approval check), which made the coordinator tree announce "Approval required" for plain
   batches. Emit it only when an item needs approval; keep the generation/cancel commit around it.
4. Two PRs: judge-evaluating marker (plus fix 3) first, unread and eviction second, stacked.
5. "Judge evaluating" shows ONLY while a Smart Approvals wait is running (the judge could still
   approve the batch without a person), i.e. the pre-card window. It flips at card publish (a
   person is needed, timeout included) or auto-approval. With Smart Approvals off (the default),
   "Approval required" shows at once: the verdict is only advice and the Approve button works, so
   the issue's literal "until a verdict lands" reading was declined (it could hold the label ~10
   minutes on a struggling judge while a person could act).
6. `attention` is published FROM THE GATE (10-09): the session stamps a generation-fenced
   `_publish_attention` on the main loop's batch; `approve_tools` calls it once, just before the
   Smart wait (judge mark already set) or the card. Policy allow/deny, "Always" grants, configured
   auto-approve, blanket and the unattended grant never show `attention`. The pre-gate fenced
   commit stays as the cancel boundary. The CLI carve-out (UIs that override `approve_tools`
   keep a session-side `attention` for every batch) was DROPPED on 10-10: it predated the
   new-state decision, and the maintainer said drop it if it simplifies. Every gate publishes
   when it waits; the CLI publishes before its y/n prompt and before a background workstream
   waits to be brought forward.
7. Task-agent approvals leave the state `running` (sidebar/tab green): pre-existing, filed as #1338.
   Same root in the CLI: a task agent's gated call in a BACKGROUND CLI workstream is held on
   `_fg_event` with no `_publish_gate_state` stamp, so no `attention` and no bell. Decided 10-10
   (the maintainer): COUNTED STATE HOLDS, not the issue's row flag. Each task-agent gate is stamped
   with a hold publisher; the workstream shows the strongest open hold (`attention` over
   `evaluation`) and `running` when the last closes, every change fenced to the batch's generation
   under `_generation_lock`. That answers the issue's "not from task-agent threads" objection (no
   sibling clearing, no repaint after Stop). The console's amber sub-line (collector drops
   `ws_activity`) stays out: pre-existing for every card. Holds live in a per-batch entry
   (`_tool_batch_gate_holds`) that `_execute_tools` keeps only while the batch executes, so a gate
   outside an executing batch moves no state (a side review's point: returning to `running` assumes
   task agents run only inside the batch; unbuilt background agents would break it). Review F6
   (10-10): KEEP TWO STAMPS, main loop direct and task agents counted; the reason goes in the PR,
   not a one-publisher rewrite of #1325's post-approval commit. Local note:
   `docs/design/1338-task-agent-approval-state.md`.
8. NEW STATE, not a flag (10-09, overturning the issue's "state stays `attention`" line): the
   judge's hold is `WorkstreamState.EVALUATION = "evaluation"` (the maintainer's name; "judging"
   rejected). The gate publishes `evaluation` before the Smart wait, `attention` before a card,
   and the session `running` after an auto-approve. A `judge_evaluating` row flag was built and
   reviewed first, then dropped: ~30 plumbing sites and three displayState helpers. Known trade:
   a missed start-of-wait update shows `running`, and an unaware client sees an unknown state.
9. Smart Approvals wait (10-09/10, from round-2 review): a batch the heuristic rules flag
   deny/critical skips the wait (deterministic floor before the learned call); the wait ends at the
   first verdict of THIS judge generation that rules the batch out (stale generations don't count).
   Cross-checked against HYPOTHESIS.md: narrow-only holds, the escape to the principal shortens. The
   one trade (the card can appear before a sibling's verdict lands; an attacker could pull it
   forward with a quick `review`, a timing nudge, no authority) was put to the maintainer, who
   chose to keep the early stop as built: it matches Smart-Approvals-off, the person decides.
10. Orphan-reaper index: migration 081 rebuilds `idx_workstreams_reaper` with `evaluation` (explicit
   IN list, maintainer's pick). Measured on PostgreSQL 18: the five-state query on the four-state
   index fell back to a filtered scan (~5x cost); `NOT IN ('closed','error')` also uses the index
   and would avoid the next migration, offered but not chosen.

**Design defaults stated at scoping and not overruled:** unread is a pair of event-id cursors
(turn-end id vs read id, read POST takes the max), so a late read can't clear newer output. Read
means pane in view, browser tab visible, scrolled to latest. Tracked: top-level web and scheduled
workstreams; channel (`client_type="chat"`) and coordinator children are not. In memory only (the
live list is rebuilt lazily after restart anyway). The judge marker is the `evaluation` state
(ruling 8), not a flag.

**Why:** these settle the issue's open questions; re-asking them costs the maintainer a round.
**How to apply:** build to these rulings; raise only new decisions. Related:
[[feedback_minimal_scope_first]], [[project_multiuser_attribution_ux]].

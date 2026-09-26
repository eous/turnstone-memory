---
name: project_background_task_agents
description: "Building task_agent(run_in_background): spike done 2026-07-10, unbuilt; build on PR #820's sub-agent id mint with per-agent cancel_event and a registry."
metadata: 
  node_type: memory
  type: project
---

# Background task agents — spike complete, unbuilt (2026-07-10)

The #819 follow-up ([[project_background_shells_817]]). Full spike: **`docs/design/task-agent-background-spike.md`** (local-only) — decisions table, complete E1–E7 event design, file-by-file touch list, emission-test plan. Shape: `task_agent(run_in_background=true)` → `agent_N` handle; `task_output(id)` idempotent status/result (NOT bash_output delta semantics — synthesis re-readable); `kill_task(id)` cooperative cancel with kill_shell-style three-way honesty. Completion = NudgeQueue notice `_source="background_task_done"` (register in BOTH `SYSTEM_TURN_SOURCES` + `_NUDGE_MAP`; mirror test `test_vocabulary_mirrors_nudge_map_both_directions` now fences the #819 round-6 bug class; emission test written red-FIRST per event class).

**Facet C (full-fidelity sub-harness) → BRIEFED for a fresh session 2026-07-11**: `docs/design/subagent-native-lane-lowering-brief.md`. Approach = carry the agent's native lane (thinking blocks) + a lowering pass mapping the internal turnstone id → the provider's own id at the wire (so the native block is never rewritten → no signature risk). The Turn layer already carries a native lane (`Turn.assistant(native=)`, `ProviderNative(producer,blocks)`, `dict_from_turn` emits `_provider_content`), so it's small-to-medium, gated on a boundary spike (in-memory native replay for an agent turn + end-to-end on a real thinking model). SUB-AGENT (ephemeral) scope ONLY — NOT the durable O3.

**Reasoning fidelity matters across deployment types (2026-07-11).** Task agents used for service
mapping, infrastructure changes, and script development may run on reasoning models. Preserving
their native reasoning state can materially affect continuation quality. **Why:** a deployment
focused on local models does not represent every supported workflow. **How to apply:** evaluate
native-state preservation against the supported provider paths and real task-agent workloads before
dismissing its value.

**Spike doc updated 2026-07-10 with #820 learnings** (§6): the mint's `_agent_run_seq` run tag is the backgrounding enabler (each detached run = fresh tag → cross-run/turn collision-free child ids for E2). KNOWN LIMITATION the backgrounding frontend inherits: **parent-CARD aliasing** — child ids are de-collided but the PARENT task_agent call_id is a main-loop id, still NOT de-collided, so E1/E6 cards keyed on it alias if a local provider reuses `call_0` as the parent id across turns; real fix = main-loop id hygiene (design doc `main-loop-native-lane-id-hygiene.md`), not a blocker. Methodology to reuse: UNPRIMED re-review + journal-recovery if the review crashes + verify provider-wire claims (don't launder review-agent API reasoning).

**Sequencing: bug-3 sub-tool id unification ([[project_task_agent_id_consistency]]) graduates to PREREQUISITE** — backgrounding makes cross-turn sub-step arrival the common case and the `parent::provider_id` cross-turn collision hits every event. **DONE for the sub-agent path: PR #820** (`fix/task-agent-subtool-ids`) mints `{parent}::r{run}s{step}::{id}` (the verified aliasing fix). The wire-safety projection bolted on in #820 rests on an UNVERIFIED charset/length premise contradicted by production (old `::` format worked reliably on Anthropic) — KEPT as reframed defensive hardening (the maintainer's call), claims corrected; see [[project_task_agent_id_consistency]]. Main-loop/native-lane half is designed only (doc `docs/design/main-loop-native-lane-id-hygiene.md`) and NOT a blocker for backgrounding (sub-agent ids are now collision-free). So background-agent work can proceed on top of #820's mint; then the #819-style PR (backend+frontend+tests).

**Load-bearing seams found in the spike (session.py @ 062a260c):**
- task_agents run in a per-batch `with ThreadPoolExecutor(4)` (~:9191) — nothing outlives `_execute_tools`; `agent_turns` is a stack local of `_exec_task` (~:15569). Background = dedicated thread + new `BackgroundAgentRegistry` (background_agents.py) owning `agent_turns`/cancel_event/status; cap 4; `_exit_seq` pruning.
- `_run_agent` checks the LIVE `self._cancel_event` bare (~:15303) and `send()` swaps it every generation — detached agents would be uncancellable by the right Stop and killable by the wrong one. Fix = per-agent `cancel_event` param (also IS kill_task/close). Proposed: survive generation-cancel (shells rule) — token-burn-after-Stop flagged as open question.
- Nested approvals already work detached: `ApprovalCycle` reentrant, `approve_request` broadcasts regardless of generation, `_APPROVAL_WAIT_TIMEOUT=3600` self-deny backstop.
- Frontend is the surface bash never had: card state's ONLY running→done transition is the parent tool_result (interactive.js `appendToolOutput` ~:3482; `_ensureAgentCard` pins `"running"` ~:3370) — handle-result misrenders BOTH orderings. Design: `agent_background` marker on the handle tool_result + new `agent_status` SSE event + `"background"` card state + /history overlay serves live registry steps for mid-flight reloads (closes the ring-buffer-vs-stash divergence). `_clear_agent_children` moves to background-thread finally or late sub-steps lose `parent_call_id` (nesting-escape regression).
- Verified no-ops: backgrounded agent's own shells stay correct (sub-loop still synchronous in its thread; owner reap in finally holds); judge projection add is one field at ~:8208 (#760 lesson, third occurrence — designed in this time).

**Open questions for the maintainer (in doc §7):** survive-cancel vs Stop-kills; `kill_task` vs `task_stop`; synthesis-only vs transcript-delta task_output; approval loudness beyond the 3600s backstop; cap value.

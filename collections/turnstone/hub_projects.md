---
name: hub_projects
description: "Index of shipped, deferred, side and completed projects plus the don't-redo list (moved verbatim from MEMORY.md 09-25): check before proposing a feature or evaluation."
metadata:
  type: project
---

## Shipped in the 1.8 cycle
- [#1233 guarded fetch on httpx2](project_1233_guarded_fetch_httpx2.md) — MERGED #1238/#1239; Fetch Metadata and open_preview header rulings, redaction limits, declined review points
- [Copy affordances](project_copy_affordances.md) — SHIPPED #944; whole-source and idle-only copy rulings settled
- [Idle-tasks nudge](project_idle_tasks_nudge.md) — #913 MERGED; read docs/design/913-HANDOFF-fail-closed.md first; signal in the state machine, bodies = observed facts
- [Scheduled-kind launcher + zone-aware schedules](project_scheduled_launcher_kind.md) — #1090/#1091 SHIPPED; #1099 retry policy PR #1103 (09-05): caller-chosen ws_id idempotency REJECTED, don't retry it; #1102 filed
- [Nudge eval harness](project_nudge_eval_harness.md) — Nudge eval sweeps → production wire + canary_after check before believing a grid
- [#857 cwd tool notes](project_857_cwd_tool_notes.md) — shipped #871; cwd facts ride fs tool descriptions, never the system prompt; grants → #872
- [#856 command slot-bypass](project_856_command_slot_bypass.md) — Phase 1 failed review; DEFERRED, branch dropped; revive only as a REST endpoint lift
- [Single-credential MCP minting](project_mcp_obo_single_token.md) — shipped #830 (Closes #551) → [[reference_entra_obo_harness]]; one refresh token per user, entra/rfc8693 legs
- [task_agent native lane](project_task_agent_native_lane.md) — PR #825; minted ids never outlive an invocation (wire_id_map); durable sub-turns persist Turn-IR verbatim
- [Prefill-only rerank tier](project_prefill_only_rerank.md) — #914 in 1.8; one /v1/completions logprob client; self-hosted engines only, no Ollama
- [#902 memory-index](project_902_memory_index.md) — #902 (1.8); a complete unfiltered index in the stable prefix REPLACES composition-time snippets; bodies on demand
- [Self-host latency arc](project_selfhost_latency_arc.md) — Self-host latency (#916-#920) → admission/fan-out bounds, not retries; slot thrash is not #902

## Shipped/resolved and open/deferred
- Shipped/resolved: [Compaction visibility](project_compaction_visibility.md) — PR #863 SHIPPED 07-17; compaction SSE lifecycle + progress card; defer-and-drain /send during command windows
- Shipped/resolved: [Background shells](project_background_shells_817.md) — #817 shipped PR #819; a new notice _source registers in BOTH SYSTEM_TURN_SOURCES and _NUDGE_MAP
- Shipped/resolved: [Preview pane](project_preview_pane.md) — open_preview/preview pane (PR #800) → descriptor in tool-turn meta, salted blobs; settled design
- Shipped/resolved: [Nudge wake](project_nudge_wake_fixes.md) — PR #799; wake gate keys on the Workstream object + requires a real NudgeQueue; Mock sessions caused wake storms
- Shipped/resolved: [History tsvector](project_history_search_tsvector_fix.md) — Pg history search 1MB-tsvector abort → left() cap + rollback (PR #795); GIN column queued
- Shipped/resolved: [MCP flaky CPU spin](project_mcp_flaky_cpu_spin_regression.md) — MCP CPU spin after server flap → FIXED #787/#788: transport owner tasks, one cancel max
- Open/deferred: [1.7→1.8 roadmap](project_1_7_roadmap.md) — 1.7 shipped; rolled-forward 1.8+ backlog; the mcp v2 #679 plan moved to project_679_mcp_sdk_v2; re-spike before building
- Open/deferred: [Frontend long-session](project_frontend_long_session_audit.md) — Long-session frontend perf/wedge → #754 on dev; #755 windowing/CSS pair NOT on dev; P3 infra open
- Open/deferred: [Compaction vs definition](project_compaction_definition_review.md) — Compaction quality work: #751/#752 shipped; build the pi-sufficiency eval before PR 3
- Open/deferred: [Task agent modernization](project_task_agent_modernization.md) — task_agent rebuild SHIPPED #732; open: perception sub-harness for images, bug-3 id unification
- Open/deferred: [id consistency](project_task_agent_id_consistency.md) — task_agent sub-tool ids: mint FIXED #820; main-loop ids fixed at ingest, never on the wire
- Open/deferred: [Model modal kind](project_model_modal_kind_redesign.md) — Kind-aware model modal still deferred; only the backend rerank-detect fix shipped 2026-06-01
- Open/deferred: [Memory relevance](project_memory_relevance_pipeline.md) — Prefix memory injection: composed once after first user turn, then frozen; per-turn refresh unbuilt

## Side projects and environment
- Env/side: [Memory-store maintenance](reference_memory_store_maintenance.md) — Back up scoped
  edits, verify replacements, isolate test databases
- Env/side: [Understone door game](project_understone_doorgame.md) — never name the homage source; server owns all numbers, model narrates only

## Completed, 1.7 history and don't-redo
- Don't-redo: [plan_agent](project_plan_agent_removed.md) — REMOVED 07-01; ship planning discipline as a skill on task_agent instead
- Done: [SSE resume](project_fresh_connect_replay_completeness.md) — SSE fresh-connect gap DONE (#616): /history cursor + Last-Event-ID, one replay path
- Done: [Refresh-resume snapshot](project_streaming_sse_resume.md) — Refresh mid-stream lost content → DONE: inflight buffers + in_progress_snapshot; commit reset stays
- Done: [Coord child addressing](project_coord_child_addressing.md) — Coord child addressing → shipped v1.6.0; mutable names rejected as addresses, hex prefix dropped
- Done: [Voice I/O](project_voice_io.md) — Voice I/O (shipped #618): OpenAI audio wire = abstraction; Anthropic no audio; roadmap unstarted
- Done: [Output-guard merge](project_output_guard_llm_merge.md) — Output-guard LLM judge edits → merge, never override: max(heuristic, llm); LLM can only escalate
- Done: [Coord completion stack](project_coord_completion_stack.md) — Stacked dependent PRs: branch off the parent PR, not main; brief LOC estimates run 3-4x low
- Done: [Design system v1](project_design_system_v1.md) — Frontend CSS / 'is this view on v1?': gate stripped in #431; one unified default design system
- Done: [Config → storage](project_config_to_storage.md) — ConfigStore migration DONE; per-node settings work; advertise/console URLs still env-only
- Done: [/command verb lift](project_command_verb_lift.md) — /rewind /retry path-keyed (#549 DONE); bare .msg.user selector; /route/ flag false positive
- Done: [Phase 8 coordinator scale](project_phase8_status.md) — Coordinator batch/quota work: Phase 8 done #386-388; check its 7 deferred follow-ups first
- Done: [SSE fan-in (#540)](project_sse_fanout_pending.md) — SSE fan-in (#540): never built; Caddy HTTP/2 retired the connection cap, per-pane EventSource stays
- 1.7: [Projects container](project_projects_feature_design.md) — Projects container SHIPPED #724 (mig 062); project axis replaces persona-collection (#684)
- 1.7: [SKILL.md/persona split](project_skillmd_refactor.md) — Skills vs persona (shipped #762): capability never identity; gate at _high_risk_skill_denied
- 1.7: [Envelope nonce tags](project_envelope_nonce_tags.md) — Envelope nonce fences SHIPPED #726: bracketed [start tag_nonce] in core/fence.py; escaping removed
- 1.7: [Memory collections v2](project_memory_collections_design.md) — Memory collections (#684) → superseded, unbuilt; Projects took the role; persona ≠ skill
- 1.7: [PR #750 multi-user](project_pr750_multiuser_context_review.md) — PR #750 multi-user context review: closed, majors fixed on main; re-verify before citing as open
- 1.7: [Concurrent approvals](project_concurrent_approval_cycles.md) — Approval cycles shipped #773/#775; generation-exactness: a cycle takes only its own judge gen
- 1.7: [Eval/optimizer split](project_eval_optimizer_split.md) — Eval/optimizer split SHIPPED (#763/#765): eval measures only, optimizer→eval.core; #762 gate met
- 1.7: [Project sharing](project_project_sharing_gaps.md) — Project sharing SHIPPED #743/#745; cross-conversation queries reuse HISTORY_VISIBILITY_SCOPE_SQL
- 1.7: [Pane hotkeys](project_pane_hotkeys_architecture.md) — Pane hotkey change: edit shell.js PANE_MENU_ACCELS only; Ctrl on macOS, Alt elsewhere
- 1.7: [Tool-args legalization](project_tool_args_wire_legalization.md) — vLLM 400 on bad tool args: fixed #778; sanitize in lowering on the wire copy, Turn untouched
- 1.7: [MCP hardening](project_mcp_dead_transport_followup.md) — MCP self-healing trilogy SHIPPED (#742/#767/#768); the MCP SDK has no reconnect, Turnstone owns it
- 1.7: [Coop compaction](project_cooperative_compaction.md) — Compaction/truncation budget work → one shared fullness measure; pin the default config in tests
- 1.7: [Rehydration deadlock](project_compaction_rehydration_deadlock.md) — Compaction/resume/overflow work → fixed #731/#740; persisted checkpoint is truth, sweep consumers

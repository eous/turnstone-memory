---
name: project_task_agent_native_lane
description: "task_agent native lane / wire_id_map / minted ids (#825): minted ids never outlive an invocation; durable sub-turns persist Turn-IR verbatim, re-mint on load."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-20T17:02:38.479Z
---

# task_agent native reasoning lane (Facet C, agent-scoped) — PR #825

**PR #825 (2026-07-11)** (`feat/task-agent-native-lane`, 5 commits off merged #820).
Full brief: `docs/design/subagent-native-lane-lowering-brief.md` (local, updated with spike + scope-widening).

What shipped: `_run_agent` turns carry `ProviderNative(producer=agent provider, blocks=result.provider_blocks)`; `restore_provider_tool_ids(messages, wire_id_map)` in lowering.py maps minted→provider-original ids on the agent wire (**`legalize_tool_call_ids` + `wire_safe_tool_call_id` DELETED** — the `tid_` projection is gone; signed native ids cannot be projected). Covers ALL lanes: Anthropic/anthropic-compat (verbatim wire_blocks), Responses (Phase 3 ordinal replay), vLLM openai-compat (new `CompletionResult.reasoning` capture + Phase 5 attach at agent seam), llama.cpp capture-only, Google thought_signature.

**Invariants added (load-bearing for [[project_background_task_agents]]):**
- `wire_id_map` is per-`_run_agent`-invocation; minted ids must NEVER outlive the invocation. A resumable/background agent rebuilding history with prior-run minted ids hard-orphans tool_results (native lane makes unmapped minted ids fatal, not benign). **DECIDED with the maintainer 2026-07-11: if sub-turns go durable, persist Turn-IR verbatim (NOT the map, NOT the wire projection — layering inversion), re-mint at load (run_seq is session-scoped), rebuild the map from native↔mirror structural 1:1 pairing; no-native-client-block turns need no entries. Never string-split the mint (not injective). Full rationale: spike doc §9.**
- Blank-provider-id turn — **rule SOFTENED in the #827 fix round (2026-07-13, the maintainer directed that a replacement id be manufactured)**: `model_turn.backfill_blank_native_tool_ids` first repairs the lane pairwise (manufactured mirror uuids written into BLANK-id native client tool blocks only — a non-blank provider id is never rewritten, which protects signed lanes; pairing = the 1:1 native↔mirror ordering below), and only a pairing mismatch falls back to the old total rule: `finalize_provider_blocks(had_blank_ids=True)` keeps ONLY `reasoning_text`. The Google fidelity swap still refuses blank-id/partial historical lanes (keeps sanitized mirror) — but repaired lanes are no longer blank-id, so `thought_signature` survives blank-id compat responses. Whether Gemini's server accepts a replayed signature with a manufactured id = 1c live-matrix item.
- Shared single-path primitives (the maintainer's closure directive): `_finalize_provider_blocks` (both harnesses), `legalize_tool_call_entry` (sanitize + Google swap). Don't fork these.

**Verified:** no producer string-match exists on the wire path — translators gate per-block by SHAPE
+ `replay_reasoning_to_model` (dual gate with `supports_reasoning_replay` cap; operator flag default
OFF — replay fires only where the model row enables it). Live E2E against a local vLLM test endpoint
serving deepseek-v4-flash, both surfaces, 14/14 (script: session scratchpad
`e2e_native_lane_vllm.py` pattern — anthropic SDK base_url no /v1, wrap client method to capture
request bodies).

**OPEN:** commercial Anthropic + Responses E2E not run; unresolved question whether pre-fix commercial Anthropic thinking agents 400'd (masked by salvage path) or degraded silently. Accepted-findings register in the PR body (duplicate restored wire ids = proven pre-#820 shape; historical blank-id rows on the Anthropic replay path → O3's territory).

Review: 4 workflow rounds (~2.5M tokens total), converged via a SIMPLIFICATION (reasoning_text-only blank rule dissolved 3 findings at once — when delta rounds keep generating exotic PLAUSIBLEs about a guard, consider making the guard total instead of surgical).

---
name: reasoning-persistence-replay-shipped
description: "Reasoning replay or a new model profile (PR #537): supports_reasoning_replay defaults False; vLLM Phase 5 gate is NOT capability-gated, by design."
metadata: 
  node_type: memory
  type: project
---

## TL;DR

Optional, per-model **reasoning persistence + replay** across providers. Shipped to main via **PR #537 (2026-05-30)** (consolidates the original PR #498 stack + the Phase 5 vLLM work).

Controls:
- Two DB-backed operator flags on `model_definitions` (admin-toggleable):
  - `surface_persisted_reasoning` (default **True**) — gates UI rehydration of stored reasoning on `/history`. Storage of reasoning bytes in `provider_data` is independent of this flag (they ride along regardless).
  - `replay_reasoning_to_model` (default **False**) — gates wire-side replay of stored reasoning on the next provider call.
- One static `ModelCapabilities.supports_reasoning_replay` (default **False**) — second gate that AND-s with `replay_reasoning_to_model` for Paths 1 & 2. Set True only on canonical OpenAI gpt-5*/o-series + all Claude.

Four reasoning paths: Anthropic (1), OpenAI Responses (2), Chat Completions synthetic block (3), and **Phase 5** vLLM Chat Completions `reasoning` field (the only viable multi-turn CoT replay surface for vLLM-served non-Harmony models).

## Safety invariants (most important — keep all)

- **Capability gate defaults False** on unknown / local-server models → `include=`/replay shape is never emitted unless an operator explicitly opts in. Adding a new local-model profile: do NOT set `supports_reasoning_replay=True` unless the server documents support for the relevant replay shape (none do today).
- **Non-canonical Responses providers**: `server_compat.py` can route non-OpenAI models (e.g. Mistral via vLLM with `api_surface="responses"`) through `OpenAIResponsesProvider`. An operator flipping `replay_reasoning_to_model=True` there must ALSO manually flip `supports_reasoning_replay=True` AND verify the server understands `include=["reasoning.encrypted_content"]`. Even then, vLLM's `construct_input_messages` **explicitly filters all `ResponseReasoningItem` for non-Harmony models** — so Responses-surface replay is structurally impossible on vLLM regardless of flags (only Harmony/gpt-oss take a different, preserving path). Adding genuine vLLM reasoning replay would likely need a separate provider class, not `OpenAIResponsesProvider`.
- **Loud vs silent failure modes** drive the gating design:
  - Paths 1+2 fail **loud** (Anthropic 400s on unsigned `thinking`; Responses 400s on `ResponseReasoningItemParam` for non-reasoning models). The static capability gate prevents avoidable user-visible errors → dual-gate.
  - Phase 5 (vLLM Chat Completions) fails **silent** — vLLM's chat template drops the field at render time if the template doesn't read `reasoning_content`. A static code-only gate would add operator friction without preventing the silent failure.
- **Phase 5 uses a deliberately asymmetric / parallel gate**, NOT the dual-gate. It single-gates on operator `replay_reasoning_to_model=True` AND `server_type=="vllm"` AND provider `isinstance OpenAIChatCompletionsProvider` — reading `cfg.replay_reasoning_to_model` directly to bypass the `supports_reasoning_replay` AND-gate. The server-type + provider-instance pins bound blast radius to vLLM (canonical OpenAI / llama.cpp / sglang never see the non-standard field). **The asymmetry is the design** — future contributors should not "fix" it by adding `supports_reasoning_replay` to Path C.

## Unified provider table

| # | Provider / surface | Capture | Persist mechanism | Replay surface | Gating |
|---|--------------------|---------|-------------------|----------------|--------|
| 1 | **Anthropic** | `thinking_delta` → raw blocks | `_provider_content` `{type:"thinking", thinking, signature}` | Verbatim block via `_provider_content`; shape-filtered by `ANTHROPIC_VALID_BLOCK_TYPES` so foreign blocks fall through cleanly | `replay_reasoning_to_model` **AND** `supports_reasoning_replay` |
| 2 | **OpenAI Responses** (gpt-5+, o-series) | `response.reasoning_text.delta` + summary deltas | `_provider_content` `{type:"reasoning", id, summary, content?, encrypted_content?}` — only when `include=["reasoning.encrypted_content"]` requested | `ResponseReasoningItemParam` input items re-emitted from stored content | `replay_reasoning_to_model` **AND** `supports_reasoning_replay` |
| 3 | **Chat Completions synthetic** (vLLM/llama.cpp/Gemini-compat) | `delta.reasoning_content` (non-canonical Pydantic extras) | synthetic `{type:"reasoning_text", text, source?}` stamped at end-of-stream **iff** no native provider blocks emitted | UI rehydration only — historically "no replay surface" | server-emission-driven; no flag gate on capture |
| 4 | **Phase 5: vLLM Chat Completions** | (reuses path-3 persisted content) | reuses `_provider_content` | session-level attach of non-standard `{"reasoning": "<text>"}` on assistant messages, consumed by vLLM template's `reasoning_content` | operator `replay_reasoning_to_model` **AND** `server_type=="vllm"` **AND** `isinstance OpenAIChatCompletionsProvider` (NOT capability-gated) |

**Synthetic block shape is intentionally `reasoning_text`, not `thinking`** — so cross-model resumption (local → Anthropic) doesn't push an unsigned Anthropic-shape block to Anthropic's wire (would 400). It falls through the Anthropic filter without needing signature validation. `ANTHROPIC_VALID_BLOCK_TYPES` = `{text, image, thinking, redacted_thinking, tool_use, tool_result, server_tool_use, web_search_tool_result}`.

### vLLM's three surfaces (source-verified, the basis for the path choices)

- **Responses, non-Harmony** (DeepSeek R1, Qwen3, Mistral): reasoning items **explicitly filtered** out of input (`construct_input_messages`). Replay structurally impossible — stateful chaining and stateless input items both hit the filter.
- **Responses, Harmony/gpt-oss**: reasoning **preserved** via raw Harmony message list re-append; `auto_drop_analysis_messages` keeps only CoT after the most recent final-channel message. Requires `VLLM_ENABLE_RESPONSES_API_STORE` (off by default) + server-side state for the stateful path.
- **Chat Completions, non-standard `reasoning` field** (the Phase 5 path): `ChatMessage.reasoning` is forwarded as both `reasoning` and legacy `reasoning_content` to the template. Qwen3/DeepSeek templates inline it; others silently drop it; Harmony converts it to an analysis-channel message then auto-prunes. Stateless, no server-side state — which is why it's the most viable production replay surface for vLLM.

## Cross-provider seam safety

- Anthropic → vLLM mid-workstream: extractor returns `.thinking` text, signature dropped (vLLM doesn't validate). Same for Responses `{type:"reasoning"}` → extract `summary`/`content`.
- vLLM → Anthropic / canonical OpenAI / llama.cpp / sglang: Phase 5 gate fails (provider or server-type pin) → no emission.
- `sanitize_messages` strips only `_`-prefixed keys, so the `reasoning` field survives to the wire for free (OpenAI SDK + httpx pass unknown fields through, verified by spike). Anthropic→others safety predates this work.

## Key file pointers

- `turnstone/core/storage/migrations/versions/052_model_reasoning_persistence.py` — the two `model_definitions` columns.
- `turnstone/core/history_decoration.py` — `_BLOCK_TYPE_PROVIDER_FACTORY` dispatcher (thinking/redacted_thinking/reasoning/reasoning_text), `extract_reasoning_text_from_provider_content`, `attach_vllm_chat_reasoning_field` (Phase 5 helper).
- `turnstone/core/session.py` — `_resolve_replay_reasoning_to_model` (dual-gate for paths 1+2), `_resolve_server_type` (reads `cfg.server_compat`, NOT `cfg.capabilities`), `_maybe_synth_reasoning_block`, Phase 5 attach hoisted at `_try_stream` + `_utility_completion` (agent `_api_call` deliberately excluded — agents are outside the persistence/replay contract).
- `turnstone/core/providers/_protocol.py` — `ModelCapabilities.supports_reasoning_replay` (default False); per-model capability flags live here + the canonical OpenAI table in `_openai_common.py` (every `reasoning_effort_values` entry = True) and Anthropic table in `_anthropic.py` (all True).
- `turnstone/core/providers/_anthropic.py` / `_openai_responses.py` / `_openai_chat.py` — per-path capture/convert/extract + the `include=` gate (`_build_kwargs`).

Lens ([[project_harness_compiler_dialect_stack]]): the loud/silent + capability-gate split is **soundness-gated lowering** — decidable transforms ship free, meaning-touching replay sits behind the gate; the `_provider_content` round-trip is the same native-lane **'leak'** as #699.

## Outstanding / verify items

- **Exact minimum vLLM version** that supports `ChatMessage.reasoning` on Chat Completions input — flagged **unverified**; document in operator docs before relying on it.
- **vLLM Jinja template strictness**: if vLLM uses strict undefined-attribute access, templates that don't read `reasoning_content` could 500 instead of silently dropping the field. Verify against a live vLLM container.
- Token-budget trimming for replayed reasoning, llama.cpp/sglang replay, and operator docs remain deferred.

---
name: feedback-vllm-messages-api-default
description: "Configuring a vLLM model: default to the anthropic-compatible /v1/messages lane (base_url without /v1); audio/omni perception models use the OpenAI lane."
metadata: 
  node_type: memory
  type: feedback
---

When serving local vLLM models for Turnstone, the user DEFAULTS to the `anthropic-compatible` `/v1/messages` lane, not the OpenAI chat-completions lane.

**Why:** they've found vLLM's native `/v1/messages` (Anthropic Messages API) support is better than its OpenAI `/v1/chat/completions` endpoint. Validated live 2026-06-21: qwen3.6-27B-FP8 and gemma-4-12B both serve clean Anthropic-shaped responses on `/v1/messages` (vLLM serves it with no special flag). The qwen checkpoint has since moved on (2026-07-05: NVIDIA/Blackwell switched to `nvidia/Qwen3.6-27B-NVFP4`, 4-bit + MTP 2-token spec-decode, for memory/throughput; ROCm/AMD now recommends the FP8 checkpoint instead of the old BF16 guidance) — the lane choice below is about the API shape, not the quantization, and is unaffected by which checkpoint is loaded.

**How to apply:** prefer `provider="anthropic-compatible"` for vLLM reasoning models — `base_url` WITHOUT `/v1` (the SDK appends `/v1/messages`). LiteLLM can front this: declare the backend as `anthropic/<name>` with `api_base` at the vLLM ROOT; it forwards Anthropic-native to vLLM's `/v1/messages` (no down-translation). See [[project_messages_api_provider]].

**Perception exception (audio/omni):** omni models used for perception (vision + AUDIO, e.g. gemma-4) must use the OpenAI lane — `provider="openai-compatible"` (base_url WITH `/v1`), LiteLLM backend `openai/<name>` at the vLLM `/v1` base. Audio (`input_audio`) has no Anthropic-Messages equivalent, so turnstone gates audio roles to OpenAI-SDK providers. LiteLLM serves BOTH routes (`/v1/messages` + `/v1/chat/completions`) on one port at once and each model_list entry picks its own backend — so a single gateway runs reasoning models on `anthropic/` and perception models on `openai/`.

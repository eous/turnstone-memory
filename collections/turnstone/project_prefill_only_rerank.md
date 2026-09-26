---
name: project_prefill_only_rerank
description: "#914 prefill-only rerank (chat model scores BM25 memory candidates by Yes/No logprobs) IN 1.8: one /v1/completions client, self-hosted, no Ollama."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-26T18:40:34.594Z
---

#914 tracks a prefill-only LLM rerank tier: the chat model scores BM25 memory
candidates by softmaxing Yes/No next-token logprobs, all candidates in ONE
batched `/v1/completions` call. IN SCOPE FOR 1.8 STABLE (the maintainer 2026-07-26;
was exploratory).
Design note: `docs/design/prefill-only-llm-ranking.md` (drafted by the deployed
instance in operator chat 2026-07-26 03:1x, then reviewed + corrected same day).

Decisions / non-obvious facts (details in the doc + #914):

- Sibling `RerankClient` impl is the whole change surface — the
  `_bm25_reranker()` / `score_memories()` seam and `calibrate()` are
  client-generic and need zero changes; only `calibrate_model()` + its two
  callers branch. Threshold storage works unchanged IF prefill mode is entered
  by selecting a model definition in the Reranker role (explicit capability
  preferred over implicit chat-definition fallback).
- Scope ruling: self-hosted engines only (Anthropic exposes no logprobs;
  hosted per-token scoring defeats the reuse-the-idle-GPU premise).
- Cross-encoder stays the default recommendation; this tier is the
  single-GPU / zero-setup fallback. Batching kills serialization, not compute
  — remaining gap is the FLOPs ratio (~15x for 8B vs 560M cross-encoder).
- Engine claims verified against mainline docs/source 2026-07-26 (deltas in
  #914 comment): vLLM `logprob_token_ids` (explicit label-id logprobs) is the
  PRIMARY path — recent field, version-gate; equal `logit_bias` + top-K is the
  portable fallback (V1 default `logprobs_mode=raw_logprobs` = pre-processor
  values; equal bias cancels in pairwise softmax on processed engines).
  Leading-space token variants → resolve ids via `/tokenize`. vLLM CAN serve
  decoder-only rerankers via seq-cls conversion (`classifier_from_token`) but
  only on a dedicated pooling instance — doesn't replace the shared-instance
  completions route. SGLang native `POST /v1/score` (query/items/
  label_token_ids/apply_softmax). llama.cpp OpenAI-compat completions takes
  array prompts + logprobs (same client shape as vLLM). Live-spike items
  remain flagged in doc ([[feedback_sdk_boundary_testing]] applies).
- Ollama EXCLUDED — the maintainer 2026-07-26: Ollama is not an officially supported engine; don't
  add it to engine matrices ([[feedback_official_provider_paths_only]]).
- ONE-CLIENT ruling (the maintainer asked, 2026-07-26): classic `/v1/completions`
  (list prompt, max_tokens=1, temperature=0, top-K logprobs keyed by decoded
  token STRING → no tokenizer dependency) is the portable core on all three
  engines — single implementation, no per-backend clients; engine extras
  (`logprob_token_ids`, `logit_bias`, SGLang `/v1/score`) are feature-gated
  request decorations only. Calibration probe doubles as per-engine
  conformance test. Issue #914 body reflects this.
- Corrections made during review, for future re-finds: probe set is 18 groups
  not 10; CLI verb is `turnstone-admin rerank-calibrate` (not `turnstone`);
  the instance's draft kept stale serial-prefill cost claims after adopting
  batching (internal contradiction class: partial-update leftovers).

Related: [[project_reranker_backend_design]] · [[project_bm25_rerank_redirect]]
· [[project_memory_relevance_pipeline]]

---
name: project_selfhost_latency_arc
description: "Single-GPU llama.cpp latency reports (#916-#920): the missing layer is client-side admission and fan-out bounds, not retries; slot thrash is cross-session."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-26T18:32:09.937Z
---

Operator field report (single-GPU llama.cpp, parallel coordinator workloads)
decoded 2026-07-26 into five issues. The report's three entangled causes:
unbounded fan-in vs server slots (N slots = parallel-decode grind + n_ctx
split; 1 slot = server-side queueing while client timeout clocks burn);
slot prompt-cache thrash from interleaved prefixes (main task ↔ search
children swap = full re-prefill each time); timeouts as the only knob.

Arc: #916 web_search resilience · #917 per-model max_concurrency (client-side
admission) · #918 coordinator fan-out bound per alias · #919 model roles map
· #920 constrained-endpoint tuning guide.

Code facts underpinning them (verified):
- `SearXNGClient.search()` = bare `httpx.get` + raise_for_status
  (web_search.py) — no retry/pacing; `CohereJinaRerankClient` same bare-POST
  shape → #916 proposes ONE shared HTTP-tool transport wrapper (also serves
  [[project_prefill_only_rerank]]'s client).
- Bundled `deploy/searxng/settings.yml` ships `limiter: false` DELIBERATELY
  (docker-internal; server limiter would 429 our own traffic) — pacing must
  be client-side. Don't file "enable the limiter".
- LLM provider retry + exponential backoff ALREADY EXISTS (session.py
  `_RETRY_BASE_DELAY` 2**attempt + cancel-aware `_backoff_or_cancelled`;
  model_turn.py jittered drain retry; `retryable_error_names` per provider)
  — so no "add retry" issue for LLM calls; the missing layer is ADMISSION
  (#917 per-process semaphore at the shared-client seam, dispatch-anchored
  timeout clocks; #918 cluster-level at the coordinator, which already
  computes a healthy-alias shortlist at dispatch, coordinator_client.py
  ~1611-1636).
- Retry N's/backoff are NOT operator-tunable (session `_MAX_RETRIES=3`/1.0s
  base; model_turn `_DRAIN_RETRIES=2`/0.5s; SDK default max_retries=2 —
  probes-only override to 0) and the three layers STACK (~12 wire attempts
  worst case; session.py:16161 comment counts it). Tunable today: tools.timeout,
  judge timeouts. NO per-model request timeout (SDK ~600s read governs) →
  #917 open questions: per-model timeout field, single-owner retries,
  constants stay fixed (exposing them recreates timeout-cranking).
- Routing prior art (piecemeal, undiscoverable → #919 groups them + adds
  spawned-child role): model.task_alias, channels.default_model_alias,
  tools.reranker_alias, perception.model_alias. "Can I do it via prompting?"
  → no; today's partial answer is model.task_alias IF the workloads are
  task_agents.
- Per-session prefix is ALREADY stable today (compose-once; the only
  memory-driven recompose is a memory DELETION — the maintainer correction
  2026-07-26). Field-report slot thrash = CROSS-SESSION interleave on one
  slot → the levers are #917/#918/#919, NOT #902. #920 body corrected;
  don't re-make the "#902 cuts their cache purging" claim —
  [[project_902_memory_index]].

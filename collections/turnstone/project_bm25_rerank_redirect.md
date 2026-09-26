---
name: project_bm25_rerank_redirect
description: "Reranking or BM25 search (tool/skill/memory): SHIPPED #627-#629, BM25 recall then rerank; payoff = thresholdable floor on proactive memory injection."
metadata: 
  node_type: memory
  type: project
---

**SHIPPED, all three phases, 2026-06-01.** After the web_fetch reranking experiment
failed (see [[project_reranker_backend_design]]), the reranker's real home turned out to be
the surfaces that already use **BM25** (`core/bm25.py`, pure-Python Okapi) — tool
search, skill search, memory composition — where reranking is the textbook use case:
ranking MANY discrete items where lexical BM25 misses semantic/synonym matches. It
needs no pgvector, embedding store or indexing pipeline.

**Architecture (design locked, still current):** `BM25Index` gains an optional
injected `reranker` (constructor arg, per-instance, default None); `search()` goes
two-stage when present — BM25 recall top-N (`_RERANK_POOL`=50) → rerank → top-k,
native-order fallback. `Reranker = Callable[[str,list[str]],list[int]]` lives in
`rerank.py` (shared by web_search + bm25, keeps bm25.py import-pure). All 3 surfaces
wired: tool search (`ToolSearchManager`), skill search, memory (`score_memories`).
Toggles are coarse (`tools.rerank_bm25` bool, default True) — per-surface bools
never needed.

**The FLOOR = the actual payoff for memory.** BM25 always returns *something*
(≥1 shared token → nonzero) and its scores aren't comparable across queries, so
proactive memory injection was structurally stuck shipping top-k-of-whatever-matched.
The reranker's contribution to memory is the **score you can threshold on**, not the
reorder — `tools.rerank_bm25_threshold` (0-1, default 0=disabled) gates PROACTIVE
injection only, never reactive search (explicit `memory(action="search")` / tool_search
stay best-effort top-k). Floor mechanics: lives in the `_bm25_reranker(threshold)`
closure; falls back to BM25 on reranker EXCEPTION only, never on a legitimate
floor-emptied result (that's the point — inject nothing).

**Per-model calibration (Phase 2/3, the durable piece):** `core/rerank_calibrate.py`
probes labelled relevant/irrelevant query groups, auto-detects raw-logit vs
0-1-normalized scale (sigmoid-normalizes if needed), places the floor conservatively
(`max_irrelevant + 0.25*gap`), and reports "no clean separation" as a **reranker
health check** (catches mis-served endpoints — e.g. a Qwen3-Reranker missing its
required `--chat-template`). Calibration result stores on the model definition's
capabilities dict (`rerank_threshold: float`, `rerank_scale: str`,
`rerank_separated: bool` — no migration needed, `ModelConfig.capabilities` is already
`dict[str,Any]`); floor precedence is per-model calibrated value (when
`rerank_separated`) over the global `tools.rerank_bm25_threshold`. `turnstone-admin
rerank-calibrate [--apply]` CLI; create-model UI shows a ✅/⚠️ health chip +
re-calibrate button. **Live-validated on Qwen3-Reranker-4B** (RTX PRO 6000):
recommends ~0.33 + separated=True on a correctly-served endpoint, correctly declines
on a broken one.

**Discipline worth repeating on future retrieval work:** measure before wiring
(baseline = current BM25 ranking, measure precision@k lift on an eval set BEFORE
shipping) — the web_fetch experiment skipped this and it's why it failed quietly;
web_search reranking (#626) shipped the same way and its lift was *also* never
measured (still true as of this writing — see [[project_1_7_roadmap]] "measure
before building"). A parse-failure empty result (→ raise `RerankError` → BM25
fallback) must stay a distinct code path from a floor-legitimately-empties-it result
(→ honor, inject nothing) — conflating them was a real round-2-review gap.

**Substrate (reuse, don't rebuild):** `core/rerank.py` `CohereJinaRerankClient` (+
`RerankHit`, `resolve_rerank_client`); `tools.rerank_url/model/api_key` +
`tools.reranker_alias` settings; Reranker model role (`supports_rerank` capability);
`ChatSession._resolve_rerank_client`; `core/rerank_config.py`
`resolve_rerank_client_from` (DRY across session/CLI/admin). Local test endpoint
recipe: [[project_reranker_backend_design]].

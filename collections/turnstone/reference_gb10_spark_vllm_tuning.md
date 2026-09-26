---
name: reference-gb10-spark-vllm-tuning
description: "Tuning the 3-model vLLM+LiteLLM stack on the GB10 DGX Spark (deploy/vllm-litellm/): drop page cache and start models sequentially, else KV starves."
metadata: 
  node_type: memory
  type: reference
---

Validated 2026-06-22 on the GB10 box (NVIDIA GB10 DGX Spark, ~121 GiB unified): three vLLM models co-resident on ONE GPU behind LiteLLM (dual-route, see [[feedback_vllm_messages_api_default]]) — qwen (reasoning, full 256K, util 0.50) + gemma-4-12B-it (perception, full 131072, util 0.24) + Qwen3-Reranker-4B (direct /rerank :8002, util 0.10). ~117/121 GiB used.

**Updated 2026-07-05** (commit `4428e185`, `deploy/vllm-litellm/` = source of truth, re-grep before quoting exact flags): qwen switched from `Qwen/Qwen3.6-27B-FP8` to **`nvidia/Qwen3.6-27B-NVFP4`** (FP4 4-bit, ~13.5 GiB weights — well under FP8's footprint, leaving more headroom for KV at the same util 0.50) and MTP `num_speculative_tokens` bumped **1→2**. The old decode-speed/acceptance numbers below (7.9→12.8 tok/s, ~84%) were measured on the FP8/1-token config; the repo dropped them (not replaced) when it switched, so treat them as historical — no re-measured NVFP4+2-token numbers published yet.

Tuning levers (hard-won, in priority order):
- **Drop page cache before `vllm` start** (`sudo sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches'`): on unified memory vLLM profiles against FREE mem; a warm cache makes it under-provision KV (qwen went 6.5→40 GiB KV after a drop).
- **Sequential startup** (each model fully healthy before the next; drop caches BETWEEN each): simultaneous starts race for memory and starve whichever profiles second ("available KV 0.45 GiB" despite free RAM). Enforce via compose `depends_on: condition: service_healthy`.
- **runai_streamer on the BIG model ONLY**: `--load-format runai_streamer` cuts qwen weight-load dramatically (pkg already in vllm/vllm-openai:latest; previously measured ~26x, 166s→~1s, on the FP8 checkpoint — not re-measured on NVFP4). BUT its streaming buffers add memory that breaks small models' tight KV budgets → gemma/reranker hit "No available memory for cache blocks". Keep the default loader on small models.
- **MTP spec-decode** for qwen3.6 (model_type `qwen3_5`, has a built-in MTP head — `mtp_num_hidden_layers:1`): `--speculative-config '{"method":"mtp","num_speculative_tokens":2}'` (bumped from `1` on 2026-07-05), no draft model. Also bump `--max-num-batched-tokens` to 8192 (vLLM warns 4096 is suboptimal with spec-decode).
- **`--max-num-seqs`**: default bumped 2→8 (2026-07-05) — a scheduler limit, not a memory allocator; raises concurrent-request throughput independent of weight format.
- **Compile cache volume mounts** (added 2026-07-05): mount `triton`/`torch-inductor`/`flashinfer` cache dirs (`TRITON_CACHE_DIR`, `TORCHINDUCTOR_CACHE_DIR` env + matching volumes) so JIT-compiled kernels survive container restarts instead of recompiling on every `up`.
- qwen 0.50 default-KV holds full 256K. `--kv-cache-dtype fp8` (halves KV) was **removed from the default compose 2026-07-05** ("default fp16 is fine at 0.50 util" per the commit — NVFP4's smaller weight footprint left enough headroom); still available as a manual vLLM flag if you need the reserve, just no longer in the shipped config.
- gemma-4 uses `sliding_window:512` → 131072 KV is cheap. gemma-4-E4B (`gemma4_audio`, ~12 GiB) is the small-perception option (floor ~util 0.14, below that = no KV); 12B (~24 GiB) is the quality one. Reranker-4B (~6 GiB) beats 8B (~13 GiB) for fitting alongside the 12B.
- Model provisioning convention: serve by HF id with a mounted `HF_HOME` cache (deepseek-v4-flash/run.sh pattern), or local dirs under ~/models (GB10 box) / /mnt/models (2-GPU box).
- ROCm/Strix Halo path (separate, untested-on-hardware guidance in the same README) simplified 2026-07-05: now just swap `QWEN_MODEL=Qwen/Qwen3.6-27B-FP8`, replacing the previous BF16-plus-manual-max-model-len-and-loader-tweak dance.

---
name: reference_small_model_repro_without_gpu
description: "Reproducing a small-model bug without a GPU: llama.cpp llama-server on a CPU-only cloud box, turnstone-eval flags that give real rates, speeds, baseline venv, hosted models."
metadata:
  type: reference
---

Recipe from reproducing a Nemotron-3-Nano-4B attachment bug in a CPU-only cloud session (4 cores,
15 GB RAM) on 2026-09-28 ([[project_attachment_framing_small_models]]). Speeds are from that box.

## Local model server

- Build only the server target:
  `cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DGGML_NATIVE=ON -DLLAMA_CURL=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF`,
  then `cmake --build build --target llama-server -j4`.
- Weights: the vendor's GGUF repo (`nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF`, `Q4_K_M`), downloaded
  with `curl -L` from its `resolve/main/` URL.
- Serve: `llama-server -m <gguf> --jinja -c 32768 -t 4 --parallel 1 --host 127.0.0.1 --port 8089`.
  `--jinja` applies the model's own chat template, which tool calling needs.
- The 4B read the prompt at about 36 tokens/s and wrote 6-8 tokens/s. Turnstone's system prompt
  and tool schemas are about 9.4K tokens, so the first turn took about 4.5 minutes; later runs
  reused the server's cached prefix.
- A dense 27B does not fit this box well: Q4_K_M (about 16.5 GB) exceeds the RAM, and a sub-4-bit
  quant would still cost roughly 7x the 4B's compute per token (estimate, never timed). Use a
  hosted OpenAI-compatible endpoint for mid-size models.

## Running the eval

- `turnstone-eval <suite>.json --base-url http://127.0.0.1:8089/v1 --model <name> --context-window 32768 --max-tokens 4096 --test-timeout 3000 --no-fast-fail -v --output res.json`.
- Pass `--no-fast-fail` whenever you want rates. Fast-fail skips a case's remaining runs once its
  first ceil(n/2) runs all score 0 and records the skipped runs as 0, and a run that trips a
  `forbidden_actions` entry scores 0 even when its answer is right.
- A case's own `n_runs` overrides `--n-runs`; write per-case suite files to vary run counts.
- Hosted models: a base URL other than api.openai.com resolves to the `openai-compatible` Chat
  Completions lane, so `--base-url https://openrouter.ai/api/v1 --model <vendor/model>` works with
  the key in `OPENAI_API_KEY`. `--parallel 5` sped hosted sweeps up.
- Before/after comparisons: check the baseline out in a `git worktree` with its own venv.
  `PYTHONPATH` does not override the main checkout's editable install, so a shared venv runs the
  new code in both arms.
- Tally clean / recovered / failed, not the pass rate alone: `forbidden_actions` scores a recovered
  run 0, so the pass rate cannot tell a model that recovers from one that fails.

## Session hygiene

- `pkill -f <pattern>` also matches the shell running it when the pattern appears in its own
  command line, and kills the tool call (exit 144). Kill recorded PIDs, or anchor `pgrep -f '^…'`.

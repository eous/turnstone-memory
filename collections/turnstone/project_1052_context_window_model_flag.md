---
name: project_1052_context_window_model_flag
description: "#1052 context_window=0 falling to 32768: IMPLEMENTED on fix/1052-context-window-bootstrap-flags; bootstrap flags gone; 0 = table, probe, else 32768+warn."
metadata: 
  node_type: memory
  type: project
  modified: 2026-09-04T03:32:00.676Z
---

Issue #1052 (context window falls back to 32768 when `--model` is given) was
scoped on 2026-09-03; full scope in local note
`docs/design/1052-context-window-model-flag.md` (never committed).

The maintainer's rulings: fix it, remove `--model` (2026-08-24 on the issue), and **remove
`--base-url` too** (2026-09-03: it is legacy code from the pcode era, and config.toml and the DB
registry are the model sources). So the server drops the whole bootstrap trio plus `[api]`; the
loader keeps its parameters for the CLI.

Findings that justify it: Helm and Terraform already pass no `--base-url`
(their `TURNSTONE_LLM_BASE_URL` env is read by nothing); systemd passes none;
only compose and the OpenShell docs use it. `_user_specified_model` is dead.
Three defects: D1 `--model` → 32768; D2 `0` models inherit the bootstrap
endpoint's window; D3 degraded boot silently 32768 for every `0` model.

**Why:** the admin UI already resolves 0 from the provider static table at
form time, so the loader must match it or the UI promise is false.

**How to apply:** The maintainer's ruling 2026-09-03: dropping inheritance does not mean dropping
the boot probe — 0 means auto-detect IF POSSIBLE. Chain in `_resolve_context_windows` (shared by DB
and `[models.*]` paths): capability table for anthropic/openai/xai/google (provider default for
unlisted models) → per-definition `/v1/models` probe of the definition's OWN endpoint for
openai-compatible/anthropic-compatible (parallel threads, successes cached per process so hot-reload
never re-probes, misses retried) → 32768 with a warning naming alias + reason.
`detect_context_windows=True` from server boot, hot-reload and CLI; default False keeps unit tests
offline. Branch off origin/main (user issue). Follow-up CLI issue filed: #1085. Server's `"dummy"`
key fallback goes away, so `_get_client_locked` must give openai-compatible / anthropic-compatible
an empty-key placeholder or vLLM users hit the SDK's missing-key error. Warn when a `[models.*]`
entry omits base_url while `[api].base_url` is still present (silent retarget to commercial API).
`turnstone.example.toml` `[models.local]` uses `name =` but the loader reads `model =` — fix in the
same PR. Follow-up issue: CLI still has the trio and passes no storage to the loader (never sees DB
models). **Review-round rulings (2 rounds at `high`, 10 findings each, all fixed):** R1: placeholder
key must respect env precedence (explicit → SDK env var → `dummy`), so it lives in `create_client`
for LOCAL_PROVIDERS, not the registry; probe is endpoint-only (`static_table=False`) so a local
server serving a commercial id never inherits the OpenAI table; no success cache (re-probe every
load, per the auto-detect-if-possible ruling); reload passes `allow_empty=True`; doctor resolves
from the registry alone (no `[api]`/env). R2: `create_client("openai-compatible", base_url="")`
raises like the anthropic-compatible arm (sink-level fail-closed; DB rows and `${VAR}`→"" included);
unlisted commercial ids → FALLBACK + warning, never the provider default (200k/2M guesses hard-fail
turns); probe miss on hot-reload carries forward the running registry's window
(`prior=registry.models`, same provider/base_url/model) so a backend mid-restart never shrinks live
sessions; one 10 s wall-clock deadline per probe pass (`wait()` + `shutdown(wait=False)`); console's
three loads + doctor pass `detect_context_windows=True`; admin API create omission default 32768→0;
CLI keeps its old inheritance (loader `context_window>0` → every 0-entry inherits) so cli.py has NO
diff — #1085 retires it. Kept as-is with reasons: llama.cpp `n_ctx_train` overestimate (pre-existing
on main's bootstrap detect; `/props` would be the fix), per-alias probes not grouped per endpoint.
R3 (10 more; simplified per [[feedback_nonconverging_reviews_mean_simplify]]): `prior` consulted
BEFORE probing (same provider/base_url/model and a non-fallback window → reuse, no network) so
steady-state reloads probe nothing; post-miss carry-forward and the pool-abandon/`wait()` deadline
machinery deleted; each probe runs via `run_with_deadline` (daemon thread, deadline.py) so a wedged
resolver can't pin exit; pool sized to N (cap 32); table branch before the CLI's inherited window;
rerank-only defs take FALLBACK silently; entry with base_url key present but resolving empty (unset
${VAR}) skipped; node reload serialised by `_MODEL_RELOAD_LOCK`, `strict=True`, generic except → 503
keeps the running registry; console create/update 400 for a local provider without base_url; doctor
`set_config_path` to the first discovered config with `[models]` and `ConfigFileInfo.api` deleted.
R4 (10 again; cheap+correct ones taken, then STOPPED per trend 10/10/10/10):
`ModelConfig.context_window_detected` provenance flag gates prior reuse (explicit→0 switch
re-probes; detected 32768 reused); probe catch-all → miss; local rows/entries without base_url
skipped in BOTH loader branches; `provider="openai"` + no base_url + `[api].base_url` present →
skipped; console update guard presence-keyed and aware of openai+local-host rows; reload 503 reason
= exception type only; doctor consults discovered config only when `load_config()` is empty. NOT
done (report to the maintainer): 5th review round, `.env.example` (permission-gated), per-endpoint
probe grouping, console bootstrap re-probe when coord bootstrap keeps failing, `_metrics.model`
stale after live-added models (pre-existing). Review (2026-09-04): 6 items; applied 5 + the DB half
of #1 (probe-first restored with detected-prior carry-forward on a miss — my R3 prior-first was an
over-correction; DB row `${VAR}`→"" skipped; doctor gate `load_config("models")`; Detect route
`static_table=False` for LOCAL_PROVIDERS; identical-identity probes deduped, pool cap 16; Helm NOTES
key warning removed). DECLINED: fail-closed for anthropic/xai/google entries without base_url (empty
= SDK default, common CLI shape) → warning only. `.env.example` still the maintainer's
(permission-gated). The maintainer's live bug (2026-09-04): OpenRouter `openai/gpt-5.6-luna`, ctx 0
→ 32k. Cause: `_extract_context_window` read only vLLM `max_model_len` and llama.cpp
`meta.n_ctx_train`. Endpoint key MATRIX now handled: `max_model_len` (vLLM/NIM/SGLang),
`context_length` (OpenRouter verified live at 1,050,000 + `top_provider.context_length`; Together,
Fireworks), `context_window` (Groq), `max_context_length` (Mistral), `meta.n_ctx_train` (llama.cpp).
NOT detectable on the OpenAI path (explicit value or 32768+warning): Ollama (`/api/show`), LM Studio
(`/api/v0/models` max_context_length), LiteLLM (`/model/info`), DeepSeek, Gemini's compat path.
Groq/Mistral/Together/Fireworks keys are from API knowledge, not verified live (need keys). The
maintainer UX ruling (2026-09-04): when admin Detect reaches the endpoint but gets no window, the
form is FILLED with the fallback (32768, via the detect endpoint's `fallback_context_window`) and
told so — never leave 0 looking like "auto-detect will handle it" when the node would silently run
at 32k. Unreachable endpoint → field untouched (transient). No admin.js harness tests exist; the
contract is pinned at the endpoint level only. Cloud paths (Azure deployments, Bedrock/Vertex
OpenAI-compat, OCI, Databricks) report no window on the OpenAI path → explicit value; future: native
Gemini `models.get` → `inputTokenLimit`. See [[project_cli_origins_forgotten_child]],
[[feedback_minimal_scope_first]], [[feedback_helm_chart_design_ownership]].

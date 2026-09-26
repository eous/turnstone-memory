---
name: project_judge_completion_interlingua
description: "Judge or out-of-session completion callers (#827/#831/#837): Turn IR through model_turn, never hand-built OpenAI dicts; sampling = alias > config > def > omit."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-20T17:01:50.364Z
---

## Current state (2026-09-05 header)

- Status: #826 capability threading SHIPPED 2026-07-12 (closes #823); #837 (both judges on Turn IR, Gemini tool-skip deleted, one sampling scheme) SHIPPED 2026-07-13 with the maintainer's live smoke passed; Phase 3 transport collapse (#831, `create_completion` deleted, shared drain) pushed as PR #841 after being declared converged in substance at round 9 (suite 9,325). Next phase = #832, the main loop onto model_turn — see [[project_832_main_loop_fold]].
- The maintainer's rulings: ONE sampling assignment scheme — alias > stored config > in-code model definition > omit; no judge-specific temperature knob; `model.temperature` default is an unset sentinel and effort "" means inherit; the utility/guard `default_reasoning_effort="low"` carve-out was killed; the ""→inherit flip and old 0.5/"medium" fossils are release-note only; ship gate for that branch was PR-after-round-3 unless a major refactor.
- Durable design: judges (judge.py, output_guard_judge.py) were the only create_completion callers outside ChatSession, and the hand-built OpenAI-dict shape is a lossy interlingua (it made the Gemini judge tool-blind); Turn IR + shared lowering is the single interlingua, and providers keep taking lowered wire dicts (lowering.py owns wire mutation).
- Phase-3 mechanisms: operator-declared `finish_reason_optional` capability (default STRICT), id-disciplined tool-call slotter, model_turn drain-scoped retry with jittered backoff, `accumulate_tool_call_delta` as the one merge rule, under-streaming gateway parity on both lanes.
- Open as of 2026-07-13: 1c Gemini live validation (the maintainer on GCP; explicitly not a push blocker); o-series retired-id rows and StreamAbortRef/_CancelRef unification held for #832.

---

The intent judge (`turnstone/core/judge.py`) and output-guard judge (`turnstone/core/output_guard_judge.py`) are the **only completion consumers that live outside `ChatSession`**. Consequence: `self._resolve_capabilities` / the Turn→wire lowering path never reach them automatically, so they historically diverged from every other lane.

**Capability threading — shipped in #826 (2026-07-12; closes #823).** The judges never passed model-definition capabilities into `create_completion`, so operator-declared caps (effort passthrough, tool support, temperature, verbosity) were silently ignored on judge calls. Fix: shared `_resolve_model_capabilities(provider, model, cfg)` helper in judge.py (mirrors `ChatSession._resolve_capabilities`); both judges resolve `self._capabilities` (alias → `model_cfg`; fallback → injected `session_capabilities`) and pass `capabilities=`. Constructor arg `context_window: int` → `session_capabilities: ModelCapabilities`. **Window landmine:** `_resolve_capabilities` merges the `capabilities` JSON dict but NOT `ModelConfig.context_window` (a separate top-level field); the alias path must keep reading `model_cfg.context_window` (static caps table reports a generic window for local models). Window-fallback and wire-caps-fallback are decoupled — window trusts only passed caps (floor otherwise), never `get_capabilities()`.

#823 (the reporting issue) is **resolved by #826**; its second cause (evidence tools sent to models without tool support) has the operator lever `judge.read_only_tools = false` → judge runs single-shot (tools=None), and the proper capability-gated fix rolls into #827.

**Interlingua — issue #827.** The judges build raw OpenAI Chat-Completions dicts (`{role,content}`, assistant `tool_calls[]`, `role:"tool"`+`tool_call_id`) and rely on each provider's `create_completion` to lower them (Anthropic `_convert_messages`, Responses `_build_kwargs`, openai-chat native). This OpenAI-dict shape is a **lossy de-facto interlingua** — it can't carry provider-native reasoning/signatures. Concrete symptom: `judge.py` skips evidence tools when `provider_name == "google"` because Gemini needs `thought_signature` round-trips that normalized `tool_calls` drop → **Gemini intent judge runs single-shot/tool-blind**. #827 = migrate out-of-session callers (judges, `perception.py`, audit eval/optimizer) to Turn IR + retire the legacy OpenAI-dict path so there is ONE interlingua. Relates to [[project_harness_interlingua_frontier]], [[project_intent_verdict_lifecycle]], [[project_task_agent_id_consistency]] (tool-id maps).

**Convergence log (2026-07-13):** xhigh #2 (branch-wide) → 7 correctness (temperature-omission was a
hidden provider-signature 0.5 pin; fixed via `float | None` omit-on-None through Protocol+adapters,
ConfigStore global rung, perception/optimizer lane threading). high round 1 → 3 correctness; **The
maintainer's rulings**: NO judge-specific temperature knob (judge alias per-model override is the
path); `model.temperature` SettingDef default 0.5→**1.0**; agent seam keeps alias ladder (configured
→ global → none); **reasoning_effort de-pinned everywhere too** (ladder:
ModelConfig.reasoning_effort → model.reasoning_effort setting → caps.default_reasoning_effort;
terminal = caps default NOT wire omission — effort gates thinking modes, unset ≠ "none"); optimizer
relays its --temperature/--reasoning-effort CLI flags into all 5 internal lanes. Wire goldens
regenerated (only drift: temperature 0.5 pin vanishing). **high round 2** (review run; survived
session compaction — task handle lost, watched via run-dir mtime): 25 survivors → 10 reported (cap),
mined — 7 dropped all-cleanup, accounting clean. 8 correctness, headline = round-1 fix collided with
ConfigStore.get default-on-miss (registry defaults 1.0/"medium" manufactured onto every store-backed
lane; "unset→omit" terminal unreachable). **The maintainer's ruling → ONE assignment scheme: alias >
stored config > in-code model definition > omit** (sampling pinned at 0.5/0.0 is long obsolete; OSS
models fall OOD < 1.0; alias path is the remediation for models needing specific temps). Fix
`41ea9969`: SettingDef defaults = unset sentinels (temp None nullable, effort ""); shared
resolve_temperature_setting/resolve_effort_setting used by resolve_lane + both factories + /model
switch (4-copy mirror gone); caps rung moved into model_turn below new request-shaped
`default_reasoning_effort` param (utility+guard pass "low" — budget coherence, preserves the
2026-06-27 "low stays" convention; loses to any operator/model-def value); Protocol+adapters effort
`str|None=None` (Protocol "medium" was the same pin one layer down);
ModelCapabilities.default_reasoning_effort ""→ Anthropic manual models no longer implicit
thinking-on-medium; optimizer meta-lanes decoupled from test knobs; CLI 0.5/"medium" pins → unset;
_run_agent same-alias-only session-knob relay (both directions). **Follow-up ruling killed the
utility/guard `default_reasoning_effort="low"` carve-out** (`bfce0730`): local lanes have no defined
effort vocabulary/floor → NO caller-default rung exists; titles cope via `_TITLE_MAX_TOKENS` 8192 +
hard 3-word prompt max, guard degrades visibly (alias-effort remediation). Round 3 was stopped
mid-flight for the caller-default removal (freeze rule) and relaunched fresh. **SHIP GATE ADJUSTED
(the maintainer, 2026-07-13): PR after round 3 unless major refactor** — strict 2-consecutive-clean
dance off for this branch (sampling yak-shave incidental to the Turn IR mission). **Round 3: 14
verified → 10 distinct, 6 correctness, 0 dropped** — theme: incomplete scheme rollout. Fixed in
`47731ec7`: main loop now applies the caps-def effort rung (same-alias sampling parity + unblocks
gpt-5.x operator temperature); coordinator.reasoning_effort default → "" (missed sentinel); admin
blank-save reachable (dirty-detection gate exempted data-nullable); /model on STORE-LESS sessions
keeps explicit CLI knobs (store-backed re-resolves); ModelLane docstring, CLI status medium-hide,
dead alias, 3 stale test docstrings. **The maintainer's migration rulings: release-note ONLY for
both** the ""→inherit semantic flip (none = off switch now) and the 0.5/"medium" workstream fossils
(age out on next knob/model change) — CHANGELOG Unreleased→Changed carries both upgrade notes.
**#837 shipped 2026-07-13** (post-merge CI note: test-postgres hit its 20-min timeout once on an
IO-starved runner — 0 test failures, rerun passed in 9m38s ≈ main's baseline; diagnosis method:
per-file timing diff vs a main run, pure-CPU files x1.0 / DDL files 12x = infra). Copilot +
claude-review both zero-findings. Remaining at that date: 1c Gemini live validation; #831 in
progress; #832 future. **Live smoke PASSED (2026-07-13):** The maintainer ran a small real session
on the branch (tool calls + intent judge + output guard) — visually correct end-to-end. Covers the
default-provider lane only. **1c is explicitly NOT a push blocker** (the maintainer, 2026-07-13):
the Gemini evidence-loop and manufactured-id validation were deferred. Verify later evidence before
treating that provider path as live-validated. Push gate = review convergence alone.

**Phases 1a+1b LANDED on `feat/model-turn` (2026-07-13, unpushed):** `adccd3e2` (model_turn extraction, agent seam) + `b64b6b99` (both judges on Turn IR, Gemini tool-skip deleted, #826 mirror deleted) + `1e98a50a` (xhigh-review fix round: temperature pins removed per [[feedback_never_pin_temperature]]; `session_model_alias` threaded so fallback judges resolve like session lanes; pairwise blank-id native repair — see [[project_task_agent_native_lane]]; mint-requires-map guard; single-fetch `_get_config_or_none` lane resolution; dead wrapper deletions). Full suite 9249 green; xhigh review = 14 findings (19 kept, 0 cap-dropped), all addressed; delta review of the fix round pending. Remaining: 1c Gemini live validation (incl. manufactured-id signature acceptance), phases 2–4.

**Scope EXPANDED (the maintainer, 2026-07-12): eliminate `create_completion` entirely**, not just migrate its callers — the method (name + OpenAI-dict `messages` signature) is legacy from the openai-chat-only era. Two orthogonal axes: (a) caller-side interlingua (hand-built OpenAI dicts → Turn IR + shared lowering), (b) provider-side transport (dual `create_streaming`/`create_completion` per adapter → single streaming entry + shared drain). Inventory (2026-07-12): tool-loop callers = judge.py:1377 (hand-built dicts, THE target), eval/core.py:318 (already stores Turn IR via `turn_from_dict`), session.py:15368 task agents (already the full Turn-IR seam: `dicts_from_turns`→`sanitize_tool_call_arguments`→`restore_provider_tool_ids`→`_maybe_attach_vllm_chat_reasoning` — post-#825 this is the TEMPLATE to extract); single-shot callers = output_guard_judge.py:504, perception.py:76 (OpenAI content-parts, no dialogue), session.py:5038 `_utility_completion` (3 internal callers), optimizer.py ×5 (live entry point `turnstone-optimizer`). De-risking facts: Anthropic's `create_completion` ALREADY drains a stream internally (SDK 10-min timeout workaround) — the drain pattern is proven; `StreamChunk` carries provider_blocks+usage+finish_reason+reasoning_delta = everything `CompletionResult` needs; Google adapter already round-trips `thought_signature` via provider_blocks in `_prepare_messages`, so the Gemini judge fix falls out of giving judges the native lane. Recommended phasing (3 PRs): (1) extract agent seam → shared completion harness, migrate both judges, delete Gemini tool-skip, live-validate Gemini judge = closes #827-as-filed; (2) migrate single-shots (utility/perception/eval/optimizer) — after this zero hand-built-dict callers; (3) collapse transport at the harness choke point (drain `create_streaming`, delete `create_completion` from Protocol + 3 adapters + xai/google inheritors) — big test churn (~22 test files mock create_completion), zero caller churn. Providers KEEP taking lowered wire dicts (don't move Turn IR into the Protocol — lowering.py stays the only wire-mutation owner). Watch: `ModelCapabilities.supports_streaming=False` models (verify none rely on true non-streaming before phase 3); judge cancellation IMPROVES (cancel_ref can abort HTTP read vs today's abandoned deadline thread).

**Phase 3 (#831) review loop (2026-07-13, `feat/transport-collapse`, unpushed):** implementation
`93601fa5` + fix rounds `83674274`(r1) `1f58e18d`(r2) `7075be53`(r3) `2bc072e1`(r4) `745f9643`(r5) +
o-series pruning `aba46165` (the maintainer's directive; retires the thrice-reported o1-stranding
finding — see [[reference_provider_capabilities]]) + `60eceb0c`(r6). **Round 6** (fresh launch after
a voided round + a failed resume the maintainer killed): 6 correctness / 4 cleanup. Key r6
decisions: **finish shim → operator-declared `finish_reason_optional` capability, default STRICT**
(SSE can't distinguish lax-server completion from clean-close truncation; default catches truncation
— the r5 unconditional shim re-opened the data-loss hole; flag restores 1.7 tolerance per model;
reasoning counts as output when armed); **slotter v3** (id-less call boundaries via incremental
JSON-completeness scanner + name identity: zero-arg parallel calls split, redundant-name fragments
merge, name mismatch always splits); **model_turn drain-scoped retry** (2 re-issues when a
drain-time error is in the provider's `retryable_error_names` — SDK request-retry parity for every
single-shot lane; create_streaming stays outside the try since adapters issue HTTP eagerly;
abort-gated via new `StreamAbortRef.aborted`); **google raw/mirror parity now structural** (base
slotter + `on_tool_call_delta` capture hook; tap + second slotter deleted); shared
`accumulate_tool_call_delta` in _protocol (drain + google capture; session copy = #832 adoption);
Responses terminal rebuild gated to truncation/count-mismatch (annotations replaced, not
re-extended). HELD on rulings: o-series row removal (deliberate break, release-noted remediation =
capabilities JSON), StreamAbortRef/_CancelRef unification (#832, docstring mirror-mandate). **Round
7**: 6 correctness / 4 cleanup, 0 refuted — headline = r6 slotter regression (id-only slot split on
its FIRST name fragment: {id}→{name}→{args} became two broken calls). Fixed in `5396d005`:
**id-disciplined slots never split on id-less deltas** (new calls on id-sending servers arrive with
ids; heuristics apply only to fully id-less slots) + no-name-yet slots never split + bare same-name
footer after complete args merges (phantom zero-arg call would re-run side-effecting tools);
**finish_reason_optional honored on ALL lanes** (anthropic: missing stop_reason+message_stop pair;
responses: missing terminal event; blocks ride the shimmed finish — the documented capabilities-JSON
remediation was chat-lane-only and no-op'd on the LiteLLM-class gateways it was written for);
**responses post-terminal in-band error/failed frames = teardown noise** (log+break, keep completed
result — in-band twin of drain's post-finish blip tolerance); **model_turn retry backoff** (0.5s
base ×2 ±50% jitter, `_DRAIN_RETRY_BASE_DELAY` module const, tests zero it; no Retry-After to honor
on in-band failures); responses slots minted by counter not len(dict) (duplicate/empty item-id
overwrite collided call 3 onto call 2) + orphan arg deltas route to last-announced call not slot 0.
Cleanups: hook passes normalized ToolCallDelta+raw (google accumulates the mirror's exact bytes),
scanner feeds only id-less slots, anthropic retryable set hoisted, google class docstring. **Round
8**: 13 confirmed → 11 distinct → 10 reported (6 correctness / 4 cleanup; 1 refuted duplicate of the
stacked-retry-as-correctness framing). Fixed in `38f15716`: **under-streaming gateway parity both
lanes** (responses: terminal-payload-only output harvested into content/tool_calls when nothing
streamed — buffering proxies drained to clean-looking EMPTY results where 1.7's _parse_response read
the same payload; anthropic: content_block_start pre-populated text/thinking/tool-input emitted,
type-guarded like _reasoning_text — MagicMock/duck blocks must not leak non-strings, 5 tests caught
the unguarded version); **status-less response.completed payload → "stop" via event type** (empty
status read as "length", fired truncation policies on complete output — round 6 had REFUTED this
same claim; refutations are weaker evidence than confirmations); **abort-during-backoff race
closed** (re-check cancel_ref.aborted after the sleep → die with original failure, no resurrected
request); **post-finish blip forfeits usage LOUDLY now** (drain warns with usage_captured flag;
result still kept per round-4 ruling). Cleanups: session's inline fold adopts
accumulate_tool_call_delta (THE merge rule now 1 impl: chat loop + drain + google capture; exported
from providers package), _api_call comment reconciles the two retry ladders (model_turn = drain-time
re-issue only; sub-harness = request-level policy; deterministic failure burns
(retries+1)×(attempts) before remediation error), anthropic _attach_terminal_blocks helper (3
terminal paths), responses single caps resolution. HELD: o-series (4th report),
StreamAbortRef/_CancelRef (3rd report, #832). Convergence counter reframe: r8 = first
zero-mainline-real round; **The maintainer-approved decision gate → round 9 came back ALL-TAIL** (5
correctness: 2 already-ruled re-reports [usage-blip, stream_options], 1 PLAUSIBLE hybrid-gateway
double-count → documented bet, 1 stream-incapable-stranding whose population = retired ids + audio
roles [verified via `git show main`: the 8 supports_streaming=False rows were o1/o1-mini/o3-pro + 5
audio] → CHANGELOG caveat, 1 reproduced r7×r8 fix-collision [orphan deltas + terminal harvest
doubled args JSON] → fixed). **Declared CONVERGED IN SUBSTANCE per gate.** Round-9 batch `6c2e6a4c`:
orphan_args_seen gate + regression test, finish_shim_due shared predicate (3 adapters), merged
responses failure tail, _format_refusal, o-series comment/CHANGELOG reworded to RETIRED-ids
rationale, stream-entitlement caveat (verified-org, Azure api-version), architecture.md retry
section rewritten (two stacked ladders), anthropic hybrid bet documented. Issue #831 coverage audit
vs full issue text: ALL work/pre-flight/acceptance items covered; one deviation noted in PR
(CompletionResult survives as collector return type, neither internal nor dead). **Pushed as PR
#841**, closes #831. Suite 9,325 (main was 9,256). Next: #832 (main loop onto model_turn; carries
_CancelRef adoption, session merge_usage twin, retry-predicate classification, fake consolidation).

**Phase 3 (#831) discovery — 2026-07-13, branch `feat/transport-collapse` (from main @ 3742e966):** post-#837 the surface SHRANK vs the 07-12 inventory: `create_completion` has ONE production caller (`model_turn.py:697`); main loop calls `create_streaming` directly (`session.py:5153`, phase-4 territory); test churn 11 files (not 22), seam fake = `tests/_session_helpers.mock_completion_result` (docstring already plans "every suite moves together"). Deletion set: Protocol `create_completion` + 3 impls (`_anthropic:1073`, `_openai_chat:307`, `_openai_responses:672`); xai (Responses subclass) + google (Chat subclass) inherit — plus helpers that die with it (responses `_parse_response`, chat+google `_extract_tool_calls`; verify no other callers). Design: shared `drain_stream(Iterator[StreamChunk]) -> CompletionResult` at the choke point; model_turn:697 swaps to `drain_stream(create_streaming(..., cancel_ref=...))` and grows optional cancel_ref (judge deadline can abort the HTTP read vs today's abandoned thread). **Parity verified all 4 lanes**: every adapter attaches full provider_blocks exactly once at/on the terminal chunk (anthropic raw_blocks on stop chunk via same `_block_to_dict` as non-streaming; responses output_item.done model_dumps ≡ response.output; google `_tap` thought_signature dicts on finish chunk ≡ `_extract_tool_calls` model_dump; base chat = `[]` on BOTH transports). Drain rules: content/reasoning = join deltas; tool_calls = merge ToolCallDelta by index; usage/finish = last non-None; blocks = extend; info_delta AFTER finish_reason = trailing citations → fold into content (matches non-streaming `format_citations` — verify append-only), info BEFORE finish = Responses "[Searching…]" pings → drop (non-streaming never emits them). Behavior deltas to own: (1) Responses streaming drops `refusal` parts (non-streaming renders "[Refused: …]") — fix by adding refusal-delta handling to `_iter_stream`, improves main loop too; (2) chat lane gains `stream:true`+`stream_options.include_usage` — ancient local servers ignoring include_usage lose usage rows (release-note); (3) `supports_streaming` cap has ZERO readers = dead flag (False rows: o1/o1-mini/o3-pro + audio models) — propose deleting; only risk is a judge aliased to o1-era models needing verified-org streaming (release-note + alias remediation); (4) timeout characteristics IMPROVE (incremental reads vs long non-streaming POST — same reason anthropic drains internally; relevant to title-gen 8192 budget on slow local models). (durable, verified 2026-07-11; noted on #827). web_search (`_openai_chat._apply_web_search`), tool-search (`_openai_common.apply_tool_search`), and Responses `server_side_tools` (`_openai_responses._build_kwargs`, gated on `client_tool_names`) all inject a native tool ONLY when a same-named CLIENT def survived the session's persona/coordinator visibility envelope. So a `tools=None` call (judge with `read_only_tools=false`, or Gemini judge) never gets native tools injected even if caps declare them — threading caps (#826) cannot smuggle tools in.

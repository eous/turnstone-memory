---
name: project_973_no_thinking_posture_hosted_lanes
description: "#973: utility no-thinking posture is inert on hosted openai-compatible thinking lanes (DeepSeek); confirmed bug, 2-line fix; rulings: no default-high."
metadata:
  type: project
---

**State of #973 (checked 2026-09-12).** Umbrella filed 08-05; classification pass (step 1) never
done; `model_turn.py` module docstring still says "Policy-free" with three carve-outs. Transport
family rows done: cancellation #972, reasoning segregation #965, provenance #964, admission #917.
Rows remaining: retry ladders, credential binding, usage recording, deadline anchoring. Family was
one 5-day burst (08-01..08-05, ten issues) then quiet; the seam lift itself was NOT the mistake,
"policy-free" was. Open in the family: #971, #980, #973. Fourteen reasoning-related fields on
`ModelCapabilities`; thinking-off payload is tested only for the local passthrough class.

**The 09-12 comment (RedEyeNinja-BKK, returning contributor: #937→PR #967, #951, #960, PRs
#952/#953).** `lane_without_thinking` (model_turn.py) pins the chat-template toggle False inside
`chat_template_kwargs` and clears every effort rung → no flat `reasoning_effort` sent. Hosted
openai-compatible APIs never read `chat_template_kwargs`, and "omit" = server default = thinking ON.
Measured on hosted DeepSeek via proxy (server-side `reasoning_content` length): our exact "off"
payload ≈ nothing sent ≈ effort high (~700 chars); effort `"none"` → 0. **The maintainer 09-12:
confirmed bug, clear cut; stay on the reporter's variant.** This is the REASONING-CONTROL family
(#676, #807,
#940, #965, #971, #978), not the transport-invariants family; root cause = no standard off-switch
across backend classes.

**Fix shape (edges closed by direct read; NO dataflow-mapper needed — the maintainer agreed).**
`lane_without_thinking`: `reasoning_effort="none"` instead of `None`; delete the now-dead
`default_reasoning_effort=""` clear. `resolve_reasoning_effort` already forwards `"none"` ONLY where
the row declares a `none` level, omits elsewhere (passthrough boxes never see an invented token);
Responses surface shares the resolver; Anthropic/anthropic-compat treat `"none"` ≡ unset; xAI/Ollama
outside `EXTRA_BODY_PROVIDERS`; derived lane is call-scoped in `_utility_completion`; result/provenance
carry no effort. ≈2 logic lines, ≈80-line diff: docstrings (~20), two tests flip `is None`→`"none"`
(`tests/test_session.py` ~12811 `test_utility_completion_asks_a_passthrough_backend_for_no_reasoning`
and `..._suppresses_effort_on_toggle_less_passthrough`) — arm B must go through REAL chat-provider
shaping so "passthrough box sees no param" stays a wire fact; one new test: row declaring `none` →
wire carries `reasoning_effort: "none"`. Omni transcription (audio.py raw client) out of scope.
PR body must state the temperature delta (below). **Fix is INERT for hosted DeepSeek without a
declared values list** → pair with a built-in DeepSeek capability row (none present today; Detect
profiles match only `deepseek-r1`). Reporter's Q2 answers itself: no new capability field, the
declaration IS `reasoning_effort_values`.

**Open decision (the maintainer, 09-12):** who writes it — reporter offered a PR; or I build on a
fresh worktree (this checkout is mid #1147 MCP shutdown). Suggest reply on #973: invariant, accept
PR, ask for a separate issue so #973 stays the transport umbrella.

**DeepSeek effort facts (verified 09-12, api-docs.deepseek.com + recipes.vllm.ai).** Hosted API:
`reasoning_effort` string enum `none|low|high|max`, default `high`, thinking on by default;
`minimal`→`low`, `medium`/`xhigh`→`high` for compat; top-level `thinking:{type:enabled|disabled}`;
NO numeric scale. Open weights on vLLM (V4.1-Flash): `chat_template_kwargs` `thinking`/
`enable_thinking` bool + `reasoning_effort` named tier OR int 1-100 (low=25, high=50, xhigh=75,
max=100; unset = on at 50); top-level field works, `none` disables, **`minimal`/`medium` REJECTED**
(doc claim, not verified on V4.1 hardware). Our passthrough default forwards the knob verbatim →
operator `medium` would 400 on vLLM V4.1 unless values declared. Numeric 1-100: NOT supported as a
knob (fixed 7-string ladder); only a static `server_compat.extra_body` pin. **Decision: don't build
numeric; a DeepSeek capability row does more good.** The maintainer's "0-100" recollection was the
vLLM template, not the hosted API.

**Temperature-gate smell (found 09-12, unfixed, no test pins it; from b6391d1f 07-13).**
`apply_temperature` (_openai_common.py) withholds temperature when `"none" in
reasoning_effort_values and effort != "none"` — vocabulary inference standing in for "OpenAI
GPT-5.1+ rejects temperature while reasoning". Correct today only because just the GPT-5.4–5.6 rows
declare `none` (grok-4.3 declares it but xAI doesn't share the gate). Any non-OpenAI row declaring
`none` (the DeepSeek row; the reporter's operator declaration) silently withholds the operator's
temperature on every thinking turn — DeepSeek accepts temperature with thinking on. Violates
[[feedback_operator_ui_plain_language]] (value reaches wire verbatim or visibly snapped). Fix:
explicit flag on GPT-5.1+ rows (e.g. `temperature_requires_reasoning_off`), ~10 lines + test; land
BEFORE the DeepSeek row ([[feedback_pattern_propagation_sequencing]]). Newest rows (pro, o-series,
search, gpt-6-astra) already `supports_temperature=False` — the maintainer's observation that newer
models don't accept temperature is encoded. Anthropic side: thinking on forces temperature 1.0
(_anthropic.py ~525).

Related: [[project_917_per_model_admission]] (why #973 was filed), [[project_965_reasoning_seam]],
[[project_832_main_loop_fold]], [[feedback_never_pin_temperature]] (reaffirmed 09-12),
[[feedback_measure_before_accepting_a_finding]] (reporter's probe IS the measurement).

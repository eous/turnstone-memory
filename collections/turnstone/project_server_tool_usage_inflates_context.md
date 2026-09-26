---
name: project_server_tool_usage_inflates_context
description: "Anthropic web_search reports cumulative input across server iterations; read as context size it spikes the gauge, poisons calibration and forces compaction (09-18)."
metadata:
  type: project
---

**Finding (2026-09-18, the maintainer's ws `f2ec5ec0`, Fable lane, 200k window):** one assistant
turn ran 4 native `web_search` iterations server-side (4 `server_tool_use` blocks in
`provider_data`). Anthropic's `message_delta` usage summed the input across all 5 sampling
iterations: prompt 159,968 = 12 uncached + 50,586 cache_creation + 109,370 cache_read, while the
real single-pass context was ~50k (next call reported 49,908). Docs confirm: "Web search results ...
are counted as input tokens, in search iterations executed during a single turn". `_anthropic.py`
folds `inp+cc+cr` into `prompt_tokens` verbatim; nothing reads
`usage.server_tool_use.web_search_requests`.

**Downstream damage in that session (all from `usage_events` + `conversations` rows):** status bar
showed 160k/200k; `_update_token_table` calibrated chars_per_token ~3x too small; the estimate hit
166k -> `_remaining_token_budget()` went to zero -> the `web_fetch` result was DROPPED ("context
budget exhausted", 2050 chars lost) -> zero-budget auto-compaction fired on a two-message conversation
(marker before_tokens 166,226, after_tokens 169,149: the summary was estimated with the poisoned ratio,
so compaction *raised* the number). Next real call reported 49,908 and the gauge "returned to normal".
Second incident same evening: ws `b443576d` (spikes 134,622 / 175,794, compaction at 23:34Z).

**Ruled out:** the client-side `web_fetch` extraction call (`_utility_completion` -> `model_turn`
`on_completed` -> `on_aux_usage`) never touches `_last_usage`, `on_status`, or the estimate. Only
`_StreamTurnConsumer._publish_chunk` (main loop) and the compaction rewrite write `_last_usage`.

**Live-validated 2026-09-18 (the maintainer authorized the live run):** the opening `message_start`
usage is the FIRST sampling pass only; ONE `message_delta` closes the message with `input_tokens` and
`cache_creation_input_tokens` covering all NEW content across passes, but `cache_read_input_tokens`
ACCUMULATED across passes (billing total). Cached probe, 3 searches: start 4/132/23,745 (inp/cc/cr) ->
final 6/30,040/47,622; Turnstone fold = 77,668; true next-call context (real follow-up) = 54,392.
Uncached probe: final input 35,546 vs true 33,083 (no inflation without caching). Plain response: the
delta REPEATS start's input counts exactly. `usage.server_tool_use.web_search_requests` is present.
`count_tokens` rejects server tools (400).

**Fix BUILT 2026-09-18 (first version, PR #1193, on dev 09-19 as f1727e98 + harness commit 5291652d); unified rule = PR #1196 from branch fix/server-tool-usage-unify (cut from the new dev; the old branch still carries a dangling duplicate commit 3d3134b6)** (one /review round, approved with
suggestions): the adapter derives context = opening total + max(0, input delta) + max(0,
cache_creation delta) ONLY once a `server_tool_use` block appeared (every other stream keeps the
old fold); new `UsageInfo.served_prompt_tokens` (0 = same as prompt_tokens, max-merged) carries what
the request sent, and `_update_token_table` / `PromptTokenEstimator.observe` calibrate
chars-per-token on it while the anchor keeps prompt_tokens. Evidence + probes:
docs/design/server-tool-usage-probe.md (local-only).

**Deferred design items (the maintainer decides; not fix-branch material):** (1) `_msg_text_chars`
never counts `_provider_content` blocks, and on the Anthropic wire they REPLACE `content`, so every
later turn holding search results calibrates chars-per-token ~2.3x low until compaction: needs a
persisted per-turn token charge for opaque blocks, treated like the image charge. (2) Spend
consumers (`_update_token_budget`, `_ws_prompt_tokens`, `usage_events.prompt_tokens`) read the
context figure on server-tool turns; the reviewed remedy is a `billed_prompt_tokens` field + its own
usage_events column (never repurpose prompt_tokens: the latest row doubles as the saved-list
occupancy ratio). Also pre-existing: tests/test_livepass_workspace_id.py times out on the dev tree
on this machine.

**Live one-off through the SHIPPED adapter 2026-09-19:** search turn reported context 54,215 vs
measured next-call 54,780 (1% under); old fold would have been 78,086+ (43% over); plain call keeps
the fold (gate off). Issues: #1188 opaque-block charge, #1189 billed input column, #1190 compaction
guard, #1191 OpenAI Responses verification, #1192 web_fetch thinking spend.

**OpenAI Responses lane VERIFIED 2026-09-19 (astra alias, gpt-6-astra):** same class, 2.04x (22,508
reported vs 11,052 true next input, 3 hosted searches). No opening usage event; `cached_tokens` not
summed but `input_tokens` is; search results are not replayed. Issue #1191 (now a bug) holds the data and
the fix shape: flag cumulative usage when `web_search_call` items appear, keep the previous anchor plus
local estimates in `_update_token_table`. Chat Completions `web_search_options` lane still unmeasured.

**Unified mechanism (the maintainer ruling 2026-09-19: one mechanism, never per-provider
variants):** adapters report raw counters + three facts on `UsageInfo` (`served_prompt_tokens`,
`appended_prompt_tokens`, `prompt_tokens_cumulative`); `resolve_context_usage(usage,
local_request_estimate=thunk)` in compaction.py yields (anchor, served-or-None); consumers:
`_update_token_table`, `PromptTokenEstimator.observe` (returns the anchor for the agent badge),
`merge_usage`. `_last_usage["prompt_tokens"]` MEANS context for every reader (status, replay
preamble, usage row = saved-list occupancy, compat branch); `_rewrite_usage_slot` publishes the
anchor, keeps `billed_prompt_tokens` beside it, clears the facts; `_update_token_budget` charges
billed. Anthropic no-opening branch stays 0/0 (a cache-creation floor re-inflates on an uncached
prefix). OpenAI Responses: cumulative flag on `web_search_call` items, session estimate stands in
(`_estimated_prompt_tokens(use_usage_slot=False, tool_def_chars=served)`). Issues: #1194 (other
hosted tools unmeasured), #1195 (image generation feature), #1189 got the Responses note.

**#1188 + #1190 BUILT 2026-09-19 (branch fix/1188-native-block-charge, stacked on #1196; design at
docs/design/1188-native-lane-charge.md, local):** the completion builder records the provider's
count of what it appended on the assistant Turn as `meta.extra["native_tokens"]`
(`Turn.native_tokens`, dict sibling `_native_tokens`, persisted in `conversations.meta` beside
provenance, routed out of `source_meta` on load, carried by the atomic fork). The measure
`_msg_text_chars(msg, *, replay_producer)` returns `(text_chars, FIXED_TOKENS, doc_chars)`: the
middle element changed meaning from image COUNT to fixed tokens (images*1000 + native lane),
`image_tokens` params deleted. Lane-aware: charged only when `_producer == replay_producer` (serving
lane's provider via `model_turn.lane_producer(lane)`; the session may never read `lane.provider`
directly, an AST test enforces it). `resolve_context_usage` now returns `ContextUsage(anchor,
served, appended)`: the anchor is what the request carried, appended is the turn's own cost (charged
on the turn at append: completion + native; `observe()` still returns anchor+appended for the
badge). #1190: a workstream compaction with after >= before logs `compaction.estimate_not_reduced`,
LOG ONLY: a pause latch was built, reviewed twice and DELETED (round 2 proved it unreachable: the
drain's pre-existing `pre_attempted_compact` already limits one estimate-driven compaction per tool
batch, every reply re-anchors, the agent has its epoch guard). The slot/badge add the charge the
ACCEPTED turn carries (`_update_token_table(native_tokens=)`, `observe(native_tokens=)`);
`trajectory.assistant_meta_envelope(turn)` = the one persisted provenance+native_tokens builder.
Round 3 rules: an accepted turn that replays a lane is charged TEXT FROM CHARS + the lane's count
(`compaction.accepted_turn_tokens`, `PromptTokenEstimator.append_accepted`), never completion +
appended (the completion count already holds the pre-search output the server fed back as appended
input); `model_turn.replayed_lane_tokens` (round 5 shape): early exit at 0; refused + LOGGED above
`_lane_window(lane, cfg) = max(capability TABLE window, model-definition ROW window)` (the row never
reaches caps, #826; unlisted ids default to 200k in the table: a served-based clamp on the table
window silently zeroed the charge on 1M aliases and was DELETED); one scan -> `last_result`
(`providers._protocol.SERVER_RESULT_BLOCK_TYPES`); fed-back TEXT always discounted, fed-back
reasoning discounted when replay off, trailing reasoning ADDED when replay on, sized UNCAPPED via
`LLMProvider.reasoning_text_parts` + `history_decoration.reasoning_text_chars` (NEVER the display
extractor: 64 KiB cap) at chars/4; total clamped to the window. `Turn.native_tokens` is 0 without a
native lane. `ContextUsage` = (anchor, served) only. A "one summary call per model turn at threshold
with an irreducible preserved tail" finding was REFUTED as pre-existing (drain's
`pre_attempted_compact`, one compaction per batch on both trees). Bounds: `NATIVE_TOKENS_CAP = 1 <<
21` in `native_tokens_from`; `CALIBRATION_MIN_TEXT_SHARE = 0.05` in `calibrated_chars_per_token` (a
ratio band was rejected: it breaks the tiny-synthetic-message calibration pins). Review round: 13
findings -> 10 -> all applied but the fork nit. The maintainer RULED 09-19: the in-process fork copy
(`resume(fork=True)` without a snapshot, test-only) is deleted in its own PR, issue #1197.

**Responses lane live-verified THROUGH THE SHIPPED ADAPTER 2026-09-19 (astra):** billed 22,849 flagged
cumulative; session anchor 10,518 (+ estimated turn 10,725) vs measured 10,824 (0.9% under); the alias
row's `capabilities` override (`supports_web_search: true`) must be applied or the model emits a
client `web_search` call; the hosted tool itself costs ~4.4k prompt tokens per request.

**How to apply:** a `usage_events` row whose cache_read exceeds every cache the workstream ever created,
followed by a much smaller main-loop call, is this bug, not a leak from tool sub-loops.
Related: [[feedback_measure_before_accepting_a_finding]], [[project_883_zero_budget_truncation]].

**2026-09-19 evening (branch fix/1188-native-block-charge, single amended commit, unpushed until the maintainer says `push`).** Round 6: 0 majors; round 7 (bug + quality only, the maintainer's ruling): ZERO correctness findings = ship gate met. The maintainer's rulings that evening: KEEP the branch rather than the simplification finder's 3x-smaller cut (500 new lines judged acceptable); the regression finder pair is recorded in [[feedback_review_convergence_methodology]] lesson 11. Final shape facts: the window bound FAILS CLOSED (a 0 window from `apply_capability_overrides({"context_window": 0})` or a caps-less lane refuses every count through `native_lane.count_refused`); `calibrated_chars_per_token(lane_tokens=)` judges the 5% text floor against the REPORTED lane share only (images exempt, so image-heavy requests calibrate as on dev); one lane reader `ChatSession._lane_tokens` for dict and Turn, bound with the measure by `_message_measure -> BoundMeasure(measure, lane)`; `PromptTokenEstimator.observe` returns the anchor it installs (caller adds the charge for the badge; `lane_measure` field); a task-agent reply with completion_tokens 0 is measured from text (announced in CHANGELOG). Declined with reasons: session re-estimate sites keep dev's chars round trip (<= 1 token drift); `extract_reasoning_text` stays on the Protocol beside `reasoning_text_parts` (35 call sites). Pushed on the maintainer's `push` 2026-09-19 as PR #1198 (against dev; Closes #1188, #1190; refs #1197); the cut commit pushed 2026-09-20 (PR = two commits, squash-merge lands the PR body) — new commits only from here, never amend. Design note docs/design/1188-native-lane-charge.md has every round.

**Cut taken after all (2026-09-19 night), second commit on PR #1198:** two post-PR cross-configuration findings (count baked to the replay posture; producer-name match vs the shared Messages-API converter) made the maintainer reverse the keep ruling. Final shape: raw appended count, refused above `min(_lane_window, NATIVE_TOKENS_CAP)` (one logged arm, fail-closed on a 0 window), recorded only when the lane survives finalization (`not had_blank_ids`); accepted charge = `max(1, completion) + lane` (measure only when the count is missing); `replay_family()` over `ANTHROPIC_PROTOCOL_PROVIDERS` (constant now lives in providers/__init__.py, re-exported by model_registry via the `as` idiom for strict mypy); a request carrying a charged lane is NOT a calibration sample (ratio frozen until compaction or a family switch; cold starts hold 4.0) — the text-share floor is gone; `_update_token_table(bound=)` re-estimates through the one binding. Reasoning-walk Protocol member and its chain deleted; adapters byte-identical to dev. Rounds 8-10 on the cut: 1 latent, 1 narrow, 0. Lesson recorded in [[feedback_review_convergence_methodology]] lesson 11 postscript.


**Live on the cut, shipped SESSION path (2026-09-20, fable, 3 calls ~87k billed input mostly cache reads, ~1 search):** turn recorded 9,849 = adapter appended; slot = 14,345 + 9,849; follow-up estimates 24,343 vs 24,324 served (+0.1%) and 24,366 vs 24,387 (-0.1%); ratio calibrated once on the lane-free first request (4.0 -> 2.31) and frozen on the two lane-carrying requests; persisted (9849, 0, 0). Script pattern: `make_registered_session` + `replace_session_lane(provider=AnthropicProvider(), client=anthropic.Anthropic(api_key=<key>), model, alias, capabilities)` + tee `provider.create_streaming` for usage.

**Responses lane, session path, live 2026-09-20 (astra; override `supports_web_search` must be applied by hand, the table does not auto-populate it for gpt-6-astra):** search call reports cumulative usage with NO served figure -> anchor = local estimate, native_tokens 0, ratio stays 4.0; first plain follow-up -24% (uncalibrated default vs true 3.04, pre-existing cold-start gap), second follow-up -0.2%. The skip rule did not engage (lane 0), as designed.

**Landed 2026-09-20:** PR #1198 rebase-merged onto dev by the maintainer's instruction (not the usual squash), so both commits sit on dev with new SHAs 60bfed7b (turn-charged lane + compaction warning) and 4e677f1f (raw count, completion+lane charge, replay family, calibration skip). All 16 CI checks green at 81ea0e0f. Remote branch `fix/1188-native-block-charge` left in place (not asked to delete). Local dev fast-forwarded to 4e677f1f. Open follow-up: #1197 (delete the in-process fork copy, its own PR). Related read the same morning: #1187 (model-requested compaction research bet) — see [[project_1187_model_requested_compaction]].

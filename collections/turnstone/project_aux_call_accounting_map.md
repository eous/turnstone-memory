---
name: project_aux_call_accounting_map
description: Verified 2026-09-20 map of how utility calls, task agents and judges pick a lane, whether they touch the main context estimate, and whether their spend reaches the usage ledger (judges do not)
metadata:
  type: project
---

Verified on dev at 4e677f1f (2026-09-20), at the maintainer's request, after the #1188 lane charge
landed.

**Context-estimate isolation (correct):** `_update_token_table` and the `_last_usage` slot are written only
on the main commit path (session.py commit site + `_anchor_usage_slot`). `resolve_context_usage` runs in
two places: the main commit and `PromptTokenEstimator.observe` (task agent's own estimator, own context
window, own compaction via `_build_summary_runtime(lane, context_window=agent_context_window, ...)`).
Utility completions and judges never touch the main estimate or its calibration.

**Ledger (`usage_events` via `record_usage_event`, one writer `_write_usage_row` in session_ui_base):**
- Main turns: `_print_status_line` → `on_status` with the RESOLVED slot (`prompt_tokens` = context size
  since #1196; `billed_prompt_tokens` stays in the slot, not persisted = #1189).
- Utility (title, compaction summary, web_fetch extraction incl. PDF) and task agents:
  `model_turn(on_completed=_record_aux_usage)` → `on_aux_usage` → same row writer, `tool_calls_count=0`,
  model = the lane's model. `on_completed` fires at model_turn.py before `_ingest_completion`, so aux rows
  carry the RAW provider `prompt_tokens` (on a server-tool loop: the billed sum). Main rows and aux rows
  therefore disagree in meaning on server-tool turns — #1189's column would settle it; bundle.
- **Judges (intent judge judge.py `_run_judge`, output-guard judge) record NOTHING:** both call `model_turn`
  with no `on_completed` and never read `result.usage`. Judge spend is absent from the ledger and from
  Prometheus whether the judge rides the session model or a `judge_model` alias. No test or ruling pins
  this; `_record_aux_usage`'s docstring lists title/compaction/web-fetch/sub-agents and omits judges.

**Lane / connection:** utility calls default to `self._primary_lane()` (same client, same model, same alias
admission gate; `model_turn` takes the admission lease, so they serialize against main turns on a
single-slot local server). Task agents: own alias lane when configured (`same_lane` false). Judges:
`_judge_binding_from_session` re-resolves the SESSION provider/client/model with judge sampling; a
`judge_model` alias gives a distinct lane. Title generation runs in a daemon thread concurrent with the
main turn.

**Prefix cache:** hosted lanes are keyed by content prefix (Anthropic top-level `cache_control` ephemeral
on every request; OpenAI `prompt_cache_options`/retention, no `prompt_cache_key`), so a utility prompt
neither reads nor evicts the conversation prefix; cost is one small 1.25x write per utility prompt. On
self-hosted servers the KV prefix cache is server memory shared by every request to that alias; nothing
in our code keeps utility prompts off the conversation's server except routing them to another alias,
which exists only for task agents (task alias) and judges (`judge_model`). Not measured live.

**Why:** The maintainer asked to confirm isolation and counting; the judge gap is the one defect
found. **How to apply:** judge accounting needs an `on_completed`-style hook threaded into the judge
binding (the judge holds a `ResolvedModelBinding`, not the session); a utility role/alias is the
only lever for local KV-cache pressure and is the same shape ruled for #1192.

Posted to #1189 on 2026-09-20 as a comment (judge gap + aux-row raw vs main-row resolved), on the maintainer's instruction; the judge accounting fix is scoped to ride with or just ahead of the #1189 column.

Filed as #1199 (bug) on 2026-09-20 at the maintainer's request: dedicated issue, references PR #1198 as provenance and #1189 as the related column; ships without a migration. Cross-link comment left on #1189.

**#1199 BUILT 2026-09-20 on `fix/1199-judge-usage-accounting` (single amended commit, unpushed until
The maintainer says `push`; PR body at scratchpad pr_body_1199.md).** Shape: `UsageRecorder`
Protocol (`__call__(usage, *, model)`) + `_UsageHandoff(record_usage, model=, source=)` in judge.py;
both judges take keyword-only `record_usage`, session passes `self._record_aux_usage`. The handoff
exists because `model_turn` fires `on_completed` on the deadline worker
(`run_abortable_with_deadline`) before handing back the result, so a synchronous usage row write
there would charge storage latency (sqlite busy 30 s, postgres pool_timeout 30 s) to the verdict
budget; capture queues on the worker, the caller flushes in a `finally` after the deadline call, an
abandoned worker self-records (best-effort in the intent batch lane: the eval worker's
`client.close()` can cut the late call short, pre-existing race). Three unprimed review rounds;
round 3 bug finder: zero correctness findings. Declined: a test_session variant of the wiring test
(duplicates `test_record_aux_usage_attributes_explicit_model`). Judge rows do NOT advance
`_ws_prompt_tokens` (aux path by design); CHANGELOG says so.

Live-verified 2026-09-20 on the Anthropic lane (fable): one intent + one guard call; sink received exactly the provider closing usage (1180/226, 1017/76) under the judge model from the eval worker and the caller thread; usage_events summed 2197/302, sum_workstream_tokens 2499. Probe: scratchpad probe_live_judge_usage.py (SessionUIBase subclass on a tmp sqlite so the row really writes).

Pushed 2026-09-20 as PR #1200 against dev (head 2f3adc3c). New commits only from here, never amend.

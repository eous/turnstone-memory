---
name: project_nudge_eval_harness
description: "turnstone-eval --nudges (coordinator nudge merge gate): lower through _prepare_wire_messages (production wire); check canary_after before trusting a grid."
metadata:
  node_type: memory
  type: project
  modified: 2026-07-28T23:43:57.167Z
---

`turnstone-eval --nudges` — behavioral eval for the coordinator idle
nudges, built on #913 as its **merge gate** (the maintainer: numbers before
merge). `turnstone/eval/nudges.py` + `scenarios/nudges.py`, harness
tests in `tests/test_eval_nudges.py`. Design and chronology:
`docs/design/nudge-eval-design.md`, `nudge-eval-tuning-log.md`.

## What makes it different from skill-adherence

- **State-first scoring.** Cells seed a real envelope through the
  production `tasks_add`; the model's `tasks` calls really execute;
  ground truth is the FINAL ENVELOPE plus a forbidden-action list. The
  forbidden-action rate is the headline number.
- **Named stimulus arms over one seeded state**, not treatment/control
  (a no-stimulus control is degenerate — no wake, no turn, vacuous
  pass). `bare_continue` is the reference line the typed body must beat.
- **Production-rendered bodies** via the real formatters, so the eval
  cannot drift from what ships. `--body-override` exists only for
  tuning sweeps.

## Traps that void a sweep — check these first

- **Send the PRODUCTION wire.** The loop must lower through
  `_prepare_wire_messages` (fold_system_turns). Injecting raw mid-list
  `system` turns is a shape production never emits: one endpoint
  accepted it silently, the next hard-rejected it, and every number
  measured before the fix is suspect.
- **`/v1/models` `created` is stamped at REQUEST time**, not server
  start. It can never witness a restart. A guard built on it reported
  drift on every sweep, and it is what made me wrongly diagnose a vLLM
  restart (`docker inspect`: RestartCount=0).
- **The tool-call canary**: never `tool_choice="required"` (a qwen3.6
  build returned `finish_reason="tool_calls"` with an EMPTY list while
  natural choice was 3/3 — the probe manufactures the failure it tests
  for); budget it at the sweep's own `max_tokens` (a thinking model
  burns a small budget inside its reasoning block and returns
  `finish_reason="length"` with empty content, indistinguishable from a
  dead parser); retry, because natural choice may answer in prose once.
- **Check `canary_after` in every result JSON** before believing a
  grid.

## Arm lifecycle (the maintainer, 2026-07-28)

Tuning-era arms retire once their question is answered on the honest
instrument. **pair_cf: RETIRED** (ordering answered twice on the
correct wire, tasks-first ≥ everywhere; design-pinned by seq tests —
pair_tf stays as the canonical co-delivery arm). **no_provenance:
retires AFTER one final outing** — F2-c made the merge-gate sweep the
FIRST clean isolation of the provenance paragraph (every earlier
number was wrong-wire or confounded by the caveat riding the same
paragraph). If it shows nothing, the PARAGRAPH is the pruning
candidate, not just the arm. bare_continue is the permanent reference
line and never retires.

## What it measured that mattered

Zero forbidden actions across 225 runs of three body generations on the
correct wire — the founding safety claim. `bare_continue` dispatched
past an explicit sign-off 70% of the time; the typed body 0-10%.
Ablating the provenance paragraph quadrupled the forbidden rate.
Branch-scope confusion (not missing permission) was the done-branch
failure: scoping the escalation clause took that cell 30% → 90%.

Local panel — THREE TIERS (gemma ruled IN, the maintainer 2026-07-28), each
answering a distinct question:
- **deepseek-v4-flash** (`:8000`, GPU 0 box) — the SAFETY
  DISCRIMINATOR: only model measured strong enough to attempt the
  unsafe action. Flaky nightly tool parser; the canary + G6
  retry/timeout exist for it. Decision numbers read from here.
- **qwen3.6-27B** (`:8002`, GPU 1, `/mnt/models/qwen3.6-27B/run.sh`)
  — mid-tier confirmation. Endpoint rock-solid; model produced 0%
  forbidden in BOTH arms (dead instrument for safety cells).
- **gemma-4-E4B-it** (`:8001`, GPU 0,
  `/mnt/models/gemma-4-E4B-it/run.sh`, `--tool-call-parser pythonic`
  UNVERIFIED — canary settles it) — the FLOOR: typed-body
  comprehension, bookkeeping pass rates, the confusion failure mode
  (nudge read as authorization). Do NOT assume small =
  safe-by-incapacity; small models can be more impulsive, E4B may
  discriminate from the opposite end.
Live-provider runs need the maintainer's go-ahead
([[feedback_live_provider_probes]]).

Related: [[project_idle_tasks_nudge]], [[reference_gb10_spark_vllm_tuning]],
[[feedback_harness_scripted_events_not_verification]].

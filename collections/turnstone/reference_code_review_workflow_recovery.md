---
name: reference_code_review_workflow_recovery
description: "code-review Workflow hangs at synthesis, or a healthy run reports at cap (15 max/xhigh, 10 high): mine journal.jsonl .result or the synthesize prompt."
metadata: 
  node_type: memory
  type: reference
  modified: 2026-08-03T01:09:54.403Z
---

The local `code-review` Workflow (`Workflow({name:"code-review", args:"max …"})`) runs the finders + an independent verifier reliably, but its FINAL structured-synthesis stage is flaky — observed twice on one small diff: once a mid-generation hang (status stuck "running", no completion notification), once `TelemetrySafeError: StructuredOutput retry cap (5) exceeded`. The crash is the **forced output schema** on that last stage, not the agents themselves.

**JOURNAL SHAPE DRIFTED (verified 2026-08-02).** The payload now hangs off **`.result`**, not
`.value` — `jq 'select(.type=="result") | .value'` returns `null` on every line and looks like an
empty run. Working extractors:
`jq -r 'select(.type=="result") | .result.candidates // empty | length'` and
`… | .result.verdicts // empty | .[] | .verdict`. Event keys are
`{type, key, agentId, result}`. Re-check this before concluding a run produced nothing.

**Recovery (proven, 2026-06-26):** the finder `candidates` and verifier `verdicts` persist as `{"type":"result"}` events in the run's `journal.jsonl` under `…/subagents/workflows/<wf_runId>/`. Extract:
- `candidates`: `{file, line, summary, failure_scenario}` (one finder finding each).
- `verdicts`: `{index, verdict (CONFIRMED|PLAUSIBLE|REFUTED), evidence}`. **`index` is BATCH-LOCAL** — the verifier runs one agent per file:line group and indices restart per group, so do NOT pair candidates↔verdicts by a global index. Correlate via the `evidence` text, which names the candidate's file:line and restates the claim.

Finish the pipeline by invoking the stage agents **directly via the Agent tool** — `code-review-dedupe` (merge / drop-refuted / severity; have it Write its JSON to scratchpad) → `code-review-sanity` (re-validate each finding against current source, render the markdown report). Direct invocation returns free-form text and does NOT force the schema that crashes the workflow, so it completes. An `implementer` agent then applies the sanity report. The dedupe stage does real reconciliation — it refuted several of my own concerns (server-capped 429 Retry-After; per-ws Pane architecture defeating a tab-switch DELETE mis-target).

**Resume gotcha:** `Workflow({scriptPath, resumeFromRunId})` cache-hits only with the SAME `args`. Omit `args` and every finder prompt changes → full re-run from scratch, AND it reuses the run dir, polluting that journal with a second run's results.

**Cap-mining on HEALTHY runs (the maintainer's standing rule, 2026-07-12):** the workflow verifies more candidates than it may emit — `maxFindings` is **15 at max/xhigh, 10 at high** (script `LEVEL_PARAMS`), while the max pool can reach ~88 candidates (5 correctness angles × 8 + cleanup 40 + sweep 8). When the reported count lands at/near the cap — and always for security-sensitive diffs — mine the run's transcripts for verified-but-dropped survivors:
- The **synthesize agent's PROMPT** embeds the COMPLETE ranked survivor list: "N findings survived independent verification", numbered `[i]` with file:line, verdict, summary, failure scenario, and verifier evidence — no candidate↔verdict correlation needed (unlike the crash-recovery path above).
- **Locate the synthesize agent BY CONTENT (2026-07-25, more robust than the label path below):** `grep -l "survived independent verification" <transcript-dir>/agent-*.jsonl`. Re-verified that run: journal v2 `started` events carry only `{type,key,agentId}` AND the `agent-*.meta.json` sidecars carry only `{agentType,spawnDepth}` — *neither* has a label, so content is the only reliable handle and it does not depend on the result payload arriving intact.
- **Confirmed on a healthy max run (2026-07-25):** 35 survivors → 15 reported → **8 genuinely dropped, one of them CONFIRMED**. Ranking pushes drops toward cleanup/PLAUSIBLE but severity does not follow the rank — mine every time the count hits the cap.
- **Where the prompt lives (journal v2, verified 2026-07-13):** `journal.jsonl` `started` events now carry only `{agentId, key, type}` (keys are `v2:<hash>`, no prompts, no labels), so jq-ing the journal for the prompt finds nothing. Get the synthesize agent's id from the workflow result's `workflowProgress` (label `"synthesize"`), then read its first user message from `agent-<id>.jsonl` in the same transcript dir: `jq -r 'select(.type=="user") | .message.content | if type=="array" then .[0].text else . end' agent-<id>.jsonl`. Extraction one-liner for the numbered list: `rg -n "^### \[" <dumped-prompt>`.
- Accounting that decides "was anything dropped": reported primaries + locations named in `[same root cause also at: …]` merge notes must cover every survivor index; `stats.reported < kept` is usually merges, not drops (2026-07-13 run: 19 kept → 14 primaries + 5 merged, zero dropped).
- The report keeps ≤cap primaries; `merge` arrays absorb same-root-cause survivors (those ARE represented — their locations appear as "[same root cause also at: …]"). **Genuinely dropped = survivor indices never claimed as primary or merge.** Ranking is correctness-CONFIRMED → correctness-PLAUSIBLE → cleanup-CONFIRMED → cleanup-PLAUSIBLE, so drops are usually cleanup/PLAUSIBLE — but on a security diff triage them anyway.

Related: [[feedback_large_review_orchestration]], [[feedback_code_review_effort_budget]].

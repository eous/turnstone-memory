---
name: project_output_guard_llm_merge
description: "Editing output_guard_judge.py or merge_guard_display_payload (#560; shipped #601/#602): merge, never override; risk=max(heuristic, llm), LLM never lowers."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-26T00:22:09.672Z
---

The output-guard LLM judge (Facet 2b, issue #560) was reworked from
"LLM verdict overrides regex" to an **annotated merge**. Shipped as two PRs
(2026-05-29): **#601** (the merge + reconnect fix) and **#602** (move
the `judge.output_guard_model` picker into admin Models → Roles). Builds on the
already-merged `output_guard_judge.py` / migration 057 work. Extends
[[project_three_facet_validation]]. Now a settled, load-bearing production
path — PR #760 (2026-07-03, [[project_judge_func_args_projection]]) built
directly on `output_guard_judge.py`'s oversize-backstop behavior described
below, confirming these invariants are still the live contract.

**Security invariants — easy to accidentally break, preserve them:**
- **Merge, never override.** `risk_level = max(heuristic, llm)`, `flags = union`.
  The LLM can *escalate* but must **never lower** a heuristic positive — it
  evaluates adversarial tool output, so defeating the judge must not erase a
  deterministic regex finding. Do NOT re-introduce silent de-escalation
  (the old `test_llm_enabled_can_de_escalate_clean` behavior was deliberately
  removed). Credential redaction stays heuristic-only, always applied. In [[project_harness_compiler_dialect_stack]] terms the guard is the **disturbance-rejection margin**: the LLM = the stochastic **verifier ρ**, untrusted output = the **adversarial environment E**, and `max(heuristic, llm)` holds the deterministic floor under minimax drift (#693's reframe).
- **The model is never told the judge cleared a finding.** The `GuardAdvisory`
  spliced into the tool-result envelope gets merged risk+flags + heuristic
  annotations + the LLM's reasoning ONLY when it *escalated* (`risk != none`).
  A judge fooled into "none" must not talk the model out of caution. The
  operator UI (chip) DOES see the full verdict incl. "benign" — operator-only.
  (`_evaluate_output` builds `context_annotations` separately from the chip `d`.)
- **Failed judges → `tier="llm_error"`** (audit-only), excluded from the replay
  display merge so a `risk="none"` failure row can't shadow a heuristic finding
  on reconnect (the reported vanishing-chip bug). Tiers are now
  heuristic / llm / llm_error.
- **Defaults disabled**: `judge.output_guard_llm = False` (judge.py +
  settings_registry); gate honored live via `_ensure_output_guard_judge`
  (re-checks the flag every call).

**Single source of truth**: `output_guard.merge_guard_display_payload` drives
BOTH live (`session.py::_evaluate_output` → `on_output_warning`) and replay
(`history_decoration.py::build_merged_output_assessment_payload`). Keep them in
lock-step — wire-shape parity is the whole point, and a shared helper alone doesn't
prove it: the guard is a test that diffs the two payloads, not the common call site.
Chip payload fields: risk_level, flags, redacted, annotations, tier, judge_risk
(LLM's own verdict, for the dissent badge), confidence, reasoning, judge_model.
The SDK `OutputWarningEvent` must declare every key the merge can emit (drift
guard test in test_sdk_events.py).

**Admin model-role config**: `judge.output_guard_model` (and `judge.model`) are
model-role pickers in **Models → Roles** (`admin.js` `MODEL_ROLES`), NOT the
Judge tab — the Judge tab's `renderJudgeSettings` (governance.js) skips both.
Adding a judge model role = add to MODEL_ROLES + skip on Judge tab (two-file
coupling). Read/write via generic `/v1/api/admin/settings`.

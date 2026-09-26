---
name: eval-pipeline-optimization-findings
description: "Eval pass rate plateaus on system-prompt tuning for small local models: switch to tool-description optimization (--optimize-tools), 79% to 98%."
metadata: 
  node_type: memory
  type: project
---

Eval pipeline (`turnstone-eval`) optimization findings from 2026-03-24/25. **Path note (2026-07-03, [[project_eval_optimizer_split]]):** `turnstone-eval` has since split into a measure-only substrate + `turnstone-optimizer`; the `--optimize-tools` flag referenced below now lives on `turnstone-optimizer` (`turnstone/optimizer.py`, renamed from the old top-level `eval.py`), not on the measure-only `turnstone-eval` CLI. The finding itself (tool descriptions > system prompts for small models) is unaffected by the rename.

**Key discovery:** Tool descriptions have significantly more leverage than
system prompts for small local models (20B). The system prompt competes
with conversation context for attention; tool descriptions are read at
decision time when the model chooses which tool to call.

**Results:**
- Baseline: 79% pass rate (16 test cases, 10 runs each)
- System prompt optimization alone: plateaued at ~86%
- Tool description optimization (`--optimize-tools`): reached 98% peak
- Combined: 91% baseline → 98% peak in 15 iterations

**What worked in descriptions:**
- Trigger phrase examples: "What Python version?" → bash(command='python --version')
- Tool disambiguation: "For file creation use write_file instead" in bash description
- Prerequisite chains: "Requires read_file first — it will fail without this" in edit_file
- Negative boundaries: "Not for direct code changes" in plan_agent description
- "Questions about X are tool-use tasks — use Y, not memory" pattern

**What didn't work:**
- Imperative rules (MUST/NEVER/ALWAYS) — models trained on Anthropic data
  produce them but they don't improve scores and often hurt
- Optimizer/analyst naturally drift toward rules; need explicit "patterns
  over rules" framing in their system prompts to counteract

**Why:** Conventional wisdom says system prompt is king. For smaller models
with competing fine-tuning priors, the tool schema is closer to the
decision boundary. System prompts fight priors from a distance; tool
descriptions shape them at the source.

**How to apply:** When eval scores plateau on system prompt optimization,
switch to `--optimize-tools` mode. Alternate between surfaces — each
lifts the floor for the other. Adopt successful description changes into
the actual tool JSON files after reviewing (strip rule language).

**Lens ([[project_harness_compiler_dialect_stack]]):** descriptions live at the controller/lowering layer (closer to the decision boundary than system prompts); eval pass-rate as the tuning signal = the harness's **PGO** (cf. #690 measure).

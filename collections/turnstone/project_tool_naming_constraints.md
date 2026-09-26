---
name: local-model-tool-naming-constraints
description: "Naming a new tool for local models: bare words like plan/task collide with chat-template channels and hallucinate channel syntax; suffix (task_agent)."
metadata: 
  node_type: memory
  type: project
---

Tool names must not collide with chat template channel/mode names in local
models. Discovered 2026-03-25 when `plan` tool caused the model to hallucinate
`<|channel|>plan<|message|>` syntax inside tool call JSON payloads.

**What happened:** A 20B local model with a structured chat template
(channels like `<|channel|>commentary`, `<|channel|>analysis`) saw a tool
named `plan` and spontaneously invented a "plan channel" by analogy. It
treated this channel as a thinking/analysis space before making tool calls.
This was not in the training data — the model generalized from the template
structure. The server returned 500 errors due to malformed JSON.

**Fix:** Renamed `create_plan` → `plan_agent` and `task` → `task_agent`.
The `_agent` suffix is clearly a tool dispatch pattern, not a channel/mode
concept. Having both `plan_agent` and `task_agent` in the tool list
reinforces the pattern contrastively.

**Why:** Emergent behavior from chat template structure. The model doesn't
need to have seen specific training examples to generalize template
patterns to new names. Any tool name that looks like a plausible channel
name (single common words like `plan`, `debug`, `analyze`) is at risk.

**How to apply:** When naming tools for local models, prefer compound names
with a suffix (`_agent`, `_tool`, etc.) over bare words. Test new tool
names against the model's chat template to verify no channel collision.

**Lens ([[project_harness_compiler_dialect_stack]]):** a tool name is surface syntax in the wire dialect; `plan`/`task` collide with chat-template channels, and `plan_agent`/`task_agent` output is the as-yet-unbuilt **plan dialect** (intent→plan→tool-call→wire).

**Update 2026-07-01:** `plan_agent` has since been REMOVED ([[project_plan_agent_removed]]) — a planning skill handed to `task_agent`, or model-native planning, outperformed the dedicated agent; the historical rename above is why tests still reference the name. The naming lesson stands unchanged for `task_agent` and any future tool names.

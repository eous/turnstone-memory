---
name: feedback_model_errors_never_suggest_switching
description: "Writing an error a model reads about a model it can't use (task_agent, spawn, create refusals): say why and suggest retrying only if retryable; never steer it to another model, never forbid one."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-13T20:17:18.947Z
---

An error that a model reads, saying a model it relies on isn't available, names the model and
why, and suggests trying again only when the failure may clear by itself (for example the secret
store didn't answer, `SecretError.retryable`). It never tells the model to use another model: no
list of other aliases, no "pass `model=`". It doesn't forbid one either: an explicit choice the
model makes on its own stays allowed (maintainer, 2026-10-13, #1359).

**Why:** a model told to switch will usually switch at once, often to a pricier or hosted model,
and unattended runs (schedules, coordinators, auto-approved tools) have no human to catch it.
That silently undoes the "never move to another model" rule #1359 set for routing.

**How to apply:** this covers any text that reaches a model's context: tool results (task_agent),
spawn results that echo a node's create refusal, and errors a coordinator reads. Human-only
surfaces (the console launcher, the CLI, the `/model` remedy in a person's transcript) may still
suggest choosing a model. Keep the loader's raw reason out of model-facing text: it names secret
reference paths and store mounts; give the kind of failure instead (see
`ModelRegistry.unavailable_reason`). Related: [[project_1359_default_fail_closed]].

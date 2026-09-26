---
name: Don't optimize for smallest models
description: "Designing error messages or model-facing feedback: keep full context, never trim tokens for 9B-class models; most users run larger models."
type: feedback
---

Don't reduce error message context (e.g. raw argument echoing) just to save tokens for very small models like 9B. Most users run larger models where the extra context is useful. 9B is the extreme low end.

**Why:** User pointed out that 9B is on the very small side of models typically used with turnstone — optimizing for that edge case would degrade the experience for the majority.

**How to apply:** When designing error messages or model-facing feedback, keep full context rather than aggressively trimming. Let the model have enough signal to self-correct.

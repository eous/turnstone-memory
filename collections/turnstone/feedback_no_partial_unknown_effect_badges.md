---
name: feedback_no_partial_unknown_effect_badges
description: "Tempted to add partial/unknown effect-status badges or wire effect_status to SSE/render: don't; it stays internal and persisted only."
metadata: 
  node_type: memory
  type: feedback
---

We deliberately do NOT render user-facing badges for the `partial`/`unknown` effect-status (the EffectStatus trichotomy from the cancellation "never none" discipline, HYPOTHESIS appendix). The status IS tracked and durably persisted internally — `_tool_status` → `conversations.meta` → `Turn.meta.extra["effect_status"]` (round-trips, tested in `tests/test_cancel.py`) — but it is intentionally not wired to the frontend (`tool_result` SSE carries no status; `project_history_messages` doesn't project it) and there is no `partial`/`unknown` badge chrome.

**Why:** honest internal accounting (never-`none`, for owner/parent reconciliation and compensation) is a correctness requirement that must hold; a *user-facing* representation of it is a separate UX decision the user is holding back until the right visual language exists. Internal tracking is the current frontier; surfacing is not.

**How to apply:** keep effect-status internal and persisted; never regress it. For outcomes — including cancelled task agents — surface the honest *prose* disposition (which already says e.g. "in flight at cancel: … — outcome UNKNOWN") plus the existing `✓`/`✗`/denied signals. Do not invent `partial`/`unknown` badges or wire `effect_status` to the wire/render layer as part of unrelated work. Links: [[project_canonical_trajectory_redesign]] (Turn.effect_status), [[project_intent_verdict_lifecycle]].

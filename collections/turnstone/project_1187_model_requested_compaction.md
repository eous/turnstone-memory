---
name: project_1187_model_requested_compaction
description: "#1187 research bet (model-requested compaction, usage floor, long-context pricing boundary): what the repo can and cannot measure today, and how it touches the #1188 lane charge"
metadata:
  type: project
---

#1187 (filed 2026-09-19, labels performance+research, NOT committed) proposes a model tool that
self-raises the existing compaction-pending advisory, refused below a server-side usage floor whose
refusal returns the usage percentage; long-context sessions opt-in; a separable prerequisite is a
per-model `long_context_threshold` caps row bounding BOTH the compaction policy and the summary
chunk budget via `min(context_window, long_context_threshold)`. Non-goals: in-place pruning
([[feedback_no_tool_result_pruning_prefix_cache]]), conditional tool visibility, timer compaction.

Read on 2026-09-20 (after #1198 landed, [[project_server_tool_usage_inflates_context]]):

- **Evidence item 1 is unmeasurable today.** The compaction start/end SSE payloads and the marker
  carry `trigger` (auto/manual), `where` (set ONLY at the mid-turn tool-result drain site), `pct`,
  `before_tokens`, `after_tokens`. `carry_spill` / `stopped_to_compact` reaches neither payload, so
  spill compactions cannot be told from plain threshold compactions in persisted data. One boolean
  on the start payload + marker meta is the prerequisite for any spill-rate number.
- The usage percentage a floor refusal would return is only trustworthy since #1193/#1198 (gauge
  was 160k vs real 50k on server-tool loops before).
- The `long_context_threshold` prerequisite must NOT bound `_lane_window` (model_turn.py): the lane
  refusal asks "is this count plausible for the model", which is the raw window.
- The pricing-cliff claim (premium tier applies to the whole request incl. cache reads above ~200k)
  is unverified in-repo; the issue names it the crux.

**Why:** the issue's sequencing (evidence first, tool last) depends on instruments that do not yet
exist; knowing which field is missing saves re-deriving it.
**How to apply:** if #1187 is picked up, add the spill flag and the trailing-usage-pct experiment
before designing the tool; file the caps-row prerequisite as its own issue.

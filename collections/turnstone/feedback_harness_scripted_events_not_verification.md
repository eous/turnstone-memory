---
name: feedback_harness_scripted_events_not_verification
description: "UI behavior that hinges on the backend emitting an event, with a render harness (livepass) scripting it: also assert the emission in a backend test."
metadata: 
  node_type: memory
  type: feedback
---

A frontend render harness (e.g. `scripts/livepass.py`) drives the real UI with
**hand-scripted** events. A scripted event is an *assumption* about what the
backend emits — NOT verification that it does. Where a UI behavior depends on
the backend *emitting* a specific event, assert the emission with a **backend
test**; the render harness can't catch a missing emission because it fabricates
the event itself.

**Why (the worked instance):** the `task_agent` card's completion (running →
done/error) + its synthesis render both hinge on a `tool_result` event for the
task_agent. The parent tool-loop only reports error/denied results centrally;
success results rely on each tool *self-reporting* via `_report_tool_result`, and
`_exec_task` never did (pre-existing — the old `on_info` legs masked it; the
chunk-3 card inherited the gap). So the live card would have shipped stuck on
"running", AND a failed task recorded `is_error=False` in the canonical
trajectory (the source of truth lying about a sub-harness's outcome — HYPOTHESIS
effect-record / "unknown, never none" inverted). The chunk-3 livepass *scripted*
the `tool_result`, so it screenshotted green; trajectory-level tests passed
because `run_one`'s return still populated the Turn. Caught only by a later
whole-stack bug review. [[project_task_agent_modernization]]
[[project_canonical_trajectory_redesign]]

**How to apply:** when a feature's correctness is "the backend emits event X and
the UI reacts," write a test that the backend EMITS X (assert the
`on_*`/`_report_*` call), separate from any harness that feeds the UI a scripted
X. Treat a harness that green-screenshots off fabricated events as covering the
*consumer*, never the *producer*. Be suspicious any time the test/harness
supplies the exact signal whose presence is the thing in question.

---
name: project_eval_headless_loop_no_admission
description: "Moving a tool's output bound from its executor into batch admission: the eval headless loop has no admission step, so bound the result there too (found 2026-11-05)."
metadata:
  node_type: memory
  type: project
  modified: 2026-11-05T11:28:05.299Z
---

`HeadlessSession._run_headless_loop` in `turnstone/eval/core.py` appends each tool's raw output
to the model's context with no admission, output guard or fold. It relies on executors bounding
their own output, as the bash capture does. When `wait_for_workstream` moved its sizing from the
executor into admission (2026-11-05), that loop would have sent every child's message unbounded;
it now applies the tool's `_ADMISSION_REFITS` entry at the session ceiling.

**Why:** only a regression finder tracing every consumer of the executor's output caught it; the
main-session tests all run through the batch drain and stayed green.

**How to apply:** when a change lets an executor return more than a fold could show, or moves a
cut into admission, check the eval headless loop and any other caller of `_execute_tools` that
skips `_admit_batch`. Related: [[project_wait_message_sizing]],
[[project_cli_origins_forgotten_child]].

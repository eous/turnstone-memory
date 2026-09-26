---
name: feedback_regex_timeout_needs_subprocess
description: "Bounding a regex with model/user-supplied pattern or subject: sre holds the GIL so in-process timeouts are inert; run it in a killable subprocess."
metadata: 
  node_type: memory
  type: feedback
---

A catastrophic-backtracking regex (`(a+)+$` on a long non-matching subject) executes inside ONE C call in CPython's sre engine, which **holds the GIL for the whole call**. Every mitigation that lives in the same process is therefore inert: a sacrificial thread + `join(timeout)` never fires (the joiner can't be scheduled), signal handlers don't run, watchdogs freeze. Discovered live on the #817 background-shells branch — my thread-based filter timeout froze the entire pytest process; the maintainer spotted the hang.

**Why:** long-running C extension calls only yield the GIL if they explicitly release it; sre does not. `sys.setswitchinterval` preemption applies to bytecode boundaries only.

**How to apply:** any regex whose PATTERN or SUBJECT is model/user-supplied must be bounded by a **separate process** you can SIGKILL (`start_new_session=True` + `killpg` on `communicate(timeout=...)` expiry), or by a regex engine with native timeouts (the `regex` package) / linear-time guarantees (rg/RE2). Also pin subprocess pipe encodings (`encoding="utf-8"` + child `PYTHONIOENCODING`) — `text=True` alone is locale-dependent and a C-locale node turns U+FFFD into UnicodeEncodeError. Truncate the subject parent-side so pipe I/O can't eat the time budget. In turnstone this lives in `background_shells._filter_lines_bounded` (the reusable shape: JSON in, matching indexes out).

Related: [[project_bash_tool_pipe_eof_hang]] (the sibling never-returns class), [[feedback_asyncio_timeout_vs_wait_for]].

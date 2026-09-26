---
name: project_judge_deadline_daemon
description: "Timing out a blocking LLM/regex call (judges SHIPPED v1.6.7, PR #674): use core/deadline.py run_with_deadline, never ThreadPoolExecutor; atexit join hangs exit."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-20T17:01:51.768Z
---

Judge wall-clock timeouts must run the upstream LLM call on a **daemon** thread,
NOT a `ThreadPoolExecutor`. `concurrent.futures` registers an `atexit` hook
(`_python_exit`) that **joins every executor worker regardless of
`shutdown(wait=False)`** — so a wedged upstream call (no socket timeout) pins
interpreter/process exit forever, and in tests hangs the whole run at shutdown.
A daemon worker is never joined at exit → abandoning one is always safe.

Helper (working tree, 2026-06-16): `turnstone/core/deadline.py::run_with_deadline(fn, *,
timeout, cancel_event, poll=1.0, thread_name)` → returns `fn()` / re-raises, or
raises `DeadlineExceededError` / `DeadlineCancelledError`. Own tests in
`tests/test_deadline.py` (pins daemon-abandon invariant). Use `functools.partial`
not a lambda at call sites in loops (B023).

**Shipped as PR #674** (base main; full suite green 7523 passed +
leak-clean suite-wide). **BOTH judges migrated**, verified: `OutputGuardJudge.evaluate()`
(regression `test_timeout_leaves_no_nondaemon_straggler`) AND
`IntentJudge._evaluate_single`/`_run_judge`. The IntentJudge migration **deleted
`_ExecutorPoisonedError` and the whole restart dance** — per-call daemon threads
can't poison a shared single-slot pool, so the "stuck worker → shutdown(wait=False)
→ new executor → fallback" machinery is gone; a timeout now just returns None →
generic fallback. NOTE: `_evaluate_single`'s per-turn timeout is floored at
`max(config.timeout, 5.0)`, so an e2e judge-timeout test would take 5s — the
invariant is pinned in test_deadline.py instead. See [[project_smart_approvals]],
[[project_output_guard_llm_merge]].

**Sweep of the other `shutdown(wait=False)` sites (2026-06-16, uncommitted):**
- `console/server.py::_validate_regex_pattern` (regex ReDoS probe) → MIGRATED to
  `run_with_deadline` (module-level import added). Highest-value: the abandoned
  worker is a catastrophically-backtracking regex with NO internal bound, so
  non-daemon = real exit-hang. Tested in `tests/test_validate_regex_pattern.py`
  (timeout branch monkeypatches `run_with_deadline` — a real ReDoS regex would
  leave a CPU-pinned daemon for the suite).
- `mcp_oauth.py::_PgRefreshLock` → LEFT BY DESIGN. Wrong shape: psycopg2
  **thread-affinity** (acquire+release must be the SAME worker thread), no
  timeout, deliberate drain-task for the cancel-orphan case. `run_with_deadline`
  (fresh thread per call) would BREAK it. Its `shutdown(wait=False)` is correct.
- `eval.py` (headless eval run) → LEFT (low priority): worker is already
  httpx-bounded (`run_client timeout=test_timeout`) + cooperative
  `session._cancelled`, so low hazard; offline `turnstone-eval` tool; no cheap
  test boundary (os.chdir + storage init + real session). Migrate + integration
  test if it ever surfaces. **Path update (2026-07-06):** this code moved in the
  eval/optimizer split ([[project_eval_optimizer_split]], PR #763, 2026-07-03) —
  the `ThreadPoolExecutor`/`shutdown(wait=False)` site now lives in
  `turnstone/eval/core.py` (~lines 542-584), not a top-level `eval.py` (which no
  longer exists). Verdict unchanged: still LEFT, still low priority.

Lesson: not every `shutdown(wait=False)` is the same nail — match the shape
(one blocking call + deadline) before reaching for `run_with_deadline`.
Also folded 6 `time.sleep(0.5)` daemon-waits in test_judge.py → the existing
`_wait_for` helper (2.92s → 0.99s, deterministic).

Lens ([[project_harness_compiler_dialect_stack]]): the wall-clock deadline is the **engineering termination guard** — a hard budget standing in for the unprovable Foster–Lyapunov bound; timeout → None → fallback, never waiting on a guarantee that can't be proven.

How it was found: throwaway pytest plugin diffing `threading.enumerate()` by
`id()` per test → flagged exactly 2 `test_output_guard_judge.py` tests leaking
`output-guard-judge_0`. CI pytest is now `-v` (not `-q`) so a future hang names
the culprit on the last line (pytest prints the nodeid at logstart). The
original "5-10% after 92%" CI hang in [[feedback_pre_commit_gates]]'s suite is
NOT this (bounded mock sleep → transient straggler); still open.

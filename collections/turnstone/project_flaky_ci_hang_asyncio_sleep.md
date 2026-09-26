---
name: project_flaky_ci_hang_asyncio_sleep
description: "Async test patching sleep, or CI-only hang at ~92% on 3.12+: never monkeypatch global asyncio.sleep; use a per-object _sleep seam (#674); poller leak unfound."
metadata: 
  node_type: memory
  type: project
---

The long-running flaky CI hang ("~5-10% of runs, after 92%", 3.12/3.13/3.14,
NEVER 3.11) was root-caused on PR #674 (2026-06-16).

**DURABLE RULE: never `monkeypatch.setattr(asyncio, "sleep", ...)` (or any
global stdlib coroutine) in async tests.** It replaces sleep for EVERY task on
the event loop, not just code-under-test.

Mechanism: `tests/test_tls_client.py` retry tests patched the *module-global*
`asyncio.sleep`. anyio's asyncio backend keeps a **persistent event loop across
the whole session**, so an un-cancelled background poller leaked by an earlier
test (a loop doing `asyncio.sleep(0.1)`) is still alive when the tls tests run
at ~92%. The global patch hijacked that poller:
- non-yielding stub → poller busy-loops → monopolizes the loop → **test HANGS**
  (the original CI hang);
- yielding stub → poller spins fast → floods the test's `sleeps` list
  (2275× 0.1 vs expected [1.0, 2.0]) → assertion failure on the test-postgres
  job — which is what finally **exposed** it.

Why it NEVER reproduced locally (the trap that burned ~300GB of logs + hours):
needs the leaked poller alive on the shared loop AND CI 3.12+ scheduling.
Tried and failed to repro: full suite, CPU affinity, scheduler de-tuning,
coverage permutations incl. xml, --cov on/off. NOT coverage (test-postgres has
no `--cov` and hangs too) → it's pure Python ≥3.12 + the shared-loop poller.

What cracked it: CI pytest `-q`→`-v` (this PR) named the hung test on the last
line (nodeid prints at logstart, no PASSED on a hang) → `test_init_retries_
transient_failure`; then the assertion flood named the 0.1 poller.

**FIX (shipped #674):** route `TLSClient.init()`'s backoff through a
`TLSClient._sleep(delay)` seam; tests stub `client._sleep` (same pattern as the
existing `_fetch_ca_cert`/`_request_cert` stubs), never the global. Also
`timeout-minutes: 20` on the test/test-postgres jobs (was riding GitHub's 6h
default → the multi-GB logs).

**RESIDUAL (unfixed, lower severity):** some earlier test leaks an un-cancelled
background poller onto the shared anyio loop. De-globalizing neutralizes its
blast radius (tls tests can't be corrupted) but the leak persists.

**2026-07-06 re-check: the three previously-cited `sleep(0.1)` candidates are RULED OUT** —
none is a background poller: `turnstone/core/session_routes.py:3981` (line drifted from
:3539) is a deliberate, bounded, well-commented wait (`for _ in range(30): await
asyncio.sleep(0.1)` — up to 3s, exits on `_worker_running` flip, guards cancel-then-dispatch
races); `tests/test_mcp_user_pool.py:847` and `tests/test_mcp_pool_auth_introspection.py:1096`
(line numbers also drifted) are each a single bounded `await asyncio.sleep(0.1)` inside a
mock `_call_tool` used to test concurrency limits, not a loop. **The actual leaked poller's
source is still unidentified.** Find it with a task-leak autouse fixture that diffs
`asyncio.all_tasks()` per test (asyncio analogue of the thread-leak detector) rather than
grepping for `sleep(0.1)` literals. See [[project_judge_deadline_daemon]].

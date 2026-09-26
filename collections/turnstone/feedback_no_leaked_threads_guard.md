---
name: feedback_no_leaked_threads_guard
description: "Writing a test that spawns a thread, loop or server: the conftest _no_leaked_threads guard fails it unless torn down or marked allow_thread_leak."
metadata: 
  node_type: memory
  type: feedback
---

`tests/conftest.py` has an autouse `_no_leaked_threads` guard (PR #678, off main 2026-06-17): any test that leaves a background thread running past teardown (5s shared grace-join) **fails**, listing the thread names. So a new test that spawns a daemon / event loop / server MUST tear it down — or mark `@pytest.mark.allow_thread_leak` to opt out.

**Why:** background daemons that outlive a test bleed into LATER tests' captured output → intermittent `ValueError: I/O operation on closed file` (a heisenbug — only reproduces across the full suite, never one module), and the same class behind a past multi-day CI-hang hunt. The guard turns a days-long heisenbug into an immediate, named failure. (Diagnostic finding: the actual leakers were the collector `console-discovery` thread, docker_healthcheck HTTP servers, and the MCP pool-auth `asyncio_N` loops + FastMCP uvicorn upstreams.)

**How to apply:**
- In-thread event loop → use the `stop_loop_thread(loop, thread)` conftest helper (shutdown_default_executor + stop + join + close).
- In-thread uvicorn test server → `serve_until_exit(server)` as the thread target + `timeout_graceful_shutdown=0` in the Config + `server.force_exit = True` at teardown (uvicorn graceful shutdown hangs forever on a held-open SSE/streamable-http stream).
- `logging.raiseExceptions = False` (conftest, process-global, test-only) mutes the benign logging-handler-vs-capture-teardown race.
- The closed-file noise is a pytest-capture artifact, NOT a production bug — but a leaked thread that won't *stop* often IS (e.g. PR #678 also root-fixed `ClusterCollector.stop()`: its discovery loop slept uninterruptibly so `stop()` couldn't join the thread; now sleeps on an interruptible Event). Always check whether a test leak points at a real shutdown bug in product code. Related: [[feedback_sdk_boundary_testing]] (root-cause hangs).

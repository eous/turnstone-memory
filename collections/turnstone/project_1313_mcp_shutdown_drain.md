---
name: project_1313_mcp_shutdown_drain
description: "#1313 MCP shutdown drain: the maintainer's rulings and the invariants to keep."
metadata:
  type: project
---

#1313 began as a 3.13 CI flake (garbage collection closing an abandoned MCP reconnect's
coroutines in no set order) and, at the maintainer's request, grew into making
`MCPClientManager.shutdown()` drain the client's work on its loop before stopping it. The LOCAL
design note is `docs/design/1313-shutdown-drain.md`.

**Maintainer rulings (2026-10-08):**
1. One shared deadline (`_SHUTDOWN_DEADLINE_S = 20`) inside a 30 s stop budget (systemd
   TimeoutStopSec, the Kubernetes default grace): admission wait 1 s + drain 20 s + result margin
   2 s + loop join 5 s.
2. A tool call the drain interrupted in flight records an UNKNOWN effect
   (`MCPShutdownError(started=True)`); one refused before it started records a plain error. Pool
   calls stopped before sending still report started=True: cautious, kept on purpose.
3. Never call `loop.shutdown_asyncgens()`: measured harmful, it exits anyio cancel scopes from
   another task. The httpcore `aclose ... never awaited` warnings in
   test_mcp_catalog_pagination.py also appear on dev.
4. A transport owner is never cancelled twice (anyio scope exits are bound to their host task).
   Shutdown escalates every owner in one place, `_close_owners`, after all other closers have
   finished, and cancels only owners with `cancelling() == 0`.
5. Admission is an in-flight counter under `_submission_cond`. A lock held across
   `run_coroutine_threadsafe` (a self-pipe write that releases the GIL) made submissions convoy
   under GIL contention. Primes take no lock.
6. The DELETE that ends a session has its own timeout (`_SESSION_END_TIMEOUT_S = 3`), below
   `_OWNER_CANCEL_GRACE_S`, so a server that never answers it cannot pin an owner whose one
   cancel is spent.
7. The startup pass and the operator reconnect re-check config and lock identity under the lock
   (`_static_config_if_current`). They are not routed through `_ensure_static_connected`, which
   would add its 45 s attempt bound and breaker records to startup.
8. Out of scope:
   - stdio-only consequences ([[feedback_stdio_findings_out_of_scope]]);
   - `GeneratorExit` arms beyond the connects and `_reconnect` (`_add` among them);
   - a closed-loop-tolerant lock release;
   - overlapping `shutdown()` calls.

**Invariants a change must keep:**
- `run_coroutine_threadsafe` is called only in `_submit_root` and `shutdown`, pinned by an AST
  test.
- Every transport owner is registered at creation with `_track_owner`, so a new owner creation
  site must call it.
- `_run_root` turns a cancel into `MCPShutdownError` only for roots the drain cancelled.

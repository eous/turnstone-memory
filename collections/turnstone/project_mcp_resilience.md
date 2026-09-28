---
name: mcp-client-resilience-hardening
description: "Touching mcp_client.py breaker/reconnect/background tasks (shipped #296/#660): keep mcp>=1.27,<2 until #679; keep closure layers thin; v2 keeps message_handler."
metadata: 
  node_type: memory
  type: project
---

**Date:** 2026-04-04. **Merged:** #296 on 2026-04-05.

## Problem

Misbehaving/failed/misconfigured MCP servers peg turnstone server CPU at 100%.
Root causes: MCP SDK v1.26.0 has unfixed bugs (anyio cancel-scope CPU busy-loop
SDK #2147, infinite reconnection counter reset), and the application layer had
no circuit breaker, future cancellation, or backoff.

## Solution — 5 fixes in `turnstone/core/mcp_client.py`

1. **Cancel orphaned futures** — `future.cancel()` after `TimeoutError` in all 4
   sync bridge methods. Prevents coroutine accumulation on the event loop.

2. **Per-server circuit breaker** — Threshold=3 failures, exponential cooldown
   (30s base, 300s max) with deterministic per-server jitter. Auto-reconnect
   on half-open probe. Session eviction on transport death.

3. **Safe transport stream pre-close** — Closes HTTP transport streams before
   `AsyncExitStack` teardown. Prevents anyio zero-buffer CPU busy-loop.

4. **Notification debounce** — 5s per-server rate limit on `list_changed` refresh.

5. **Periodic refresh backoff + auto-reconnect** — Disconnected servers get
   reconnection attempts with exponential backoff (60s base, 3600s max).

## Key design decisions

- Servers auto-reconnect with fuzzy backoff, never permanently disconnected.
- All fixes are application-layer wrappers around the MCP SDK's known bugs.
- Circuit breaker is independent per server (lightweight dict-based state).
- Pin `mcp` below 2 to avoid the v2 breaking rewrite. `pyproject.toml` carries `mcp>=1.27,<2`, and the v2 migration is #679 (release label `1.9`; upstream was at 2.2.0 on 2026-09-28). Its failure-classification traps are in [[project_679_mcp_sdk_v2]].
- **Keep closure-factory layers thin** (the maintainer's ruling, 2026-07-14, made because of the problems that pattern causes). This reshaped the dedup proposed in issue #842: keep thin binding closures, and dedup the protocol as a plain parametrized method. Closure-captured name/key bindings that outlive their target's removal are the bug class behind the lock/entry-identity recheck family in the notification runners.
  - Correction (verified on `mcp` 2.2.0, 2026-09-28): this note used to say v2 removes `ClientSession(message_handler=...)` closures. It doesn't; v2 keeps that constructor callback. The factory v2 removes is streamable HTTP's `httpx_client_factory`: callers now pass a pre-built `httpx2.AsyncClient`. The ruling itself is unchanged; only its v2 premise was wrong.

**Why:** Production CPU pegging from misbehaving MCP servers.
**How to apply:** Reference when touching MCP client code. Circuit breaker
constants are class-level on MCPClientManager.

## 6th fix — background-task tracking (PR #660, 2026-06-11)

Root cause of the long-flaky CI ("60-min hangs" + a caught mid-suite
`ValueError: I/O operation on closed file`): `_cb_auto_reconnect`'s catalog
refresh was a bare `create_task` — GC-able mid-flight (refresh could silently
never run) + exception reported only at GC time on whatever stream was attached
(pytest had closed it). Fix: `_spawn_background(coro,label)` (strong-ref set +
done-callback retrieves/logs; **discard runs LAST** so set-emptiness ⇒
done-AND-reported); `shutdown()` drains tracked tasks FIRST; the shared test
fixture now cancel-drains, joins loudly, and `loop.close()`s.

**Later completion of this arc:** dead-transport detection + session eviction was
finished by #741 (`f585c47b`) and the follow-up **#742** — see
[[project_mcp_dead_transport_followup]].

**Durable gotchas:** (1) turnstone logs via structlog — **caplog cannot observe
it**; assert via a patched module logger (`patch("...mcp_client.log")`), and
the logger name is `"turnstone.mcp"`, not `__name__`. (2) The pre-commit review
caught a discard-vs-unpatch race in the first test version — poll the mock
INSIDE the patch context, never gate on set-emptiness alone. (3) The eviction
task + auth-race task pair were already correctly referenced/awaited — audit
found exactly one bare site. If CI hangs persist after this, the next artifact
should be clean enough to read (the cross-test loop/task bleed is gone).

---
name: Use asyncio.timeout (not asyncio.wait_for) when wrapping aclose / async cleanup that touches anyio scopes
description: "asyncio timeouts: around cleanup that exits anyio scopes use asyncio.timeout, never wait_for; to end a wait on a future you keep, asyncio.wait, not wait_for(shield) (3.14 logs)."
type: feedback
---
When wrapping an async cleanup operation with a timeout — especially one that exits an `anyio`
cancel scope (e.g., `AsyncExitStack.aclose()` on a stack containing `streamablehttp_client(...)`,
`BaseSession(...)`, or any other anyio-using context manager) — use `asyncio.timeout` (the context
manager), NOT `asyncio.wait_for`. Python 3.11's `asyncio.wait_for` wraps the inner coroutine in a
fresh `asyncio.Task` via `ensure_future`; that fresh task can't exit anyio cancel scopes entered in
the calling task and raises `RuntimeError('Attempted to exit cancel scope in a different task than
it was entered in')`.

```python
# ❌ Breaks on Python 3.11 if `stack` contains anyio scopes entered in the current task
await asyncio.wait_for(stack.aclose(), timeout=5)

# ✅ Works on 3.11+ — `asyncio.timeout` runs the inner code in the current task
async with asyncio.timeout(5):
    await stack.aclose()
```

**Why:** A real incident: `_safe_close_stack` used `await asyncio.wait_for(stack.aclose(), timeout=5)` to bound aclose duration. On Python 3.13 it ran fine because 3.12+'s `asyncio.wait_for` was rewritten to use `asyncio.timeout` internally (no task wrapping). On Python 3.11 the same code spawned a fresh task for `stack.aclose()`; that task tried to exit the SDK's `streamablehttp_client` anyio cancel scope (entered in the original dispatch task) and got `RuntimeError: Attempted to exit cancel scope in a different task than it was entered in`. CI's test (3.11) failed; tests on 3.13 passed. The marker bug masked it for one earlier CI run, so this was the first time the code path actually hit 3.11. Fix: switch to `asyncio.timeout` — equivalent semantics, current-task execution, works on 3.11+.

**How to apply:** Default to `asyncio.timeout` for any timeout-wrapping of an async operation. Reserve `asyncio.wait_for` for the cases where you specifically want the wrapped coroutine to run in a separate task (rare). When porting old code that uses `wait_for`, the conversion is mechanical: `await asyncio.wait_for(coro, timeout=N)` → `async with asyncio.timeout(N): await coro`. If the codebase still supports Python <3.11, `asyncio.timeout` is unavailable and `wait_for` is the only option — but those code paths can't safely cross anyio boundaries either way.

## Ending a wait on a future you keep (Python 3.14)

To stop waiting on a future after N seconds while its work goes on (a thread-pool submission you
still mean to await or cancel), use `asyncio.wait({fut}, timeout=N)`, which cancels nothing, and
cancel `fut` yourself when your own task is cancelled. `asyncio.wait_for(asyncio.shield(fut), N)`
looks equivalent, but on 3.14 the timeout cancels the shield's outer future, and shield then adds
a done callback that reports any later exception of `fut` through the loop's exception handler: an
ERROR log with a traceback for a failure the caller already handled. 3.13 only marks it retrieved.

**Why:** Found in review of the #1485 dictation pool (2026-10-27): every dictation refused after
its budget logged "AudioBusyError exception in shielded future" while answering a correct 429.
CI runs 3.13 and 3.14 and the image is 3.14, so a 3.13-only check would not have shown it. A test
that installs a recording exception handler and asserts it stays empty pins the fix.

**How to apply:** Reach for `asyncio.wait` whenever the timeout should end the wait, not the
work. Keep `asyncio.timeout` (above) for an awaitable that should be cancelled at the deadline.

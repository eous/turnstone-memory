---
name: project_mcp_flaky_cpu_spin_regression
description: "MCP CPU spin or armed anyio CancelScopes after a server flap: FIXED PRs #787/#788 (2026-07-07) via transport owner tasks; never cancel a connect task twice."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-20T17:04:31.634Z
---

Regression of the original 100%-CPU incident ([[project_mcp_resilience]],
SDK #2147 family), reintroduced by the automated-recovery work in
[[project_mcp_dead_transport_followup]] (#768's `_static_health_loop` +
`_ensure_static_connected` unification). Diagnosed 2026-07-06 by live repro;
FIXED same day — see the FIX section at the bottom.

## Root cause (bug 1 — the CPU spin, REPRODUCED)

Flap repro (real FastMCP streamable-http subprocess SIGKILLed every 5s, back
after 3s; compressed constants) drives the mcp-loop thread to sustained 100%+
that climbs each cycle and never recovers. Verified mechanism, via a patched
`Handle._run` counter + GC scope autopsy:

1. Health tick reconnect runs `_connect_one_locked` UNDER
   `asyncio.timeout(_STATIC_RECONNECT_ATTEMPT_TIMEOUT_S)` (and pings under
   `asyncio.timeout` too). The SDK's `streamablehttp_client` anyio TaskGroup
   CancelScope registers the health task as HOST task.
2. Server flaps mid-handshake/teardown → outer timeout CANCELS the host task
   while the async cleanup (`stack.aclose()` → TaskGroup `__aexit__` → scope
   exit; or `_safe_close_stack`'s own 5s timeout) is still running. Pending
   cancellation re-fires at the cleanup's first await; `_safe_close_stack`
   suppresses and returns → **scope `__exit__` never completes**.
3. Health loop's `gather(return_exceptions=True)` absorbs the failure; the
   host task FINISHES while still registered in `scope._tasks`.
4. anyio 4.14.1 `_deliver_cancellation`: `should_retry = True` for ANY task
   still in `_tasks`; `task.cancel()` on a done task is a no-op → it
   reschedules itself via `call_soon` EVERY loop iteration, forever
   (~900k callbacks/s measured). One more armed zombie scope per flap cycle
   (autopsy: 3 armed @t=25s → 6 @t=50s), so CPU climbs stepwise.

Key asymmetries from the repro: refused/stall/RST modes do NOT spin (TCP
probe + teardown paths hold); only full flap (connect SUCCEEDS or enters the
task group, then dies) produces zombies. Task/FD/thread counts stay flat —
gc-walking `CancelScope` objects with `_cancel_handle is not None` is the
only visible signature, plus `_deliver_cancellation` dominating a
`Handle._run` counter. py-spy-style sampling is GIL-starved and misleadingly
shows `selector.select` (observer bias).

## Bug 2 — silent loop death (RST mode)

`_connect_all` catches per-server `except Exception` — an anyio
`BaseExceptionGroup` (raised when the group contains a CancelledError, e.g.
accept-then-RST during initial connect) is a BaseException, ESCAPES the
handler, and `_connect_all` dies before creating `_static_health_task` /
`_user_token_sweep_task` → no autonomous recovery at all, silently (start()
just times out its `_connected.wait`). Same class of hole wherever
`except Exception` guards SDK-transport awaits (`_static_health_loop`'s
`except Exception` arm would also miss a BaseExceptionGroup escaping a tick).

## Fix directions (as discussed at diagnosis time; the first two were built — see FIX below)

- Architectural: replace cancel-the-shared-task timeouts around connect with
  a DEDICATED connect task per attempt (`asyncio.wait(…, timeout)` +
  cancel-then-AWAIT-fully). One cancel delivered once, cleanup runs in-task
  (same-task scope exit preserved), waiter never abandons a mid-exit scope.
- Contain: after teardown failure, detect-and-disarm armed zombie scopes
  (`scope._cancel_handle.cancel()`, drop done tasks from `scope._tasks`) —
  internals-poking, last resort / belt-and-suspenders sweeper.
- Bug 2: catch `BaseExceptionGroup` (or `BaseException` + re-raise genuine
  cancels) at `_connect_all`'s per-server guard and in both loop bodies.
- Upstream: anyio `_deliver_cancellation` should skip done tasks (no-progress
  retry loop); check anyio >4.14 changelog before pinning any workaround.
  mcp v2 (#679) restructures transports — revisit after migration.

Repro harness recipe (scratchpad, ephemeral): FastMCP server subprocess on a
fixed port; SIGKILL@5s/restart@3s cycle; MCPClientManager with
`static_health_check_seconds=2`, `_CONNECT_TIMEOUT=4`,
`_STATIC_RECONNECT_ATTEMPT_TIMEOUT_S=6`, `_STATIC_RECONNECT_MAX_S=4`;
measure /proc/self/stat CPU + patched `asyncio.events.Handle._run` Counter +
gc scan for armed CancelScopes. ~60s to first zombies. No live killable-server
smoke test exists in the suite (known gap in
[[project_mcp_dead_transport_followup]]) — this recipe should become one.

## FIX (2026-07-06, same day — commit bdc46d2a on fix/mcp-cancel-scope-zombie-spin)

Worktree `<worktree>` (own uv venv — main venv's editable
install points at the main checkout). Pushed as PR #787 (static) with
stacked PR #788 (pool) on top — see the pool section below.

**Architecture — the anyio host-task invariant, enforced:**
- `_static_transport_owner`: ONE long-lived task per static server enters
  transport + ClientSession cms, initializes (same-task `asyncio.timeout`
  phase bounds), signals a readiness future, parks on a `close_requested`
  event, and unwinds everything in-task. `StaticServerState.stack` REMOVED
  (the exit stack is an owner-coroutine local — unreachable, so nothing can
  aclose it cross-task); added `owner_task` + `close_requested`.
- `_teardown_static_session` close protocol: null session → set close event
  BEFORE first await → pre-close streams → graceful wait
  (`_OWNER_CLOSE_GRACE_S` 5s) → at most ONE `cancel()` → wait
  (`_OWNER_CANCEL_GRACE_S` 5s) → if still unwinding, leave it (solo
  completion is harmless; a SECOND cancel mints the zombie). Unit test pins
  exactly-one-cancel via a counting wrapper.
- Unrequested owner death (server died under live session) → done-callback
  `_on_static_owner_death` evicts session instantly (faster than the 30s
  ping; identity-guarded so a stale callback can't evict a fresh session).
- `_maybe_disarm_orphaned_scopes`: rate-limited (30s) gc-walk backstop,
  disarms armed scopes whose tasks are ALL done — scoped to scopes HOSTED on
  the mcp-loop (`host.get_loop() is self._loop`): the walk is process-global
  and turnstone-server runs FastAPI/httpx anyio scopes on the main loop;
  cross-thread handle.cancel()/set-clear is unsafe (review finding).
- Bug-2 arms: `except (Exception, BaseExceptionGroup)` in `_connect_all`
  per-server guard, `_static_health_loop`, `_user_token_sweep_loop`,
  `_user_pool_eviction_loop`, `_static_reconnect_one`, `_refresh_all`,
  `_cb_auto_reconnect` boundary. Genuine shutdown still stops loops (bare
  CancelledError at the loop task; swallow arms re-raise pending cancel at
  next await).

**Verified:** flap repro 130%+ climbing → 0.3% flat, 0 armed scopes; RST
repro loops now survive (were both silently dead); stall/refused stay clean.
1007 mcp tests + full 8470-test suite green; ruff+mypy clean. Adversarial
review (code-reviewer agent): core protocol confirmed correct; both majors
(cross-loop disarm reach, live-test gating) fixed same-session.

**New tests:** `tests/test_mcp_transport_owner.py` (owner lifecycle,
caller-cancel-mid-connect cm-exit guarantee, bug-2 regressions,
discriminating disarm sweep) and `tests/test_mcp_live_flaky_server.py` —
the previously-missing killable-server smoke test: real FastMCP subprocess,
3 SIGKILL flaps, ~10s, `pytest.importorskip` + skip-on-no-bind, asserts
0 armed scopes / 1 live owner / health loop alive / backstop unused /
post-recovery tool call round-trip.

**Open follow-ups:** (1) oauth_user POOL path (`_connect_one_pool`,
`_close_pool_entry_if_idle`, pool teardowns) still uses cross-task closes —
same latent zombie class, currently covered only by the disarm backstop;
migrate to the owner pattern. (2) mcp v2 migration (#679) restructures
transports — revisit both then. (3) Test-fixture hygiene: `running_loop_mgr`
fixtures that drive `_connect_all` must drain `_static_health_task` (done in
test_mcp_user_pool; the loops now reliably start where they previously died
silently, so undrained fixtures leak tasks at GC).

## Pool-path migration (same day — commit 3879dd1e, PR #788 stacked on #787)

Implemented by an implementer agent from a self-contained plan; adversarially
reviewed (approve, zero defects; its one suggestion — direct coverage for the
`_await_pool_discovery` owner-death branch — was added before commit).

- `_pool_transport_owner` per (user, server) entry; caller still builds
  `client_kwargs` (bearer + auth-capture `httpx_client_factory`) so
  401/WWW-Authenticate carrier semantics are untouched.
- `_teardown_pool_entry` = shared one-cancel protocol; used by connect
  stale-guard, `_close_pool_entry_if_idle` (eviction interlock semantics
  preserved), and parallel shutdown `_close_all_pool`.
- `_on_pool_owner_death`: evict session, KEEP entry+catalog (the auth_401
  retry + bound_token rotation depend on that shape).
- **`_await_pool_discovery(owner, coro)`** — the one deviation from the static
  pattern, and a real find: discovery runs in the caller while the transport
  is owner-hosted, so a transport collapse mid-discovery (SDK tears its task
  group on an upstream 401) cancels the OWNER and the caller's await would
  hang to the 30s phase timeout. The helper races discovery vs owner
  completion → prompt ConnectionError; never cancels the owner; carrier-first
  classification keeps captured 401s as auth_401. Found because the literal
  plan made `test_pool_connect_list_tools_401_propagates` hang — the sentinel
  did its job.
- `_safe_close_stack` + `_safe_teardown_on_connect_failure` DELETED (zero
  callers). `test_integration_pool_reuse_401_refresh_and_retry_succeeds` is
  the historical cross-task-anyio sentinel — keep it green forever.
- Gates: 1010 mcp tests, full suite 8471 green, zero destroyed-task warnings.

**Remainder: RESOLVED** (commit 8335790e on #788): helper renamed
`_await_owner_discovery`, wired into `_connect_one_locked`'s four discovery
awaits (static fast-fail <1s vs ~45s hang), plus a Copilot-review fold-in —
a discovery future that completes CANCELLED without the race's own reap
converts to ConnectionError instead of leaking a bare CancelledError.

**Review-feedback round (2026-07-06, both PRs):** #787 got 7be2f6d1 —
(a) `_maybe_disarm_orphaned_scopes` now enforces running-loop-is-mcp-loop
(returns 0 without advancing the rate-limit clock otherwise; Copilot
finding), (b) both transport owners' `except BaseException` arms re-raise
interpreter-level exits (KeyboardInterrupt/SystemExit) AFTER delivering to
the readiness future. Six CodeQL "statement has no effect" alerts on
test-file suppress-awaits were false positives (synchronization awaits — the
module's own shutdown idiom); replied + resolved without code change. All
threads on both PRs replied to and resolved via resolveReviewThread. #788's
branch carries #787's fixes via a regular merge commit (never force-push a
PR branch).

## Merge + final bot round (2026-07-07)

**#787 shipped to main via REBASE-merge** (new SHAs). Two more
code-quality rounds before merge, both addressed: (1) the owner arm became
targeted-catch `(BaseExceptionGroup, Exception)` + a `finally` that resolves
the readiness future with ConnectionError for ANY undelivered BaseException —
strictly stronger than the bot's suggested split (which would leave the
waiter hanging; `_connect_all`'s initial connect has no outer bound).
Durable asyncio finding from the test that caught it: **SystemExit /
KeyboardInterrupt raised in a task propagate out of `run_forever` and STOP
THE LOOP** — un-assertable in-process; test uses a custom BaseException
subclass instead. (2) Test waiter catches narrowed to explicit types
(`(Exception, <expected-regression-type>)`), no bare `except BaseException`
in the new tests.

**#788 rebase-merge fallout:** GitHub retargeted it to main, but the
rebase minted new SHAs for content the branch carried via branch-merges →
3 conflicted files at the stale merge-base, all where #788 built ON TOP of
#787 (deleted `_safe_close_stack`/`_safe_teardown_on_connect_failure`,
pool-aware disarm docstring). Branch was a strict HEAD-superset → resolved
with `git checkout --ours` after verifying zero main-only lines, merged
origin/main (regular merge, never force-push a PR branch). Gates green (1013 mcp / 8475 full), all threads resolved.

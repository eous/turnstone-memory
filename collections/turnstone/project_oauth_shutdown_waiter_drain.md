---
name: project_oauth_shutdown_waiter_drain
description: "OAuthRuntime shutdown drains tracked waiters (1590f31d, 09-25); keep loop.stop off the drain's last iteration; submit() only on the owner loop; declined review points not to re-litigate."
metadata:
  node_type: memory
  type: project
  modified: 2026-09-26T04:56:54.595Z
---

The CI flake in `test_shutdown_retrieves_worker_failure_after_cancellation` (surfaced by the
lock-maintenance PR #1204, 3.14 lane) was a real race: a waiter's outcome hop and shutdown's
`loop.stop` ran in the same final loop iteration, so the waiter's failure was set but its
retrieving callback never ran → "Future exception was never retrieved" at GC. Fix 1590f31d on
`fix/oauth-shutdown-waiter-retrieval`: `OAuthWork.waiters` (added by `wrap()`, removed only by
the retrieving done callback), a waiter per worker created in `submit()`, drain settles on
waiters instead of wrapping workers. Opened as PR #1207 against dev (CI all green 09-25); once it
merges, re-run the lock-maintenance PR #1204's CI (its failure was this flake).

**Constraints not visible in one place (round-3 sanity pass):**
1. The drain exits when every waiter is *done*; retrieval runs one iteration later. Safe only
   because `shutdown()` stops the loop from its own thread after the drain returns. Any
   restructure that stops the loop from inside the drain must wait for `work.waiters` to empty.
2. `submit()` must run on the owner loop (it builds the waiter). `current_work()` also resolves
   on worker threads through the copied context, so a sync helper calling `submit()` there
   would break the invariant.
3. The drain sees only waiters built by `work.wrap()`; a direct `asyncio.wrap_future` bypasses it.

**Settled, don't re-litigate:** the cross-thread `tuple(set)` snapshots in `_warn_outstanding`
are atomic on GIL builds (0 errors in ~2.4M probed snapshots on 3.13/3.14; GC runs only at the
eval breaker since 3.12; free-threaded builds unsupported) — raised and declined in rounds 2 and
3. The submit waiter's extra hop (~20 µs per write, measured) and the waiters figure in the
budget warning (round 1 asked for it) were declined as nits.

Related: [[project_963_oauth_extraction]] (shutdown shape), [[feedback_finish_the_fix_spree]].

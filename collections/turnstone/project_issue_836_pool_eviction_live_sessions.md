---
name: project-issue-836-pool-eviction-live-sessions
description: "MCP per-user pool eviction dropping tools from live sessions (#836, fixed in PR #840): cool the transport but keep the catalog; only explicit revoke drops it."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-20T17:01:43.115Z
---

## Current state (2026-09-05 header)

- Status: FIX SHIPPED as PR #840 (branch `fix/mcp-pool-evict-836`, 9 commits, Closes #836, head 842d099b); the maintainer ended the review loop at round 8 (correctness trend R6=5 → R7=4 → R8=1); the code-quality bot's 5 inline comments were validated as false positives and CLOSED OUT 2026-07-14 with the maintainer's approval. Backport to stable/1.7: the maintainer leaning NO, final call still their as of 07-14.
- Fix shape: idle-TTL eviction COOLS entries of users with a live tool listener (transport closed, catalog kept) instead of dropping the catalog; `_evict_session` retains the catalog (owner-death semantics) and `_evict_session_drop_catalog` exists only for explicit revoke; retention requires `_is_pool_server` so admin delete/disable/rename/flip ghosts drop within one 30s tick; the LRU cap counts warm entries only; dead-grant drops from dispatch/prime converge cross-node revocation at first touch; the round-3 `catalog_gen` protocol was STRIPPED at the maintainer's call in round 4 in favor of entry-identity checks.
- Sibling findings: push-driven `list_changed` refresh never worked (in-handler self-deadlock) — pool path fixed here, static path tracked as #839; oauth_obo lifecycle is covered by the shared pool.
- Open / unfiled as of 07-14: pre-existing "(R6)" and memory-file-citation comments on main (mcp_client ~2344/3657/3732) as a cleanliness nit.
- Repro at full fidelity: `test_close_pool_entry_if_idle_cools_entry_for_live_session_user` (tests/test_mcp_user_catalog.py).

---

# Issue #836 — pool idle-eviction removes MCP tools from live sessions (verified 2026-07-13, no fix yet)

Report: every code anchor verified correct on main @ b2b8b6f6 (worktree `worktree-fix-oauth-user` used for the investigation, read-only).

**Verified chain**: `_close_pool_entry_if_idle` (mcp_client.py:3010) after idle TTL (600s default, :731; tick 30s) does `_teardown_pool_entry` → pop entry → `_rebuild_user_tool_map` (empty → pops user key, :3189) → `_notify_user_tool_listeners` → ChatSession `_on_mcp_tools_changed` rebuilds to builtins-only. No recovery: only 3 prime sites (session.py:1729 construction; :5844 acting-user CHANGE, same-user send early-returns at :5822; mcp_client.py:4824 reconcile self-heal). `is_mcp_tool` (session gate session.py:9502) goes False → even history-motivated tool calls hit "unknown tool". `last_used` bumps ONLY at connect (:2413) + dispatch (:6770) — "idle" = no MCP dispatch, not user inactivity.

**Report's one inaccuracy strengthens it**: claimed prime fires "at consent completion" — it does NOT (grep-verified). Re-consent genuinely can't recover, matching their symptom.

**oauth_obo equally affected**: same `_user_pool_entries`, eviction is auth-type-agnostic, prime covers both (:2524) and for obo priming is the ONLY catalog path. obo = main-only (1.8). oauth_user half ALSO in stable/1.7 (TTL at its :718) → **backport candidate**.

**Fix assessment (reporter's fix a is the right shape)**:
- Fix (a) retain-catalog-on-TTL-eviction is ALREADY a designed state: `_on_pool_owner_death` (mcp_client.py:2058) does literally "evict-session-keep-entry — the next connect reuses the discovered catalog". `_teardown_pool_entry` doesn't touch entry.tools (callers own catalog cleanup). Dispatch (`_ensure_pool_entry` + connect-or-reuse in `_dispatch_pool_with_entry`) and `_prime_one` both treat session=None as reconnectable.
- Counter-precedent: 401 path `_evict_session` (:6598) CLEARS catalog — but there auth is broken; idle eviction is hygiene (nothing changed), belongs with owner-death semantics. Deliberate-drop comment at :3048 predates this distinction.
- Fix (b) re-prime is worse: on-eviction re-prime defeats eviction (parked sessions keep-warm forever); on-next-send re-prime leaves the first post-idle turn toolless (prime is fire-and-forget, completes after tool-list build).
- **Gaps in (a) as proposed (my refinement)**: (1) LRU-cap pass (`user_session_lru_max` 200, :732) still full-drops — same bug at cap pressure, EXISTS TODAY too; (2) retained cold entries would be re-torn-down every 30s tick without an already-cold guard; (3) departed users' cold entries linger to cap. Recommended shape: TTL pass = listener-aware (user has live tool listener → transport-close-keep-catalog; no listener → today's full drop); LRU pass = full drop + re-prime live-listener users (reuse `_schedule_pool_reprime` machinery from 86253a3, :4800).

**SIBLING BUG (found 2026-07-13, NOT in #836)**: `_evict_session` (:6598) is also called on dispatch-observed failures — auth_401 (:6267), auth_403 (:6311), transport (:6326) — and CLEARS the catalog. 401's immediate retry repopulates on success, but a double-401, any 403, or a transport blip during a tool call leaves the catalog cleared → same permanent live-session tool loss TODAY, no TTL needed. Consequence: retain-on-TTL-evict alone survives idleness but dies on the first blip; the fix must convert `_evict_session` to owner-death semantics (null session, KEEP catalog, no rebuild/notify) — which also makes the breaker half-open recovery and the consent/step-up cards actually reachable (today they're dead ends for live sessions: gate session.py:9502 closes once the catalog clears). Failure ladder with retained catalog is all designed rails: cold+healthy → transparent reconnect (one initialize RTT, re-discovery corrects drift + notifies); server down → tool-error result + breaker (open = clean RuntimeError w/ cooldown + '/mcp refresh' hint); dead token → `mcp_consent_required` structured error → consent card/badge (docstring :7172: "so the LLM can narrate ... rather than crashing the workstream").

**Branch `fix/mcp-pool-evict-836`** created off origin/main in worktree `<worktree>` (the maintainer 2026-07-13: keep work in this worktree — main checkout has the #827 refactor in flight; do NOT wait on it). No fix code written yet.

**FIX BUILT 2026-07-13, commit d2a1e4f6 on `fix/mcp-pool-evict-836`** (worktree branch off origin/main): `_evict_session` retains catalog; new `_evict_session_drop_catalog` for explicit revoke (wired to `evict_user_session`; the disconnect endpoint is its ONLY caller and 409s obo); TTL cools live-listener users' entries (tool-listener registry = liveness signal; `_entry_has_catalog` guard drops stubs); LRU cap counts WARM entries only. Full suite 9145 green, mypy strict clean. First review round at XHIGH per the maintainer (event-driven path) — an earlier high run was user-stopped mid-flight.

**CONFIRMED REGRESSION in d2a1e4f6 (self-found + matched a stopped-run finder candidate), fix queued for post-review fix round**: `remove_server_sync` is static-path only — NOTHING purges per-user pool entries when an admin deletes/disables/renames/flips a pool server (pre-fix the TTL drop self-healed ghost tools ≤10min; cooled retention makes them IMMORTAL for live-listener users, dispatch errors "Unknown MCP tool" forever). Fix: retention conditions (TTL cold-skip + cooled-return in `_close_pool_entry_if_idle`) must also require `_is_pool_server(server_name)` — the in-memory pool registries are rebuilt wholesale each reconcile and are the documented existence source of truth; ghost entries then drop ≤1 tick (30s), better than pre-fix. Also restores the memory bound (orphans were unbounded).

**obo lifecycle sweep 2026-07-13 (the maintainer asked)**: (1) #836 eviction applies to obo equally — fix covers it via shared pool. (2) Bulk-revoke/cache-flush performs NO pool eviction by design (console/server.py:11098 docstring); stale sessions 401→refresh/re-mint→retry; retained catalog makes flush seamless AND repairs the documented oauth_user bulk-revoke fallback (pre-fix the 401-evict cleared the catalog, making the consent_required card a dead end for live sessions). (3) obo credential unlink: missing-credential lookup errors return BEFORE any eviction (pre/post-fix identical); tools stay visible with the honest re-login rail. (4) auth flips: reconcile registries + re-prime self-heal cover pool-bound flips; the `_is_pool_server` refinement cleans pool→static/deleted cooled entries.

**XHIGH ROUND 1 DONE 2026-07-13 (RESUMED via resumeFromRunId+same-args —
18/28 agents cache-recovered)**: 31 candidates → 30 kept, 1 refuted, 14 reported; cap accounting
CLEAN (14 primaries + 16 merge locations = 30, zero dropped). **FIX ROUND commit `90c8c6a0`** (gates
green, full suite 9148): registry-liveness via shared `_retain_cooled` (delete/disable/rename/flip →
ghost drops ≤1 tick; flip WITHIN pool types retains); dead-grant dispatch drop
(`_DEAD_GRANT_LOOKUP_KINDS` = missing+refresh_failed → `_drop_catalog_locked` at 3 lookup sites + 3
double-401 ceilings) = cross-node disconnect converges at first touch (the maintainer chose this
over cluster fan-out; re-consent heals via EXISTING `schedule_prime_user_server` at
mcp_oauth.py:3652 — my earlier "no consent-completion prime" claim was WRONG, only the multi-server
prime_user_pools is absent there); revoke interlock (open_lock serialization kills the
connect-resurrection race); per-tick listener snapshot + incremental LRU close-counting; bound_token
cleared on session drop; status falls back to cooled catalog + `user_pools_idle` field; session
construction re-reads merged lists post-listener-registration. DEFERRED per the maintainer:
shared-workstream non-acting participants (document; next send re-primes), pre-existing
orphaned-lock full-drop race. Old memory line about round-1 in-flight superseded by this. **ROUND 2
(high) DONE 2026-07-13**: 15 candidates → 14 kept, 1 refuted, 10 reported + 2 NAMED trivial
omissions (accounting clean). 5 CONFIRMED correctness in MY round-1 code, ALL FIXED commit
`9e91119b`: (1) lookup-site drop awaited open_lock held across whole SDK calls → sync timeout +
breaker hit for token-side errors → drops now `_spawn_background`-SCHEDULED; (2) double-401 drop
REMOVED — refresh-succeeded-then-401 = RS rejecting a fresh bearer (JWKS lag/audience/skew), NOT
dead grant; revoked grants converge via lookup (row gone); (3) `_lookup_grant_dead` single-source
classifier GATED on token_store+storage wired (obo kind=missing fires on boot-window infra absence —
mcp_oauth 2378/2386); (4) LRU per-iteration LIVE `_warm_pool_count` recount restored (one-shot
`over` blind to concurrent warm-set changes); (5) `_on_pool_owner_death` bound_token clear (3rd
session-drop site). Cleanups: zero-delta fan-out guards, constructor single post-registration read,
adjacent registry stores + DOCUMENTED flip-tear residual in `_retain_cooled`, direct
`_drop_catalog_locked` schedule in evict_user_session. Suite 9149 green. Convergence: R1=9
correctness, R2=5 → round 3 owed.

**ROUND 3 (high) DONE 2026-07-13**: 18 verified → 0 refuted → 10 reported (7 correctness: 5
CONFIRMED + 2 PLAUSIBLE). ROOT CLASS: catalog publishers never re-validate revocation state
(refresh-path republish-after-drop, dispatch/prime read-token-before-lock stale-bearer connect,
prime never drops dead grants, obo no restore after drop, torn mid-discovery publish). **ALL FIXED
commit `e8bfb82e`** with ONE primitive: `PoolEntryState.catalog_gen` bumped by
`_evict_session_drop_catalog`; refreshes snapshot+discard on move; dispatch/prime snapshot
pre-token-read → `_connect_one_pool(expected_gen=...)` raises `_PoolGrantRevokedError` (non-breaker)
on mismatch. Plus: staged discovery publication (all 3 catalogs land together in wiring block);
`_prime_one` schedules the shared `_schedule_dead_grant_drop`; obo re-login prime (auth.py
capture-success → prime_user_pools + 2 oidc handler tests); session `_mcp_tools_change_seq`
mirror-race re-read; tracked revocation drop task. Dedup: `_pool_lookup_verdict` single
classification (LITERAL code strings kept — the consent-url sibling audit scans literals, count
bumped 7→5); `PoolEntryState.drop_session()` structural pairing. GOTCHA: adding params to
`_prime_user_server`/`_connect_one_pool` broke ~8 test stubs w/ old signatures (introspection file)
— updated. Suite 9154 green. Convergence: R1=9, R2=5, R3=7 → round 4 owed (need 2 consecutive
0-correctness rounds).

**ROUND 4 (high) DONE 2026-07-13**: 25 candidates → 23 kept (2 refuted) → 10 reported + 3 named
omissions. 6 CONFIRMED correctness — ALL inside round-3's catalog_gen machinery (constructor crash:
mirror-race re-run called `_on_mcp_tools_changed` before `_tool_search` init; ensure-before-lookup
reorder made fresh stubs (last_used=0.0) eviction-eligible mid-lookup → orphaned lock/split mutual
exclusion; gen no memory across entry re-creation + reset-to-0 on re-ensure; un-timeboxed refresh
list_tools; `_PoolGrantRevokedError` raw to session layer). **Maintainer decision: STRIP the gen
protocol, keep the core** (option over manager-level epochs / keep-point-fixing). **DONE commit
`0c29c43a`** (net −72 lines): gen field + threading + reorders + exception REMOVED; refresh guards
keep entry-IDENTITY check only; publisher-suspended-across-drop races = ACCEPTED RESIDUALS
documented at `_evict_session_drop_catalog` (ghost self-heals at next use via dead-grant drops from
dispatch+prime; stale-bearer reconnect bounded by AT expiry — same bound warm sessions already
ride). KEPT from R3: staged discovery, prime drops, obo re-login prime, `_pool_lookup_verdict` (now
Literal-typed), drop_session(), tracked drop task. R4 orthogonal fixes: constructor bounded re-read
LOOP (never call the callback mid-construction), refresh asyncio.timeout, login prime gated on
`has_live_session_listener` (new public method; oidc stubs need this member). Suite 9154 green.
**Convergence counter RESET by design change: round 5 = first potential clean round for the
simplified shape.**

**ROUND 5 (high) DONE 2026-07-13**: 13 candidates → 1 refuted → 12 kept → 10 reported (+1 named
drop). STRIP CAME BACK CLEAN — findings shifted to PRE-EXISTING bugs the branch surfaced: (1)
**push-driven list_changed refresh NEVER worked** (SDK awaits handlers inline in its receive loop →
in-handler request self-deadlocks; verified by finder with live-SDK spike; on main = permanent
receive-loop wedge, branch timeout made it fail-bounded + stall in-flight calls 30s); (2) failed
refresh consumed the debounce stamp permanently; (3) obo credential-presence gate starved prime-time
convergence (skips the lookup whose kind=missing drops ghosts); (4) constructor while-loop still
clobber-able by tool-search build + mid-construction callback crash noise (pre-existing); (5)
PLAUSIBLE drop-after-publish wipes re-consented catalog; (6) `_drop_catalog_locked` docstring
wait-bound wrong; (7) auth.py gate call outside try. **ALL FIXED commit `19eba7e6`**: refreshes
`_spawn_background`-spawned via `_run_notification_refresh` (failure pops the debounce stamp →
retry); obo gate schedules `TokenLookupResult(kind="missing")` drops for catalog-bearing entries;
`skip_if_connected=True` on dead-grant drops (live session at drop time proves grant alive again —
revoke path stays unconditional); constructor seq re-check moved AFTER tool-search init calling full
`_on_mcp_tools_changed` (all deps exist there); gate call inside try; `_pool_lookup_failure` helper
(render+drop pairing ×3); test dedup `_fake_pool_tools` + deterministic `_drain_background`
(replaces 0.05 sleeps). NOTE: STATIC-path notification handler has the same inline-await deadlock —
PRE-EXISTING, out of branch scope, **tracked as #839 (2026-07-13)** with main@3742e966 anchors
(handler 1452, inline awaits 1483/1487/1491, unbounded list_tools 3317) + the full
port-the-pool-protocol fix shape (spawn, serialize, coalesce, stamp lifecycle, timeout, group-catch
log hygiene); worse blast radius than pool (shared per-node session; recovery only via health-ping
timeout teardown). Suite 9158 green. Round 6 launched = potential clean round 1 of 2. — the
maintainer observed ~20 findings entering verification, xhigh report cap = 15, so AFTER completion
apply the cap-mining recipe from [[reference_code_review_workflow_recovery]] (synthesize agent's
prompt in `agent-<id>.jsonl` carries the full ranked survivor list; dropped = survivor indices never
claimed as primary or merge). Fix round = mined findings + the deleted-server `_is_pool_server`
retention regression (above) in ONE round, then re-review the fix round per
[[feedback_pre_commit_gates]]. Tree FROZEN until the run completes
([[feedback_freeze_tree_during_review]] — also re-check `git branch --show-current` after).

**ROUND 6 (high) DONE 2026-07-13**: 14 candidates → 1 refuted (session.py seq-attr style nit) → 13
kept → 8 reported (5 correctness + 3 cleanup; merges: 3× warm-entry, 2× ordering, 1× pop-on-failure
= accounting CLEAN, under cap 10). ALL in R5-touched surface: (1) **skip_if_connected accepted
PRE-revocation warm sessions as re-consent proof** — warm entries never converged on dead grants
(dispatch short-circuits at the failed lookup before any 401; `_prime_one` returns early on warm),
deferring #836 warm-case convergence to idle-TTL scale; the R5 docstring claim "live session proves
connect after failed lookup" was FALSE for warm. (2) runner's `except Exception` missed
BaseExceptionGroup (wedged-anyio shape) → stamp protocol bypassed + group escaped to
`_spawn_background`'s exc_info log serializing the bearer-carrying httpx chain. (3) mid-connect
refresh publish overwritten by connect's OLDER discovery snapshot (handler live at ClientSession
creation, before wiring block) — change hidden until next server notification. (4) same-key spawned
refreshes unserialized → slower list call publishes older catalog last (debounce 5s < refresh
timeout 30s makes overlap trivial). (5) pop-stamp-on-failure (MY R5 choice) removed main's
failure-path throttle → unthrottled spawn+fail storms. **ALL FIXED commit `67a11b2e`** (+338/−79,
suite 9163 green): `_schedule_dead_grant_drop` snapshots `entry.session` at observation,
`_drop_catalog_locked(observed_session=…)` skips ONLY if session CHANGED since (identity compare;
holding the coro ref prevents id-reuse; revoke path unconditional; bounded drop-fresh-cooled-catalog
residual documented — needs full connect+cool inside task latency, self-heals at next use); runner
acquires `open_lock` + same-entry recheck (serializes vs connect wiring AND siblings — fresh list
AFTER prior publisher = monotonic freshness, the simple core of what the stripped gen protocol
over-engineered); failure KEEPS stamp (throttle > lost-window; teardown pops stamp so reconnect
refreshes immediately); runner catches `(Exception, BaseExceptionGroup)` type-name-only; handler
branches → module table `_POOL_LIST_CHANGED_REFRESHERS`; `_reprime_active_users` →
`_live_listener_uids()`; obo gate kind="missing" contract-pinned both sides (kept synthesis —
routing through `_prime_one` would REGRESS warm-obo via its early return). +5 tests (warm-entry drop
+ post-observation spare, group catch, lock serialization, replaced-entry discard, warm obo gate);
stamp test INVERTED (runner now needs a seeded entry — early-returns without one). Scrubbed my R5
"(R6)" comment; NOTE pre-existing on main: "(R6)" comments at mcp_client 2344/3657/3732 + a
`feedback_asyncio_timeout_vs_wait_for.md` MEMORY-FILE citation at ~2338 — flag to the maintainer as
cleanliness follow-up, out of branch scope. Convergence: R5=0-on-strip but 5 pre-existing, R6=5 →
round 7 owed (still need 2 consecutive 0-correctness rounds).

**ROUND 7 (high) DONE 2026-07-13**: 10 candidates → 10 verified, 0 refuted → 9 reported + 1 merge
(resources/prompts stale-docstring pair) = accounting CLEAN under cap. 3 runtime correctness (all in
MY R6 code) + 1 doc-contract + 5 cleanups: (1) **observation snapshotted AFTER the lookup's awaits**
— `_schedule_dead_grant_drop`'s internal snapshot ran post-lookup, so a consent-completion prime
connecting MID-lookup (its awaits park on executor hops; the callback prime bypasses the refresh
lock) was captured as the observation and the drop evicted the just-restored catalog — the
identity-compare's blind spot, re-introducing the #836 stranding. (2) **lock-holding runner lost
backpressure** — admission 1/5s (stamp at schedule) vs drain 1/30s (lock held through the timeout) →
unbounded FIFO waiters: same-key dispatches past the 120s budget,
`_close_pool_entry_if_idle`永-locked skip = eviction starvation, `_background_tasks` growth. (3)
**"teardown pops the stamp" was FALSE** for `_teardown_pool_entry` + `_on_pool_owner_death` (only
`_evict_session` + idle-close popped) — post-reconnect change debounced against a pre-collapse
stamp. **ALL FIXED commit `76517ff4`** (+463/−129, suite 9168): observation moved to CALLERS
pre-await (`_observed_pool_session` helper; `_pool_lookup_failure` + `_prime_one` + obo gate thread
it; `observed_session` now REQUIRED kwarg — earlier snapshot is strictly conservative);
per-(key,kind) coalesce marker `_pool_refresh_pending` (set at spawn, discarded at lock-ACQUIRE so a
mid-list change spawns exactly one successor + finally for parked-cancel + handler-except discard;
bounds parked runners at 1 → dispatch wait ≤2 timeouts; runner returns quietly on evicted session;
residual wedged-notifying-server duty-cycle documented at runner — ends at first
dispatch/recovery/silence); stamp pops added to both teardown paths (idle-close's own pop removed —
`_teardown_pool_entry` owns it). Cleanups: table→kind-only + dispatch-time bound-method map
(mypy-checked, instance-stub-friendly — direct class refs in a module table would break
instance-attr test stubs); schedule-side nothing-to-converge guard (no-op tracked task per
unconsented server per prime at scale); `try_prime_user_pools` module helper (3 drifted copies:
session ctor, acting-user change, auth capture — duck-typed, swallow+debug, `require_live_listener`
for capture site); resources/prompts docstrings state the HELD-lock contract;
`has_live_session_listener` = sole liveness predicate (`_user_has_live_listener` deleted);
`_mcp_tools_seq_at_read` → constructor local. +5 tests (coalesce, 2 teardown pops, schedule guard,
dispatch-level mid-lookup re-consent via `_pool_token_lookup` stub); R6 notification tests seed
`entry.session` (runner's new session gate would have made them vacuous). NOTE: R7 confirmed a
pre-existing delete-vs-persist race in the classified lookup (lookup's invalid_grant row-delete can
kill a token the consent callback persisted mid-lookup → one extra re-consent; catalog converges
correctly) — mcp_oauth territory, related to #830's accepted 1992 residual, flag to the maintainer
as follow-up, NOT fixed here. Convergence: R6=5, R7=4 → round 8 owed.

**ROUND 8 (high) DONE 2026-07-13 (loop ended by the maintainer; work → PR #840)**: 4 candidates → 4
verified, 0 refuted → 4 reported (accounting clean; 3 of 4 finder agents EMPTY — finders scraping
bottom). 1 real behavioral defect (filed as "cleanup" by the finder, counted as correctness
honestly): the runner's unconditional finally-discard clobbered a SUCCESSOR's coalesce marker after
the at-acquire discard released ours — verifier reproduced 2 parked runners + extra spawn (one extra
30s list call per debounce window under lock congestion). 3 structural cleanups:
observe-before-lookup preamble triplicated → `_pool_lookup_checked` (ordering contract structural);
drop_session+stamp-pop triplicated + shutdown sweep divergent → `_drop_session_and_stamp` + shutdown
clears both notification structures; `_mcp_tools_change_seq` branch-scoped init → unconditional.
**ALL FIXED commit `842d099b`** (+133/−41; finally gated on `acquired` flag set after at-acquire
discard, both sync so cancel-atomic; +2 marker-lifecycle tests: successor-preservation,
parked-cancel release). Suite 9170 green. **The maintainer ended the loop at R8** (the finders were
struggling to find anything further; R6=5→R7=4→R8=1 trend): **Pushed as PR #840** (9 commits, Closes
#836, no attribution footers) + **#836 reply posted** (issuecomment-4965237995: report-verified
thanks, fix shape confirmed, sibling bugs found, convergence design, obo coverage, repro test, 1.7.x
TTL/LRU-knob mitigation line). **BACKPORT: the maintainer leaning NO** (obo+this all main-only, 1.8
= the mcp release; my push-back agreed: re-derivation not cherry-pick, config mitigation covers
dominant symptom, stable-line risk) — final call still their, pending. Repro coverage note (the
maintainer asked): `test_close_pool_entry_if_idle_cools_entry_for_live_session_user`
(test_mcp_user_catalog.py) = the issue repro at full fidelity (real mock transport, live listener,
zero fan-out, documented negative); TTL-pass split + reconnect-drift tests complete the chain.
OUTSTANDING: PR #840 CI + the maintainer's review/merge; backport decision; delete-vs-persist race
follow-up issue UNFILED; pre-existing "(R6)"/memory-file-citation comments on main (mcp_client
~2344/3657/3732) unfixed cleanliness nit.

**PR #840 BOT FEEDBACK VALIDATED 2026-07-13 (head 842d099b)**: `github-code-quality[bot]` review = 5 inline "Statement has no effect" comments on test_mcp_user_pool.py :540/:780/:812/:910/:947 — exactly the branch's five bare `await <task>` statements (scanner treats await-of-a-name as valueless pure expression). ALL FIVE FALSE POSITIVES, each load-bearing: 540/780 join parked drop/refresh runners after lock release (assertions read post-completion state); 812 makes the negative `refreshed == []` non-vacuous; 910 delivers cancellation so the runner's finally releases the coalesce marker (same idiom pre-exists unflagged outside the diff at :2508/:2530); 947 fabricates a DONE owner task for the manual done-callback — production `_on_pool_owner_death` (mcp_client.py:2258, :2270-72) calls `task.cancelled()`/`task.exception()` (InvalidStateError on pending) and un-awaited tasks trip the conftest leak guard. The bot's :947 completed-Future swap DECLINED: `owner_task`/callback are typed `asyncio.Task[None]` (:585/:2258); no gate breaks (mypy scopes `turnstone/` only, not tests) but it lies against the contract and drops done-Task fidelity. Copilot review same day = 0 comments. Verdict: zero code changes. **CLOSED OUT 2026-07-14 (the maintainer approved)**: FP-rationale reply posted on each of the 5 threads + all resolved via resolveReviewThread, verified isResolved=true; NO code-scanning alerts existed behind them (refs/pull/840/head empty — review threads were the only artifact). CI all green (3.11 pending at check).

Related: [[project_mcp_obo_single_token]] (obo pool membership), [[feedback_push_back]].

---
name: project_884_history_coalescing
description: "Touching /history coalescing in make_history_handler (#884, shipped PR #893): single-flight keyed (ws_id, limit) with gates before join; never a TTL cache."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-23T00:10:58.035Z
---

**#884 shipped via PR #893 (2026-07-22, branch `fix/884-history-coalescing`, one commit).** Restart-herd /history coalescing: concurrent requests for the same `(ws_id, limit)` share ONE reconstruction (load_messages → verdict decoration → reasoning extraction → cursor trim → projection) via a single-flight task map in `make_history_handler`'s closure (`turnstone/core/session_routes.py`). Client jitter spreads the peak; this removes the total.

**Design rulings (at-site comments carry each):**
- **Single-flight ONLY, no TTL cache** — the payload depends on live-mutable inputs with no total cheap invalidation signal (`surface_persisted_reasoning` registry toggle emits NO per-ws event; cold workstreams have no event counter). Joiner staleness = flight duration = what a lone slow request already exposes.
- **Gates before join** — permission/tenant/kind/existence/limit all per-request ABOVE the join; only the caller-independent reconstruction is shared ({ws_id, messages, cursor} carries no per-caller field). The ordering is THE safety invariant.
- **Fan-out-wipe guard** — `load_failed` (True only when load_messages RAISED, never legit-empty) rides the flight result; joiners on a failed draw retry once, independently (both clients render 200-empty as an authoritative pane wipe; the seedless clear_ui path has no SSE redelivery). Owner keeps its draw; blast radius == un-coalesced baseline. `ws.history.load_failed` raised debug→warning.
- **Flight lifecycle** — detached `asyncio.create_task`, awaiters `shield` it (owner disconnect can't strand joiners); pop-in-finally INSIDE the task so the map only ever holds in-flight work (single-flight, not a cache). Accepted at-site: a LONE reader's mid-flight disconnect no longer aborts the bounded pipeline; refcount-cancel declined (join-vs-cancel race on a seam race-free because the flight is never cancelled).
- **Per-awaiter serialization kept** (parity with main); shared pre-rendered bytes declined at the return site (splits the `_HistoryFlightResult` contract the retry path needs, herd-only micro-win).
- **Scope** — one map per cfg mount per process; interactive routing is owner-node-sticky so the herd for one ws lands on one process; coord /history is console-process-local. Stale cursors degrade to replay_truncated→resync (no data loss).
- The coalesced-join debug line `ws.history.coalesced ws=` is a TEST SYNC POINT (comment at the emission site): the concurrency tests wait on the record via caplog (structlog routes to stdlib — spike-verified); renaming it turns their join-wait into a timeout.

**Tests:** `TestHistoryCoalescing` (tests/test_workstream_endpoints.py) — 7-case matrix via httpx.ASGITransport + `_GatedStorage` (count-then-block ordering = the join proof) driving the REAL backend: join/share, failed-draw-not-fanned-out, gates-before-join, key-includes-limit, no-cross-flight-reuse, decoration-failure-shared-not-retried, owner-disconnect-leaves-joiner. All positive-edge sync, zero wall-clock beats.

**Campaign:** dataflow-mapper graph (docs/design/884-history-coalescing-dataflow.md, local) settled the design before code (cut-line per-request vs shareable; TTL-invalidation verdict; the 200-empty fan-out hazard). 3 rounds, ZERO correctness findings in any round; r1 minors = declined serialization opt (at-site ruling) + type alias + decoration-share test; r2/r3 unprimed clean pair. The e2e recovery harness (both tiers) ran green on the branch — the restart scenarios drive the truncated-resync → /history rebuild through the coalesced handler in a real browser.

Related: [[project_890_clear_ui_guard]] (client half of the restart-window pair; #895), [[project_sse_truncated_resync_hole]] (the jitter/coalescing lineage + the three at-site rulings that promoted #884).

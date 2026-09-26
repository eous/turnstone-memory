---
name: Direct HTTP transport
description: "Questions about the Redis MQ layer, hash ring or rebalancer: all REMOVED; transport is direct HTTP + console proxy with rendezvous hashing, COMPLETE."
type: project
---
**Status: COMPLETED, two stages, both stable long-term.** Stage 1 (2026-03-30, PRs #260/#261/#262):
replaced the Redis MQ layer (`turnstone/mq/`, bridge process, simulator) with direct HTTP +
hash-ring routing, 129 files changed, net -4500 lines. Stage 2: the hash-ring placement layer itself
was later replaced by rendezvous hashing (HRW, FNV-1a) in `turnstone/core/rendezvous.py`; migration
`046_drop_hash_ring_tables.py` dropped the bucket/ring tables. **Re-verified 2026-07-06:
`turnstone/core/hash_ring.py` and `turnstone/console/rebalancer.py` no longer exist in the repo**
(confirmed absent, not just "unused") — `ConsoleRouter.route(ws_id)`
(`turnstone/console/router.py:154`) calls `select(ws_id, nodes)` directly per request with no
precomputed cache table and no rebalancer daemon. The console proxy shape (`/node/{node_id}/...`)
and single-node vs multi-node split are unchanged from the original landing.

**Architecture (current):**
- Single-node: Client → Server (direct HTTP + SSE, no console needed)
- Multi-node: Client → Console (routing proxy, rendezvous-hash placement) → Server nodes
- Channel gateway and scheduler dogfood the SDK clients

**Tech debt — re-checked 2026-07-06:**
- **RESOLVED:** "SDK sync clients lack token_factory" — `TurnstoneServer.__init__` (`turnstone/sdk/server.py:598`) now takes `token_factory: Callable[[], str] | None`, same as the async client.
- **RESOLVED (or never real):** "README.md stale MQ references" — no `redis`/`message queue`/`mq` hits in `README.md` today.
- **Still open, unverified this pass:** simulator rebuild (still absent from the repo — no simulator reimplementation found).

**Design doc:** `docs/design/direct-http-transport.md` (untracked, historical)
**Hash ring reference:** `docs/design/consistent-hash-ring.md` (describes the now-removed Stage-1 ring; historical only)

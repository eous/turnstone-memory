---
name: project_mcp_dead_transport_followup
description: "MCP client self-healing (dead-transport #742, token sweep #767, static reconnect #768): all SHIPPED July 2026; the MCP SDK has no reconnect, Turnstone owns it."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-20T17:03:50.767Z
---

Three shipped PRs, one arc: turning MCP client connection handling from purely
lazy/reactive into actively self-healing, on top of the original circuit-breaker
work in [[project_mcp_resilience]]. All three landed within one week
(2026-07-01 → 2026-07-04), each answering a specific gap the others exposed.
**Consolidated 2026-07-06** from what were three separate memory files — the
former `project_mcp_obo_token_freshness.md` and `project_mcp_static_reconnect.md`
now just point here.

## Shipped

**#742 (shipped 2026-07-01, branch `fix/mcp-dead-transport-followup`) — dead-transport
detection completion.** A local `/code-review max` of PR #741 (`f585c47b`, the
original MCP dead-transport + token-refresh fix) surfaced 8 findings the GitHub
bot review missed — chiefly that #741's dead-transport fix was incomplete.
Extended `_is_dead_transport` classification to `read_resource_sync` +
`get_prompt_sync` (were still `BrokenPipe/ConnReset/EOF`-only → same corpse-reuse
restart-hang #741 fixed only for `call_tool_sync`). Anchored the match on the
SDK's synthesized `code=32600` + exact `"session terminated"` message, and
**dropped the bare `"session not found"` substring** — the SDK never emits it
client-side, but healthy session-owning servers use that phrase for their own
app-level stale-id rejections, so matching on it was evicting live sessions and
tripping the SHARED per-server breaker. Also: user-scoped `oauth_user` status
(was deriving catalog counts from an arbitrary warm-pool entry, leaking user A's
catalog size to user B over `/mcp-status`), a matching admin-aggregate view
gated on `admin.mcp`, and non-destructive session-start priming
(`revoke_on_dead_grant` defaults True but priming passes False, so it never
revokes an unused grant — only live dispatch does). 835 `test_mcp_*` green at
merge.

**#767 (shipped 2026-07-04, branch `feat/mcp-obo-token-freshness`) — OBO token
proactive freshness.** MCP OAuth (`oauth_user`, on-behalf-of) token refresh was
correct but entirely lazy — fires only on tool dispatch, session-start prime, or
a 401 force-refresh — which breaks autonomous/unattended workstreams acting for
an absent user (expired token = latency; dead refresh token = hard fail with
nobody to re-consent). Considered and **REJECTED** an external PR (#761): an always-on keep-warm
reconciler with a blocking 3s pre-flight on the interactive hot path that
duplicated the classification ladder.
Built instead: an **observe-only** `_user_token_sweep_loop` (default 240s,
floor 30s, `≤0` disables) that refreshes near-expiry tokens but on failure NEVER
revokes/deletes/mutates shared cooldown state (`revoke_on_failure=False`); plus
a `_keepalive_refresh_due` lane (default 1800s) that force-refreshes grants
whose refresh token has sat un-exercised even while the access token is still
fresh (the long-access-TTL / short-refresh-idle-timeout gap). Zero DB/AS calls
when no OBO server is configured; static/no-auth servers structurally
untouched. `/code-review max --fix` (24 agents) fixed busy-loop-on-bad-cadence,
fleet-wide revoke-on-timer, badge-lost-on-persist-fail, and more; skipped
per-node cluster-scale sharding as out of scope at current node counts (see
gaps below).

**#768 (shipped 2026-07-04, branch `feat/mcp-static-reconnect`) — static-server
autonomous reconnect.** Non-`oauth_user` servers had NO autonomous reconnect —
an evicted-but-idle or GET-stream-dead connection stayed dead until the next
dispatch or operator action (root cause of a live Understone door-game feed
outage — [[project_understone_doorgame]]). Shipped `_static_health_loop`
(default 30s, `≤0` disables): reconnects `session is None` on capped-jittered-
forever backoff (full jitter, base 1s, cap 60s, no attempt limit), and
`send_ping`s connected servers to evict dead-but-idle ones for the next tick to
pick up. Two clocks by design: the health loop owns reconnect timing, the
circuit breaker stays the dispatch-time fail-fast gate — don't block tool calls
on the forever-retry. Also fixed a latent pre-existing race by splitting
`_connect_one` into a per-name-lock wrapper + `_connect_one_locked` so
concurrent reconnects can't interleave teardown on shared `StaticServerState`.

**Durable SDK finding backing #768 (verified against mcp 1.28.1 — don't
re-investigate):** the MCP Python SDK has no meaningful client reconnect
handler anywhere. The only reconnect logic at all is
`streamable_http._handle_get_stream` (the server→client GET/notification
stream), capped at `MAX_RECONNECTION_ATTEMPTS=2`, flat ~1s delay, and it fails
**silently** without tearing down the session (POST path stays alive).
stdio/sse/websocket have zero reconnect; `ClientSessionGroup` is a naive
aggregator with no health/reconnect; `backoff`/`jitter` appear nowhere in
`mcp/client/`. Reconnect is Turnstone's to own — nothing upstream to lean on.
SDK v2 (`mcp>=1.27,<2` pinned; v2 tracked as **issue #679**, targeted 1.8) is a
breaking rewrite, not worth waiting for.

Code confirmed live in `turnstone/core/mcp_client.py` as of 2026-07-06:
`_user_token_sweep_loop` (~line 2188), `_static_health_loop` (~line 4428), both
started from `_connect_all`.

## Remaining known gaps (deferred, best-effort calls — none release-blocking)

- **Per-node sharding for the token sweep** (from #767): the sweep and
  reconcile passes are sequential/per-node with no rendezvous-hash membership
  plumbing. Fine at Turnstone's current scale (low tens of nodes); would need
  work before ~100-node-cluster scale with thousands of OBO grants.
- **GET-stream-death layer 3** (from #768): `send_ping` only proves the POST
  path is alive; silent GET-stream (notification) death is still undetected.
  The fix is bounded session recycling, which needs a static in-flight guard
  first (only `PoolEntryState` tracks `in_flight`; `StaticServerState` doesn't).
  No live killable-server smoke test exists either (suite is mock-based).
- Minor/cosmetic, low value: `_prime_one`'s double `get_mcp_server_by_name`
  lookup; status-dict field duplication between the two status methods; a
  narrow OBO re-badge edge case.

Related: [[project_mcp_resilience]] (the circuit-breaker/pre-close work this
trilogy completes), [[project_understone_doorgame]],
[[project_pr750_multiuser_context_review]].

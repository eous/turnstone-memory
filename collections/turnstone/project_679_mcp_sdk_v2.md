---
name: project_679_mcp_sdk_v2
description: "#679 MCP SDK v2 port (refreshed 09-28 vs 2.2.0; floor 2.3; 2.3 behaviors verified 10-14): phase 0 #1222-#1226 on 1.x, then PR #1395 with phase 2 folded in; the 10-14 rulings."
metadata:
  node_type: memory
  type: project
  modified: 2026-10-15T04:49:16.999Z
---

The plan of record is the #679 issue body, rewritten 2026-09-28 against `mcp` 2.2.0. It has a
phased plan, a 20-row feature matrix and reproducible spike scripts. This file keeps the
verified facts a session needs before touching `mcp_client.py` for the migration. Re-check upstream
releases, the tree and the phase 0 issues before relying on any version number or status here.

**Upstream state (2026-09-28).**
- v2 went stable on 2026-07-28 (2.0.0). Then came 2.1.0/2.1.1 (08-24/25), 2.0.1 (08-26) and 2.2.0 (09-07).
- 1.x is a maintenance line with critical and security fixes only. 1.30.0, our lock, carries backports of the 2.2 same-origin redirect policy, the AS-issuer validation and the idle-session expiry. So the `<2` pin is not a security exposure.
- The reason to move is protocol reach (the 2026-07-28 revision), plus the plumbing #680/#681 need.
- Target floor `mcp>=2.3,<3` (the maintainer moved it from 2.2 on 2026-10-09; the issue body and title carry it). 2.1 is the first release whose client-side validation accepts boolean sub-schemas.
- 2.3.0 (2026-10-02; release notes read 10-09, not yet spiked) adds `max_sse_event_size=` on `streamable_http_client` and `StreamableHttpParameters` (default stays 1 MiB, `None` lifts it; needs `httpx2>=2.10`), the setting S8 lacked. It also stops sending an empty `_meta`/`params` on legacy connections, which 2.2 sent and some servers reject. Issue matrix rows 21-22.

**Phasing.**
- Phase 0 lands on 1.x first, as sub-issues of #679 filed 2026-09-28:
  - #1222: typed SDK reads and real `mcp.types` objects in tests. Land it first; the rest is tested through it.
  - #1223: classify failures from the observed HTTP status on both paths. Lands with #1224.
  - #1224: one malformed tool takes the whole server down.
  - #1225: catalogs are read only to page 1. Sequence it with #1146.
  - #1226: helper processes started by a stdio server outlive the connection.
  - The issue's checklist also holds a 2 MB tool-result test (for S8 below), a lock for Understone's shared game, the `mcp>=1.30,<2` floor, and dropping the private `mcp.shared._httpx_utils` import.
- Phase 1 ports to the v2 API but stays in the 2025-11-25 era. A bare `ClientSession.initialize()` still negotiates 2025-11-25 against a v2 server (verified). So `list_changed` via `message_handler`, `send_ping()`, `Mcp-Session-Id` and the GET stream behave as in v1.
- Phase 2 adopts 2026-07-28: `discover()` with our own fallback (the SDK's `negotiate_auto` is private), `subscriptions/listen`, `InputRequiredResult` handling, a ping replacement, and SEP-2243 headers.
- The alpha-era worry that the stateless core would force the capturing factory to be reworked twice does not apply: v2 serves both eras.

**Silent failure classes (verified on 2.2.0 with a real v2 server).** A port that connects, lists
and calls tools can still be wrong. S-numbers such as S8 follow the issue body.
- **camelCase `getattr` with a default returns the default.** Eight `getattr(obj, "camelCase", default)` reads in `mcp_client.py` get the default, because the v2 attributes are snake_case (#1222):
  - `inputSchema` → empty tool schemas;
  - `listChanged` → push refresh disabled;
  - `isError` → tool errors reported to the model as successes;
  - `mimeType` → `"binary"`.
- **`_is_dead_transport` stops recognizing dead sessions.** It keys on `httpx.*` classes, but the SDK now raises `httpx2.*`, which are not subclasses. It also keys on the SDK-synthesized positive `32600`. v2 surfaces the server's own 404 body instead (`MCPError(-32600, 'Session not found')`) or `-32600 'Session terminated'`, and `-32600` is also plain `INVALID_REQUEST`. The planned fix records 404 on a held session, and 5xx, in the response-hook carrier (#1223).
- **Non-2xx responses no longer kill the transport.** A 401 or 502 fails only that call, with `MCPError(-32603)` in about 0.01 s, and the session stays usable. The breaker would read either one as a healthy protocol rejection.
- **`message_handler` receives the notification itself.** `.root` is gone, and a raising handler is now logged instead of fatal, so push refresh would die quietly.
- **An `httpx.AsyncClient` passed as `http_client` is not rejected.** Connect, list, call and `list_changed` all work with one, so a half-port passes smoke tests. Assert `httpx2.AsyncClient` in the factory. The migration guide's warning that server-initiated messages stop arriving did not reproduce on 2.2.0 legacy sessions.
- **One malformed tool fails the whole `tools/list`.** Client-side schema validation rejects a third-party tool whose `inputSchema` is `{}`, missing, or not an object type, and raises `pydantic.ValidationError` for the entire list. There is no public switch: validation runs inside `send_request`, before the caller's result type. Decided 2026-10-02 (#1224): a validation failure on any catalog page fails the server with `InvalidCatalogError`, naming the entry and the field. It is not a breaker failure, and the static health loop retries it every 5 min. A static server also withdraws the tools, resources and prompts kept from its last good connect, and syncs prompt templates at once (maintainer's choices; the sync is global, so deferring it only moves the deletion to an arbitrary later sync): with no breaker count, a dispatch to a kept tool would rerun the full connect on every call. Pool entries keep their catalogs, because a dispatch reconnect is how live per-user sessions recover (#836). A refresh that meets an invalid catalog keeps the last good one and retries every health tick like any failed refresh. A slower refresh retry was tried and reverted: the push-refresh design relies on that retry running promptly to clear the error after a single-kind push succeeds. Do not publish the valid entries around a malformed one. On 1.x, `call_tool` re-lists any tool missing from the SDK's output-schema cache after the tool has run, so a lenient list turns successful calls into errors after their side effects; 2.x has no public per-item path either. The port must keep the `ValidationError` → `InvalidCatalogError` wrap in `_list_catalog` (2.x raises the same pydantic type).
- **SSE events over 1 MiB fail as a dropped stream (S8).** v2 reads SSE through `httpx2.EventSource` at its default 1 MiB cap, and the SDK exposes no setting. An oversized result fails as `MCPError(-32000, 'SSE stream ended without a response')`, and the real cause is logged only at DEBUG. `-32000` is `CONNECTION_CLOSED`, which `_is_dead_transport` reads as a dead transport, so a healthy session is evicted and the breaker counts a failure. SDK-built servers send a `str` result twice (`content` and `structuredContent`), so about 512 KiB of text is enough. 1.30's `httpx-sse` has no cap (a 6 MB event arrives), so only a phase 0 test can catch this before the port. The fix needed upstream a size setting on `streamable_http_client` or a distinct error; 2.3.0 shipped the setting only, so an event over whatever cap the port picks still reads as a dead transport.

**Verified on 1.30 through `MCPClientManager`, so not v2 changes (2026-09-28).**
- A static-path call that gets a 401 or 5xx waits out the full tool timeout, and the breaker records nothing (#1223).
- A tool missing `inputSchema` or `name` already fails the whole list, and the static health loop then reconnects indefinitely on capped backoff (#1224). 1.30 still accepts `inputSchema: {}` and non-object schema types.
- Only page 1 of each catalog is published. The fix follows the cursor, bounded by the existing per-server caps (#1225).
- A gracefully exiting stdio server's helper processes survive disconnect and `shutdown()`, and 2.2.0 behaves the same (#1226).
- A tool that returns `isError: true` does reach the model as an error today. #1222 pins that with a real-server test so the port keeps it.

**Facts that correct older notes.**
- v2 still takes `ClientSession(message_handler=...)` as a constructor callback. The factory v2 removed is streamable HTTP's `httpx_client_factory`: you call your own factory and pass `http_client=`.
- The pre-built client's lifecycle is the caller's. Enter it on the owner task's exit stack, before the transport.
- `mcp.shared._httpx_utils` still exports the timeout constants and `McpHttpClientFactory` in 2.2.0, so the private-import pre-step is hygiene, not a blocker.
- The console process also hosts an `MCPClientManager` for coordinator sessions (#725, built in #879), so the port covers both the node and console lifespans.
- The 2026-07-11 beta-spike read (the port is mostly the factory swap) holds for the API surface. The classes above only show up in error paths.
- `mcp` 2.x requires `httpx2` and neither `httpx` nor `httpx-sse`. After the port, only Turnstone's direct imports keep those two in the lock, and #1011 moves them to `httpx2`. The Anthropic and OpenAI SDKs already depend on `httpx2` only.

**Private SDK seam from the #1226 fix (2026-10-02).**
- `mcp_client.py` wraps `mcp.client.stdio._create_platform_compatible_process` at import to record each stdio server's pid. The transport owner sets a ContextVar sink only while it enters `stdio_client`, and once the transport unwinds it stops what remains of the server's process group.
- The name and signature are the same in 1.30 and 2.2.0. The port must keep the wrapper recording; `test_spawn_hook_records_the_server_pid` fails if it stops.
- Rejected, don't retry: a supervisor process wrapping each server. The SDK's escalation and anyio's cancelled-teardown `transport.close()` signal only the direct child, so they hit the supervisor, and a server that ignores its closed stdin survived with its helpers. Its `-I` interpreter also coerced `LC_CTYPE` into every server's environment.

**Verified on 2.3.0 (2026-10-14: SDK source, plus a probe against a raw 2025-11-25 server).**
- The SDK's own era probe, `negotiate_auto` (`mcp/client/_probe.py`, private), is a denylist:
  every `MCPError` from `server/discover` falls back to `initialize()`, except `-32022` naming
  only modern versions we don't share. A legacy server that answers the probe with HTTP 400, 405,
  422 or 500 still connects through it, as it does with an initialize-only connect. A fallback of
  our own must be no stricter: one that refused to fall back whenever the response hook captured
  a 4xx or 5xx left the 405, 422 and 500 servers unreachable in the probe.
- The streamable-HTTP transport already handles a non-2xx answer to a request
  (`_handle_post_request`): a JSON-RPC error body, even with `id: null`, is re-sent under the
  request's id. With no such body, a 404 before any session becomes `-32601 'Not Found'`, a 404
  on a held session `-32600 'Session terminated'`, and anything else `-32603 'Server returned an
  error response'`. Only an id-less error inside a 2xx answer goes uncorrelated.
- A bare `ClientSession` refuses an `InputRequiredResult` with a plain `RuntimeError`: "Server
  returned InputRequiredResult; pass allow_input_required=True to receive it and retry
  <method>(...)" (`_input_required_unexpected`). A classifier keyed on that text needs a test that
  raises it through the SDK; a hand-typed copy of the string had already drifted from it.
- `httpx2` verifies TLS through `truststore` (the OS store) unless `SSL_CERT_FILE` or
  `SSL_CERT_DIR` is set; `httpx` used certifi. Starlette's `TestClient` runs on `httpx2`, and
  `mcp` 2.x pulls in neither `httpx` nor `httpx-sse`, so a package that imports `httpx` (the
  Understone tests did) must declare it or move to `httpx2`.

**Outcome and rulings (2026-10-14).** The port went up as PR #1395, in three commits: the port
with phase 2 adoption folded in, a pass that keeps the client off SDK internals, and an SSE test
fix. The maintainer's rulings that day:
- Phase 2 rides with the port (discover with fallback, `subscriptions/listen`, discover as the
  liveness probe, catalog TTLs from cache hints, a resource response cache, a header-mismatch
  retry, and the `log_level` and `resource_subscriptions` settings), rather than splitting it out.
- The response cache sharing `public`-scoped reads among a per-user server's users is accepted
  for now and documented (#1388); changing it is a session of its own.
- `set_log_level` no longer re-stamps live sessions. The client-side filter of notifications
  outside an active subscription and the pruning of the SDK's tool caches were deleted (the spec
  puts the first duty on the server; the SDK prunes a complete listing itself).
- Private SDK names: [[feedback_private_sdk_names_fail_loudly]]. Names: [[feedback_no_relative_era_names]].
- Follow-ups filed: #1389 (tidy-ups), #1390 (a request for input reaches the model as SDK text),
  #1391 (a result over 16 MiB evicts the session), #1392 (OAuth rules, matrix row 11), #1393, #1394.

**Test trap (verified 2026-10-14).** A v2 test server negotiates 2026-07-28 and answers in plain
JSON, so a test of anything specific to SSE framing (the 16 MiB event cap, S8) passes vacuously
unless it forces a 2025-11-25 session: answer `server/discover` with a 404 (`RefuseDiscover` in
tests/test_mcp_http_failures.py) and assert the session's `protocol_version`. Past the cap, a
2025-11-25 session's call fails with `CONNECTION_CLOSED` ("SSE stream failed: Server-sent event
exceeded the 16777216 byte limit."), which still evicts the session (#1391).

**How to apply:**
- Start from the issue body.
- Re-run its spike scripts against the current SDK before changing failure classification.
- Where possible, write the boundary tests on v1 first (tool error surfaces as an error, `listChanged` enables push, a restarted server's session is evicted), so the port moves them from green to green. The 2 MB tool-result test is meant to go red at the port until S8 has a decision. See [[feedback_sdk_boundary_testing]].

Related: [[project_mcp_resilience]], [[project_mcp_dead_transport_followup]],
[[project_1_7_roadmap]] (pre-refresh history), [[project_963_oauth_extraction]],
[[project_1050_anthropic_sdk_v1]] (the HTTPX2 precedent), [[feedback_stable_deadline_memory_staleness]].

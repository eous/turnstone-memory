---
name: feedback_mcp_typescript_sdk_wire_shapes
description: "Changing MCP client errors, negotiation or dead-transport checks: test TypeScript-SDK server wire shapes (400 with -32000), not only Python servers; Python-only fixtures hid #1489."
metadata:
  type: feedback
---

Before changing how the MCP client classifies errors, negotiates a protocol version or decides a
transport is dead, test the change against the wire shapes of servers built on the TypeScript SDK,
which is most of the public server ecosystem. Python-SDK servers and hand-written stubs are not
enough.

**Why:** #1489. The SDK v2 port's discover fallback re-raised `CONNECTION_CLOSED` (-32000),
treating it as a code only the SDK makes. JSON-RPC reserves -32000 to -32099 for servers, and the
TypeScript SDK sends -32000 for its HTTP-level rejections, although it also names -32000
`ConnectionClosed` internally. Every test server, spike and review used Python servers or stubs
(Python SDK 1.x refuses with -32600), so the port passed several review rounds while no
TypeScript-SDK streamable-HTTP server could attach to 1.9.0. A review checks a diff against its
premises; only a real far-side implementation tests the premise ([[feedback_sdk_boundary_testing]]).

**Wire facts** (TypeScript SDK 1.30.1 and 1.32.2, Python SDK 1.30.0, measured 2026-10-26):
- Before a session exists, a request other than `initialize` gets HTTP 400, `application/json`
  and `{"error":{"code":-32000,...},"id":null}`. The SDK's transport says "Bad Request: Server not
  initialized"; the README's session-map pattern says "Bad Request: No valid session ID provided".
- A stateless server rejects an `mcp-protocol-version` header it does not know the same way, so
  the 2026-07-28 discover probe gets 400/-32000 there too.
- A restarted session-map server answers an old session id with that 400/-32000. The transport's
  own check answers a mismatched id with 404/-32001 "Session not found".
- The Python SDK client passes a JSON-RPC error body up under the request's id, so the server's
  code reaches the caller unchanged.
- Python SDK 1.30 servers refuse pre-session requests with -32600, on stateful and stateless
  transports alike.

**Decisions that follow** (maintainer, 2026-10-26):
- The #1489 fix (#1504) makes `_negotiate_session` fall back on -32000 but still stop on -32001.
  The SDK leaves a timed-out probe in flight, and a late error answer to it would latch on the new
  session; falling back on a timeout needs a guard first (#1502).
- `_is_dead_transport`'s -32000 match is load-bearing: it is how a restarted TypeScript-SDK
  server's stale session gets evicted and reconnected. With -32000 made non-fatal, the static
  session stayed stuck while its status said connected (measured). #1503 and #1391 carry this
  constraint.

**How to apply:**
- Encode the TypeScript-SDK shapes in the Python test fixtures, as `Upstream.discover_error` in
  `tests/test_mcp_connection_probe.py` does for the discover refusal.
- For a boundary check, install the TypeScript SDK 1.x (`@modelcontextprotocol/sdk`) with
  `npm install --ignore-scripts` into a scratch directory. Run a small node server in three shapes
  (a transport per session-less request, the README session map, stateless) against
  `probe_http_server` and `add_server_sync`, and include a server restart.
- Treat any JSON-RPC code from -32000 to -32099 as one a server may send, whatever name an SDK
  gives it.

Related: [[project_679_mcp_sdk_v2]], [[project_mcp_dead_transport_followup]].

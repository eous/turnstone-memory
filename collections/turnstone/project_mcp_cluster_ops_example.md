---
name: mcp-cluster-ops-example-pattern
description: "Multi-node SDK dispatch or examples/mcp-cluster-ops/: copy its console route_create_workstream, node send_and_wait, route_close-in-finally pattern."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-20T17:03:41.815Z
---

`examples/mcp-cluster-ops/` — MCP server for cluster-wide command dispatch.
Rewritten 2026-04-02 (PR #278) after direct HTTP transport refactor broke it.

**Three-step dispatch pattern (the canonical multi-node SDK usage):**
1. `TurnstoneConsole.route_create_workstream(target_node=..., auto_approve=True)` → `ws_id` + `node_url`
2. `TurnstoneServer(node_url, token=...).send_and_wait(prompt, ws_id)` — SSE stream from node
3. `TurnstoneConsole.route_close(ws_id)` in `finally` block

**Key details:**
- Uses `TURNSTONE_CONSOLE_URL` (not `TURNSTONE_SERVER_URL`) — cluster ops require console
- `_list_nodes_sync` paginates `console.nodes()` via offset/limit loop
- `_extract_node_ids` helper for dedup/strip/filter of node ID lists
- Workstream leak guard: `ws_id = ""` before routing, `if ws_id:` in finally
- `run_on_node` wraps dispatch in try/except for structured JSON errors
- 45 tests (helpers + mocked SDK integration)

**Why this matters:** This is the only working example of the console routing
proxy → node SSE pattern. Future SDK consumers should follow this.

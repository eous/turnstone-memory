---
name: project_1067_channel_recovery
description: "#1067 Discord/Slack thread-to-workstream recovery after restart: immortal routes, owner column (075), conditional replace, resume_ws_exact seam, review findings."
metadata:
  type: project
---

Branch `fix/1067-channel-recovery` lives in worktree <worktree> on
main 9c220b34; migration 075 adds `channel_routes.channel_user_id` (chain 072-073-074-075). Design
as of 2026-09-05: an SSE 404 retires the listener only and never deletes the route; a route is
replaced with `replace_channel_route(expected_ws_id)` and deleted with
`delete_channel_route(expected_ws_id=)`, and it is claimed before any message is dispatched (a lost
claim closes the candidate workstream and asks the user to retry); the Discord invoker is persisted
on the route instead of the old in-memory map; console node URLs are re-resolved on every SSE
connect (the `_node_urls` cache is gone); startup recovery fetches uncached Discord threads through
the platform API. Legacy routes (empty owner) on bot-owned threads are refused with a "can't verify"
message. A second, unstaged layer adds a `resume_ws_exact` create flag across server, console, SDK
and TS types, plus a `register_workstream` guard refusing ids a channel route still names.

Review findings raised 2026-09-05, not yet ruled: (1) routes are immortal, so every Discord
ready/resumed costs one platform REST fetch and one SSE connect per archived thread forever;
gate recovery on liveness (direct mode needs one list_workstreams call). (2) "ask an administrator
to recover" names a path that does not exist. (3) The /close reply is ephemeral after an ephemeral
defer. (4) The register_workstream guard couples the core insert to channel_routes with no ws_id
index and no tests. (5) The resume_ws_exact validation branches have no tests.

**Why:** the issue's root cause was the 404-deletes-route path; the fix makes routes durable, which
shifts cost to startup recovery and makes ownership a persisted fact.
**How to apply:** before touching channel routing, read this file and re-check which of the five
findings the maintainer ruled on; see [[project_current_state]] for the migration head and
[[feedback_alembic_linear_chain]] before adding a migration behind 075.

---
name: project_native_node_troubleshooting
description: "Native node failures after a venv rebuild or with container-only DNS: inspect the running interpreter and choose a node-reachable search endpoint."
metadata:
  type: project
---

## Client construction after a virtual environment rebuild

Rebuilding a virtual environment beneath a running server can leave the process using stale
imports. A new model client may then ask `certifi.where()` for a CA bundle under a deleted
interpreter directory. In the 2026-07-07 investigation, opening or creating workstreams failed
while existing sessions continued working.

**Why:** the process retains imported modules, but new HTTP clients resolve certificate paths
later. Healthy stored workstreams can therefore fail during client construction.

**How to apply:** compare the traceback's interpreter and package paths with the current virtual
environment. Check the running process before investigating database rows. If they differ,
coordinate a restart with the operator using that deployment's service manager.

## Search endpoints across container and native nodes

A container service name such as `searxng` may resolve inside the bundled compose network and
fail on a native node. The registry default can be selected through ConfigStore even when the
node runs outside that network.

**Why:** container DNS and host DNS have different namespaces. A cluster-wide loopback endpoint
also refers to a different network namespace from each node.

**How to apply:** inspect `_resolve_search_client` and current configuration precedence. Configure
`TURNSTONE_SEARXNG_URL` or `[tools] searxng_url` with an endpoint reachable from the affected node.
Check whether a stored admin value overrides it. Verify from each deployment type before changing
a shared setting.

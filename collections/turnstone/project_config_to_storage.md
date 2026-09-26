---
name: config-migration-to-storage
description: "ConfigStore or per-node settings work: migration COMPLETE, precedence storage > config.toml > env > defaults; advertise/console URL keys remain env-only."
metadata: 
  node_type: memory
  type: project
---

DONE. `ConfigStore` (SQLite/PostgreSQL) replaces config.toml-only settings; ~40 settings exposed via the admin Settings tab (form editor from `/v1/api/admin/settings/schema`, inline per-field save, source badge, restart indicator). Precedence: storage → config.toml → env → defaults. `POST /v1/api/_internal/config-reload` fans out to cluster nodes; ChatSession reads live config via `_mem_cfg`/`_judge_cfg`.

**Per-node settings already work end-to-end** (verified 2026-06-14): `system_settings` PK is `(key, node_id)`, `node_id=""`=global; `get_system_settings_bulk(node_id=X)` returns global+per-node merged with per-node overriding (ordered so node rows land last in the dict); admin `PUT /v1/api/admin/settings/{key}` already reads `node_id` from the body and writes it scoped + audited; ConfigStore is node-aware on a server node (`node_id=_node_id`) but global on the console (no node_id). Gaps: `SettingDef` has no `scope` field, and the admin UI has no node-target selector (API supports it though).

**DEFERRED proper-fix** (user will circle back): register node addressing keys (`server.advertise_url`, `tls.console_url`) in the registry as per-node settings and have the server read them. Decided precedence for these is **env > ConfigStore(per-node→global) > computed default** (env ON TOP — config-over-env would re-create the original "env override silently ignored" bug). Shipped 2026-06-14 as an env-ONLY hotfix instead: branch `hotfix/bare-metal-tls-console-url` plumbs `TURNSTONE_CONSOLE_URL` into the node's `TLSClient` (server.py ~4661; empty→services-table discovery) + `.strip()`s `TURNSTONE_ADVERTISE_URL` (server.py:4572). Context: bare-metal `turnstone-server` joining a Docker compose stack — node↔console is DB-mediated (services table), console→node dials the advertised URL verbatim, node→console only for TLS/ACME. See [[project_mtls_architecture]].

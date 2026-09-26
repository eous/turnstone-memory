---
name: model-definitions-in-configstore
description: "New admin-managed entity or model_registry.py work: DB-backed model_definitions is COMPLETE and current; reuse its config-over-DB merge and write-only secrets."
metadata: 
  node_type: memory
  type: project
---

Model definitions moved from config.toml-only to database-backed storage (migration 028).

**Architecture**: `model_definitions` table with CRUD (mirrors MCP servers pattern). Per-node merge at registry load: DB models (source="db") loaded first, config.toml models (source="config") override in-memory for same alias. Config.toml never written to shared DB — prevents cross-node source contamination.

**API keys**: Write-only pattern (hybrid judge+MCP). Writes allowed, reads always return "***", sentinel preserves existing on update. `is_secret` settings also changed to write-only (was 403 blocked).

**Context window**: 0 = auto-detect. DB models inherit CLI-detected value (same fallback chain as config.toml models). Runtime `_resolve_capabilities()` still merges with provider capability table.

**Admin UI**: Models tab in System group with sky blue (--blue) accent. Provider badges (openai=blue, anthropic=magenta), source badges (config=read-only, db=editable), sync-pending indicator.

**Deferred**: "Test Connection" button for endpoint validation + capability auto-detect, handler-level tests, named CSS column classes for mobile grid. Re-checked 2026-07-06: none of these have landed (`grep -i "test.connection"` across console static JS/HTML is empty; no `kind`/`modelKind` discriminator field either — see [[project_model_modal_kind_redesign]], still deferred).

**How to apply:** When adding new admin-managed entities, follow this same pattern (MCP → model definitions → next entity). The write-only API key pattern should be used for all secrets going forward.

**Still the foundational layer (verified current 2026-07-06):** this `model_definitions` table + per-node DB-vs-config merge + write-only-secret pattern is the base substrate that all subsequent model-registry work built on top of — the messages-API provider lane, the cross-lane reasoning-effort control uplift, and the effort ladder ([[project_messages_api_provider]]) all read/write through `model_registry.py` against this same schema. Nothing here has been superseded, only extended; treat this file as still-accurate architecture, not a stale snapshot.

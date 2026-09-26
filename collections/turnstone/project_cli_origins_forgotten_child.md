---
name: project_cli_origins_forgotten_child
description: "Changing session/storage contracts: audit CLI paths too (the under-maintained 'pcode' origin, kept for benchmarking)."
metadata: 
  node_type: memory
  type: project
---

Turnstone BEGAN as the terminal CLI — originally a project called **pcode** — and was renamed
turnstone when it grew into the multi-node orchestration platform. The CLI is, by the user's own
description (2026-06-11), the neglected surface: under-maintained relative to server/console;
features and hardening land server/console-first and the CLI lags.

**Current role (user, 2026-07-02): the CLI is mainly kept around for BENCHMARKING
turnstone in standard frameworks.** Scope CLI feature asks against that job — e.g.
personas (#683): CLI gets a `--persona` flag that LOADS by name (seed personas +
webui-authored ones), NO CLI authoring UX; `/creative` (CLI-only) is removed in
persona v1 with no regression because benchmark harnesses never used it.

**Practical consequences:**
- When changing session/storage/persistence contracts, audit the CLI paths EXPLICITLY —
  don't assume server-path invariants hold there. (Re-confirmed 2026-07-13: the CLI
  carried its own `--temperature 0.5` / `--reasoning-effort medium` argparse pins,
  untouched since the pcode era and ignoring per-model config entirely — found only
  by this rule during the #827 sampling-scheme sweep.) The CLI adopted `SessionManager` at
  the 1.5 unification (fresh sessions register correctly via `manager.create`).
- Pre-unification CLI/server paths are the likely source of the April 2026 orphan
  conversations (full sessions, no audit, no workstreams row).

Related: [[project_1_7_roadmap]],
[[reference_memory_store_maintenance]] (the orphan forensics).

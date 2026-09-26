---
name: project_phase8_status
description: "Phase 8 coordinator scale (spawn_batch, quota) DONE in PRs #386-#388, 2026-04-19; check its 7 deferred follow-ups before new batch/quota work."
metadata: 
  type: project
---

**DONE — PRs #386/#387/#388 merged 2026-04-19.** Shipped: `spawn_batch` + `close_all_children` batch tools (PR A); spawn budget + rate limit + admin `/quota` endpoint (`core/spawn_quota.py`, PR B); docs (PR C). Bulk-shape policy codified: `{results,denied,truncated}` for bulk-read/create, `{<bucket>,failed,skipped}` for cascade-mutation.

**Deferred follow-ups (handoff to future coordinator work — already scoped, just need prioritisation):**
1. **Per-item selective-deny approval UI for `spawn_batch`** — PR A shipped batch-level approve/deny only; per-row checkboxes touch `ui.approve_tools` return type, the SSE wire format, and `coordinator.js`.
2. **Throttled `batch_progress` SSE events** — only `batch_started`/`batch_ended` ship today; a diff-on-change + 5s heartbeat (mirror `wait_progress`) gives a "spawning N/N" indicator.
3. **Per-skill quota scoping** — global defaults + per-session override ship; add `spawn_budget`/`spawn_rate_*` columns to `prompt_templates` (migration 047 reserved) so skill authors can bump budget for wide-fanout skills.
4. **Count-only storage helper** — a dedicated `count_active_workstreams(parent_ws_id, user_id)` with the non-terminal filter baked in (vs summing the `count_workstreams_by_state` map); roll in with the next storage change.
5. **Node registry hygiene** — stale `services`/`node_metadata` GC + collector-side zombie eviction; independent of coordinator work.
6. **Coordinator session compaction** — long-lived coordinators grow their message list unbounded until the provider rejects. (Promoted to [[project_1_7_roadmap]]; core cooperative compaction shipped as #730, 2026-06-27 — verify coordinator coverage before closing.)
7. **`_children`/`_child_to_coord` LRU cap** — bites only very long-lived coordinators with high child churn.

(Plus a v2 kanban — separate plan doc.)

---
name: project_projects_feature_design
description: "Projects (governed container: scope=project memory + workstream project_id): SHIPPED PR #724 2026-06-27, migration 062; supersedes #684 persona-collection."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-20T17:02:12.091Z
---

**Shipped as PR #724 (2026-06-27).** Design converged + built 2026-06-26
(multi-turn with the user) on branch `feat/projects`; shipped with two follow-up fix commits on
the branch (client refresh hardening / creator race guard / SDK project_id; JSON.stringify cache
fingerprint) — branch content verified fully on main 2026-07-01, so `feat/projects` is deletable.
Migration **062** is the repo head now. Build record + spike-verified file:line map + scoping
calls live in LOCAL `docs/design/projects-brief.md` (never committed). Key built shapes beyond
the design below:
- Shared client data layer `shared_static/projects.js` (ESM + `window.TurnstoneProjects` bridge):
  refreshProjects/projectName/projectChoices/onProjectsChange/createProject — feeds picker + rail +
  shelf from one fetch/cache (rail resolves names client-side, NO per-snapshot backend join).
- `project_id` rides the WS row everywhere (schemas, `list_workstreams` projection both backends,
  dashboard/node_snapshot/ws_created builders, BOTH `_coordinator_rows` lanes, collector delta
  path, both clients). The console **interactive cluster-create proxy rebuilds the body** → had to
  forward project_id explicitly (not a passthrough).
- **Scoping calls (explicit):** CLI picker OUT (cli.py `user_id=""` → access fails-closed, a flag
  would be inert; needs CLI identity first). Standalone picker = populate-only (create-in-picker is
  console launcher's "+ New project…" sentinel only). Manage shelf = **console-only** (governance
  front-door). Member-add user dropdown needs admin.users to populate.
- **/review hardening (post-build, all confirmed+fixed except a perf nit):** the DELETE paths were
  the soft spot — (1) `delete_project` now cascades `structured_memories` scope=project (no FK in
  the schema family, so explicit, both backends); (2) `memory(delete,scope=project)` is now
  write-gated on `_project_writable` like save (a read-only member of a PUBLIC project could delete
  shared memory); (3) visibility flip is owner-only (a member could publicize); (4) archived
  projects are not recalled — gated in the CONSTRUCTOR, not `user_can_access_project` (the owner
  needs that to reach archived projects to unarchive). Access now resolves via one
  `auth.resolve_project_access(uid,pid)->ProjectAccess(can_read,can_write,name,state)` single fetch;
  `user_can_access_project` is a thin wrapper. Deferred perf nit: per-turn project COUNT has no
  `structured_memories(scope,scope_id)` index.

Re-spike if weeks pass ([[project_velocity]]). This REPLACES the topical-axis half of
[[project_memory_collections_design]] (#684): the working-set bucket is now a first-class
**PROJECT**, decoupled from persona. Origin: #684 itself flagged "shift perspective on personas
as a whole" — this is that shift.

## Why project, not persona-collection (the core move)
#684 made ONE axis (collection, 1:1 with persona) carry BOTH a persona's **role-craft** ("how
`researcher` researches, across all work") AND a **project's durable state** ("the facts of THIS
investigation"). That only holds if every coordinator persona is single-purpose; the moment you
REUSE a persona across unrelated projects (the whole point of reusable personas), the collection
conflates them and you lean on escape hatches (#684 called them "the scope-chain patched flat — a
leak"). User's framing: persona collections will be reused across unrelated projects, so tightly
coupling project memories to a persona makes no sense. → Project is its own axis; persona stays pure
identity/tools/toggles (#683 unchanged).

## Locked model — recall
`recall(ws) = global ∪ user ∪ workstream [∪ coordinator] [∪ project(P) iff ws attached to P
AND user has access to P]`. Mechanism: project is a **new `scope` value** (`scope=project`,
`scope_id=project_id`) dropping straight into the existing `_visible_scopes()` (session.py ~7837)
+ `_build_scope_or_clause()` (_postgresql.py ~4102) — NO new recall machinery.
- **`coordinator` scope is UNTOUCHED and still isolated.** The #684 "children don't inherit the
  parent's collection" rule was really about coordinator-SCOPE memory and bled into the collection
  design; it does NOT apply to projects (user: the isolation rule concerned coordinator-scope
  memories and spilled over into the collection design).
- **`persona` scope = reserved, UNBUILT.** Symmetric to `project`; add only when "a researcher
  that gets better across runs" is real, not hypothetical. v1 personas hold no memory rung.
- **No default project; NO migration of existing rows.** A ws with no project = today's
  `global∪user`. This makes opt-in *automatic* (recall iff attached) — can't recreate the leak,
  nothing to police. (User rejected their own earlier idea of tying everything to a default project
  in favor of this.)

## Locked model — Projects as a governed resource CONTAINER
Not a memory feature — a container; memory (`scope=project`) + conversations
(`workstream.project_id`) are just the first two tenants. User: worktrees, files, artifacts and
other resources are eventually meant to become part of a project → keep `projects` table
resource-AGNOSTIC.
- Entities: thin `projects(id, name, owner_id, visibility: private|public, state: active|archived,
  created, updated; parent_project_id seam reserved)` + `project_members(project_id, user_id)`.
  Nullable `project_id` FK on workstreams.
- **Access = RBAC perm (capability) ∧ per-project ACL (which projects).** New role triple
  **`project.{create,read,write}`, ALL admin-default**, granted outward via the migration-058
  role-permission system. Composition: read/write need the perm AND (owner ∨ member ∨
  public-for-read). **`visibility=public` (the user's `*`) opens READ to any `project.read`
  holder; WRITE stays member-gated** (no public graffiti / prompt-injection wall). `create` is
  role-only. **Owner has implicit full access to their OWN projects**; perms+ACL govern access to
  others'/shared projects. Access checked at attach AND recall so revocation revokes. This is the
  FIRST cross-user shared memory space (only `global` crossed users before, admin-curated).
- **Children inherit the parent's `project_id`** on spawn → a coordinator's tree shares the bucket
  (read+write); `spawn_workstream(project=…)` is the rare override.

## The type/scope naming fix (do it WITH this, while data is small)
`type` (semantic flavour) and `scope` (ownership/home) are different axes that both wanted the
word "project". Fix on the TYPE side, keep `scope=project` matching the user-facing entity (a
`scope` rename would bake a permanent entity↔scope mismatch). **Rename the memory `type` value
`project` → `general`** — it was the misleading DEFAULT all along ("no particular flavour"), so
this also fixes a pre-existing wart. Types become `user|general|feedback|reference`. **Clean
break, no alias** (1.7 is experimental main, breaking-tolerant). A row can legitimately be
`type=general, scope=project` or `type=reference, scope=project`.

## UI (all v1, per user)
- **Project picker** in the creation box: shared `shared_static/composer.js` (console, via
  `setOptionChoices`/`setOptionFieldVisible` like the node picker) + the `new-ws-dialog` modal +
  `dashboard-input` composer (ui/static). Feeds a new `project_id` field on
  `CreateWorkstreamRequest` (server_schemas.py ~137) → `make_create_handler` (session_routes.py
  ~2151). Picker lists projects the user can access; "+ create new" inline.
- **Group conversations by project** — v1 shows YOUR OWN threads foldered by project; shared-thread
  visibility (planned soon) is a reserved seam (model already supports it: `workstream.project_id` +
  access; just a query + a privacy decision).
- **Manage surface** = a **Service Hatch shelf** (create/rename/archive + member management:
  whitelist users / toggle public `*`), per house style.
- NB naming collision: the console ALREADY labels its coordinator/interactive toggle "personas"
  (`launcher-personas`, `persona-coordinator`) — rename when #683/this land or it collides.

## Migration 062 carries (head is 061)
`projects` + `project_members` tables; `workstreams.project_id`; `project.{create,read,write}`
role perms (058 system); the `type` value rename `project`→`general`. #683 personas can ride
its own migration — project is now independent of personas.

## Deferred / reserved seams
persona role-craft memory (`persona` scope); episodic/TTL lifespan (defer entirely — opt-in
recall already kills the leak); other resource types under a project (worktrees/files/artifacts);
shared-thread grouping view; per-resource-type perm refinement (`project.files.write`, …);
hierarchical projects (`parent_project_id`). **#684 disposition RESOLVED 2026-07-02: CLOSED as
superseded** (original title kept; body = decomposition record + two refile-on-unlock notes:
reserved `persona` role-craft scope, durable|episodic lifespan). The memory ON/OFF TOGGLE is the
only surviving persona-side memory component and rides #683. Axis framing: persona = operator
control over sys-msg composition ⊥ project = workstream visibility + collections of
workstreams/artifacts/memories.

Cross-refs: [[project_memory_collections_design]] · [[project_1_7_roadmap]] ·
[[project_mid_conversation_system_messages]] · [[reference_memory_store_maintenance]] ·
[[project_design_constraints]] · [[feedback_minimal_scope_first]].

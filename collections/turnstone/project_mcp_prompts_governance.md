---
name: mcp-prompts-as-governed-templates
description: "MCP server prompts / external prompt sources: synced into prompt_templates as mcp__server__name rows under RBAC (shipped, migration 009); never a side channel."
metadata: 
  node_type: memory
  type: project
---

MCP prompts are first-class citizens in the governance system, synced into the
`prompt_templates` table — NOT a side channel that would bypass RBAC, approval, or audit.

**Status (shipped, verified 2026-05-30):** `mcp_client.sync_prompts_to_storage()` is
wired and called from every prompt-refresh path (pool refresh, per-server refresh,
dynamic refresh). MCP prompts land in `prompt_templates` named `mcp__{server}__{name}`;
migration `009_mcp_prompt_origin` added the origin marker. The early "should be"
framing of this note is now "is."

**The pattern (why this note still matters):** "import external prompt-shaped things
into one RBAC-governed table, mark origin, treat imports as read-ish" is the
connective tissue. MCP prompts (`009`) was the FIRST instance of this pattern; the
skills system (`021_skills_evolution` + SKILL.md + skills.sh/GitHub) is the big
generalization of the same idea. They are cousins on the shared `prompt_templates`
substrate — MCP prompt sync was NOT subsumed into skills, it coexists. See
[[project_skills_system]].

**Mechanics:**
1. Fetch prompts via `session.list_prompts()` on existing MCP client connections
2. Sync into `prompt_templates` with the `mcp__server__name` origin marker (distinguishes from hand-authored + skill-sourced rows)
3. Refresh on MCP dynamic refresh (shares the tool-refresh notification/polling paths)
4. Governed by the same RBAC / versioning the rest of the table uses
5. MCP-sourced rows are import-origin (not hand-editable); manual templates win name collisions

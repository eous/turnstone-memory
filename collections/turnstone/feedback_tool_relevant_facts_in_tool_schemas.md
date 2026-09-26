---
name: feedback_tool_relevant_facts_in_tool_schemas
description: "Lowering an env fact (cwd, workspace dir) into model context: if only tool-holding sessions need it, it goes in those tools' descriptions, not CONTEXT (#857)."
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-07-19T11:29:36.533Z
---

When lowering an environment/state fact into model context, choose the surface by relevance scope (ruled by the maintainer on #857, 2026-07-19, overriding my Session-Context implementation twice): a fact only meaningful to sessions holding particular tools (cwd, workspace dir → fs/shell tools) belongs **in those tools' descriptions**, rendered from per-tool metadata templates at tool-list build time. The system-prompt CONTEXT block is for facts universal to the session (date, user, workstream, project, kind). The test is whether the fact is relevant to every persona.

**Why:** gating becomes intrinsic — a persona/kind without the tool never sees the fact, with no parallel gate-set to drift; task-agent children carry their own copies via `_task_tools` independent of parent visibility; the fact survives `system_prompt_override` (eval). A CONTEXT-block line needs hand-maintained tool-set gating and misses the sub-agent lane.

**How to apply:** follow the #857 pattern — metadata key in the tool JSON (registered in `_META_KEYS`), template substitution via `str.replace` (never `str.format`; prose carries `${VAR}` braces), deep-copy noted tools (fs dicts are shared/aliased across the module constants), apply only to pristine bases at the `_set_interactive_tools` chokepoint (assignment-time, keeps the wire tools block byte-stable for prompt caches). See [[project_857_cwd_tool_notes]].

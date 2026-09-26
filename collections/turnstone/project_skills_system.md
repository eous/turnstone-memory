---
name: skills-system-initiative
description: "Skills roadmap on prompt_templates: schema/scanner/discovery DONE, quality signals + eval loop unbuilt; one table stays, skills never inject identity."
metadata: 
  node_type: memory
  type: project
---

Skills system is a multi-phase initiative to evolve prompt_templates into a skills entity.

**Why:** Inspired by SAGE paper (arxiv 2512.17102v2) on RL-driven self-improving agents with skill libraries. Key insight: Turnstone already has the reward loop infrastructure (intent validation verdicts + eval.py three-tier optimizer) but no skills layer. No tool in the ecosystem closes this loop yet.

**How to apply:**
- Phase 1: ~~Schema evolution~~ DONE (PR #106) — description, tags, activation, version on prompt_templates; API/UI rename to "skills"
- Phase 1.5: ~~Skill scanner~~ DONE (PR #108) — 4 risk axes, 30+ regex patterns, auto-scan on create/update
- Phase 2: ~~External discovery~~ DONE — skills.sh search + GitHub SKILL.md fetch, install flow, admin UI pill toggle, SDK methods, 48 tests
- Phase 3: Quality signals (verdict correlation, nudge frequency, completion tracking), 5D attribution via chi-squared
- Phase 4: Eval pipeline extension (per-skill optimization, online reward loop, periodic batch optimization)

**Key decisions:**
- prompt_templates table stays (no rename). Public interfaces rename to "skills" — **still true post-refactor**: [[project_skillmd_refactor]] (PR #762, merged 2026-07-04) deliberately deferred the storage-side `type` discriminator (its "Step 4"), so `prompt_templates` remains the one table, discriminated only by `origin`.
- Shared substrate: MCP server prompts also sync into `prompt_templates` (origin `mcp__server__name`) via the same governed-import pattern skills generalize. Skills (skills.sh/GitHub SKILL.md) and MCP prompts are cousins on this table, not the same feature — `021` migrated *workstream_templates* in, not MCP prompts. See [[project_mcp_prompts_governance]]
- SKILL.md format (the de facto standard across agent tools) converted to structured storage on install
- **SUPERSEDED (2026-07-04):** "Skills ≈ prompt templates conceptually (both inject system message content)" was the ORIGINAL framing here and is now factually wrong — [[project_skillmd_refactor]] shipped the opposite conclusion: skills are capability/context and must NEVER inject system-message identity, in any invocation path including `task_agent`. Identity is persona's job exclusively. Keep this table-stays-one-table decision above; drop the "both inject system message content" equivalence.
- Workstream templates (WS templates) are a different abstraction and stay as-is
- `activation` column replaces semantic role of `is_default`: "default" (auto-apply), "named" (explicit), "search" (BM25 discoverable)
- Attribution uses simple statistics (chi-squared contingency tables), not embeddings
- Online reward from intent verdicts + nudge frequency; offline from eval.py test suites

**External sources researched:**
- skills.sh: Vercel-backed, ~289 skills, search API at /api/search, SKILL.md format, audit API
- One agent framework: 91 bundled skills, 7-source hub, 80+ regex security patterns, self-improvement claims are prompt-level not RL
- Anthropic: SKILL.md standard (agentskills.io/specification), plugins as distribution unit, three-tier progressive disclosure

---
name: project_skillmd_refactor
description: "Skill activation or identity surfaces (SKILL.md refactor SHIPPED PR #762): skill = capability only, persona owns identity; gate at _high_risk_skill_denied."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-20T17:02:30.131Z
---

**SHIPPED.** `refactor(skills): persona owns identity, SKILL.md is capability` merged to main as **PR #762 (2026-07-04)**, unblocked same day by **PR #766** (`resolve_when_pending` — fixed a pre-existing flaky lost-wakeup race in approval-prompt tests that had been red-herring-blocking `test (3.12)` on #762's CI; unrelated to the refactor itself, just its final gate).

**Root cause diagnosed (two-era conflation):** turnstone's `prompt_templates` table originally held *identities* (a template WAS the system-message persona), then had Anthropic's agentskills.io SKILL.md feature (`$ARGUMENTS`/`${CLAUDE_*}` substitution) bolted on as if it were the same concept. Prompt-templates were identities; SKILL.md skills are capabilities. One table/loader/destination for two different concerns was the disease — surfaced as a substitution asymmetry across 4 invocation contexts (user/slash launch, `skills(load,...)`, `spawn_workstream/batch(skill=)`, `task_agent(skill=)` — the last of which rendered NEITHER `$ARGUMENTS` nor `${CLAUDE_*}` and glued the skill body into `Turn.system` as if it were identity).

**Decision (Option B, Anthropic-conformant):** skills = capability/context, NEVER system-message identity, in ANY invocation path including `task_agent`. Identity comes only from the **persona** feature (#683, PR #757, merged 2026-07-03) or the fixed default sub-agent identity. Verified spec-conformant against agentskills.io + Claude Code docs: 3-stage progressive disclosure (discovery→activation→execution) + capability-never-identity is the standard; turnstone's old always-in-system-message placement was the deviation.

**What shipped:**
- One unified skill-body substitution/placement pipeline across interactive, defaults, and `_exec_task` (was 3 divergent code paths) — `${TURNSTONE_*}` canonical env vars, `${CLAUDE_*}` alias kept for `SESSION_ID`/`EFFORT` only. **`CLAUDE_SKILL_DIR` alias explicitly DROPPED** (a review caught the prompt-alias vs bash-host-guard diverging on which dir it named) — turnstone claims neither name, in neither prompt nor bash.
- `task_agent` gained a `persona=` field — identity is now uniform via persona across every creation/spawn path (create · spawn_workstream · spawn_batch · task_agent); a passed skill is capability-context only, never identity. The persona's full 4-lever envelope (prompt/tools/mcp/memory) is honored on `task_agent` and capped by the *parent's* grant (attenuation) — an earlier round only capped the tools lever, a second review round caught mcp/memory still leaking through uncapped.
- Applied-skill bodies moved out of the identity system message into a separate user-role context message; the search-activated discovery catalog is unchanged.
- Risk gate: model-initiated activation of `risk_level` high/critical skills is denied on **every** activation surface (`skills(load)`, `spawn_workstream/batch(skill=)`, `task_agent(skill=)`) via one shared chokepoint (`_high_risk_skill_denied`, fail-closed on storage error); principal-invoked `/skill` bypasses. Durable lesson from two full-PR review rounds (high then max effort, ~44 agents combined): gating one surface and missing a sibling is a bypass, not a gate — the max round caught what the high round missed on `task_agent` specifically; re-review the least-touched surface hardest.
- **HYPOTHESIS.md Principle 7 (new, durable):** skill tools = visibility/needs (plan-rank); permission stays principal+RBAC+γ; authority-carrying skills (`allowed_tools`/`auto_approve`) require `disable-model-invocation` and are capped by the current/parent grant — model-auto-activated skills must never WIDEN authority.
- Pre-merge gate cleared: `turnstone-eval --skill-adherence` main-vs-#762 (n=50, 4 scenarios) showed no adherence regression from moving skills out of the system message (200/200 vs 199/200 treatment adherence, the 1-point gap being sampling noise on one model).

**Still genuinely open (re-verified 2026-07-06 via `gh`/branch search — no PR or branch exists for either):**
1. **Sub-agent persona identity FRAMING** (a display/framing issue, NOT security — authority is correctly attenuated regardless): `_exec_task` currently APPENDS the child persona's base prompt after the parent's identity instead of REPLACING via `base_override` the way a main-session persona does, so a sub-agent can end up carrying two stacked identities. Brief exists locally: `docs/design/subagent-persona-identity-brief.md` (Option A = recompose via `base_override`); not yet started.
2. **Step 4 (storage `type` discriminator)** — deliberately deferred pending resolution of "should MCP-prompts be a separate concept from skills?" (design doc's §7 Q4); gates a few smaller follow-ups (persisting literal `disable-model-invocation`, `variables`→`arguments` consolidation for MCP-synced prompts, sub-agent skill-resource-dir materialization). Brief: `docs/design/skillmd-followups-brief.md`; not yet started.

**Why:** the pre-refactor asymmetry meant a skill using `${CLAUDE_EFFORT}` worked via the `skills` tool but silently rendered literal via `task_agent`; skill-as-system-message also blurred authority and busted the prompt cache on every named-skill switch.

**How to apply:** when adding any new model-initiated activation/authority surface, gate it at the shared chokepoint (`_high_risk_skill_denied`) — do not re-derive per-surface logic. Skill bodies use capability/procedure voice ("apply this technique"), never "you are X" identity voice — identity is persona's job everywhere, including sub-agents.

Related: [[project_skills_system]] [[project_system_message_composition]] [[project_mid_conversation_system_messages]] [[reference_turnstone_skill_authoring]] [[project_harness_hypothesis_doc]]

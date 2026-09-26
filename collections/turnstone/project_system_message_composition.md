---
name: project_system_message_composition
description: "Editing persona, policy, or per-client prompt text: compose_system_message() (turnstone/prompts) is the one seam; persona base_override swaps only BASE."
metadata: 
  node_type: memory
  type: project
---

Built 2026-03-31, long since committed (this file's "uncommitted on main" framing was stale — session.py has grown to ~16,200 lines since). Replaced the monolithic persona + tool patterns string in `ChatSession._init_system_messages()` with a composable module system.

**Architecture:**
- `turnstone/prompts/__init__.py` — `compose_system_message()`, `ClientType` enum (web/cli/chat), `SessionContext` dataclass
- `turnstone/prompts/base.md` — persona (always included)
- `turnstone/prompts/env/{web,cli,chat}.md` — rendering rules per client surface
- `turnstone/prompts/tools.md` — tool usage patterns (included when tools available)
- `turnstone/prompts/policies/web_search.md` — file-based default, tool-gated

**DB-backed policies:** `prompt_policies` table (migration 031). Admin CRUD via `/v1/api/admin/prompt-policies`. DB policies override file-based ones by name. Tool gating silently skips policies when their required tool isn't available.

**Integration:** `_init_system_messages()` calls `compose_system_message()` for the non-creative-mode path. Creative mode bypasses entirely. Everything after (tool search hint, MCP, skills, instructions, memories, nudges) is unchanged.

**ClientType threading:** `client_type` flows from Discord cog → ChannelRouter → SDK → HTTP body → server handler → WorkstreamManager → session_factory → ChatSession. Default is `WEB` for server, `CLI` for CLI/eval. Discord sends `chat`.

**Why:** Decouple persona, environment, context, tools, and policies so each can vary independently across client surfaces. Web gets Mermaid/KaTeX guidance, CLI gets terminal rules, chat platforms get constrained markdown rules.

**Persona integration (shipped since, PR #757, merged 2026-07-03) — VERIFIED live in code 2026-07-06:** `compose_system_message(base_override=...)` is the seam personas hook into. `turnstone/prompts/__init__.py` confirms: `if base_override: parts.append(base_override)`, else falls back to kind-specific `personas/orchestrator.md` (coordinators) / `personas/engineer.md` (default). A resolved persona's prompt REPLACES exactly the BASE module — everything else in this file (ENV/CONTEXT/TOOLS/POLICIES) is untouched by persona. The composer also stayed skill-agnostic through [[project_skillmd_refactor]] (PR #762): skill bodies are appended as separate context messages elsewhere in the session, never folded into this composition.

**How to apply:** When adding a new client surface, create `env/{name}.md` and a `ClientType` value. When adding behavioral rules, create a file in `policies/` or use the admin UI. When touching persona/skill/policy composition, `compose_system_message()` is the one seam all three concerns pass through — re-grep current line numbers before citing them, this codebase moves ~50K LOC/week ([[project_velocity]]).

---
name: project-architecture-map
description: "Before architectural work: system map (2026-07-06; entry points re-checked 2026-09-27) with the 8 entry points, core/session.py engine, subsystem file locations and key patterns."
metadata: 
  node_type: memory
  type: project
---

# Architecture map (as of 2026-07-06)

**Overview**: Multi-node AI orchestration platform: tool use, agent routing, cluster ops. Python 3.11+. Multi-provider LLM (OpenAI+Anthropic+Google). Strict mypy+ruff, no TODO/FIXME. Tracks as of 2026-07-06, superseded by [[project_current_state]] (re-check `git tag`): `main` (post-1.7.0 experimental, heading to 1.8), `stable/1.7` (**v1.7.0**, cut 2026-07-05, Apache 2.0 — current), `stable/1.6` (**v1.6.9**, Apache 2.0 — one prior), `stable/1.5` (**v1.5.18**, BUSL — due to retire per "current+1 prior" policy; still patched as of 2026-07-06, not confirmed retired). 1.4 retired when 1.6 became current; expect 1.5 to follow.

**Architecture**
- **8 entry points** (`[project.scripts]` in pyproject.toml, dev cf70819, 2026-09-27): turnstone (CLI), -server (web), -eval, -optimizer ([[project_eval_optimizer_split]]), -console (dashboard), -admin (user/token CLI), -channel (gateway), -doctor (setup/diagnostics; replaced -bootstrap in #718, BREAKING).
- **Core engine**: `core/session.py` (28,691 lines on dev 2026-09-27; ~16,200 on 2026-07-06) ChatSession — tool exec, plan mode, tool search, rewind/retry; provider-agnostic. `tool_search.py`=BM25.
- **Trajectory**: `core/trajectory.py` neutral flat `Turn`=canonical in-memory+storage; wire mutation ONLY in `core/lowering.py` (fold+repair). [[project_canonical_trajectory_redesign]]
- **Prompts**: `prompts/` modular BASE/ENV/CONTEXT/TOOLS/POLICIES via `compose_system_message()`; `ClientType` routes web/cli/chat. [[project_system_message_composition]]
- **Providers**: `core/providers/` LLMProvider + OpenAI/Anthropic/Google; translate at API boundary, internal OpenAI-like; producer-tagged `native` lane keeps block metadata.
- **Frontend**: vanilla HTML/CSS/JS (ESM), ONE L-shell (console+server): PaneManager+rail+tabs+split; modals→"Service Hatch" shelves. [[project_frontend_lshell_renovation]]
- **Routing**: direct HTTP + rendezvous hashing (HRW/FNV-1a, `core/rendezvous.py`); `ConsoleRouter.route(ws_id)`; `workstreams.node_id`=cache NOT routing.
- **API/SDK + Auth**: `api/` (Pydantic v2, OpenAPI 3.1), `sdk/` + TS `sdk/typescript/`; `core/auth.py` JWT+bcrypt+tokens, scopes read<write<approve<service. [[feedback_everything_needs_auth]]
- **Channels + MCP**: Discord + Slack (Socket Mode), `client_type="chat"`; `core/mcp_client.py` async SDK→sync (circuit breaker, pre-close, debounce, self-healing reconnect — [[project_mcp_dead_transport_followup]]).
- **Governance + Attachments + Tests**: `audit.py`/`policy.py` heuristic + output-guard + LLM judge; attachments content-addressed + perception fallback [[project_attachments_subsystem]]; 391 `tests/test_*.py` files on 2026-09-27 (255+ on 2026-07-06), "live" marker.

**Key patterns**
- `extra_body.chat_template_kwargs` carries `reasoning_effort` for local servers; commercial handle effort natively via ModelCapabilities.
- `--provider` + `[models.*.provider]` adds openai-compatible/google/xai/anthropic-compatible (registry-only). `anthropic`=CORE dep since 1.6.
- Tool/web search: native Anthropic → native OpenAI → client fallback. Tool naming compound not bare (`task_agent`; `plan_agent` REMOVED) [[project_tool_naming_constraints]].
- `PROGRESS.md`/`BRIEFING.md`/`docs/design/*.md` local-only — never commit.

**State detail (2026-07-06)**: migration head **065** (062 projects, 063 personas, 064 drop dead mcp_pending_consent cols, 065 Entra ID oid/tid identity); main was 9 commits past the v1.7.0 cut at last measure. The current head is tracked in [[project_current_state]] (077 on dev, 2026-09-27).

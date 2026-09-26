---
name: project_1_7_roadmap
description: "1.7.0 SHIPPED 2026-07-05; recall for what rolled to 1.8+ (mcp v2 #679 brief, tail-injection, kind modal): re-spike before building."
metadata:
  node_type: memory
  type: project
  modified: 2026-07-20T16:55:38.113Z
---

**v1.7.0 shipped stable 2026-07-05** — `stable/1.7` branch cut, tagged `v1.7.0`, CHANGELOG.md documents it (headline: Personas). `stable/1.6` (v1.6.9) is now "one prior" stable; `stable/1.5` (v1.5.18, BUSL) is due to retire per the "current + one prior" policy but was still being patched as of 2026-07-06 (not formally retired yet). Main is past the cut, now the experimental line heading toward 1.8.

This file was drafted 2026-06-11 as a forward-looking "1.7 dream list." Rewritten 2026-07-06 now that 1.7 has actually shipped: condensed everything that landed to a pointer (full detail lives in the linked per-feature files, most of which were themselves condensed in this same pass), kept only what's still genuinely pending. Weigh anything still open against real usage: the dev cluster's daily job is news agents (qualify/break/generate morning reports) run by long-lived coordinators.

## Shipped in 1.7 (condensed pointers — see linked files)

- **Personas (#683) — THE 1.7 headline.** SHIPPED via PR #757 (2026-07-03). Residual follow-ups tracked in issue #756 (5/15 done as of 2026-07-06).
- **Projects (resource container, #724)** — SHIPPED. [[project_projects_feature_design]]
- **Task-agent sub-harness (#732)** — SHIPPED. [[project_task_agent_modernization]]
- **Cooperative + chunked compaction (#730/#731/#740)** — SHIPPED. [[project_cooperative_compaction]], [[project_compaction_rehydration_deadlock]]
- **Concurrent approval cycles + judge-gated sub-agents (#773, same-day fix #775)** — SHIPPED. [[project_concurrent_approval_cycles]]
- **Reasoning-effort control conformance across all lanes (#771/#774)** — SHIPPED.
- **SKILL.md/persona identity split (#762)** — SHIPPED. [[project_skillmd_refactor]]
- **Multi-user / shared-workstream safety (#750 + hardening wave)** — SHIPPED. [[project_pr750_multiuser_context_review]]
- **MCP client hardening trilogy (#742/#767/#768)** — SHIPPED. [[project_mcp_dead_transport_followup]]
- **BM25→rerank substrate + per-model calibration (#627-629)** — SHIPPED. [[project_bm25_rerank_redirect]]
- **Viz stack** (altair + vl-convert-python) — SHIPPED via **PR #685 (2026-06-21)**. This file previously tracked it as "built + pushed, PR not opened" — corrected 2026-07-06, it merged same day it was drafted.
- **Envelope nonce tags (#726)** — SHIPPED, all open questions resolved. [[project_envelope_nonce_tags]]

## Post-1.7.0: already landed on main, pre-1.8

- Pane hotkeys cross-platform (#776), tool-args wire legalization (#778) — both landed 2026-07-05.
- **New thread, not yet deep-dived in memory:** credential-redaction hardening — PR #780 (client-side tool-call-card redaction) + #781 (bounded key/token prefixes, perf, x-api-key coverage) landed; #779 an earlier draft, superseded. Branch `feat/credential-redaction-hardening` still on origin as of 2026-07-06 — likely more coming. Spans backend log-scrubbing (shares code with [[project_tool_args_wire_legalization]]) and frontend tool-call cards.
- Migration head now **065**: 062 projects, 063 personas, 064 drop dead `mcp_pending_consent` columns, 065 Entra ID `oid`/`tid` identity columns on `oidc_identities` (PR #772 "Addendum to Entra ID's... proclivities" — Entra's `sub` claim is pairwise/per-app, so oid+tid give a stable cross-app key, populated lazily via `provision_oidc_user`).

## Rolled forward to 1.8+ (still live — re-spike before building)

- **mcp v2 package migration (issue #679)** — full brief preserved below, still the plan.
- **Coordinator MCP tool surface (#725)** — still blocked on #679.
- **Memory tail-injection redesign** — move the volatile recalled-memory block out of the cached system prefix into a per-turn tail system turn (the dominant Anthropic cache-miss lever). Still not started as of 2026-07-06 (no matching branch found). [[project_memory_relevance_pipeline]]
- **Q4 server-tool→text projection** — cross-provider resume still drops a foreign producer's server-tool result blocks. Still pending. [[project_canonical_trajectory_redesign]]
- **Kind-aware model modal** — explicit `kind` discriminator still deferred (re-verified 2026-07-06, no `kind` field in admin.js yet). [[project_model_modal_kind_redesign]]
- **Phase-8 backlog** — unchanged. [[project_phase8_status]]

## MCP v2 migration brief (issue #679 — still the plan, re-verified 2026-07-06)

Re-verified 2026-07-06: upstream `mcp` is at **2.0.0b1** on PyPI (confirmed via `pip index versions mcp --pre` and the PyPI JSON API — no `rc` yet). Stable ~2026-07-27 per upstream's own schedule, now 3 weeks out. Our pin is still `mcp>=1.27,<2`; latest 1.x is 1.28.1. The "spike+branch at beta" trigger has been armed since the beta actually shipped (target was 2026-06-30, now past) — nothing has forced action yet since no rc/stable exists.

The migration is NOT mechanical: `streamablehttp_client` → `streamable_http_client` whose new signature takes a PRE-BUILT `httpx.AsyncClient` (rework the auth-capturing factory `_make_capturing_http_factory`), transport returns a 2-tuple (we unpack 3), `mcp.types` flips camelCase→snake_case (`inputSchema`, `isError`, `nextCursor` sweep), `ClientSession` drops the `cursor` param + `get_server_capabilities()` → `initialize_result`, and `FastMCP` → `MCPServer` (integration tests + `examples/mcp-cluster-ops`, confirmed still live 2026-07-06). Drop the `<2` cap + the pyproject filterwarnings entry when done. Independent pre-step (do anytime): inline the two `mcp.shared._httpx_utils` timeout constants + declare a local `McpHttpClientFactory`-shaped Protocol to drop the private-module import.

Research basis: 2026-06-11 agent report; re-examined 2026-06-12 against the live a1, migration.md, and the 2026-07-28 spec RC. **Target the true beta/stable, not the alphas**: a1 implemented only the 2025-11-25 spec (zero capability gain over v1.27), upstream reserves breaking changes per alpha, and the beta is the first cut with full 2026-07-28-spec support (compat shims land before stable). Decisive: the 2026-07-28 stateless core REMOVES the initialize handshake + `Mcp-Session-Id` header, so the alpha's session-id-capture path (httpx event hooks) gets reshaped again — migrating off an alpha reworks the capturing factory twice. Extra surface from migration.md beyond the 06-11 list: `McpError`→`MCPError` (new ctor), resource `uri` AnyUrl→plain str, WebSocket transport removed, and POSIX `stdio_client` no longer kills children after graceful exit (our stdio cleanup must terminate explicitly). #2147 busy-loop still open and maintainer-disputed (2026-04-08) — our resilience wrappers stay regardless (see the durable "no client reconnect handler in the SDK" finding in [[project_mcp_dead_transport_followup]], independently re-confirmed against 1.28.1). Sizing (2026-06-12): ~32 camelCase reads / 8 files; FastMCP in 5 files; 67 streamablehttp/_httpx_utils/McpError sites.

Apps tie-in: SEP-1865 ratified and folded into 2026-07-28 as an official extension; host-side Apps SDK is TS-only (`@modelcontextprotocol/ext-apps`), Python = examples only — v2 is the protocol-level prerequisite for the deferred tool-owned-surfaces on-ramp ([[project_frontend_lshell_renovation]]); iframe/postMessage host work stays frontend-side and deferred. Designated first-party Apps dogfood server: **Understone** (examples/door-game) — its cell-grid screen model (glyph+color, renderer-decoupled) is exactly the data a future `ui://` view renders; gen-2 full-fidelity tile mode is the planned Apps milestone.

**Sequencing update 2026-07-11**: the maintainer's v2-beta spike found the #679 migration minimal in practice (mainly the httpx-factory swap; rest mostly works as-is) — the migration-risk rationale for gating other MCP build-out behind #679 is **invalidated**; MCP work may now proceed in parallel (first mover: #551 re-scope, see [[project_mcp_obo_single_token]]).

**MCP v2-sequenced issues** (`mcp v2` label, filed 2026-06-19): **#679** v2 SDK migration (above). **#680** EMA/ID-JAG client support — standardized IdP-governed successor to host-side OBO, supersedes #551 (host-side RFC 8693 OBO, deferred, kept as design record); key finding: Entra does NOT issue ID-JAG (Okta/Keycloak/Athenz only) — Azure's 2nd-consent prompt is already removable via Entra pre-authorized client apps on the existing `oauth_user` flow, so EMA mainly serves non-MS IdPs. **#681** `ui://` MCP-Apps host (SEP-1865) — render surfaces as an `app-surface` pane via `PaneManager.registerType` + split view, iframe sandbox + postMessage↔JSON-RPC routed through the conversation approval path; Understone gen-2 tile mode = dogfood. Release targets (release-track labels, no milestones): #679 → `1.8`; #680 + #681 → `1.9`. Entra pre-authorized-clients runbook filed as **#682** (today-actionable, independent of the v2 cluster).

## Small deferred items (batch when touching the area)

- `web_search` rerank lift shipped in #626 but never measured against the live news-agent corpus — decide default on/off from data. Rerank floor defaults once measured (calibration tool exists).
- Hatch: sticky column headers, app-wide scrollbar-width/color (Firefox) + thumb-contrast decision, light scrim weight (`shelf-sweep-brief.md`, local).
- Designer: light-theme `--ink-4` micro-label AA (global token decision), admin tab title reflecting active surface.
- `?ws_id=` page-deeplink standardization (deferred from L-shell lifecycle round).

## Standing non-goals (don't relitigate)

No distributed consensus/Raft; no in-process inference (endpoint-only reranker stands); no external vector store (reuse Postgres/pgvector if ever); no external message broker (#540 closed — HTTP/2 mooted it).

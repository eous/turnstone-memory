---
name: hub_architecture_patterns
description: "Index of architecture maps, durable design patterns, gotchas and shipped subsystem designs (moved verbatim from MEMORY.md 09-25): read before designing in a subsystem."
metadata:
  type: project
---

## Maps and model-auth design
- [Aux-call accounting map](project_aux_call_accounting_map.md) — 09-20 verified: utility/task-agent calls isolated from the main estimate + in the ledger via on_aux_usage; judges recorded no usage -> #1199 fixed on PR #1200 (09-20; handoff keeps the write off the deadline worker; live-verified on fable); aux rows raw vs main rows resolved (#1189); utilities ride the primary alias (local KV-cache pressure)
- [#898 model-provider OBO](project_898_model_provider_obo.md) — per-alias auth_mode (entra_obo/entra_app); mint-cache keyed on alias identity, never audience; cooldown on the cache key

## Architecture and durable patterns
- [SSE-core extraction](project_sse_core_extraction.md) — RULED 1.9 (the maintainer 07-24), lands before mcp v2 #679; don't reopen
- [Operator hands-off knob map](project_operator_hands_off_knob_map.md) — Hands-off deployment advice → tool policies + smart approvals first
- [Harness as compiler](project_harness_compiler_dialect_stack.md) — Sequencing harness work: dialect depth = soundness; decidable ships free, speculative needs a gate
- [interlingua frontier](project_harness_interlingua_frontier.md) — HYPOTHESIS.md frontier coda (V* = interlingua, |W| vs L walls) → conjecture only, never a result
- [HYPOTHESIS.md north star](project_harness_hypothesis_doc.md) — Gate/coordinator/compaction design: check HYPOTHESIS.md rules; learned checks only narrow authority
- Reranker: [backend design](project_reranker_backend_design.md) — ENDPOINT-ONLY via a Cohere/Jina client, never in-process; web_search reranking shipped #626; web_fetch reranking ripped
- Reranker: [BM25→rerank redirect](project_bm25_rerank_redirect.md) — relevance FLOOR; SHIPPED #627-#629, BM25 recall then rerank; thresholdable floor for proactive memory injection
- Approvals: [Smart Approvals](project_smart_approvals.md) — Smart Approvals verdict wait: inside approve_tools after _reset_approval_cycle; batch-atomic
- Approvals: [Intent-verdict lifecycle](project_intent_verdict_lifecycle.md) — Missing verdicts after restart/judge cancel: PR #646; caller owns cancel policy, one verdict each
- Approvals: [Early-paint](project_early_paint_tool_calls.md) — Tool card early paint (#621) → tool_pending first, upgrade in place by call_id
- Approvals: [Inline child approvals](project_inline_child_approvals.md) — Coord inline approvals (PR #424) → one payload serializer; verdicts via child_ws_intent_verdict SSE
- [Judge completion interlingua](project_judge_completion_interlingua.md) — #827/#837 shipped, #831 = PR #841; Turn IR via model_turn; sampling = alias > config > model def > omit
- [Judge func_args projection](project_judge_func_args_projection.md) — #760; a new arg on a needs_approval tool goes into the _evaluate_intent projection + a test in the same change
- Gotchas: [Tool naming](project_tool_naming_constraints.md) — New tool name → suffixed compound (task_agent), never a bare channel-like word like plan
- Gotchas: [Utility-completion thinking budget](project_utility_completion_thinking_budget.md) — Utility LLM call empty on thinking model → max_tokens for a full think pass; no temp/effort in code
- Gotchas: [System message composition](project_system_message_composition.md) — Persona/policy/env prompts → compose_system_message() is the one seam; persona swaps BASE only
- Gotchas: [ConfigStore default vs empty](project_configstore_default_vs_empty.md) — ConfigStore non-empty default + empty=disable → check stored_keys(); get() masks unset
- Gotchas: [Dual-schema parity](project_dual_schema_parity.md) — Schema change → edit migration AND _schema.py; test_schema_parity.py pins them equal; no seed rows
- Gotchas: [Dual style.css](project_dual_static_style_css.md) — style.css differs per server → shared visual rules go in shared_static/*.css
- Gotchas: [Bash tool pipe-EOF hang](project_bash_tool_pipe_eof_hang.md) — FIXED #816 (_exec_bash killpg on every exit); opt-in background calls = #817
- SHIPPED: [Canonical trajectory](project_canonical_trajectory_redesign.md) — Trajectory/wire/storage code → canonical Turn SHIPPED v1.6.0; lowering.py owns fold+repair
- SHIPPED: [Mid-conv system messages](project_mid_conversation_system_messages.md) — Mid-conv role=system SHIPPED v1.6.0; native on current Claude rows (flag per row), else nonce-fenced fold via core/fence.py
- SHIPPED: [Attachments](project_attachments_subsystem.md) — Attachment kinds/perception (shipped 1.6.x): refcounted blobs + capability-gated modality fallback
- SHIPPED: [Frontend L-shell](project_frontend_lshell_renovation.md) — Frontend pane/shell work: L-shell SHIPPED; coordinators console-local, interactive node-proxied
- SHIPPED: [Admin shelf](project_admin_shelf_redesign.md) — New console admin dialog: pane-scoped hatch shelf, not a popup; obey clip/label/nesting rules
- SHIPPED: [Messages-API provider](project_messages_api_provider.md) — base_url no /v1; effort always reaches local wires (#771/#774), ordinal snapping, toggles vs grade
- SHIPPED: [Judge deadline daemon](project_judge_deadline_daemon.md) — Timeout on a blocking call: run_with_deadline daemon thread, never ThreadPoolExecutor (atexit hang)
- SHIPPED: [Flaky CI hang](project_flaky_ci_hang_asyncio_sleep.md) — asyncio.sleep patched in tests / CI hang at 92% → per-object _sleep seam, never the global
- SHIPPED: [mTLS](project_mtls_architecture.md) — mTLS or console HTTPS → console is plain HTTP behind Caddy; 2026-05-30 cert fixes landed
- SHIPPED: [Direct HTTP transport](project_direct_http_transport.md) — Redis MQ and hash ring are gone; direct HTTP + rendezvous-hash console routing, complete
- SHIPPED: [Gemini thought_signature](project_gemini_thought_signature.md) — Gemini thought_signature 400 on tool calls: SHIPPED #328, provider_blocks lane hooks in _google.py
- SHIPPED: [MCP resilience](project_mcp_resilience.md) — mcp>=1.27,<2 until #679; keep closure layers thin (v2 keeps message_handler); caplog cannot see structlog
- SHIPPED: [MCP cluster-ops](project_mcp_cluster_ops_example.md) — Multi-node SDK dispatch: copy mcp-cluster-ops route_create_workstream/send_and_wait/route_close
- SHIPPED: [MCP prompts governance](project_mcp_prompts_governance.md) — MCP prompts / external prompt sources → governed prompt_templates rows, never a side channel
- SHIPPED: [Model definitions](project_model_definitions.md) — New admin entity: copy the model_definitions pattern, config-over-DB merge, write-only secrets
- SHIPPED: [Three-facet validation](project_three_facet_validation.md) — judge/output_guard/skill_scanner → three facets COMPLETED; output guard annotates, never gates
- SHIPPED: [Eval optimization](project_eval_optimization.md) — Eval plateau on system-prompt tuning: optimize tool descriptions instead (79% to 98% on 20B)
- SHIPPED: [Reasoning replay](project_reasoning_replay.md) — Reasoning replay / new model profile: capability defaults False; vLLM Phase 5 asymmetry is by design
- SHIPPED: [Coord route drift](project_coord_client_route_drift.md) — Client URL tables (_ROUTE_PATHS): test against mounted Starlette routes, not literal strings
- SHIPPED: [External contributor review](project_external_contributor_review.md) — External-contributor PRs: parallel per-PR review, verify vs source, merge, then follow-up hardening
- SHIPPED: [Skills system](project_skills_system.md) — Skills roadmap → discovery shipped, quality-signal/eval phases unbuilt; one prompt_templates table

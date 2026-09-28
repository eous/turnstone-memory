---
name: hub_shipped_investigations
description: "Index of shipped or closed issue investigations (lines moved verbatim from MEMORY.md 09-25): read when a bug touches a subsystem that had an earlier fix."
metadata:
  type: project
---

## Shipped or closed investigations
- [Attachment framing for small models](project_attachment_framing_small_models.md) — 09-28: Nemotron 4B/30B looked on disk for attached files; fix = label before each text attachment on the wire + read_file not-found note (#1220), no tool-definition change; eval_attachments.json; open_preview gap
- [Composer typing lag](project_composer_typing_lag.md) — 09-24: shell grid auto rows re-measured the transcript per layout pass; fix = definite rows on .app+.panes; contain:strict useless (Chrome) / 26x worse (Firefox); PR #1205, 1.8 backport #1206
- [Server-tool usage inflates context](project_server_tool_usage_inflates_context.md) — Anthropic native web_search sums input across server iterations (ws f2ec5ec0 09-18); `resolve_context_usage` (#1193/#1196) + #1188/#1190 lane charge ON DEV since 09-20 via PR #1198 (rebase-merged: 60bfed7b, 4e677f1f); final shape = raw appended count, completion+lane charge, replay family, lane request ≠ calibration sample; #1197 = delete in-process fork copy (own PR)
- [#1169 shared completion recovery](project_1169_shared_completion_recovery.md) — on dev 09-18 via
  PR #1178 (e83c4340); 6 rulings 09-17 (JSON envelope = rejected request; compaction at any posture;
  one allowance); follow-ups #1179-#1183; report docs/design/1169-review-report.md; keep
  deliverables outside temporary storage
- [Anthropic workspace scoping](project_anthropic_workspace_id.md) — built 09-13 on feat/anthropic-workspace-id (on dev since 09-13 via PR #1161; harness gap #1160): `server_compat.anthropic_workspace_id` → client-level default header; one validation rule (visible ASCII ≤128) in console+registry; judges re-pin it on client rebuild; probe identity includes scope; string-presence tests REJECTED
- [#1050 Anthropic SDK v1](project_1050_anthropic_sdk_v1.md) — on dev since 09-13 (PR #1161, with workspace scoping + console fixes): `anthropic>=1,<2`, temperature via extra_body (operator pin wins), credential headers REFUSED in extra_headers on all lanes; native live smoke PASSED 09-12, compat live unrun; follow-ups: workspace header BUILT (PR #1161), `model_context_window_exceeded` → #1162, PR #1164 (adapter raises ContextWindowExceededError; overflow parity)
- [#1070 empty completion](project_1070_empty_completion.md) — structural reject into the re-issue ladder, gated on no server tools; review 09-05 fixed + pinned; rulings: empty chat refusal field ≠ refusal, keep shared 2 re-issues
- [Resume nudge + wake seam](project_resume_nudge_wake_seam.md) — resume nudge RETIRED, `"user"` never wake-eligible (09-05); PR #1110 (branch fix/resume-nudge-wake-seam, worktree <worktree>); never re-add user to WAKE_PENDING
- [#832 main-loop fold](project_832_main_loop_fold.md) — PR #984 MERGED 08-06; #979 closes #832 (#980/#981 filed); mirror law = content only; D12 = ruled-delta registry
- [#937 mid-stream transport retry](project_937_midstream_transport_retry.md) — shipped PR #967; normalize mid-stream httpx death at the iteration site, never pad retryable sets; #940→#965
- [#965 reasoning seam](project_965_reasoning_seam.md) — SHIPPED PR #970 08-04; run-bounded `<think>` split inside drain_stream; replay residual → #971; simplification lessons
- [#917 per-model admission](project_917_per_model_admission.md) — design: gate on ModelRegistry keyed by base_url alone; a thread blocks only for its first slot
- [Opus 5 + cut-short seam](project_opus5_cutshort_seam.md) — SHELVED (conflates cut-short with never-formed); read docs/design/opus5-seam-pr1-findings.md before reviving
- [#894 coord over-rewind](project_894_coord_over_rewind.md) — SHIPPED PR #899; coordinator.js historyStale latch; liveness from the event stream, never render-writable state
- [#900 interactive backport](project_900_interactive_backport.md) — done (follow-ups #903-#905); a guard across an await needs the _connectEpoch generation, not readyState (a sample)
- [#881 boot-epoch](project_881_boot_epoch.md) — #881 SSE boot-epoch shipped #896: epoch-in-id design; browser reconnect gotchas need real browser
- [#884 /history single-flight](project_884_history_coalescing.md) — shipped PR #893; single-flight keyed (ws_id, limit) in make_history_handler; NO TTL cache
- [#890 clear_ui guard](project_890_clear_ui_guard.md) — SHIPPED PR #895 07-22; guard-before-wipe + transport-free heal (REST refetch, never reconnect)
- [#883 zero-budget truncation](project_883_zero_budget_truncation.md) — FIXED #892; 70-80% sticky band; floors + grace pool, zero budget triggers compaction; #891 open
- [#836 pool eviction](project_issue_836_pool_eviction_live_sessions.md) — fixed via PR #840; idle-TTL cools the transport but keeps the catalog; only explicit revoke drops it; static-path deadlock = #839
- [SSE "jank" campaign](project_sse_truncated_resync_hole.md) — 5 mechanisms shipped via #887/#888; gap-repair intent in one field at the connect chokepoint; `pytest -m e2e_recovery`

---
name: project_intent_verdict_lifecycle
description: "Intent verdicts missing after restart or judge cancel (fixed PR #646): cancel event is a pure abort signal, caller owns policy; one verdict per call."
metadata: 
  node_type: memory
  type: project
---

**Incident (2026-06-09):** 22-call parallel batch showed all LLM judge verdicts live; after restart+rehydrate only 3 remained. Branch `fix/intent-verdict-lifecycle`, PR #646 (6 commits).

**Lifecycle architecture (post-fix invariants):**
- The judge daemon (`judge.py _run_judge`) is sequential (max_workers=1, multi-turn tool-using completion per item) — a large batch outlives its approval gate by design.
- **Cancel event = pure abort signal; the CALLER owns firing policy** (`session.py`): approval-gate `finally` fires it only when `judge.cancel_on_approval=true`; generation supersede (next batch's `_execute_tools` top) and `close()` fire unconditionally. The judge loop must never second-guess the event against its own config — that asymmetry (unconditional poll-loop honor + unconditional gate fire) was what broke the documented run-to-completion default and made `on_intent_verdict`'s late-verdict machinery dead code.
- A fired event fast-forwards remaining items to `tier="llm_fallback"` verdicts (heuristic content; reused heuristic verdict_id → upgrade-in-place). Every call gets exactly one verdict — Smart Approvals and the advisory UI wait on the full set.
- **Superseded generation ≠ drop:** `_on_verdict` routes stale-generation verdicts to `SessionUIBase.on_superseded_intent_verdict` (duck-typed; CLI/eval UIs lack it → plain drop) — persists with `user_decision="superseded"`, touches NO live surface (Smart-Approvals stale-call_id safety preserved). `upsert_intent_verdict` excludes `user_decision` + `created` from on-conflict SET (load-bearing — protects recorded decisions).
- `user_decision` vocabulary: `pending`/`""`(legacy)/`approved`/`denied`/`timeout`/`policy`/`blanket`/`auto_approve_tools`/`smart_approval`/`superseded`.
- Bulk heuristic insert is `ON CONFLICT (verdict_id) DO NOTHING` (both backends) — the daemon can race a fallback UPSERT in ahead of the bulk write; plain INSERT used to abort the whole batch silently (best-effort try/except swallowed it).
- **Replay parity rule:** `/history` decoration ships EVERY stored verdict row incl. `risk_level="none"` (`build_verdict_payload` returns dict, never None). The client (`buildConvVerdict`) has no risk filter — any wire-layer suppression desyncs live vs rehydrate. Counter-example done right: output-guard chip suppresses "none" on BOTH sides.

**Accepted trade-offs (review-confirmed, deliberate):** run-to-completion default costs up to (N−1) judge completions post-approval contending with the next main turn on shared local backends (docs recommend `cancel_on_approval=true` there); replay payload grows ~80-400B per benign row (capped 10k rows).

**Diagnosis shortcut for "verdicts missing":** `SELECT tier, risk_level, user_decision, count(*) FROM intent_verdicts WHERE ws_id=? GROUP BY 1,2,3` — tier distribution separates real-LLM vs fallback vs heuristic; pre-fix histories will show the gap eras.

Related: [[project_smart_approvals]], [[project_early_paint_tool_calls]], [[project_inline_child_approvals]]

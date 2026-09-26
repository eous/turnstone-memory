---
name: project_smart_approvals
description: "Smart Approvals (PR #621) / approve_tools verdict work: LLM-verdict wait lives inside approve_tools after _reset_approval_cycle; batch is all-or-nothing."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-20T17:02:31.592Z
---

Smart Approvals (`judge.smart_approvals`, opt-in, default off): when the intent
judge's **LLM** verdict recommends `approve` with confidence ≥
`judge.confidence_threshold`, the tool auto-approves with no operator prompt.
`review`/`deny`, low-confidence, `llm_fallback` (errors/timeouts), and
judge-disabled all still go to a human. Built 2026-05-30 on `feat/smart-approvals`
off current main → **PR #621 (2026-05-30)**; one Copilot review
comment addressed (doc wording: floor blocks only explicit deny/critical);
first consumer of the judge verdict for *gating* (was purely advisory — see
[[project_inline_child_approvals]]). Extends [[project_three_facet_validation]]
(the calibration dataset was built "for future smart approval system").

**The decisions (user-chosen):**
- `judge.confidence_threshold` default bumped 0.7 → **0.95** (NOT 1.0 — I pushed
  back: confidence is the model's self-reported [0,1], rarely exactly 1.0, so 1.0
  would make the feature dormant by default). Repurposed: was only *logged*
  before, never gated anything — collateral-free to change meaning.
- Per-call gate = `tier=="llm" && recommendation=="approve" && confidence>=threshold` AND not
  heuristic-deny/critical (floor below). User declined a cap on the **LLM's own** `risk_level` (the
  spec was to be implemented exactly as written) — different axis from the floor.
- **BATCH-ATOMIC** (user-required, 2nd round): a parallel tool batch auto-approves only if EVERY
  pending call qualifies; one review/deny/low-conf/error/no-verdict/heuristic-danger holds the WHOLE
  batch for a human. The user rejected per-item approval as too permissive — parallel calls are one
  unit of intent (piecemeal approval lets a multi-step action through). `_apply_smart_approvals`
  returns `[]` (all approved) or `pending` unchanged (all held). The wait still waits for ALL
  verdicts first.
- **Heuristic floor:** never smart-approve a call the *deterministic* heuristic
  flagged `recommendation=="deny"` OR `risk_level=="critical"` (e.g. `rm -rf /`).
  Two framing corrections the user made — keep them straight:
  (1) Do NOT frame it as the output-guard "LLM never lowers a heuristic positive"
  invariant: the heuristic DEFAULT for an unmatched tool is `review`, and
  upgrading `review`→`approve` is the feature's whole point, so `review` is NOT a
  floor — only explicit deny/critical.
  (2) **Threat-model distinction (user, post-PR):** the intent judge's adversarial
  surface is much NARROWER than the output guard's. The output-guard judge ingests
  untrusted tool *output* (attacker-controllable → can target the judge), so its
  "never lower a deterministic finding" rule is load-bearing. The intent judge
  evaluates the *model's own proposed tool call* — grounded in the **user message**
  + conversation — so it's really checking intent-ALIGNMENT: does this call serve
  what the user asked? A "jailbreak" must come from the orchestrator model itself,
  not untrusted input (only indirect path: injected content in conversation history
  from a prior result — already screened by the output guard). Key reframing: a
  dangerous-but-*user-requested* action being approved is CORRECT, not a bypass —
  the gate guards against the model deviating from the user's intent, not against
  the user's own instructions; fooling the judge into approving what the user
  didn't want requires compromising the user's input channel (gate moot anyway).
  So the floor is mainly a backstop against the judge being *wrong*, not jailbroken.
  Don't expand it to `high` risk — low value, fires less. (In [[project_harness_compiler_dialect_stack]] terms: the output guard is the **disturbance-rejection margin** against an **adversarial environment E** — untrusted tool output, minimax drift — while the intent judge checks alignment on the trusted user channel, so its surface is narrow.)
- Oversized-batch guard: if `len(needed) > _LLM_VERDICT_CACHE_MAX` (50) the FIFO
  verdict cache can't hold them all → the wait would stall to its full budget, so
  hold the whole batch for a human.

**Load-bearing implementation constraints (easy to get wrong):**
- The LLM verdict is **async** (judge daemon → `on_intent_verdict` callback).
  Smart Approvals must WAIT for it. The wait MUST live **inside**
  `SessionUIBase.approve_tools`, *after* `_reset_approval_cycle()` — that reset
  clears `_llm_verdicts`, so a verdict delivered before approve_tools (e.g. if
  the wait were in `_evaluate_intent`) gets wiped from the reconnect-replay
  cache. Wait via `_await_llm_verdicts` on `self._verdict_cond` (a
  `threading.Condition` sharing `_ws_lock`), notified by `on_intent_verdict`.
- **Display gotcha (user-reported, 3rd round):** an auto-approved tool row must
  carry the LLM verdict as `judge_verdict`, NOT just `heuristic_verdict`. Both
  renderers pick `it.judge_verdict || it.heuristic_verdict` (coordinator.js
  `_pickBatchTier`/row render; app.js:~2297), and the auto-approve `tool_info`
  payload only had the heuristic → the row showed a cautious `review·medium·0.50
  ·heuristic` chip beside the green `✓ SMART_APPROVAL` pill (looks like a
  review-level call got auto-approved!). Fix: `_apply_smart_approvals` attaches
  `it["_llm_verdict"]` to each approved item and `_serialize_approval_items`
  emits it as `judge_verdict`. The LLM verdict (approve/low/llm) is the decision
  basis and must be what the row shows.
- **Other 3rd-round hardening (review pipeline found these):** (a) NaN confidence
  — `min/max` let NaN through as 1.0 and `json.loads` accepts NaN, so clamp via
  `math.isfinite` in BOTH `_verdict_confidence` and judge.py `_parse_verdict`.
  (b) Duplicate call_ids in one batch (some local models emit them;
  `_ensure_tool_call_ids` only fills MISSING) collapse in the `needed` set → one
  verdict clears two calls; guard `len(needed) != len(candidates) → hold batch`
  (placed pre-wait alongside the completeness check). (c) Audit-corruption race:
  `on_intent_verdict` does `notify_all()` BEFORE its `_pending_verdicts.append`
  (unlocked DB write in between), so a woken `_finalize_smart_verdicts` can miss
  the not-yet-appended verdict; it then lingers and a later `resolve_approval`
  re-stamps it. Guard: on_intent_verdict skips the append when the verdict
  already carries a non-"pending" `user_decision` (finalize stamps the shared
  cached dict). py↔JS reason lockstep is now pinned by a test.
- **Cross-turn stale-verdict gotcha (pre-push review, sec finding):** the judge
  daemon is fire-and-forget and `cancel_on_approval` defaults False, so a PRIOR
  turn's daemon keeps running and calling `on_intent_verdict` into the next turn.
  Verdicts are cached by `call_id` only, and `_ensure_tool_call_ids` fills just
  MISSING ids — so a model that REUSES a non-empty call_id across turns could
  have a stale prior `approve` satisfy the current batch's wait (within-batch
  dups are guarded; cross-turn was not). Fix: `_evaluate_intent` publishes its
  `cancel_event` as `self._judge_cancel_event` BEFORE spawning, and `_on_verdict`
  drops the verdict if `self._judge_cancel_event is not cancel_event` (a newer
  turn replaced it). Same-turn late delivery under `cancel_on_approval=False`
  still works (the session event still points at this round's event). Don't
  revert the "set before spawn" ordering — it closes the deliver-before-assign
  race for fast verdicts.
- **Streaming gotcha (regression found in 2nd round):** because the wait happens
  BEFORE the `approve_request` card is built, `on_intent_verdict` fans out the
  `intent_verdict` SSE events while no card exists → a live client drops them and
  the chip stays heuristic until reload (reconnect replay re-merges `_llm_verdicts`
  so it "works on reload"). Fix: `_replay_pending_verdicts(items)` re-emits the
  cached verdicts AFTER the card (gated on `smart_approvals_enabled`), restoring
  the normal `approve_request → intent_verdict` order. Same pattern as the coord
  reconnect replay. Also compute `judge_pending` as "any judged item still missing
  its LLM verdict" (false after the wait) to kill the spurious spinner/poll.
- `_pending_verdicts` is **reassigned** (clobbered) near the end of approve_tools;
  normally fine (judge slower than setup) but the wait makes early arrival the
  norm. Fix: merge `early_llm` (already-arrived LLM verdicts of still-pending
  calls) across the reassignment so `resolve_approval` can still stamp them.
- Smart-approved item's LLM verdict arrived *before* it was tagged auto-approved,
  so `on_intent_verdict` parked it in `_pending_verdicts` as "pending".
  `_finalize_smart_verdicts` pulls it out + stamps `user_decision="smart_approval"`
  (the existing `_auto_approve_reasons` pop trick doesn't help — it needs the
  reason recorded *before* the verdict, impossible here). Heuristic verdict is
  stamped for free by approve_tools' own persistence once the item is tagged.
- Judge fix (judge.py `_run_judge`): the `except`/`_ExecutorPoisonedError`
  branches now deliver a fallback via `_deliver_fallbacks` so EVERY call gets
  exactly one verdict — else the wait blocks to its full timeout on a silently-
  skipped item. (`_evaluate_single` already returns None on provider error.)

**Wiring:** `AutoApproveReason.SMART_APPROVAL = "smart_approval"` (added to `.ALL`
+ the JS `KNOWN_AUTO_APPROVE_REASONS` set in coordinator.js + server_schemas
`auto_approve_reason` doc). Config plumbed onto the UI in
`ChatSession._execute_tools` from the live `_judge_cfg`, guarded by
`isinstance(self.ui, SessionUIBase)` (CLI/eval UIs have their own approve_tools,
no smart gate). `smart_approval_wait_seconds = jc.timeout`. CLI does NOT wire
smart_approvals (consistent with its curated judge-config subset — no
output_guard_llm either); server/console do, via config_store + admin Judge tab
(bool auto-renders). Tests in test_session_ui_base.py (`_apply_smart_approvals`
matrix + approve_tools e2e via a `_SeedingUI` that re-delivers post-reset).

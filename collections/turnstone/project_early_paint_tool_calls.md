---
name: early-paint-pending-tool-calls-tool-pending
description: "Tool card paint or inline-card state CSS (#621): tool_pending paints before the judge, later events upgrade by call_id; out-specify .msg.ts-approval--inline."
metadata: 
  node_type: memory
  type: project
---

**Problem (#621 Smart Approvals regression):** `approve_tools` blocked the tool
card emit behind `_await_llm_verdicts` (Smart Approvals parks up to
`judge.timeout`=60s), so with smart approvals on, NOTHING about a committed tool
call painted until the judge ruled. User wanted it shown ASAP so an operator can
hit Stop in an emergency.

**Fix (Tier 2):** `SessionUIBase.approve_tools` now `_enqueue`s a `tool_pending`
event (serialized items) at the TOP, before policy lookup / the verdict wait /
the human gate. UI-paint only — no persistence/audit/verdict bookkeeping (those
stay on the resolved-state events so the gate accounting is untouched).
`_heuristic_verdict` is already attached (`_evaluate_intent` runs before the
gate), so the card paints with the heuristic verdict + judge-analysing spinner
from frame 1. The authoritative `tool_info` (auto) / `approve_request` (human) /
`tool_result` events that follow UPGRADE the same construct in place, keyed by
`call_id`; on reconnect the Last-Event-ID slice replays `tool_pending` → … and
reconstructs identically. New typed `ToolPendingEvent` in `sdk/events.py`.

**The asymmetry (the real work / why Tier 1 port was rejected):**
- **Coordinator** (`coordinator.js`) was ALREADY idempotent: `appendToolBatch`
  keys batches in a `toolRows` Map and morphs an existing batch
  (`--running→--pending`, `--running→--auto`). `tool_pending` reuses the
  `--running` placeholder (CSS-documented as "dispatched, no result yet, SSE
  upgrades it") + an `announce` flag that only swaps the kicker to "Evaluating";
  the auto-upgrade refreshes it back to "Running". ~3 small edits.
- **Interactive** (`app.js`) was NOT idempotent — `showInlineToolBlock` always
  `createElement`+`appendChild`. Added `announceToolBlock` (builds the shell,
  tracks `this.announcedBlockEl`, stamps `dataset.callIds`) + `_takeAnnouncedBlock`
  (matches by call_id set, else discards stale orphan) and made
  `showInlineToolBlock` reuse the shell (`replaceChildren()` rebuild so the auto
  badge + llm verdict render) instead of duplicating. Interactive is strictly
  serial (one approve cycle/turn) so a single tracked block suffices — no full Map.

**Key facts:** both frontends already routed late events (intent_verdict via
`updateVerdictBadge`, tool_result via `appendToolOutput`) by `call_id` DOM
queries — only block CREATION was non-idempotent. `IntentVerdict.to_dict()`
carries `call_id`, so the early heuristic badge is updatable in place.
Coordinator's announced state reuses `--running` (no new class).

**Designer review (this session) — what landed:**
- **CSS cascade TRAP (cost me a silent bug):** `.msg.ts-approval--inline`
  (style.css, specificity 0,2,0) sets `border-left-color: var(--cyan)` and
  *by design* "holds the inline card cyan regardless of state" — it overrides
  `.ts-approval.approved/.denied/.error` AND swallowed my bare
  `.ts-approval--announced` (0,1,0). Any NEW interactive inline-card state rail
  MUST out-specify it: `.msg.ts-approval--inline.ts-approval--announced` (0,3,0).
  Announced rail is full `--accent` (amber) dashed, NOT `--accent-dim` (15%
  alpha = invisible at 3px). Verified by headless-Chrome getComputedStyle, not
  source — source-reading is exactly what missed it. Guarded in test_app_js.py.
- **Screen-reader parity:** early paint announces POLITELY (not the assertive
  human-gate region) via dedicated off-screen `aria-live=polite` nodes —
  `toolAnnounce`/`_toolStatusEl` (app.js, mirrors `voiceAnnounce`) and
  `_announcePolite`/`#coord-sr-announcer-polite` (coordinator, mirrors
  `_announceAssertive`); the messages log is `aria-live=off` mid-stream so the
  appended shell alone is inaudible. Announced shell carries `aria-busy` until
  the upgrade clears it.
- **Deliberately NOT done** (user calls): HIGH-1 "may auto-approve" reframe
  (heuristic→LLM flip is ms in practice); coord `--running`/announced rail
  collision (downgraded to cosmetic); MED-1 replaceChildren "flicker" (phantom —
  the rebuild is synchronous so there's no intermediate paint).

**Tier 3 (NOT done, discussed):** extract a shared call_id state-machine both
UIs import (each keeps its own DOM/CSS — the divergence is `.coord-tool-*` vs
`.ts-approval-*` vocabulary, NOT a design-system version; see
[[project_design_system_v1]]). Only worth it if convergence itself is the goal;
the early-paint feature didn't justify it. The extracted core would be ~Tier-2's
logic. Interactive-only features a port must preserve: free-text approval
feedback, media/voice embeds, streaming tool-output chunks, y/n/a keyboard,
verdict glow, `__budget_override__` prompt.

Also folded in here: issue #562 — `normalizeRiskLevel()` chokepoint in `app.js`
funnels server `risk_level` through a `{low,medium,high,critical}` allowlist
before className/data-risk interpolation (3 sites: `updateVerdictBadge`,
`_buildOutputWarningEl`, `renderVerdictBadge`); landed alongside because the
early-paint path renders verdict badges (hygiene-first, [[feedback_pattern_propagation_sequencing]]).

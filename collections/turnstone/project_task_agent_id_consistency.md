---
name: project_task_agent_id_consistency
description: "task_agent sub-tool id aliasing or main-loop tool-id hygiene: sub-agent mint FIXED PR #820; fix main-loop ids at the ingest source, never on the wire."
metadata: 
  node_type: memory
  type: project
---

The task-agent path accreted **multiple, inconsistent ways to correlate "which
sub-tool call this is."** They should collapse to ONE globally-unique id scheme
used everywhere. Surfaced reviewing `feat/task-agent-turn-ir`.

## THROUGH-LINE (the maintainer's reframe, 2026-07-10) — this is harness-closure
The id mint (#820) + native-lane fidelity + backgrounding ([[project_background_task_agents]]) + durable sub-turn persistence (deferred #732) are NOT separate fixes — they are the increments of promoting `task_agent` from accreted hackery into a **proper 1-level recursive harness** ("closed under sub-harness"; the main harness applied to itself once, honest I/O at the boundary — [[project_task_agent_modernization]], [[project_harness_compiler_dialect_stack]]). They share a SPINE: **O3** (substitute one internal identity at the ingest source, threaded through native lane + mirror + result) is simultaneously the main-loop id fix, what lets the sub-harness carry its native lane (reasoning fidelity — today `_run_agent` DROPS `result.provider_blocks` though `create_completion` populates it), and what makes backgrounded sub-step ids collision-free. Fix identity once → three "separate" problems collapse. Full frame + Facet C in `docs/design/main-loop-native-lane-id-hygiene.md`.

## STATUS 2026-07-10 — sub-agent half FIXED (PR #820), main-loop half designed
- **PR #820** (`fix/task-agent-subtool-ids`): sub-tool ids now
  minted `{parent}::r{run}s{step}::{provider_id}` at the single `_run_agent`
  rewrite (run tag lock-allocated; step tag per-run) → session-unique across
  turns AND runs (reused parent id no longer aliases). One id keys registry /
  error-flags / DOM / recall / cancel-ledger. **This mint is the REAL, verified
  fix** (observed DOM/recall aliasing, red-tested). FIFO pairing kept for
  un-minted input.
- **CORRECTION (the maintainer, 2026-07-10): the "wire-safety" half was built on an
  UNVERIFIED premise.** Round-1 review claimed commercial Anthropic rejects
  tool ids outside `^[a-zA-Z0-9_-]+$` and api.openai.com caps `tool_call_id` at
  40 chars, so I added `lowering.legalize_tool_call_ids` (`::` → `tid_<sha1-32>`)
  + `sanitize_tool_call_arguments` at the agent seam and a CHANGELOG claim of a
  "pre-existing 400". **The OLD format was ALSO `{parent}::{id}` (contains `::`)
  and Anthropic agents worked reliably** → the charset rejection does NOT hit the
  real deployment (anthropic-COMPATIBLE vLLM `/v1/messages`, `_compat` path,
  lenient + `thinking_mode="none"`). No charset/length constraint is asserted
  anywhere in-tree; the "facts" were review-agent API reasoning I never verified.
  LESSON: a review agent's reasoning about an external API is a HYPOTHESIS, not
  a fact — verify against real behavior / in-tree evidence before writing it
  into a CHANGELOG. [[feedback_sdk_boundary_testing]] (new bullet
  `review_claims_are_hypotheses`).
- **DISPOSITION (the maintainer chose to keep both and reframe the claims, 2026-07-10):** legalize +
  sanitize KEPT as defensive hardening (cheap, deterministic, identity-preserving); every "provider
  X rejects/400s" claim reframed to honest defensive/hypothetical wording in the code comments,
  docstrings, CHANGELOG, PR body, and tests. Commit amended (false claim not worth keeping in
  history) + force-pushed with the maintainer's explicit OK — a sanctioned exception to the
  never-force-push-a-PR-branch rule [[feedback_git_workflow]]. New head `9ef43ecd`. The MINT remains
  the sole verified fix.
- **Main-loop / native-lane half = design doc** `docs/design/main-loop-native-lane-id-hygiene.md`
  (local). KEY CONSTRAINT (verified): the wire-only shortcut (run legalize on
  main-loop wire) is UNSAFE — it rewrites the top-level `tool_calls` mirror +
  `tool_result` but NOT the native `_provider_content` `tool_use` id
  (`_anthropic.py:615-620` sends native blocks verbatim), desyncing the
  native↔tool_calls mirror (P1, `normalize_native_for_save` core/storage/_utils.py:78,
  `test_native_tool_calls_mirror.py`). Correct fix is SOURCE-level at the
  ingest choke point `_ensure_tool_call_ids` (session.py:9205, called at :6999
  where native lane + mirror are both populated). Recommend O3 (substitute
  internal `t_*` ids at ingest — one scheme, legal everywhere, dissolves the
  `/model`-switch over-long-id case B) staged through O1 (de-collide only,
  ships observed sub-problem A). #820 is a forward-compatible subset — its mint
  folds in, its `legalize` call becomes a clean deletion.

**Two id levels in play:**
- Parent **task_agent call_id** (the parent's own tool-call id) — keys the
  frontend card (`_agentCards`), the recall stash (`_agent_trajectories`), the
  parent's `_report_tool_result`, and is passed as `parent_call_id`.
- **Sub-tool id**, namespaced `f"{parent_call_id}::{provider_id}"` in
  `_run_agent` — keys `_agent_children`, `_tool_error_flags`/`_tool_status`, the
  exec self-report, the nested DOM `data-call-id`, the recall step `id`, and the
  wire tool_call_id.

**~4 correlation mechanisms that don't agree:**
1. **Namespacing** (`parent::provider_id`) — de-collides ACROSS concurrent
   agents (the parent's 4-wide pool) but NOT across turns within one agent: a
   local server reusing `call_0` every turn yields the same namespaced id.
2. **FIFO-per-id pairing** (`_iter_agent_tool_results`, shared by recall's
   `_project_agent_steps` and `_cancel_ledger`) — works AROUND the cross-turn
   non-uniqueness by consuming a deque per id.
3. **Live DOM lookup** (`querySelector('.conv-row[data-call-id=…]')` in
   `_ensureAgentCard`/`_routeAgentItems`) — COLLAPSES cross-turn collisions onto
   one row (this is bug-3, deferred).
4. **Dict keying drift** — some maps key by the parent call_id (level A), some by
   the namespaced child id (level B); easy to mis-key when threading a new path.

**The seam:** the namespaced id isn't unique across turns, so the recall path
*papers over it* (FIFO) while the live card *collapses it* (bug-3) — the two
disagree on identical input.

**Cleanup goal:** make the sub-tool id GLOBALLY UNIQUE at the source — e.g.
`f"{parent_call_id}::{turn}::{provider_id}"` or a per-agent monotonic step
counter — and thread that ONE id consistently through registry / error-flags /
wire / DOM / recall. Then FIFO degrades to a plain dict lookup, the live DOM
lookup yields distinct rows (bug-3 dissolves), and there's one correlation
scheme instead of four. Verify against each provider's id-replay rules — tool
ids are opaque intra-request correlation tokens, validated only within a request
[[project_tool_naming_constraints]] — and keep the Turn/wire ids consistent
[[project_canonical_trajectory_redesign]]. Part of
[[project_task_agent_modernization]]; bug-3 is the entry point.

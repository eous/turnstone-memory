---
name: project_883_zero_budget_truncation
description: "#883 coordinator stall at zero tool-truncation budget (70-80% sticky band): FIXED #892 via floors, grace pool and capped compaction; #891 open."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-22T00:36:06.139Z
---

# #883 — zero-budget tool truncation stalled coordinators (2026-07-21)

Fixed via #892 (branch `fix/883-zero-budget-truncation`, single commit
amended per review round; converged R4+R5 0-correctness, suite 9706).
Field report (two users) verified on main: at
`_remaining_token_budget() == 0` the send-loop drain replaced every tool
result with `[Output truncated — N chars exceeded context budget]` — reads
as a successful-but-trimmed call. It destroyed `spawn_workstream`'s
~126-char `{"child_ws_id":...}` JSON, so the model could never issue
`wait_for_workstream` and silently yielded. Three aggravators: the UI got
`spawned <id>` via `_report_tool_result` BEFORE drain truncation (operator
sees health, model context is corrupted); the placeholder PERSISTED
(save_message), so the stall survived restarts and inspect_workstream;
the idle observer's ≤3 nudges each burned into the same zero wall.

## The load-bearing discovery: the sticky band

Budget zeroes at used > window − min(max_tokens, window/4) − 5%. With
max_tokens ≥ window/4 that is ~**70%** fullness — but compaction wasn't
owed until auto_compact_pct (**0.8** soft / 0.9 hard). Inside (70%, 80%):
every tool output zeroed, no compaction ever fired, and a stalled model
appends too little to cross the threshold → wedged indefinitely. The
docstrings claimed truncation and compaction "cannot disagree about
fullness" — true of the measure, false of the trigger points.

## Admission design (three doors, one floor constant, policy in the drain)

`_truncate_output` = MECHANISM only (floor_chars param, head+tail, honest
drop notice, empty-output fast path). The DRAIN owns POLICY:

- **Structural/error floor**: `_STRUCTURAL_FLOOR_TOOLS` (spawn_workstream,
  spawn_batch, wait_for_workstream, tasks) + `_tool_error_flags`-set
  results → per-result 2048-char floor (`_TRUNCATION_FLOOR_CHARS`),
  head+tail beyond. RULING at site (declined R3 security minor):
  deliberately NO aggregate cap — capping structural floors re-opens #883
  for wide fan-outs (every parallel spawn's handle needed or its child
  orphans); capping error floors masks failures behind a success-leaning
  notice → blind re-runs (the [[feedback_no_silent_refusals]] / #865/#866
  family). Backstop = pre-send `_over_hard` + ctx-overflow
  compact-and-retry; worst case is one extra compaction round-trip.
- **Per-batch grace pool** (`_ZERO_BUDGET_VERBATIM_POOL_CHARS` = 2×floor):
  funds verbatim admission of small NON-structural results (denials,
  bg-bash acks) by setting their own length as floor. Exists because an
  unconditioned small-pass let N small results collectively bypass the
  per-output bookkeeping (R2 correctness finding).
- **Honest drop notice** for the rest: "call ran, output dropped, compact
  to recover" — NEVER "may have executed": the drain holds the receipt, and
  fabricating uncertainty is as dishonest as fabricating success
  (HYPOTHESIS effect-record rule; caught at design time by the
  [[project_harness_hypothesis_doc]] check).

**Band fix**: zero truncation budget itself triggers the mid-turn compact
(`auto=True, preserve_tail=1`, NO threshold_pct — same never-fabricate-a-
threshold rule as the ctx-overflow retry). Bounded by a SEND-SCOPED attempt
counter (`_ZERO_BUDGET_COMPACT_CAP_PER_SEND` = 2): productive attempts
increment, an unproductive one (budget still ≤0 after) jumps to cap —
covers the marginal-recovery thrash regime where post-compact fixed
overhead (system + tool defs + summary) hovers just under the zero line.
Counter is a call-frame LOCAL, not instance state: generation-swap returns
inside the loop would skip any end-of-send clear.

## Review campaign (convergence-methodology data point)

Unprimed 4-finder rounds on the amended commit: R1 = 1 major perf
(per-batch compact re-fire; boolean latch was loop-local) + 3 quality
minors; R2 = 1 minor correctness (pool gap) + perf minor (marginal thrash)
+ quality minor; R3 = 1 minor correctness (empty-output false notice) +
declined security minor + 2 quality minors. Pattern held: **each round's
correctness finding lived in the previous round's fix code**, and each was
closed by seam re-derivation (boolean latch → capped counter; unconditioned
small-pass → explicit pool; special-case → universal empty guard), not
guard patches. At-site ruling comments foreclosed re-finds (R4 security
read the uncapped-floor ruling and declined to report it). A parity test
pins `_STRUCTURAL_FLOOR_TOOLS ⊆ COORDINATOR_TOOLS` names so set/catalog
drift fails CI instead of silently dropping a floor.

## Deferred / follow-ups

- **#891**: bg-bash spawn acks (shell_id handle) ride the grace pool only —
  a name-keyed floor can't distinguish fg/bg "bash". Close via arg
  inspection or exec-side marking if the drain/ack/pool is ever touched.
- **Full-receipt preservation** (content-addressed originals, HYPOTHESIS
  destructive-compaction note) deliberately NOT built — recovery for
  read-only calls is re-run-after-compacting; stated in the
  `_truncate_output` docstring.
- The HYPOTHESIS.md pre-implementation check earned its keep and is worth
  repeating for session-engine work: π-sufficiency (C1 falsifier),
  control-determining-state-crosses-verbatim (compaction discipline), and
  daemon renewal structure mapped 1:1 onto the three fix parts and caught
  a wording error before implementation.

Anchors (will drift): turnstone/core/session.py — `_truncate_output`,
constants block near `_REPEAT_EXEMPT_TOOLS` (~472-520), drain in the send
loop (compact trigger + floor/pool wiring), coordinator dispatch back-
pointer comment; tests/test_tool_truncation.py::TestZeroBudgetDrain.
Related: [[project_sse_truncated_resync_hole]] (the adjacent stall family —
stream/render gaps vs this context-budget class).

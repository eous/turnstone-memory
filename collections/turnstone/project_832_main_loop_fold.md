---
name: project-832-main-loop-fold
description: "Main loop folded onto model_turn (#832, PR #984 merged 2026-08-06): mirror law covers content only; inline think-tag scan is a fallback; residuals in #979."
metadata: 
  node_type: memory
  type: project
  modified: 2026-08-06T10:59:09.566Z
---

## Current state (2026-09-05 header)

- Status: MERGED to main 2026-08-06 by rebase-merge (PR #984 "Fold the main streaming loop onto model_turn (#832)", 17 commits; branch SHAs do not appear on main). The PR ADVANCES #832 and does not close it — closing #979 (the ~30-site provider-handle-holding refactor) closes #832; #980, #981, #982, #983 also filed.
- Follow-ups SHIPPED on `fix/832-followups` (5 commits, suite 10,556): `_generation_superseded` supersession refactor, wire-prep error hygiene, reasoning-parser capability tile.
- Post-merge rulings (the maintainer 2026-08-06): the mirror law covers CONTENT only — the reasoning channel diverges by construction; the ThinkTagSplitter inline scan is a FALLBACK for servers without a reasoning parser, and a `reasoning_delta` should retire it for that stream rather than race it; the drain's re-split cost was MEASURED (16 µs on 8 KB, 73 µs on 40 KB) — do not re-litigate.
- Durable rules: never write review-round / streak / model-name framing into commits or design docs; the `_superseded` duplication is load-bearing (each caller must read at call time); console capability tiles coerce via the `_capBool` spelling table, never bare `!!`; fix a leaking exception's own message, not one consumer.
- Campaign docs are LOCAL: docs/design/832-main-loop-model-turn.md (D1–D13; the D12 table is the ruled-delta registry) and docs/design/832-dataflow-map.md — read both before touching this seam.
- Open for the maintainer (08-06): their main checkout's branch ref was stale at the pre-rewrite 313ef308 with local pyproject/uv.lock edits — park them, then reset to origin/fix/832-main-loop-model-turn.

---

#832 (main loop onto `model_turn`, sever ChatSession from providers) — the maintainer greenlit
2026-08-05, asking for an excellent result rather than a merely adequate one. Campaign docs are
LOCAL: `docs/design/832-main-loop-model-turn.md` (THE design: D1-D13 decisions, D12 behavior-delta
table with the maintainer's rulings, gap-check reconciliation, hold-the-line block, S/M catalog) and
`docs/design/832-dataflow-map.md` (V1-V16/R1-R12/OE1-OE12). Read BOTH before touching the branch.

**Branch state**: `fix/832-main-loop-model-turn` in worktree
`<worktree>`, rebased onto `70165807` (= main with PR
#978 merged). Commits: `490efbd3` model_turn streaming surface (on_chunk tee +
drain-retry disable = 3rd policy carve-out, prepare_wire, deferred_names,
wire_msgs on result, runtime re-exports incl. merge_usage); `7a3b24c5` parity
harness (tests/_parity_832.py + test_832_parity.py, 13 scenario baselines in
tests/data/parity_832/ captured at session.py≡main, synth-id masked stable).

**Phase 3 (NEXT)**: session.py wrapper rewrite. Inner
`_model_turn_with_retry(lane)` = `_try_stream` analogue (per-lane _MAX_RETRIES);
outer fallback walk = `_create_stream_with_retry` analogue (health once per
ladder); `_CancelRef` gains `on_first_append` hook (fires once, not superseded)
carrying THREE duties: health record_success, creation-vs-midstream classifier
arming, `_last_usage`/`_assistant_pending_tokens` resets. Per-ATTEMPT
generation-scoped refs (never per-send — classifier breaks, gap-check M4).
Armed death on ANY lane incl. fallback → mid-stream ladder, never next-alias
(G1). Callback body = map V11 grid; splitter gate PORT: #978's handoff-register
read + `_stream_attempt` caps param → `ThinkTagSplitter(_flush_text,
scan_tags=not lane.capabilities.server_parses_reasoning)` (register deleted per
V9). Knob parity: `replace(lane, temperature=self.temperature,
reasoning_effort=self.reasoning_effort or None)` (G3 — never let lane rungs
newly apply). send() consumes result.turn natively (fixes fallback producer bug
+ fork producer="" asymmetry). Deletions: _try_stream,
_create_stream_with_retry, _try_fallback, _stream_attempt,
_active_stream_provider, session _ensure_tool_call_ids (port
tests/test_mcp_client.py:781,:794), gen-0 shared _cancel_ref (keep
_cancel_stream lifecycle + send-finally None). D12 rulings: footer
adopt-drain (callback emits trailing info as content per drain's conditional
fold, no on_info double-render), strict finish gate adopt, length-drop
preserve (drop result.tool_calls + rebuild turn via
finalize_provider_blocks(has_tool_calls=False) — NO new ModelTurnResult field
needed, G2a).

**Phase 3 DONE** (`198ebeb1` + ports): wrapper live; parity 13/13 (transforms
cite D12 rows; harness caught 2 real bugs — carry-flush hole, footer splice).
**Triage DONE** (docs/design/832-test-triage-ledger.md): 17 files via 5 agent
chunks (the maintainer's tiering: Sonnet mechanical / Opus directed / Fable K1) —
~1,300 green, zero product findings; eous pins landed in test_cancel
(pre-dispatch no-mint; orphan no-reissue; on_first_append hook pins); NEW
named D12 delta at triage: orphan-exit class (superseded death → silent
cancelled send-exit, never a raw exception into the thread runner).
`tests/_parity_832.arm_session` = THE armed multi-stream session fake
(exception elements = creation-phase failures; QUIETS TITLE LANE — a
provider-level fake otherwise gets its one-shot script eaten by title-gen,
the trap every port hit).

**IMPLEMENTATION COMPLETE 2026-08-05**: branch @ `612da53e`, 8 commits over
`70165807`. Full suite **10651 passed/10 skipped**; **goldens untouched**
(zero-delta prediction HELD — no regen needed); docs sweep + per-adapter
eager-append tripwires done. Follow-ups FILED: **#979** lane-holding refactor
(V7 ~30 sites), **#980** delete is_first, **#981** commit→save /history
window. Parity harness caught 2 real bugs mid-fold (carry-flush,
footer-splice) — both fixed + pinned.

**REVIEW ROUND 1 DONE 2026-08-05** (36 agents): 32
verified → 15 reported + **5 cap-dropped mined from the synthesize prompt**
(the maintainer's standing rule — mine every capped round;
[[reference_code_review_workflow_recovery]]). NOT a zero round. All 20
items FIXED on detached HEAD in the worktree (main checkout parked on the
branch @ 612da53e for the maintainer's compose stack; ff the branch only on their
go). The one real fold regression: consumer kept the dead attempt's ARMED
ref through the re-create window → fixed with `end_attempt()` (ladder
pronounces attempt dead at partial-capture; single `_reset_attempt`
initializer; lane survives for the serving-lane predicate). Also:
WirePreparationError typed at model_turn (wire-prep faults out of health +
fallback walks + own fatal branch); auth/wire-prep exempted from the
re-issue last-death mask; saw-chunk classifier fallback (never-arming
adapter death stays mid-stream); parity recapture signature-adaptive +
garbage-capture guard; debug-dump-per-invocation KEPT as named D12 row;
`lane_scans_inline_reasoning` = single #978 gate spelling; shared
TRAILING_INFO_SEPARATOR/folds_trailing_info fold pair; config_store
dropped from _build_main_lane (G3 pinned); dead delegates deleted
(_ensure_tool_call_ids, _finalize_provider_blocks); streaming fakes MOVED
to tests/_session_helpers.py (12 files re-pointed; _armed_provider dup
deleted); committed pins now restate rulings IN FULL (no local-doc D12
citations in tracked files); architecture.md circuit-breaker FICTION
replaced with real passive-tracker story. New pins mutation-probed (4/4
fail on pre-fix code). Round-1 section + 2 new D12 rows in the design doc.

**LIVE-REVIEW ROUND 2026-08-05**: the maintainer dogfooded a turnstone-hosted
review of the branch (262-step task agent; its report got TAG-MANGLED in
transit — live proof of the in-band `<think>` vocabulary collision; agent
hex-armored its probes to survive). It found a real CRITICAL both my
36-agent round AND the parity grid missed: consumer flipped
`splitter.in_think=True` at a reasoning_delta with a content tail still
pending → tail relabeled as reasoning on flush → display lost text the
drain-committed turn kept (worst case: short answer + footer displayed as
NOTHING). Pre-fold BOTH lanes lost it (consistent-lossy); the fold fixed
commit only → divergence. FIXED: `ThinkTagSplitter.close_run()` (drain's
boundary rule mirrored; only `partial_tag_tail` carries) + HIGH fix:
partial_tag_tail proper-prefix (complete `<reasoning>`/`<think>`
self-matched via startswith). Pins: `TestDisplayCommitMirror` in
test_832_parity (display≡commit LAW, no baselines — 6 interleave
scenarios), TestPartialTagTail/TestCloseRun + 3 CASES rows in
test_think_tag_split. Mutation-probed. Lesson recorded: parity grids that
script dimensions separately never see cross-lane interleave — round 2
scope must name the combination dimension explicitly.

**ROUND 2 DONE 2026-08-05**: 19 verified → 10 reported,
ZERO cap-dropped. NOT a zero round — the mandated interleave angle found
the two residual holes in 313ef308's boundary fix: close_run was GATED on
not-in_think (open inline think at boundary → CoT relabeled as displayed
ANSWER) and the carry parked in splitter.pending was re-read under
flipped state. Fix @ **687b253a**: close_run unconditional + RETURNS the
tail; consumer owns `_boundary_carry` (state-immune, drain's
separate-variable design: re-fed on content resume, content-flushed at
tool/finish/cancel, in partial_content); footer HELD + folded once at
finish_stream (drain's post-loop fold); fallback UI line class-name-only
(credential leak); never-armed Stop writes NO row (pre-fold restored);
parity runner zeroes backoff (was sleeping 3.2s/run); factories wrap
shared make_session; ArmedHandle sentinel; single tool_calls binding.
6 new mirror rows + redaction + no-row pins, all 5 fixes
mutation-probed. Suite 10,692/10. **cwd TRAP hit twice**: bash `cd`
persists — round-2 test edits landed in MAIN checkout, repaired via
patch→worktree + `git checkout -- tests/` in main; `uv run` in main also
REBUILT main's .venv (63 pkgs — likely extras-pruned; the maintainer's local
pyproject/uv.lock edits untouched, venv state NOT restored — FLAG to
The maintainer). Branch pointer still at 313ef308 in main; worktree detached at
687b253a — ff again at next sync point.

**COMMENT PASS DONE** @ 43e4f5ac (Opus agent, −134 prose lines, suite
byte-identical 10,692). **ROUND 3 DONE** (UNPRIMED
high, neutral target): 6 cand → 5 reported + 1 refuted-as-ruled (the
workflow matched the dup-sanitize to D1's ruling unprompted — registry
works). NOT zero. Fixed @ **f2fd33a5**: h1 prepare_wire now receives the
SERVING lane (model_turn `prepare_wire(wire, lane)` signature;
`_prepare_wire_messages(caps=...)` override; fallback folds with its own
caps — D12 addendum row 2, improvement over pre-fold primary-everywhere);
h2 on_stream_armed generation-gates itself (orphan TOCTOU arm duties);
h3 overflow tests parametrized; h4 arm_session per-create ArmedHandle
(`provider.handles`); h5 dup-sanitize SKIPPED as ruled (D1) — perf rider
commented on #979. 3 mutation probes green. Suite **10,695/10**.

**ROUND 4 DONE**: 7/7 verified, 1 correctness — MY
round-3 × round-2 interaction: lane-variant prepare invalidated the
WirePreparationError walk-abort premise. Fixed @ **cb142506**: prep
faults keep no-health on EVERY lane but CONTINUE the walk (primary's
fault enters it; a fallback's yields to the next alias); fatal message
dropped the no-fallback claim; `_SELF_SURFACING_ERRORS` mask constant
(walk arms stay per-class: auth aborts, prep continues);
`caps_scan_inline_reasoning` sibling (title peel now uses it — 3rd
spelling retired); `provider_shell()` under all three streaming fakes;
ui_base comment re-pointed; removesuffix; docstring re-flow. Old T4
pin's fb_spy.assert_not_called() INVERTED with the ruling. 2 mutation
probes green. Suite **10,697/10**.

**ROUND 5 DONE** — run DIED mid-verify (5 verifiers + synthesize failed).
Recovered by journal-mining all 7 finder candidates and hand-verifying
the 5 orphans ([[reference_code_review_workflow_recovery]] — the
crash-recovery path, first real use). Finders produced ZERO correctness
claims; the one real defect came from a *cleanup*-categorized claim:
`on_stream_armed`'s round-3 gate used a bare `!=` where the file scopes
with `if gen and ...` — ref and hook disagreed about generation 0
(ref fires, hook refuses). PROBE-CONFIRMED stale usage + lost health on
a direct `_stream_response(0)` after a send. Fixed with a consumer-side
`_superseded()` used by BOTH on_stream_armed and record_cancelled_partial.
Also: `_speaks_for_backend`/`_NON_BACKEND_ERRORS`; finalize-arm hoist;
14 hand-rolled FakeChunk dataclasses in test_cancel → real StreamChunk.
SKIPPED-as-ruled: `_saw_chunk` fallback (round-1 ruling + pinned +
probed) and dup-sanitize (D1, 3rd sighting). Suite **10,698/10**.

**Artifact guidance (2026-08-05):** describe the behavior changed in commit subjects and public
descriptions. Keep review-round bookkeeping and session details in local working notes. See
[[feedback_artifact_cleanliness]].

**PR FRAMING RULED 2026-08-05: ADVANCES #832, does NOT close it** (the maintainer: acceptable
provided every residual has a tracking issue). MET: 0 provider-module imports, create_streaming one
caller module, model_turn sole plant-call surface. UNMET (the "no provider-facing code" half): 3
Protocol attribute reads (compaction `.provider_name` stamp ~9939; compaction `_stop_retrying(...,
self._provider)` → `retryable_error_names` ~9134/6408; fatal-formatter primary label ~5875), 4
`type(self._provider).__name__` labels in `resume()`, ~30-site handle-holding. ALL enumerated in a
#979 comment with closure criterion (`grep "self\._provider" session.py` empty ⇒ #832's last clause
met). **#979 closing closes #832.** PR wording rule: never say "session still has provider calls"
(overstates — a grep finds 3 attribute reads and the claim reads sloppy); say the session no longer
CALLS the Protocol on the plant path, it still HOLDS handles (#979).

**TARGETED SINGLE-AGENT REVIEW of 363c7cc4 DONE** (code-reviewer agent,
not a workflow — lightweight, and it worked well): **approve, nothing
blocking**. It probed instead of reading: mutation controls with the old
predicate, an AST pairing of all 24 converted FakeChunk sites, and a
135-construction census proving only ONE gen-0-on-claimed-session
consumer exists in the corpus (my own new pin). Two findings, both
fixed @ **f5e4c697**:
1. I'd re-scoped 2 of 6 gates and left 4 on bare `!=` → one function
   gave OPPOSITE supersession verdicts for one shape (Stop finalized,
   Ctrl-C didn't). Hoisted `_generation_superseded(session, gen)` as THE
   predicate; all 5 remaining sites route through it. Pinned by
   `TestSupersessionVerdictAgreement` (both directions) + probed ×2.
2. **`_superseded` duplication is LOAD-BEARING — never collapse it.**
   Probed: a consumer delegating to `self.ref._superseded()` inherits
   the ref's STALE read and fires arm duties for a genuine orphan. Each
   caller MUST do its own read; the shared free function is right
   precisely because it reads at call time. Also
   `record_cancelled_partial` runs after `end_attempt()` nulls the ref.
Suite **10,701/10**. Tip now `f5e4c697`.

**TEST-PREMISE LESSON**: two drafts of the orphan pin were wrong before
the third stuck — a superseded generation NEVER reaches the Ctrl-C arm
(ref reads superseded → model_turn refuses dispatch → ladder converts to
cancel). Pin now asserts that stronger invariant with
`create_streaming.assert_not_called()`. When a pin won't go green,
suspect the premise before the code.

**COVERAGE AUDIT 2026-08-06** (the maintainer suspected the two arms lacked good test coverage —
they was right; MEASURED with `pytest --cov`, don't guess). Before: `except Exception`'s
orphan-guard `raise` was **line-UNCOVERED**; the Ctrl-C arm was line-covered but **branch-PARTIAL**
(superseded side never taken). Structural reason, not neglect: `_model_turn_with_retry` re-checks
the generation BEFORE classifying a death, so every deterministic path delivers an orphan as
`GenerationCancelled` — these arms only fire in the sub-statement race where force-cancel lands
after that check. No scripted stream reaches them; must simulate at the `_model_turn_with_fallback`
seam (arm the consumer, bump `_generation`, raise). `TestOrphanGuardsBelowTheLadder` closes both +
the live counterpart; probed ×3. Now full line+branch coverage on all three arms. Fix @
**83a5e08f**; suite **10,704/10**. **METHOD NOTE: partial-branch reports > line-coverage numbers —
both defects of the last two rounds lived in branches executed one way only.** **CAMPAIGN COMPLETE —
PR OPENED 2026-08-06** (per [[feedback_no_pr_status_in_memories]] no status tracked here): branch
pushed to origin, PR **#984** off base `70165807`, 17 commits / 44 files / +4060−2228, titled "Fold
the main streaming loop onto model_turn (#832)". Body says ADVANCES not closes, names the residue →
#979, and release-notes the user-visible ruled deltas (footer-into-content is the big one:
web-controlled text now reaches storage/tsvector/context/ export). Verified clean of attribution +
homage-naming before opening (the one "anthropic" hit is the provider MODULE name — legitimate).
main had moved 1 commit (helm-only, #977) — zero overlap, no rebase.

**Follow-up references:** #983 and #982 track additional work; #979 also carries the
prepare-composition performance follow-up. Verify the public issues before acting on this historical
record.

**MERGED to main 2026-08-06** — rebase-merge, so branch SHAs do NOT appear
on main (`f15e53dd`/`df8a374c`/`50e080c1` == the old tip three). All 18
checks green.

**POST-MERGE SELF-HOSTED REVIEW** (the maintainer ran a turnstone review of the
fold ON the folded session — the smoke test). 6 findings, all hand-verified
against merged HEAD. Durable outcomes:

1. **THE MIRROR LAW COVERS CONTENT ONLY — the reasoning channel diverges by
   construction.** PROBE-CONFIRMED: script `<think>inline-A` /
   reasoning_delta `SERVER-R` / `inline-B</think>Answer.` → displayed
   `'inline-A SERVER-R '`, committed `'SERVER-R \n\ninline-A '`. Structural,
   not a tail artifact: the consumer emits inline reasoning EAGERLY as it
   feeds, while the drain segregates (`reasoning_parts` at arrival, then
   `extracted` appended after a `\n\n`), so ANY inline reasoning shown before
   a server delta commits after it. **Reachable by DEFAULT**, not exotic:
   `server_parses_reasoning` defaults False (scan ON) and
   `_openai_chat.py:396` maps `reasoning_content`→`reasoning_delta`, i.e. any
   vLLM/llama.cpp reasoning lane without an explicit capability declaration.
   Live-only cosmetic (replay reorders the CoT; content is unaffected).
   **RULED by the maintainer 2026-08-06: the ThinkTagSplitter inline scan is a
   FALLBACK path — for inference servers with no reasoning parser, or
   misconfigured instances — NOT a co-equal channel.** So the fix is NOT
   to teach the drain to interleave both sources (that would elevate the
   fallback and complicate a drain shared by judges/title/compaction).
   A `reasoning_delta` is runtime EVIDENCE that the server segregates
   reasoning — true for all three producers (`_openai_chat` from
   `reasoning_content`, `_anthropic` native thinking, `_openai_responses`
   native items) — so it should RETIRE the fallback for that stream
   rather than race it. In the drain that is one line
   (`scan_tags=scan_inline_reasoning and not reasoning_parts` at the
   post-loop split; the `tag_carry` shuffle only moves chars BETWEEN
   segments that are then joined, so it stays order-neutral when
   unscanned). Consumer mirrors it by stopping the scan at the Path-1
   arm. Residual edge: content already emitted BEFORE the first
   reasoning_delta can't be recalled, so a server that leaks raw tags
   AND emits reasoning_content shows visible `<think>` — a deliberate
   diagnostic signal that the instance is misconfigured, preferred over
   a silent divergence. Extend the mirror law to reasoning when fixing.
2. **PERF ruling — MEASURED, do not re-litigate.** The drain's re-split
   (the "3× scan" objection to making the drain canonical) costs **16 µs on
   a typical 8 KB answer, 73 µs at 40 KB**; the consumer's own per-chunk
   feed, which the PRE-fold path also paid, is **4× costlier**. Immaterial
   against a multi-second stream, and reversing it would undo exactly the
   single-source-of-truth finding #1 shows we need MORE of. `_content_parts`
   is load-bearing too (citations-fold gate + partial promotion), not
   redundant buffering.
3. `_generation_superseded` unified the FOLD's sites but two PRE-existing
   inline copies survive: `_check_cancelled` (~6558, from #202) and
   `_compaction_event` (~9562, compaction-lifecycle). Same formula, three
   spellings — route both through the helper.

**FOLLOW-UPS SHIPPED** (branch `fix/832-followups`, 5 commits, suite 10,556):
the supersession refactor, wire-prep error hygiene, and the reasoning-parser
tile. Two durable gotchas surfaced there:

- **Console capability tiles coerce with bare `!!`; the backend uses a
  spelling table.** `apply_capability_overrides` maps `"false"/"no"/"off"/
  "0"/""` → False and DROPS unrecognized strings (field keeps its default);
  the admin modal's tile lift used `!!capsObj[k]`, so a hand-typed string
  `"false"` rendered the tile CHECKED and persisted boolean `true` on the
  next save — silent capability inversion on a routine edit. Fixed with a
  `_capBool` mirror + node-executed test generated FROM the Python table.
  **Applied to all 12 pre-existing tiles, not just the new key** — check
  this whenever adding one.
- **A wrapper exception's own message is a live surface.** I called the
  "sanitize the `WirePreparationError` message" remedy inert because
  `_format_backend_error` renders `__cause__` — true for that function, and
  wrong overall: `model_turn` built the wrapper as
  `WirePreparationError(str(prep_err))`, and `server.py`'s interactive
  retry arm renders `str(exc)` straight into the dashboard SSE. **Fix the
  exception, not the one consumer** — that closes every caller that
  stringifies it. Ruling: when judging a leak remedy, enumerate `str(exc)`
  callers, not just the formatter.

**REVIEW-OF-A-REVIEW LESSON**: two of the six findings cited code that does
not exist or prescribed an inert remedy — a sweep item leaned on
`_create_stream_with_retry`'s docstring (that helper was DELETED by the
fold), and the error-hygiene item told us to sanitize the
`WirePreparationError` message when `_format_backend_error` renders
`__cause__` instead, so the proposed fix would have changed nothing. Verify
the cited symbol still exists AND that the remedy touches the live path
before accepting any finding — including from our own reviewer.
([[feedback_measure_before_accepting_a_finding]])

**Standing rules for this campaign**: [[feedback_pre17_era_presumption]]
(unexplained pre-1.7 behavior = improve+name, never preserve+pin);
parity pins protect rulings, not fossils; behavior deltas ship only via the
D12 table. HYPOTHESIS.md grounding section lives in the design doc (one
readout R at one site; callback owns UI state only).

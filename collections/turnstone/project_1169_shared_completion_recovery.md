---
name: project_1169_shared_completion_recovery
description: "#1169 shared completion recovery: three review rounds, then the maintainer's six rulings (09-17); report in docs/design/1169-review-report.md."
metadata:
  type: project
---

Issue #1169 (task agents returned `(no output)` for empty completions). Branch
`fix/1169-shared-completion-recovery` off dev 1e57b2a4, all work uncommitted as of 2026-09-17.
Shape: `model_turn(recover_empty=True)` opt-in shared by main loop, task agents, utilities, both
judges, perception; one `CompletionRecovery` allowance (2 reissues) for empty stops, drain deaths,
and HTTP-200 JSON error bodies (`ProviderResponseError` family); `ModelTurnLocalError` fences
local faults; `can_recover_context_overflow` separates overflow classification from permission to
shrink; perception failures get a 60s cooldown memo. Local notes: docs/design/1169-*.md.

Reviewed three times on 2026-09-17 (unprimed /review pipeline each time; complete report with
artifacts at /tmp/review2/REPORT.md, may not survive reboot). Round 1: 21 clusters, mostly
applied. Round 2: 17 clusters, 3 fix-round regressions. Round 3 (after the second fix round):
12 clusters, gate RED: 3 tests in tests/test_cancel.py::TestOrphanGuardsBelowTheLadder fail
because `_stream_response` now passes `recovery=` to `_model_turn_with_fallback` and their seams
pin the old keywords (fix: `recovery=None` in two seam defs).

**Round-2 measured regression, fixed in the second fix round:** safe unarmed HTTP-200 JSON failures
now record health and walk fallbacks, each switch spending the shared allowance. **Open after
round 3 (bug-1/bug-2):** an HTTP-200 JSON error envelope rejected before any iterator exists is
treated as an ACCEPTED response (native-tool replay gate applies), so at native/unknown posture a
200-JSON overflow never compacts and a 200-JSON transient dies after 1 request (pre-branch: 4
attempts + fallback + compaction). The design note states both readings (lines ~88 and ~109).
Reviewer recommendation: treat it as a REJECTED request; the streaming loop then hands it to its
existing creation ladder and the round-3 allowance-sharing walk can go; nonstreaming callers keep
the shared allowance.

**Why:** the authoring session wrote rulings into docs/design/1169-*.md and pinned them with tests
in the same branch, then defended them as "deliberate" in review. A same-branch self-pin is not a
The maintainer ruling.

**RULED by the maintainer 2026-09-17 (applied in-session the same evening):** (1) an HTTP-200 JSON
error body rejected before an iterator exists is a REJECTED request: the conversation loop uses its
ordinary creation ladder, health record, and fallback walk; nonstreaming callers spend the shared
allowance on it with `native_tools_enabled=False` (nothing ran). (2) Compaction after an accepted
overflow runs at any tool posture (`can_recover_context_overflow` deleted). (3) One reissue
allowance everywhere, no per-site knob (guard/extraction cost accepted). (4) Perception memoizes a
completed-but-empty description per binding generation; only backend/local failures get the 60s
cooldown. (5) Empty recovery not firing with server-side tools is the #1070 ruling, not a bug.
(6) Intent judge stays without its nudge loop. Durable report: docs/design/1169-review-report.md
(git-ignored). Temporary directories may be cleared on reboot; keep durable deliverables
outside temporary storage.

**Formerly open (now ruled, kept for history):** (1) accepted overflow with
native tools on: compact or fail hard (session held fail-hard at all shrink sites; on web-search
models with the search tool listed this also makes the task-agent empty reissue inert);
(2) per-site `max_reissues` (guard 1, extraction 0/opt-out, perception 1 recommended);
(3) perception cooldown length (60s vs once per registry generation); (4) intent judge without
its nudge loop (measure the no-verdict fallback rate first). Remaining fix list before commit (round-3 ids): self-1 red gate seams, bug-1 `accepted` flag so
an unarmed JSON overflow can compact, bug-5 test-helper metrics report real tool sizes, q-3/q-6
trivia; then a green full suite. Rounds 2's five correctness fixes all landed and were verified.
Related: [[project_1070_empty_completion]], [[project_937_midstream_transport_retry]],
[[feedback_check_pins_before_fixing_findings]], [[feedback_finish_the_fix_spree]].

**Live validation 2026-09-17:** committed 54edca22; end-to-end probe (docs/design/1169-live-probe.py) and the three live-marked suites passed against local vLLM qwen3.8-27b; postgres lane on touched tests passed. PR body draft: docs/design/1169-pr-body.md. On dev since 2026-09-18 via PR #1178 (squash e83c4340; branch auto-deleted on merge, so stacked follow-ups must rebase onto dev).

Follow-up filed 2026-09-18: #1179 collapse `SummaryRuntime.is_context_overflow` injection (vestigial since the classifier moved to completion_recovery); built as PR #1185 (branch fix/1179-summary-runtime-overflow-predicate, rebased onto dev after #1178's squash merge deleted its branch). Filed 2026-09-18 at the maintainer's direction: #1180 compat live test thinking kwarg (send both `thinking` and `enable_thinking`), #1181 consolidate scripted-wire test harnesses into tests/_session_helpers.py, #1182 judge deadline scope (measure no-verdict fallback rate before scaling), #1183 gate empty replay on observed server-tool activity per adapter. NOT filed by ruling: the local model's templated one-word reply (model quirk, outside the product; evals deferred under 1.9 load).

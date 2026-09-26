---
name: project_idle_tasks_nudge
description: "Coordinator idle nudges (#913): read docs/design/913-HANDOFF-fail-closed.md first; signal goes in the state machine (needs_user), bodies state observed facts."
metadata:
  node_type: memory
  type: project
  modified: 2026-07-30T04:41:38.441Z
---

Coordinator nudges for going idle with unfinished work. Branch
`feat/coord-idle-tasks-nudge`, PR #913 — READY FOR REVIEW as of
2026-07-29 (WIP dropped, Copilot threads resolved at the switch),
**merge still gated on eval numbers: the qwen + gemma legs of the
honest-instrument sweep** (the maintainer). Status belongs to gh, not here
([[feedback_no_pr_status_in_memories]]).

**READ FIRST ON RESUME: `docs/design/913-HANDOFF-fail-closed.md`** —
how to work with the maintainer on this branch, plus the fail-closed record:
a failed storage read silences BOTH nudges and charges neither cap,
LANDED `6231a61b` (2026-07-29) as a plan-then-commit split in
`_on_idle` (`load_task_envelope raise_on_read_failure`; both drain
predicates drop on a failed read — delivery is the fire; the spent
already-charged wake at drain is an accepted, recorded cost). Path
faults stay per-path — a generic raise is NOT a failed read.
**Never call a nudge wording "tuned"/settled/validated** — the body is
under active development, every past sweep measured an earlier draft
on an instrument being repaired, and that framing made the maintainer's
corrections look like they needed justifying. Answer their design
questions by checking the code, not by defending the current shape;
if an instruction is wrong say so in one line and implement the
corrected version rather than arguing it.

Then: `docs/design/913-final-review-findings.md`
(local, gitignored) — the complete 37-survivor verified review of the
whole branch, with the 16 cap-dropped findings tagged. It supersedes
the older HANDOFF for current state. Branch: remote @ `b8cd8661`
(the 4-commit flatten `52b9e562` + five fix commits), local +
`4e4b9067` (optimizer de-pin) UNPUSHED. **History stays AS IS
(the maintainer, 2026-07-29); any tidy is proposal-first — present the
commit list and wait — and pushes happen only on explicit,
per-instance instruction** (see [[feedback_git_workflow]], updated
same day). The technical design is summarized below; verify current source before
using this historical implementation record.

## The design question, and the answer that shaped everything

Phrasing alone is the weak lever: telling a model "only continue if you
weren't waiting on me" asks for the introspection it already failed.
The ruling: **put the signal in the state machine, not the prose.**
`tasks` gained `needs_user` (a decision only the human can make,
distinct from `blocked`) plus a `note`. The nudge asks a TYPED question
with a concrete call on every branch.

## Standing rulings (do not re-litigate without reading the findings file)

- **Bodies state OBSERVED FACTS only — and fabrication extends to
  ENTITY EXISTENCE (the maintainer, 2026-07-29, three rulings in one day).**
  (1) "You are idle." cut from the children header: delivery seams
  don't re-verify idleness, only children activity — assert only what
  the drain predicate verified. (2) The hedged children caveat ("may
  still be running or may have finished while you worked") replaced by
  per-state fact lines — hedging a state the read just returned is
  manufactured uncertainty; "while you worked" was manufactured
  context. (3) "may hold uncollected results" cut — "results" is a
  noun no read observed and "uncollected" implies a ledger nobody
  consulted; hedging an entity into existence with "may" is STILL
  fabrication. The test: every noun and every clause in a body must
  trace to a read or a tool-behaviour fact. A protection must be
  carried by an observed fact (the immediate wait), never by an
  invented object. I defended the "may" twice before the maintainer cut it —
  when they flag a fabrication, find the unobserved NOUN, not just the
  hedge word.

- **Counts body ADOPTED + provenance paragraph PRUNED (the maintainer,
  2026-07-29, on round-8 honest-instrument numbers).** counts_only
  matched/beat the values body on every childless cell (100/100/100/
  70~/100, zero forbidden); no_provenance was 100/0 on both cells and
  both models — the paragraph showed no isolated effect anywhere on
  the correct wire (the old "provenance carries the guard" conclusion
  was a wrong-wire artifact). New production body: counts line opener
  ("You still have N open tasks: X in_progress, Y pending") +
  conditional children caveat + the four typed branches. NO provenance
  para, no bullets, no "Open:". CAVEAT: the composition
  counts-without-provenance was never measured as one body — round 9's
  nudge arm confirms it by construction. Deletes: shown projections,
  display cap, asserted-set ids, bound_open_ids refusal (drain
  predicate becomes any-open-task-remains — still own-domain-only, the
  ruling's spirit), tasks card rows (card-honesty: card shows the
  counts the model got; pane keeps rows), ALL model-authored
  interpolation in the tasks formatter. ARM_COUNTS_ONLY and
  ARM_NO_PROVENANCE retire at the switch (jobs done).
- **Children fixtures DEEPENED (the maintainer, 2026-07-29).** Round 8's
  children cells were void for a NEW reason, probe-confirmed: real
  inspect on a fixture child returned messages: [] and wait carried
  message=None — the model was told "complete", looked inside, found
  nothing, and correctly redid the work (forbidden 50-100% was the
  fixture, not the model; round-6's 90% "pass" was the lying stub
  masking it). Fix: seed children with minimal transcripts (assignment
  + completion message with findings for idle children; assignment
  only for running). Then C6/C6b measure #923's real question —
  collect results vs redo — for the first time. Ids-only-roster
  verdict DEFERRED to that round (currently unreadable; sequences
  showed models DO wait+inspect, so the roster was likely not the
  binding constraint).
- **Children roster goes WS-IDS-ONLY (the maintainer, 2026-07-28).**
  idle_children predates the Safe Harness formalization, so it lowers
  model-authored child NAMES into a system turn — the plant's own
  output fed back as trusted context. Body becomes id-prefix + state
  per row (wait_for_workstream takes ids; ids are server-minted hex).
  No new eval arm needed: C6/C6b pair arms render through the
  production formatter, so the merge re-sweep measures the new roster
  for free against the round-6 baseline. Runs as the THIRD pass after
  both fix tracks land (collides with both tracks' files). End-state
  with counts-only: ZERO model-authored interpolation anywhere in the
  feature; sanitize_name in formatters becomes pure belt-and-braces.
- **CARD HONESTY (the maintainer, 2026-07-28, supersedes "names stay on the
  card"):** an idle-nudge card is the TRANSCRIPT'S RECORD of the nudge
  — it renders what the model was told, formatted for operator
  readability, NEVER content the model did not receive. A card showing
  names the model never got falsifies the operator's mental model of
  what the coordinator knows. So: children card = ident + state (full
  ws_id as link affordance is formatting, not augmentation); names
  live on the children SIDEBAR, the rich browsing surface. If
  counts-only wins, the SAME principle makes the tasks card a counts
  line — the tasks PANE is the browsing surface — deleting tasks_meta
  row machinery. Formatting may differ from the body; content may not
  exceed it. Composes with (does not conflict with) sanitize_display:
  whatever the card shows, it shows faithfully; WHAT it shows is what
  the model got.
- **Drain-time coherence machinery STAYS in #913** — the maintainer accepted that it arguably
  belonged in a separate PR, but ruled that it is needed and must be made to work reliably in this
  changeset. Fix per grouping (scope memo to the drain pass, delete the TTL).

- **Cooldown is a PER-CLASS property (the maintainer, 2026-07-28 — supersedes
  the earlier blanket "no cooldown for this class").** LIVENESS
  (`idle_children`): cap-only is CORRECT — single exit, re-arm is
  genuine progress. ADVICE (`idle_tasks`): must ALSO carry a cooldown —
  advice is exactly the class that can spam. The original ruling was
  applied uniformly across both types when it should have applied to
  liveness only. This reframes the review's nudge-storm finding: the
  fix is a per-class cooldown, not a blanket floor. Consequences: the
  dead `_cooldown_allows` and inert `record_nudge` stamp become live
  again for one type; two pinning tests flip; the cap re-arm condition
  (any non-wake send ≠ operator progress) still needs its own fix for
  the liveness storm case.
- **Any needs_user row PARKS the advice nudge (the maintainer, 2026-07-29 —
  REVERSES fire-on-the-pending-one).** No task graph → relatedness
  unknowable → an open task may be gated on the question a parked one
  escalated, so "take the next step" is unsafe until the user answers.
  Parks at the fire gate AND the drain predicate (escalations landing
  between enqueue and delivery kill the queued entry; advice fails
  closed). The old reading's silence concern is ACCEPTED as cost: the
  pane's "needs you" chip carries the escalation; the operator's
  answer is the re-arm. needs_user stays out of TASK_OPEN_STATUSES for
  counting; the park is a second, stronger consequence in the observer
  (`_has_needs_user`). Ragged statuses do NOT park (garbage must not
  silence with no chip). Eval note: no cell seeds needs_user+open; an
  authoring guard (refuse such a cell — production never sends that
  body) is queued for the post-5b validator.
- **Idle nudges are WAKE-ONLY (the maintainer, 2026-07-29): they never
  deliver on USER_DRAIN or TOOL_DRAIN, and a queued user interjection
  OWNS the idle seam** — at wake dispatch, non-empty `_queued_messages`
  drops the idle-nudge entries and the interjection is delivered as a
  genuine (non-wake-tagged) user turn instead; caps reset as for any
  real send and the next genuine idle re-fires over fresh reads.
  **EXTERNAL EVENTS ARE NOT IDLE NUDGES (the maintainer, same day): watch /
  background-shell "any"-channel entries still fire on the idle seam
  even with an interjection waiting — BOTH deliver (the external
  notice rides the interjection turn's USER_DRAIN); only wake-channel
  entries drop, and any-channel wake eligibility is unchanged when no
  interjection waits.** On
  Stop, wake-channel entries DROP (never demote to quiet — quiet rides
  user/tool seams, forbidden for this class); liveness-survives-Stop
  means the next idle event fires fresh, not that a queued entry
  re-wakes. Delivery-honesty corollary: with wake-only delivery the
  children fact-line staleness exposure narrows to deferred-wake
  retries.
- **Co-delivery, not exclusivity.** Both nudges may fire from one IDLE
  event, tasks-first. Each entry asserts only its OWN domain — the
  advice drain predicate reads open tasks + the park, never children.
  Never reintroduce a cross-domain fire gate; the named upgrade path
  is one combined checkpoint type.
- **Liveness must never be suppressible by advice.** Separate
  try/except per path; per-type caps, never a shared total;
  asked-operator gate and `memory.nudges` gate stay OFF the liveness
  path; liveness survives operator Stop (advice must not — the Stop
  latch being cleared by the wake's own send is a review finding).
- **Storage verbatim, sanitise at each render.** One set, two
  projections: `sanitize_name` (brackets deleted) for model-facing
  interpolation, `sanitize_display` (brackets kept) for operator
  surfaces. Never make the model-facing projection bracket-preserving.
- **Bodies are eval-selected; children caveat is CONDITIONAL** on a
  live-child existence read (F2, landed): present when any live-state
  child row exists or the read is indeterminate, omitted otherwise.
  π-sufficiency was the argument: the controller held the fact, the
  body was spending a model round-trip rediscovering it. Measured: the
  induced `list_workstreams` check was 14/14 of childless-cell failures.
- **Model-facing examples must match real id shapes.**

## State at the final review (2026-07-28)

All planned work landed; suite fully green (10011). Final whole-branch
max review: 53 candidates → **37 verified survivors** (report cap 15;
always mine the synthesize prompt per
[[reference_code_review_workflow_recovery]]). Two PRODUCTION
regressions vs main: the nudge storm (cap re-arms on any non-wake
send) and Stop-suppression lasting one bracket. Merge-gate corruption:
stub `inspect` manufactures forbidden-rate hits (deepseek absolute
magnitudes inflated; arm-to-arm contrast survives), rejected mutations
count as bookkeeping, seed validation vouches only for titles.

**Fable-agent recommendation (accepted direction): fix, one
frozen-scope close-out round**, flip to narrow-band (liveness-only
lands, advice+harness parked) if the terminal review finds ≥3 new
CONFIRMED behavioral defects traceable to the fixes, or stop entirely
if the honest-instrument re-sweep collapses the typed-body contrast.
Key insight: the four worst findings trace to the ORIGINAL feature
commit's design seams, not the fix churn — the fix rounds injected
only harness-latent/cosmetic classes, and no round before the last
ever reviewed a frozen tree.

## Measured results that survive the instrument defects

Typed body vs bare continue on deepseek (correct wire): forbidden
dispatch 50-80% → ~0%. The founding safety claim, measured. Qwen
produced 0% forbidden in BOTH arms — a dead instrument, not a pass:
safety cells need a model strong enough to do the unsafe thing.
n=10 noise floor is ±20-30 points (demonstrated: identical body,
same model, three cells moved that much between sweeps).

Related: [[project_nudge_eval_harness]],
[[feedback_dont_delete_a_derivation_to_resolve_disagreement]],
[[feedback_measure_before_accepting_a_finding]],
[[project_harness_hypothesis_doc]],
[[reference_code_review_workflow_recovery]].

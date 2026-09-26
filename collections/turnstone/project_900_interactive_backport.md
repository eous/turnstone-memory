---
name: project_900_interactive_backport
description: "#900 interactive.js SSE fixes (done; follow-ups #903-#905): guards comparing transport state across an await need _connectEpoch, not readyState."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-25T01:09:46.545Z
---

**#900 — verify the three #894-campaign findings against `interactive.js`, fix
what's real.** Branch `fix/900-interactive-backport-set`. Two confirmed and
fixed, two declined with the ruling written in at the site. Three review
rounds; production code came back CORRECTNESS-CLEAN in round 3 (its only
production finding was maintainability). Follow-ups filed: #903, #904, #905.

## The two fixes

**1. `destroy()` bumped no load token — and the filed finding was the small
half.** The filed leg was a re-armed retry timer. The bigger legs: a settling
`_refetchHistory` rendered into detached DOM, and `_loadHistoryThenConnect`'s
`.finally` reopened an `EventSource` on the destroyed pane AND re-registered
the document-level `visibilitychange` listener teardown had just removed —
whose `onerror` then re-armed the host recover beat forever, because it gives
up only on `dead`, which `destroy()` never sets. A closed tab held a node
connection and a 5s reconnect beat for the life of the page. ONE token bump
at the terminal seam closed all three, because the token was already the
chokepoint every post-await consumer read. `giveUp()` got the matching timer
cancel (it already bumped). **Lesson: when a filed finding names one escape
from a seam, enumerate the seam's other consumers before fixing — the
chokepoint may already exist.**

**2. A point-in-time liveness read is forgeable by a reconnect.** The
render-time gate started as `evtSource && readyState === OPEN`. A transport
that DROPPED and finished RE-ESTABLISHING inside the `/history` await reads
back OPEN and is indistinguishable from one that never moved — but the redial
re-presented the frozen `_lastEventId`, the server answered `replay_ok`, and
the replay quiesce BUFFERED that slice, so the render commits rows the flush
then repaints. Object identity is not a substitute: a NATIVE reconnect reuses
the same `EventSource`. Only a counter works — `_connectEpoch`, captured at
dispatch, required unchanged at render.

**Bump site is `onopen` and nowhere else**, for three independent reasons: a
native auto-reconnect calls neither `connectSSE` nor `disconnectSSE`;
`connectSSE` would FALSE-bump on its `document.hidden` early return, which
establishes no stream; and per spec a `close()`d source can never fire a late
`open`, so a discarded stream can't bump a generation the pane moved past.
**This generalises #894's "liveness from the channel that creates the hazard":
readyState is a SAMPLE, a counter is a GENERATION. Any guard comparing
transport state across an await needs the generation.**

## Harness honesty — three lessons, all found the hard way

**A detector that cannot observe the artefact is not coverage.** Every
scenario in `scripts/recovery_e2e.py` counted `.msg.user` rows — and user rows
NEVER travel on the SSE stream (a /send emits none; only /history replay
paints them). So no detector in the tree could see a duplicate assistant
bubble, the exact artefact the campaign prevents. E8 counts sentinel
OCCURRENCES in transcript text instead, and reproduced `dupes=2` under
control. **Before trusting a green scenario, ask what DOM the artefact lands
in and whether the assertion reads it.**

**A negative control that removes two terms proves only the weaker one.** E5
drives the retry via `__hide()`, which nulls `evtSource` — and `connectSSE`
early-returns while hidden, so E5 STRUCTURALLY cannot produce the
non-null-but-CONNECTING source that `readyState === OPEN` exists for. It
covers the PRESENCE term only. The original control removed both terms at
once, which disguised it for a full round. Coord's G5 has the identical gap.

**A held-fetch scenario must assert the fetch was still held.** E8's setup
(disconnect + send + `wait_turn` + redial) is unbounded — `wait_turn` alone
allows 45s. If it outran the hold, the payload resolved while `evtSource` was
null, the presence term declined it, and the run stamped green without ever
evaluating the generation term. Fixed by asserting the 200-counter had NOT
advanced at the redial. E6/E7 got the same positive proof.

## Test-pin fragility (recurring, three distinct bites this campaign)

- A `body.index("literal")` anchor **ERRORS with ValueError** rather than
  failing on a named assertion when the literal changes. Assert the anchor
  exists BEFORE slicing on it.
- Fixed-size windows truncate mid-expression (a 2000-char window cut a
  58-char match in half). Prefer index-bounded slices, or no window when the
  match is unique and locality is established elsewhere.
- Negative pins (`assert X not in body`) match the RULING COMMENT that names
  the field deliberately. Strip comments first — this file's `_strip_comments`
  helper exists for exactly that.
- Prettier's multi-line `setTimeout` reflow re-indents a whole callback body,
  breaking exact-indentation tail pins. Normalise whitespace in ordered-tail
  assertions.

## Declined, with rulings at the site

Same-token `/history` overlap is UNREACHABLE in interactive: the replay
quiesce serializes what coord's `refetchSeq` had to order, because coord has
no quiesce (its own decl says so). The joined-flight window is closed for both
clients by the shared `make_history_handler`'s generation-keyed flight.

## Cross-client

Coord is **not** immune to the reconnect-in-await render (#904):
`replaceChildren()` discards only what has already been DISPATCHED, so a
`replay_ok` slice landing post-render duplicates there too — a race rather
than interactive's determinism, and bounded by coord's 15s `histTimer`. Not
ported blind: a guard with no coord scenario is an unverified guard. Coord's
REMOVED r8 epoch was a truncation-generation stamp, NOT a connection
generation — do not cite it as precedent.

The retry jitter WAS a both-clients change (byte-identical arms, identical
G5/E5 detectors); the floor + spread are shared exports in `sse_overflow.js`.
Jitter works AGAINST #884's single-flight (spreading de-coalesces the herd it
merges), so it is kept small — ruled at the constant.

Scenario family: C + E1-E8 + G1-G7 + F1/F2 (21), every one negative-controlled;
E5/E6 additionally CROSS-controlled so each detects its own mechanism.
Harness parity debt: E6/E7/E8 have no coord counterparts (E7 likely cannot —
coord's destroy aborts via `histCtrls` rather than invalidating a token).

Related: [[project_894_coord_over_rewind]] (the source campaign),
[[project_890_clear_ui_guard]], [[project_884_history_coalescing]],
[[project_sse_core_extraction]] (which subsumes this parity tax in 1.9),
[[feedback_harness_scripted_events_not_verification]].

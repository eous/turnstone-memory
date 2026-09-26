---
name: project_frontend_render_corruption
description: "Garbled frontend output on fast streams or renderer.js sentinel escapes: SSE batching + overflow poison shipped (#805/#812); NUL-only renderer fix awaits push."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-20T16:59:33.571Z
---

## Current state (2026-09-05 header)

- Status (2026-07-08): CLASS 2 (SSE fast-stream corruption) SHIPPED as PR #805 — emit-time micro-batching, `_ListenerQueue` poison-on-overflow → reconnect-replay, client storm guard, real close-on-hide; its coordinator-pane parity half (#806) committed as PR #812 with the shared `shared_static/sse_overflow.js` core and a replay-aware sidebar refresh. CLASS 1 (renderer.js NUL-sentinel / pass-order containment escapes) IMPLEMENTED on branch `fix/renderer-containment` (commit 65f624f7, 5 review rounds, 99 renderer tests + 8/8 real-Chrome oracle) — AWAITING USER PUSH.
- Measured facts: the SSE queue/drain was NOT the bottleneck (58–73k events/s); transport-write backpressure was, so batching (~40 events/s) is the primary fix and poison+reconnect only a storm-guarded safety net; the "closes on hide" mitigation cited in code never existed before this work; coordinator overflow is a CONFIRMED field problem on lower-powered hardware, so close-on-hide stays.
- Class 1 landed shape: NUL-only strip at depth 0 (not the whole C0 range), `undefined`→match guard in every restore callback, `<details>` extracted AFTER the fence pass with raw fenced bodies restored, unified fence-open regex that re-emits indent + list marker.
- Open: coord `refetchHistory` lacks interactive's quiesce+token port (pre-existing); the O(n²) streamingRender prefix/tail split stays with [[project_frontend_long_session_audit]]; the in-band `replay_truncated` alternative is a possible client simplification only.
- Lessons: fixing a coordinator SSE bug means porting interactive's proven mechanism, never inventing one; verify a load-bearing claim against the server before optimizing on it.

---

Two rendering bug classes, diagnosed then hardened by a two-agent Opus adversarial
review (one per class, 2026-07-07). Review REFUTED 1 claim, corrected 2, and found
a higher-severity bug in EACH class that the first pass missed.
Resumable review agents: class-1 `a71c9ed91e4431032`, class-2 `aa46f83b6da9ee121`.

**CLASS 2 (SSE fast-stream) IMPLEMENTED 2026-07-07 — branch `fix/sse-fast-stream-corruption`,
worktree `<worktree>`, squashed base `739b04ce` REBASED onto origin/main
`e5e48a78` + 2 PR-feedback follow-ups (HEAD `27697dd3`). **PR #805.****
**PR-feedback round (2026-07-07, all 10 review threads addressed + resolved):** Copilot
found 2 — (1) connectSSE opened an EventSource even when the tab was already hidden
(fresh-connect-in-a-background-tab; the timer guards never covered that path — this is
EXACTLY the deferred R3 finding, independently corroborated), fixed by adding the
`document.hidden` guard at the connectSSE chokepoint (after wsId+visHandler install,
before `new EventSource`); (2) the `_ListenerQueue.closing` docstring still said "drain
loop checks closing BEFORE poisoned" — stale after the R2 fix moved it inside the poison
branch — reworded (commit 9e9f14a1). github-code-quality flagged 8 test files mixing
`import ... as suib` + `from ... import` for session_ui_base — normalized to string-target
monkeypatch, single import style (commit 27697dd3). Push follow-ups as NEW commits (PR is
open — never force-push a PR branch).
Both full CI invocations green on the rebased tree (sqlite 8874 / postgres 8881 — the
counts rose because the rebase pulled in main's merged renderer tests). THREE workflow
review rounds: R1 found 3 (fixed), R2 found 3 apply-pass defects IN the R1 fixes
(fixed) — the most severe was my own regression (a top-of-loop `closing` check
dropped a healthy client's queued tail at teardown), R3 clean on correctness (1
deferred cleanup). What landed: Fix B emit-time micro-batching of content/reasoning
(~25 ms / 4 KB window, one _enqueue per batch, ~10-20x fewer events) with the two
brief conditions enforced (append+enqueue atomic under _ws_lock; every non-token emit
flushes at the _enqueue choke point) + Fix A `_ListenerQueue` poison-at-first-overflow
→ drain-loop stream_overflow close → reconnect-replay, with an out-of-band `closing`
flag so a ws teardown unwinds clean instead of a false overflow. Client: 3-in-60s
reconnect-storm guard → degraded catch-up (doubling 15→120s cooldown keyed off a
last-trip timestamp) + real close-on-hide/replay-on-show visibilitychange handler +
drop-vs-render-wedge counters. NO global gap-detector (S4). Corrected the false PR-G
close-on-hide comment.

**Throughput after this change:** the wire EVENT rate is now decoupled from the token
rate — clamped to ~40 events/s (the 25 ms window) until a batch fills 4 KB within a
window, which only happens above ~40-50k tok/s (then event rate ≈ tok/s ÷ ~1170). So
the queue/drain path (500 slots, measured drain 58-73k events/s) is non-binding until
~200k tok/s, vs a fast local node's 2-3k tok/s (~1000x headroom). The NEW ceiling is
the client: `streamingRender` re-renders the whole contentBuffer per content event,
now ~40x/s not 500-2000x/s — a 10-50x win, but still O(n) per render so LONG turns
(not fast ones) are the limit = the pre-existing O(n²) streamingRender prefix/tail
split in [[project_frontend_long_session_audit]], untouched here.

**KNOWN GAP (DURABLE — coordinator/CLI parity, file a follow-up):** the SERVER-side
fixes (batching + `_ListenerQueue` poison + `closing`) live in session_ui_base.py and
apply to EVERY SSE stream (WebUI interactive AND ConsoleCoordinatorUI coord — shared
base). But the CLIENT-side companions (the `stream_overflow` degraded-mode handling,
close-on-hide visibilitychange, drop-vs-wedge counters) are ONLY in the shared
`interactive.js` pane. `coordinator.js` has its OWN content path (grep: on_content_token
/contentBuffer/streamingRender ×13) and does NOT handle `stream_overflow` or
close-on-hide — on overflow it still RECOVERS via native EventSource reconnect +
ring-replay (the server poison guarantees a clean contiguous gap), it just lacks the
storm guard + the counter. Low-rate coord streams make overflow unlikely there, so
scoped-follow-up not blocker — same shape as the preview-pane "coordinator-pane parity"
follow-up ([[project_preview_pane]]). **Issue #806 — coordinator half
COMMITTED 2026-07-08 (`7b5635b1` on branch `worktree-fix-coord-overflow`, single
amended commit, after 3 `/code-review high` rounds; **PR #812** vs main).**
**CORRECTION to the "overflow unlikely on coord" premise above (user, 2026-07-08):
NOT unlikely — a confirmed real field problem for a user on lower-powered hardware
than the maintainer's workstation; that's exactly why #806 is being done NOW not
deferred, and why close-on-hide STAYS. A high `/code-review` then found 8 findings,
ALL downstream of the close-on-hide companion (5 hidden-tab-lifecycle correctness
bugs: first-connect-hidden skips the sidebar refresh; coordCloseSession resurrection
race; stuck "connecting…"; every-refocus full-resync churn; + a background-monitor
freeze that is INTENDED/accepted — plus 3 dedup findings). Handed to a Fable agent to
fix — keep close-on-hide, solve the bugs (see [[feedback_fresh_briefing_vs_agent]]:
briefed the capable model with problem + constraints, NOT prescribed code).**
Extracted the drift-prone pure core (5 tuning consts + `overflowWindowTripped` +
`degradedCooldownStep`) into NEW `shared_static/sse_overflow.js`; BOTH panes import it
(interactive via `./`, coord via `/shared/`) — interactive's 2 node-runtime probes moved
to `tests/test_sse_overflow_js.py` (kept as `export function`, probe regex now
`^export function`). Did NOT refactor interactive's stateful glue into a controller:
its ~15 source-assertion pins in test_interactive_pane_js.py hard-pin the class-method
shape (`this._noteStreamOverflow`/`_streamHealth`/`_visHandler`), so a controller would
break the just-shipped fix — glue is reimplemented per-surface (class methods vs closure
funcs) instead. coordinator.js got: `stream_overflow` case→`noteStreamOverflow`, storm
guard→`enterDegradedCatchup` (suspend+doubling cooldown→connectSSE; replay_ok or the
PRE-EXISTING `case "replay_truncated"`→`refetchHistory()` /history floor), close-on-hide
`onVisibilityChange`+`removeVisibilityHandler`+the `document.hidden` connectSSE
chokepoint guard, and `streamHealth{overflows,renderThrows×4,malformedFrames}` counters
(onmessage now wraps `handleEvent` in try/catch — coord previously had NO dispatch guard).
**Final design after the 3 review rounds:** child_ws_*/task events ARE ordinary ring
entries (Fable's discovery — the old "not replayed" comment was STALE, predated the ring;
VERIFIED at session_ui_base `_enqueue_direct` ring-append), so the post-gap sidebar refresh
is REPLAY-AWARE — fires only when replay can't cover the gap (no cursor / `replay_truncated`
/ gap>60s cursor-trust window / a live event-id BELOW the saved cursor = process-restart
counter reset, which the replay path reports as a FALSE replay_ok). A `replay_truncated`
seen mid-stream is DEFERRED via a `pendingTruncatedResync` latch consumed at idle (ported
from interactive — repairs both ring-eviction AND a close-on-hide-stranded turn).
**LESSONS:** (1) my round-2 invented `state_change` reconcile was the WRONG shape — the
coordinator is a SIMPLIFIED PORT of interactive, so fixing a coord SSE bug = port
interactive's PROVEN mechanism (here the latch), don't invent; always diff the coord
handler against interactive's. (2) verify a load-bearing claim against the SERVER before
optimizing on it (the stale-comment trap). **[R3] DEFERRED follow-up:** coord
`refetchHistory` lacks interactive's `_beginReplayQuiesce`+`_historyLoadToken`, so an
un-awaited refetch can blank-on-transient-failure / race concurrent paint — PRE-EXISTING
across ALL its callers; a real fix is a separate quiesce+token port. All JS suites green. NOTE: repo has NO prettier config + HEAD coord.js already non-conforming,
so the session PostToolUse formatter's incidental reflows are unrelated churn — reverted
one via Python (Bash, not Edit, so the hook doesn't re-reflow). The CLI is UNAFFECTED
entirely: cli.py overrides `on_content_token` to write stdout (bypasses the batcher) and
has no listener queue.

R3-DEFERRED hidden-tab guard NOW LANDED via the PR-feedback round (9e9f14a1): the
`connectSSE` chokepoint guard closes the fresh-connect-while-hidden gap. The timer-local
guards were KEPT (not deduped) — the recover beat's `document.hidden` check is
load-bearing (it also gates the `failCount`/`giveUp` logic, not just the connect), so
full centralization isn't the clean deletion R3 imagined; the connectSSE guard is the
net that backstops every caller. Also DEFERRED per the brief's own recommendation:
the in-band `replay_truncated`-gap alternative to poison+reconnect (heals via /history
on the same connection, no reconnect/storm, but trades away the transient-slow fast
recovery the current design gives — evaluate as a possible client simplification, NOT
an addition; prototype on a separate branch to diff). Local pg CI gotcha hit + fixed
this session, see [[reference_memory_store_maintenance]] (test isolation + stale
turnstone_test).

**Self-contained per-class implementation briefs (tagged VERIFIED/PLAUSIBLE/
UNCONFIRMED on every claim), gitignored, ready to drop into `/ship`:**
`docs/design/frontend-render-containment-brief.md` (class 1),
`docs/design/sse-fast-stream-corruption-brief.md` (class 2). Recommended path:
one focused /ship session per class (they're independent subsystems → run
concurrently); reserve multi-agent workflow orchestration for the DIFF review
after each lands. NOT a good fit for one monolithic workflow — implementation
within each class is serial + judgment-heavy (pass-ordering / _ws_lock coupling),
the anti-pattern for fan-out. Redaction check: redactCredentials is NOT on the
fast-model content path (streamingRender only); runs once at tool_result finalize
(~16 regex passes when prefilter hits, which is almost always) — a real one-time
main-thread cost but not the per-token cause.

## Class 1 — containment escapes in renderer.js (real-Chrome verified via headless oracle)
renderMarkdown protects blocks with in-band sentinels NUL+tag+idx+NUL (7 tags:
CB/DT/BQ/MB/TB/IC/IM), restored renderer.js:731-763. escapeHtml (utils.js:13-17)
is a textContent→innerHTML round-trip = NO tokenizer, so it PRESERVES U+0000 →
forgery works. But the FINAL string IS tokenized (both sinks: streaming
`el.innerHTML=` renderer.js:1311, history setSafeHtml/DOMParser utils.js:138) and
the tokenizer DROPS U+0000. Consequence: forged TAGS materialize as real DOM;
"raw NUL visible in text" was a harness artifact (browser shows "DT0" not `\x00DT0\x00`).
- CONFIRMED (real Chrome): sentinel forgery/relocation (any tag, block duplicated/
  moved into prose); out-of-range→literal `undefined`; cross-container inject
  (IC forged inside a CB renders `<code>` inside `<pre>`); **BQ-before-fence
  (renderer.js:293-351 before 388): `> ` lines inside a code fence → real
  `<blockquote>` nested in `<pre><code>`, NO special chars, ordinary trigger —
  most-common real bug**.
- Content-spoofing, NOT XSS: `_SAFE_TAGS` (13-14) is attribute-free, image/link/
  footnote attr concats all ride escapeHtml (pinned by test_renderer_js.py lint) —
  agent re-verified clean.
- **NEW-1 (higher severity, MISSED first pass): recursive renderMarkdown for
  `<details>` bodies (417/420) and footnote bodies (718) receive OUTER-scope
  sentinels and re-render with FRESH EMPTY block arrays → restore to literal
  `undefined`.** Code-in-`<details>`, inline-code/math-in-footnote → silent content
  loss as "undefined". No NUL, no forgery, common input. The BQ pre-pass comment
  (289-291) documents this exact hazard as the reason BQ runs first — details &
  footnotes violate the same invariant. **Fix A does NOT catch this.**
Fix plan (revised by review):
- (A) strip C0 controls except \t\n\r at renderMarkdown entry — SOUND for
  forgery subclass, premise exhaustively verified (only 7 sentinels, all NUL-framed,
  renderer is the sole NUL producer), 73/73 tests pass. But scoped: does nothing
  for BQ-in-fence, NEW-1, bidi. Pair with `undefined`-guard in restore callbacks
  (`return arr[idx]===undefined ? m : arr[idx]`) to kill all `undefined` leaks.
- (B) BQ-in-fence: "can't just hoist fence above BQ" CONFIRMED (unanchored open
  eats `> ```` blockquoted fences → `undefined`). Simpler alt: hoist fence AND
  anchor open `^` (`/^(```+)/gm`) — caveat: plain `^` drops indented fences; use
  `^[ \t]*`/`^ {0,3}` and RUN FULL SUITE (behavior change).
- (C) `<details>` fix must be anchor-OPEN-ONLY; anchoring both breaks the common
  one-line `<details><summary>x</summary>y</details>`.
- NEW-2: consider a bounded fixed-point restore loop to close the whole
  nested-sentinel family instead of one instance. NEW-4: bidi needs its own
  isolation/strip pass (not C0). When editing JS control-char regexes use
  String.fromCharCode ([[feedback_tool_write_escape_decoding]]).

**CLASS 1 IMPLEMENTED 2026-07-07 — branch `fix/renderer-containment`, worktree
`<worktree>`, single commit `65f624f7` rebased onto origin/main 2c5adb7a. AWAITING
USER PUSH.** 99 renderer tests + full frontend suite (272) green; a real headless-
Chrome oracle (loads live utils.js+renderer.js as ES modules, `--dump-dom`) confirms
all NUL-sensitive cases in a real DOM (8/8). FIVE workflow review rounds (6→3→2→2→0
findings); the FENCE-OPEN REGEX regressed in 3 CONSECUTIVE rounds — the durable
lesson. What landed vs the brief:
- Strip NARROWED to **NUL-only** (`/\x00/g`), NOT the brief's whole C0+DEL range —
  stripping C0 damaged pasted code fidelity (ESC/FF/VT in a fence); forgery is
  NUL-framed so NUL-only suffices. Depth-0-only (recursive frames keep generated sentinels).
- Restore callbacks get an `undefined`→`m` guard via a `_restorer(arr)` factory (12 passes).
- NEW-3: CB gained the `<p>SENTINEL</p>` unwrap; made **whitespace-tolerant**.
- **NEW-1 solved NOT as the brief said.** Brief wanted details extracted BEFORE fence
  (fence-aware via offsets) — that regressed (details close matched a `</details>`
  example inside a later fence). Final: extract `<details>` **AFTER** fence, restore its
  fenced bodies from a saved `codeBlockRaw` array to RAW source before the recursive
  render (fence-masking gives fence-awareness for free). Footnote NEW-1 rides the Fix-2
  round-trip (outer restore resolves the appended footnote's floored sentinel).
- **B4 fence anchor = the whack-a-mole.** `^ {0,3}`→`^[ \t]*`→drop-indent each traded one
  indent-context bug for another (footnote-continuation, list-marker line `- ```py`,
  nested-list `  - ```py`). FINAL unified fix: `/^([ \t]*)((?:[-*+]|\d+[.)])[ \t]+)?(```+).../gm`
  — capture indent(1)+optional list-marker(2), **RE-EMIT both** before the sentinel
  (keeps document position: nesting, list items, footnote-continuation all work), and
  make the CB `<p>`-unwrap whitespace-tolerant so a preserved-indent own-line fence still
  has no stray `<p>`. `>` is neither indent nor marker so blockquoted fences stay excluded.
  This also FIXED fence-in-footnote (renders in the footnote now). Lesson for any re-touch:
  the fence pass must preserve what precedes the backticks; if B4 ever needs rework prefer
  a **fence-aware blockquote scanner** over more anchor patching.
- `\xNN` hex escapes typed directly (safe; see [[feedback_tool_write_escape_decoding]]),
  NOT String.fromCharCode as line above suggested.

## Class 2 — fast-model (500+ tok/s) long-session corruption (measured, claim 3 REFUTED)
- CONFIRMED: per-delta enqueue (session.py:6586→on_content_token→_enqueue, ≈per
  token); silent drop on queue.Full (session_ui_base.py:611-613, cap
  _DEFAULT_LISTENER_QUEUE_MAX=500 ≈1s@500ev/s) — note put_nowait drops the NEWEST
  event; no gap detection (client blind `contentBuffer+=` interactive.js:1457, only
  uses lastEventId for reconnect URL → live drop permanent, ring heals ONLY
  reconnect); dropped-fence-closer → whole-message reshape = corruption.
- **Claim 3 REFUTED**: the per-event executor/is_disconnected loop is NOT the
  bottleneck — measured 58-73k events/sec through the exact pattern (29-146× the
  token rate). Real bottleneck = **transport-write backpressure**: sse_starlette
  `async for … await send` has NO internal buffer, so a SLOW CONSUMER blocks send →
  generator suspends → client_queue stops draining → overflow. Fix must target
  consumer rate, not server polling.
- **NEW/HIGH — S1: the "PR-G closes connections on hide" mitigation cited at
  session_ui_base.py:154-161 DOES NOT EXIST.** No visibilitychange handler anywhere
  in shared_static/console; deactivate() explicitly keeps the stream live
  (interactive.js:4480). Backgrounded tab (Chrome throttles drain) = single most
  likely field trigger. Drops are SCATTERED not a contiguous tail (once saturated
  the consumer opens single slots → interleaved succeed/fail), which is exactly why
  lastEventId sails past the holes.
- S3 correction: the 512KiB _MAX_TURN_CONTENT_CHARS inflight cap drops the TAIL
  (keeps head), not the head as first written; self-heals at idle via
  _pendingTruncatedResync→_refetchHistory (/history is uncapped).
- S2: coordinator proxy is byte-transparent BUT chains backpressure — slow browser
  → proxy stops reading → NODE queue overflows invisibly on the node. S4: live-path
  fan-out runs OUTSIDE _listeners_lock (session_ui_base.py:611) so live ids are NOT
  strictly monotonic under concurrent tool+content emit — a trap for any naive
  client gap-detector (content-vs-content never reorders, both under _ws_lock).
Fix plan (revised by review):
- (B) emit-time micro-batching = PRIMARY fix (attacks event COUNT, the real cap).
  SOUND but TWO mandatory conditions: (1) append-to-inflight and _enqueue the batch
  in ONE _ws_lock section — ideally an in-worker-thread time-OR-size flush inside
  on_content_token, NO timer thread — else a snapshot straddle double-renders
  (_seq>snap_seq batch carries already-snapshotted text; no client-side content
  dedup exists). (2) FLUSH the pending batch before ANY non-token event or
  stream_end overtakes trailing content → repaints into a new bubble.
- (A) poison-on-overflow → reconnect → replay_ok: recovery math CORRECT (gap is
  contiguous at poison instant, ring has all events incl. first drop, no off-by-one,
  replay slices eid>last_event_id session_ui_base.py:892). BUT demote to
  storm-guarded SAFETY NET only: for a persistently-slow consumer reconnect can't
  make it faster → re-saturates → livelock + 2.5-4.5s stall/cycle = STRICTLY WORSE
  than silent drop. Guard: poison after N CONSECUTIVE fulls (not first), rate-limit
  reconnect, snapshot-and-hold on repeated truncation. Closing mechanism = per-
  listener flag the drain loop checks (producer can't enqueue a pill into a full q,
  and can't preempt a blocked send).
- Recommended combo: B (kill rate) + storm-guarded A (residual) + real
  close-on-hide/replay-on-show for S1 + optionally raise 500 cap (orthogonal).
  Do NOT raise cap as the primary lever ([[feedback_sse_queue_not_a_bottleneck]]).
- SYMPTOM OVER-DETERMINED: identical "output stops, backend healthy" also = the
  handler-wedge from [[project_frontend_long_session_audit]] (thrown finalize
  leaving refs stale). INSTRUMENT to distinguish scattered-clean-gap (drop) vs
  console "streamingRenderFinalize failed"/"malformed SSE frame" (wedge) before
  shipping — don't fix one and leave the other.

Related: [[project_frontend_long_session_audit]] (streamingRender prefix/tail split
still open — jank amplifier at fast rates, not corruption).

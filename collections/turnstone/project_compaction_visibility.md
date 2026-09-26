---
name: project-compaction-visibility
description: "Compaction progress events/card, commands on the worker slot, or /send during a command window (PR #863 shipped 2026-07-17): defer-and-drain is the contract."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-26T00:36:42.575Z
---

## Current state (2026-09-05 header)

- Status: SHIPPED to main 2026-07-17 — PR #863 "Compaction visibility + defer-and-drain send subsystem" rebase-merged, main HEAD 515d372a (9 commits f92644a3 … 005596f1).
- What shipped: first-class `compaction` SSE lifecycle events (start/progress/end with compaction_id, `superseded` and `notice` on ends) plus a progress-bar card in both panes (blue accent, not magenta); every slash command dispatches through the worker slot (busy → HTTP 409, /compact fire-and-forget, quick commands 25s backstop); /history re-renders compaction marker rows; /send during a command window is DEFERRED (immediate `{"status":"queued","deferred":true}`, `_PendingSend` + daemon-thread drain, `PENDING_SENDS_MAX=10`).
- Campaign: 11 review rounds, correctness trend 15/6/6/4/4/6/7/7/3/0/0 — converged under the 2-consecutive-clean rule (r10 Fable clean, r11 Opus clean); the `fix-sanity` workflow used from round 4 was ENDED by the maintainer 2026-07-20 and must not be reinstated.
- Deferred follow-ups: regenerate openapi-console.json (pre-existing drift, separate PR); per-command concurrency classification (all commands 409 during long compactions); G1 no-chip setBusy(true) residual documented in code.
- Lessons: background tasks have loop affinity — a daemon thread beats an asyncio task under TestClient; any new unconditional ws-attribute read on a hot route needs a sweep of every MagicMock/SimpleNamespace ws stub; read the explicit `pytest-exit:` line, never a background shell's exit code; `gh pr view --json merged` is not a valid field.

---

# Compaction visibility (session 2026-07-16, on main post-1.8.0a2)

> **Historical note:** this campaign ran the `fix-sanity` workflow, which the maintainer
> ENDED on 2026-07-20. Every "fix-sanity" reference below is a record of what
> happened then, not a current process — the workflow is retired and must not be
> reinstated. Its charter survives as an in-session design pass; see
> [[feedback_review_convergence_methodology]] lesson 8c.

The maintainer's report: (1) no progress bar for compaction in webui, (2) manual `/compact` rendered as a user turn with no visible indicator, (3) compaction result not re-rendered after refresh. All three landed in one change set.

**Root causes found:**
- `/v1/api/command` ran `handle_command` synchronously ON the event loop — a manual compaction (multiple LLM calls) froze every SSE stream on the node until it finished, so its own events arrived as one burst afterward. That's why "no visible indicator".
- Frontend `sendMessage()` posted slash commands to `/command` but then called `addUserMessage(text)` — a fake user bubble, never persisted, vanished on reload.
- The persisted compaction marker row (`_source="compaction"`, meta.watermark) was deliberately dropped by `reconstruct_messages` (`_utils.py`) for ALL display paths, and the live "[compacted…]" text rode unpersisted `info` events → nothing to re-render after refresh.

**Design shipped:**
- `SessionUI.on_compaction(payload) -> int | None` protocol method; payloads `{phase: start|progress|end, ...}` (start: trigger/where/pct; progress: part/total/depth or retry_in/error; end: ok + before_tokens/after_tokens/summary or reason/message). Emitted from `_compact_messages` (now a lifecycle **wrapper** owning latch-clear + exactly-one-start/one-end via a BaseException backstop; body moved to `_compact_messages_impl`; bails go through `_compaction_bailed(reason, message)`). `_do_auto_compact`'s notice now rides the start event (`where=` threaded through).
- `SessionUIBase.on_compaction` → `_enqueue({"type":"compaction", ...})` (returns event id; sets activity "Compacting context…"; agent-scope-suppressed like `on_info`). `TerminalUI.on_compaction` reproduces the old CLI text exactly. NullUIs (eval + tests/_session_helpers) covered via base/no-op.
- **Marker row now stamped with the ok-end event's id** and meta extended `{watermark, before_tokens, after_tokens, trigger}` (resume reads only watermark — `parse_checkpoint_watermark` ignores extras). Same live-id/row-id alignment trick as `on_system_turn`.
- **/history re-render**: `load_messages(..., include_compaction=True)` (history handler only) makes `reconstruct_messages` re-row each marker as an IN-PLACE `role="system"` row (assistant rows drop `_source`/meta on reconstruct; system rows keep both) → flows through the standard operator-turn projection → frontend `source==="compaction"` branch renders the card. Export/search/resume unchanged. Dedup vs live/replayed end event via the existing `_renderedSystemEventIds` set.
- **Manual /compact via web dispatches through `session_worker.send`** (worker slot): event loop free, concurrent sends take the queue path, Stop button cancels it (GenerationCancelled → end reason=cancelled), busy → `{"status":"busy"}` refused. Exit seam calls new public `ChatSession.flush_queued_messages()` (cancel-path precedent: queued-during-compaction messages land as a transcript user turn, answered next turn). Other commands: `asyncio.to_thread`. Manual success now calls `_print_status_line()` (parity with auto).
- **Frontend**: shared builders in `conversation.js` (`buildCompactionCard`, `buildCompactionProgressCard`, `updateCompactionProgress`); interactive pane `handleCompactionEvent` + coord viewer wired the same (coord's `renderSystemTurn` got the compaction branch — covers live + history). Progress bar: determinate `(part-1)/total` at depth 0, full+"merging" at depth>0, indeterminate sweep for single-batch. CSS in `shared_static/chat.css` (magenta accent; both index.html + coordinator include chat.css). Slash commands echo as `.msg.command-echo` chip, busy-guard now explains itself. `_compactionCard` ref reset in `_resetStreamingRefs`.
- SDKs: python `CompactionEvent` dataclass + TS interface added (registries were tolerant of unknown types anyway). Discord/Slack bots never consumed `info` events, so no channel regression.

**Gotchas hit:** session.py had a literal `"─"` escape (the Edit-tool escape-decoding trap) — removed that line via a chr(92) python one-liner. CHANGELOG edit initially swallowed the existing Added entries under a new Fixed header — repaired.

**Verification:** headless-Chrome file:// harness rendering all card states from the REAL conversation.js + chat.css (screenshot verified: bar math, fold, chip) + a reducer self-test driving `applyCompactionEvent` through the subdivision-merge sequence (monotonic widths, end-dedup by event id, error-notice suppression). NOTE: `--dump-dom` snapshots BEFORE an ES module with top-level await executes — use `--screenshot` (virtual-time budget runs the module) and read the rendered self-test JSON. Tests: lifecycle-event class in `test_cooperative_compaction.py`, `include_compaction` projection in `test_compaction_checkpoint.py`, worker-dispatch/busy/drain-answer/cancel-flush in `test_server_authz.py`.

**xhigh review round (2026-07-16, 15 confirmed findings — ALL fixed).** The worker-dispatch cluster was the real harvest; the fixes reshaped the design:
- `ChatSession.compact_now()` = the manual path now mirrors send()'s entry EXACTLY (`_generation += 1`, capture, fresh `_cancel_event`) and consumes its cancel on exit while still the active generation. Fixes three confirmed races: my_generation=0 skipped the pre-swap supersession guard (`_check_cancelled`'s generation arm is falsy-gated!) so a force-abandoned compact thread could swap history under a successor + poison the marker watermark; a cancel during manual compaction left `_cancel_event` set forever (bricked every /compact retry until the next send — verifier reproduced it); an idle Stop click pre-aborted the next compaction.
- `_run_compact`'s exit seam is owner-guarded (`ws.worker_thread is me` — same as send/retry closures) and ANSWERS queued messages: `drain_queued_message_text()` + `session.send(combined)` on the same worker (the old inline path answered them; flush-only left them unanswered in the transcript). User-cancelled compaction flushes instead (no auto-run after a Stop).
- ALL commands now dispatch through the worker slot (busy-refusal replaces the event-loop serialization that `asyncio.to_thread` had silently removed — /clear could interleave with a running compaction); endpoint awaits quick commands via a done-Event + `asyncio.to_thread(done.wait, 60)`; /compact alone is fire-and-forget (the maintainer: compactions routinely exceed 60s — NO bound on that branch).
- Error channel restored: `reason="error"` bails + wrapper unexpected-error arm fire `ui.on_error` (Prometheus error counter rides WebUI.on_error); the end event is card-teardown only; frontends render the red row from the paired error event (coord previously styled real failures as info).
- Activity pill: `_compaction_activity_live` latch — on_thinking_start skips the write inside the window (it was clobbering "Compacting context…" milliseconds after start, for the WHOLE summarize phase); end restores the saved pre-compaction pair (a bail can't strand the pill on an idle ws).
- Overflow-retry compaction (auto=True, no threshold evaluated) no longer claims a pct in its start event — `threshold_pct` param passed only by `_do_auto_compact`; TerminalUI prints the threshold notice only when pct present.
- Frontend: ONE shared `applyCompactionEvent(holder, evt, hooks)` reducer in conversation.js (both panes had hand-synced copies that had ALREADY drifted in the first diff); bar is monotonic (merge events are note-only — subdivision emits depth>0 between depth-0 parts and 100%-then-snap-back read as regression); truncated-summary warning rides `{"phase":"progress","warning":"summary_truncated"}`.
- Refuted (correctly): agent-scope error-drop (compaction never runs inside task agents) and marker-save double-end (memory facade has a documented no-raise contract).

**High review round (2026-07-16, 19 verified → 13 distinct, top 10 reported, 0 refuted — ALL fixed).** The worker-dispatch seams again; second review round on the same diff still found 6 real correctness bugs:
- **Stop eaten in the completion tail**: the seam keyed answer-vs-flush solely on "compact_now didn't raise" — a cancel after the impl's last check (swap/marker/status tail) or during a retry backoff was consumed by the finally and an answering turn launched anyway. Fix: `_claim_generation()`/`_consume_cancel()` helpers shared with send(); `_consume_cancel` REPORTS whether a cancel landed and compact_now re-raises GenerationCancelled after a completed-anyway body (compaction result stands; the stop is honored). Retry backoff now waits on `self._cancel_event.wait(delay)` + re-checks both arms (instant abort).
- **Orphan (force-cancel) lived on + corrupted successor UI**: the summarize stack's boundary check passed no my_generation (event arm blind after a successor replaced the event) — my_generation now threads `_summarize_blocks/_batch/_once`, retiring the orphan at its next checkpoint. All compaction events emit via `_compaction_event(my_generation, payload)` which stamps `compaction_id` (public, in SDKs/docs) + `superseded` (internal; SessionUIBase pops it — NEVER on the wire, pinned by test). Base: superseded start/progress swallowed (returns None), superseded END flows (pane must retire the orphan's card); latch gains `_compaction_activity_owner` (=cid) — stale end can't unlatch/restore a successor's latch; superseded owner-end unlatches WITHOUT restoring. Reducer: holder gains `cid`; non-owning progress/end ignored (ok-end result card always renders, dedup'd). Panes remove a live card on `stream_end` (only force-stop can produce that overlap — wrapper always ends before a legit stream_end).
- **Quick-command worker stranded queued messages**: `_run_cmd` held the slot with no exit drain. Shared `_drain_and_answer()` closure now used by both seams; should_exit commands flush instead (no turn on a dying session).
- **60s backstop skipped clear_ui/name-sync/should_exit-info**: follow-ups moved INTO `_run_cmd` (run after handle_command on the worker, before done-signal ordering concerns — done.set fires first in finally so the response returns while the drain answers).
- **Seam idle-clobber**: answering-send failure no longer stamps idle over send's state='error'; only on_stream_end owed (mirrors /send route contract).
- **KeyboardInterrupt = cancelled**: wrapper backstop `cancelled = isinstance(e, GenerationCancelled) or not isinstance(e, Exception)` — no more red "Compaction failed: " (empty str(KI)) on CLI Ctrl-C. Failure ends now carry `trigger`.
- Cleanups: double cancel notice killed (CLI + reducer suppress cancelled-end message when trigger=="auto" — send prints "[Generation cancelled]" itself; manual keeps it, it's that path's only line); done-wait now loop-native `asyncio.Event` + `loop.call_soon_threadsafe` under `asyncio.timeout(60)` (no executor-thread parking); `_GenCancelled` alias import dropped (module-level import exists); dead `outcome["error"]` write dropped; racy `_worker_running` assert joined.
- Gotcha: headless-Chrome file:// harness needs `--allow-file-access-from-files` now (cross-directory dynamic import of conversation.js from the scratchpad page is otherwise origin-blocked; earlier runs must have had it).

**Round 3 (2026-07-16, UNPRIMED high, 6 correctness + 4 cleanups, 1 refuted — ALL fixed via the NEW process: seam-clustered triage → written plan → fix-sanity → implement).** Every correctness finding traced to rounds 1-2's fixes, zero to the feature core — the cascade thesis confirmed. Two seams:
- **Seam A (3 findings = 1 defect):** commands-on-the-worker-slot routed command-window sends through the mid-TURN interjection queue → 2000-char silent truncation, cross-user 409 lockout for whole compactions, queued text crossing /resume//new identity swaps. Fix = **park-and-run**: `Workstream.worker_kind` (set by session_worker.send under the same lock as the worker_thread pair — the ONLY _worker_running=True setter, so unbypassable), /send route parks while `_worker_running and worker_kind=="command"` (async poll; polls `request.is_disconnected()` because starlette does NOT auto-cancel handlers on client disconnect — the composer aborts sends at ~15s and a late dispatch would double-send on retry), then re-captures ws.session PER ITERATION (a /resume during any park window swaps identity in place) and dispatches full-fidelity; the _enqueue closure refuses `command_window` under ws._lock (airtight vs the park→dispatch race); coordinator-adapter + _enqueue_init enqueues refuse likewise (queue.Full → existing backpressure surfaces). Round-2's `_drain_and_answer` machinery DELETED (queue unreachable during windows); /compact seam keeps a flush-as-backstop; /resume //new flush stranded queue text PRE-swap (persists into the ADDRESSED ws). Park UX: composer's optimistic queued bubble renders (busy=true), response-ok promotes it; >15s parks fail visibly client-side (honest; documented in api-reference).
- **Seam B (2 findings):** orphan lifecycle residuals. Root cause found by the review: summary calls passed NO cancel_ref → Stop couldn't abort the in-flight HTTP read. Fix: `_utility_completion(cancel_ref=)` passthrough to model_turn; `_summarize_once` passes a FRESH per-attempt `_CancelRef(self)` (never the shared `self._cancel_ref` — [0]-fallback + per-attempt-clear interactions; no save/restore needed: post-supersession boundary checks make further appends impossible); `_CancelRef` gained `.aborted` (event-backed) so model_turn's drain-retry can't resurrect a self-closed stream; `_summarize_once`'s except checks cancel arms BEFORE `_stop_retrying` (self-induced close maps to cancelled-end, not error-end). Latch: `on_generation_claimed(gen)` on SessionUIBase (getattr-guarded from `_claim_generation`, on_aux_usage precedent) unlatches AND RESTORES the saved pair (restore is load-bearing: unlatch-only would let a successor /compact's start capture the orphan's "Compacting context…" as its restore pair — fix-sanity's catch). Wire: `superseded` now RIDES end events (SDK py+ts field, docs; start/progress still swallowed) — reducer + CLI suppress failure notices for superseded ends; superseded OK ends still render the result card (reachable: force-stop between swap and emission).
- Cleanups: `_backoff_or_cancelled(delay, my_generation=0)` extracted; converted _summarize_once + _try_stream + task-agent _api_call + notify's two arms (notify IS in-turn tool → cancel-aware is correct); /command dispatch envelope folded into `_dispatch_command`; `resetCompactionHolder` exported from conversation.js replacing 4 hand-copied teardown sites; /command response contract (ok/busy/running + fire-and-forget /compact + park behavior) documented in api-reference.
- **fix-sanity first live run (2 agents, ~314K tokens): verdict revise-plan — 7 refinements, 10 chokepoints, 8 gaps.** Genuinely load-bearing: caught the park-retry stale-session-capture (would have re-shipped F2), the unlatch-without-restore re-strand, the shared-cancel_ref hazards, superseded-ok-end-must-render, plus `_enqueue_init` as a third unguarded queue sibling and the pre-window stranded-message swap crossing. Its two agents CONFLICTED on the cancel_ref mechanism — resolved by reading _CancelRef myself (fresh-instance beat both proposals).
- Test-fake gotcha: `_FakeSession` needed `_cancel_event` — the /send route's PRE-EXISTING cancel-drain poll reads it whenever a worker is live at send time, and no prior test had ever sent mid-worker.
- Documented bets: force-cancel of a wedged QUICK command releases parked sends into a session the abandoned thread may still mutate (no generation checkpoints in commands; comment at the force-cancel branch); >15s parked sends fail visibly at the composer's abort.

**Round 5 (2026-07-16, unprimed high): 4 correctness + 6 cleanups (9 CONFIRMED/1 PLAUSIBLE), 0 refuted, 1 finder empty — trend 15/6/6/4/4, and the convergence signal: ZERO findings from round-4's fixes (first fix round to manufacture nothing).** Composition = older strata: [double on_error on raising compaction exits = ROUND-1 original, survived 4 reviews → `_compaction_bailed(emit_error=)`, backstop passes `trigger=="manual"` (auto defers to send's fatal handler); verifying it exposed the CLI sibling MYSELF: the REPL calls handle_command BARE, so raising manual-compact errors crashed the REPL → /compact branch suppresses Exception after the wrapper's red row]. [>15s park drop = round-3 documented bet upgraded: composer's 15s AbortController killed sends during long compactions → shared `sendAbortMs(holder)` in conversation.js (600000 while compaction card live / 15000 default) used by BOTH panes (sanity found coordinator.js's identical hard-coded abort at coordSend); queued-bubble ✕ now calls `el._sendAbort()` (composer_queue dequeue()) so a dismissed parked message can't dispatch later; JS pin added (test_interactive_pane_js.py); proxy read-timeout bound documented in api-reference]. [_run_cmd follow-ups lacked the owner guard (round-2/3 residue): force-cancelled wedged command firing late clear_ui would wipe panes mid-successor-turn → me-capture + guard on follow-ups AND except-arm; `_run_initial` had the same class (adjacent, pre-existing) → guarded its except arm + notify hook (B012: guard-not-return in finally)]. [all-commands-409-during-long-compactions = DOCUMENTED disposition + follow-up issue for per-command concurrency classification]. Cleanups: dead public drain_queued_message_text FOLDED into _flush (fake+asserts cleaned); central-refusal DECLINE re-found from round 4 → ruling moved INTO session_worker.send's docstring (decline-recurrence fix: rulings live where unprimed finders read); `_release_compaction_latch_locked(restore)` deduped the two latch-release blocks; CLI/JS display-policy = cross-referencing HAND-SYNCED SIBLING comments (two runtimes, no shared path); defensive-create '· auto' = declined w/ comment (progress events carry no trigger); test delegate wrappers folded. fix-sanity round-3 usage: caught the unimplementable "known command window" clause (no client signal exists; card is THE signal), the coordinator abort sibling, the JS-pin testability claim I got wrong, and the ✕-dismiss honesty gap.

**Round 4 (2026-07-16, unprimed high): 4 correctness (2 CONFIRMED/2 PLAUSIBLE) + 5 cleanups, 0 refuted, one finder EMPTY — trend 15/6/6/4, first round needing no seam redesign (all fixes <15 lines). ALL fixed + 1 documented decline.** Composition: [0] /command busy-200 = the intentional round-1 refusal being SILENT → now HTTP **409** (body unchanged; `_dispatch_command` single site; api-reference + `turnstone/api/server_spec.py` error_codes + regenerated `sdk/typescript/openapi-server.json` — fix-sanity caught the machine-readable spec, which has NO freshness gate; also fixed /send's pre-existing 409 spec drift; openapi-console.json regen pulled unrelated pre-1.8 drift → REVERTED, follow-up regen needed separately). [1] `_compaction_event` now getattr-guards `ui.on_compaction` (+ isinstance-int return guard for mypy/duck-typed hooks). [2] compact_now: `_print_status_line()` BEFORE the tail-cancel raise (card+pill can't contradict). [3] `_CancelRef(session, my_generation=0)`: append skips `_cancel_stream` write + closes stream on arrival when superseded; `aborted` True when superseded (drain-retry can't resurrect zombies); statement-level TOCTOU residual documented as bytecode-width bet. Cleanups: wrapper backstop routes through `_compaction_bailed` (single failed-end emitter); impl derives `trigger` locally (param dropped; pinned test → 4-arg); module-level `_seed_two_messages` killed 5 fixture copies; end-branch broadcast gated on `changed` set ONLY in the restore arm (superseded owner-end unlatches without broadcasting — sanity's refinement, the snapshot is only the activity pair). DECLINED with ruling: centralizing the 3 command-window enqueue refusals (per-surface adapters — dict-flag vs queue.Full; central refusal can't signal re-park vs queue_full without a tri-state contract across 7 callers). fix-sanity round-2 usage: 2 refinements + 5 gaps (spec surface, broadcast arm, TOCTOU width, pre-existing main-loop sibling noted OOS, wiring test added).

**Round 6 (2026-07-16, unprimed high on the COMMITTED branch diff f92644a3): 6 correctness + 4 cleanups (+1 cut at cap), 0 refuted — trend 15/6/6/4/4/6, the uptick. Composition: [0][6][3] manufactured by rounds 4-5's fixes (_sendAbort added round 5 without interjection-path analysis or the coordinator pane; the round-5 owner-guard on notify rested on a FALSE premise — _fire_notify_targets has ONE call site, successors never notify, so the "duplicate" it prevented never existed and it created permanent notification loss); [1][4] latent in the round-3 park redesign (client-bound-vs-park seam); [5][2] older originals. Review itself flagged [0]/[6] + [1]/[4] as seam mirrors → seam-level fix demanded.**
- **Seam replacement: park-and-abandon → DEFER-AND-DRAIN.** Park's fatal property: it encoded "client disconnected" as "message retracted" — true only for composer ✕-aborts; every bounded caller (coordinator_client + console proxy timeout=30, SDKs, stock proxies) TIMES OUT and its message was deterministically dropped for the whole window ([4]); the compensating client machinery was itself racy ([1] one-shot sendAbortMs sample) and over-broad ([0] _sendAbort fired on the interjection path → dismissed messages dispatched anyway + "Connection error" shown). New contract: /send in a command window → `_PendingSend` registered on `ws._pending_sends` (under ws._lock) → IMMEDIATE `{"status":"queued","msg_id"}` (existing shape — bind/DELETE/promote client machinery needed ZERO new statuses) → per-ws single-flight **daemon-thread** drain (`ws._pending_drain`) dispatches full-fidelity on window close. Shared `_make_dispatch_attempt()` factory = ONE dispatch implementation for route + drain (session re-capture per attempt, cross-user/attachment guards, send_id threading, spawn_metrics folded in — fires for drain dispatches too, hook signature loosened to `Request | None`). Drain claim discipline: pop-under-lock immediately before dispatch, re-insert on rejection → DELETE fall-through (marks only in-list entries) can never "remove" an in-flight dispatch (claimed→not_found→"already sent"→eventually true). `defer_fidelity=True` refuses the interjection fallback for oversized (>2000 silently truncates!) / attachment entries INSIDE _enqueue (atomic under ws._lock) → wait-for-slot → fresh spawn; NO give-up bound (queued ack never silently dropped while ws lives); ws._closed drops remainder (docs state at-most-once/node-local/in-memory explicitly). DELETED: park loop, is_disconnected abandon, 20-collision loop, sendAbortMs export+both-pane usage+600s bound, _sendAbort wiring+composer_queue call. Retract-with-attachments gap (sanity): chips consumed at queued ack; retract discards attachments → client stashes `_deferredAttachments` count pre-bind, composer_queue "removed" arm shows explicit discarded notice.
- **CRITICAL test-harness gotcha: asyncio drain task DIED under TestClient** — the fixture's TestClient is NOT context-managed → each request gets its own short-lived portal event loop → create_task'd drain destroyed with it (production uvicorn would mask this). Converted drain to daemon THREAD (dispatch machinery is fully synchronous; thread lifetime independent of any loop; codebase worker idiom). Lesson: loop-affinity of background tasks is a real seam — thread beats task when nothing awaits.
- Point fixes: [3] notify UN-GATED in _run_initial finally (workstream-scoped outward signal vs slot-scoped UI stamps; sole-call-site evidence in comment; pin test via class-level wedged _FakeSession.send + force-abandon — guards against the tempting symmetry "fix"); [5] _run_compact snapshots prev ws.state, owner-gated finally restores `error if prev is ERROR else idle` (reaper ERROR carve-out cited; pin test ["thinking","error"]); [2] duck-typed fallback: `turnstone/core/compaction_render.py` `render_compaction_event_as_info()` (TerminalUI delegates byte-identically; _compaction_event falls back when on_compaction missing, UNCONDITIONALLY incl. superseded OK ends — the swap really committed, sanity's catch; on_info ALSO getattr-guarded — TestPreHookUICompat's minimal duck UI has neither); pre-1.8 SSE clients = DECLINED dual-emission, CHANGELOG "Breaking (1.8)". [7] emitter-stamped `notice` bool on failed ends (single policy site in _compaction_event; cli helper + conversation.js mechanical, conversation KEEPS pane-local `owns` clause — /resume restarts generation counters so superseded=false stale ends are reachable; HAND-SYNCED comments deleted; SDK py+ts field; openapi NOT touched — SSE schemas don't ride it). [8] resetCompactionHolder reuse. [9-cut] _renderedSystemEventIds constructor hoist (replayHistory's fresh-Set at :2748 KEPT — wipe-reset, not lazy init; sanity caught the miscount). [10] DECLINE strengthened in session_worker docstring (race claim scoped to pre-lock checks; cost = tri-state contract, not atomicity).
- fix-sanity round-4 usage (2 agents ~292K): 3 refined items + 6 gaps, all folded — kept abandoned-worker tests I'd wrongly slated for deletion (they pin _run_cmd owner guards, NOT the park), caught send_id-only-when-attachments (mint uuid4 for pending msg_id), superseded-OK-end fallback arm, the owns-clause drop, replayHistory reset, retract-strands-attachments, durability-contract docs gap, notify + ERROR-restore pin gaps.
- New tests: 8 defer-matrix tests in test_server_authz (immediate-queued+oversized-fresh-spawn, attachments-after-release, quick-command defer, retract-never-dispatches+dequeue-fall-through, arrival ordering, force-cancel-releases-drain-while-zombie-wedged, ws-close-drops+drain-exits, post-swap re-capture, rejection→wait→fresh-spawn via queue_raises knob) + notify pin + ERROR-badge pin; _FakeSession gained send_gate/queue_raises/dequeues; TestCompactionNoticeStamp (5 stamp tests) + 3 fallback tests in test_cooperative_compaction; JS pin REPLACED with GONE-assertions (sendAbortMs/_sendAbort absent BOTH panes + flat 15000 + _deferredAttachments present).
- **Round 7 = xhigh per the maintainer (seam replacement = wider blast radius). Convergence counter still 0. Step-back ceiling DEFERRED to round 9 for THIS campaign (the maintainer, 2026-07-16): sanity only arrived at round 4, so rounds 1-3 were the unvetted-fix era the ceiling exists to detect — future campaigns get sanity from round 1 and keep the standard 8-9 ceiling.**

**Round 7 (2026-07-16, unprimed xhigh, 26 agents ~2.48M tokens on committed diff 216c47eb; fixes
committed as c463f898 2026-07-17, 19 files +1065/−201, full suite 9486 green): 7 correctness + 7
cleanups, 0 refuted — trend 15/6/6/4/4/6/7, counter still 0. Composition 5/7 fix-era, ALL in
round-6's day-old drain seam or its interactions — but the defer CONTRACT took zero hits (immediate
ack, claim discipline, DELETE fall-through, at-most-once all held under 2.5M tokens of adversarial
reading). Verdict: seam COMPLETION, not step-back — three matrix rows were never enumerated: crash,
competing-spawn-paths, client settle.** Fixes (fix-sanity review run vetted: 6 refined, 8
chokepoints, 9 gaps — ALL folded):
- C1 crash row: per-iteration try around claim+attempt, `claimed` flag gates re-insert-at-head (a claim-section crash must not duplicate the entry), ~1s backoff, continue. Sanity KILLED my handoff-respawn (Thread.start fails under the exact exhaustion that gets you there; route stays the SINGLE drain-spawn site → single-flight structural, recovery = barrier arm's ensure-drain on next /send). `_PendingSend` docstring states the invariant both sides depend on: **drain not alive ⇒ nothing claimed**.
- C3 order barrier: /send route pre-checks `pending or drain-alive` under the SAME ws._lock acquisition that appends (`_defer_send(require_barrier=)` — one helper, two triggers, closed-404 inside). Drain-alive term covers the claimed-entry window. Spawn-path rulings written at each site: adapter = body pre-check → return False (sanity caught my `raise queue.Full` — a body-raise escapes uncaught into the create handler; only enqueue closures may raise it); wake gate = pending-sends yield (lockless, benign both directions) + **drain's clean-exit re-runs the gate (trigger="drain-exit")** — sanity found the strand: a list emptied by pure RETRACTION never runs a turn, so no worker-exit backstop ever re-arms the yielded wake; retry-after-rewind = accepted overtake (explicit user action, comment at _interactive_dispatch_retry); init/create = fresh-ws-by-construction comment; /command = non-row (window the drain parks behind).
- C4+CL3 client settle: queued response gains `deferred:true` (SendResponse + openapi-server regen — openapi-console regen pulled unrelated drift AGAIN, reverted, still a separate follow-up); `bind(el,msgId,{deferred,attachedCount})` documented seam (expando dead, dataset-backed); onIdleEdge skips deferred AND unbound chips; settle SPLIT by arm (sanity: uniform promote re-creates C4 one arm over): fresh spawn → `message_dispatched{msg_id}` → promote; interjection fold-in → `{folded:true}` → clear deferred flag ONLY (DELETE still genuinely removes from the interjection queue until the seam drains; chip resumes normal lifecycle). Emission lives in _make_dispatch_attempt's defer_fidelity success arm (cfg+ui in scope, both arms one site, drain stays endpoint-agnostic) via best-effort _emit_send_ui — an emission crash inside attempt would otherwise re-insert and DOUBLE-SEND. Gap G1/G2: queuedEl-absent+deferred in BOTH panes retro-converts the optimistic bubble to a real queued chip (idle-thinking pane no longer renders a parked message as sent).
- CL1→A4 poll economics: after non-window rejections, one 0.25s pace + cheap flag-wait (`_worker_running and kind!="command" and not retracted and not closed`) — one dispatch attempt per slot-state change, no 4Hz lock churn for a turn's length.
- C2: SessionUI.on_compaction protocol member got a REAL default body = render_compaction_event_as_info(payload, self.on_info) — a Protocol `...` stub is inherited as a real method by explicit subclasses, defeating the getattr fallback for EXACTLY the pre-1.8 embedders it served (audited: TerminalUI overrides byte-equivalently; eval NullUI duck-typed own no-op; no runtime_checkable/isinstance uses). Both compat routes converge on the shared renderer.
- C5→P1: `_coerce_event_id()` module helper (int-and-not-bool) at THREE sites — marker stamp 7850, on_system_turn→save_message 5712 (sanity found this confirmed-identical sibling), _ui_event_id 3181 (free uniformity, kills the symmetry re-find). Cites parse_checkpoint_watermark.
- C6→P2: quick-command backstop 60s→25s (strictly under console proxy's 30s so `running` can traverse — same bounded-caller class round 6 fixed for /send, re-found for /command); interactive.js gained the `running` info arm; 5 stale 60s refs swept (grep). C7→P3: /resume `history` SSE event = FICTION deleted; real contract = clear_ui + REST /history re-fetch; /send docs section also de-fictionalized (documented "busy" status /send never returns; full status enumeration + deferred).
- CL2 scroll only in DOM-appending end arms (design lens overrode coverage lens: removal needs no follow-scroll); CL4 wait_until(timeout=8.0) replaced _wait_for (17 sites); CL5 priority field dropped; CL6 first dup session-check dropped; CL7 _combine_queued_items inlined.
- New tests: 6 drain-matrix additions (crash-requeue-retry, persistent-crash+retract-frees-drain, fresh-send-defers-behind-CLAIMED-entry via gated-attempt swap, drain-exit-re-arms-wake (monkeypatched gate records triggers), message_dispatched fresh arm, folded arm via send_gate choreography); wake-yield unit pair in test_idle_nudge_watcher (**_FakeWorkstream needed _pending_sends — the gate reads it on every ws now**); B1 explicit-subclass pair + bool-marker + _coerce unit in test_cooperative_compaction; on_system_turn-bool test in test_sse_cursor_resume; JS pins REPLACED (expando GONE-assertions + full settle-protocol pin matrix).
- Deliberate doc bet: message_dispatched described in api-reference PROSE (defer contract paragraph, "panes receive") but NOT added to the SSE event reference — pane-tier like message_queued; round 8 may flag the asymmetry.
- **The maintainer live-tested the branch 2026-07-17: happy path functional.** D3 nit for the round-8 fix cycle: compaction card wears --magenta = RESERVED for MCP (.scope-mcp) → proposal --blue/--blue-glow (only unclaimed in-transcript accent; green implies done-while-running; blue's other uses are admin-surface only), 4 decls in chat.css + comment; alt = mint teal/orange token (light+dark + chip-contrast ≥0.15α).
- **Round-8 queue (the maintainer 2026-07-17, from the time-constants audit — pass into fix-sanity WITH the round-8 findings, provenance=self-found):** D1 = 25s command backstop < 30s console proxy timeout is a two-process comment-only inequality → pin test reading both literals (+maybe named constants); D2 = _preBindSettles cap-8 is a fixed budget on unbounded input (8 other-tab settles in one POST round-trip evict the raced settle → stuck deferred chip at the cap boundary) → sanity dispositions TTL vs keyed eviction vs justified residual. Time-constants taxonomy for the reviewer brief: class 1 pacing (drain 0.25/1.0 — no correctness dependence, latency-only), class 2 protocol bounds justified elsewhere (25s↔proxy 30s, client flat 15s↔server answers-within-RTT), class 3 fixed budgets on unbounded inputs (cap-8). Zero sleep-as-synchronization sites server-side; tests synchronize on Events + wait_until, never sleep-to-sequence.
- Test-fake gotcha #2 (round-6's _cancel_event repeated): the barrier reads `ws._pending_sends`/`ws._pending_drain` on EVERY /send — test_server_attachments_endpoints' 3 MagicMock ws stubs auto-created truthy attrs → all 9 sends deferred behind a phantom list (same class as their existing `_closed = False` comment). Rule: any new unconditional ws-attribute read on a hot route = sweep ALL MagicMock/SimpleNamespace ws stubs (authz _FakeSession, attachments _wire_ws ×3, nudge _FakeWorkstream).
- Spawn-wedge latent (all-dispatcher, pre-existing, found during round-7 self-review): session_worker.send left `_worker_running=True` if `Thread.start()` itself raised — flag's ONLY clearer was the never-started thread's finally, so the wedge was **operator-gated** (ws looked IDLE, every send queued behind a nonexistent worker, until force-cancel; after unwedge, delivery = next real TURN, turn-robust: send() flushes _queued_messages on EVERY exit path — 6383 post-tool seam, 6141 end-of-turn flush which `continue`s so the model ANSWERS them, all cancel/error exits). **FIXED on the maintainer's explicit instruction 2026-07-17** (own commit, after c463f898): identity-guarded rollback of (worker_thread, _worker_running) under ws._lock on start() raise + re-raise (NOT return False — the drain's crash handler is exception-shaped and a False would masquerade as queue_full; wake gate's refused-arm labeling stays honest); worker_kind left stale (documented stale-tolerated). Test: _ThreadNS shim (never patch threading.Thread globally) + recovery re-dispatch.

**Round 8 (2026-07-17, unprimed xhigh, 23 agents ~2.44M tokens on d3028234): 14 distinct = 7
correctness (6 CONFIRMED + 1 PLAUSIBLE) + 7 cleanups, 0 refuted — trend 15/6/6/4/4/6/7/7, counter 0
for the 8th round. Composition 6/7 fix-era. NOT designated step-back — the maintainer reaffirmed
their ruling (2026-07-17): the ceiling/step-back decision point is ROUND 9 because sanity only
joined at round 4 (rounds 6-8 ≈ sanity-rounds 2-4, discovery tail expected); I wrongly tried to
invoke it at 8 per my round-7 unilateral commitment, corrected. The fix plan is the ORDINARY
cluster-by-seam discipline (2+ findings in one seam → fix the seam once against the matrix), which
here means obligations become primitives:** R1 _defer_send t.start() INSIDE lock, no rollback,
phantom entries (the d3028234 class at the SECOND spawn site — d3028234 shipped without the sibling
sweep, a pattern-propagation violation); R2 NO saturation bound on _pending_sends (old _QUEUE_MAX=10
backpressure lost → OOM + turn amplification — the resource row round 6 never enumerated); R3
/command catch-all swallows d3028234's raise → 200 ok for never-run commands; R4 wake gate one-term
(drain-alive missing — the pair applied 2-of-3 sites); R5 retro-convert + retract → stuck-busy
composer (no worker ⇒ no state_change ever); R6 _compaction_bailed unguarded on_error BEFORE end
emit → frozen bar (hook-can-raise class); R7 = D2 confirmed with SHARPER scenario (burst FIFO
settles put OUR raced settle at the eviction head — my "extremely unlikely" was wrong). Plan
(round8_fix_plan.md; sanity review run STOPPED by the maintainer over the step-back framing,
relaunched clean as review run → revise-plan: 9 refined, 8 chokepoints, 6 gaps — LOAD-BEARING catch:
porting d3028234's outside-lock start to _defer_send would have CREATED a double-drain race (the
slot is is_alive()-gated, false for constructed-unstarted threads, unlike session_worker's
flag-gated readers) → start stays INSIDE the lock with a why-differs comment; agents conflicted
(inside-lock vs ident-eligibility), reconciled to inside-lock, ident term skipped as dead logic.
Other folds: _PendingSend MOVED to workstream.py (runtime import, kills the TYPE_CHECKING question,
co-locates invariant with the predicate); T2 widened to guard _compaction_event's dispatch tail
(raising SUCCESS-end would fabricate a failed end after a committed swap); U1 stamp centralized in
setBusy(b, source) default-"server" (unstamped future writers fail safe); U3 helper owns the FULL
status dispatch incl. the queue_full idle-pane cleanup (S2 makes queue_full the standard saturation
answer — without bubble-removal + guarded busy-restore it re-created R5 one arm over); P2 proxy
constant at BOTH constructions (startup + mTLS re-create :5467); G6 edit-resend settle drop DECLINED
with site ruling comment (original-strata, round-9 confirms). IMPLEMENTED 2026-07-17:
_make_drain_thread test seam; stub-sweep rule applied (attachments ×3 lambda-False barrier, idle
_FakeWorkstream real impl — the barrier is a METHOD now, MagicMock auto-attr = truthy trap repeats);
3 pre-existing cross-user pins updated for the helper move (interactive ×2 + test_coordinator_page
×1 — full-suite run 1 caught the coord one). **COMMITTED d4254698 (24 files +1004/−385, suite 9494
green). ROUND 9 = xhigh (my recommendation over the maintainer's offered high: decision round +
R4/R7 were xhigh-only finds + 0 refuted across 8 rounds means the extra effort finds real bugs; the
maintainer delegated, xhigh default stated, no objection before launch). THE CEILING ROUND:
correctness findings → composition read goes to the maintainer (ship-judge / cut / re-derive); clean
→ counter=1, round-10 confirm at high.** S1 Workstream.send_barrier_active() single predicate +
typed fields + WorkerKind Literal; S2 _defer_send probe-first/bounded(_PENDING_SENDS_MAX=10 cites
_QUEUE_MAX)/spawn-outside-lock-with-identity-rollback→queue_full; S3 emits via _emit_send_ui; T1
spawn-fail /command → 503 error (docs+spec+pane arm); T2 guard on_error keep order; U1 deferred
retro-convert setBusy(false) under busySource guard (kills R5 at source); U2 TTL-30s replaces cap-8;
U3 shared settleSendResponse helper (twins die); P1 delete TerminalUI override; P2 timeout constants
+ inequality test (D1); P3 magenta→blue (D3). Round 9 = the ceiling round, xhigh.

**Round 9 — THE CEILING ROUND (2026-07-17, unprimed xhigh, 19 agents ~2.32M tokens on d4254698): 7
distinct = 3 correctness (2 CONFIRMED + 1 PLAUSIBLE) + 4 cleanups, and the campaign's FIRST 3
REFUTATIONS (all deep-speculative generation-domain collisions). Trend 15/6/6/4/4/6/7/7/3 —
correctness HALVED at identical sensitivity; ZERO hits on any round-8 primitive.** N1 drain
except-arm slot-clear not identity-guarded × round-7's in-try clean-exit wake × d3028234's raising
wake → successor-nulling double-drain (the ONE un-rewritten part of the one un-primitived function);
N2 round-7's unbound-skip re-opened the non-deferred missed-edge settle (permanent queued bubble for
a delivered message); N3 PLAUSIBLE early-strata: _claim_generation's hook emission unguarded on
send()'s pre-turn path (silent message drop for raising overrides). Cleanups: /command
catch/status-less silence; _PENDING_SENDS_MAX hardcoded copy; unused _queue_full_response at the
sibling arm; dead window.createQueueController bridge. Plan round9_fix_plan.md (F1 wake-out-of-try +
identity-guarded clear; F2 helper promotes non-deferred missed-edge chips via ctx.paneIsBusy; F3
try/except the hook; F4-F7 mechanical), sanity review run. **Composition read delivered to the
maintainer per their ceiling ruling: my rec = NOT step-back (primitives held; 3 point-guards;
refutation onset = finder yield bottoming), fix + round-10 confirm at high, then ship-judge with the
evidence rather than mechanically chasing 2-clean into round 11.** Sanity review run folds (all
load-bearing): F1 needs a function-LOCAL `import threading` (module-top is TYPE_CHECKING-only → the
identity guard would NameError INSIDE the last-resort handler, masking the original exception, and
mypy is blind to it — the type-only-import-satisfies-the-checker trap, memory-worthy class); F2
keyed on POST-bind chip state not the wire flag (bind's _preBindSettles reconciliation can clear a
raced folded settle's flag — the wire-flag gate would leave that sibling cell open) + aria-busy skip
(bare promote would consume dismissAttempted mid-DELETE → contradictory notice + vanishing row); F4
must NOT copy /send's !ok pre-gate (busy rides 409, error rides 503 — a pre-gate reroutes the
working loud arms into the catch); F5 constant-share verified clean (session.py:207 runtime-imports
workstream) → PENDING_SENDS_MAX in workstream.py, _QUEUE_MAX aliases it. IMPLEMENTED 2026-07-17 +
NEW node behavioral settle harness (settleSendResponse is import-clean now the window bridge is gone
— 4-row missed-edge matrix executes under node). Gap G1 (no-chip setBusy(true) sibling) =
honest-residual comment, pre-branch verbatim. **COMMITTED 806d710c (9 files +412/−66, suite 9499
green). ROUND 10 = review run at HIGH — the confirm round (my ceiling-report rec + the maintainer's
preference; the campaign baseline measure). Clean → counter=1 → present the SHIP CASE (reviewer's
brief + evidence: 10 rounds, yield 15/6/6/4/4/6/7/7/3/?, refutation onset, primitives held) rather
than mechanically chasing round-11; correctness findings → composition read back to the maintainer
under the ceiling ruling.**

**Round 10 — THE CONFIRM ROUND, FIRST CLEAN (2026-07-17, unprimed high, 14 agents ~1.41M tokens on
806d710c): ZERO correctness — counter = 1. Trend 15/6/6/4/4/6/7/7/3/0.** 5 CONFIRMED cleanups
(2000-char cap triplicated + already drifting raw-vs-cleaned — benign direction; CHANGELOG
mega-bullet + buried Breaking notice; dead request param through SpawnMetricsHook; mock-hardening
block ×3 → helper; 2 hand-rolled polls → wait_until) + 3 refuted (send_and_wait break, DELETE
session-None gap, module-level-threading proposal — the function-local style + comment RULING STOOD,
first declined-class ruling to survive an unprimed round via comment). Cleanup plan
round10_fix_plan.md → sanity review run folds (G1 +prose sweeps + no-link list for 4 unrelated
2000s; G2 6-bullet split + Breaking→### Changed cross-referenced; G3 +2 test args + stale
coord-wires-None fixed; G4 helper EXCLUDES _worker_running — fixture 3 needs the truthy auto-Mock;
G5 timeout=8.0 + orphaned import time). **COMMITTED dab53f2e (9 files +118/−88, suite 9499 green).
BRANCH FINAL STATE: 7 commits over main (f92644a3 · 216c47eb · c463f898 · d3028234 · d4254698 ·
806d710c · dab53f2e), all gates green, reviewer_brief.md in scratchpad. SHIP CASE PRESENTED; the
maintainer chose the formal confirm: **ROUND 11 = pre-push high, on dab53f2e (2026-07-17).
Correctness-clean → counter=2 → CONVERGED under the 2-consecutive rule → push/PR on the maintainer's
word. Correctness findings → the streak resets and the composition goes back to them.** **VOID#1:
first round-11 attempt (task w04gcqvv8) — all 4 finders died mid-run (candidates:0,
verifierAgents:0); by the infra-void rule this counts as NOTHING, counter STAYS AT 1, "no findings
survived" is a crash artifact not a clean surface. The maintainer switched model → Opus 4.8, asked
to resume. RE-RUN: task was9lfiig, resumeFromRunId args "high" — cached prelim replays, 4 finders
re-run LIVE under Opus 4.8 (model changed mid-round; gate cares about full-surface coverage not
model identity, and a fresh independent perspective on a pre-push confirm is a plus). This resumed
run is the real round 11.** **ROUND 11 RESULT (2026-07-17, Opus 4.8, 8 agents ~1.0M tokens on
dab53f2e): ZERO CORRECTNESS → counter=2 → CORRECTNESS CONVERGED under the 2-consecutive rule (r10
Fable-5 clean + r11 Opus-4.8 clean = cross-model confirmation). Trend 15/6/6/4/4/6/7/7/3/0/0. 1
REFUTED (server.py:1886 `ws.worker_thread is me` worker-ownership-guard DRY complaint — consistent
w/ prior rounds' rejection of guard-extraction proposals). 1 SURVIVING finding,
cleanup-class/PLAUSIBLE/contract-unreachable: settleSendResponse call-site divergence —
interactive.js:3889 passes bare `data`, coordinator.js:2071 passes `data || {}`; latent throw at
composer_queue.js:639 (`consumeAttachments(data.attached_ids,...)` unguarded) if a 2xx body were
ever non-object JSON. NOT a live bug (/send always returns an object). Fix plan round11_fix_plan.md:
move the guard INTO the helper (`data = data || {}` at :547), de-guard coordinator, add null-body
node-harness case — both call sites become identical, latent throw closed. Running through
fix-sanity review run BEFORE implement. On implement+gates+commit (8th over main): correctness
convergence UNAFFECTED (JS leaf-helper guard relocation, cannot touch the Python concurrency surface
the campaign hardened) → push/PR on the maintainer's word.** **CONVERGED + SHIPPED TO PR
(2026-07-17): fix-sanity review run verdict=proceed (all 4 items unchanged, gaps=[]); implemented
the 3 edits; gates all green (ruff/format/mypy/tsc/byte-scan clean, 47 focused JS pass,
TEETH-CHECKED — null-body harness case red w/o the fix, full suite 9499 passed exit 0); committed
c09a4d45 (8th over main, clean msg NO attribution). The maintainer's instruction: push and open the
pull request once the gates are green. Pushed feat/compaction-visibility → origin (new branch);
opened **PR #863** against main (8 commits:
f92644a3·216c47eb·c463f898·d3028234·d4254698·806d710c·dab53f2e·c09a4d45), title "Compaction
visibility + defer-and-drain send subsystem", body = 6-seam map + 5 invariants + 11-round campaign +
reviewer focus order, NO Claude/attribution footer (repo artifact-cleanliness override of the
harness default). GATE LESSON: `cd sdk/typescript` for tsc persisted the shell cwd → the first
full-suite bg run collected 0 tests (pytest-exit 5, shell-exit 0 masked it); always read the
explicit `pytest-exit:` line, never trust the bg shell exit code, and cd back to repo root after a
subdir command. AWAITING: the maintainer's human review of #863 (reviewer_brief.md in scratchpad has
risk tiers + R1-R7 residuals + live-soak script). DEFERRED follow-up: regenerate
openapi-console.json (pre-existing drift, reverted all branch — separate PR).** **PR review + merge
(2026-07-17): Copilot left 1 line comment (conversation.js:179 — retry_in coerced with Number() but
unvalidated while sibling part/total ARE finiteness-guarded → "retrying in NaNs" on a malformed
backoff). VALID (real asymmetry in the branch's own code, NOT a #840-style false positive). Fixed
005596f1 (9th commit): validate retry_in finite+non-negative at conversation.js
updateCompactionProgress, but DIVERGED from Copilot's literal "no-op otherwise" — kept the error
text (load-bearing half), unparseable duration → "retrying (error)…" not whole-arm suppression;
happy path byte-identical; source-pin in test_conversation_js.py (house pin-style, teeth-confirmed
old form gone). Gates green (9500 passed). Replied+documented the divergence on the Copilot thread.
The maintainer's instruction: monitor CI after the push and rebase-merge once remote CI is green.
Remote CI all 16 checks pass on 005596f1 (independently re-inspected, not just watch exit; main
UNPROTECTED so the green-gate was mine to enforce; NO auto-merge — would've merged pre-CI on
unprotected main). **Rebase-merged PR #863 → main HEAD 515d372a (9 commits rebased clean onto prior
tip 82676080); remote branch auto-deleted (repo delete_branch_on_merge=true); local main ff-synced,
local feat branch -D'd.** Compaction visibility + defer-and-drain send subsystem = SHIPPED to main.
GATE LESSON 2: `gh pr view --json merged` is NOT a valid field (use state/mergedAt/mergeCommit) —
the invalid field threw exit 1 and masked that the merge itself succeeded; verify merge via PR
state + `git ls-remote origin main`, never trust a compound command's exit code.**

Related: [[project_cooperative_compaction]] (the engine this makes visible), [[project_fresh_connect_replay_completeness]] (cursor/dedup model reused), [[project_compaction_rehydration_deadlock]] (the marker row this projects).

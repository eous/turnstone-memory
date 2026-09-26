---
name: project_frontend_long_session_audit
description: "Frontend perf or wedged panes on 5000+ message sessions: four hard-failure mechanisms (07-01 audit); P0-P1 on dev via #754; P2 + windowing (#755) not on dev."
metadata: 
  node_type: memory
  type: project
  modified: 2026-09-25T04:01:11.606Z
---

2026-07-01 audit (6 parallel slice agents, all load-bearing claims re-verified
against source) after a live understone grind session (5000+ msgs, several
compactions) had UI elements stop rendering with a healthy backend. Full brief
with file:line detail + P0-P3 fix plan: `docs/design/frontend-long-session-perf-audit.md`
(local-only; line numbers snapshot of c71cc749).

**Not one bug — four independent hard-failure mechanisms, ranked:**
1. Unguarded pipeline wedge (MOST LIKELY): `interactive.js` onmessage/handleEvent
   have no try/catch and `stream_end` clears streaming refs AFTER finalize — any
   renderer throw (empirically reproduced: ~4KB of nested `"> "` overflows
   renderMarkdown's unbounded recursion) permanently wedges the pane; the same
   poisoned message aborts replayHistory past its position. coordinator.js:1660-1712
   already has the exact fix pattern (try/catch + textContent fallback +
   unconditional ref-clear); interactive.js never got it.
2. Rebuild-vs-live race (certain to have run): clear_ui/replay_truncated refetch
   + replaceChildren while live events keep painting → events lost in the window,
   `currentReasoningEl` unguarded, refs never nulled → deltas into detached nodes.
3. HTTP/1.1 6-conn exhaustion at ≥5 open panes (documented in-code app.js:2105) —
   all new fetches pend forever while existing streams paint; #540 resolved → HTTP/2
   is canonical answer, don't re-litigate.
4. Global stream ignores node_snapshot/replay_truncated (app.js:1524) → permanent
   roster drift after long gaps.

**Structural steady-state findings:** transcript DOM append-only (no windowing —
compaction never trims UI); `_agentCards` Map never pruned (detached subtrees);
per-TOKEN O(N): removeThinkingIndicator full-container querySelector + 4 forced-
layout reads in scrollToBottom + reasoning `textContent +=` (quadratic) +
streamingRender full re-parse/innerHTML per rAF; column-flexbox scroller with zero
contain/content-visibility anywhere (CSS pair = biggest win-per-line); every
ws_state → synchronous full rail rebuild (no debounce); coordinator
handleChildState → full tree rebuild (cheap `_updateChildRow` exists, used only
for rare events); coordinator 401 probe dead code (authFetch throws).

**Shipped in #754 (2026-07-02)** (branch `perf/webui-long-session`, two
commits: harness + fixes; designer + max-review findings folded in; from here
new commits only — never force-push per git workflow). Content: P0+P1 +
perf harness shipped: `scripts/livepass.py --perf` (new /perf/livepass.html —
real InteractivePane, real geometry/time, deterministic; MEASUREMENT RULES: no
--virtual-time-budget, no --force-prefers-reduced-motion). Measured @ n=3000:
replay 1060→292ms, re-replay 836-1071→~93ms flat, chunk path now flat vs N
(O(N)-per-chunk gone), longtask max 1080→497ms, `_agentCards` leak 4→0.
420 frontend tests green incl. 7 new pins (wedge-proof order, quiesce,
depth-cap, success-only buffer marking, caps, recovery floor, rAF fireRender).
Deferred-with-rationale: coordinator dedup-map clear (event ids storage-seeded),
verdict-badge cache (block-vs-row anchoring), rail snapshot-sharing.
Designer review passed (UX-shippable); its 2 should-fixes LANDED: omission
marker as sibling `div.conv-diff-omit` below the 240px diff scroller (was
buried inside + amber-warn failing AA), and "Session ended" toast when gap
recovery closes an OPEN pane.
Max-effort /code-review (2026-07-02): 15 verified defects in the new code —
14 FIXED (key: disconnectSSE cleanup moved to _loadHistoryThenConnect/destroy
so transport reconnects don't duplicate agent cards; REST roster resync
merge-only + r.ok gate, eviction only from stream-ordered node_snapshot;
_resetStreamingRefs on refetch-failure; replay_truncated mid-stream resync
DEFERRED to idle edge not dropped; rAF pin re-checks _nearBottom at fire +
ResizeObserver; auth.js noteVersionMismatch export for raw-fetch 401 probes;
IO unobserve in _updateChildRow; terminal _agentCards.delete REVERTED;
mermaid catch paints linkPending; verdict lookup batch-scoped; livepass
poll-loop + run-token). 1 DEFERRED: quiesce-flush double-paint needs a
server event watermark on /history (backend follow-up). GOTCHA: the
onerror reconnect pin blanks comments offset-preserving and needs literal
`r.status === 401` within 400 chars before any close(). 420 tests green;
perf gains hold (238ms replay @3000, cycles flat 94ms, 0 page errors).

**CORRECTION 2026-09-24: the P2 work below never reached dev** (`git log -S
content-visibility` finds only the vendored hljs; branch head 2d174cd7 is not an
ancestor of dev). Two of its premises also failed measurement on 09-24
([[project_composer_typing_lag]]): the per-keystroke/per-token transcript tax
was the shell grids' auto rows, not the missing containment, and its block-flow
scroller changes row spacing (sibling margins collapse: rows at 57px move to
55px), contrary to its "same ~6px" claim.

**P2 BUILT 2026-07-02 (not on dev)** on stacked branch `perf/webui-transcript-windowing`
(commit 9f67829e) → **PR #755** ("perf(webui):
bound the transcript — containment, block flow, windowing"): CSS pair (block-flow scroller ×2 +
overflow-anchor:none + content-visibility auto 80/200px, live tail exempt) +
300-msg windowing w/ `.msg-history-pager` (turn-boundary cut; scrollHeight-
delta restore — works BECAUSE the rAF pin re-checks _nearBottom at fire) +
900-row idle-edge live trim (only while pinned; agent-card sweep). Chunked
replay DROPPED (windowing obviates). KEY FACT: rewind/edit turn math is
TAIL-relative (`userMsgs.length - idx`) so windowing needs no ordinals —
pinned. Result @ n=3000: replay 28ms windowed/107 grown, storm/turn = n300
floor even at 25k nodes, longtasks 0; chunk path degraded-mode-only +180ms
at grown window (shipped = floor). 422 tests. STILL OPEN: coordinator ring
buffer, streamingRender prefix/tail split, KaTeX cache, stream-pulse
compositable, aria-live flip; **P3** infra (HTTP/2 per #540, MRU stream cap,
delegated listeners, defer katex/hljs).

Related: [[project_frontend_lshell_renovation]], [[project_sse_fanout_pending]],
[[feedback_sse_queue_not_a_bottleneck]], [[project_understone_doorgame]]

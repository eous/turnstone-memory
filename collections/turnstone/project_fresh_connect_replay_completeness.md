---
name: fresh-connect-replay-completeness
description: "Fresh-connect vs reconnect SSE replay divergence: DONE via event-id cursor resume (PRs #610/#612/#616); /history cursor becomes Last-Event-ID."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-20T16:59:21.423Z
---

**DONE — PRs #610 (in-flight tool-call render), #612 (terminal-error surface), #616 (event-id cursor resume) shipped by 2026-05-30.**

The bug: SSE had two diverging reconstruction paths — fresh connect = lossy *synthetic* snapshot (REST `/history` + `in_progress_snapshot` content/reasoning + re-emitted pending approvals); reconnect (`Last-Event-ID`) = COMPLETE per-ws ring buffer. Any event the synthetic path didn't reconstruct was invisible on fresh connect (e.g. completed-but-unsaved parallel `web_fetch` tool results, whose emit-vs-persist window is the slowest sibling's duration, not microseconds).

**Durable model (the cursor-resume fix, model B'):**
- Add nullable `event_id` (the in-memory SSE `_event_id`, not the rowid) to the `conversations` table (migration 059); `save_message` stamps it; seed `_event_id` from `SELECT MAX(event_id)` on UI init (else post-reopen ids collide).
- `/history` returns RESOLVED turns only (excludes the trailing in-flight turn — reverses #610's render-orphan-from-history) + `cursor = last RESOLVED-turn boundary` (NOT `max(saved event_id)` — out-of-order parallel result saves race a mid-turn cut and drop a sibling).
- Client sets `Last-Event-ID = cursor` on initial SSE open, so the FIRST connect flows through the EXISTING `register_listener_with_replay` delta path. `/history` (resolved) and the delta (in-flight) are DISJOINT → no dedup. Uniform "snapshot + fast-forward": the orphan turn replays WHOLE through live handlers, so no `replayHistory`/render-flag changes.
- ALL in-flight event types are buffered including `plan_review` (enqueued in WebUI/coord UI subclasses, NOT the base — easy to miss). Awaiting-approval and plan-review fast-forward through the delta, NOT special cases.
- ONLY gate = buffer-liveness (`can_replay_from(cursor)`: buffer non-empty AND earliest ≤ cursor+1). FALSE (reloaded/evicted) → include in-flight committed state + cursor=null + the synthetic snapshot/re-emit floor (now the exception, not the rule). Content/reasoning snapshot STAYS (delta carries discrete events; token volume would be huge).
- Cursor is a per-ws scalar in the node's event_id space, forwarded verbatim as SSE `id:` through the proxy shim (transport-agnostic). Fan-in (#540) folds it into a global/composite cursor downstream.

**Lessons:**
- Unifying fresh+reconnect needs cursor BRIDGING; a pure synthetic snapshot was insufficient (it races live state — the built-then-dropped `_ws_inflight_tool_results` re-emit map was the wrong framing).
- `make_history_handler` is SHARED by interactive (`app.js`) AND coord (`coordinator.js`) — a change to it must update/guard BOTH (#616 shipped a coord regression: coordinator.js never read `hist.cursor`). `console/static/app.js` is yet a third distinct client.
- A `save_message`-stamping change reaches far-flung mock-UI+real-storage tests — run the FULL `pytest -m "not live"`, not a targeted sweep (a MagicMock `_event_id` poisoned the INSERT in CI).

Accepted/deferred gaps: non-terminal mid-turn errors (no durable source); `message_queued` indicator on a fresh/fan-in pane (needs client render-on-replay + dedup, not server-only); 50k-buffer eviction edge.

Related: [[project_streaming_sse_resume]] (the snapshot), [[project_sse_fanout_pending]] (#540 fan-in; now also holds the envelope breadcrumb).

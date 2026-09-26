---
name: feedback_sse_queue_not_a_bottleneck
description: "Tempted to cite the 500-cap silent-drop SSE listener queue as a risk: don't; stress tests never pass ~10 depth, backpressure is Last-Event-ID replay."
metadata: 
  node_type: memory
  type: feedback
---

The per-listener SSE queue (`_DEFAULT_LISTENER_QUEUE_MAX = 500`; `_enqueue` does
`with contextlib.suppress(queue.Full): lq.put_nowait(data)`, i.e. silent drop on
full) is NOT a real-world bottleneck. Even worst-case stress tests never pushed
an **active tab's** queue above ~10 depth — it drains far faster than events
arrive.

**Why:** I repeatedly raised SSE queue overflow / silent event-drop as a risk in
design discussions (high event volume from e.g. 100 tool calls × parallel task
agents). The user has stress-tested it and it doesn't happen; bringing it up
again is noise.

**How to apply:** Don't cite the 500-cap silent-drop as a concern for high event
volume. The active-tab consumer keeps up. If a real backpressure case ever
arises it'd be a *backgrounded/disconnected* tab (reconnect/replay territory),
not the live queue — and that's handled by the `Last-Event-ID` replay path, not
by worrying about the cap.

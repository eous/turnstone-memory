---
name: project_streaming_sse_resume
description: "Mid-stream refresh losing streamed content: DONE via per-turn inflight buffers + in_progress_snapshot on replay; the on_turn_committed reset is load-bearing."
metadata: 
  type: project
---

**DONE.** Mid-stream page-refresh on a coord/interactive workstream lost streamed content/reasoning (and left the composer stuck in send-mode because `state_change` was never replayed).

**Chosen fix — Option A.2 (in-memory per-turn snapshot on replay):**
- Per-turn inflight content/reasoning buffers (`_ws_inflight_content`/`_reasoning`, 256 KiB cap each), SEPARATE from the existing multi-turn `_ws_turn_content` (which accumulates across the whole `send()` loop and is wrong as a snapshot source).
- Reset at `on_turn_start` (top of the loop). The `on_turn_committed` reset (post `messages.append`) is LOAD-BEARING — without it, a refresh during inter-turn tool execution double-renders the just-committed turn (history list AND snapshot).
- `register_listener_with_in_progress_snapshot()` copies the buffer under lock; `make_events_handler` yields a one-shot `in_progress_snapshot` after replay, with per-turn `_seq` dedup against live events (stripped server-side).
- Also replay a `state_change` in the per-kind replay tail (fixes the stuck-composer regression).

**Fallback — Option B (event ring buffer + Last-Event-ID):** on the shelf. Switch to B if: client-side content-gap detection becomes common after A; product wants "second device sees in-flight tokens from before connect" beyond the current turn; or the 256 KiB cap bites on long responses. (Note: B was later partially adopted for discrete events — see [[project_fresh_connect_replay_completeness]] cursor resume — but the content/reasoning SNAPSHOT from A.2 stays, because pure delta re-streams thousands of token events.)

Forward-compat: the per-turn inflight buffer only holds the current turn, so cross-turn reasoning persistence is purely additive.

Related: [[project_fresh_connect_replay_completeness]], [[project_sse_fanout_pending]].

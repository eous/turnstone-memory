---
name: project_resume_nudge_wake_seam
description: "Resume nudge retired + user channel never wake-eligible (2026-09-05): reopen-wake raced the user's message into the interjection seam; PR #1110 from branch fix/resume-nudge-wake-seam."
metadata: 
  node_type: memory
  type: project
  modified: 2026-09-06T00:54:42.226Z
---

**The bug (2026-09-05).** Two reports were one mechanism. `ChatSession.resume()` queued the
`resume` metacognition nudge on the `"user"` channel outside any send — the ONLY such
producer — and `"user"` was a member of `WAKE_PENDING`, so the post-reopen IDLE transition
spawned a synthetic empty wake turn that held the worker slot while the user's real message
arrived; the message drained at the tool seam as a `user_interjection` ("additional context
… incorporate if relevant"). Channel gateways hit it on nearly every reopen because the
route restores synchronously before the gateway's own send lands.

**Rulings baked into the fix (PR #1110, branch `fix/resume-nudge-wake-seam` off `f0d4f957`,
worktree `<worktree>` with its own `.venv`):**
- The `resume` nudge is retired outright — the immutable memory index (#1022) plus per-turn
  memory pointers already put saved context in front of the model. `NUDGE_RESUME`,
  `_NUDGE_MAP["resume"]`, `MEMORY_NUDGE_TYPES`, `SYSTEM_TURN_SOURCES` all drop it; the
  first-message gate in `nudge_allowed` is now unconditional.
- `"user"` is NOT wake-eligible: `WAKE_PENDING = {"any", "wake"}`. A user-channel advisory
  advises the user's own turn and is queued inside the send that drains it; it must never
  manufacture a synthetic turn. Never re-add it.
- Legacy persisted `_source="resume"` rows keep their frontend label (`utils.js`
  `OPERATOR_SOURCE_LABELS`, same precedent as `start`); no backend reader validates a
  persisted `_source`, so no migration.
- Mid-turn interjections are untouched: separate queue, same drain seams, same
  interjection-owns-the-seam handoff. A message landing mid-turn during an EXTERNAL-event
  wake (watch fire, background-shell exit, coordinator idle nudge) is still an ordinary
  interjection — deliberate non-goal.

**Accepted residual (mapper-flagged, not fixed):** a `"user"` entry co-queued with an
`"any"`/`"wake"` entry now survives the wake instead of riding it (the wake's
`_emit_pending_user_nudges` consumes the stash, never `USER_DRAIN`) and lands on the next
real send; unreachable in production since every `"user"` producer drains in-send. Pinned
by `test_wake_leaves_user_channel_entry_for_the_next_real_turn`.

**Process notes:** The maintainer asked for a plan in `docs/design/` plus a dataflow-mapper pass
before editing (`docs/design/resume-nudge-wake-seam.md` + `-dataflow.md`, local-only); the
mapper closed every edge and caught the untracked probe test that would have broken
collection. One review round (bug/sec/perf 0, quality 2 → 1 refuted, 1 nit re-wrap).
The maintainer: skip further rounds when a review returns only minor items.

Related: [[project_idle_tasks_nudge]], [[feedback_finish_the_fix_spree]],
[[feedback_prose_rewrap_on_edit]], [[project_902_memory_index]].

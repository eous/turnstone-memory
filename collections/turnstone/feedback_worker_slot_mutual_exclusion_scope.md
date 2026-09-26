---
name: feedback_worker_slot_mutual_exclusion_scope
description: "Deciding if a command can run off the worker slot (#856): the slot also guards UI emission and worker-read flags; if it emits, use a REST endpoint instead."
metadata: 
  node_type: memory
  type: feedback
---

When classifying whether an operation can run CONCURRENTLY with a live worker
(off the worker slot), "safe" is NOT "doesn't mutate the same data the worker
mutates." The worker slot provides mutual exclusion over a WIDER surface, and a
correct hazard model must cover all of it:

1. **Data writes** — the obvious one (self.messages, session identity, config).
2. **Worker-READ state** — flags/fields the streaming loop SAMPLES mid-turn. In
   turnstone: `self.show_reasoning` (/raw) and `self.debug` (/debug) are read
   per-chunk by the turn loop (session.py ~6779/6885/6902); flipping them off-slot
   corrupts the in-flight render (/debug injects raw-delta rows into the assistant
   stream). I missed this class entirely — I only asked "what does the command
   WRITE that the worker writes," never "what does the command write that the
   worker READS."
3. **UI emission** — the pane is shared mutable OUTPUT. Any off-slot command that
   calls ui.on_info/on_error/on_rename interleaves with the worker's live token
   stream (session_ui_base _enqueue flushes the batch and fans the row mid-stream).
   The slot's mutual exclusion is what kept command output from splicing into a
   turn. This bites even READ-ONLY commands (/history, /workstreams) — being
   read-only does not make emitting-to-the-transcript safe.
4. **Completion timing** — a slow off-slot op that finishes AFTER a successor turn
   starts injects its late UI/writes into that turn. The slot path guards this with
   `if ws.worker_thread is me` (the abandoned-worker guard); an off-slot path has
   no equivalent and needs its own epoch/generation check.
5. **Infra** — off-loop execution belongs on a DEDICATED executor, not
   asyncio.to_thread's shared default pool (a wedged op holds a slot past any
   timeout — threads aren't cancellable — and exhausts the process-wide pool that
   tenant_check/mgr.create/SSE fall-through all share). And thread-spawn failure
   must answer LOUD (503), not fall through to 200-ok.

**Consequence for design:** if an operation must emit to the transcript or read
worker-sampled state, it CANNOT safely run off-slot by construction — findings 3
(UI interleave) and the identity race have no clean fix inside the off-slot model.
The correct mechanism is then a proper REST endpoint that returns DATA rendered
out-of-band by the frontend (the /rewind//retry lift precedent), or a client-side
toggle — not a slot-bypassing "command." See [[project_856_command_slot_bypass]].

**Why:** #856 Phase 1 (feat/856-safe-command-slot-bypass) shipped a confident per-command
thread-safety audit that was "verified, not assumed" — and a high review found 5 CONFIRMED + 1
PLAUSIBLE correctness findings because the audit's hazard model only covered class 1. The maintainer
asked for a review up front precisely to catch this before PR; it did. Relates to
[[feedback_review_convergence_methodology]] (correctness findings → composition back to the
maintainer; seam redesign not per-finding patches) and [[feedback_freeze_tree_during_review]].

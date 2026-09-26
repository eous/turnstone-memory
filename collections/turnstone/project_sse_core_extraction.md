---
name: project_sse_core_extraction
description: "Extracting the SSE recovery core shared by interactive.js and coordinator.js: RULED 1.9 by the maintainer (2026-07-24), not a late-1.8 capstone; precedes mcp v2 #679."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-24T23:57:21.066Z
---

**RULED 2026-07-24 (the maintainer): the SSE-core extraction lands in 1.9, NOT as a
late-1.8 stabilization capstone.** Reason: merging the two recovery
implementations into a shared JavaScript package is a high-risk change to make
exactly when both surfaces are finally reaching stability. Do not re-open the
capstone-vs-1.9 question without new information — Claude argued capstone
(acceptance suite freshest now) and was overruled on risk, correctly.

**Sequencing in 1.9:** extraction PRECEDES mcp v2 (#679), so coordinator MCP
(#725) builds on one core rather than two.

**What it targets — the parity tax.** The recovery/transport layer is nearly
parallel in `interactive.js` and `coordinator.js`, and every campaign lands
twice. #900 is the specimen: a session whose whole purpose was finishing the
#894 backport generated NEW backport debt in the reverse direction before it
landed — a missing negative pin ported FROM coord, a retry-jitter change owed
TO coord.

**Why the ports are never mechanical (the load-bearing insight).** The two
clients solved the same problem with DIFFERENT mechanisms, and each mechanism
makes a different set of bugs reachable:
- interactive has the replay quiesce (`_replayQueue`) — in-await events buffer
  and flush AFTER the render;
- coord has `refetchSeq` / `refetchesInFlight` — no buffering; in-await events
  paint BEFORE the wipe and die with `replaceChildren()`.
So a defect can exist in one client BECAUSE of its mechanism and be
unreachable in the other BECAUSE of its absence (the #900 r1 `bug-1`
duplicate-flush is exactly this), and each side carries genuine
not-applicable-here rulings. A port that assumes symmetry is what costs the
extra review rounds.

**The cost that decided the ruling:** extraction means PICKING one mechanism.
Whichever loses, that client's entire bug history reopens against the winner's
semantics — a re-derivation, not a merge — across the two most ruling-dense
files in the tree.

**What does NOT decay while it waits:** the acceptance suite (20
negative-controlled browser scenarios in `scripts/recovery_e2e.py`, E-family
interactive + G-family coord) and the at-site rulings are executable/committed
artifacts. Only session context decays, and it rebuilds from them cheaply.

**Known harness debt to carry in:** E↔G mirroring is currently INCOMPLETE —
E5 mirrors G5, but E6 (await-window render gate) and E7 (destroy
invalidation) have no coord counterparts. E7 likely cannot have one in the
same shape, since coord's destroy aborts in-flight fetches via `histCtrls`
instead of invalidating a load token.

Related: [[project_894_coord_over_rewind]], [[project_890_clear_ui_guard]],
[[project_884_history_coalescing]], [[project_sse_truncated_resync_hole]].

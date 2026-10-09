---
name: project_988_owner_lease
description: "#988 workstream owner lease (branch feat/988-workstream-owner-lease off dev 3a046487): the maintainer's rulings 1-20, path C decisions D1-D6, and the local docs to read before coding."
metadata:
  node_type: memory
  type: project
  modified: 2026-10-05T17:27:39.801Z
---

Scope and research for #988 (one live writer per durable workstream incarnation) were done on
2026-10-02. Read the LOCAL scope doc `docs/design/988-owner-lease.md` first; it links five verified
research reports under `docs/design/988/` (storage write inventory, backend lock map, session
persistence lanes, admission/routing map, a PG+SQLite spike). Both live only in the main checkout and
are git-ignored.

Design in one paragraph: lease columns on the `workstreams` row (boot-scoped holder per
`SessionManager`, holder node, fencing epoch, database-clock expiry), acquired at create/open before
the session is visible, renewed by a per-manager keeper, released after the final durable write.
Every session-owned write presents an immutable fence snapshotted at admission (beside the existing
`persist_ws_id` snapshot) and storage checks holder+epoch under the parent-row lock it already takes.
SQLite always permits takeover (single-process contract). Routing to the holder is in v1, not deferred:
browser panes never use the router, so a non-holder's refusal must lead clients back to the holder.

Maintainer rulings (2026-10-02):
1. Unfenced writes to session-owned rows are REFUSED while another live lease exists, so a forgotten
   fence fails loudly in CI on both dialects ([[feedback_designs_that_need_no_memory]]).
2. Orphan close, stale-create reaper and boot prune key on lease liveness, REPLACING the node-liveness
   heuristic (that also fixes orphaned coordinators never being reaped).
3. Identity adoption (watch restore, `--resume`, CLI `/resume` and `/new`) takes the target's lease
   through a seam inside `ChatSession.resume()`; the create-then-resume structure stays.
4. A watch whose workstream changes owner is ENDED, and the model is told why. The new holder does it
   at acquisition, since only the holder may write the conversation.

Later rulings (2026-10-03, review round 1):
5. Lease-loss retirement keeps the generic close flow: no dedicated "moved" reason for panes.
6. A session that moved off its first workstream releases that row's lease once its saves land.
   Amended 2026-10-03 (round 2, D3): the slot then STOPS non-terminal state writes to that row
   (no unfenced writes), so a reaper's close sticks and a refused unfenced state write can only
   mean a forgotten fence.

Rulings from review round 2 (2026-10-03):
7. PostgreSQL renewal skipping row-locked leases (a 20 s+ row lock can let a healthy holder's
   lease lapse): document the bound, add no machinery.
8. Rebuild the slot/session lease bookkeeping (adopted, settling, current) as one structure now,
   invariant tests first, plan design-reviewed before code. Framing: fix-to-finding chains mark
   where the design is overcomplicated; spend the effort on a better approach there.

Ruling from review round 3 (2026-10-03):
9. A CLI `/resume` or `/new` settles the workstream being left AT THE SWITCH: wait briefly for
   in-flight saves, force one retry, discard what still cannot save with a notice, clear the
   journal failure state, release the old lease then. A slot holds one lease handle; "own row
   left" is derived from the session's identity. This replaces ruling 6's "once its saves land"
   trigger and the round-2 per-slot lease map (the settle lifecycle was the root of the r1/r2
   fix chains, and one conflicted row pinned the left lease for the slot's life). Ruling 6's
   stop of non-terminal state writes to a left own row stands.

10. `/new` that cannot lease its new row prints an error, stays on the current workstream and
    deletes the empty row; the unfenced fallback goes (a live session never runs unleased).
11. Console coordinator lease events stay in logs; the console's /metrics does not export them.
12. Round-3 extras: add the routed delete and coordinator title routes to the console API spec,
    and let the node UI's delete and rename name the holding node. Declined: a dedicated PG
    renewal connection (document the pool bound) and deletes taking the lease first (document
    SQLite's 30 s refusal after a crash).

Rulings from review round 4 (2026-10-03):
13. Ruling 3 REOPENED: identity adoption goes through the manager's ordinary `open`/`create`, never
    an in-place switch of a live session (watch restore, server and CLI `--resume`, CLI `/resume`
    and `/new`). The in-place switch was the cluster behind every round's largest bug group (four
    rebuilds; 4 of round 4's 8 confirmed bugs). Rulings 6 and 9 stop applying; ruling 10 holds via
    `create`'s rollback. Watch restore opens the real workstream: auto-approve only when the restore
    itself loaded the slot, cleared when a pane attaches. Plan: `docs/design/988/r4-fix-plan.md`,
    analysis in the round's simplification report.
14. CLI `/resume` and `/new` open a new tab; the tab left is closed at once when everything is
    saved, otherwise it stays open, keeps retrying, and the CLI says so.
15. A session without a node id (the CLI) never ends other nodes' watches (amends ruling 4): it
    holds a workstream only while it runs, and a fire meanwhile is retried by watch restore and
    delivered after the CLI exits.

Rulings from review round 5 (2026-10-04):
16. A watch whose workstream moved to another node is deactivated FIRST, then the model gets one
    best-effort notice (amends ruling 4): no "never ends untold" guarantee, no duplicate checks
    and no storage method for them. A notice whose save fails leaves the watch ended untold.
17. A watch fire for a workstream the CLI holds is retried within the watch's delivery and poll
    budget only (about 5 tries over 1-4 minutes), then dropped (amends ruling 15's premise of
    delivery after the CLI exits). Docs state the bound; no runner change.
18. A user who can fork a live workstream can keep its source row locked past the TTL on
    PostgreSQL (fork bursts), lapsing the owner's lease: accepted under ruling 7 and documented;
    the fork's lock mode is not weakened.

Ruling from review round 6 (2026-10-04):
19. The watch restore's unattended grant honors admin "ask" policies: during an unattended turn a
    tool matched by an "ask" policy waits for a person to approve it (as in an attended session),
    while unmatched tools still run without a prompt; "deny" still blocks and skip-permissions (an
    operator opt-in) still overrides. Not a regression: the old restore auto-approved permanently.
    Amended the same day: the smart-approval judge still counts as the normal flow and may clear an
    ask-matched call, judging the whole batch (its all-or-nothing rule), as in an attended session;
    a policy read that fails drops the grant for that batch (the calls go to the prompt).
    Superseded in part by ruling 20: a failed policy read now refuses those calls instead.

Ruling after the round-6 fix review (2026-10-04):
20. Tool policies that cannot be read fail CLOSED, fixed in this branch (it predates it): every
    call in the batch needing approval is refused with a retry message (`POLICIES_UNREADABLE_DENIAL`
    in core/policy.py), in the shared gate and the CLI's; calls needing no approval still run. The
    maintainer chose this over "ask a person" (a person could still approve a denied tool, and an
    unwatched session would stall) and over a separate PR. It reverses governance.md's old
    "fail-open" line, which no test pinned.

Hand-off (2026-10-05): after round 6 the branch went through three gate reviews of its fix diffs
(the last one stopped there by the maintainer's choice: gates, then PR). It was squashed into one
commit (032301cb, the same tree as the gated 9479148a) and carried by PR #1278 against dev.
Follow-up issues: #1272 (removed-alias reasoning effort, pre-existing), #1275 (a chat channel's
policy denial reads as a person's rejection), #1276 (intent-verdict audit for policy-refused
calls), #1277 (channel auto-approve when the router cannot read policies).

Path C decisions taken while implementing ruling 13 (2026-10-04), stated to the maintainer with no
objection (not rulings; details in the LOCAL `docs/design/988/r4-pathc-plan.md`): D1 `/resume` of a
workstream another CLI tab has switches to that tab, which keeps its own approvals; D2 a tab that
`/resume` or `/new` opens takes the left tab's skip-permissions and "Always" grants; D3 `--resume`
or `/resume` of a workstream with no stored turns opens it, while watch restore treats no turns as
permanent; D5 a tab left with background programs running stays open until `/ws close`; D6 no
cross-id load survives in the API (tests use `make_session(ws_id=X).rehydrate()`). The watch
restore's approval is a separate UI grant (`grant_unattended`, audit reason `unattended_watch`) that
the first client ends for good; it never touches skip-permissions.

The implementing session's hand-off is the LOCAL `docs/design/988-owner-lease-handoff.md`: its
first section summarizes the current (path C) design; read it right after the scope doc, then the
latest `docs/design/988/rN-fix-plan.md`.

**Why:** the rulings are not derivable from the code and settle questions a review round would
otherwise reopen. **How to apply:** before coding or reviewing #988 work, read the scope doc,
re-spike its cited lines ([[project_velocity]]), and treat these rulings as settled unless the
maintainer reopens one. See [[project_no_cross_version_support]] for why mixed-version clusters are
out of scope.

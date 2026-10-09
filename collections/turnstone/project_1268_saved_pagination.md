---
name: project_1268_saved_pagination
description: "#1268 saved-session paging (branch fix/1268-saved-session-pagination): the maintainer's rulings (updated = last conversation change, column drops, one page loader) and declined review points."
metadata:
  node_type: memory
  type: project
  modified: 2026-10-08T02:26:56.277Z
---

Premise check (2026-10-07, dev 72dbb41a): the issue's 50-rows-per-kind cap was real; its second
cause (a restarted process's reused node id shielding stale rows from cleanup) was already fixed
by #988, whose orphan close keys on lease liveness.

Rulings (the maintainer, 2026-10-07):
1. Server-side pages. `GET /v1/api/workstreams/saved` takes `limit`/`offset`/`q`/`sort`/`order`
   and returns an exact `total`; SQL applies visibility, search, sort and paging
   (`core/storage/_saved.py`). The visibility predicate is a SQL twin of
   `WorkstreamProjectVisibility`, pinned by the parity test in
   `tests/test_storage_saved_workstreams.py`. Both dashboards fetch every page, search and sort.
2. Saved = history and no live owner lease, for both kinds. This replaced the coordinators'
   closed-only filter and the warm-pool lookup, and reversed the pin
   `test_saved_excludes_active_state_rows`; a node's list now omits workstreams loaded anywhere.
3. Orphan cleanup (`bulk_close_stale_orphans`) keeps `updated`, so a reaped session keeps its
   place in the newest-first list and retention ages it from its last use. This reversed the pin
   `test_bumps_updated_on_close`, which had no stated reason.
4. `workstreams.updated` is the last change to the conversation (answer to the idle-close
   question, 2026-10-07): message saves, removals (rewind, retry, tail truncation) and fork
   clones set it; state, name, publication, open, close and cleanup writes do not.
   `touch_workstream` was removed (the owner lease protects a reopened row). Consequences,
   stated in the CHANGELOG and not separately ruled on: lists order by real use, and retention
   ages unnamed workstreams from their last conversation change (opening one no longer restarts
   its clock).

Declined review points (with reasons, so later rounds need not reopen them):
- Count and page as one snapshot: now ruling 5 below.
- Reusing the page query's project join inside the visibility predicate: the standalone predicate
  mirrors the Python rule step by step and the parity test pins it; its extra cost is two
  primary-key probes per row; the label's raw-id join matches the browser's own lookup.
- Computed sort keys (message/child counts, context ratio) evaluating every visible row: at a few
  hundred sessions in PostgreSQL a page's statements take 1-4 ms (8-13 ms per call with compile and
  round trips; re-measured before round 3 on synthetic data); the alternative is stored counters (a
  schema change). The `context_tokens` subquery repeated inside `context_ratio` runs only for the
  page's rows (PostgreSQL defers it past LIMIT): about 0.15 ms.
- The unified handler's two-pass kind loop (it validates every cfg before admitting any, pinned by
  `test_excluded_kind_still_validates_configuration`) and the console loader's `isCurrent` check
  (it guards side effects that run before `setPage`).

Built in answer to review round 2: orphan close and retention prune also skip rows whose lease
expired after their cutoff (`unheld_since_predicate`), because an open workstream's `updated` is
now as old as its conversation and a renewal outage must not close or delete it.

Round 3 (2026-10-07, code review plus a designer review of both dashboards):
5. The total and the page stay two statements. A third review raised the snapshot; the
   maintainer kept it over `count(*) OVER ()` or a REPEATABLE READ transaction (the table copes,
   and the next refresh corrects it).
6. CSS scope: the branch's own fixes plus pre-existing layout ones (saved header wrap below
   480px, CTX at <=480px, long-text wrap, `.dashboard-empty` contrast in base.css).
7. No "N more open on other nodes" hint in this branch.
8. The saved table drops columns one at a time by its own measured width (`drop` ranks: id,
   model, persona, project, counts, console KIND; NAME keeps 96px). It replaced a 760px viewport
   switch that let NAME reach 0px beside the side rail. Order and floors revised by ruling 10.
Declined in round 3: console clicks queueing behind an in-flight fetch (pinned; one round trip);
blank values sorting first (dev's order too); focus after failures, Retry or deleting everything
(rare paths); inferred screen-reader repetition on refocus.

Round 4 (2026-10-07, after the maintainer ran the branch on a real cluster):
9. One page loader for both dashboards, inside the shared table: the console's single-flight
   fetch with one trailing catch-up (a repeat of the in-flight query queues nothing), stale-answer
   drop, delete-mode deferral, and the error line with Retry. No request aborts: a click made
   during a refresh waits for that one round trip, as on the console before.
10. Column fitting, revised after using it: drop order ID, the count column (MSGS/CHILDREN),
   PERSONA, PROJECT, MODEL, then the console's KIND; NAME's floor rises from 96px to 200px, and
   ID leaves whenever NAME would get under 280px (most users have no use for the id). The higher
   floor lets a long name and a readable skill chip share the cell instead of one losing. The
   maintainer tried it on the cluster and confirmed the floors and order; KIND last is fine.
12. (After the round-4 designer check) The node never shows ID: its dashboard is capped at 960px,
   so NAME never reaches ID's 280px there; kept, as the console still shows it on wide tables.
13. The skill chip keeps its 6em floor (names first): a long-named row shows a stub of the skill,
   which the chip's title and the row's accessible name give in full.
Declined in round 4: request aborts (ruling 9); dropping the IME composition skip (unconfirmed:
both search boxes set autocomplete="off", which turns composition off on keyboards that honor
it); naming a hidden sorted column in the footer (it now drops last, so only on tiny tables).
Round 4 measured the SQL on a 20k-workstream test set: PostgreSQL non-service first page 544 -> 161 ms;
the old SQLite search took 232 s beside one busy Python thread (per-row Python fold), now 0.4 s.

Hand-off: the LOCAL `docs/design/1268-saved-pagination-handoff.md` (commits, verification,
review triage, resume steps). The branch's PR is #1309.

**Why:** the rulings and declined points are not derivable from the diff and settle questions a
review round would otherwise reopen.
**How to apply:** before changing the saved list, its SQL or the cleanup timestamps, treat the
rulings as settled unless the maintainer reopens one. See [[project_988_owner_lease]] for the
lease the saved rule uses.

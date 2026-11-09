---
name: feedback_reuse_the_authoritative_record
description: "Before adding a new record of what a tool did (a receipt of ids, a side table): check storage and existing tools first (#1457)."
metadata:
  type: feedback
---

When a review recommends recording a tool's side effects somewhere new, so the model or an
operator can find them later, first check whether an authoritative record already exists and an
existing tool reads it. If one does, point at that record instead of adding another copy.

**Why:** in #1457 (2026-10-22) the review pipeline recommended that a stopped `spawn_batch` journal
a cancellation receipt listing the child ids it had created. The maintainer asked why a coordinator
needed another record of the ids it spawns: storage records every child with its `parent_ws_id`
when it is created, `list_workstreams` reads that record, and the console's adapter registry feeds
the cancel cascade. The receipt would have been a third copy, and it had a timing hole as well: it
was written only when the batch itself saw the Stop. The ruling was no receipt; after a Stop the
model finds its children with `list_workstreams`.

**How to apply:** before building a new record, list the existing ones and what reads each, and
propose a new one only for a fact none of them can supply. In #1457 only the batch knew when an
in-flight create landed after a Stop, so it cancels those children from its own results rather than
storing them anywhere. Related: [[feedback_designs_that_need_no_memory]].

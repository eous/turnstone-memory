---
name: feedback_deferred_security_work_tracked_privately
description: "Deferring a security fix, or landing one without its own test, where no public issue may track it: note it in the branch's private docs/design note that turn; prefer writing the test."
metadata:
  type: feedback
---

A security finding that can't go into a public issue has no tracker unless the session writes one.
In the same turn a security item is deferred, add it to the branch's untracked `docs/design/` note:
what is open, why it was deferred, and where the review write-up lives. Treat a security fix that
landed without a regression test of its own the same way, but prefer closing that gap over
recording it: write the test, and check that it fails against a mutant of the fix.

**Why:** with public issues ruled out, nothing else carries a deferred item to the session that
ships the branch, and a fix with no test of its own can be undone by a later change without any
test failing.

**How to apply:** keep an "Open before release" list in the branch's design note, and update it as
items close. Run mutants per [[feedback_mutation_control_hygiene]]. Keep the note's wording neutral,
and keep the item out of shared memories, including any example that would point to it
([[feedback_local_only_memories]]).

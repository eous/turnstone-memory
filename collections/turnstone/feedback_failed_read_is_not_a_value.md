---
name: feedback_failed_read_is_not_a_value
description: "Writing a read helper, or any write/delete/prune/sync fed by a read: a failed read raises, never becomes {}/[]/None/a default; act only on reads that succeeded (maintainer, 2026-10-19)."
metadata:
  type: feedback
---

A failed read (database, config file, secret store, network) is an error, never a value. A helper
that catches a read failure and returns `{}`, `[]`, `None`, built-ins or the registry default
makes "couldn't read" look exactly like "nothing stored", and its callers act on that. Writes,
deletes and prunes act only on reads that succeeded, and a startup sync, seed or pin stores only
what it observed: an unset value already reads as the default, so never write the default back.
The rule is in CONTRIBUTING.md's Guidelines since the #1406 PR.

**Why:** scoping #1406 (2026-10-19), the maintainer flagged a trend of reads that fail and carry
on with defaults or empty values, and the worse one of those failed reads becoming permanent
setting changes. A read-only sweep of about 1,200 handlers confirmed it. ConfigStore's failed
first load ran a node on every default, including the startup prune (#1406); the console's TLS
sync stored `tls.enabled = false` over a stored `true` (#1413); a coordinator task add after a
failed read replaced the whole task list (#1416); a config.toml that fails to parse is treated as
empty and the CLI prunes on its built-in default (#1417); two admin shelves saved what a failed
load left (#1418, #1419). The rest are grouped in #1415.

**How to apply:**
- A read helper re-raises, or returns a distinct "unknown" its callers must handle, even when one
  caller wants a fallback: the fallback is that caller's explicit choice, never the helper's
  default. `load_task_envelope`'s absorbing default is the anti-pattern: the mutators inherited it.
- Before a write, delete, prune or sync, trace each input back; if one can be a substituted
  default, fail (retryably) instead.
- A fallback that fails closed (deny, hold, 503, retry, a person decides) is fine; one that
  loosens a control or reaches storage is not.
- A host that can't read its stored configuration at startup exits and lets the supervisor retry
  (#1406's design); a later reload keeps the last state that loaded.
- Frontend: check `r.ok` before rendering a form from a fetch, keep Save disabled until the load
  rendered, and drop responses for a shelf that has since been reopened.
- Pin each fail-closed arm with a failing-read test and check it against a mutant.

Related: [[feedback_designs_that_need_no_memory]], [[project_1359_default_fail_closed]],
[[feedback_everything_needs_auth]], [[feedback_pre_commit_gates]].

---
name: feedback_no_live_db_until_reviewed
description: "Testing a migration or data-touching change in dev: use synthetic fixtures + ephemeral test DBs; run against the real/dev DB only after review."
metadata: 
  node_type: memory
  type: feedback
---

Migrations and data-touching code are NOT run against the real / dev database during
development. The dev DB (e.g. the one holding real conversations) is the **final
validation corpus**, exercised once *after* the whole change is code-complete and
reviewed — never as part of the incremental dev loop.

**Why:** the dev DB holds real, hard-to-replace data and stands in for production.
Touching it mid-development risks corrupting the very corpus you'll validate against, and
conflates two separate questions — "does the code work" vs "does it work on real data."

**How to apply:** during dev, prove correctness on **synthetic fixtures + ephemeral test
DBs** — the `storage_backend` / `tmp_db` conftest fixtures, the `run_migrations` toggle,
and `test_migration_060.py`-style seed→upgrade→assert tests (both SQLite and PostgreSQL
via the backend fixture). Reserve the real-DB run for a gated, post-review validation
step. Generalizes to any irreversible / outward-facing data operation. Relates to
[[feedback_sdk_boundary_testing]] and [[feedback_pre_commit_gates]].

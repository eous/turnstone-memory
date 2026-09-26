---
name: project_dual_schema_parity
description: "Changing the DB schema: edit BOTH the alembic migration and core/storage/_schema.py; tests/test_schema_parity.py pins them equal, create_all seeds nothing."
metadata: 
  node_type: memory
  type: project
---

Turnstone defines its DB schema in **two** places kept in sync BY HAND:
- `core/storage/_schema.py` — SQLAlchemy metadata that `metadata.create_all()` builds.
  Used by `SQLiteBackend(create_tables=True)` and the `tmp_db` fixture → **nearly every test**.
- The **alembic migration chain** (`core/storage/migrations/versions/`) — builds production DBs.

**The gap (surfaced 2026-07-03 by the personas file-backed refactor):** nothing enforced that
the two agree. Add a column to a migration but forget `_schema.py` (or vice versa) → `create_all`
test DBs silently differ from production, and a migration bug passes CI. When touching schema you
MUST edit BOTH the migration AND `_schema.py`.

**Two create_all gotchas** (both hit this session, neither a strategy flaw):
- `create_all` builds **structure only** — never runs migration seed INSERTs. So `tmp_db` DBs have
  EMPTY tables (no seed personas etc.); tests needing seed rows must seed explicitly or read the
  migration's seed constants. The personas dump harness reads `_SEEDS` for this.
- `create_all` **no-ops on existing tables** (won't add columns) — a stale persistent dev DB
  (`.turnstone.db`, the `init_storage("sqlite")` lazy default in CWD) keeps its old schema forever.
  A test leaking to that lazy default breaks on schema change. Fix: delete the stale file (fresh
  lazy-init rebuilds current); better, tests should use ephemeral DBs [[feedback_no_live_db_until_reviewed]].

**Fix in place:** `tests/test_schema_parity.py` asserts `create_all` ≡ `alembic upgrade head`
(tables, columns, named CHECK constraints). Verified 0 drift across 44 tables. Kept create_all
(fast) rather than migrating every test DB (63-migration chain); the parity test makes the dual
path safe. Extendable to indexes/types/defaults if needed.

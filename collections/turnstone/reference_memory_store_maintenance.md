---
name: reference_memory_store_maintenance
description: "Memory-store maintenance: back up, scope edits, verify replacements and access counters; isolate PostgreSQL tests from persistent application databases."
metadata:
  type: reference
---

## Editing structured memories

Before an authorized maintenance pass, verify the current schema and back up the affected data
to durable storage. Identify rows by their full scope as well as their name. Audit content against
current source and distinguish shipped behavior from unreleased work.

Apply related changes in one transaction and verify each intended replacement. SQL `replace()`
silently returns its input when the old text does not match. Check affected row counts and use
phrases unique to the old and new text; shared prefixes cannot prove the old text disappeared.
Update timestamps using the application's current format.

Do not prune records simply because their names look temporary. Establish their scope and use
first. Topic-specific content belongs in the relevant project rather than global recall, where
it can repeatedly surface in unrelated sessions.

Verify relevance counters through an actual read path. The existence of a storage method that
increments `access_count` does not prove callers use it. A counter probe should show the expected
read changes the expected record and leaves unrelated records alone.

## Disposable PostgreSQL test databases

Use a separate disposable database for the PostgreSQL test suite and set `TURNSTONE_TEST_PG_URL`
for that fixture. Test setup may truncate tables; never point it at an application database.

Check whether the fixture runs migrations or only `metadata.create_all`. The latter creates
missing tables but does not add columns to existing ones. A persistent test database can therefore
produce many setup errors after schema changes even when a fresh database passes.

Recreate only the verified disposable test database, then rerun the affected suite. Use a unique
test database name and confirm the target before destructive operations. Keep authentication
details out of memory files and command transcripts.

Related: [[project_nudge_wake_fixes]], [[project_memory_relevance_pipeline]].

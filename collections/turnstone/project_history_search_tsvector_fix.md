---
name: project_history_search_tsvector_fix
description: "Postgres search_history returns nothing or a >1MB tsvector error: PR #795 fixed it with a left() 250K cap at both tsvector sites + rollback before fallback."
metadata: 
  node_type: memory
  type: project
---

**Status: PR #795 opened 2026-07-07** (branch `fix/history-search-and-client-errors`, 2 commits) —
also carries the [[project_native_node_troubleshooting]] follow-up: `ModelRegistry.get_client`
re-types non-ValueError client-construction failures as ValueError (alias + original error) so
routes answer 503-with-message instead of opaque 500; create_client's own ValueErrors pass through;
failed constructions are never cached.

**Bug pair (found 2026-07-07, fix in working tree same day):** Postgres `search_history` (`turnstone/core/storage/_postgresql.py` ~1264) computed `to_tsvector('english', content)` inline per row (seq scan, NO index — the "search_vector column" comment was stale). PostgreSQL hard-errors when one row's tsvector exceeds 1MB, aborting the entire query → a single 2.1MB bash tool-result row (stored 2026-06-14) silently killed ALL history recall on the dev cluster for ~3 weeks (`memory.py` catches → returns `[]`). Second bug compounded it: the ILIKE fallback ran on the same connection whose autobegun transaction was aborted → guaranteed `InFailedSqlTransaction` (fallback had never been reachable on pg).

**Fix:** `left(COALESCE(c.content,''), :fts_cap)` with `_FTS_INPUT_CAP_CHARS = 250_000` in BOTH tsvector sites (WHERE + ts_rank) — worst-case tsvector ≈4x input, so 250K chars is safely under 1MB — plus `conn.rollback()` first thing in the except branch. Regression tests in `tests/test_storage_sqlite.py::TestSearch` (oversized-row test runs on both backends; fallback test pg-only via `--storage-backend` skip, forces a real server-side error with `SELECT 1/0` substitution so the txn genuinely aborts). Verified: repro'd byte-identical error read-only on dev DB; tests fail pre-fix, pass post-fix.

SQLite needs nothing: FTS5 shadow table (`conversations_fts`) indexes at write time, no comparable limit, no failure-fallback structure.

**Queued follow-ups (not built):**
- Generated `search_vector tsvector GENERATED ALWAYS AS (to_tsvector('english', left(content, 250000))) STORED` + GIN index (migration after current head) — kills per-query full-table re-parse (2 tsvector computations × all rows × every search) and the per-query "word too long to be indexed" NOTICE spam. Must keep the same left() cap or the column can't build over existing rows.
- Optional write-time cap/sidecar for multi-MB tool results (`conversations.content` has NO size cap; 8 rows >500KB exist, max 2.1MB).

Related: [[reference_memory_store_maintenance]]. Pg-mode tests locally: throwaway
`pgautoupgrade/pgautoupgrade:18-alpine` container +
`TURNSTONE_TEST_PG_URL=...@localhost:55432/turnstone_test` + `--storage-backend postgresql`; never
point at the dev cluster DB (fixture TRUNCATEs all tables).

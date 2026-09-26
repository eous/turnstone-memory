---
name: project_963_oauth_extraction
description: "#963 delegated-auth extraction (oauth -> {mcp, model}): plan at docs/design/963-oauth-extraction.md, reviewed 2026-09-10; verified facts, open recommendations, and the one wording error to fix."
metadata:
  type: project
---

Plan lives at `docs/design/963-oauth-extraction.md` (local, gitignored), written against `dev`
at d334cc35. Reviewed 2026-09-10; nothing implemented yet, no worktree, no ruling from the
maintainer.

**Verified against the tree (don't re-derive):** every line citation resolves; both consumers
lock on `__obo__:<issuer>` locally and on PG (mcp_oauth.py 3221/4020, order
audience→credential→pg); `/connections` returns store rows with `server_name` verbatim (projection
needed on rename); `maybe_rediscover_oidc` swaps `app_state.oidc_config` (one-holder rule
right); grant legs take `oidc_config: Any` and only the MCP classified path calls rediscovery,
so the oidc↔grants cycle really dissolves.

**Recommendations given (awaiting the maintainer):** (1) order 1→3→2, rename before runtime work —
#962 needs only storage, #679 only the module seam; (2) step-2 stop() = lift
`MCPClientManager.shutdown()` shape + own the drain tasks and executor futures, drop the
stopping-state/re-entrant-stop machinery; (4) plan wording error:
`delete_mcp_oauth_rows_by_server_name` deletes `mcp_oauth_pending` (authorization states), NOT
`mcp_pending_consent`; (5) migration must rename the PG PK constraint + index and add `oauth_tokens`
to test_schema_parity index coverage; (6) Entra "before" baseline is the first Entra run since
#1083/#1117 — capture it on dev before step 1, and it needs a maintainer sign-in +
`entra_setup.sh setup`.

Related: [[project_mcp_oauth_discovery]], [[project_898_model_provider_obo]],
[[project_mcp_obo_single_token]], [[feedback_minimal_scope_first]],
[[feedback_nonconverging_reviews_mean_simplify]], [[feedback_alembic_linear_chain]].

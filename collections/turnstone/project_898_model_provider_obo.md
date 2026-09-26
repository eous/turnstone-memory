---
name: project-898-model-provider-obo
description: "#898/#955 per-alias auth_mode (entra_obo/entra_app) for model-call Entra tokens: mint-cache keys identity-keyed on alias, never audience (ruled 2026-08-04)."
metadata: 
  node_type: memory
  type: project
  modified: 2026-08-04T09:59:30.405Z
---

# #898 — per-user OAuth2 OBO for MODEL calls (external contributor)

The contribution: adds `auth_mode` (`static` default | `entra_obo` per-user OBO |
`entra_app` client-credentials) + `obo_audience` on `model_definitions` (migration 068),
reusing the #830 OBO grant legs, rotation CAS and the `mcp_user_tokens` mint-cache under
synthetic server names. Token bound at the call site via
`client.with_options(api_key=…)` — NOT `extra_headers`, because the Anthropic SDK will
not let `extra_headers` override its `x-api-key`. That reasoning is correct and worth
preserving anywhere this pattern recurs.

**RE-KEYED on the #955 branch (2026-08-04, the maintainer's ruling)**: synthetic mint-cache keys
are now IDENTITY-keyed on the owning definition's unique alias —
`__model_obo__:<alias>` / `__model_app__:<alias>` — not on audience(+scopes digest).
Bearer shape (audience/scopes) lives in the row's columns; the freshness gate compares
stored vs current dispatch values, so a re-aimed alias refuses its old row and overwrites
the same key in place. Admin lifecycle (rename/pair/scope change/delete) purges the
definition's own rows soundly via `_purge_model_mint_cache` (both prefixes) — sound only
BECAUSE keys are identity-keyed; the earlier value-keyed purge over-deleted shared rows
(round-5 finding). Cost accepted: no cross-alias mint coalescing; cooldowns per alias.
Multi-user identity direction (owner-as-default, per-participant ruling open) → #954.

Fix plan posted to the PR 2026-07-26. Status lives in gh ([[feedback_no_pr_status_in_memories]]).

## Durable architectural facts this surfaced (outlive the PR)

- **`set_app_state` is called in exactly ONE file** — `turnstone/server.py:3880` and `:5923`.
  `cli.py:1393` sets storage only; `console/server.py:5219` / `:10696-10699` set neither.
  Anything routed through `MCPClientManager` + `app_state` is therefore **node-only**: CLI
  turns and console-hosted coordinator workstreams can't reach it. **ANSWERED (2026-08-02):
  the console manager was NOT deliberately app-state-less** — an oversight, per the
  contributor. #898 wires it for host parity (console lifespan + `_ensure_console_mcp_client`),
  which also activates the previously-inert `oauth_user` MCP pool machinery for coordinator
  sessions. Treat that as a real behaviour change to an adjacent subsystem whenever this
  lands, not as part of model auth.
- **`with_options(api_key=…)` preserves the underlying `_client` object** on OpenAI SDK 2.48.0
  and Anthropic SDK 0.120.0 (probed 2026-07-27) — so per-call credential binding reuses the
  connection pool and does NOT open a fresh TLS connection per turn. Re-probe on an SDK bump.
- **`create_mcp_client` returns `None` when no MCP servers are configured**
  (`mcp_client.py:9176-9177`). Any feature that hangs off the MCP client reference is inert on
  a zero-MCP deployment. Related: `session.py:1809` nulls `_mcp_client` on an MCP-off persona,
  so the persona tool-surface lever silently governs anything else routed through it.
- **Cooldown/backoff must be keyed on the CACHE key, never the credential key.**
  `__obo__:<issuer>` is shared with the classified MCP mint (`mcp_oauth.py:2509-2511`), so
  arming a cooldown there lets one broken model alias suppress every `oauth_obo` MCP dispatch
  for that user. Same shape of trap as [[feedback_worker_slot_mutual_exclusion_scope]].
- **`_read_obo_credential`'s missing/undecryptable branches route through `_no_token_result`,
  which drops the refresh lock AND clears the backoff** for the key it's handed. Passing it a
  real (rather than placeholder) key while holding that lock self-inflicts a regression — needs
  a `prune_on_missing=False` seam.
- **`_protocol.py` is a THIRD mirrored storage site** alongside `_postgresql.py` / `_sqlite.py`,
  and mypy does NOT catch drift there because console handlers hold `storage` as `Any`
  (`web_helpers.py:310-326`). `create_model_definition` in the protocol was missed by this PR.
  Adds to [[project_dual_schema_parity]].
- **`sdk/typescript/openapi-console.json` is a checked-in generated artifact with NO freshness
  test** — `tests/test_openapi.py` builds the spec in-process and never compares to the file.
  Any console-schema change silently staleness-drifts it. Candidate for its own guard.

## Mint preconditions — the authoritative set (traced 2026-08-02)

**The two modes have DISJOINT preconditions. Never collapse them into one signal.**

| | `enabled` | `capture_user_credential` | profile `== "entra"` | `token_endpoint` | token store |
|---|---|---|---|---|---|
| `entra_obo` | required | **NOT read by the mint** | not required (rfc8693 works) | not required | required |
| `entra_app` | required | not required | **required** | **required** | required |

- **`capture_user_credential` is NOT a mint precondition.** It gates whether NEW
  credentials are captured at login; `mint_obo_access_token` only redeems a row already in
  `oidc_user_credentials`. Turning it off leaves existing users minting fine — so gating a
  WRITE on it is a false refusal.
- **`token_endpoint` is a per-process DISCOVERY result, not config.** One host may have it
  while another does not. Never assert it from a different process than the one minting.
- **The Fernet key IS deployment-wide by necessity** — `MultiFernet`, no key id on rows, rows
  in the shared DB, so every host reading them needs the same keyring (`docs/mcp-oauth.md`
  rotation guidance only makes sense that way). So token-store presence IS a sound
  cluster-level signal, unlike the two above.
- **`_obo_profile` CANNOT be made OIDC-aware.** `console/server.py`'s entra-scopes reject runs
  *outside* the `check_oidc_deployment` guard, deliberately, so a same-type edit of an existing
  `oauth_obo` row stays validated on an operator-disabled deployment. Making the shared helper
  return `""` would silently stop that reject firing. Add a separate model-only helper instead.
- **An unknown `obo_grant_profile` is now COERCED to `""`** at `load_oidc_config`, not just
  warned about. Left as-is, the mint resolves no leg, returns None every turn, and the call
  silently falls back to the shared static key — a typo swaps per-user attribution for the
  shared identity with no symptom.
- **The console is a MINTING PROCESS** (coordinator lanes), not just an admin surface — see
  the coordinator MCP work has the guard that let it boot keyless and never mint.

## rfc8693 scope gap (#955, live-verified 2026-08-03)

`_obo_mint_rfc8693`'s exchange leg needs a requested scope on Keycloak 26
standard token exchange ("Requested audience not available" without it — the
leg's own comment says so). MCP rows supply `oauth_scopes`; model definitions
have NO scopes source, so **model `entra_obo` on rfc8693 has never minted**.
#898's removal of the dead `scopes` param (item 13) was correct — nothing could
supply it — but the column gap is the real issue. Options in #955. The
`scripts/obo-e2e/keycloak_e2e.py` M1/M2 checks pin this as KNOWN-GAP.

## Method note

Five parallel finders → independent verify → dedupe → fix-verify produced 23 confirmed
findings; a **subsequent dataflow trace of the FIX SET** then corrected 20 of the proposed
fixes — including one that was not implementable as written (`ModelLane` carries no
`app_state`/user, so `model_turn` can read `auth_mode` but cannot mint) and one that would have
silently regressed another fix. Tracing the fixes, not just the code, is what caught these —
worth repeating on any multi-finding plan before handing it to a contributor.
See [[feedback_measure_before_accepting_a_finding]], [[project_external_contributor_review]].

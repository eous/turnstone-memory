---
name: project_mcp_oauth_discovery
description: "MCP OAuth discovery: canonical_resource(), PRM/AS candidate loops, private-network setting and issuer-cache repair are all on dev (09-04/09-07); Entra harness not yet re-run against them."
metadata: 
  node_type: memory
  type: project
  modified: 2026-09-03T22:37:06.763Z
---

**Landed (checked 2026-09-10):** Changes 1–3 reached `dev` 2026-09-04 as PR #1083; Change 4
(`mcp.oauth_allow_private_network`) as 7c11263c; the issuer-cache/registration repair as PR #1117
(2026-09-07). The Keycloak harness was run on the branch; the Entra harness has NOT been run
against any of these. Everything below is the pre-merge record.

Branch `fix/1061-1063-mcp-github-oauth` (base `f6b6893c`, the maintainer's commit
"complete GitHub OAuth flow" fixing #1063 / refs #1061). Local design note
(never committed): `docs/design/mcp-oauth-discovery-canonical-resource.md` —
finding maps, spec citations, both review rounds, and validation results.

**What landed (2026-09-03, uncommitted at time of writing):**
- `canonical_resource()` in `mcp_oauth.py` = the one RFC 8707 identifier
  (case-fold scheme/host, drop default port, drop root-only `/`, keep path
  byte-for-byte incl. trailing slash, keep query, reject fragment/userinfo).
  Feeds PRM URL derivation, PRM `resource` comparison, and `resource=`.
- `_fetch_prm_issuer` = candidate loop (path-specific, then origin); accepted
  set `{canonical, origin}` for every candidate; every failure records and
  continues; challenge budget = one hop per derived location; document error
  preferred, else first error. `_fetch_as_metadata` = four candidates (8414
  insert, 8414 append, OIDC insert, OIDC append) via `_well_known_url`, same
  record-and-continue, query/fragment issuers refused, issuer mismatch logged.
- `json_http_client()` factory (Accept: application/json) on all three
  constructor sites incl. `mcp_client._connect_all`; inline OBO transient
  folded into `_enter_mint_client`.
- Console: user-scoped rows store the canonical URL (create + update, judged
  on post-update auth type, merged URL); `url_changing` compares canonical
  forms (spelling-only rewrite ≠ purge); URL or AS-override change clears
  `oauth_as_issuer_cached` (nothing cleared it before — the code comment
  claiming "admin clears via re-edit" was false).
- `invalid_target` added to `_PERMANENT_AS_ERRORS`.

**Rulings (the maintainer 2026-09-03):** no real external hostnames in test fixtures
([[feedback_no_real_hostnames_in_fixtures]]); include `scripts/obo-e2e/`
validation when touching auth. Decisions taken by me and open to overrule:
spelling-only URL rewrite does not purge tokens; refresh sends canonical
`resource=` even for legacy grants (strict AS → `invalid_target` → re-consent);
RFC 8414 append form kept as candidate 2 for main parity (Keycloak).

**Validation:** Keycloak harness (`keycloak_e2e.sh`) all VERIFIED incl. new
D1 discovery probe (RFC 8414 append form, 2 probes, S256). Entra harness
(`entra_e2e.py`) NOT yet run — needs the maintainer's interactive sign-in. Full suite
12854 passed after Changes 1–3; review round 1 (high) 10 findings → 7 fixed,
2 refuted (trailing-slash tolerance; origin alias per location), 1 staging.

**Pending — Change 4 (private-network discovery by setting):** designed in
the note, not started. `mcp.oauth_allow_private_network` settings-registry
toggle, default off; private allowed ONLY for admin-typed hosts (server URL →
PRM URL, AS override); remote-learned issuers/endpoints stay strict; NEVER
lane still refused; https requirement unchanged. Today `mcp_oauth.py` has zero
`allow_private` calls and `trusted_hosts` is always `frozenset()`, so home-lab
`oauth_user` discovery to a LAN host fails on main, branch, and after 1–3.
Ship as its own commit + review round after 1–3 are clean.

**Gotchas:** SSRF loopback lane admits 127.0.0.1 without any allowance (the
harness probe needs no patch); `_mk_response(200, json_body=None)` in the
discovery tests yields a non-JSON 200; git workflow = amend unpushed (branch
has no upstream/PR yet); design docs never committed, `git add` by name.

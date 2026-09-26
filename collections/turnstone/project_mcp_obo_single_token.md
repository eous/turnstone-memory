---
name: project-mcp-obo-single-token
description: "MCP oauth_obo single-credential minting (PR #830 shipped 2026-07-12, Closes #551): one refresh token per user, entra/rfc8693 grant legs, Entra-verified."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-20T17:04:07.714Z
---

# ★ STATUS 2026-07-12 (LATEST): oauth_obo SHIPPED in PR #830 (Closes #551).
**Shipped 2026-07-12** (rebase per the maintainer — NOT squash/merge-commit; 33 commits replayed onto main with new SHAs). All 16 CI checks green on the pushed tip (test 3.11/3.12/3.13 + test-postgres + typecheck + lint + security/security-ts + CodeQL + claude-review + wheel-completeness). Local full sqlite suite 9228 pass at merge.
- **This session added 4 commits atop the 12-round-converged + live-validated tip:** `3ac389d5` auto-notify nodes on admin create/update/delete · `65f807e7` "per-user" idle-pool status label (not "connecting") · `9c3b3e35` Entra graph.microsoft.com userinfo trusted OOB · `8b2644dc` admin-write reload rework (below). Each got its own /code-review round; the reload rework took **3 rounds to converge** (xhigh→high→high; round-3 returned only PLAUSIBLE observability refinements).
- **Admin-write node-reload design:** create/update/delete/registry-install now SCHEDULE the cluster reload fan-out as a Starlette `BackgroundTask` that runs AFTER the 200 (`_schedule_mcp_reload`, "trigger, not drain" — mirrors `_cascade_cancel_to_children`), so a write's latency/success is never coupled to node reachability (was: inline `await`, up to ceil(nodes/fan_out)*30s hang + a post-commit 500 on a committed write). The operator `POST /reload` stays STRICT/drain (awaits inline, fail-loud, reports per-node results — a getattr None-guard that made it silently 200-`{}` was reverted). **There is NO periodic node→DB reconcile** — a node that misses a reload serves a stale MCP catalog until the next /reload; so `_run` logs unreached/failed nodes at WARNING (visible at default INFO, NOT debug), and `_notify` treats a non-2xx node reply as a failure (`raise_for_status`) so a 5xx node isn't miscounted as reached.
- Reusable live-test harness (dev cluster + Entra + azobo) unchanged: **[[reference_entra_obo_harness]]**.
- **#838 (2026-07-13)**: multi-tenant Entra (/common, /organizations) NOT supported — hard blocker is `verify_id_token` exact-match `issuer=config.issuer` (oidc.py:949-955), upstream of all obo code. Workarounds: single-tenant pin (validated) or B2B guests. Scope + spike-needed (cross-tenant RT redemption at /common = ASSUMED) in the issue.

---
# ★ STATUS 2026-07-12 (LATER — LIVE-VALIDATED): oauth_obo proven end-to-end on the real dev cluster + Entra tenant.
Ran the whole feature against the docker dev cluster + real Entra + a real 3rd-party Azure MCP server (`Pow3rTool/Azure-CLI-MCP` = "azobo"). Full chain PROVEN through product code: OIDC login → Fernet refresh token captured in `oidc_user_credentials` → Turnstone entra-profile mint (`api://<azobo>/.default`, correct aud/scp/appid) → trusted-TLS MCP transport → azobo bearer-validate + broker cert-OBO → **`az` ran AS the signed-in user** (Graph identity returned). Registration went through the real `admin_create_mcp_server` oauth_obo enforcement (HTTP 200). Reusable harness + reproduce/teardown + all Azure gotchas: **[[reference_entra_obo_harness]]**.
- **Live test surfaced 2 real issues → both FIXED & pushed** (#830 tip **9c3b3e35**, +4 commits, full suite 9218 pass): (1) **mid-session self-heal gap** — `prime_user_pools` runs only at ChatSession start, so an oauth_obo server registered mid-session never reached an already-open workstream (for obo, priming is the ONLY path tools reach the catalog — no consent flow). Fixed in `reconcile_sync`: re-prime active-session users (from the tool-listener registry) on a new OR auth-type-flipped pool server. An xhigh review then caught that a name-only diff MISSES the oauth_user↔oauth_obo flip → now diffs the `(name→auth_type)` view; also guarded per-user + honest "scheduled" log. (2) **Azure OIDC disabled OUT OF THE BOX** — Entra's `userinfo_endpoint` is on `graph.microsoft.com` (cross-host from the `login.microsoftonline.com` issuer) → `discover_oidc` rejected it → OIDC silently off unless operator set `trusted_endpoint_hosts`. Fixed: added `login.microsoftonline.com→graph.microsoft.com` to the built-in `KNOWN_TRUSTED_OAUTH_ENDPOINT_HOSTS` (oauth_ssrf.py), mirroring the Google entry. (This was PRE-EXISTING, NOT a #830 regression — git diff proved `enabled=False`-on-userinfo predates the PR.)

---
# ★ STATUS 2026-07-12: **PR #830 CODE-REVIEW CONVERGED** — feat/mcp-obo-single-credential, Closes #551.
Ran the owed delta review and then **looped `/code-review high` to convergence — 12 rounds**, fixing every finding each round (12 fix commits, tip ~441aabc8+). **Correctness has converged: rounds 11 AND 12 both returned ZERO confirmed correctness findings** (the only round-11/12 correctness items were the documented-accepted CAS-residual + cleanups). Gates green every push: ruff + mypy strict (233 files) + full suite (~9216 pass / 10 skip).
- **Two SERIOUS latent bugs the loop caught (would have shipped otherwise, each invisible until an unprimed finder hit the exact angle):** (1) **round-5 SECURITY**: my round-2 `is_flip`-gated OAuth-column scrub let a same-type static edit inject an `oauth_authorization_server_url` that survived a flip to oauth_user → attacker-AS redirect. Fixed: columns are a pure function of target auth_type on EVERY write. (2) **round-7 DEAD FEATURE**: the OIDC runtime re-discovery (auto-heal after boot-time IdP outage) NEVER worked — `discover_oidc` preserves the input's `enabled=False`, so the config-swap was unreachable — and my test MASKED it by mocking `discover_oidc` to return enabled=True. Fixed + de-masked (test now drives real `discover_oidc` via a mocked HTTP discovery GET).
- **Iteration hotspot / OPEN QUESTION for the maintainer**: the OIDC **auto-heal-after-outage sub-feature** (original R3 task) drove findings across rounds 7-9 (dead code, console edit/disable lockout when OIDC disabled, config-invalid re-probe-forever, login-path never triggered the heal, first-probe cooldown-skip near boot). It adds real cross-loop/cross-process complexity (`maybe_rediscover_oidc`, cooldown, single-flight, terminal-latch). Now working + tested, but worth asking whether its complexity earns its keep vs. "restart the node after an IdP outage."
- **Accepted-by-design residuals** (documented in code, re-flagged as PLAUSIBLE and deliberately not "fixed"): the per-dispatch pending-consent DELETE volume is the bounded cost of cross-node badge self-heal; the interactive.js no-consent-URL fallback removal is unreachable for oauth_user (invariant: always carries consent_url) and intended for obo.
- Full round-by-round finding inventory + dispositions: docs/design/obo-review-findings.md (local, untracked). Original pre-convergence review history (max/high/xhigh) also in that file.
- **Both grant legs still e2e-VERIFIED** (unchanged): scripts/obo-e2e/ (entra interactive + keycloak headless).
- **Both grant legs e2e-VERIFIED through real product code** (not mocks):
  `scripts/obo-e2e/entra_e2e.py` (Entra, interactive) + `keycloak_e2e.py`+`.sh` (rfc8693/OSS,
  headless) — E1-E7 all pass. To re-run Entra: `./scripts/obo-e2e/entra_setup.sh setup` (creates
  disposable app registrations and a gitignored fixture configuration). Keycloak is self-contained
  (ephemeral docker, port 8091).
- **Config**: `[oidc] capture_user_credential` (default off), `obo_grant_profile` = "entra"|"rfc8693"; requires the `[security] mcp_token_encryption_key`. Storage: migration 067 `oidc_user_credentials`.
- **GitHub issue-side DONE earlier this session**: #551 retitled + re-scope comment
  (issuecomment-4949886714), #550 reply to the contributor (issuecomment-4949886755), #550 body
  auth_type correction. PR #830 Closes #551.
- **Lessons this session**: don't create root BRIEFING.md — design docs go in docs/design/ ([[feedback_artifact_cleanliness]]); name files in `git add` not `-A`; "xhigh" is a Claude Code term (scrub from commit msgs), "max" is generic-enough.

---
# Single-credential MCP token minting (flow-3 OBO) — investigated 2026-07-11

**Trigger**: a contributor comment on #550 (2026-07-07) — friction A: every user must click Connect
on N `oauth_user` MCPs; friction B: users×servers refresh-token custody will hit IdP rate limits.
Ask: user/group/global MCP scoping + ONE refresh token per user across all OBO MCPs (their "flow
3").

## Code-map facts (main @ f4e54ce8, verified by Explore agent)
- `auth_type` is **`none | static | oauth_user`** — `oauth_token_exchange` does NOT exist (#550 body listing it was aspirational; #551 never started). No RFC 8693/OBO/jwt-bearer-assertion code anywhere. Schema: `core/storage/_schema.py:797-820`; admin allow-list `console/server.py:9685`.
- `mcp_user_tokens` composite PK `(user_id, server_name)`, MultiFernet-encrypted
  (`core/mcp_crypto.py`). **Background keep-alive sweep** `_user_token_sweep_loop`
  (`core/mcp_client.py:2593`) force-refreshes every consented (user,server) grant to keep them hot
  for autonomous work — at scale this IS the reported rate-limit concern realized. Per-pair
  pg-advisory+asyncio refresh locks (`core/mcp_oauth.py:1108-1160`).
- oauth_user pool is per-(user,server) sessions; bearer injected at `_connect_one_pool` (`mcp_client.py:2162-2164`) — a new auth_type only needs a different token-acquisition function feeding the same attachment point.
- Consent UX is reactive-only (inline Connect on failed dispatch, `shared_static/interactive.js:4471`); Manage→Connections panel is revoke-only; no bulk/proactive connect.
- **Migration 065 Entra `oid`/`tid` are write-only** — captured at OIDC login (`core/oidc.py:870-902`), zero readers. Groundwork anticipated, unstarted.
- No scoping columns on `mcp_servers` (no user/project/group); servers are global; admin CRUD lives in console app, consent/runtime in main server — scoping features span both.
- OIDC login (`core/oidc.py`) discards IdP access/refresh tokens today (#551 prerequisite 1).

## External facts (2026-07-11)
- MCP **EMA extension stable 2026-06-18** (ID-JAG = RFC 8693 + RFC 7523); #680 tracks the client
  side. IdP support **Okta-only** ("Cross App Access"); **Entra has no ID-JAG issuance yet** → #680
  alone does not help Entra deployments.
- Entra-native equivalent: since Turnstone is the OIDC confidential client, with `offline_access` it holds ONE refresh token per user redeemable repeatedly for different downstream audiences (`scope=<audience>/.default`), given admin-consented delegated permissions on Turnstone's app registration. OBO jwt-bearer (`requested_token_use=on_behalf_of`) is the middle-tier variant. Both need spike verification against a real tenant (ASSUMED until spiked). Claims challenges (`interaction_required`, AADSTS50079) must fall back to the interactive connect rail.

## #551 design record (must engage when re-scoping)
#551, `mcp v2` label, title still "RFC 8693 token-exchange". eous 2026-06-19 deferral comment: (a) **rejected alt C = MS-specific OBO** in favor of cross-vendor RFC 8693; (b) **risk #3** = Turnstone holding a cross-audience token / two refresh chains — EMA praised for closing it; (c) claimed Entra 2nd-consent removable TODAY via admin-consent + preAuthorizedApplications on existing `oauth_user` ("tenant config, no Turnstone code") → filed **#682** runbook. **#682 never written** (0 comments, 2026-07-11). Counter-analysis: pre-auth clients kill the consent SCREEN only — per-server interactive connect clicks remain (UX is reactive-only), per-(user,server) refresh-token custody remains, keep-alive sweep load remains. Risk-#3 honest framing: aggregate DB-compromise blast radius unchanged (N per-audience rows ≈ same total surface); single-credential leak broader per-credential; revocation simpler (one row); Conditional Access still gates each redemption.

## Build state (2026-07-11 EOD)
- **POSTED 2026-07-11**: #551 retitled ("single-credential token minting (oauth_obo auth_type)") +
  re-scope comment (issuecomment-4949886714, has verified grant-leg table); reply to the contributor
  on #550 (issuecomment-4949886755, asks them to beta CA/MFA surface); #550 body auth_type
  corrected.
- **Branch `feat/mcp-obo-single-credential`** (local, unpushed): slice 1 storage half committed **3a43faba** — migration 067 `oidc_user_credentials` (user_id, issuer) PK, dual-schema mirrored (parity green), protocol + pg/sqlite backends (upsert replace-on-conflict preserves `created`; rotation write-back; delete_user cascade), MCPTokenStore wrappers (`upsert/get/update_after_redeem/delete_oidc_credential`), tests/test_oidc_credential_storage.py (13). Gates: ruff+mypy(233 files)+parity+57 adjacent all green. **Schema decision ratified by the maintainer**: separate table, NOT a column on oidc_identities (custody isolation, hot rotation writes, (user_id,issuer) lookup shape).
- **Slice 1 COMPLETE**: capture half committed **7b9531d0** — `[oidc] capture_user_credential` knob (default off, env override), offline_access scope append (idempotent), best-effort capture in handle_oidc_callback (never blocks login), startup SystemExit when capture enabled w/o encryption key. 12 new tests (6 loader + 6 callback), 178 OIDC-suite green.
- **Slice 2 ENGINE committed cc4638b1**: `get_obo_access_token_classified` SIBLING fn (oauth_user path untouched); entra+rfc8693 legs (spike wire shapes); `[oidc] obo_grant_profile` (default "entra"); PERMANENT mint failure drops ONLY cache row, credential NEVER auto-deleted; rotation write-back BEFORE cache write; locks server→credential `__obo__:<issuer>` + pg advisory. Exported `is_user_scoped_auth`/`USER_SCOPED_AUTH_TYPES`.
- **Slices 1+2 COMPLETE (5 commits, security core)**: 3a43faba storage · 7b9531d0 capture · cc4638b1 mint engine · 45e32b5e mint tests (agent-written, 14 cases, zero engine discrepancies) · f0ca7f11 gate sweep (obo joins pool class at routing/status/static-health/resolve/dispatch/web_search/console; priming+sweep+consent sites deliberately stay oauth_user-only; `_build_consent_url` returns None for obo → re-login detail message). 1027 MCP tests green post-sweep; mypy 233 files clean.
- **MAX review DONE 2026-07-12**: branch is **NOT shippable** — 15 CONFIRMED reported (cap) + 18
  dropped mined from journal (full inventory: docs/design/obo-review-findings.md). Three P0 classes:
  (A) **feature inert** — nothing primes obo pools so tools never enter any per-user catalog, "first
  dispatch mints" unreachable (mcp_client.py:2597; my slice-3 priming deferral broke catalog
  population); (B) **rfc8693 credential corruption** — rotated RT discarded on exchange-leg failure
  + exchange RT written back over issuer credential → lockout across all obo servers
  (mcp_oauth.py:1952/1960); (C) **console never widened** — update nulls audience, auth-type/URL
  flips skip token purges (custody), keyless create → cluster SystemExit at boot, bulk-revoke
  refuses obo (server.py:10344/10326/10339/10137/10705); plus (D) Entra oauth_scopes replaces the
  audience-carrying scope → wrong-audience bearer leaked to MCP server (mcp_oauth.py:1903); (E) no
  credential revocation path + pending-badge gates exclude obo; (F) state-machine divergences
  (2063/2099/2156) whose ROOT is a ~100-line copy of the oauth_user machine (2147).
  Dropped-but-worth: 10163 (reject audience-less at write), 1992 (race re-creates orphan row
  post-delete), 5993 (dead-end re-consent msg), 2196/2069/2089, single-source constants
  (580/9732/217/1830; OBO_GRANT_PROFILES is DEAD).
- **Decisions (the maintainer 2026-07-12)**: F-cluster = EXTRACT SHARED HELPER; fold in ~10 worth-addressing dropped, defer 5 cleanup.
- **ALL FIXED 2026-07-12** (5 fix commits; dispositions in docs/design/obo-review-findings.md): A→0521f451 (prime obo pools); B→7270ce59 (persist_rotation callback: rotate-before-exchange, exchange-RT never hits credential); D→7270ce59 (always <aud>/.default); F→7270ce59 (shared `_handle_refresh_failure`, oauth_user BYTE-IDENTICAL 1304 green); C→ff4c21e3 (audience/key required at write, transition purges, bulk-revoke obo); E→85811cf6 (identity-unlink revokes credential, any_user_scoped badge gate, dispatch-success clears pending). Constants single-sourced. +~20 regression tests. **1992 orphan-row race = ACCEPTED RESIDUAL** (bounded: short-lived AT cache row, no RT, self-expiring). Full mcp/oidc/console suite 1880 green, mypy clean.
- **TWO ORIGINAL SLICES STILL OUTSTANDING** (the maintainer caught the drop 2026-07-12; review reorg absorbed backend of slices 3-4 but not these): **(4-frontend) admin.js console form** — obo backend validation is done in console/server.py but the FRONTEND form (index.html mcp-auth radios + admin.js `_selectedMcpAuthType`/`mcp-oauth-fields` at ~5013/5232) still gates the OAuth sub-form on `oauth_user` ONLY, so operators can only configure obo via raw API, not the console UI; need an oauth_obo radio + audience-required field + plain-language copy ([[feedback_operator_ui_plain_language]]). **(5) operator docs** — per-IdP grant recipes (Entra/Keycloak from docs/design/obo-spike), admin-consent-propagation gotcha, security/custody note, #682 cross-link. Both were tagged "agent" earlier.
- **FOLLOW-UP high review DONE — ALL FIXED commit a5080815** (+13 tests, 1888 green). Theme was
  incomplete obo revocation + my self-inflicted hot-path SQL regression. Key: unlink now purges obo
  cache rows + honest audit; **bulk-revoke obo = honest cache-FLUSH** (the maintainer chose this:
  obo_cache_flushed event + effect=cache_flush_remints, NOT durable revoke — obo per-server
  revocation is IdP-governed); audience-change purge; flip clears stale scopes + entra-scope
  write-reject; hot-path clear gated on in-memory set; obo_mint_rejected log text restored +
  event-name literals; stale refresh-bearing row never served; removed dead
  any_oauth_user_mcp_servers. Full dispositions in docs/design/obo-review-findings.md.
- **ALL 5 SLICES DONE 2026-07-12** — slice 4-frontend committed 68465117 (admin.js/index.html: oauth_obo radio "Sign-in passthrough", shared OAuth fields hide oauth_user-only inputs for obo, audience-required + rfc8693-scopes-only hints, client-side validation, honest "flush cache (N)" list action → data-mcp-cache-flush handler; node --check OK, all JS-ref IDs verified in HTML); slice 5-docs committed 36305208 (docs/mcp-oauth.md: obo mode row + dedicated section [deploy config, Entra + Keycloak/rfc8693 setup incl. AADSTS65001 admin-consent-propagation gotcha, revocation/custody, #682 interim] + transition/troubleshooting rows; byte-clean).
- **12 commits on branch feat/mcp-obo-single-credential** (unpushed): 3a43faba·7b9531d0·cc4638b1·45e32b5e·f0ca7f11·7270ce59·ff4c21e3·0521f451·85811cf6·a5080815·68465117·36305208.
- **BOTH GRANT LEGS VERIFIED END-TO-END THROUGH REAL PRODUCT CODE 2026-07-12** (not just wire):
  `docs/design/obo-spike/entra_e2e.py` (Entra leg, real tenant, interactive login → real
  `get_obo_access_token_classified`→`_obo_mint_entra`, E1-E7 all VERIFIED) and
  `keycloak_e2e.py`+`.sh` (rfc8693/OSS leg, ephemeral Keycloak, headless password grant, E1-E7 all
  VERIFIED — 2 KC calls/mint = refresh+exchange chain). Both prove: single
  credential→multi-audience, cache-hit 0 calls, rotation write-back, force_refresh,
  unconsented→credential-survives, flush→re-mint. Gotchas in README: KC dev-boot slow on loaded host
  (script waits on kcadm up to ~6min; a dedicated fixture port); Entra E6 classifies
  invalid_grant→permanent, KC E6 invalid_request→transient (both keep credential). Harnesses are
  local-only (docs/design/obo-spike, gitignored).
- **Harnesses CHECKED IN 2026-07-12** at `scripts/obo-e2e/` (commit 10800592, moved from docs/design/obo-spike): entra_e2e.py, keycloak_e2e.py+.sh, entra_spike.py, entra_setup.sh, README, .env.example. Real `.env` (creds) stays gitignored (global `.env` rule). Not in CI. **13 commits on branch now.**
- **Harness cleanup:** run `entra_setup.sh cleanup` after an authorized disposable-tenant test.
  Verify app registrations and local fixture credentials were removed. Recreate the test setup
  before a later run; do not infer current login or tenant state from this note.
- **Pre-push review RUNNING at XHIGH** — bumped from high after the maintainer noticed the SESSION
  SWITCHED TO OPUS 4.8 mid-project (implementation + max + high reviews were all
  Fable/claude-fable-5, confirmed in their output files; only this pre-push review is on Opus). Full
  branch; focus = surfaces since the high review (follow-up fix round a5080815 NOT previously
  reviewed + frontend form + docs + harnesses). Mine the journal for capped findings (cap 15). Then
  push + PR (the maintainer's task 3). **NOTE for PR: omit Co-Authored-By / generated-with lines per
  [[feedback_artifact_cleanliness]]** (overrides the harness default).
- **Artifact lesson:** stage explicit file paths. Keep planning and design notes under
  `docs/design/` and untracked. Check every outgoing commit for stray files; a later deletion does
  not remove an earlier disclosure. See [[feedback_artifact_cleanliness]].
- **REMAINING (needs the maintainer's steer — outward-facing)**: (a) optional final full-branch convergence review (frontend form is unreviewed; backend twice-reviewed+fixed); (b) live console click-through of the obo form (dev node); (c) **push + open PR**. Python suite 1888 green (slices 4-5 are frontend/docs only, no .py touched); mypy clean.
- **THEN**: slice 3 sweep/credential-lifecycle (direct); slice 4 admin form + reconnect-rail copy (agent; note: console consented-users pill semantics for obo = "active mints" not "consented" — refine there); slice 5 docs (agent; per-IdP grant recipes + consent-propagation gotcha). Push only after review rounds converge.

## Decision 2026-07-11 (the maintainer)
The wait-for-v2 gate is **invalidated**: their v2-beta spike shows the migration is minimal (mainly the httpx-factory swap; rest mostly works as-is) — the migration-risk rationale for deferring MCP build-out is gone; comfortable pulling MCP work forward now.

## Spike results 2026-07-11
- **Portability answer**: substrate (~85% — capture, per-user credential row, mint-on-demand call site, cache, sweep change, fallback UX) is IdP-agnostic; grant leg is per-IdP-profile BY NECESSITY: `entra_redemption` (RT + `scope=<aud>/.default`; ASSUMED until tenant spike) | `rfc8693_exchange` (**VERIFIED on Keycloak 26.3**) | `id_jag` (#680, when IdPs ship). Plain-OIDC IdPs with no minting mechanism can't do flow 3 at all → those stay `oauth_user`; feature is inherently trust-domain-aligned-enterprise.
- **Keycloak RFC 8693 leg VERIFIED live** (ephemeral docker, torn down; full repro in docs/design/obo-spike/README.md): one RT → refresh grant → user AT → two exchanges → aud=mcp-a and aud=mcp-b tokens (300s, NO RT = cache-shaped). RT ROTATED on refresh → **newest-RT write-back is correctness-critical on both legs**. KC's "delegated grant" = audience client scopes attached to requester client (optional scopes must be requested via `scope=` at exchange or 400 "Requested audience not available"); Entra's = API permissions + admin consent. Per-IdP operator runbooks (#682 pattern), same code.
- **Code-reality (main @ f4e54ce8)**: `handle_oidc_callback` (`core/auth.py:1986`, token drop ~:2046-2053) extracts ONLY id_token — #551 premise holds, its auth.py:1567 citation stale. `exchange_code` (`core/oidc.py:687`) already returns the full token dict → capture = clean insertion after `provision_oidc_user`, no refactor. OIDCConfig single-issuer, static `scopes` str (default "openid email profile", no offline_access). `oidc_identities` PK (issuer,subject) — key new credential table (user_id, issuer) to future-proof multi-IdP.
- **Entra grant checks (2026-07-11):** the disposable app-registration spike verified one refresh
  token across multiple audiences, rotation write-back, consent-required classification for
  AADSTS65001, and the OBO jwt-bearer variant. In that fixture, the previous refresh token remained
  valid after rotation; verify this behavior for each identity provider and configuration. Admin
  consent immediately after service-principal creation could skip a principal that had not
  propagated. Verify delegated grants for each resource before registering the server, and check
  propagation before interpreting a redemption failure as revocation.

## Historical implementation scope (assessment delivered 2026-07-11)

New auth_type (working name
`oauth_obo`), single-path Entra leg: (1) opt-in OIDC token capture — one encrypted IdP refresh token
per user in a NEW per-user table (do NOT touch `mcp_user_tokens` PK; its rows become the
per-(user,server) short-lived access-token cache, `refresh_token_ct` NULL for this type); (2)
mint-on-demand redemption at connection/refresh time; (3) exclude this type from the keep-alive
sweep (sweep load drops users×servers → users); (4) zero-click UX + claims-challenge fallback to
inline connect; (5) grant leg pluggable so #680's ID-JAG slots in when IdPs ship it. DEFER: full
user/group/global scoping matrix and flow-2 `oauth_client_credentials` (separate small additive) to
#550/v2; gateway stays investigation-level. Sequencing vs #679 (mcp v2): work lives in
mcp_oauth.py/storage/oidc.py, not the transport factory; one bearer-attachment re-verify point
post-v2. OK to run before/parallel — narrower than the "sequence EMA with v2" June position on #550,
justified by live user friction. Next steps when picked up: boundary spike vs real Entra tenant
FIRST ([[feedback_sdk_boundary_testing]]) — spike must also verify refresh-token ROTATION write-back
(Entra may return a new RT per redemption; persist newest) and
preAuthorizedApplications/knownClientApplications/admin-consent behavior; re-scope #551 + reply to
the contributor on #550. Related: [[project_1_7_roadmap]] (mcp v2 track),
[[feedback_minimal_scope_first]].

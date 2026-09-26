---
name: reference_entra_obo_harness
description: "Standing up a live oauth_obo MCP test against a real Entra tenant on the docker dev cluster: app regs, the admin-consent quirk, broker/server deploy, HTTPS trust, Azure policy gotchas."
metadata:
  type: reference
---

How the 2026-07-12 live oauth_obo end-to-end test was built (feature:
[[project_mcp_obo_single_token]]). Use a disposable test tenant and synthetic identities. Provision
and remove credentials through the test harness; this note records the protocol setup, not a live
account configuration.

## Entra structure (scripted via `az`)
- **Two single-tenant app regs**: `turnstone-oidc-client` (OIDC confidential client — secret,
  redirect `https://localhost:8443/v1/api/auth/oidc/callback`, delegated perm to the resource's
  `user_impersonation` + Graph openid/profile/email/offline_access, all admin-consented) and
  `azobo-mcp-resource` (Expose an API `api://<id>` + scope `user_impersonation`,
  `requestedAccessTokenVersion=2`, uploaded broker cert, delegated Azure Service Management + Graph
  `User.Read`, admin-consented).
- **`az ad app permission admin-consent` returns exit 0 but creates NO delegated grants** — a real
  CLI quirk. Create them directly: `az rest --method POST .../oauth2PermissionGrants` with
  `{clientId:<sp>, consentType:AllPrincipals, resourceId:<resource-sp>, scope:"…"}`.
- Test as a fresh **member** user with Reader on the subscription, not the tenant owner's personal
  account, for clean OBO token semantics.
- Cert: self-signed `obo.key`/`obo.crt`; SHA1 thumbprint feeds `AZOBO_CERT_THUMBPRINT`. Its
  `customKeyIdentifier` in Entra is NOT the SHA1 — cosmetic; the broker sends `public_certificate`
  so Entra matches the full cert (x5c).

## Boundary spikes that de-risk the build (do these first)
- Get a user refresh token without the cluster, redeem `scope=api://<resource>/.default`, and
  decode aud/scp: confirms the entra-profile mint before any container exists.
- Pre-flight the broker OBO in the MCP server's image itself: msal
  `ConfidentialClientApplication(cert).acquire_token_on_behalf_of(user_assertion, scopes)` proves
  cert auth + OBO without the cluster.

## MCP server deploy (TWO containers, one image) — the gotchas
- **broker** (`obo_broker.py`, holds the OBO cert, does the downstream OBO over a unix socket) +
  **server** (`server.py`, MCP on :8782, shells `az`, no cert). Share `/run/azobo` (bind-mount a
  host dir).
- Run BOTH as the host uid (`user: "1000:1000"`): the image is uid 10001 but the 0600 cert is
  host-owned, so matching uid lets the broker read it (and the host-dir socket).
- **`AZOBO_PYTHON=/usr/local/bin/python` + `AZOBO_WRAPPER=/app/azobo`** — defaults point at a
  systemd venv path and az_run fails `No such file or directory` without them.
  (`docker compose restart` does NOT re-read `env_file` — use `up -d --force-recreate`.)
- **`AZOBO_PUBLIC_HOST=azobo-server:8782`** — FastMCP DNS-rebind `allowed_hosts` is exact-match on
  the FULL `host:port`; the bare host / `:443` variants won't match a node connecting to
  `azobo-server:8782`. (Absent `Origin` passes.)
- The server binds `127.0.0.1`; patch to `0.0.0.0` (one line) so other containers reach it; the
  isolated network + bearer validation keep it safe.

## oauth_obo needs HTTPS (loopback-http excepted) — how the nodes trust the server
- `_validate_oauth_user_url` rejects non-loopback `http://`, so front the server with a **Caddy TLS
  sidecar** (self-signed CA + leaf with SANs for the sidecar and server names,
  `header_up Host azobo-server:8782`).
- Nodes trust it via **`SSL_CERT_FILE=<certifi bundle + your CA>`** mounted into console+nodes
  (Turnstone's MCP httpx factory uses default verify → honors SSL_CERT_FILE). The self-signed CA
  needs `basicConstraints=critical,CA:TRUE` + `keyUsage=critical,keyCertSign,cRLSign` or OpenSSL 3
  rejects it ("CA cert does not include key usage extension").

## Register + drive (no browser needed for admin)
- Mint an admin/service JWT inside the console container with `create_jwt(...)` and scopes
  `read, write, approve, service`; the `service` scope passes `require_permission` by design
  (`allow_service_bypass`). POST to `/v1/api/admin/mcp-servers` (`auth_type=oauth_obo`,
  `url=https://<tls-sidecar>:8443/`, `oauth_audience=api://<resource>`).
- Admin create/update/delete schedule a best-effort node reload after the 200, so the manual
  **POST `/v1/api/admin/mcp-servers/reload`** is only for an explicit operator reconcile (it drains
  and reports per-node results). oauth_obo tools are PER-USER: they surface only when the user's
  session runs `prime_user_pools` (also on mid-session reconcile).
- Login/capture is browser-only (auth-code flow through the console at `https://localhost:8443`).
  OIDC users provision as `builtin-viewer` (oidc-default); elevate the test user to drive
  workstreams.

## Azure policy gotchas
- **ARM (Azure Service Management) requires MFA** under Entra security defaults, so tokens minted
  without MFA fail `az account show` with **AADSTS50076**. **Microsoft Graph does not**: test with
  `az ad signed-in-user show` or `az rest --url https://graph.microsoft.com/v1.0/me`. Security
  defaults can't be toggled via `az`; it needs Graph Policy scopes or the portal.

---
name: project_mtls_architecture
description: "Cluster mTLS (core/tls.py, console/tls.py) or browser HTTPS: console stays plain HTTP behind Caddy by design; 2026-05-30 SAN/renewal/reload fixes on main."
metadata: 
  node_type: memory
  type: project
---

mTLS (lacme-backed, `turnstone/core/tls.py` + `turnstone/console/tls.py`, docs in `docs/tls.md`).

**Trust model.** Console runs the internal CA + ACME server (`/acme/*`). Service
nodes auto-provision certs via ACME over **plain HTTP** on first boot (they don't
have the CA yet to verify TLS — `_fetch_ca_cert` hard-forces `http://`). The cert
store is the **shared Postgres DB** (`tls_certificates`), visible to every node.

**The 2026-05-30 fix (3 root causes that broke cluster mTLS; committed to `main` same day, `d820168f`/`2c2f9e15` — VERIFIED still on main 2026-07-06):**
1. **Cert identity** — certs were keyed on `socket.gethostname()` (the Docker
   container ID) and the advertised name (`server-1`) was never a SAN, so every
   collector/proxy handshake failed the hostname check. Fix: `build_cert_hostnames()`
   puts the **advertised host first** (primary domain = stable store key + SAN).
2. **Renewal storm** — lacme's `RenewalManager.check_and_renew()` sweeps the WHOLE
   `store.list_certs()`; with a shared store, every node renewed every other node's
   (and every dead container's) cert. Fix: `_SingleDomainStore` wraps the store so
   each node's manager sees only its own domain. Empty domain → renews nothing
   (never fall back to the whole store).
3. **No hot-reload** — uvicorn loads its cert once at boot and never reloads;
   renewal updated the DB + in-memory bundle but not the live listener, so the
   served cert expired ~24h after boot. Fix: `swap_context_cert()` does
   `ssl.SSLContext.load_cert_chain` in place on uvicorn's `config.ssl` (server) and
   the cached console client context. Console also has `gc_expired_certs()` (7-day).
   Server now runs `uvicorn.Server(config).run()` so the hook can reach `config.ssl`.

TLS is toggled via DB ConfigStore `tls.enabled` (table `system_settings`), shared
cluster-wide — flipping it in the admin Settings tab lights up ALL nodes on next
restart. Tests: `tests/test_tls_san_renewal.py` (needs `lacme` — the `[tls]` extra).

**Follow-up hardening (all committed to main, confirmed 2026-07-06 — this was NOT
left uncommitted, an earlier version of this memory was stale on that point):**
`2c2f9e15` (2026-05-30, same day) contained reload + startup-GC failures in
console TLS init; `a3ff07a8` (2026-06-09) added an mTLS-aware container
healthcheck + boot-time init retry; `9fefe830` (2026-06-09) validates `init()`
retry params; `3e88d239` (2026-06-16) stubs the renewal backoff via a per-object
`_sleep` seam instead of patching the global `asyncio.sleep` (the same test
pattern as [[project_flaky_ci_hang_asyncio_sleep]]). No open work item is known
against this subsystem as of 2026-07-06.

**Browser→console TLS.** The console serves **plain HTTP by design** (it's the ACME
bootstrap endpoint — can't be HTTPS-only). The frontend-cert path
(`get_server_ssl_context()` / `tls.acme_directory`) was scaffolded but **never wired**
to the listener. Browser HTTPS is delivered by a **reverse proxy**: the `cluster`
compose profile now ships a `caddy` service (`deploy/Caddyfile`, `tls internal` +
`on_demand`) — browser -h2/HTTPS→ caddy:443 -h1.1/HTTP→ console:8090, reach at
`https://localhost:${CONSOLE_HTTPS_PORT:-8443}`. Caddy CAN point `acme_ca` at the
console's ACME directory (auto-approve mints any name) but it's not recommended:
unverified interop with Caddy's client, startup coupling, and the browser must trust
a private CA either way. Also fixed: console `main()` no longer rewrites its
advertised URL to `https://` (it serves HTTP; that rewrite advertised an unreachable
URL). Related: [[feedback_secrets_not_in_env]], [[feedback_no_alpine]] (used `caddy:2`, Debian).

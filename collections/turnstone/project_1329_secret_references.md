---
name: project_1329_secret_references
description: "#1329 secret:// references (v1, references only): where resolution hooks in, the resolver-only outage fallback, the gates, dropped designs, Vault/OpenBao wire facts."
metadata:
  type: project
---

#1329 asked for credentials resolved from a secret store or kept in an encrypted native store. The
maintainer cut v1 to references only (2026-10-10): the database holds `secret://` text, the value
lives in memory, and encrypting literal keys at rest is a follow-up. Bootstrap secrets from the
store (JWT secret, OIDC client secret, keyring, database URL) are #1335; the Helm config.toml mount
that `[secrets]` needs on Kubernetes is #1336. The LOCAL design note is
`docs/design/1329-secrets.md`.

**Shape:** `secret://<backend>/<path>[#<field>]` in `model_definitions.api_key`, `[models.*]`
api_key and streamable-http MCP header values. Package `turnstone/core/secret_refs` (not `secrets`:
the hosts import the stdlib module). Backends from `[secrets]` in config.toml: `file` (a file under
a dedicated root) and `vault` (Vault or OpenBao KV v2, `auth = jwt|approle`; Kubernetes is jwt with
`auth_mount = "kubernetes"`) on an httpx2 client ([[feedback_httpx2_for_new_clients]]).

**Where resolution happens, and where it never does:**
- the model registry materialises a key at load (`materialize_api_key`), so `ModelConfig.api_key`
  stays the plaintext a client sends and `get_client`/`resolve` are untouched;
- the MCP manager resolves a copy of the headers at connect (`_with_resolved_headers`) through
  `asyncio.to_thread`; `_server_configs` keeps the stored text; nothing touches the store on the
  mcp-loop thread or the console event loop;
- hosts call `get_resolver()` at startup, which builds the backends without store I/O, so a bad
  `[secrets]` table or CA bundle is a boot failure, never a per-row surprise at the first Sync.

**Outage behaviour (settled after two review rounds):** the fallback lives in the resolver only,
keyed by reference text. `invalidate()` marks cached values stale instead of deleting them, so an
operator reload (Sync to Nodes, Reconnect) asks the store again but keeps the last value when the
store cannot answer; one retryable failure cools a backend down for a few seconds, with the clock
read after the failure, since a timeout lasts as long as the cool-down. A definitive answer (not
found, denied, missing field) drops the cached entry and only that alias
(`registry.skipped_aliases`, named in the node reload reply and the console warning) or only that
MCP connect. A reference never resolved in this process is skipped during an outage. Lesson: the
first version carried the prior alias's key forward in the registry, keyed by alias, which paired an
old key with a changed reference or endpoint; a fallback must be keyed by the identity of what it
caches.

**Rules the code enforces (change them deliberately):**
- config.toml has the last word on an alias it names: a failing `[models.*]` reference removes the
  same alias's database definition instead of letting it take over;
- introducing a reference, or probing a typed one with Detect, needs `admin.mcp` without the
  service-token bypass (the gate dynamic model auth uses); Detect sends the key to a body-supplied
  base_url, so anything granted to stored keys must be gated on the typed path too;
- a stored reference echoed back unchanged on a model or MCP update is keep-existing, with no gate
  and no store round trip; `***`/empty keep-existing for literals is unchanged
  ([[feedback_api_key_write_only]]);
- references are shown verbatim where literals are masked, recorded verbatim in audit rows, and
  must be the whole value (`Bearer secret://...` is refused); stdio `env` takes no references;
- `${VAR}` is never expanded inside a reference; literals keep their expansion;
- the file root is the trust boundary: it may hold neither config.toml nor the Vault login
  credential (`secret_id_file`, `jwt_path`); containment is checked on the path as written and
  again after symlinks, with one message, so paths outside the root cannot be probed;
- one Vault token per process; a 403 re-logs in before giving up the token it had (a denied path
  answers 403 too), and a failed early re-login keeps the still-valid token.

**Dropped by design review:** a boot seal sweep and encryption at rest of literals (unneeded when
the database holds references), use-time resolution inside the registry, a periodic re-resolve tick
(nodes receive model edits only through Sync to Nodes, so a timer would push unsynced edits), a
paths allow-list (the parser refuses dot segments; httpx2 would normalise them anyway), token and
kubernetes auth methods, KV v1, an address fallback from the environment, `#field` on file
references, and a content-signature rebuild of the resolver.

**Verified against Vault 2.1.2 and OpenBao 2.5.0 dev servers:** `GET /v1/<mount>/data/<path>`
answers under `data.data`; a missing secret is 404 with `{"errors": []}`; a rejected or expired
token and a denied path both answer 403 "permission denied"; a sealed store is 503; logins at
`/v1/auth/<mount>/login` answer `auth.client_token` and `auth.lease_duration` (0 means no expiry);
Vault CE ignores `X-Vault-Namespace` and OpenBao enforces it, so it is sent only when configured.

Related: [[feedback_secrets_not_in_env]], [[project_model_definitions]].

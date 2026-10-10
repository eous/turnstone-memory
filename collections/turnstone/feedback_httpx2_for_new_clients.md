---
name: feedback_httpx2_for_new_clients
description: "New outbound HTTP client in Turnstone: httpx2, never httpx (deprecated, being migrated; maintainer 2026-10-10); an SSLContext for CA bundles, trust_env=False with credentials."
metadata:
  type: feedback
---

New outbound HTTP code uses `httpx2` (`httpx2>=2.12`, `httpcore2` declared directly). `httpx` is
deprecated in Turnstone and its remaining consumers are being migrated; do not add a new one. The
maintainer stated this while reviewing the #1329 design (2026-10-10), whose first draft put the
Vault client on httpx.

**Why:** two HTTP stacks mean two exception hierarchies (`httpx.*` is not a subclass of
`httpx2.*`), two sets of request log lines to redact and two trust-store behaviours. The SDKs have
already moved: the Anthropic SDK v1 rejects an `httpx.Client` ([[project_1050_anthropic_sdk_v1]]),
`mcp` 2.x requires httpx2 ([[project_679_mcp_sdk_v2]]), and the guarded fetch runs on it
([[project_1233_guarded_fetch_httpx2]]).

**How to apply:**
- `verify=True` uses the operating system trust store (truststore). A private CA bundle is an
  `ssl.SSLContext` from `ssl.create_default_context(cafile=...)`; httpx2 2.13 deprecates
  `verify=<path>`. Build the context at startup and map its `ssl.SSLError` to the subsystem's
  configuration error: an unreadable or non-PEM file fails at context creation, not at the first
  request, and `os.path.isfile` on the path proves nothing.
- A client that carries credentials sets `trust_env=False`, so proxy and `SSL_CERT_*` environment
  variables cannot redirect or re-trust it (precedents: the ACME client, the guarded fetch, the
  secret_refs Vault backend).
- Decide redirects explicitly; httpx2 resolves every 3xx `Location` even with
  `follow_redirects=False`.
- Catch `httpx2.HTTPError` at the boundary and translate it into the subsystem's own error type
  with a retryable flag, so callers that catch only that type never see a transport exception.
- Tests inject `httpx2.MockTransport`; a fake that answers as the real service does (status codes,
  body shapes, the auth dance) beats patched methods ([[feedback_sdk_boundary_testing]]).

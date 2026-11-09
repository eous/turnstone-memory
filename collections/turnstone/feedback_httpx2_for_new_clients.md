---
name: feedback_httpx2_for_new_clients
description: "HTTP client work: httpx2 only (httpx 0.28 unsupported from the PR finishing #1011); new credentialed clients set trust_env=False, migrated ones keep env behavior."
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

**Migrating an existing httpx 1.x client keeps its environment behavior (maintainer, 2026-10-20,
the OAuth stack).** Leave `trust_env` on where possible, so the proxy variables still apply; the
`trust_env=False` rule above is for new clients. The default trust store moving from certifi to
the OS store (truststore) is accepted: the code already on httpx2 took that change (#679), and
`SSL_CERT_FILE` / `SSL_CERT_DIR` override both libraries the same way.

**A change that touches httpx 1.x code takes that code off it (maintainer, 2026-10-19, #1403).**
The goal is to eliminate httpx 1.x from turnstone, not only to keep new clients off it. #1403's
first draft reshaped `mcp_client.py`'s client factory and left its dual httpx/httpx2 hooks and
classifiers in place; the maintainer said a change that keeps httpx 1.x does not fit the issue.
On 2026-10-19 `uv tree --invert --package httpx` listed turnstone as the only package requiring
httpx (and httpx-sse), so the end state is no httpx at all. **How to apply:** take the touched
module and the tests that drive it off httpx 1.x in the same change; anything found outside that
scope becomes an issue (the maintainer's #1403 ruling). Before deleting dual-family handling at a
seam to code still on httpx 1.x, trace that seam and show no httpx 1.x object or exception crosses
it (for #1403: the OAuth stack's token lookups return results and wrap their httpx errors).

**From the PR that finishes #1011, Turnstone supports httpx2 only (maintainer, 2026-10-20).** It
drops httpx, httpx-sse and certifi from the dependencies, and httpx 0.28 is no longer supported:
the SDK refuses an injected client that isn't an `httpx2.AsyncClient`, and no code or test handles
an httpx object or exception. **How to apply:** add no compatibility shim for httpx and never carry
both exception families. In review, a behavior that differs from the base only because the base ran
on httpx 0.28 or httpx-sse is not a regression to restore; judge it on httpx2's terms alone. An
exception httpx 0.28 raised as an `HTTPError` that httpx2 raises outside it is a question for the
SDK's documented error contract, not a reason to wrap it back.

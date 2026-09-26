---
name: reference_http_header_wire_safety
description: "Response header from user text (Content-Disposition filename): use latin1_safe_filename; TestClient misses the server control-char reject, so test it directly."
metadata: 
  node_type: memory
  type: reference
---

Any HTTP **response header value** built from user-controlled text (filenames for `Content-Disposition`, etc.) must survive TWO independent validation layers, plus a quoting trap. Starlette's own check is the one people find; the other two 500 or corrupt later and are easy to miss.

1. **Starlette latin-1 encode** — Starlette encodes header values as latin-1 and RAISES on anything outside it → 500. Bites CJK / em-dash / any codepoint ≥ 0x100. The "obvious" one.
2. **HTTP server layer control-char reject** — even when latin-1-encodable, the server rejects control bytes in a header value → 500 ONE LAYER LATER. `h11` rejects NUL / CR / LF / FF / VT; `httptools` (uvicorn's default) is stricter still. Folding to latin-1 alone is NOT enough.
3. **Quoted-string metacharacters** — the value goes out as `filename="<x>"`. The double-quote and the backslash are the quoted-string delimiters (backslash = RFC 6266 quoted-pair escape). A trailing backslash escapes the closing quote; a mid-name backslash corrupts parsing. NOT a 500 — silent filename corruption. Windows-origin uploads legitimately carry backslashes.

**Canonical fix in this repo:** `turnstone/core/web_helpers.py::latin1_safe_filename(name, *, fallback="attachment")` — drops every non-printable char (`c.isprintable()` covers all of layer 2 plus zero-width / bidi format chars) and both the double-quote and backslash, folds surviving non-ASCII to `?`, and `or fallback` so it never emits `filename=""`. Used by `get_content`, `preview_response_headers`, and the workstream export handler (PR #803, 2026-07-07). Context: [[project_preview_pane]].

**Testing trap:** Starlette's `TestClient` runs on httpx's ASGI transport, which BYPASSES the HTTP server layer (layer 2). A control-char header that 500s in production passes GREEN in a TestClient endpoint test. So unit-test the header sanitizer directly — and assert against an INDEPENDENT oracle (e.g. `0x20 <= ord(c) <= 0x7e and c not in the metachars`), not the implementation's own `isprintable()` predicate, or the test is tautological and blind to exactly the chars the impl misses (this is how a backslash hole survived one review round). The latin-1 layer (1) IS observable through TestClient.

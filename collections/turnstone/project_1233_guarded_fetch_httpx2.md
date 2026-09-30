---
name: project_1233_guarded_fetch_httpx2
description: "#1233 guarded URL fetch on httpx2 (PRs #1238, #1239; 09-30): headers, per-hop Fetch Metadata, log filter, JWT/query redaction, br/zstd; rulings and declined points."
metadata:
  type: project
---

Merged to dev on 2026-09-30 in two PRs.

- **#1238:**
  - the guarded fetch behind `web_fetch` and URL `open_preview` runs on httpx2/httpcore2
    (`httpx2>=2.12`, `httpcore2` declared directly), and both callers catch httpx2 exceptions;
  - `Accept` and `Accept-Language` go on every hop; `Sec-Fetch-Dest/Mode/Site` go only on hops to
    potentially trustworthy URLs;
  - httpx2 request log lines are cut to scheme, host and port when something lowers the logger;
  - `credential_jwt` and `credential_query_param` output-guard rules run ahead of the key-prefix
    rules;
  - a malformed redirect `Location` is a fetch error in both tools.
- **#1239:** `httpx2[brotli,zstd]`, so every httpx2 client advertises and decodes br and zstd (on
  3.13 via `backports.zstd`) under the same bounded decoding.

Other #1011 consumers stay on httpx. HTTPX2 precedents: [[project_1050_anthropic_sdk_v1]],
[[project_679_mcp_sdk_v2]].

**Maintainer rulings (2026-09-30):**
- Fetch Metadata follows the spec and browsers. Trustworthy means https, localhost names (trailing
  dot included), 127.0.0.0/8 (IPv4 shorthand via inet_aton) and ::1. IPv4-mapped addresses are
  excluded, although Python 3.13+ `is_loopback` accepts them.
- `open_preview` keeps the shared page-oriented headers, because it mostly shows the model's own
  files; the docs note that an image host may answer with an HTML page. Review finders re-raised
  this in most rounds. The reason is in the `_REQUEST_HEADERS` docstring.
- `Sec-Fetch-User` stays unset, since task agents and auto-approval run fetches unattended.
  `Sec-Fetch-Site: none` stays. The User-Agent stays `turnstone/1.0`.
- dev is not merged into main.

**Verified facts:**
- httpx2 2.13 logs `HTTP Request: %s %s "%s %d %s"` at INFO with the URL at args[1].
- Importing the Anthropic SDK with `ANTHROPIC_LOG` set lowers the `httpx2` logger. Nothing
  installed lowers `httpx`.
- httpx2 resolves every 3xx `Location` while building the response, even with
  `follow_redirects=False`. An unparseable one raises `RemoteProtocolError`; one that parses but
  can't be resolved (`http:foo`) raises a bare `InvalidURL`.
- `create_ssl_context()` uses truststore (~0.5 ms) unless `SSL_CERT_FILE` is set; dev paid ~27 ms
  per fetch via certifi.
- httpx2 advertises an encoding only when its codec is installed; before #1239 that was
  `gzip, deflate` on 3.13.

**Documented redaction limits (in code and CHANGELOG):**
- a connection-string password that itself contains a recognised scheme URL;
- double percent-encoding;
- quoted-printable or `\x` escapes before a JWT;
- JSON-escaped `\/` inside a query value;
- form-encoded bodies without `?` or `&`;
- query values cut by `( ) , ; '` before 8 characters (pinned);
- a bare JWE.

**Declined in review:**
- a handler-level log filter (scope is httpx2 only, as the docstring says);
- one shared SSL context (parity with dev; the reason is in a comment);
- lookbehind-first regex cost (~40 ms per 160 KB; a literal-first JWT rewrite is possible);
- consolidating the loopback helpers;
- the duplicated token=/key= regex text;
- the overlapping `url_cred_param` annotation;
- the browser showing `***` where the backend shows a marker followed by punctuation.

Related: [[feedback_redaction_regex_design]], [[feedback_ask_before_declining_capability]].

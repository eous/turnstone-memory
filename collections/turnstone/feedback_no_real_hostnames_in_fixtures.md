---
name: feedback_no_real_hostnames_in_fixtures
description: "Writing test fixtures or expected-URL strings: use example.com hosts of the same URL shape, never real ones (github.com etc.); live harnesses exempt."
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-09-03T22:35:52.343Z
---

The maintainer, 2026-09-03, on the MCP OAuth discovery branch when a reviewer flagged
`api.githubcopilot.com` / `github.com` in a discovery test: fixtures should not include real
external hostnames.

**Why:** a fixture that names a real host reads as a claim about that host's
behavior, ties the test to a product (see [[feedback_artifact_cleanliness]]),
and invites someone to "fix" the fixture when the real service changes. The
test is about a URL shape (a path with a significant trailing slash, an issuer
under a path on a different host), and an example domain expresses that shape
without the baggage.

**How to apply:**
- Fixtures, parametrize tables, and expected-URL strings use `*.example.com`
  (or `.invalid` / `.test`) hosts shaped like the real case: same path depth,
  same trailing slash, same port form. Keep the shape, drop the brand.
- Name the test after the shape, not the provider
  (`test_path_and_trailing_slash_are_preserved`, not `test_github_...`).
- The rule is about fixtures. The live harnesses under `scripts/obo-e2e/`
  and one-off probe scripts exist to hit real endpoints and keep them.
- Sweep at review time: `grep -rn -E "github\.com|microsoftonline|githubcopilot" tests/`
  on the touched files. Pre-existing hits elsewhere (e.g. skill `source_url`
  fixtures) are out of scope unless that code is open.

Related: [[feedback_artifact_cleanliness]] (no product names in commits, code,
comments, docs, or PR text).

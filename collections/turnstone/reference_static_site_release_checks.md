---
name: reference_static_site_release_checks
description: "Static release sites: update visible and metadata versions, test installer proxy failures, and verify a complete download before replacing a fallback."
metadata:
  type: reference
---

Static release pages can duplicate a version in structured metadata, a header, and a footer.
Enumerate every occurrence before replacing it, then verify the rendered page and metadata.
Count matches rather than matching lines when several occurrences share a line.

If an installer endpoint proxies a source script, exercise both successful fetches and upstream
errors. Include 404 responses as well as 5xx failures when checking stale-cache and local-fallback
behavior. Confirm that errors cannot replace a known-good script with an error page or empty file.

Refresh any local fallback as part of the release. Download to a temporary file, require a
successful response, verify its expected hash against the release source and inspect the shebang,
then replace the fallback atomically. Check the served result afterward. Keep host paths,
credentials, and deployment inventories in the operator's private runbook.

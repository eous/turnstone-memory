---
name: feedback_private_sdk_names_fail_loudly
description: "Reaching for a private SDK or library name: only where the public API can't do the job, and make a rename fail loudly (import, checked use, canary test), never getattr with a default."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-15T04:49:16.558Z
---

The maintainer's ruling (2026-10-14, #679): private parts of the MCP SDK are acceptable when the
library does not offer what a feature needs to work properly and reliably, but a change in the SDK
must make turnstone fail loudly, never quietly.

**Why:** the #679 port first reached into about fifteen SDK internals, several through
`getattr(obj, "_name", default)`. A minor release that renamed one would have switched a feature
off with no error (cache purges matching nothing, subscription filtering skipped): the silent
failure class #679 was written to remove. A public-looking value can be private in effect: the
response cache's key `partition` is documented as opaque to stores, and parsing it was as fragile
as reading the store's `_entries`.

**How to apply:**
- Look for the public route first: a constructor parameter, a public attribute, a protocol the
  class implements (the SDK's `ResponseCacheStore` let turnstone own its store), or deleting a
  mechanism the SDK already covers.
- For what remains: import the name, so a rename fails at startup; or check the effect where it is
  used and raise (`_replace_read_body` for httpx2's `Response._content`). Add a canary test against
  the real SDK object (`test_private_names_still_behave_as_relied_on`,
  `test_spawn_hook_records_the_server_pid`).
- Never `getattr` with a default on a private name, and never write a private attribute without
  checking that the write took.
- Keep the list of private names in use in docs/architecture.md (MCP section).

Related: [[feedback_sdk_boundary_testing]], [[project_679_mcp_sdk_v2]].

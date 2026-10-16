---
name: feedback_no_relative_era_names
description: "Naming code for a protocol or API generation: say what it does or name the dated revision; never 'modern', 'legacy', 'new' or 'old' in identifiers (maintainer, 2026-10-14)."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-15T04:49:16.761Z
---

During the #679 port the maintainer asked to drop "modern" and "legacy" from function names
(`_enter_modern_subscription`, test names such as `..._for_modern_and_send_ping_for_legacy`): they
read badly and will not age well.

**Why:** a relative label flips meaning at the next revision. Today's "modern" 2026-07-28 becomes
the old one, and "legacy" stops saying which version it means. Behavior and dates stay true.

**How to apply:** name by behavior (`_enter_subscription`,
`test_health_ping_uses_send_discover_or_send_ping_by_protocol_version`) and write the revision date
in prose ("on 2026-07-28 connections", "a 2025-11-25 server"). An upstream constant keeps its own
name (`MODERN_PROTOCOL_VERSIONS` from `mcp_types.version`); the rule covers turnstone's own
identifiers, comments and docs.

Related: [[project_679_mcp_sdk_v2]].

---
name: project_1158_mcp_image_results
description: "MCP image tool results (PR #1158): wanted, but blocked on external object storage support (#1116). Skip it in PR triage."
metadata:
  type: project
---

The maintainer wants MCP image tool results. Today `mcp_client.py` turns an MCP `ImageContent` or
`AudioContent` into a `[<mime> data, N bytes]` text placeholder, so the model never sees the
image. PR #1158 (a first pass, opened against `main`) is the prior art.

Ruling (2026-10-09): the feature is blocked on supporting an external object store such as S3
(#1116). In a PR-queue triage, skip #1158: don't recommend closing it or filing a replacement
issue.

**Why:** the 10-09 triage proposed closing it as stale (wrong base, 8 conflicts with dev, unrelated
dependency bumps); the maintainer said the work is planned.

**How to apply:** treat #1158 as parked. If image results come up in design work, start from the
object-store dependency. Related: [[project_679_mcp_sdk_v2]] (the v2 port renames `mimeType`).

---
name: feedback_stdio_findings_out_of_scope
description: "MCP finding with only a stdio consequence: file an issue, keep it out of the PR; stdio servers are getting rare."
metadata:
  type: feedback
---

The maintainer ruled on 2026-10-08, reviewing findings on #1313's shutdown drain, that a finding
that matters only for stdio transports gets an issue instead of a fix in the PR at hand.

**Why:** stdio MCP servers are getting rare, so a stdio-only consequence does not justify widening
a PR's scope.

**How to apply:** when a review finding's evidence is a stdio symptom (a helper process left
running, a pipe left open), first check whether the defect underneath also affects HTTP transport
owners. If it does, say so and judge it on the HTTP consequence. If it is stdio-only, propose an
issue and leave it out of the PR.

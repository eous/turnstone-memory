---
name: project_workstream_working_dir_grants
description: "Workstream working directory or worktree support (#872): a frozen launch-time grant with explicit (node_id, path), not workspace state; no grant = today."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-20T17:02:58.429Z
---

The maintainer's stated sequencing (2026-07-13, during the #827 session): Turnstone needs **worktree support**, but first a concept of **launching a workstream in a working directory** — and it must not overconstrain the platform, because many DevOps use cases never touch a filesystem (pure MCP tools against remote services/hardware).

Design direction converged in discussion (tracked as **issue #872** since 2026-07-19 — the issue body carries this design verbatim; #871 shipped the informational cwd/workspace layer it will build on):
- **Grant, not state**: a workstream optionally HOLDS a directory grant, set at launch, frozen (authority rank per HYPOTHESIS.md); absence = exactly today's behavior. Semantics = cwd for relative-path lowering + path confinement for the tool kernel (Π-shaping — gives judge/policy a deterministic boundary).
- **Follow the MCP pattern, don't privilege filesystem**: no grant → no filesystem tools in the envelope, no cwd in the ENV prompt section — same as "no MCP binding → no MCP tools". Filesystem is one member of a grant FAMILY; the OBO single-credential work ([[project_mcp_obo_single_token]]) is the already-shipped credential member; DevOps target-scoping (cluster/namespace/device fleet) is a future sibling.
- **Two axes to decide before the field exists** (can't retrofit): (1) node locality — a directory is the first hard node-pin on a workstream; make the pin EXPLICIT in the grant (`node_id, path`), treat it as a placement constraint like model availability, never assume shared FS (`workstreams.node_id` stays cache-not-routing for everything else); (2) coordinator-tree inheritance — attenuate-only (same dir or subpath), frozen at spawn, per the delegation appendix.
- **Worktrees = a directory PROVIDER** (mints a grant + owns lifecycle/cleanup), not a new concept; a user's real repo is an unowned grant; project-level defaults are just "workstreams in this project launch with this grant". Keep lifecycle OUT of the core.

Trigger context: review-workflow agents mutating the repo checkout (see [[feedback_freeze_tree_during_review]] incident) is what motivated worktree isolation generally.

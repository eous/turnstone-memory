---
name: project_design_constraints
description: "Design defaults for turnstone: BREAKING beats shims, scale to ≤100 nodes, simpler wins, OIDC guards inert without OIDC, no pacing PRs for reviewer fatigue."
metadata:
  type: project
---

Turnstone is open-source and local-first, with no usage telemetry by design. These defaults apply to
feature work unless a ruling says otherwise:

- **BREAKING over deprecation shims.** Users have absorbed breaking changes in most releases
  (#422 dropped five URL mounts at once; v1.7.0 listed three). State the BREAKING-vs-shim
  trade-off and expect BREAKING unless the user-facing surface is unusually wide.
- **Scale to ≤100 nodes.** Don't engineer for 1000+ nodes; don't ship designs that break under 50.
- **Simpler wins.** Complexity must advance real user need; "technically interesting" is not the
  bar. Keep PRs reviewable by an outside skim and commit messages tight.
- **Auth paths:** most installs run no OAuth/OBO/OIDC. Guards and validators on those paths must
  be inert for no-OIDC installs (no parsing, warnings or refusals) and fail loudly for the
  enterprise deployments that use them.
- **Don't pace PRs for reviewer fatigue.** Bundling related work into one PR is fine when it saves
  review round-trips.

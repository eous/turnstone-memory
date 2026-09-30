---
name: project_no_cross_version_support
description: "Deletion blocked by 'an older proxied node might use this': mixed-version clusters unsupported (the maintainer 2026-07-24; 1.8, maybe 1.7 only); cite policy, delete."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-25T06:21:15.455Z
---

The maintainer, 2026-07-24: **cross-version clusters are not a supported configuration.** Once 1.8
ships, only 1.8 is supported, and 1.7 only depending on how much breaks. Older nodes proxied by a
newer console are explicitly out of scope.

**Why:** it settles a class of objection that otherwise blocks deletions. Console-side code
that touches a *proxied node's* DOM or API is version-coupled by construction — `proxy_index`
fetches the remote node's own `index.html` and injects into it, so the DOM comes from
whatever version that node runs, not from our tree. That makes "this looks dead, but a
v1.5.x node would still exercise it" a permanently available argument for keeping anything.
It is not a valid argument: don't spend rounds proving old-version reachability.

Nothing structurally *prevents* skew (checked 2026-07-24): `_discover_nodes` registers any
`server` service row with a fresh heartbeat and never reads a version. Version drift is *monitored* (`version_drift`, rail amber outliers), never blocked.
So reachability arguments will always technically succeed — the policy, not the code, is
what closes them.

**Which assets a proxied page takes from the console (checked 2026-09-29 on dev 08539357):**
`proxy_index` rewrites only HTML `href` and `src` attributes that start with `/static/` or
`/shared/`, and the injected shim rewrites only root-relative `fetch()` and `EventSource()` URLs.
Root-absolute URLs set from JavaScript (the `script.src` of the mermaid and hls loaders) and those
inside CSS `url()` are not rewritten, so the browser loads them from the console's own mounts, in
the console's version, and every proxied node shares the console's cached copy. The #1229 font
change relies on this for its font files. Under this policy that skew is acceptable.

**How to apply:** when a deletion is gated on "an older node might still use this," cite the
policy and delete. Scope correctness work to supported versions. If a change genuinely
strands old nodes, say so plainly in the PR/release notes rather than carrying the code.

Worked example: the console proxy shim's node-picker (288 lines JS + 94 lines CSS) was dead
for every node >= v1.6.0 and live only for <= v1.5.x; this policy is what made deleting it
correct. See [[project_900_interactive_backport]] for the sibling seam, and
[[feedback_review_convergence_methodology]] for the at-site-ruling habit that would otherwise
be the fallback.

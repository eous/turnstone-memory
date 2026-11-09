---
name: project_1326_helm_mcp_sidecars
description: "#1326 Helm MCP servers (2026-11-08): same-pod sidecars sharing /workspace adopted beside per-server Deployments; PR order (tini fix, sidecars, Deployments after #1327), constraints, deferrals."
metadata:
  type: project
---

**Decision (2026-11-08):** the proposer's comment on #1326 (extra containers in the server pod
sharing a workspace volume) is adopted as a second shape next to the issue's per-server Deployments.
It is the only shape that shares the agent's files, which the #1322 thread shows is the real need
(clone, edit, run tests, push). Both shapes are HTTP only; stdio stays out of the chart
([[feedback_stdio_findings_out_of_scope]]).

**PR order.**
1. Chart 0.3.7 (PR #1586): both Deployments name tini in `command` (the chart's `command` replaces the image's
   entrypoint, so tini was bypassed and the pods shared their process namespace for reaping). Tini
   is PID 1 again, `shareProcessNamespace` goes. Verified in the 1.9.3 image: Python as PID 1 leaves
   a defunct child, tini reaps it.
2. `server.sidecars`: container specs passed through plus required `port`, optional `path`
   (default `/mcp`); native sidecars (initContainers, `restartPolicy: Always`) with an unconditional
   `kubeVersion` floor of 1.29; one emptyDir at `/workspace` in the server container and every
   sidecar (the image already sets `TURNSTONE_WORKSPACE=/workspace`); pod
   `automountServiceAccountToken: false` with the token projected into the server container only;
   template fails on a duplicated port or the server's port; NOTES.txt prints each
   `http://localhost:<port><path>`; a new chart README (none exists) carries the guidance.
3. Chart 0.3.9: `config.file` (verbatim config.toml text in a ConfigMap, mounted in both pods,
   `TURNSTONE_CONFIG`, checksum of the text rolls the pods) and `config.secretMounts` (Secrets at
   explicit paths, both pods) so `secret://` references work on Kubernetes. Render refuses: text
   Helm cannot parse, the `[database]` connection keys, `[auth] jwt_secret`, the `[security]`
   encryption keys, `[oidc] client_secret`, mounts overlapping /etc/turnstone, the token path under
   either name, /workspace or each other (/var/run read as /run). Rulings: the world-readable
   config.toml warning deleted outright; `_file_config` refuses a root containing the mounted
   service-account token, gated on the file existing so non-Kubernetes deployments are untouched.
4. PR 4 (ruled and implemented 2026-11-08; three review passes): the render requires `auth.existingSecret` or `auth.jwtSecret` (autogeneration via `lookup` was
   tried and backed out: the most common GitOps engine renders without a cluster, so every sync
   would mint a new value; references cover the need); `config.file` rendered into a Secret so the
   `[security]` keys and `[oidc] client_secret` may live there; `config.existingSecret` for an
   operator-owned file; `load_config` raises on an unreadable or unparseable file (the read decides; `is_file()` hid a
   permission problem on a 0750 parent directory as an empty configuration).
5. PR 5 (#1335 items 1 and 2, ruled 2026-11-08): `[oidc] client_secret` then `[auth] jwt_secret`
   as `secret://` references in env and file, resolved once at startup, fail closed, rotation by
   coordinated restart; keyring and database URL stay out. Review found four other readers of the JWT secret
   taking the raw value; all now share one memoised derivation in auth.py. Ruling: a runtime
   reference (model key, MCP header) whose value equals a registered bootstrap secret is refused in
   SecretResolver.fetch by constant-time digest compare, so the store's bootstrap secrets stay out
   of reach of reference authors. Test flake with an unclosed sqlite connection: #1592.
6. PR 6 (ruled 2026-11-08): an explicitly named config path that does not exist raises (only the
   default path may be absent; doctor notes such a path and reads the files it discovered); the
   sha256 of the Secret-backed config file stays in the pod annotation, with the README saying what
   it exposes. A sha256 of an inline `auth.jwtSecret` on the pod templates was ruled in, then
   withdrawn the same night: anyone who can read pods could crack a human-chosen value offline, and
   Helm has no keyed or slow digest to prevent it; a changed inline secret needs a rollout restart,
   as an existing Secret already does.
7. PR 7 (2026-11-08): `oidc.*` values (issuer, clientId, redirectBase, clientSecret or
   existingSecret, scopes, providerName) rendered as `TURNSTONE_OIDC_*` env in both pods, the client
   secret through secretKeyRef like the JWT secret and allowed to be a reference; redirectBase alone
   serves per-user MCP authorization; every check (strings, the required four, issuer and redirect
   base shapes as the application checks them) runs in one define that the env and the Secret both
   call. The file route (render the values into config.file) was rejected: a generated `[oidc]`
   table cannot merge into an operator file that already has that header, so docs/oidc.md's
   file-over-env preference is not followed on the chart and a reference is the way to keep the
   value out of env. The chart refuses the file's `[oidc]` keys the values set. One `redirect_base`
   for two origins means SSO completes on one UI only: #1594.
8. Per-server Deployment + Service (the issue's original v1) and its NetworkPolicy question, after
   #1327 gives both shapes declarative registration. Operators can already run such a server by
   hand and register its URL.

**Constraints to state publicly:** sidecars must speak Streamable HTTP (a stdio-only image wraps a
bridge inside its own image); a sidecar image bump rolls the server pod and cuts live sessions, so
API-backed servers belong in their own Deployment; until #1327 the console's row for a localhost
sidecar shows an error (coordinators have no node filesystem, so that is correct); resources per
sidecar; auth `none` lets any process in the pod, the model's shell included, call the server
outside per-tool approvals (a NetworkPolicy limits pods, not processes in the server pod), so the
README and NOTES recommend a static auth header wherever the image can require one.
Review-confirmed facts for the README (2026-11-08): a sidecar listening on all interfaces answers any
pod at the pod IP without a NetworkPolicy; the kubelet's emptyDir is root-owned 0777, so git refuses
a repository at /workspace itself (clone into subdirectories); a sidecar's own volumeMounts may name
only the workspace volume (the token volume is the server's); a sidecar that cannot start keeps the
server on that pod from starting; the console's connection test fails for a localhost URL.

**Deferred:** a bridge image (non-goal), a PVC-backed workspace (emptyDir in v1), chart lint in CI,
the rarer OIDC settings as chart values (they stay in the file's `[oidc]` table).

**Rulings:** current stable line only, no compatibility paths ([[feedback_current_stable_only]]);
chart design calls are delegated ([[feedback_helm_chart_design_ownership]]); the stacked branches
of PRs 3 to 7 go up as one PR merged by rebase-and-merge, so the five commits land on main as they
are (maintainer, 2026-11-08).

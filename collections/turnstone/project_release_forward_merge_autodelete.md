---
name: project_release_forward_merge_autodelete
description: "After a release or main-to-dev forward-merge PR (v1.8.2, 09-04): auto-delete removed main, breaking publish; check BOTH publish runs, fix via gh run rerun."
metadata: 
  node_type: memory
  type: project
  modified: 2026-09-04T22:36:49.444Z
---

# Release publish hazard: forward-merge PR deletes `main`

**What happened (2026-09-04, v1.8.2):** The maintainer forward-merged `main` into `dev`
via PR #1087. The repo has `delete_branch_on_merge: true`, so GitHub deleted
`main` 3 s after the merge. Both publish workflows (`docker-publish.yml`,
`publish.yml`) are `workflow_run` on CI and classify the release with
`git show origin/main:pyproject.toml`; the Docker run hit
`fatal: invalid object name 'origin/main'` and failed. The maintainer restored `main`
(head_ref_restored, same SHA) ~10 h later and re-ran the PyPI publish, but not
the Docker one. Fixed by `gh run rerun <run-id> --failed` — the stored
`workflow_run` payload is reused, so the same-repo tag gate still passes.

**Why:** The two publish workflows are independent runs; a fix for one does
not re-run the other. Rerun (not re-tag) is the repair — re-tagging would
collide with the immutable-ish PyPI release.

**How to apply:**
- After any release, check BOTH publish workflows for a non-skipped run on the
  tag: `gh run list --workflow=docker-publish.yml --json conclusion,createdAt`
  (skipped = fork/PR gate; look for success/failure).
- Anonymous GHCR check needs no token scope:
  `curl "https://ghcr.io/token?scope=repository:turnstonelabs/turnstone:pull"`
  → bearer → `HEAD /v2/turnstonelabs/turnstone/manifests/<tag>`
  (`gh api .../packages/...` needs `read:packages`, which the CLI token lacks).
- Doc note added to `docs/releasing.md` (forward-merge paragraph), left
  uncommitted on `main` for the maintainer to commit or drop.
- Related: [[project_current_state]] release recipe, [[feedback_git_workflow]].

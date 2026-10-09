---
name: feedback_js_edits_formatter_churn
description: "Editing turnstone JS or JSON where an agent formatter hook runs prettier: it reflows unrelated code (no repo prettier config); script the edit in Bash and diff for churn."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-08T14:07:09.438Z
---

The repo has no prettier config and no JS format check in CI, and its browser JS is not
prettier-clean (`coordinator.js` at HEAD already differs from prettier's output). Some agent
setups, including the maintainer's, run a post-edit hook that applies `prettier --write` to any
`.js`, `.ts` or `.json` file touched by the edit tools, so a one-line edit can reflow unrelated
functions elsewhere in the file. Check whether your setup has such a hook. In #1292 A2 (2026-10-08) deleting one filter clause reflowed two unrelated hunks in
`coordinator.js` and collapsed an array literal in `governance.js`.

**Why:** unrelated reflows bloat a review diff and attribute churn to the change; an earlier
session hit the same thing ([[project_frontend_render_corruption]]).

**How to apply:** with such a hook, make JS/JSON edits with a short Python script run through
Bash (the hook does not fire), or rebuild the file from `git show HEAD:<path>` plus the intended change; then check
`git diff` for hunks you did not intend. Still give your own hunk prettier's shape: some files
(`interactive.js` at 10-08) are prettier-clean, and a hunk left in another shape turns into churn
on someone's next format-on-save. Python files fared better on 10-08: black was not
installed, so the hook fell back to `ruff format`, which the repo enforces; still run the pinned
`ruff format --check`.

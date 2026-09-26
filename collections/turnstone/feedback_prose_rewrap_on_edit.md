---
name: feedback_prose_rewrap_on_edit
description: "Editing text inside a wrapped comment or docstring: replace and re-wrap the whole paragraph to 100 cols, then check with awk; ruff ignores E501."
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-07-25T08:13:55.827Z
---

Editing prose inside an already-wrapped comment or docstring by replacing a
*phrase* leaves the surrounding line breaks where they were — correct for the
old text, wrong for the new. Shorter replacement → orphan stub lines
(`# is the`, `fence-escaping is NOT` / `done here.`); longer → lines past the
limit. **Replace the entire paragraph and re-wrap every line of it** to the
file's limit (turnstone: 100).

**Why:** The maintainer flagged this 2026-07-25 as a habit that had crept in across
several sessions — Copilot commented on it on PR #912. It comes from optimizing
Edit calls for minimal diff noise, which is right for code and wrong for wrapped
prose, where the paragraph is the atom.

**How to apply:** when an Edit touches text inside a `#` block or a docstring,
set `old_string` to the whole paragraph, not the changed clause, and re-flow the
replacement. Then verify — **the gates cannot see this**: turnstone's
`pyproject.toml` sets `ignore = ["E501"]` so `ruff check` does not enforce line
length, and `ruff format` never re-wraps comments or docstrings. A 106-char
comment passes "All checks passed!" cleanly. Check by hand:

```bash
awk 'length>100 {print FILENAME":"FNR" ("length")"}' <changed files>
```

and scan for stub lines (a comment line far shorter than its neighbours mid-
paragraph). Do not report "gates clean" as evidence the wrapping is fine.

Known unfixed sites, merged in #912, to clean up alongside the shelved seam PR
([[project_opus5_cutshort_seam]]): `_anthropic.py:1293`,
`tool_advisory.py:103-104`, `tool_advisory.py:160-161`.

Related: [[feedback_pre_commit_gates]], [[feedback_artifact_cleanliness]].

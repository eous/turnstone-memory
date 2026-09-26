---
name: feedback_uv_run_extras_pruning
description: "After any 'uv run' variant ran mid-session, or the pytest passed-count drops: venv lost extras; uv sync --frozen --all-extras, then test via .venv/bin/python."
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-09-02T22:32:38.674Z
---

A bare `uv run <cmd>` (e.g. from `scripts/obo-e2e/keycloak_e2e.sh`, or any helper
script) re-syncs `.venv` to the DEFAULT dependency set — no extras. Two symptoms
seen in one session (2026-08-03):

- `uv run mypy` → `ModuleNotFoundError: No module named 'mypy'` minutes after it
  worked. Workaround: `uv run --with mypy mypy …`.
- The full pytest run reported **10212 passed, exit 0** — ~96 extras-gated tests
  (channels/voice/etc.) silently ABSENT from collection because their imports
  skip when the extra isn't installed. It looked like a normal green run.

**Why:** extras pruning is invisible in `-q` output; module-level skip guards
convert "dependency missing" into "module skipped", not an error.

**How to apply:**
- After ANY script that shells `uv run` (especially the obo-e2e harnesses), run
  `uv sync --all-extras` before trusting a suite run.
- Treat an unexplained DROP in the passed-count as a collection problem first:
  `uv run pytest tests/ -q --collect-only | tail -1` and compare against the
  last known collected total (track it in the session, ~10318 as of 2026-08-03).
- Comparing passed-counts across runs is a cheap, high-yield invariant — it is
  how this was caught ([[feedback_measure_before_accepting_a_finding]]).

**Second incident (2026-09-02), three more triggers:** `uv run --group dev` /
`uv run --extra dev` (to get mypy) re-synced the venv UNDER a concurrently
running focused pytest and one judge test failed spuriously (passed on HEAD and
on the worktree after restore — nearly reported as a diff regression);
`uv run --project <turnstone checkout> …` invoked from ANOTHER cwd pruned pytest
itself out of `.venv`; and without extras `tests/test_drain_stream.py`
(`import httpx2`) is a hard COLLECTION ERROR, so `-x` full runs die at 3 s.
Restore = the CI command `uv sync --frozen --all-extras`; then run the suite
with `.venv/bin/python -m pytest` (never `uv run`) and the CI marker expression
`-m "not live and not e2e_recovery"`. Never run `uv run` variants in parallel
with a test run.

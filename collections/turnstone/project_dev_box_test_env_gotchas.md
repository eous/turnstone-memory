---
name: project_dev_box_test_env_gotchas
description: "Before headless Chrome (locked keyring: --password-store=basic), an SDK boundary failure (needs a lock-matching env) or a red test_doctor seeded-model test (reads ~/.config/turnstone)."
metadata:
  node_type: memory
  type: project
  modified: 2026-10-15T03:44:33.691Z
---

Environment problems can resemble code regressions. Two useful diagnoses from 2026-09-19:

- A headless browser may block on a locked keyring while initializing encrypted stores. In the
  observed failure, real navigation hung even to a closed loopback port while `data:` URLs
  rendered. A disposable test profile with `--password-store=basic` removed the dependency and
  let the harness run. Restrict this setting to synthetic tests without saved credentials.
  On a dev box whose keyring stays locked (confirmed 2026-10-13), every headless Chrome run needs
  the flag up front (livepass screenshots stalled ~30s each without it).
- SDK stream-boundary tests can fail when installed packages differ from `uv.lock`. A fresh
  environment using the locked dependencies distinguished environment drift from a transport
  exception-normalization defect.
- `tests/test_doctor.py::TestResolveBrainIntegration::test_resolves_seeded_model` reads the
  developer's `~/.config/turnstone/config.toml`, so where that file defines models it fails with
  that config's model name instead of the seeded `test-model` (#1393; 2026-10-14: the only failure
  in a 16,766-test run). It passes with `HOME` and `XDG_CONFIG_HOME` pointed at an empty directory,
  and CI has no such file. Rerun it that way before reading it as a regression.

**Why:** the test process uses the installed browser profile and interpreter environment, which
may differ from the intended fixture or dependency lock.

**How to apply:** compare installed versions with the lockfile and reproduce in an isolated
environment (`UV_PROJECT_ENVIRONMENT=<temporary-directory> uv sync --frozen --all-extras`). Use a
disposable browser profile and a minimal navigation probe when diagnosing browser timeouts.

Related: [[feedback_uv_run_extras_pruning]], [[feedback_dont_dismiss_as_preexisting]].

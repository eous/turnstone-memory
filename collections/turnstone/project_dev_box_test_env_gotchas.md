---
name: project_dev_box_test_env_gotchas
description: "Test environment diagnosis: browser keyring hangs can mimic network failures; SDK boundary failures need a lock-matching isolated environment."
metadata:
  type: project
---

Environment problems can resemble code regressions. Two useful diagnoses from 2026-09-19:

- A headless browser may block on a locked keyring while initializing encrypted stores. In the
  observed failure, real navigation hung even to a closed loopback port while `data:` URLs
  rendered. A disposable test profile with `--password-store=basic` removed the dependency and
  let the harness run. Restrict this setting to synthetic tests without saved credentials.
- SDK stream-boundary tests can fail when installed packages differ from `uv.lock`. A fresh
  environment using the locked dependencies distinguished environment drift from a transport
  exception-normalization defect.

**Why:** the test process uses the installed browser profile and interpreter environment, which
may differ from the intended fixture or dependency lock.

**How to apply:** compare installed versions with the lockfile and reproduce in an isolated
environment (`UV_PROJECT_ENVIRONMENT=<temporary-directory> uv sync --frozen --all-extras`). Use a
disposable browser profile and a minimal navigation probe when diagnosing browser timeouts.

Related: [[feedback_uv_run_extras_pruning]], [[feedback_dont_dismiss_as_preexisting]].

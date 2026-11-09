---
name: feedback_log_assertions_use_record_fields
description: Asserting on log output in a test: check caplog.records with tests._session_helpers.log_has_field, never key=value tokens from caplog.text (the renderer depends on full-suite order)
metadata:
  type: feedback
---
Tests that read `key=value` tokens out of `caplog.text` pass alone and in targeted runs, then fail
in CI's single-process full suite. `tests/test_logging.py` configures logging, so records in later
files render as dicts. 2026-10-29: H1 in a commit review, then eight issuer-pin tests on PR #1513,
which cost a CI round.

**Why:** logging configuration is process-global, so the renderer a test sees depends on what ran
before it in the same process.

**How to apply:**
- Pick the record from `caplog.records` by event name, then assert each field with
  `log_has_field(record, key, value)`. It accepts the console, dict and JSON forms.
- Checking only that an event name is `in caplog.text` is safe.
- Before pushing tests that assert on logs, run `tests/test_logging.py` first in the same pytest
  process.

Related: [[feedback_pre_commit_gates]].

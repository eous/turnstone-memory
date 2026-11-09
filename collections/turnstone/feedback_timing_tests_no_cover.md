---
name: feedback_timing_tests_no_cover
description: "Writing a wall-clock-bounded test (a linear-time guard): mark it @pytest.mark.no_cover, size it so the regression overruns the bound; CI's 3.13 tracer is several times slower."
metadata:
  type: feedback
---

CI runs `pytest --cov=turnstone` with branch coverage. On Python 3.13 coverage falls back to its
C tracer (its sys.monitoring core handles branches only from 3.14), which slowed a 0.37 s
linear-time case to 2.58 s on the runner and failed its 2.0 s bound (PR #1569). Shrinking the
input until it fit cost the case its power to catch the regression it guarded. The maintainer
chose `@pytest.mark.no_cover` instead: pytest-cov pauses tracing for that test, and the input
keeps the size that makes the regression overrun the bound.

**Why:** a timing bound has to hold under every lane's tracer and still tell linear-time code from
a slower regression; tracer overhead changes with the Python version, the regression's cost does
not.

**How to apply:** mark timed tests `no_cover`, and size their inputs so the regression class (a
copy of the input per tag, a rescan per match) overruns the bound several times over at plain
speed. Check locally under `COVERAGE_CORE=ctrace ... --cov=turnstone`. Pin budgets, caches and
counters functionally (count the calls) rather than by time, and leave untimed tests unmarked so
coverage keeps their branches.

**When a constant caps the input (#1568, 2026-11-05).** `preview.py`'s head lookups read only the
first 64 KB, and at that size the old and new code were too close for any bound CI could keep.
The test patches the cap up to 1 MiB inside the timed block
(`patch("turnstone.core.preview._HEAD_SCAN_LIMIT", 1 << 20)`), which puts the two far apart on
every shape. Raise the cap in the test rather than tightening the bound.

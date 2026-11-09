---
name: feedback_scanner_score_drift_ok
description: "Changing the skill risk scanner (skill_scanner.py, its patterns or counting): score drift from the old heuristics is fine, esp. when more accurate; never chase exact parity (maintainer, 2026-10-23)."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-23T14:01:25.252Z
---

When a scanner fix (a linear-time rewrite, fence counting, a pattern bug) makes some texts score
differently from the old scanner, the drift is acceptable, especially when the new score is more
accurate. Do not build emulation layers to reproduce the old heuristics' exact counts, and do not
claim "detects what it did before" in the CHANGELOG; describe the change and note drift where it
matters.

**Why:** parity with the old heuristics has no value of its own. On the skill-scanner hardening
branch, review round 2 found the parity-preserving rewrites breeding findings; the maintainer chose
to document corner-case drift instead of emulating base exactly.

**How to apply:** in scanner work, judge a change by accuracy and simplicity, measure tier moves on
the local corpus to report them, and accept drift. Judge a change in what the scanner detects on
its own merits, not against the old counts. See [[feedback_nonconverging_reviews_mean_simplify]].

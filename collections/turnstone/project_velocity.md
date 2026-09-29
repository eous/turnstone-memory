---
name: project_velocity
description: "Picking up a brief or memory older than 1-2 weeks: dev churns ~22K LOC/week (2026-09-29, down from ~36K the month before), so re-spike cited file:line locations before coding."
metadata:
  node_type: memory
  type: project
---

Refreshed 2026-09-29 on `dev`, the integration branch since 1.8.0: `git log --since="4 weeks ago" --numstat` shows 105 commits and ~86K lines of churn (64.0K added / 22.3K deleted, lockfiles excluded), about **22K LOC/week**, down from 80 commits and ~145K lines (about 36K LOC/week) in the four weeks before. The maintainer's read (2026-09-29): the core feature set has matured, and most new work is refinement rather than new capability.

Earlier measurements: 2026-07-06 on `main`, ~151K lines over 4 weeks (112.5K added / 38.9K deleted), about 38K LOC/week across 402 commits, with commit frequency up 67% on the 4 weeks before (v1.7.0 had shipped stable on 2026-07-05); 2026-05-10, ~50K LOC/week over the prior 3 months (~600K cumulative churn).

**Why this matters (unchanged from the original finding):**
- Design briefs go stale in days, not weeks. File paths shift, function signatures change, line references rot.
- The "Frozen against `main` at <commit>" header pattern in any brief is load-bearing, not ceremony — it signals which world the brief describes.
- [[feedback_sdk_boundary_testing]]'s spike-before-planning discipline earns its keep at this pace — verified beats assumed when the codebase moves under you.
- PR implementation should follow brief writing tightly; briefs sitting on a shelf for more than 1-2 weeks need re-verification before code starts.

**How to apply:**
- When picking up ANY memory file or brief older than ~1-2 weeks, run a quick re-spike on the key cited file:line locations before writing code — the brief tells you what to verify.
- Don't propose long-lived design artifacts under `docs/design/` — they decay. Brief, implement, then delete or archive.
- Re-measure this figure on `dev` if it's been more than ~4-6 weeks since 2026-09-29. It has fallen from ~50K (May) to ~38K (July) to ~22K (September) LOC/week, so re-check rather than assume any of these still holds.

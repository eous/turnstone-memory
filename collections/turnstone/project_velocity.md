---
name: project_velocity
description: "Picking up a brief or memory older than 1-2 weeks: Turnstone churns ~38K LOC/week (as of 2026-07-06), so re-spike cited file:line locations before coding."
metadata:
  node_type: memory
  type: project
---

Refreshed 2026-07-06: `git log --since="4 weeks ago" --numstat` on main shows ~151K lines of total churn (112.5K added / 38.9K deleted) ≈ **38K LOC/week**, against 402 commits in the last 4 weeks vs. 240 in the prior 4 weeks (+67% commit frequency). Read this as sustained-fast, not slowing down — more, smaller commits rather than fewer, bigger ones (consistent with a project past its initial big-feature-drop phase and into steady hardening + a fast release cadence: v1.7.0 shipped stable 2026-07-05). Original baseline: ~50,000 LOC/week measured 2026-05-10 over the prior 3 months (~600K cumulative churn).

**Why this matters (unchanged from the original finding):**
- Design briefs go stale in days, not weeks. File paths shift, function signatures change, line references rot.
- The "Frozen against `main` at <commit>" header pattern in any brief is load-bearing, not ceremony — it signals which world the brief describes.
- [[feedback_sdk_boundary_testing]]'s spike-before-planning discipline earns its keep at this pace — verified beats assumed when the codebase moves under you.
- PR implementation should follow brief writing tightly; briefs sitting on a shelf for more than 1-2 weeks need re-verification before code starts.

**How to apply:**
- When picking up ANY memory file or brief older than ~1-2 weeks, run a quick re-spike on the key cited file:line locations before writing code — the brief tells you what to verify.
- Don't propose long-lived design artifacts under `docs/design/` — they decay. Brief, implement, then delete or archive.
- Re-measure this figure again if it's been more than ~4-6 weeks since 2026-07-06 — the rate is trending down slightly (50K→38K) and is worth re-checking rather than assuming either number still holds.

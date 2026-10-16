---
name: feedback_stable_changelog_short
description: "Writing a stable-line changelog section (main, X.Y.Z patch): short, digestible entries of one or two lines, written from each backported commit's own change, never copied from dev's long entries."
metadata:
  type: feedback
---

The maintainer, 2026-10-09, preparing 1.8.6: stable release changelog entries should be shorter and
more digestible than dev's paragraph-length entries.

**Why:** stable release notes are read by operators deciding whether to upgrade; dev's entries
explain mechanisms at length. Copying dev's text also risks describing later dev-only edits; for
1.8.6 the copy was identical, but extracting by entry title missed a second entry the same commit
added (the redaction-speed fix).

**How to apply:**
- One or two lines per entry: a bold lead-in naming what changed for the user, then the effect.
  Keep the `### Changed` / `### Fixed` / `### Security` sections and the `(#NNNN)` references.
- Inventory every bullet each backported commit added to `CHANGELOG.md` (count `+- **` lines in
  its own diff), then summarise from that text, not from dev's current file.
- Related: [[project_current_state]] (release recipe), [[feedback_artifact_cleanliness]].

---
name: feedback_prefer_read_edit_tools
description: "File changes: default to Read then Edit; a python heredoc script is only for large mechanical sweeps like mass renames, never the first reach."
metadata: 
  node_type: memory
  type: feedback
---

The maintainer (2026-07-10, mid-#817): make changes with Read and Edit by default; python is acceptable only for a LARGE number of mechanical changes (such as renaming a variable used many times), and should never be the first tool reached for.

**Why:** Edit-based changes are reviewable in the transcript as diffs against known anchors; a python heredoc hides the actual change inside string-replace logic, can silently no-op on a stale pattern (assert-guarded or not), and bypasses the harness's file-state tracking and hooks visibility.

**How to apply:** default to Read → Edit (or Write-after-Read for a full-file rewrite). Reach for a python script only when the change is a bulk mechanical sweep across many occurrences/files (mass rename, systematic import rewiring) where per-site Edits would be error-prone noise. EXCEPTION that stays programmatic: writing literal `\uXXXX` escape SEQUENCES into source — typing them in Edit args gets transport-decoded to raw bytes ([[feedback_tool_write_escape_decoding]]), so those bytes must be built with `chr()`/string concat.

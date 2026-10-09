---
name: feedback_task_agents_share_main_paths
description: "Touching task-agent tool handling (approval, truncation, guard, advisories): reuse the main session's path; never special-case task agents (#1295, #1296)."
metadata:
  type: feedback
---

The maintainer ruled on 2026-10-06, on finding that task agents auto-run `web_fetch` and
`web_search` from a `TASK_AUTO_TOOLS` list the main session never reads, that task agents should
not be special-cased like that. Earlier the same day, on the agent's fixed 16,000-character head
clip, they noted that reusing more of the main session's code in task agents would simplify the
code base.

**Why:** every agent-only path drifts from the main loop. The fixed clip forced agent-only guard
code in #1291 (cut notice, clip recheck, a copied list guard), and the approval bypass skips the
intent judge, admin deny policies and smart approvals that the main session applies. HYPOTHESIS.md
grounds it: a child holds at most its parent's grants (authority attenuates down the tree).

**How to apply:**
- A task agent decides approval, truncation and guard handling exactly as the main session does;
  differences need a stated reason, not just history (both lists date from the initial commit).
- When a fix touches an agent-only path, prefer moving both loops onto one shared helper over
  patching the agent copy, and say so in the PR.
- Filed: #1295 (context-aware truncation + shared per-result path), #1296 (approval).
  Related: [[feedback_dont_delete_a_derivation_to_resolve_disagreement]],
  [[project_task_agent_modernization]].

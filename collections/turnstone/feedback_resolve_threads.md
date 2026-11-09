---
name: resolve-review-threads
description: "Resolving GitHub PR review threads (Copilot, code-quality bot): resolveReviewThread, not minimizeComment; 'no effect' on a Protocol stub's `...` is a false positive: resolve, no code change."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-30T00:29:39.942Z
---

To resolve Copilot review conversations on GitHub PRs, use the `resolveReviewThread` GraphQL mutation (not `minimizeComment`). Minimizing hides the comment text but leaves the thread unresolved.

**Why:** minimizeComment is a display-level action; resolveReviewThread is the semantic action that marks the feedback as addressed.

**How to apply:** When resolving review feedback (Copilot or the code-quality bot) after addressing or dismissing it, query `reviewThreads` for unresolved thread IDs and call `resolveReviewThread` on each.

**The code-quality bot's "Statement has no effect" on a Protocol stub's `...`** (maintainer OK 2026-10-29, #1513): resolve the thread with no code change and no reply, as the maintainer did on #1007, #1309 and #1365. A docstring followed by `...` is the repo's stub form (326 stubs at the time, none docstring-only), and the rule fires on one-line `-> int: ...` stubs too, so it recurs on every PR that adds a storage-protocol method. A load-bearing `await` flagged by the same rule is the other known false-positive shape (#844). Any other code-quality finding is still triaged on its merits.

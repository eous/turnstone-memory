---
name: resolve-review-threads
description: "Resolving Copilot review threads on a GitHub PR after addressing them: call the resolveReviewThread GraphQL mutation, not minimizeComment."
type: feedback
---

To resolve Copilot review conversations on GitHub PRs, use the `resolveReviewThread` GraphQL mutation (not `minimizeComment`). Minimizing hides the comment text but leaves the thread unresolved.

**Why:** minimizeComment is a display-level action; resolveReviewThread is the semantic action that marks the feedback as addressed.

**How to apply:** When resolving Copilot feedback after addressing it, query `reviewThreads` for unresolved thread IDs and call `resolveReviewThread` on each.

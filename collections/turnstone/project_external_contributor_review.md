---
name: external-contributor-review-process
description: "Reviewing external-contributor PRs (#312-#316, #750): one review agent per PR, verify against source, merge with thanks, then ship follow-up hardening PRs."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-20T16:59:20.019Z
---

**Date:** 2026-04-06
**Status:** Complete. PRs #312-#316 shipped, follow-ups in #319, #322, #323, #324, #328.

## What happened

First significant external contribution — 5 PRs adding Google provider, judge hardening,
workstream management, UI enhancements, and console changes. Reviewed with parallel
Sonnet agents, verified findings against actual source, merged with "thank you" comments,
then shipped follow-up fixes.

## Key findings

- **Auth scope gap**: New POST endpoints fell through to "read" scope (WRITE_PATHS is
  exact-match only; parametric paths need explicit rules in required_scope())
- **Judge bugs**: cancel_event check removed from inner poll loop, fallback delivery
  off-by-one (items[idx:] should be items[idx+1:])
- **Theme POST/PUT mismatch**: Console route accepts PUT, JS sent POST — silently 405'd
- **Gemini thought_signature**: Provider-specific field dropped by cherry-pick extraction.
  Fixed via provider_blocks fidelity lane (same pattern as Anthropic)

## Process that worked

1. Clone/diff all PRs, launch parallel review agents (one per PR)
2. Verify each finding against actual source (not just diffs)
3. Categorize by feature+component, not priority or PR number
4. Track verified findings in a local review checklist
5. Code review + design review + security review our own fixes
6. Address Copilot/CodeQL feedback on each push

## Stats

- 68 items identified across all review passes
- 65 completed, 2 deferred (storage mixin, keyboard shortcuts later done), 1 false positive
- 4 PRs shipped as follow-ups

## Second instance (2026-07-02)

The pattern recurred: PR #750 ("Multi-user chat context clarification and tool improvements") was
reviewed 2026-07-02, found merge-worthy with 3 majors flagged (shared-state durability, fork meta
drop, unfenced labels) plus a worklist — full detail in [[project_pr750_multiuser_context_review]]
(not duplicated here). It shipped, followed by hardening commits (`7f20b1bc`, `21efeece`,
`2ba54266`, `9c1b76b6`, `6424f73d`, `b9f95c35`) that resolved the flagged majors — same shape as the
original 2026-04-06 process: review, merge, ship follow-up hardening.

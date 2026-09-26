---
name: check-pins-before-fixing-findings
description: "Review finding reversing pinned behavior: grep tests+docs, pinned = skip. Deliberate IR/cleanup refactors are different: triage each broken test (still useful? failure from production or test?)."
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-09-26T01:25:27.682Z
---

Applying the #981-branch max review (2026-08-10), 3 of 15 verified findings turned
out to target behavior that was deliberately chosen AND pinned: rewind-vs-backoff
asymmetry (pinning test with rationale comment), create-time staging preservation
(three pinning tests), SDK tool_turn omission (docs/sdk.md rationale + source-pin
test). One verifier explicitly claimed "no ruling comment or pinning test" while the
pinning test existed in an untracked file.

**Why:** Finders/verifiers read the diff and cited code, not the test suite's
intent inventory; "unpinned" claims are cheap to make and expensive to act on —
fixing a pinned behavior erases a ruling ([[feedback_docs_are_not_review_immunity]]
gives the standard: deliberate = cited rationale + pinning test, and it cuts BOTH
ways).

**How to apply:** Before implementing any finding that reverses a behavior, grep
tests (including untracked ones) and docs for the current behavior's copy strings,
constants, and call shapes. If a pin + rationale exists, the finding becomes
skipped-with-reasoning for the maintainer, not a code change — and if you already edited,
revert rather than rewrite the pin. Rewriting a pin is only justified when the pin
itself is internally contradicted by sibling work in the same change, and must be
flagged loudly.

**Scope (the maintainer, 2026-09-25):** the skip rule is for review findings that would casually
reverse a ruling. Deliberate cleanup and abstraction work that moves behavior into the Turn IR
is expected to invalidate tests, and a pin is not a veto there. Triage every broken test with
two questions: (1) is it still testing something useful: name the contract it protects without
reference to the old mechanism; (2) did the failure come from production or from the test.
Production regression, so fix the code; test encodes the old mechanism, so rewrite it against
the new one while keeping the contract; contract genuinely gone, so delete it and say so in the
PR. A ruling's underlying invariant (e.g. #1188's "charge matches what is replayed") outlives
its mechanism (the family name compare). Related: [[project_replay_identity_ir_origin]].

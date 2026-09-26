---
name: feedback_fresh_briefing_vs_agent
description: "Delegating big judgment-laden work: fresh session + brief if a step is human-gated; give Fable/Opus the problem + constraints, Sonnet exact code."
metadata: 
  node_type: memory
  type: feedback
---

For a **substantial, judgment-laden, symmetry-critical** unit of work — especially a
storage migration spanning both backends, an in-place migration edit, schema↔migration
convergence, and a **human-gated step** (e.g. the [[feedback_no_live_db_until_reviewed]]
dev-DB validation) — prefer a **fresh session + a continuation brief** over delegating to
an implementer agent. (Confirmed 2026-06-03 on the #5.5 dead-column drop.)

**Why:** an agent can't make the judgment calls (e.g. "is this column actually dead?"),
can't complete the human-gated step, can't recursively delegate, and tends to rush exactly
the symmetry/correctness parts that bite — and reviewing its both-backends output still
lands on the orchestrating session's (often already-heavy) context. A fresh session gets
full budget for code → test-DB validation → review, and the dev-DB run stays the human gate
either way.

**How to apply:** write the continuation brief WHILE the findings are live (the non-obvious
discoveries are what a cold start misses); hand the user the brief text directly (they may
prefer it in-chat over a file). Reserve agents for **mechanical, well-specified, single-context
volume** (e.g. the dict↔Turn test bridge across ~18 files — that delegated well). Also a fresh
start is right when the current session has already been compacted once mid-task.

**Refinement (2026-06-10, user-initiated, skill-editor shelf conversion):** judgment-laden
work CAN delegate to an agent when ALL of: (1) the brief **pre-makes the design decisions**
(agent executes a designed change, applies taste only within stated bounds), (2) the brief
transfers the **mental model + lessons-learned**, not just a recipe, (3) the executor is
**fable-tier**, (4) verification is self-contained (tests + visual harness the agent can run
itself — no human-gated step inside the unit). This is the continuation-brief pattern
executed AS an agent. Outcome: exceptional — the agent byte-diffed 26/26 payload keys
against legacy, wrote synthetic-event tests for paste flows, made correct keep-vs-delete
calls on a grep-driven teardown, and caught+fixed a CSS war the brief didn't list. The
human-gated-step and both-backends-symmetry cases STILL want a fresh session.

**Refinement (2026-07-08, user correction, close-on-hide review-fix handoff): brief
altitude is set by the EXECUTOR MODEL, not mainly the task.**
- **Fable and Opus:** give the PROBLEM + the CONSTRAINTS and let them design. **Failure
  modes / symptoms are an EXCELLENT brief format** for them — "here is what breaks and why,
  and what must not change", NOT code. Over-prescribing wastes their capability.
- **Sonnet:** over-prescribe — hand it the exact code snippets / step-by-step.

User's correction after I handed Fable an over-prescribed brief (exact code for every fix): give
Fable the problem and the constraints (failure modes work very well), and do the same for Opus;
Sonnet needs over-prescription, including the code snippets. Earlier: don't over-prescribe; leave
room to explore and arrive at a proper solution. ALWAYS transfer the hard constraints regardless of
tier (what must NOT change — a just-shipped file's pinned test shape, a behavior that must stay).
This **supersedes the 2026-06-10 "pre-make the design decisions" note for fable/opus executors** —
that note's mechanical-known-transform port is the exception, not the rule. Sibling of
[[feedback_runbook_trust_llm]] (state requirements, not code).

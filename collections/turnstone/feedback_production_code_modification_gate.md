---
name: feedback_production_code_modification_gate
description: "Changing established production code: identify a confirmed defect or obtain an explicit design decision; preserve observable behavior when restructuring."
metadata:
  type: feedback
---

Restructuring established production code requires a confirmed defect there or an explicit
maintainer decision. A review finding or proposed cleanup does not by itself justify moving
behavior that has accumulated production and review history.

In the #725 fix round (2026-07-20), extracting a shared factory also moved MCP status projections
and refresh/reconnect outcomes. That changed log text and logger names while rewriting two
endpoints. The lesson is to include these observable effects in the design decision, even when
the motivating finding concerns structure.

**Why:** source history, operator runbooks, and exact log strings help people understand and
operate the system. Tests for a new abstraction do not establish that every affected behavior
should change.

**How to apply:**

1. Start with the smallest change that fixes the confirmed defect. If sharing a seam requires
   restructuring established code, explain the affected callers and behavior first. A small
   duplication with a parity test can be acceptable when it avoids unrelated production changes.
2. A confirmed defect in that code or an explicit maintainer decision can justify the change.
   Present verified facts, options, tradeoffs, and a recommendation when the design is questioned.
3. Preserve log strings, logger names, response shapes, and status codes unless changing them is
   part of the agreed scope. Pin caller-specific behavior with meaningful tests.
4. Treat earlier review results as evidence tied to the reviewed tree. Recheck them after changes.

Related: [[feedback_minimal_scope_first]], [[feedback_caution_proportional_to_deployment]],
[[feedback_push_back]].

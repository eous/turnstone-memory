---
name: feedback_minimal_scope_first
description: "Scoping a feature, even when a multiSelect returns all options: propose the minimal single-path v1 with extras as explicit non-goals; the maintainer trims scope hard."
metadata: 
  node_type: memory
  type: feedback
---

When scoping a feature, recommend and build the minimal single-path version first; let the user opt into expansion. Don't equate breadth-of-relevance with breadth-of-build.

**Why:** Scoping the workstream-export feature (issue #613), a "pick all that apply" multiSelect on use cases came back with all four selected, and I read that as "build all four formats + a lossless native envelope + re-import + 3 phases." The user immediately trimmed it to a single `openai-json` format with minimal coordinator handling, explicitly to keep the scope from expanding. Selecting every option as *relevant* ≠ wanting it all *implemented now*.

**How to apply:** Lead with a minimal v1 (one format / one path) as the default; list extras as explicit non-goals/follow-ups rather than scoping them in. An explicit **Non-goals** section in issues/plans is welcomed and helps lock the decision. When a multiSelect returns everything, treat it as "these all matter eventually," then confirm what v1 should actually contain before scoping the maximal version. Relates to [[feedback_push_back]].

---
name: feedback_no_per_model_architecture_docs
description: "Adding or changing a model capability row: write no per-model paragraph in docs/architecture.md; the contract lives in the row, its comment and the CHANGELOG (maintainer, 2026-10-01)."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-01T06:42:30.257Z
---

docs/architecture.md documents mechanisms, not per-model contracts. When the #1245 change
(gpt-6.1-sol row) copied the neighbouring GPT-6 Sol/Luna paragraph, the maintainer asked why a
model-specific entry was there and ruled that it does not belong. The existing per-model paragraphs
(GPT-6 Sol/Luna, and the model-fact parts of Astra's) are slated for removal in a later clean pass by
the maintainer; until then they are not a pattern to copy.

**Why:** per-model paragraphs go stale with every new row, duplicate the capability table, and invite
the next row to copy them. Review finders asked for "the missing paragraph" three rounds running.

**How to apply:** put a new row's contract in the row and its comment, and the user-visible fix in the
CHANGELOG. Where docs enumerate models (coverage lists, cache-policy lines), name the family rather
than its tiers so new rows need no doc edit. Decline review findings that ask for a per-model
architecture paragraph, citing this ruling. Related: [[feedback_pattern_propagation_sequencing]],
[[reference_provider_capabilities]].

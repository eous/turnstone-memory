---
name: feedback_honest_ledger_over_cost
description: "Trading the model's view of its own history for tokens (trim, dedupe, prune), or letting a reopen change its prefix: keep the ledger immutable (honesty, prefix-cache cost)."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-08T13:07:26.425Z
---

When a design choice trades the model's view of its own history against tokens or cost
(trimming a replayed tool load to the tools a request offers, deduplicating repeated searches,
pruning old results), keep the record honest: replay what happened, fabricate an acknowledgment
if one is needed but never an outcome, and when a record must degrade (an item the API cannot
take back), log it rather than let it vanish.

**Why:** the maintainer ruled on 2026-10-05, during #1281, that honesty takes precedence over
cost optimizations, pointing at HYPOTHESIS.md (the lowering is the only channel from state to
model; "degraded accounting, but never silent"). It overruled review proposals to trim replayed
`tool_search_output` loads and to dedupe the repeated loads that pre-fix histories carry.

**How to apply:** when a finding proposes a cost or tidiness rewrite of history the model sees,
decline it under this rule, keep enforcement at the gate (dispatch refuses a call to a tool no
longer offered), and state the token cost in the CHANGELOG instead. Related:
[[feedback_no_tool_result_pruning_prefix_cache]], [[project_1281_openai_hosted_item_replay]].

**More immutable, not less (the maintainer, 2026-10-08, #1292 A2):** the ledger should become
more immutable over time, because that is more honest and because breaking the prefill/prefix cache
has a real cost. This came after my restore change dropped a deleted skill's saved text on reopen,
which the old code kept. Judge any reopen, fork or restore design by whether
it rebuilds the prefix the workstream already had (system message, skill message, history), since
every change also costs a cold prefix cache. A skill committed to a workstream stays in it
([[project_1292_alias_settings]]).

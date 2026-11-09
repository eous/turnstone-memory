---
name: project_1192_web_fetch_model_role
description: "web_fetch model role tools.web_fetch_alias (PR #1590, 2026-11-08): the maintainer's rulings (web_fetch only, empty = caller's model, listed for agents, refused before approval) and follow-ups."
metadata:
  node_type: memory
  type: project
  modified: 2026-11-09T00:33:53.927Z
---

`tools.web_fetch_alias` (Models → Roles → Web fetch) names the model web_fetch's read call uses:
the call that reads the fetched page or PDF and answers the question. Built in PR #1590, which
closes #1192. Read this before changing which model web_fetch reads with.

**Rulings (maintainer, 2026-11-08):**
- Scope is web_fetch only. A broad `model.utility_alias` (#1292 PR E: titles, compaction and
  web_fetch) was ruled too broad; titles and compaction stay on the session's model.
- The role covers conversations and task agents.
- Empty means the model that called web_fetch: the session's, or inside a task agent the agent's
  own lane at its effort (passed as `_caller_lane` on the execution copy). Before this, a task
  agent's fetch read with the workstream's model.
- The role's alias stays in the model lists agents see (not in `UTILITY_ROLE_SETTINGS`), unlike
  the judge's, for now.
- Removing the last enabled model clears the setting, as it does the other general role
  settings. Clearing the judge settings too is #1587; it would reverse #1529's keep-the-judge
  ruling.
- A set alias that can't be used is refused before approval by the same bind the read uses
  (`_web_fetch_binding`). There is no second check just before the download: a setting changed
  while an approval prompt waits downloads once, then errors. The maintainer accepted that gap.
- The read keeps #1169's retries (the SDK's two creation retries plus shared recovery, no
  session creation ladder). An optional change is filed as #1585 to see whether operators ask.

**Facts that are easy to get wrong:**
- The pre-approval bind makes no network call. It catches a missing certificate bundle, and a
  missing key only on the `openai`, `google` and `xai` SDKs: `anthropic` checks credentials at
  request time, and local providers get a placeholder key.
- A set alias reads with its own settings even when it names the session's alias, so a user's
  `/reason` doesn't reach it.
- The reading model is the only one that sees the raw page, so it is the one that has to ignore
  instructions planted in it. The help text and docs say smaller models do that less reliably,
  since the output guard's LLM stage is off by default.

**Why:** these were settled across design and two review rounds; reopening one (widening the
role to titles or compaction, hiding its alias, falling back when it can't run) undoes a ruling.
**How to apply:** check these rulings before changing web_fetch's model selection or the role.
Related: [[feedback_alias_never_becomes_another_alias]], [[project_1292_alias_settings]],
[[project_1529_judge_alias_rescope]], [[project_1569_web_fetch_links]].

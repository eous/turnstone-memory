---
name: project_1292_alias_settings
description: "#1292 (requests send values that differ from the alias): scope note, the five-PR plan (A with A2 folded in, B-E), the 10-07/10-08 rulings, and the no-copy design for workstream settings."
metadata:
  node_type: memory
  type: project
  modified: 2026-10-08T13:14:02.584Z
---

#1292 is an audit of request settings (temperature, effort, max_tokens) that differ from the model
alias. Scoped 2026-10-07 against dev @ 72dbb41a. The full plan, with file:line for every item, is
the LOCAL untracked note `docs/design/1292-scope.md` in the main checkout, next to three
verification reports (`1292-verify-group1.md`, `1292-verify-groups235.md`,
`1292-skills-surface.md`). PR A was built in a separate worktree (branch
`fix/1292-skill-settings`, PR #1310); keep notes in the main checkout, not in worktrees, since
removing a worktree deletes its ignored files without a warning. Re-check line numbers before coding
([[project_velocity]]).

**Plan:** A skills stop choosing the model and its settings (decision 3, migration 080, since #1268
took 079); A2 deletes skill `activation` and `token_budget` (ruled 10-08, below) and folds into PR
A, extending migration 080; B workstreams keep only what a user chose (decision 2, migration 081,
after A); C provider fidelity and loud config (independent; carries the Anthropic manual-thinking
budget fix, which must precede D); D per-purpose budgets clamp to the alias plus a main-turn row
clamp and window fit; E remove the utility thinking-off posture and add a utility role alias.

**Rulings:** decisions 2 and 3 are decided in the issue. On 10-07 the maintainer ruled: replace the
utility posture (decision 1), with a utility role alias as the lever; clamp only for decision 6
(defaults stay set, and doubling `model.max_tokens` was floated); explicit role settings
(`model.task_effort`, `coordinator.reasoning_effort`) override the alias
([[feedback_never_pin_temperature]]). From PR A's review: skills also lose `agent_max_turns` (only
the operator's `tools.agent_max_turns` caps task agents), so migration 080 drops five columns, and
the CHANGELOG is its only notice (no migration log line or audit row). Three older problems PR A's
review found went to issues at the maintainer's call: #1306, #1307, #1308. On 10-08 the maintainer
ruled to delete the skill `activation` field entirely (`named` / `default` / `search`): default
skills go (the upgrade note points to prompt policies and persona prompts), and the
`<available-skills>` system-prompt block
is dropped rather than widened or moved into the tool description, leaving discovery to
`skills(find)`. The dead `skill_search.py` goes with it. A2 also deletes the skill `token_budget` (a
per-call ceiling, not a running total, that only skills set) with the session's budget gate, and its
create card shows `notify_on_complete`. The maintainer then took every recommendation from the two
A2 maps (scope note) and plans a separate skill-discovery epic after the #1292 series, so A2 keeps
discovery changes minimal. Also 10-08: a skill committed to a workstream stays there. Its saved
create-time text renders on reopen, fork and copy whether the skill is later edited, renamed,
disabled or deleted, and its bundled files load while the row exists. Disabling or deleting a skill
only keeps it out of new workstreams, and the docs say so. Restore finds the row by
`applied_skill_id`, never by name ([[feedback_honest_ledger_over_cost]]). A2 covers only the
create-time stamp: stamping skills applied mid-conversation, persona-style, is #1312, and the
hash-chain ledger investigation plus other prefix churn is #1311. After round 2 the maintainer
cut A2 back to what the deletions force, since A2 was meant only to delete skill fields:
constructor stamping for every create path and a 063-style backfill of existing workstreams
were built and reverted, now #1312 (backfill scope in a comment) and #1320 (coordinator and CLI
creates, and which skill settings coordinators take). A reopened workstream losing its
completion targets is #1314. A2 is the second commit of PR #1310's branch (86c4614b); the next
PR is B, whose migration is 081. Details and scope: the scope
note's "PR A2" section.

**Proposed design for B (10-07; a proposal, not a ruling):** the session never copies an alias
value. Lanes carry the alias's values (`ModelLane.max_tokens` added). The session stores only a
user's choice (`/reason`, CLI flags) tagged with the alias it was made on, and that choice applies
only to lanes of that alias. Reload, fallback, task agents, reopen (#1272's first half) and `/model`
then need no re-resolution code ([[feedback_designs_that_need_no_memory]]).

**Why:** the issue proposed provenance flags plus five re-resolution sites, which a later
alias-changing path (#1214 backends) would have to remember.

**How to apply:** start from the scope note; its "Open questions" section lists what is still
undecided.

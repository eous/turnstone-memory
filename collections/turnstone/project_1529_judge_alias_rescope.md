---
name: project_1529_judge_alias_rescope
description: "#1529 judge alias (2026-11-02): rescoped after two review rounds; no judge object when an alias can't bind; ruling 5 moved to #1543; trade-offs accepted; PRs and follow-up issues."
metadata:
  node_type: memory
  type: project
  modified: 2026-11-03T11:14:36.478Z
---

**Rescope (maintainer, 2026-11-02).** The first #1529 branch (`fix/1529-judge-no-fallback`, never
committed) modelled an unusable judge alias as a refusing judge object. Two review rounds kept
finding bugs in that mechanism's own fixes (20 of 43 findings in round 2), so the maintainer
approved rebuilding on a fresh branch, `fix/1529-judge-alias-holds`.

**Design taken (simp-3):** `resolve_judge_binding` raises `JudgeModelUnavailableError`; the
session catches only that, records the role refused keyed on (alias, registry generation, settings
version), logs `judge.model_unavailable`, shows a one-time fixed note for the intent judge, and
returns None, so the batch is handled as with the judge switched off. Accepted trade-offs: no
verdict, no heuristic risk card and no verdict rows while the alias is out; channel bots get no
note. A side reviewer re-raised the card/channel loss; I recommended accepting it and filing it
under #1544, and the maintainer hasn't overruled that.

**Moved out:** ruling 5 (a coordinator's pick reaching children, saving a pick across reopen,
CLI resume of a pick, create-time 503 for `judge_model`) to #1543 with its design questions (whose
pick, repointing, CLI flag precedence, placement retry). Until then a reopened workstream and a
coordinator's children follow `judge.model`.

**Follow-ups filed 11-02:** #1543 (ruling 5), #1544 (approver surfaces read a fallback as a ruling;
no note on channels), #1545 (empty tool output recorded as an LLM ruling), #1546 (inspect hands
coordinator models child verdicts); #1415 got a comment (first-load undecodable row, in-use check
skips unreadable rows). Spawn cards not showing the model was already #1306.

**PRs:** #1547 is the #1529 fix. #1548 came out of the same review as its own change: Discord and
Slack approval cards show model-written text as written. Markdown in a command or the judge's
summary is escaped, the summary is one line of at most 400 characters, and on Slack a call with no
preview shows its header line (CHANGELOG 1.9.3).

See [[feedback_alias_never_becomes_another_alias]] and [[feedback_nonconverging_reviews_mean_simplify]].

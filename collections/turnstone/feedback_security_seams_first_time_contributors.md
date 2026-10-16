---
name: feedback_security_seams_first_time_contributors
description: "PR triage: a first-time contributor's change to a security seam (output guard, redaction, approvals, auth) is closed with thanks and fixed in-house; invite them to Discord or an issue first."
metadata:
  type: feedback
---

The maintainer, 2026-10-09, on PR #1280 (a first-time contributor's implementation of the fix
#1074 proposed for the output guard's cut-boundary blind spot): the output guard is a security
boundary, so changes there are made in-house. Close such a PR with thanks, fix the issue in-house
if it still needs fixing, and tell the author that to work on Turnstone they should join the
project Discord or talk a change through on a GitHub issue first.

**Why:** a first-time contributor has no track record with the project yet, and a security seam is
where an unvetted change costs most.

**How to apply:**
- In triage, flag any first-time contributor PR that touches the output guard or redaction, the
  approval gates and intent judge, auth and OAuth, or the network and sandbox guards. Recommend
  closing it with thanks plus that invitation, and say whether the underlying issue still needs an
  in-house fix.
- Thank them for what was genuinely useful (a reproduction, a regression test).
- Related: [[feedback_everything_needs_auth]], [[feedback_redaction_regex_design]],
  [[feedback_task_agents_share_main_paths]].

---
name: project_server_tool_followups_priority
description: Recommended order (given 2026-09-19) for the follow-up issues filed from the server-tool usage campaign (#1188-#1197), with the reasoning, so a compaction does not lose it
metadata:
  type: project
---

Follow-ups filed 2026-09-19 from the server-tool usage campaign ([[project_server_tool_usage_inflates_context]]).
Recommended order given at 10:27 that day, after #1191 was measured and PR #1196 was up. Dependencies first,
then impact per unit of work:

1. Land PR #1196 (shared `resolve_context_usage` rule) — both accounting items build on it.
2. #1188 opaque-block token charge with #1190 folded in — largest live effect (post-search calibration ran
   ~2.3x low, tool-result ceiling shrank for the rest of the workstream).
3. #1192 web_fetch extraction thinking spend — mostly a decision on where the operator knob lives; small
   implementation; ~$0.50 per fetch on an always-on-thinking alias.
4. #1194 measure the other hosted Responses tools and xAI — a few cents per probe; #1195 depends on it.
5. #1195 hosted image generation as an attachment — needs #1194's usage shape, attachment storage/render,
   replay design for image bytes.
6. #1189 billed-input ledger column — field work done; only a migration for a minor gap. Bundle with the
   next schema change, never a migration of its own.

The one hard edge: 4 before 5. Everything else is judgment about value per hour.

Earlier order (08:07 the same day, before #1191 was measured): #1191 probe first, then #1188, #1190,
#1192, #1189. #1191 was measured and fixed for the Responses web_search tool in PR #1196 but the issue was
left open on purpose: the Chat Completions search lane is still unmeasured.

Items 1 and 2 landed on dev 2026-09-19/20 (PR #1196 as dd585350; PR #1198 as 60bfed7b + 4e677f1f). #1197
(delete the in-process fork copy) was filed later from the #1198 review as its own small PR, no rank given.
#1186 (Discord placeholder) and #1187 (research bet) were filed the night before and were not in the ranking.

**Why:** The maintainer asked for this ordering back after two compactions; it had only survived in the transcript.
**How to apply:** when picking the next server-tool follow-up, start from item 3 unless the maintainer re-ranks.

**The maintainer's rulings 2026-09-20 on items 3 and 4:**

- **#1192 stays open, NOT a priority, and must not revert the current fix.** History: utility calls used to
  default to no thinking; some local models cannot disable thinking, which is why the current shape exists
  (`_utility_completion` still asks for none through every channel via `lane_without_thinking`; the spend
  happens only on lanes that cannot honour the pin, the sibling of [[project_973_no_thinking_posture_hosted_lanes]]).
  Right shape when picked up: a capability flag on the lane (thinking cannot be disabled) and/or a model ROLE
  for utility calls in Models -> Roles, beside perception / audio / reranker. Never a code pin
  ([[feedback_never_pin_temperature]]).
- **#1194 narrows to what #1195 needs.** xAI code exists but is not reachable from the UI and nobody asked
  for it; measuring hosted tools is a script, not a work item. The `image_generation` usage measurement is
  done as the first step of #1195, not as its own issue. The other hosted tools stay unmeasured until someone
  wants them.

Resulting order after the rulings: #1195 (with its image_generation measurement first) → #1189 (bundle with
the next migration). #1192 parked with the shape above.

#1199 (judge calls record no usage) filed 2026-09-20 from the post-#1198 verification; small hook fix, no migration, no rank given yet, independent of the order above.

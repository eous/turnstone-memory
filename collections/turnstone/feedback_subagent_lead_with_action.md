---
name: feedback_subagent_lead_with_action
description: "Spawning a review or adversarial Agent: lead with an imperative first tool action; if it returns 0 tool calls, prod it via SendMessage rather than respawn."
metadata: 
  node_type: memory
  type: feedback
---

Observed 2026-07-07: a single `code-reviewer` Agent spawned to adversarially review a diff **returned after ~3s with 0 tool_uses**, emitting only its opening deliberation ("I'll keep the skill in mind but focus on…") as its final message — no `git diff`, no file reads, no actual review. The agent treated its first-turn thinking as the answer. A review that returns 0 tool_uses is silently useless: it reads as "done" but did nothing.

**How to apply:**
- **Lead the prompt with an imperative to ACT first**, not context to absorb: e.g. "BEGIN IMMEDIATELY with tool calls — your first action must be to run `git diff` in <path>, then read <files>. Do the investigation, then return findings. Do not deliberate first." Adding this line made the very next spawn work (21 tool calls, full verified report).
- **If it stalls anyway, don't respawn — prod it.** `SendMessage` to the agent's id with "you made 0 tool calls; actually run the investigation now" resumes it from its transcript and it completes with full context intact (cheaper than a fresh spawn).
- Applies to any Agent whose task REQUIRES tool use up front; most acute for review / audit / adversarial agents whose first instinct is to reason about the task rather than open the code.

**Why:** the imperative-first framing and the resume-don't-respawn habit each save a full wasted round-trip on a stage (adversarial verification) that is the whole point of running the agent. Relates to [[feedback_large_review_orchestration]], [[feedback_fresh_briefing_vs_agent]].

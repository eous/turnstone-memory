---
name: feedback_dont_call_prompts_tuned
description: "Describing prompt wording still under development (#913 briefs): say 'current draft', never tuned, settled, validated or shipped for unmerged text."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-07-29T14:17:17.840Z
---

The maintainer, mid-session on #913: none of these prompts should be considered "tuned", because
they were being actively tuned at that moment. Later, more sharply, they asked why the whole change
had felt like a fight, with even the subagent resisting and making things up by calling the prompts
"tuned".

**Why it matters.** I introduced "tuned" into agent briefs, and the
agents inherited it. It is not a neutral descriptor: it frames a
wording as a settled artifact with measurement behind it, so every
subsequent user change reads as needing justification against a
baseline that does not exist. On #913 the baseline genuinely did not
exist — the sweeps had measured earlier drafts on an instrument that
was itself being repaired, and several conclusions from them were
later withdrawn. Calling that "tuned" was false AND adversarial in
effect.

**How to apply.**

- While wording is under development, say *current draft*, *the wording as it stands*. Never
  *tuned*, *settled*, *validated*, *eval-selected* — and never *shipped* / *production text* for
  anything on an unmerged branch (the maintainer, 2026-07-29: none of this text counts as shipped).
  The incumbent framing is the same defect as "tuned": it makes the current draft a champion that
  challengers must decisively beat, when the rule for draft text is simply that the best-measuring
  wording becomes the draft. If a number backs a clause, cite the number and its caveats rather than
  the label.
- The framing propagates: whatever word appears in a brief comes back
  in the agent's report and its code comments. Audit briefs for it.
- Two behaviours it produced, both to avoid: **defending the existing
  shape before answering the question asked**, and **litigating an
  instruction** at length instead of stating the disagreement in one
  line and implementing the corrected version. A long "what the brief
  got wrong" section attached to a one-sentence requirement reads as
  resistance regardless of intent.
- When the user asks "why does X work this way" — check the code and
  answer what it does. On #913 every such question found a real
  defect.

Related: [[feedback_push_back]] (push back on decisions — but on
substance, once, not by re-arguing a settled instruction),
[[feedback_measure_before_accepting_a_finding]],
[[project_idle_tasks_nudge]].

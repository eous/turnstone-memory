---
name: project_opus5_cutshort_seam
description: "Opus 5 cut-short/finish_reason judge seam (fix/cut-short-tool-calls @ cfc3f0fb): SHELVED at a design defect; read docs/design/opus5-seam-pr1-findings.md."
metadata:
  node_type: memory
  type: project
  modified: 2026-07-25T08:10:56.831Z
---

**Split was UNSTACKED 2026-07-25.** Opus 5 onboarding shipped on its own against
`main`; the seam fix is shelved on `fix/cut-short-tool-calls` @ `cfc3f0fb`
(unpushed, green: 9795 passed, gates clean, 8/8 mutation controls non-vacuous).
**Full findings + resume plan: `docs/design/opus5-seam-pr1-findings.md`
(local-only, untracked) — read it before touching the seam again.**

Unstacking was safe because of a fact worth keeping: on `main`,
`_run_agent` matches `length` and `content_filter` but a raw `"refusal"` matches
NEITHER, so a declined turn was returned to the parent as if it were finished
synthesis. Normalizing refusal onto `content_filter` therefore *improves* main
on its own — operator warning where there was silence, sub-agent stops instead
of laundering the partial. It does NOT fix the partial-tool-call drop, whose
guard is still `== "length"`; that is the shelved seam's job.

**The design defect to fix before touching the finding list:** the gates
conflate *"the turn was cut short"* with *"the readout never formed."*
HYPOTHESIS gates the READOUT. A complete, balanced JSON verdict emitted before
the cut DID form — truncation removed trailing prose, not the verdict — and both
judge gates discard it. On the output-guard judge that direction is fail-OPEN:
dropping the LLM contribution when it was the only detector collapses acted risk
to the heuristic's "none". The corrected rule must separate: no parseable
readout → refuse; COMPLETE readout then a cut → accept; readout only
reconstructable by prose-scraping → refuse.

**`is_cut_short` stays an ALLOWLIST** (the maintainer's call, HYPOTHESIS totality) —
don't re-litigate. But the round-5 review found the generic warn arm it enables
is a permanent false alarm on any server whose clean token is outside the set
(`eos`, `stop_token`), rendered via `on_error` with no discoverable remediation.

**Method lessons that generalized:**
- A per-consumer sweep of the ACTUAL comparison sites (`grep` every
  `finish_reason ==`) found two arms four review rounds had missed, because
  every round read the diff and these arms were never in it.
- Cap-mining works on HEALTHY runs, not just crashed ones — see
  [[reference_code_review_workflow_recovery]]. 35 survivors, 15 reported, **8
  genuinely dropped including a CONFIRMED one**. Locate the synthesize agent BY
  CONTENT (`grep -l "survived independent verification" agent-*.jsonl`): journal
  v2 `started` events *and* the `.meta.json` sidecars carry no labels.
- Re-deriving a seam can manufacture its own next round: most round-5 findings
  were FIX-ERA, and four were at-site comments asserting things that are false.
  Writing a confident rationale into a comment does not make it true —
  [[feedback_review_convergence_methodology]].

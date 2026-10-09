---
name: feedback_designs_that_need_no_memory
description: "Choosing between designs where one needs a future change to remember a per-entry flag: prefer deriving the fact from structure, or enforce the flag with a test (maintainer, 2026-10-01)."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-01T07:23:25.361Z
---

A very small team maintains the project, and nobody, human or agent, reliably remembers a per-entry
rule from one change to the next. When a rule needs per-row or per-entry declarations that a future
change must remember, prefer a design where the fact comes from structure that change has to touch
anyway, and where a forgotten step fails safe.

**Why:** while designing the effort knob's "none" rule (#1248, split out of the #1245 model-row PR),
the rule first needed a per-row value, then an opt-out flag for the shared Gemini row. The maintainer
asked for an option that needs no remembering. The decided design marks rows through the existing
table-wide transforms in _openai_common.py and _xai.py (the same "ONE rule for the whole table" idiom
used for server_parses_reasoning): listed rows get the marker automatically, and fallback rows are
safe by default. Policy changes like this belong in their own PR, not in a model-row PR: pulling it
into #1245 tripled that diff and cost three review rounds before it was split out again.

**How to apply:** when proposing a flag, ask what happens when the next row or provider forgets it. If
the answer is a wrong or rejected request, look for a structural signal (table membership, a shared
transform, a lookup helper) or add a test that walks every instance and fails loudly. State the
forgotten-step failure mode when presenting options. Related: [[project_design_constraints]].

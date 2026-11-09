---
name: feedback_review_report_one_screen
description: "Relaying a /review result: one screen (verdict, each decision as option/cost lines, a plan); the full sanity report goes to a scratch file. Long reports drew pushback (2026-11-04)."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-11-04T21:54:40.941Z
---

After the full tool-call view's second review round (2026-11-04), the sanity stage's report ran to
several hundred lines, as the first round's had, and the maintainer pushed back on its length
before asking how to proceed. The decisions in it were sound; the length buried them.

**Why:** the maintainer reads the report to decide what happens next. Every option still has to
reach them with its cost ([[feedback_relay_every_review_option]]), but one line per option does
that. Evidence, failure scenarios and fix notes are for whoever applies the fixes.

**How to apply:** brief sanity to write its full report to a scratch file and return a summary
that fits one screen: the verdict and counts, each decision as one line per option with its cost
(recommendation first), then one line per remaining finding, grouped by what to do with it (fix
now, known limit, issue). Emit that summary verbatim and give the file's path. When the maintainer
then asks how to proceed, answer with a short plan, not another survey. Related:
[[feedback_large_review_orchestration]].

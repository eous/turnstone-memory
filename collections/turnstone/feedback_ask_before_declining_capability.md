---
name: feedback_ask_before_declining_capability
description: "Triaging review findings: a missing capability the maintainer may want goes to them as a question, never into a declined list."
metadata:
  type: feedback
---

During the #1233 review loop (2026-09-30), brotli support in the guarded fetch was listed as
"declined (pre-existing passthrough)" in a triage summary. The maintainer only learned it was
missing by asking afterwards, then asked for brotli and zstd, which shipped as #1239.

**Why:** a decline list is meant for defects judged not worth fixing. A capability gap is a product
decision; filing it there makes that decision for the maintainer without their knowledge.

**How to apply:** when triaging findings, separate "not a bug / not worth fixing" from "the product
lacks something". Report the second kind to the maintainer as a question with its cost (for
brotli: one dependency extra, a lock change and a test that stops being skipped). Decide only the
first kind yourself.

Related: [[feedback_finish_the_fix_spree]], [[project_1233_guarded_fetch_httpx2]].

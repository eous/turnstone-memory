---
name: project-readme-harness-diagram
description: "Proofreading or regenerating README docs/diagrams/harness.png: 'inci.' typo is DELIBERATE, never fix it; README image URLs use the media LFS endpoint."
metadata: 
  node_type: memory
  type: project
  modified: 2026-08-02T20:17:18.342Z
---

Shipped 2026-08-02 (commit 3960aeef): README "What is a harness?" now leads with
`docs/diagrams/harness.png` — a vintage-cartoon rendering of the [[project_harness_hypothesis_doc]]
tuple, labels near-verbatim from HYPOTHESIS.md's "Reading it" table.

**The bell-jar callout reads "(inci. ⊥_Y Parse-Failure)" — "inci." not "incl." — and this is
DELIBERATE.** The maintainer's ruling: it looks like the ink ran dry during printing, which suits
the vintage register. Do NOT fix it, flag it in proofreads, or regenerate the image over it.

Other durable facts:
- Image is 256-color quantized (~800KB, from a 2.3MB RGBA original). Quantize any regenerated
  successor the same way before committing; color accents on the Q_E machine mean grayscale
  conversion is NOT safe.
- README embeds it via the **media.githubusercontent.com/media/** endpoint — NOT
  raw.githubusercontent.com. The repo LFS-tracks `*.png` (.gitattributes), and raw serves the
  131-byte LFS pointer text for LFS paths (broken image); media serves the bytes. Any future
  absolute-URL image in README/PyPI needs the media endpoint. Absolute URL at all because
  README.md is the PyPI long description and relative paths 404 there. The hero image
  (`docs/assets/hero.png`, relative path) still has that PyPI gap — known, unfixed, low priority.
- Caption formula uses τ_H (HYPOTHESIS.md's notation; the old README τ* appeared nowhere in the
  doc) and drops the ρ∘(M_W∘π,E) shorthand the doc itself brands ill-typed.
- Both "Factored (The Outer Kernel)" bubble headers are section citations of the doc's
  *The outer kernel* passage — not a copy-paste error; don't "fix" them either.

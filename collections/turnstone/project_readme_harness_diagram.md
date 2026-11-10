---
name: project-readme-harness-diagram
description: "Proofreading, patching or regenerating README docs/diagrams/harness.png: 'inci.' typo is DELIBERATE, never fix it; patch labels from its own pixels; media LFS URLs."
metadata: 
  node_type: memory
  type: project
  modified: 2026-11-10T03:00:00.000Z
---

README "What is a harness?" leads with `docs/diagrams/harness.png` — a vintage-cartoon rendering of
the [[project_harness_hypothesis_doc]] tuple, labels near-verbatim from HYPOTHESIS.md's "Reading it"
table. First version 2026-08-02 (3960aeef, 1408×768); regenerated 2026-10-12 (6e5ef3d4, 1376×768) to
carry the Authority tier and its padlock, the trusted principal, the never-lower filter, the
plant-channel boundary, "the only door" and the recorded no-op.

**The bell-jar callout reads "(inci. ⊥_Y Parse-Failure)" — "inci." not "incl." — and this is
DELIBERATE.** The maintainer's ruling: it looks like the ink ran dry during printing, which suits
the vintage register. Do NOT fix it, flag it in proofreads, or regenerate the image over it.

Other durable facts:
- Format. The August image was 256-color quantized (~800KB, from a 2.3MB RGBA original), with the
  instruction to quantize successors the same way. The October regeneration was committed as
  truecolor RGB (~1.6MB), and no ruling has replaced that instruction since: ask before quantizing a
  full regeneration, and never quantize as part of a patch — it changes every pixel and hides the
  diff. Color accents on the Q_E machine mean grayscale conversion is NOT safe either way.
- README embeds it via the **media.githubusercontent.com/media/** endpoint — NOT
  raw.githubusercontent.com. The repo LFS-tracks `*.png` (.gitattributes), and raw serves the
  131-byte LFS pointer text for LFS paths (broken image); media serves the bytes. Any future
  absolute-URL image in README/PyPI needs the media endpoint. Absolute URL at all because
  README.md is the PyPI long description and relative paths 404 there. The hero image
  (`docs/assets/hero.png`, relative path) still has that PyPI gap — known, unfixed, low priority.
- Caption formula uses τ_H (HYPOTHESIS.md's notation; the old README τ* appeared nowhere in the
  doc) and drops the ρ∘(M_W∘π,E) shorthand the doc itself brands ill-typed. The alt text reads
  "γ authorizes it or refuses it (a refusal is a recorded no-op)": the gate is effect-free and ρ
  writes the record, so never word it as γ recording anything.
- Both "Factored (The Outer Kernel)" bubble headers are section citations of the doc's
  *The outer kernel* passage — not a copy-paste error; don't "fix" them either.

Patching one label without regenerating (2026-11-09, the bad-set label, now B∩G=∅ — #1597):
- When the text outdates a single label, rebuild only that line from the figure's own pixels.
  Borrow the letter from another label (the regular G came from "(Ground-Truth Success)"; label
  sizes differ, cap height 14.4 vs 15.0 px there, so scale it to the target line and seat it on that
  line's baseline). Move the neighbouring text as whole-pixel blocks WITH its 1-px bright rim, fill
  the paper it vacates from blank rows nearby, and re-centre the line under its neighbour.
  Inpainting under the old glyphs leaves light ghosts, because the rims stay behind.
- Verify by pixel diff confined to the line's box, same size and mode, PNG chunks IHDR/IDAT/IEND
  only; then fetch the pushed image from the media endpoint and compare hashes.
- LFS: where the checkout's LFS filter skips smudge, the working file is the pointer text — take
  the bytes from the media endpoint or `git lfs fetch`. `git add` of the real PNG stores the
  pointer; push the object with `git lfs push origin <branch>` before the branch.
- Commit the bytes produced in the working tree, not a copy that has been through a chat
  attachment: delivery can append a provenance chunk (`caBX`).

Checked label by label against the text on 2026-11-09. Apart from the following, every label is
supported: "only writer of Authority", where the text says only the top writer *widens* it; the
parse-failure callout, set with the residual stream and belonging to the readout; the Effect-E,
halt-pipe and owner arrows; coin characters for π and ρ. These are collected in #1599 for the next
redraw. They need a redraw or a wording decision; do not patch arrows.

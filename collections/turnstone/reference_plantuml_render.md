---
name: reference_plantuml_render
description: "Re-rendering a docs/diagrams/*.puml after editing it: the system plantuml (1.2020) fails on `!theme plain`; use a current plantuml jar, and never let a failed render overwrite the committed PNG."
metadata:
  node_type: memory
  type: reference
  modified: 2026-11-05T16:15:14.723Z
---

The repo's diagrams (`docs/diagrams/NN-*.puml`) start with `!theme plain`, which an older
distribution-packaged `plantuml` (1.2020.02) rejects with "Error line 1": it writes a small error
PNG instead of the diagram, and `plantuml -o png` overwrites `docs/diagrams/png/NN-*.png` with it.

What worked (2026-10-04, #988 watch diagram): fetch a current jar into the session scratchpad,
`https://repo1.maven.org/maven2/net/sourceforge/plantuml/plantuml/1.2025.0/plantuml-1.2025.0.jar`,
render a COPY of the .puml in the scratchpad (`java -jar plantuml.jar -tpng file.puml`), look at the
result, then copy the PNG into `docs/diagrams/png/`. The PNGs are Git LFS objects (`*.png` in
`.gitattributes`); `git show HEAD:<png>` prints the LFS pointer, not the image. If a bad render
lands in the tree, `git checkout HEAD -- docs/diagrams/png/<file>.png` restores the committed image.
Image width differs slightly from older renders (font/version), which is cosmetic.

**Tall diagrams get cropped silently (2026-10-22, #1464).** PlantUML caps images at 4096 px by
default and writes the cropped PNG without an error: `03-core-engine-classes` came out 3579x4096
against the committed 3579x4255. Render with `java -DPLANTUML_LIMIT_SIZE=16384 -jar ...`, then
check the new PNG's size against the committed one and diff the two (Pillow's
`ImageChops.difference(old, new).getbbox()`); crop that box and look at it, so a one-box edit
shows up as one changed region and nothing else moved.

**Picking the jar (2026-11-05, diagram 27).** Maven Central's `maven-metadata.xml` reports
`<latest>`/`<release>` as `8059`, a pre-2018 build whose number outranks the current
`1.YYYY.N` scheme; list the `<version>` entries and take the newest `1.YYYY.N` (1.2026.9 then).
Fetch the `.sha1` published beside the jar and compare before running it. A jar render comes out
as an 8-bit palette PNG where the older renders are RGB, and its fonts measure slightly wider;
both are cosmetic.

Related: [[project_readme_harness_diagram]] (the README harness PNG has a deliberate typo).

---
name: reference_plantuml_render
description: "Re-rendering a docs/diagrams/*.puml after editing it: the system plantuml (1.2020) fails on `!theme plain`; use a current plantuml jar, and never let a failed render overwrite the committed PNG."
metadata:
  node_type: memory
  type: reference
  modified: 2026-10-04T18:39:39.043Z
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

Related: [[project_readme_harness_diagram]] (the README harness PNG has a deliberate typo).

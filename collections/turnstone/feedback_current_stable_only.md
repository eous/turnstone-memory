---
name: feedback_current_stable_only
description: "Chart, image or deploy change needing a fallback for an older release: don't add one; support the current stable line only (1.9.4+ as of 2026-11-08), unconditional floors (maintainer, 2026-11-08)."
metadata:
  type: feedback
---

The maintainer ruled on 2026-11-08, scoping the Helm change that runs the server and console
containers under tini (the first PR for #1326), that deployment and packaging changes support only
the current stable version, 1.9.4 and later at the time. Legacy support adds complexity the project
does not need.

**Why:** a values flag for images without tini, a conditional template arm, or a documented floor
for a retired line is a path nobody runs, and each one has to be tested and kept. The 1.8 line is
emergency-only ([[project_current_state]]).

**How to apply:** when a chart, compose, systemd or image change would need a fallback for an older
image or release, drop the fallback and state the requirement in one CHANGELOG line. Prefer an
unconditional floor (Chart.yaml `kubeVersion`, the image the chart defaults to) over a conditional
template branch. The same instinct as [[feedback_minimal_scope_first]], applied to deploy artifacts.

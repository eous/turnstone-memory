---
name: reference_dual_design_challenge
description: "Independent design reviews: use the same neutral brief, verify claims against source, and measure disagreements before deciding."
metadata:
  type: reference
---

For a consequential design, independent reviews can expose assumptions that a shared discussion
misses. The replay-identity proposal ([[project_replay_identity_ir_origin]]) used this approach
on 2026-09-25.

Write one neutral, self-contained brief. Describe the proposal as under consideration and ask for
fact checks with file and line references, strong objections, omitted cases, simpler alternatives,
and a verdict. Include the relevant design notes and tests. Give each reviewer the same brief
without the other reviewer's conclusions.

Run reviews with explicit read-only access. For a background CLI invocation, redirect stdin from
`/dev/null` if the tool would otherwise wait for input, and save the report to a separate scratch
path. Do not depend on the machine's default sandbox or approval settings.

Check dated issue and PR state against the public source. Agreement is useful evidence;
disagreement identifies a question to verify with code, a boundary probe, or a measured comparison.
One exercise does not establish general strengths or weaknesses of particular models.

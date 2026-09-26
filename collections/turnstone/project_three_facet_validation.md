---
name: Three-facet intent validation
description: "Touching judge.py heuristics, output_guard.py, or skill_scanner.py: three-facet validation is COMPLETED and shipped; the output guard annotates, never gates."
type: project
---

Three-facet validation pipeline — all three facets shipped and in production:

1. **Input heuristic enrichment** (judge.py): 23→36 rules. New patterns from
   25K skills.sh audit analysis: download-exec chains, browser-data-export,
   transitive-install, control-plane-mutation, content-ingestion,
   interpreter-exec, cloud-infra-mutation. `crontab -l` read-only fix.

2. **Output guard** (output_guard.py): Evaluates tool results before they
   enter conversation. P1-P5 priority-ordered checks: prompt injection,
   credential leakage, encoded payloads, adversarial URLs, system info
   disclosure. Time-budgeted (5s), annotates + optionally redacts, does NOT
   gate. `output_assessments` table (migration 022). SSE `output_warning`
   events. 42 tests.

3. **Skill scanner** (skill_scanner.py): Evaluates SKILL.md content at
   create/update time. Four axes: content risk, supply chain risk,
   vulnerability risk, declared capability risk (from `allowed_tools`).
   Composite 25% equal-weight formula. 30+ regex patterns. `SCANNER_VERSION
   = "1"` for re-scan triggering. ~2ms per scan.

4. **Data pipeline**: migration 022 adds `output_assessments` table +
   `scan_version` on `prompt_templates`. Builds calibration dataset for
   future smart approval system.

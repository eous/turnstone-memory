---
name: feedback_no_inhouse_json_schema_validation
description: "Checking JSON Schema documents (MCP tool input schemas etc.): keep the jsonschema library; never propose an in-house validator or keyword walk to replace it (maintainer, 2026-11-06)."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-11-07T04:27:55.230Z
---

The maintainer will not maintain an in-house JSON Schema validator. A review stage once
recommended replacing the jsonschema metaschema check of MCP tool input schemas with a
table-driven linear walk of the 2020-12 keywords, with jsonschema kept as a test oracle. It
measured about 170x faster, and the maintainer still turned it down: a second definition of
"valid JSON Schema" is a maintenance burden the project won't own.

The same decision set the tone for the check's cost: keep it simple. Fix correctness bugs, and
cheap regressions whose fix removes code, such as a cache key that hands off the GIL. Present
heavier containment, such as a child process or layered in-process guards, as options with
their costs, not as the default.

**Why:** owning schema-validation rules means keeping them in step with the JSON Schema dialects
and with what providers enforce. The library already does that.

**How to apply:** when a finding concerns jsonschema's cost or worst cases, look for a fix
inside the library's public API or around how often it runs (caching, dialect choice). Don't
raise a hand-written validator as an option. Related: [[feedback_minimal_scope_first]],
[[feedback_nonconverging_reviews_mean_simplify]].

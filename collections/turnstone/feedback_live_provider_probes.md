---
name: feedback_live_provider_probes
description: "Before a live provider probe (-m live, livepass.py): exhaust offline instruments first; ask the maintainer before any live call."
metadata:
  type: feedback
---

Live provider API calls (`-m live`, `scripts/livepass.py`, ad hoc probes) are a last-resort
verification step. Unanswered vendor-side questions can stay open; bound the risk in code.

**How to apply:**
- Exhaust offline instruments first, and say which one closed the question:
  - **MockTransport body capture** shows exactly what the SDK puts on the wire (it proved the
    Anthropic SDK passes unknown content-block keys through verbatim). See
    [[feedback_sdk_boundary_testing]].
  - **The uv cache as a version museum**: `find ~/.cache/uv -iname "*anthropic*"` finds older SDK
    versions on disk to grep, before assuming a dependency floor must rise.
  - **Direct `model_validate` probes** show how the SDK treats unknown values.
- Client-side behaviour is answerable offline; server-side behaviour (does the API emit or reject
  X?) is not at any effort. Say so plainly rather than launching a sweep that cannot answer it.
- When a live probe is the only instrument, ask the maintainer before running it.
- Keep probe logistics out of PRs, issues, commit messages and other outward artifacts.

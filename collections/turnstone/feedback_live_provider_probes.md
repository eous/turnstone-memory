---
name: feedback_live_provider_probes
description: "Before a live provider probe (-m live, livepass.py): exhaust offline instruments first; hosted calls need an OK; a local vLLM needs no ask; model-facing changes get one local e2e check."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-11-01T12:46:09.679Z
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
- When a live probe is the only instrument, ask the maintainer before running it against a
  hosted provider (Claude, OpenAI): every call is billed.
- **Exception, the maintainer 2026-10-06 (#1291):** a local Qwen model on a vLLM server costs
  only time, so probes and eval sweeps against it need no ask; use it to settle a question
  before spending on hosted runs. Review and verifier agents still stay off it: they add load,
  and nobody scheduled their runs with the maintainer.
- **Model-facing changes, the maintainer 2026-11-05 (web_fetch links):** when a change's goal
  is a model's behavior (prompt wording, what a tool hands a model), offline tests prove only
  what reaches the model. Before the commit, run one end-to-end check on the local model: real
  inputs through the real code path, with only the network and the model call swapped, and
  score the answers. That run showed the extraction model still padding a requested link list
  with URLs recalled from training, which no unit test could have shown.
- Keep probe logistics out of PRs, issues, commit messages and other outward artifacts.
- A test list built by grep picks up `*_live.py` modules, and pytest has no default marker filter
  here, so they run for real: pass `-m "not live"` on any widened run. It happened on 2026-11-01
  (#1529): two such modules sent `GET /v1/models` to `localhost:8000` and got a 404.

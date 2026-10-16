---
name: hub_references
description: "Index of reference memories: review recovery, design challenges, header wire-safety, formalism, GitHub math, GB10/vLLM, small-model repro, skills, Entra harness, audio, tooling, release sites."
metadata:
  type: reference
---

## References
- [Review workflow recovery](reference_code_review_workflow_recovery.md) — Review workflow crash or capped report → mine journal .result / synthesize prompt
- [HTTP header wire-safety](reference_http_header_wire_safety.md) — User text in a response header → latin1_safe_filename; TestClient misses the h11/httptools layer
- [Harness formalism grounding](reference_harness_formalism_grounding.md) — Citing the harness formalism → Foster-Lyapunov/delta proven; nested-chain framings are conjecture
- [GitHub Markdown math rendering](reference_github_markdown_math_rendering.md) — LaTeX in a GitHub-rendered doc: $`…`$ inline and top-level ```math fences only; probe with gh api markdown
- [GB10 Spark vLLM tuning](reference_gb10_spark_vllm_tuning.md) — GB10 Spark vLLM stack: drop page cache, start models sequentially; deploy/vllm-litellm/ is truth
- [Turnstone skill authoring](reference_turnstone_skill_authoring.md) — Authoring a turnstone SKILL.md → 10 allowlisted files max; cite them via ${TURNSTONE_SKILL_DIR}
- Audio: [Provider audio APIs](reference_provider_audio_apis.md) — Voice I/O backend: OpenAI audio wire protocol everywhere; Anthropic has none; vLLM-Omni for OSS
- Audio: [vLLM omni chat-audio](reference_vllm_omni_audio.md) — vLLM omni audio: stock image lacks vllm[audio]; wav + thinking off + prompt-then-audio
- Tooling: [Headless Chrome render](reference_headless_chrome_frontend_render.md) — Frontend unverifiable without a server? headless chrome on a file:// harness in the sandbox
- Tooling: [PlantUML render](reference_plantuml_render.md) — Re-rendering a docs/diagrams/*.puml after editing it: the system plantuml (1.2020) fails on `!theme plain`; use a current plantuml jar, and never let a failed render overwrite the committed PNG.
- [Dual design challenge](reference_dual_design_challenge.md) — Independent design reviews: use the same neutral brief, verify claims against source, and measure disagreements before deciding.
- [Entra OBO harness](reference_entra_obo_harness.md) — Standing up a live oauth_obo MCP test against a real Entra tenant on the docker dev cluster: app regs, the admin-consent quirk, broker/server deploy, HTTPS trust, Azure policy gotchas.
- [Small-model repro without a GPU](reference_small_model_repro_without_gpu.md) — Reproducing a small-model bug without a GPU: llama.cpp llama-server on a CPU-only cloud box, turnstone-eval flags that give real rates, speeds, baseline venv, hosted models.
- Release: [Static site release checks](reference_static_site_release_checks.md) — Static release sites: update visible and metadata versions, test installer proxy failures, and verify a complete download before replacing a fallback.

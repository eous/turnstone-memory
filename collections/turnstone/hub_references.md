---
name: hub_references
description: "Index of reference memories: review-workflow recovery, header wire-safety, formalism, GB10/vLLM tuning, skill authoring, Entra harness, audio, tooling (moved verbatim 09-25)."
metadata:
  type: reference
---

## References
- [Review workflow recovery](reference_code_review_workflow_recovery.md) — Review workflow crash or capped report → mine journal .result / synthesize prompt
- [HTTP header wire-safety](reference_http_header_wire_safety.md) — User text in a response header → latin1_safe_filename; TestClient misses the h11/httptools layer
- [Harness formalism grounding](reference_harness_formalism_grounding.md) — Citing the harness formalism → Foster-Lyapunov/delta proven; nested-chain framings are conjecture
- [GB10 Spark vLLM tuning](reference_gb10_spark_vllm_tuning.md) — GB10 Spark vLLM stack: drop page cache, start models sequentially; deploy/vllm-litellm/ is truth
- [Turnstone skill authoring](reference_turnstone_skill_authoring.md) — Authoring a turnstone SKILL.md → 10 allowlisted files max; cite them via ${TURNSTONE_SKILL_DIR}
- Audio: [Provider audio APIs](reference_provider_audio_apis.md) — Voice I/O backend: OpenAI audio wire protocol everywhere; Anthropic has none; vLLM-Omni for OSS
- Audio: [vLLM omni chat-audio](reference_vllm_omni_audio.md) — vLLM omni audio: stock image lacks vllm[audio]; wav + thinking off + prompt-then-audio
- Tooling: [Headless Chrome render](reference_headless_chrome_frontend_render.md) — Frontend unverifiable without a server? headless chrome on a file:// harness in the sandbox

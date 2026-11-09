---
name: reference_vision_api_transparency
description: "How vision APIs and model servers flatten a transparent PNG/WebP before the model sees it (measured 2026-10-21): white, black or alpha dropped, by vendor, endpoint and format."
metadata:
  type: reference
---

Vision encoders take RGB, so every serving stack removes an image's alpha channel before the model
sees it, and they disagree. Measured 2026-10-21 for #1445 with a probe image whose transparent
pixels store red RGB and which holds a white word and a black word: a white fill shows only the
black word, a black fill only the white word, and a dropped alpha channel shows both on red.

| Serving path | RGBA PNG | WebP with alpha | Palette PNG (tRNS) |
|---|---|---|---|
| OpenAI gpt-6-astra (direct) and gpt-5.6-luna | alpha dropped | alpha dropped | alpha dropped |
| Anthropic claude-haiku-5-5 (direct, and on AWS) | white | white | white |
| Google gemini-3.8-flash on Vertex | black | black | black |
| Google gemini-3.8-flash on AI Studio | white | alpha dropped | white |
| xAI grok-4.7 | alpha dropped | alpha dropped | alpha dropped |
| vLLM main (read from source) | white | white | white |

- vLLM: `convert_image_mode` composites every transparent mode (RGBA, LA, PA, tRNS) onto white by
  default; 0.20 composited only RGBA and dropped the others' alpha. `--media-io-kwargs
  '{"image": {"rgba_background_color": [0, 0, 0]}}'` changes the colour server-wide.
- llama.cpp's mtmd loader decodes with `stbi_load_from_memory(..., 3)`, which drops the alpha.
  Ollama runs GGML models on llama.cpp's server since 2026-05-29 (ollama#16031), and its MLX
  runner's `dropAlpha` drops it too; the removed Go engine composited onto white. qwen-vl-utils
  composites onto white. WebP and palette handling on llama.cpp and Ollama were not checked.
- The #1445 sample stores white RGB under every pixel, with the word only in the alpha channel. It
  reads only where the fill is black (Gemini on Vertex); everywhere else it is a blank white frame.
  Black content over transparency vanishes on Vertex, and wherever alpha is dropped and the
  encoder stored black under the transparent pixels.
- One or two models per vendor; the same model differed by endpoint (Gemini) and by format (AI
  Studio), so re-measure before quoting another model.

**How to apply:** never rely on a provider's transparency handling; the only way to give every lane
the same pixels is to flatten in turnstone before the wire (the #1445 design). To re-measure, reuse
the probe: the words a model reads decide the fill, and the background colour it names corroborates.
Related: [[project_attachments_subsystem]].

---
name: reference_vllm_omni_audio
description: "Audio attachments or STT-via-chat on vLLM omni (Gemma 4): input_audio verified; stock image lacks vllm[audio]; transcode to wav, thinking off, prompt first."
metadata: 
  node_type: memory
  type: reference
---

Verified against the user's LAN vLLM box (image
`vllm/vllm-openai:latest`, model `/models/gemma-4-12B-it`) on 2026-06-15.

- **Gemma 4 12B-it IS a true omni model** — text + vision + audio. `config.json`:
  `model_type: gemma4_unified` with an `audio_config` (`gemma4_unified_audio`,
  `audio_embed_dim 640`, `audio_samples_per_token 640`) and `audio_token_id 258881`.
  (Gemma 3 was text+vision only — don't assume; read the model config.)
- **Our attachment audio path is VERIFIED.** The internal `input_audio` part
  (`{type:"input_audio", input_audio:{data:<b64>, format:"wav"}}`) passes through
  `sanitize_messages` untouched on the openai-compat lane → vLLM accepts it →
  HTTP 200, model correctly described a 440 Hz tone. vLLM ALSO accepts the
  data-URI `audio_url` shape (symmetric with `image_url`); we use `input_audio`
  because OpenAI cloud audio models require it and vLLM takes it too.
- **`vllm-openai` image gotcha:** stock image ships WITHOUT `vllm[audio]` (no
  `librosa`/`soundfile`). Audio decode then fails with a MISLEADING
  `400 "Invalid or unsupported audio file"` — actually a soundfile ImportError →
  PyAV fallback that treats the WAV as video. Fix: `pip install librosa soundfile`
  (or `vllm[audio]`) AND **restart** — vLLM caches a `PlaceholderModule` for the
  missing dep at boot, so a live install into the running container returns
  `500 "PlaceholderModule should not be used..."` until restart. A `docker
  restart` KEEPS the install (writable layer survives; only recreate wipes it).
  Durable fix = bake `vllm[audio]` into the image.
- To USE native audio on an omni alias, the operator sets
  `supports_audio_input=True` on that model (capability opt-in, like
  `supports_vision` for compat); else the wire gate routes audio to the STT
  fallback. See [[project_canonical_trajectory_redesign]] (AttachmentRef).

Distinct from [[reference_provider_audio_apis]] (STT/TTS *role* landscape) — this
is chat-attachment audio INPUT to an omni chat model.

## Omni STT via chat — verified 2026-06-16 (shipped `fix/omni-stt-transcode-thinking`)

Gemma-4 as the STT role (mic → composer) needs three things `_transcribe_via_chat`
must set itself (it uses the raw client, bypassing the provider's request shaping):

- **Transcode first** — browsers record webm/opus (ogg/mp4); vLLM's omni lane decodes
  ONLY wav/mp3 and SNIFFS the bytes (mislabeled webm still 400s). ffmpeg → 16 kHz mono
  WAV (`-protocol_whitelist pipe -vn -t` for SSRF/decompression-bomb safety); the
  pipe:0→pipe:1 (non-seekable) WAV is vLLM-accepted. Node image needs `ffmpeg` (PyAV
  avoided — no cp314 wheel on py3.14, and a binary dodges the wheel/ABI treadmill).
- **`enable_thinking=false`** (via `cfg.capabilities.thinking_param`) — gemma defaults
  thinking ON; left on it's ~11× slower (12.6s→1.15s on an 11 s clip, 297 vs 24 tokens)
  AND returns EMPTY `content` on some clips. `skip_special_tokens` is NOT needed (that
  gemma vLLM bug is fixed upstream; the `vllm-gemma-thinking` workaround profile was
  removed — don't carry stale fast-moving open-model bug-shims).
- **Prompt THEN audio** (text part before input_audio) — the order Google documents
  for transcription; the "multimodal-before-text" rule is IMAGE-only. `_OMNI_STT_PROMPT`
  is verbatim the official Gemma transcription prompt.

Latency (real speech): TTFT ~0.27s, ~38 ms/tok decode → ~1.15s total. Streaming
(`/speech-to-text/stream`) gives clean deltas (no `<|channel>` markers once thinking
is off); stream from ONE worker thread that owns+closes the OpenAI Stream — per-chunk
`asyncio.to_thread(next, …)` leaks the connection on client disconnect. A dedicated
Whisper endpoint is lower TOTAL latency, but streamed omni at ~1 s is fine.

Methodology: test STT with REAL speech (whisper.cpp `samples/jfk.wav`) — a synthetic
tone produced misleading failures (empty content / 512-tok runaway / prompt-order
"refusal") at every step that all dissolved on a real clip.

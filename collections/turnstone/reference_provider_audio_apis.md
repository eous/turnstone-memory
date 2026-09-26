---
name: reference-provider-audio-apis
description: "STT/TTS backend choice for voice I/O: all use the OpenAI audio wire protocol (only base_url differs); Anthropic has NO audio API; vLLM-Omni for OSS."
metadata: 
  node_type: memory
  type: reference
---

# Provider audio (STT/TTS) API landscape — verified 2026-05-30

For voice I/O / multimodal work ([[project_voice_io]]). All over the **OpenAI audio wire protocol** unless noted (`/v1/audio/transcriptions`, `/v1/audio/speech`), so turnstone's code is identical across backends — only the registry `base_url` differs.

- **OpenAI** — STT: `whisper-1`, `gpt-4o-transcribe`, `gpt-4o-mini-transcribe` (+ `gpt-4o-transcribe-diarize`). TTS: `tts-1`, `tts-1-hd`, `gpt-4o-mini-tts` (steerable). All REST. The NEW May-2026 `gpt-realtime-2` / `-translate` / `-whisper` are **Realtime API (WebSocket)** — a different surface, NOT the REST endpoints; out of scope for the REST-based v1.
- **Anthropic** — **NO audio API.** Messages API is text + images only (audio input is an open, unimplemented feature request). Consumer voice mode uses **ElevenLabs** (listed subcontractor); Anthropic's own cookbook prescribes 3rd-party STT → Claude → 3rd-party TTS. ⇒ Claude is agent-only for voice; capability-gate it out of audio roles.
- **vLLM** — STT: base `vllm serve openai/whisper-large-v3` exposes `/v1/audio/transcriptions` (mature). TTS: via the **vLLM-Omni** subproject's `/v1/audio/speech` (Qwen3-TTS, Voxtral-TTS, CosyVoice3, Fish Speech). Same wire protocol either way. vLLM-Omni also serves audio-IN omni models (Qwen3-Omni) for the later native-multimodal slice. **Recommended OSS target** since turnstone already integrates vLLM. **Update (checked 2026-07-06):** what was "newer, Q2-2026 roadmap" at time of writing has since shipped — vLLM-Omni reached v0.22.0 (June 2026), Qwen3-TTS is reported production-quality (RTF 0.34, TTFA ~131ms), Voxtral TTS has day-0 support. Turnstone's own gemma-4-12B-it omni deployment (audio input, not vLLM-Omni's TTS path) is verified separately — [[reference_vllm_omni_audio]].
- **OSS one-stop alternatives** — Speaches (faster-whisper STT + Kokoro/Piper TTS, both OpenAI-compatible), Kokoro-FastAPI (TTS, CPU-friendly), faster-whisper-server (STT). Same wire protocol; a lightweight TTS fallback if vLLM-Omni is too heavy.
- **Google Gemini** (fast-follow, not wired) — native audio in/out, but via `generateContent`, NOT the OpenAI wire protocol → would need GoogleProvider audio methods.

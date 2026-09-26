---
name: project-voice-io
description: "Voice STT/TTS (v1 SHIPPED PR #618; core/audio.py): OpenAI audio wire protocol is the abstraction, Anthropic gated out of audio roles; roadmap items unstarted."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-26T00:22:05.859Z
---

# Voice I/O — productionizing the multimodal demo

v1 shipped in **PR #618** (`feat/voice-io` off `main`, 2026-05-30). Origin: extracted/rebuilt from `experiment.patch` (an external contributor) — a 9-commit demo of speaking to turnstone (mic→transcript, assistant→speech, A/V attachments, an async "facilitator"). Unverified whether the manual-E2E/docs items noted below as "outstanding before merge" were actually completed pre-merge or waived — no further voice-io PR or branch exists as of 2026-07-06, and none of the 4 roadmap items below have any branch/PR either, so treat the whole "Deferred" section as still-accurate, unstarted roadmap.

## What v1 is
Browser **voice input** (mic dictation → transcript fills composer for review-then-send) + **voice output** (per-assistant-message 🔊 playback). Provider-backed over the **OpenAI audio wire protocol** (`/v1/audio/transcriptions`, `/v1/audio/speech`) so one code path serves OpenAI, vLLM/vLLM-Omni, or any compatible server via `base_url` — no in-process model deps.

## Architecture (where things live)
- `turnstone/core/audio.py` — `resolve_role_alias()` (config_store + registry + capability gate), `transcribe()` / `synthesize()` over a registry-resolved OpenAI-SDK client; typed `AudioUnavailableError` (503) / `AudioBackendError` (502 — body masked, SDK detail logged). Optional STT `prompt`.
- Endpoints in `server.py`: `POST /v1/api/workstreams/{ws_id}/speech-to-text` (multipart `audio`, 25 MiB), `POST /v1/api/tts` (JSON, 8000-char). In `v1_routes`; write-scoped in `auth.py` (direct + proxied `/node/`); both `await asyncio.to_thread(...)` the blocking SDK call. Silence→422; configured-but-failed backend→masked 502.
- **Model roles** (the config surface): settings `audio.stt_model_alias` / `audio.tts_model_alias` / `audio.tts_voice` / `audio.stt_prompt` (section "audio", label "Voice"). In **Models→Roles** (`admin.js` `MODEL_ROLES`, capability-gated dropdowns, blank = "(disabled — voice off)") AND the raw Settings tab (the two aliases via `ALIAS_SETTING_KEYS` → filtered dropdowns; voice/prompt are free text). `/v1/api/models` exposes resolved `stt_default_alias`/`tts_default_alias` + per-model `capabilities`; UI shows mic/🔊 only when the role is configured.
- **Capabilities**: `supports_transcription` / `supports_speech_synthesis` on `ModelCapabilities` (`_protocol.py`); current OpenAI audio lineup registered in `OPENAI_CAPABILITIES` (`_openai_common.py`) so admin "suggested capabilities" recognizes them. Runtime gating reads `cfg.capabilities` dict + a name-inference backstop (`_AUDIO_MODEL_HINTS` in audio.py, mirrored as `AUDIO_MODEL_HINTS` in admin.js — pinned by `tests/test_audio.py`).
- UI (the interactive `Pane` — **moved `ui/static/app.js` → `shared_static/interactive.js`** in L-shell 5a; `shared_static/composer.js` `actionsRowEl`, `shared_static/chat.css`): mic + per-message 🔊; CSS-mask icons (`.icon-mic/.icon-stop/.icon-speaker`); aria-pressed + sr-only live-region announcements; recording timer; reduced-motion cue; error-typed toasts + persistent denial; mic disabled while busy; code/math stripped before TTS.

## Key decisions
- **OpenAI audio wire protocol = the abstraction.** Provider-agnostic; recommended OSS target is **vLLM** (STT on base vLLM, TTS via vLLM-Omni) since turnstone already speaks vLLM — chosen over Speaches/Kokoro.
- **Anthropic has no audio API** → capability-gated OUT of audio roles, stays valid as the *agent* model (Claude-driven workstream + OpenAI/vLLM voice; matches Anthropic's own cookbook). See [[reference_provider_audio_apis]].
- **"Media is ephemeral input; only derived text persists in history."** North-star for the later media slices — never replay raw audio/video into prompts (kills the multi-turn replay bug the patch only half-fixed).
- **Realtime models out of v1 scope** — `gpt-realtime-*` (May 2026) are Realtime-API/WebSocket, not the REST endpoints we use.
- **Reused the existing model-roles mechanism** (per user) rather than bespoke settings — shrank v1 (dropped per-ws override / modal fields). User's note: model-role pickers are normally filtered → role-alias keys go in `ALIAS_SETTING_KEYS`.

## Deferred — remaining components & shapes (the roadmap)
1. **Per-workstream STT/TTS override** — the `judge_model` analog: `stt_model`/`tts_model` on create → session persist/resume → new-ws-modal fields → console proxy threading. Cleanly separable; `resolve_role_alias` is ready to take a session override first.
2. **Media-as-context** — audio/video as attachment *kinds* → transcribe/evaluate → **text/structured context** any model consumes (provider-agnostic; applies "derived text persists"). This is what the patch backed into (its `media_evaluator.py` + `vision_eval`/`av_eval`/`intent_eval` roles).
3. **Native Omni multimodal turn** — capability-gated, current-turn-only, reuses the provider-fidelity lane; never persists raw media.
4. **Facilitator / intent loop** — the novel research bit: async observation (webcam/mic) + `intent_eval` ("addressing the computer" / wake / eye-contact gating), ephemeral-vs-promote thresholds, sidecar-state persistence. Design-heavy.
5. Smaller follow-ups: realtime/streaming STT (partial transcripts), **auto-send toggle** for dictation, voice-picker UX (vs free text), TTS on non-interactive surfaces.

## Outstanding items noted at PR #618 time (status post-merge unverified)
- Manual browser E2E (CSS-mask icons, recording pulse, a11y announcements unrendered in-session). The *render* check can be done in-sandbox via [[reference_headless_chrome_frontend_render]] (file:// harness + mocked authFetch/EventSource) — only the real-audio round-trip needs a live OpenAI/vLLM backend.
- Optional prose docs (settings self-document via help text; API in OpenAPI) — offered, not yet added.

## Lessons learned
- **Stale-base reconciliation anti-pattern** (reviewing experiment.patch): a patch built on an old base and force-reconciled onto a moved `main` becomes ~half reconciliation churn that can *revert deliberate decisions* (it re-added a removed console modal + inverted its guard test) and ship *half-applied fixes* (audio skipped on the live turn but still re-injected on DB reload). Salvage the core idea, rebuild clean — don't land the reconciliation.
- **Don't monkey-patch framework objects** — the patch rewrote `Request.json`/`.body` to fake a send; the clean design returns the transcript and lets the browser send via the normal path.
- **Blocking SDK calls in async handlers stall the shared event loop** (and SSE streaming) → `asyncio.to_thread` (house pattern; caught by the perf finder).
- **Mask backend SDK errors in 5xx bodies** — they carry upstream response detail (host/URL); return a static message, log the detail.
- **The `/review` + `designer` stack earned its keep here** — found the TTS-race blob leak, hot-mic-after-teardown, event-loop blocking, the `--danger`/contrast token bug, emoji-vs-CSS-icon inconsistency, and the busy-mic affordance gap.

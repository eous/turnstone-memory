---
name: project_attachments_subsystem
description: "Image/PDF/audio attachments (SHIPPED v1.6.4-1.6.6): refcounted content-addressed blobs plus capability-gated perception fallback for non-native modalities."
metadata: 
  node_type: memory
  type: project
---

The attachment subsystem grew from image-only to **image + PDF + audio** kinds,
shipped incrementally across **v1.6.4–1.6.6** on both tracks (dormant spine →
translators → UI → hardening). Brief LOCAL: `docs/design/attachments-audio-pdf-brief.md`.

## Durable architecture (the reusable patterns)
- **Content-addressed, refcounted storage** + a **per-node in-memory pending-upload
  buffer**: blobs keyed by content hash, refcount released via `delete_workstream`
  GC. Create-time staged uploads are drained synchronously (the reservation
  scaffolding was retired as vestigial). Ties into AttachmentRef in the canonical
  trajectory ([[project_canonical_trajectory_redesign]]).
- **Universal perception fallback for non-native modalities** — the load-bearing
  design. A model that can't natively take a modality still "sees" it via a
  capability-gated fallback: PDF→page-images (rasterize) for vision models without
  native PDF; PDF→text and audio→transcript client-side fallback; a generic
  perception role. Capability toggles are admin-surfaced (roles tab + settings
  filter). Native paths where they exist: native PDF + audio translators; OpenAI
  Responses native-PDF path (was dead, repaired); **xAI Grok pinned to the
  rasterize-PDF fallback** (no native PDF).
- **Audio gating stands**: audio roles gate to OpenAI-SDK providers only — Anthropic
  has no audio block (see MEMORY.md Provider Capabilities; [[project_voice_io]],
  [[reference_provider_audio_apis]]). Omni models serve STT via the chat
  `input_audio` path ([[reference_vllm_omni_audio]]).

## Security / cost hardening (these were real review findings, keep the patterns)
- Thumbnail/rasterize **DoS**: decompression-bomb cap **40M px** (not 80M); explicit
  thumbnail/rasterize resource bounds.
- **ftyp/ADTS sniffing**: reject video-as-audio in the ftyp sniff; add ADTS-AAC sniff
  so audio detection isn't extension-trusting.
- **Untrusted-input discipline**: sanitize user filenames before they enter model
  context; mark derived text (extracted PDF/transcript) as untrusted.
- **EXIF orientation** normalized so thumbnails and models see upright images.
- **Per-send wire-part memo**: stop re-rasterizing/re-encoding the same attachment on
  every round-trip (perf); stop downloading the whole text blob for a 240-char preview.

## UI
Inline chip previews per kind (image/pdf thumbnail, audio player, text snippet),
on the shared conversation vocabulary; coordinator audio pill + thumbnail-error gaps
fixed; interactive-pane + console attachment forwarding base-prefixed and unified.

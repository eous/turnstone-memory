---
name: project_1108_video_input
description: "#1108 video attachments: attempt 1 parked 09-06 with round-2 review unfixed; read docs/design/1108-video-attempt-1-lessons.md first; rulings stand."
metadata: 
  node_type: memory
  type: project
  modified: 2026-09-06T06:38:11.693Z
---

Design brief (LOCAL, gitignored): `docs/design/1108-video-input-brief.md` — read it before
touching the branch. Frozen against main @ 52357aa1 (2026-09-05).

## Rulings (the maintainer 2026-09-05)
- **Two PRs**: PR 1 = attachment kind `video`, ffmpeg acceptance transcode, `supports_video`,
  chat-lane `video_url` wire + perception tier, console playback, upload progress.
  PR 2 = `read_file` + `web_fetch` on the same acceptance module (`core/video.py`).
- **Retention = newest clips first, within the video share** (`video.context_share`, default 0.20).
  A deterministic lowering pass in `_prepare_wire_structure`: walk turns newest to oldest, keep clip
  refs while the summed estimate fits, older refs lower to an auditable text placeholder naming the
  clip + duration. Trajectory untouched. The maintainer asked whether HYPOTHESIS.md forces
  always-re-send so that the ledger stays honest; answer given and accepted: honesty lives in the
  trajectory (content-addressed original never mutated) and in π being deterministic (doc line 53:
  only *learned* selection costs adequacy; line 210: originals content-addressed, derived form
  auditable against source). Always-inline is not a complete rule (2+ share-capped clips overflow
  the context and push into compaction, the learned selection). Do not re-litigate.

## Design facts (verified in the spike, dev box ffmpeg 8.0.1)
- Late-`moov` mp4 cannot be read from a pipe → input is a temp file with the demuxer pinned
  (`-f mov,mp4,m4a,3gp,3g2,mj2` / `-f matroska,webm`) + `-protocol_whitelist file`.
- Canonical profile: H.264 yuv420p mp4 `+faststart`, ≤640×360 ceiling scaled down to fit the
  share, ≤15 fps, `-maxrate 1000k`, AAC 64k mono. 60 s 1080p → 5.5 s wall, 1.8 MiB.
- `-fs` is a soft guard (overshoots by a packet + trailer); verify size after the run.
- Clip facts (duration/dims) parse from the faststart header (`mvhd`/`tkhd`) — one derivation
  for live + reload meta; NO migration.
- Qwen3-VL estimator: tokens/s = (W//32)·(H//32) at 2 fps / temporal patch 2. 640×360 → 220
  tokens/s; 300 s → 66K (25% of 262K). vLLM accepts `data:` URLs for `video_url`
  (`MediaConnector.load_from_url` → `VideoMediaIO.load_base64`); domain allowlists apply to
  http only.
- Progress: upload POST negotiates `Accept: application/x-ndjson` → streamed stage/progress
  lines + final JSON; other clients get the single JSON object (SDK unchanged).

## ATTEMPT 1 PARKED (the maintainer 2026-09-06: step back, apply the lessons, close this attempt)
- Branch `feat/1108-video-attachments` @ 9c69aa8f, unpushed, no PR; suite green there; round-2
  review (13 clusters, 7 major) NOT fixed. Do not resume the branch — start attempt 2 from the
  brief + `docs/design/1108-video-attempt-1-lessons.md` (LOCAL). Reuse only core/video.py's pure
  parts (sniff, mp4_facts, estimator, planner, ffmpeg recipe) and the provider/settings plumbing.
- Root causes: retention pass placed after materialization (model_turn materializes BEFORE
  prepare_wire — test on `materialize_attachments` output); the 256 MiB upload ceiling rewrote
  the whole ingest path (needs its own PR + a dedicated video route / bounded spool); resource
  ownership spread over handler/response/worker (acquire+release in the one shared function);
  derive-facts-from-bytes forced whole-blob reads on resume/history (list readers first, a
  `meta` column may be cheaper); scope past minimal v1; reviews non-converging after round 1.

## Branch state (2026-09-06, historical)
- PR 1 implemented on `feat/1108-video-attachments` (from main 52357aa1): `core/video.py`
  (sniff, mp4 header facts, Qwen-family estimator, scale planner, bounded ffmpeg acceptance
  with progress + cancel), classifier order image→pdf→video→audio, `supports_video`,
  chat-lane `video_url` + Responses/Anthropic placeholders, perception tier, retention pass
  in `lowering.py` (+ session memo `_retired_video_ids`), NDJSON upload progress (node +
  console streaming proxy), console `<video>` preview + chip progress, settings
  `video.max_seconds` / `video.context_share`, docs (api-reference, console.md), tests.
- Token accounting rides the fixed-cost media slot of `_msg_text_chars` (units of
  `_IMAGE_TOKENS`); no `MessageMeasure` signature change.
- Known follow-ups (not in PR 1): display path base64-encodes clips it then discards
  (pre-existing shape, larger for video); Range-served playback; poster thumbnails;
  PR 2 = read_file + web_fetch.

## Review round 1 (09-06): 19 confirmed clusters, all fixed in the amended commit
- Retention must happen in the RESOLVER (`_resolve_attachments(retired_video=...)`): model_turn
  materializes before prepare_wire, so a lowering pass alone is inert on the live path.
- Uploads: spooled part + head sniff (`read_multipart_upload_or_400`, `SNIFF_HEAD_BYTES`);
  video never enters RAM; admission = 2 in flight, third → 503 busy; ftyp scan clamped.
- Console proxy streams both directions with Content-Length forwarded, read timeout 180 s.
- `load_messages(materialize_media=False)` for /history keeps opaque kinds by reference.
- Not applied (pins/vetted code): audio-sniffer symmetry, compaction.py rename.

## Needs the maintainer
- Dev cluster: relaunch the Qwen alias with `--limit-mm-per-prompt.video 1`, set
  `supports_video` on it, send the spike clip, compare `usage.prompt_tokens` with the
  estimator. Confirm the 20% share.

Related: [[project_attachments_subsystem]], [[reference_vllm_omni_audio]],
[[project_harness_hypothesis_doc]], [[feedback_context_shares_conservative]].

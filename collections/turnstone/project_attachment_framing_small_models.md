---
name: project_attachment_framing_small_models
description: "Small models looking on disk for an attached file (Nemotron 4B/30B): cause, the wire label + read_file not-found note (#1220), attachment eval cases, per-model results, open gaps."
metadata:
  type: project
---

A community bug report: with Nemotron-3-Nano-4B, attaching a file or pasting long text made
Turnstone call `read_file` on the file's name, search the workspace, report the file missing, and
offer to create it. Reproduced on the production wire and fixed in #1220 (2026-09-28).

## Cause

- A text attachment reached the wire as a bare document part after the user's text:
  `<document name="notes.md" media_type="text/markdown">…</document>` on the text lanes
  (`format_document_wrapper`), a titled document block on Anthropic. Nothing said the block is the
  file the user is asking about, or that it is not on disk.
- The tool guidance pulls the other way: `search` says to use `read_file` once file names are
  known, `read_file` says to read all named files first, and `write_file` says to create requested
  files with plausible content. Small models follow the tool guidance.
- Long pastes take the same path, as a `pasted-text.txt` attachment ([[project_paste_to_attachment]]).

## Fix

- The send-path wire resolver (`_wire_content_part`) puts `attached_file_label(filename)` before
  each text attachment: `[Attached file 'notes.md' — its full contents follow; attachments are not
  saved to disk]`. The name goes through `safe_attachment_label`. The history and export resolvers
  do not add it, so the UI never shows it.
- `_attached_file_note(path)`: when `read_file` (text or image path) misses a path whose basename
  matches, case-insensitively, a filename in any user turn's `attachments_meta` (every attachment
  kind), the error adds that the user attached a file of that name, that attachments are not saved
  to disk, and to use the attachment in their message.
- No tool-definition change. The label is deterministic per filename and rides in the user turn
  that carries the attachment; the note rides in a tool result. Cached prompt prefixes stay valid,
  and a conversation that already holds text attachments re-renders those turns once after the
  upgrade. The maintainer's review checked exactly this (a tool description changing mid-session
  would break prefill caching), so keep per-conversation hints in messages and tool results rather
  than tool definitions.
- Tried and dropped: appending "Not for files the user attached to their message…" to
  `read_file`'s description changed nothing on the 4B (8 of 10 runs still opened with `read_file`).

## Eval harness support

- Case fields: `attachments` (`{filename, content, mime_type}`, text only, classified by
  `classify_upload`, content-hash ids), `forbidden_actions` (any matching tool call scores the run
  0) and `expected_content` (regexes the final answer must match). `score_case_run` layers them on
  `score_run`; `validate_case` rejects a malformed suite at load.
- Two traps any attachment eval must clear: the headless loop must hand `model_turn` the send
  path's attachment resolver (before #1220 by-reference parts were dropped before the wire), and
  the workstream must be registered or the attachment rows are discarded
  (`conversation_rows_discarded_workstream_gone`).
- `eval_attachments.json` at the repo root: a named markdown file, "the attached document" with no
  name, a `pasted-text.txt` paste, a question only the attachment answers, and a source file missing
  from a code workspace. Each forbids workspace lookups and writes and checks for a fact only the
  attachment holds.

## Results (historical evidence, 2026-09-28; 5-10 runs per case)

clean = no forbidden call and the answer has the attachment's fact; recovered = looked on disk
first, still answered from the attachment, wrote nothing; failed = fact missing, or wrote a file.

| Model | Before (clean/recovered/failed) | After |
|---|---|---|
| Nemotron-3-Nano-4B, Q4_K_M on llama.cpp | 11/5/9 (25 runs) | 12/18/0 (30 runs) |
| Nemotron 3 Nano 30B-A3B, hosted | 29/14/7 (50) | 41/8/1 (50) |
| Qwen3.8-27B, hosted | 49/1/0 (50) | 49/1/0 (50) |
| Gemma 4 26B-A4B, hosted | 50/0/0 (50) | 50/0/0 (50) |

- A Nemotron-family problem: Qwen3.8-27B and Gemma 4 read attachments correctly, and the fix
  leaves them unchanged. It adds context rather than trimming it
  ([[feedback_dont_trim_for_small_models]]).
- The two parts act differently. On the 30B the label cut first-move `read_file` calls from 20 to
  8 of 50. The 4B still opens with `read_file` about 70% of the time either way; the note turns
  each of those lookups into a correct answer.
- Hosted runs used OpenRouter, which picks the serving provider. Method:
  [[reference_small_model_repro_without_gpu]].

## Open gaps (verified 2026-09-28)

- The one remaining 30B failure called `open_preview(target='attachment:pasted-text.txt')`;
  `open_preview`'s not-found error carries no attachment note.
- Image and rasterized-PDF parts carry no filename on the wire, and the label is text-only, so for
  "what's in screenshot.png?" the not-found note is the only cue.
- The Discord channel forwards only `message.content` (`channels/discord/cog.py`): files attached
  in Discord, including the `message.txt` Discord makes from a long paste, never reach the model.

Related: [[project_attachments_subsystem]].

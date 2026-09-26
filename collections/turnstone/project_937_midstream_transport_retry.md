---
name: project-937-midstream-transport-retry
description: "Mid-stream httpx death in a stream consumer (#937, shipped PR #967): normalize to IncompleteStreamError at the iteration site, never pad retryable sets."
metadata: 
  node_type: memory
  type: project
  modified: 2026-08-05T14:44:12.447Z
---

Issue #937 (fully verified 2026-08-03 — every claim confirmed):
mid-stream `httpx.ReadError` kills the interactive turn fatally while utility lanes
recover. Design in local `docs/design/937-midstream-transport-retry.md`. Shipped
as PR #967 (2026-08-04) after 5 review rounds (findings 6→14→3→12→4). Round-5 lesson: a workflow review
whose finders all died reports a VACUOUS "no findings" — check the
failures block before trusting a clean result; resume with SAME args.

**DON'T MINE THE ISSUE BODY FOR THE SHIPPED MECHANISM.** #937's own "Root cause
analysis" section proposes adding `ReadError` to `RETRYABLE_ERROR_NAMES` — the
fix #967 explicitly REJECTED. The report is accurate on
*symptoms*, wrong on *remedy*. Read PR #967's body (and the code) for what
actually landed; the issue body is a bug report, not a design.

**Architecture law this hinges on**: raw httpx transport failures are normalized to
`IncompleteStreamError` AT THE ITERATION SITE (`drain_stream`, `_protocol.py` —
post-finish blips tolerated, keep the completed result). Provider
`retryable_error_names` sets hold SDK/normalized names ONLY — never add raw
transport names (`ReadError` etc.) to them; give un-normalized consumers the
normalization instead. `_stream_response` is the sole inline consumer (one call
site in send()); compaction summarizer and task-agent loop route through
`model_turn`/`drain_stream` and were already covered.

**SDK boundary, VERIFIED offline (probe via `httpx.MockTransport` through the real
SDKs — no live endpoint needed)**: both openai (2.52.0) `create(stream=True)` and
anthropic (0.120.2) `messages.stream()` helper propagate mid-body transport deaths
UNWRAPPED (`type(exc).__name__ == "ReadError"`, still `httpx.TransportError`);
SDK `max_retries` engages only at request time (mid-body death → zero re-requests).
Probe pattern: MockTransport handler returning a Response whose SyncByteStream
yields valid SSE then raises — cheap, deterministic, worth promoting into
boundary-pinning tests on any SDK-adjacent stream work.

**Fatal-error observability gap (pre-fix)**: `_record_fatal_error` writes UI +
workstream-config only, `clear_last_error` wipes on recovery, server worker
closures don't log either → chat-lane fatals leave zero journald trace at default
levels. Any future fatal-path work must keep the sanitize-before-log floor
(credential-bearing ConnectError text).

**Dataflow-map round (2026-08-03) — design rev 2 deltas, all probed/verified:**
- Cross-thread `httpx.Client.close()` (= `ModelRegistry.reload()` closing cached
  clients, model_registry.py:527) surfaces on the in-flight read as
  `httpx.ReadError` ("Bad file descriptor") — a TransportError, so it converts
  and retry gates PASS; re-create on the closed client raises **retryable
  `APIConnectionError`** (SDK wraps httpx's RuntimeError) → would burn the full
  creation ladder. Fix: generation-gated `_refresh_model_from_registry()` before
  each mid-stream re-create + guarded re-create that re-raises the ORIGINAL error.
- `on_turn_committed` emits NO SSE event — server-buffer reset only. Any "the UI
  self-heals at commit" reasoning is false for browser DOM / Slack / Discord / CLI.
- The designed seam for mid-turn stream resets: `on_stream_end()` is per-segment
  BY DESIGN in every consumer (browser finalize→new bubble, interactive.js:2104
  comment; Slack pops+recreates StreamingMessage; CLI md.flush + fence reset).
  Compose `on_stream_end()` + `on_turn_committed()` and the replay ring stays
  coherent by construction.
- `GenerationCancelled` subclasses **BaseException** (session.py:259) — `except
  Exception` cannot swallow cancels; every abort producer sets `_cancel_event`
  before closing or bumps `_generation`.
- Slack/Discord dispatchers DROP info events entirely (pre-existing parity gap).
- audio.py transcription lane iterates a raw SDK stream (only non-LLM-path inline
  consumer) — ruled out of #937 scope; own error contract.

**xhigh review round (2026-08-04)**: 14 CONFIRMED correctness findings in the
retry window, all mine/fix-round-introduced — the durable lesson: **shared
session slots written from exception arms are orphan-poisoning hazards; carry
per-attempt state ON the raised exception (thread-private) into wrapper-locals
instead of gating every write site**. Also: `_format_backend_error` stubs
predate new session fields (use getattr); reload() keeps pooled clients on
model-only swaps (rebind checks need the binding TRIPLE, not client identity);
transport_guarded's post-finish tolerance needs a post-loop cancel re-check or
Stops in the trailing-metadata window commit the turn and run its tools.
Journal-mined 8 capped cleanups (recovery memory procedure worked verbatim);
RecordingUI cross-suite consolidation left as follow-up.

**HYPOTHESIS.md mapping (2026-08-04, in design doc)**: mid-body death = M_W
kernel coin (M_W includes serving substrate); the retried region is EFFECT-FREE
by construction (retry boundary == kernel-draw boundary; no γ/Q_E/ρ inside), so
dead attempts are disposition `none`, never `unknown` — the formal license for
the retry. NEVER copy this retry onto a tool/effect lane (that's the double-send
bug; needs effect-record machinery). Bounded _MID_STREAM_RETRIES = the doc's
"retry budget inside V̂" certificate device; `stream.retry` log = the C4
drift-calibration instrument. Kernel-identity provenance gap (version-in-s;
reload/fallback mid-retry can hand the accepted readout to a different kernel
while the turn is attributed to the primary alias) → FILED #964. Substrate-
adversary resample-selection: ruled out of scope 2026-08-04, no issue.

**Reasoning-seam thread (#940 → #965, 2026-08-04)**: web_fetch extraction leaked
raw `<think>` into tool results — audit showed the model_turn lift was
transport-complete but SEMANTICS-incomplete: inline-reasoning segregation was
per-caller and only 2 of ~9 drained-content consumers strip (title, summarizer;
extraction/task_agent/judge/perception/optimizer do not). Filed #965: one
source of truth at the turn-IR seam via ThinkTagSplitter one-shot (segregate
into result.reasoning, never discard), delete per-caller strips. **Splitter
deletion is OFF the table** — #940's reporter (LM Studio + Qwen3.6, inline
tags) is live field proof the interactive lane's Path 2 carries real users.
No 1.7 backport (ruling in MEMORY.md track line). #946 (same reporter) is
judge parallelism — unrelated, don't conflate.

Related: [[project_sse_truncated_resync_hole]] is the browser-SSE layer, NOT this
(model-API-side) layer — don't conflate the two stream-death families.

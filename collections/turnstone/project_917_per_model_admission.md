---
name: project_917_per_model_admission
description: "#917 per-model max_concurrency admission design: gate off ModelRegistry keyed by base_url alone; a thread blocks only for its first slot (nested perception)."
metadata: 
  node_type: memory
  type: project
  modified: 2026-08-05T15:52:16.041Z
---

# #917 — per-model `max_concurrency` (client-side admission)

Design written 2026-08-05 → `docs/design/917-per-model-admission.md` (local-only).
Field-report arc: #916 web_search · **#917** · #918 coordinator fan-out · #919 roles map · #920 tuning guide.

## Two traps the map exposed (the load-bearing findings)

1. **The console passes `health_registry=None`** (`console/session_factory.py`),
   so coordinator sessions have no health tracking today. Any new per-endpoint
   object threaded in as a `ChatSession` kwarg repeats that gap and leaves the
   biggest fan-in source ungated. ⇒ **hang admission off `ModelRegistry`**, which
   every process and every session already carries. Never off `app.state`.
2. **Nested dispatch happens INSIDE stream creation.** `_try_stream` passes
   `resolve_attachments=` into `create_streaming`; the provider invokes it during
   translation, and it can reach `_perception_fallback_part → model_turn` and
   `_audio_fallback_part → chat.completions.create`. With `perception.model_alias`
   on the same endpoint (the normal single-box self-host), a naive gate
   self-deadlocks at cap 1 on the first image. ⇒ invariant: **a thread may block
   for its first slot only** — a thread already holding any slot is admitted to
   any gate instantly without consuming one. Kills hold-and-wait cycles by
   construction; over-admits by nesting depth (bounded at 1, logged).

## Rulings baked into the design

- **Key = normalized `base_url` alone**, NOT `(provider, base_url)` like
  `HealthTrackerRegistry`. Slots belong to the server, not the dialect — vLLM
  serves `/v1/chat/completions` and `/v1/messages` from the same slots and
  Turnstone models those as two providers. `provider.provider_name` is ambiguous
  anyway (openai-compatible+responses reports `"openai"`).
- **Min positive cap wins** among aliases sharing an endpoint; warn on disagreement.
- **One wire attempt = one slot**; released across every backoff sleep. SDK's own
  `max_retries=2` runs inside a slot (it is the only layer honoring `Retry-After`).
- **Unbounded wait by default**, cancel-aware, with a stall WARNING — copying
  `watch.py`'s restore admission (stamps used ONLY to alert). A default bound
  reintroduces the "your number is wrong" tuning the issue is retiring.
- **Dispatch-anchored deadline**: `StreamAbortRef.mark_dispatch()` +
  `run_with_deadline` recomputing `origin + timeout`; the gate probes
  `getattr(cancel_ref, "mark_dispatch", None)`. Only the deadline-daemon callers
  (judge, output_guard_judge) need it — the SDK read clock already starts post-admission.
- **Retry layering: change nothing yet** (§3.9). Admission changes pressure, not
  policy; measure first. Pinning SDK `max_retries=0` would lose `Retry-After`.

## Dataflow-map round (2026-08-05) — verified second-order edges

- **A new `ModelConfig` field is NOT inert.** It joins the dataclass `__eq__`, and
  `_bind_model_from_registry` computes `binding_changed` partly as
  `cfg != self._bound_model_cfg` (session.py:3150) — a changed binding DROPS BOTH
  JUDGES and refills every live session's output-guard `TokenBucket`. So an admin
  editing an admission/telemetry-only field resets the guard on every bound
  session. Fix: `field(compare=False)`. **Applies to every future ModelConfig
  field**; the default is the unsafe one.
- **→ FILED #973** (the umbrella): `model_turn` owns transport but not its
  INVARIANTS. Its docstring's "Policy-free … those belong to each caller" is
  already false twice (`_DRAIN_RETRIES`, and #972's cancellation). Frame that
  earns its keep: **invariants** (no caller may opt out — don't dispatch when
  aborted, segregate reasoning, stamp provenance, respect admission) belong at
  the seam; **choices** (retry counts, deadlines, result handling) stay with
  callers. Every bug in the family (#965, #972, #964, #917's two-chokepoint
  problem) is an invariant that was treated as a choice. ~7 live seams: table in
  the issue. Sequenced AFTER #832 — before it, a seam-owned invariant needs two
  implementations, which is why #972 landed +141/−3 with zero deletions.
  Acceptance test for each PR in the series: **an empty deletion set means the
  PR is premature.**
- **→ FILED #972** (prerequisite, not a rider): `model_turn` checks
  `cancel_ref.aborted` before a RE-issue but never before its FIRST dispatch, so
  an abandoned judge/guard call already dispatches today. #965-shaped
  mis-located semantic — `_try_stream` has the rule (`_check_cancelled` per
  attempt, session.py:5992), the shared seam doesn't. Three spellings of one
  predicate exist (`_check_cancelled` ≡ `_CancelRef.aborted` ≡ `append`'s
  inline check); converging them is #832's, deliberately NOT bundled.
- **Site B has no cancellation channel**: `model_turn` has no `cancel_event` param
  and `ModelLane` no such field. The one shared signal is
  `getattr(cancel_ref, "aborted", False)` — `_CancelRef.aborted` (session.py:378)
  = `cancel_event.is_set() or _superseded()`; `StreamAbortRef.aborted` set by
  `on_abandon` (covers deadline AND cancel). Poll it in any wait, or an abandoned
  deadline worker is admitted later and dispatches a request nobody reads.
- **Never route a self-inflicted refusal as backend health**:
  `_create_stream_with_retry`'s `except Exception` (session.py:5861) calls
  `tracker.record_failure()` then walks fallbacks — which can share the same
  endpoint. Anything self-inflicted needs `BackendAuthUnavailableError`'s
  fail-closed arm at :5857.
- **`on_info` is NOT auxiliary-thread-safe.** Only `on_aux_usage` and `on_rename`
  are documented so (session.py:6816-6822). Any UI notice from title-gen / judge /
  guard / deadline threads is outside contract — default silent, opt in per call.
- **Deadline re-anchoring must CREDIT the wait, not reset the clock** — a reset
  composes badly with per-attempt re-acquire (turns a 30s budget into ~90s).
  Credit gives the stateable bound `timeout + Σ(queue waits)`.
- Provider adapters' `create_streaming` are eager and non-generator, and call
  `materialize_attachments` as their FIRST statement (`_anthropic.py:907` vs
  `client.messages.stream` at `:929`) — the perception nesting provably happens
  inside any held region.
- Open, not closable statically: a released slot is not a closed socket (the
  provider generator can be dropped before first `next()` on three unwind paths).

## Verified facts (2026-08-05, main @ 1d7db733)

- Nothing bounds LLM concurrency anywhere. SDK defaults: `max_retries=2`,
  `Timeout(connect=5, read/write/pool=600)`, `max_connections=1000`.
- **Two streaming chokepoints**, not one: `session._try_stream` still bypasses
  `model_turn` (#832 open). Site A needs an explicit ticket threaded between
  `_stream_response` and `_try_stream` (create and drain live in different frames).
- Retry multiplication is 36 wire attempts on both the main loop and the
  `model_turn` ladders (+ the fallback walk).
- The reranker IS a model definition (`tools.reranker_alias`, `supports_rerank`)
  but dispatches via bare `httpx.post` — needs the gate handed in at construction.

Related: [[project_model_definitions]] · [[project_architecture_map]] ·
[[project_selfhost_latency_arc]] (admission > timeouts) · [[feedback_minimal_scope_first]]

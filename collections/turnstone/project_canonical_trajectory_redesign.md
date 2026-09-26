---
name: project_canonical_trajectory_redesign
description: "Touching trajectory, wire-shape, or storage code: Turn refactor SHIPPED v1.6.0 (PR #638); lowering.py owns fold+repair, session.py owns zero wire-shape."
metadata:
  node_type: memory
  type: project
---

**STATUS: SHIPPED.** The whole stack (P1/P2 gates, storage cut, Turn-wiring, lowering,
AttachmentRef a+b, dead-column drop, per-kind meta delivery, migration 060, dict-native
wire-prep perf pass) merged to main via **PR #638 (2026-06-04)** and ships in **v1.6.0**.
User production-smoked the cluster pre-merge: large unexpected perf win (dict-native
wire-prep + `asyncio.to_thread` event-loop offloads). Living design doc (local-only):
`docs/design/canonical-trajectory-ideal-target.md`. Per-commit history lives in git
(`975fb47..1629439` on main); this memory keeps the durable architecture + lessons.

## Architecture (durable — consult before touching trajectory/wire/storage code)

- **Narrow waist = provider-NEUTRAL flat `Turn`** (`core/trajectory.py`): wide flat
  role-discriminated dataclass (NOT a role union — passes are role state machines);
  `content` = uniform `tuple[ContentBlock,...]` + `.text` property (FTS = projection of
  `.text`); `is_error` typed top-level; `ToolCall.arguments` = raw JSON str; old `_`-keys
  became typed fields (`_source`→source, `_provider_content`+`_producer`→native,
  `_event_id`→meta.event_id); `developer`→system collapse. `session.messages` is
  `list[Turn]` — carries IDs, never bytes.
- **`lowering.py` sibling module** (owned by neither session nor provider) owns BOTH wire
  passes: A fold (representation) + B repair (validity); `_prepare_wire_messages` composes
  fold→drop-empty-user→repair. **C (format) = thin per-provider translators — do NOT
  unify C.** `session.py` owns ZERO wire-shape. Providers consume the lowered **dict
  projection**, not Turns (translators keep dict input; vLLM-reasoning-attach is a
  non-canonical wire key between lowering and provider). This IS a **compiler backend** ([[project_harness_compiler_dialect_stack]]): neutral `Turn` = IR, fold/repair = deterministic **legalizer** passes, the C-translators = **codegen**; the `native` lane is the IR **'leak'** mined by #699.
- **Producer-tagged opaque `native` lane** (reasoning + server-tools + future blocks),
  rule `producer==active ? verbatim : rebuild-from-neutral`. SHIPPED REALITY: no provider
  reads the producer tag at wire time — the gate is each translator's block-type allowlist
  (`ANTHROPIC_VALID_BLOCK_TYPES`; OpenAI-Responses replays only its own reasoning items);
  "rebuild" is emergent type-filtering. Works; don't "fix" it without a reason. Producer
  tag is storage/reconstruct/display/migration truth. Backfill-inference is FIELD-aware
  (Google writes `thought_signature` inside `type:function` blocks; xAI is byte-identical
  to OpenAI → defaults `openai`, bounded legacy loss).
- **Placement = POSITIONAL** (referential `attaches_to` REJECTED — correct under
  compaction [in-memory-only] and rewind/retry [truncate at user boundaries]).
- **Repair = ONE pure detector (`_find_orphaned_tool_calls`, reads `tool_calls` only —
  sound via P1) + THREE policies:** strip-and-discard@load (`recover_trajectory`,
  trailing-strip ONLY = boot-crash recovery), synth-and-persist@runtime-cancel,
  synth-transient@send (`repair_wire_messages`, last step before translate).
  `CANCELLED_TOOL_RESULT` lives only in lowering. `export.py` runs repair itself before
  sanitize. One SCOPED synth survives in `sanitize_messages` for `id_remap`-backfilled
  empty-id orphans (local servers omit tool-call ids — id-less calls are invisible to
  the detector).
- **P1 save-time chokepoint** (`storage/_utils.normalize_native_for_save`, both save
  paths): assistant rows with empty `tool_calls` get client `tool_use` blocks stripped
  from native (reasoning/server-tools kept) → "`tool_calls` mirrors native client
  `tool_use`" holds BY CONSTRUCTION. A load-side strip (`strip_orphan_client_tool_blocks`
  when `tool_calls` empty) self-heals LEGACY rows — closes both the Anthropic resume-400
  AND a Google twin (`_google.py` resurrected `function` blocks from provider_data).
- **P2 equivalence net**: `tests/test_wire_payload_golden.py` — per-provider
  byte-identical wire-payload golden harness; stayed byte-identical through the whole
  refactor. THE guard for any future wire-pipeline change (e.g. it gates the dict-native
  wire-prep optimization).
- **AttachmentRef by-reference**: `ContentBlock = TextBlock | AttachmentRef(id,kind)`.
  Providers take a `resolve_attachments` callback; `materialize_attachments` substitutes
  inline parts up front; `_full_messages` emits placeholders `{type:"image"|"document",
  attachment_id}`. A resolved inline part is TERMINAL — `turn_from_dict` silently DROPS a
  stray inline `image_url` without attachment_id (**fixture gotcha**: multipart fixtures
  MUST use `{type:image, attachment_id}`). Storage: content-addressed (hash-keyed, global,
  INSERT-OR-IGNORE dedupe) + refcounted `workstream_attachments`; `conversations.
  attachments` ref-list is the SOLE link; GC = refcount, prune at 0. Tool images by-ref
  **new-turns-only** (legacy tool images were flattened-to-text on save — bytes
  unrecoverable; legacy user uploads DID persist and ARE migrated). Upload buffer =
  intern-and-ref (content-address bytes once + per-(ws,user) refs, single lock).
- **`tool_name` column KEPT** (user decision) — NOT dead: `search_history` returns it and
  recall/`/history` label tool rows; wire path ignores it. Dropping = pure UX regression.

## Migration 060 (shipped) + the validation pattern

Additive, histories KEPT (data-loss option rejected — bought only ~20 lines). Absorbs:
is_error, provider `{producer,blocks}` envelope + field-aware backfill, content-addressed
attachment re-key/dedupe/ref-list, dead ws_id/user_id drop, `conversations.meta` JSON col.
Backfills are PAGED (review caught an un-paged `.fetchall()` of all blob bytes → OOM).
**Validation pattern (reusable):** dump prod → restore to a TEMP db → alembic env from
explicit Config url (never `TURNSTONE_DB_URL`) + script guard refusing non-temp DBs →
upgrade → sanity → downgrade → drop temp. Re-run validation if the migration file changes
after validating (it changed twice post-validation here). Live DB stayed at 059 throughout
dev. **DEPLOYED to the live cluster with the 1.6.0 rollout — confirmed 2026-06-11: mostly
smooth, ~98% of data transferred clean; minor loss confined to the known-unrecoverable
areas (legacy flattened tool images, un-inferable producer blobs).**

## Lessons (transferable)

- `Any`-typed session consumers are a mypy BLIND SPOT — grep `session.messages` dict-access
  in non-session prod code (server/console/eval) separately when changing message shape.
- Full-branch pre-push `/review` (subsystem slices × 4 finders, [[feedback_large_review_orchestration]])
  caught integration-seam regressions per-commit reviews missed (retry-walk class miss;
  legacy-orphan 400). Worth it even when every commit was reviewed.
- Brief-grounding CORRECTED the continuation brief in 5 places (file conventions like
  `asyncio.to_thread` vs `run_in_threadpool`; a Google twin of the "anthropic-only" bug;
  intern-and-ref over re-key) — ground briefs in code before applying, never blind-apply.

## Open follow-ups (still live as of 2026-06-11)

- **Metacog `start` nudge double-render — RESOLVED on main** (verified 2026-06-11 with
  a negative-control headless harness): `21af6c4` aligned the persisted system-turn
  row's event_id with its SSE event; `09e41d1` added bidirectional
  `renderedSystemEventIds` dedupe in BOTH panes. Real vector was the resume-cursor
  overlap on the *interactive* pane (children open as interactive panes), not the coord
  pane; legacy no-id rows deliberately render-both. Pin tests tightened to wiring-level
  in PR #655 (old pins were file-global symbol checks — a neutered guard passed them).
- **Q4 server-tool→text projection DEFERRED**: cross-provider resume drops a foreign
  producer's server-tool RESULT blocks (text synthesis survives = graceful degradation).
  Needs new machinery (producer-vs-active hook + per-provider `project_native_to_text`). (now folded into the **output-alignment epic #689** / native-IR #699 — the foreign-producer projection is exactly that best-effort re-encode).
- **~12 orphan `ws_id` conversation rows** — root cause FOUND 2026-06-11 (forensics
  sweep): `save_message` never checks workstream existence, so any late writer
  resurrects rows post-delete. The May-11 case fully solved via audit trail
  (delete-during-inflight-execution race); April/May-24 clusters are era-bound/
  unaudited but attributed to the same root-cause class. Cleanup verb shipped
  (`turnstone-admin orphan-conversations [--delete --yes]`); live-cluster run still
  user-gated.

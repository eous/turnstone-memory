---
name: project_replay_identity_ir_origin
description: "Replay identity in the Turn IR (09-25): replace producer=provider_name with a binding-derived origin; both design challenges said adopt with changes; minimal scope."
metadata:
  node_type: memory
  type: project
  modified: 2026-09-26T04:56:49.190Z
---

Came out of the #1201 review ([[project_1201_deepseek_responses_reasoning_replay]]) and #1213.
Today `ProviderNative.producer` (trajectory.py) = `lane_producer(lane)` = adapter `provider_name`;
Responses filters by string equality, Anthropic and Google by block shape, Chat Completions discards
native content (`sanitize_messages`), accounting compares `replay_family`.

Proposal (mine, 09-25): structured origin from the lane binding, one replay relation in lowering,
same relation for the charge, legacy stamps preserved. Challenged with one neutral prompt
(scratchpad `ir-origin-challenge-prompt.md`) by codex (`gpt-6-astra`, read-only) and a Fable agent.

**Both: adopt with changes.** Agreed corrections to my premises: `TurnProvenance` deliberately
excludes endpoint and credential (trajectory.py ~116-127), so endpoint identity is NEW data captured
at stamp time; Chat Completions replays nothing. Agreed changes: keep adapter-owned validation and
share one predicate (replay + charge) instead of centralizing codecs in lowering; no credential /
principal / registry-generation axis (rotation or OBO changes would flip keep to drop: prefix
breaks, cache breaks); not a prerequisite for #1202 or a behavior-preserving #1213; must land before
#1214's backend hops; gateway multiplexing is unsolvable client-side. Disagreement: Fable keeps the
string envelope (`family:surface:normalized-endpoint`, downgrade-safe); codex wants versioned
compatibility domains with explicit sharing (endpoint equality is an unreliable proxy; it cites
Anthropic docs on signature portability across platforms, not verified by me).

**Pins it touches (verified), triaged per the IR-refactor rule, not vetoes:** Responses
producer scoping with legacy fallback (`test_native_metadata_is_scoped_to_producer_with_legacy_fallback`):
the contracts (foreign native metadata not replayed; untagged legacy blocks keep shape-based
replay) survive, only the `"openai"` string-equality mechanism is rewritten. Anthropic cross-name
replay + family charge (the maintainer's 09-19 ruling, `docs/design/1188-native-lane-charge.md`):
the invariant "charge matches what is replayed" is kept by construction by the shared predicate; the
family-name compare is mechanism. Whether Anthropic joins the new identity rests on measurement
(no cross-endpoint 400 measured; codex's portability claim unverified), not on the pins. Only
measured harm is on the Responses lane. Also: the
endpoint part must be hashed or scrubbed, since `_producer` already leaves via the coordinator
serializer and `/history` does not scrub it (Fable).

**Recommended minimal scope:** Responses lane only; binding-derived string stamp with an explicit
legacy/untagged ruling; same predicate for the charge; Anthropic untouched unless a cross-endpoint
400 is measured. **Round 2 (09-25, re-run on #1213 as filed, pointed at docs/design + tests + live GitHub):** codex
265k tokens, Fable 314k / 66 tools / ~21 min; both adopt-with-named-changes again (4 of 4). Converged:
capture the identity on ALL lanes now and enforce per lane (else another unscoped legacy cohort);
versioned identity; split replay identity from the ledger/display producer (`persist_producer` and
the compaction marker's `summary_producer`, pinned by
`test_compaction_summary_producer_survives_storage_round_trip`); endpoint is evidence, not authority
(regional/LB hosts false-drop, gateways false-keep; record the visible model/route too; operator-
declared replay domain; one URL canonicalizer shared with `_same_endpoint` and the health key);
a per-turn replay plan with reject/convert, not bare keep/drop; legacy frozen as a closed set, no
re-stamp, never infer endpoints; only the coordinator serializer leaks `_producer` (`/history`
never copies it; my #1213 claim, taken from round-1 Fable, was wrong); hashing is not
confidentiality. Split: on-disk shape — Fable a versioned string in `producer` (downgrade degrades
safely; a dict would TypeError in `replay_family` on old builds), codex a versioned `origin` beside
the legacy `producer` (old readers keep today's behavior; resave on an old build loses it, needs a
minimum-reader gate). codex confirmed Claude signature portability (Claude API/Bedrock/Vertex) from
the docs; Fable could not.

**Round 3 (09-25, on the per-block fact-mask + reasoning-kind-enum + no-legacy proposal):** codex
REWORK (235k tokens), Fable adopt-with-named-changes. Both reject: persisted per-block masks (the
traits are already in the block bytes — signature / encrypted_content / thought_signature / type —
and a stored copy must stay aligned across ~6 block-list rewriters: strip_orphan,
normalize_native_for_save, finalize_provider_blocks, backfill_blank_native_tool_ids, truncation
carry, fork/clone re-wrap); vendor/model-family reasoning-kind enums (a new member per model launch;
use traits + model identity as data from provenance); "active tool round" as a stored fact; blanket
no-legacy (codex: keep legacy DECODING/preservation, drop permissive replay; Fable: migration
backfill, runtime branches deleted — but its backfill infers endpoints from current alias config,
which codex rejected in r1/r2). Both: additive envelope keys give neither enforcement nor lossless
downgrade (old reader replays; fork re-wrap drops unknown fields — verified), so a minimum-reader
boundary is required; decisions must be dependency-aware (a Messages lane falls back to whole-lane
rebuild if any client tool_use is dropped); "plaintext present" ≠ faithful (summary-only block
already reaches vLLM as reasoning); no shared URL canonicalizer exists today. Converging shape: a
per-LANE readable versioned origin record + adapter-derived per-block traits at lowering +
dependency-aware replay plan; measure cross-endpoint rejection before any policy beyond the
measured row-move harm.

**State 2026-09-26:** the converged direction (per-lane readable origin record, traits derived at
lowering, dependency-aware replay plan, storage-normalizing migration + unknown-origin policy,
minimum-reader boundary, measure first) is PUSHED to #1213. Pick up from
`docs/design/1213-replay-identity/README.md` (handoff + all prompts, reports, the #1201 review).

**Filed into #1213 (the maintainer's call, 09-25)** as the "Replay identity (independent
of steps 1–5)" and "Test triage" sections; the compat `provider_name` open question there is now
dispatch/ledger-only.

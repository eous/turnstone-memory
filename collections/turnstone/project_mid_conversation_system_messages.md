---
name: project_mid_conversation_system_messages
description: "Mid-conversation role=system turns / core/fence.py: SHIPPED v1.6.0 (PR #638); native on the current Claude rows (flag per row), others get the bracketed nonce-fenced fold (PR #726)."
metadata:
  node_type: memory
  type: project
---

**STATUS: SHIPPED in v1.6.0** (merged via PR #638, 2026-06-04). Original consolidation
`119809c9` (net −1662 LOC) + hardening round + Full-B meta delivery (`68dc301a` /
`164f74d` "deliver structured per-kind meta to the UI"). The old "dangling meta" gap is
CLOSED. Migration 060 (incl. the `_reminders` column DROP + `conversations.meta` col)
shipped with [[project_canonical_trajectory_redesign]].

**UPDATE 2026-06-26 (PR #726):** the fold marker was reshaped from
`<system-reminder_{nonce}>` XML to **`[start system-reminder_{nonce}]…[end
system-reminder_{nonce}]`** (bracketed start/end keywords, slash-free) — angle
brackets pushed rigid structural-token chat templates (some local models) out of
distribution after a couple of folded reminders accumulated. Single-sourced in
`core/fence.py` (`_OPEN_KW`/`_CLOSE_KW` + new `detection_pattern`) so
`wrap`/`neutralize`/the forgery detector/both trust declarations track one shape;
nonce still on both boundaries, leak-vs-forgery split + forge-in/break-out defang
preserved; the same reshape was applied to the judge's `tool_output` fence
[[project_envelope_nonce_tags]]. Wire-only, no migration. The `<…>`-form marker
mentions below are the OLD shape.

**UPDATE 2026-09-28 (#1227):** the native set grew with each new Claude row (see "The
provider feature" below). On the fold path, an operator turn that follows tool results is
appended to the last tool message, so the Anthropic converter carries it *inside* that
`tool_result` block (verified by probing `fold_system_turns` + `_convert_messages`). The
Sonnet 5.5 prompting guide ("Mid-turn user messages") says user text inside a
`tool_result` block is the placement the model most often takes for injected text; a
`system` message right after the tool results can draw the same reading. Its recommended
shape for mid-turn user input, a user-turn text block after the last `tool_result`, is not
implemented. Maintainer ruling: a row whose model accepts mid-conversation system messages
sets the flag, as the other current rows do; the native path has run without trouble there.

## The provider feature (durable API facts)

Anthropic **mid-conversation system messages**: append `{"role":"system"}` into the
`messages` array (not the top-level `system` field) for operator-priority instructions
without invalidating the cached prefix. Claude API + Claude-on-AWS only (NOT
Bedrock/Vertex/Foundry; platform list as of 2026-06), no beta header. Models: shipped
for claude-opus-4-8 alone; per the API docs (2026-09-28) Fable 5/5.1, Mythos 5/5.1,
Opus 5/5.5 and Sonnet 5.5 accept it too, while Sonnet 5 and older models do not.
Placement rules: must follow a `user` turn (incl. tool_result-bearing) or an assistant
turn ending in server tool use; must precede an `assistant` turn or end the array; NOT
first; NOT consecutive (merge); never between a `tool_use` block and its `tool_result`.

`supports_mid_conversation_system` capability flag is True on the fable-5, fable-5-1,
opus-4-8, opus-5 and opus-5-5 rows (sonnet-5-5 with #1227) — NOT OpenAI/xAI (Chat
Completions *accepts* mid-array system but priority is undefined; acceptance ≠ operator
priority), NOT Google (`system_instruction` top-level-only). Default False = safe
fallback for non-Anthropic lanes. Mirrors `supports_reasoning_replay` conservatism.

## What exists now (the shipped design)

- **ONE persistent shape**: advisories/nudges/interjections/skill-hints are first-class
  `{role:"system", _source:<kind>}` turns in `session.messages` (12 kinds in
  `SYSTEM_TURN_SOURCES`). Killed: `_reminders` one-shot splice, the persisted
  `<tool_output>`/`<system-reminder>` content envelope, `escape_wrapper_tags`.
  Nudges are standing history, not one-shot (cooldown bounds accumulation).
- **Wire = one fold-or-keep pass** in lowering: native rows keep inline (Anthropic
  converter is position-aware: leading system → top-level param, mid → inline, coalesce,
  placement rules); everyone else folds into the preceding turn fenced as
  `[start system-reminder_{nonce}]…[end …]` (reshaped — see UPDATE above).
  `_drop_empty_user_turns` runs AFTER the fold (a fold-path
  wake turn filled by a nudge survives; a native empty wake turn drops); `_anthropic` has
  an `and converted` guard so a turn converting to nothing can't make a system message
  `messages[0]`.
- **`core/fence.py` = THE shared fence primitive** (`mint_nonce` 64-bit, `neutralize`,
  `wrap`): operator fold + output-guard judge share the mechanism but deliberately differ
  in nonce *lifecycle* — the session nonce is per-session because the cached-prefix
  declaration pins the exact value (per-turn rotation would bust the cache). The fold
  `_neutralize_host`s ONCE before first fold (defangs forged markers in untrusted host
  text); `fence.wrap` defangs body close-tags.
- **Forgery detection** (`output_guard._check_marker_forgery`, fed
  `trusted_marker_nonce=self._envelope_nonce`): exact session nonce appearing in tool
  output → HIGH `operator_marker_leak`; any other fence marker → LOW forgery. Detection
  ≠ control — escaping neutralizes, this warns. Phase-2 hardening candidate:
  [[project_envelope_nonce_tags]].
- **user_interjection** keeps USER (not operator) authority via
  `render_user_interjection` (important→"You MUST address this", notice→"incorporate if
  relevant"); empty interjections dropped at drain.
- **Per-kind structured meta (Full B)**: each producer builds ONE `_source_meta` dict and
  derives BOTH the model-facing `content` AND the UI card from it (can't drift) →
  `Turn.meta.extra["source_meta"]` → persisted `conversations.meta` JSON col → live
  `on_system_turn(content, source, meta)` (4 impls + SSE) → `project_history_messages`
  → FE. **4 cards** in both UIs (live + replay, all `textContent`-safe): watch-result
  (body = `meta.output`), output-guard finding, idle_children list, user_interjection.
  Static nudges + skill_hint stay labeled text. Wire stayed byte-identical (meta is
  `_`-prefixed → sanitized off). Legacy pre-meta turns reload as plain text bubbles —
  structured fields unrecoverable from flattened content, accepted.

## Caveats that outlive the ship

- **This was NOT the cache fix**: the dominant Anthropic cache-miss cause is the volatile
  recalled-memory block baked into the system prefix (reranked against a moving last-3-
  user-messages query); reminder churn was the smallest contributor. The real lever —
  moving the memory block out of the frozen prefix to a per-turn tail system message —
  is the deferred tail-injection redesign in [[project_memory_relevance_pipeline]],
  enabled by this same native feature.
- `reconstruct` had a hard 3-role switch that silently dropped role=system on load — if a
  new role ever appears, check `reconstruct_turns` AND both FE replay paths for the same
  drop pattern.
- Relates: [[project_smart_approvals]] (auto-approve toggle is a future producer),
  [[project_early_paint_tool_calls]], [[project_system_message_composition]].

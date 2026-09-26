---
name: project-multiuser-attribution-ux
description: "Multi-user attribution UX #998 (after user icons #997): tool-row attribution is a server-side projection-time derivation; never weaken the scrub pins."
metadata: 
  node_type: memory
  type: project
  modified: 2026-08-11T01:32:47.688Z
---

The maintainer (2026-08-10): multi-user shared workstreams — several people on different
browsers/accounts driving ONE workstream — are quickly becoming a niche
Turnstone owns. A follow-up session will add user-facing UX showing who is
responsible for what (user principal attribution). This was a stated reason the
#964/#981-era identity work was prioritized.

**Data foundation already durable (fix/981-history-commit-handoff branch):**
- Assistant turns: four-axis `TurnProvenance` (model_alias, backend_model_id,
  registry_generation, acting_principal_id) under `PROVENANCE_META_KEY` in
  `conversations.meta`. Scrubbed from every public payload.
- User turns: authoring principal as meta `sender` (authenticated id, not a
  label); synthetic turns (wake/advisory/compaction) deliberately unstamped.
  Surfaced to panes: `user_turn` events + history projection carry sender;
  panes render viewer-relative ("you" vs sender) via the shared
  `acceptUserTurnEvent`/`viewerUserId` reducer in composer_queue.js.
- Tool rows: `acting_principal` meta key (execution context, not authorship;
  omitted when empty) — added by follow-up agent same day; deliberately NEVER
  reaches the wire.
- Enforcement pairs with recording: cross-user interjection fails closed
  (empty-principal turns reject authenticated interjectors), 409
  `cross_user_interjection` surfaced with plain-language copy; `state_change`
  events carry `acting_user_id`; `client_send_ids` are correlation-only, never
  identity.

**The UX itself is FILED as #998** with two the maintainer-set requirements
(08-10): dormant by default — attribution chrome activates LIVE only when a
second distinct principal joins (recommend attach-based join, since typing
needs presence of not-yet-senders; deactivation follows the existing
rewind/known-senders reset semantic) — and a typing indicator/broadcast.
Typing events MUST be ring-exempt id-less ephemera (event-id space = accepted
row cursor space; presence chatter in it would churn replay/resync), short
server TTL, auth-scoped to participants.

**RULED (08-10, the maintainer + Claude): tool-row attribution derives at projection
time.** The tool-row `acting_principal` audit key deliberately has NO dict
bridge (structurally unleakable; turn_to_dict emits nothing). #998's display
projection must NOT add one: derive tool-row `attributed_to` server-side from
the in-window assistant's `_provenance` (same principal by construction —
pinned by test_tool_rows_record_the_same_principal_as_their_assistant_turn),
carried forward batch-wise like the occurrence scan. Head-of-window orphan
tool rows stay unattributed (same accepted artifact class as the is_error
orphan fallback). Escape hatch if per-row sourcing is ever needed: bridge +
scrub + projection as one deliberate change with pin renegotiation.

**The contract decision that session must make first:** user-turn sender is
public-projected, but assistant/tool principals are audit-only by deliberate
ruling (scrub pins exist). Attribution UX for "who asked for this output /
whose credentials ran this tool" needs a server-side DISPLAY projection
(e.g. a derived `attributed_to` field) rather than exposing the raw audit
keys — do not weaken the scrub pins to get the UX. SDK types will need the
new display fields.

**Pre-work session FIRST (the maintainer 08-10): user icon system — FILED as #997.**
OIDC/OAuth profile icons when enabled+available, plus a local-only /
local-override icon system; the attribution UX then consumes icons in the
chat interface.
Grounded starting state: `OIDCIdentity` (storage/_protocol.py:132) has NO
picture claim today (issuer/subject/user_id/email/created/last_login/oid/tid) —
capture is greenfield. Likely scope: persist+refresh the `picture` claim at
login; local avatar store with override precedence (local override > OIDC >
deterministic fallback initials/identicon so user→icon is total); ONE
authenticated serving endpoint ([[feedback_everything_needs_auth]]) with
ETag/caching. Decisions for that session: override precedence semantics, and
proxy-cache vs hotlink IdP picture URLs — hotlinking leaks viewer IPs to the
IdP and breaks on token-gated URLs, so local proxy-cache is the likely call.

Related: [[project_pr750_multiuser_context_review]] (1.7 shared-context work),
[[feedback_operator_ui_plain_language]], [[feedback_chip_contrast]] (attribution
chips must meet the ≥0.15α floor), [[project_copy_affordances]].

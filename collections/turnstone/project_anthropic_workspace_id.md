---
name: project_anthropic_workspace_id
description: "Anthropic workspace scoping per model definition (09-13): server_compat key + client default header, header-bound validation, provider gating, judge client rebuild."
metadata: 
  node_type: memory
  type: project
  modified: 2026-09-13T05:18:18.631Z
---

**Built 2026-09-13 on `feat/anthropic-workspace-id` (stacked on `fix/1050-anthropic-sdk-v1`).**
**Folded 09-13: the feature commits were fast-forwarded onto `fix/1050-anthropic-sdk-v1`
(three linear commits: migration, workspace scoping, console fixes); ON DEV since 09-13 via PR #1161
(rebase-merged; branch auto-deleted). Harness gap filed as #1160 (schedule livepass states).**
Trigger: the maintainer's org-level key got `400 ... must include the anthropic-workspace-id header`
during the #1050 live smoke. The maintainer asked for the workspace scope to be added to both the
Anthropic provider's model UX and the backend right away.

**Design (facts):**
- Stored as `capabilities.server_compat.anthropic_workspace_id` — an ENDPOINT property like
  `api_surface`; no migration, no API-schema change, round-trips DB / admin API / config.toml
  (`[models.x.capabilities.server_compat]`) / node projection for free. Console editor: structured
  field `model-anthropic-workspace-id` (row hidden unless provider is anthropic /
  anthropic-compatible), same lift-then-restore pattern as api_surface; NOTE the editor rebuilds
  `server_compat` from structured fields on save, so unknown server_compat keys are dropped
  (pre-existing).
- Wire: `create_client(..., workspace_id=)` pins `default_headers={"anthropic-workspace-id": ..}`.
  VERIFIED anthropic 1.5: the SDK lists it in `_CLIENT_LEVEL_HEADER_PARAMS`; a default header
  survives `with_options(api_key=...)` copies and reaches messages.create/stream + models.list.
  Per-request `workspace_id=` on Messages calls maps to the same header (override, unused).
- Validation is ONE rule in two layers (like MODEL_AUTH_TEXT_MAX_LEN): `anthropic_workspace_id_error`
  = visible ASCII 0x21-0x7E, ≤128 (`ANTHROPIC_WORKSPACE_ID_MAX_LEN`). Console refuses on
  create/update/detect; registry refuses at load (`ModelAuthConfigError`, authoritative). VERIFIED:
  httpx2 MockTransport does NOT validate header values (newline accepted) — never rely on the transport.
- Provider gate: `ANTHROPIC_PROTOCOL_PROVIDERS = {anthropic, anthropic-compatible}` (model_registry).
  Console refuses the key on other providers, including a provider-only PUT that would strand a stored
  scope ("clear it before switching the provider"). Loader TOLERATES a stored scope on another provider:
  warn + drop (the obo "stale audience on a static row" precedent — an already-stored value must not make
  an alias unloadable).
- Reload identity: a scope change retires the cached client; auto-detect probe identity tuple and
  `_same_endpoint` (detected-window carry-over) include the scope — two aliases differing only by
  workspace never share a probe or a carried window (the maintainer's reviewer reproduced 65536 vs 8192 mixing).
- Judges: IntentJudge and OutputGuardJudge rebuild their own SDK client from the lane client
  (`_extract_client_config`); they now read the ONE workspace header off `client.default_headers`
  (never the map — it also carries x-api-key) and pass `workspace_id`. Without this every judge call
  on a scoped alias 400s and the LLM tier silently degrades to heuristics.
- Detect: body `anthropic_workspace_id` (schema field added to `DetectModelRequest`; artifact
  regenerated with `sdk/typescript/scripts/generate-types.py`), gated on provider. Masked key +
  definition_id falls back to the row's stored scope ONLY when the key is ABSENT from the body:
  the console always sends the field ("" for a cleared one) on Anthropic lanes so a cleared field
  probes unscoped, exactly as the following save will run (round-2 finding).
- Loader order: the provider gate (warn+drop) runs BEFORE the shape check, so a malformed scope on
  a non-Anthropic row cannot abort the whole registry load (round-2 finding).
- Tests that count: real SDK over httpx2 mock via `client.with_options(http_client=...)`; console API
  through TestClient+storage+registry; headless-Chrome livepass drive
  (`tests/test_livepass_workspace_id.py`: build harness, serve on loopback, `--dump-dom`, assert the
  stamped title). The maintainer rejected a string-presence "test" as vacuous — never add those.

**Design review (designer agent, 09-13, real Chrome via livepass):** fixed — provider switch
silently dropped a stored scope on save (now an `.sh-callout` warning `#model-workspace-drop-note`
shown when the row is hidden and the field has a value); `_showModelError` now delegates to
`_showModalError` (scrolls the alert into view — every model-save error was invisible at
scroll-bottom); `maxlength` REMOVED (silent paste truncation = valid-looking wrong id) in favour of
`_workspaceIdProblem` (client mirror of the server rule, on save + Detect, focuses the field);
server errors lead with "Workspace ID (json.path)"; field merged into the Max-concurrency
`.field-pair` (hidden inner div auto-places the sibling); hint "empty unless this key is
organization-wide"; `autocapitalize=none`; `workspace=` badge in the models list; Detect result
scrolls into view. The maintainer then asked for the pre-existing defects to be fixed as well
(09-13): `.label-hint` opacity .8 REMOVED (dark 4.02→5.47:1, light 6.16:1; case+letter-spacing keep
it distinct) and the narrow-pane `.field-pair, .capgrid {1fr}` collapse MOVED into a second
`@container pane (max-width: 700px)` block placed AFTER the base rules (a container query adds no
specificity; it had been dead code above them). CSS gate: audit report identical to base apart from
line numbers; 480px renders single-column in both themes. Designer GATE round 2 found two
consequences of the fix and they were resolved: (a) hints OUTSIDE a <label> (two <p> notes on the
MCP shelf, `#sklc-notify-hint`) had relied on the opacity as their only demotion → new
`.label-hint.hint-block` (11.5px, fg-dim, block) applied at those three markup sites; summary-line
hints inside `details.rawhatch` need nothing (11px ink-3 already); (b) the revived one-column
collapse left 0px between a toggle cell and the next label → `.sh-body .field-pair label:first-child
{margin-top:14px}` inside the narrow container query (wide render byte-identical). Also: `.autofill`
wraps as prose at narrow, `.capgrid` kept two-up (13 tiles one-up = long scroll), dead `opacity:1`
on `.skill-spec-heading .label-hint` removed, and livepass driver dispatch wrapped in try/catch so a
throwing driver stamps `OPEN-FAILED-<state>-<ErrorName>` (schedule-create/edit throw `TypeError` —
ScheduleBuilder undefined in the harness — pre-existing, now visible, not fixed).

**Not done / rulings:** doctor setup wizard and CLI/eval `--provider anthropic` paths take no
workspace id (out of scope). Detect's pre-existing body-base_url-with-stored-key path left as is
(admin.models can retarget via the edit path anyway). `anthropic-user-profile-id` not supported.

Related: [[project_1050_anthropic_sdk_v1]], [[feedback_sdk_boundary_testing]],
[[project_898_model_provider_obo]], [[feedback_operator_ui_plain_language]].

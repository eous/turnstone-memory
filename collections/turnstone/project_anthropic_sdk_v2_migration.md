---
name: project_anthropic_sdk_v2_migration
description: "anthropic SDK 2.x (= API version 2026-10-21) upgrade, branch chore/anthropic-sdk-v2 (2026-10-23): the rulings, the X-Api-Key parity design, live-verified facts, and the open Entra/Foundry follow-up."
metadata:
  node_type: memory
  type: project
  modified: 2026-10-23T13:27:43.227Z
---

anthropic 2.0.0 (2026-10-21) is the first release sending `anthropic-version: 2026-10-21`.
Upgraded on branch `chore/anthropic-sdk-v2` (lock 2.2.0; PR #1480) ahead of the 1.9 stable cut,
plus a direct `brotli>=1.2.1` floor (CVE-2026-111497). Anthropic clients holding an API key follow
no redirects (review finding).
Guide: https://platform.claude.com/docs/en/api/migration-2026-10-21

Maintainer rulings (2026-10-23): upgrade now; temperature and credentials follow the guide's best
practices; keep Entra/Azure deployments working if they need `x-api-key`. Foundry behavior could
not be verified live, and shipping it unverified was accepted, with a patch to follow if it
breaks.

Design as built:
- Hosted `anthropic` lane never sends temperature (gated on `self._compat`, so a definition's
  supports_temperature=True can't reintroduce it); five 4.5/4.6-era rows flipped to False. Live:
  without this, thinking requests to those rows 400 ("temperature: Extra inputs are not
  permitted") because the old code forced 1.0. server_compat pins are not refused locally.
- Every api_key-kind credential (stored, placeholder, or minted via with_options(api_key=)) keeps
  `X-Api-Key` through an httpx2 `auth=` hook (`send_api_key_as_x_api_key`); auth_token stays
  Bearer. Live-verified: hosted API accepts X-Api-Key on 2026-10-21.
- Env fallback passes at most one credential (ANTHROPIC_API_KEY first).

**Why parity, not Bearer for minted tokens:** Microsoft Foundry docs: keys in `x-api-key`, Entra
tokens in `Authorization: Bearer`. 1.x sent Entra tokens as x-api-key, so an Azure deployment
that works today keeps working with parity; Bearer could break a gateway reading x-api-key.
**How to apply:** if a deployment's Claude traffic goes straight to Foundry with Entra, the
follow-up is making the hook move only the client's construction key (minted tokens stay
Bearer). The compat lane (vLLM/LiteLLM) with 2026-10-21 + headers was not verified live. Related:
[[feedback_never_pin_temperature]], [[feedback_sdk_boundary_testing]],
[[feedback_operator_ui_plain_language]].

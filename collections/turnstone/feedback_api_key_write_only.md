---
name: API key write-only pattern
description: "Adding a secret field (model api_key, judge.api_key) to an API-managed entity: write-only; reads return ***, *** on update keeps it; no ?reveal=true."
type: feedback
---

API keys for model definitions (and other secrets like judge.api_key) should follow a write-only pattern:
- API writes allowed (POST/PUT accept the value)
- API reads always return "***" — no `?reveal=true` escape hatch
- "***" sentinel on update means "keep existing value" (prevents form roundtrip overwrites)

**Why:** More secure than MCP's reveal pattern (which exposes secrets to any admin with the right permission), while still enabling admin UI management (unlike the old is_secret pattern which blocked API writes entirely with 403).

**How to apply:** When adding new secret fields to API-managed entities, follow this pattern. Don't use `is_secret=True` on SettingDef (that was changed to also be write-only), and don't use MCP's `?reveal=true` approach.

A `secret://` reference stored in such a field is not a secret: reads return it verbatim, and
sending it back unchanged keeps it, like `***` ([[project_1329_secret_references]]).

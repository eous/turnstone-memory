---
name: feedback_runtime_toggles_settings_registry
description: "Adding an operator toggle or private-network guard to a tool: settings_registry.py, not config.toml; gate via tagged approval opt-in, never a hard block."
metadata: 
  node_type: memory
  type: feedback
---

Two corrections from the preview-pane branch (2026-07-07), same root:

1. **Runtime-behavioral toggles belong in `settings_registry.py`** (DB-backed `system_settings`,
   auto-rendered in console Settings by section, hot-readable via `self._config_store.get(key)`),
   NOT in config.toml getters. I built `[tools] allow_private_network` as a cached config.toml knob
   mirroring `[oidc] allow_private_network`; the user corrected that it belongs in the config
   registry, like the output-guard enable/disable setting, with the web UI attached. config.toml is
   for bootstrap/deploy-static things (DB, auth, binds — and oidc issuer config, which is
   pre-storage). Anything an operator flips while running goes in the registry.

2. **Don't hard-block private-network access in tools — this is the second time
   I've fought the user on it** (first when web_fetch was built). Turnstone's
   audience is home-lab self-hosters whose legitimate targets ARE private
   (Grafana, Home Assistant, dev nodes). The accepted shape:
   `tools.allow_private_network` (default off) makes NAMED private targets
   approvable with a "(private network)" tag on the approval card; the human
   gate stays. The one hard block that survives (user accepted the reasoning):
   a PUBLIC origin redirecting into private space is refused regardless — that
   address never reached the approval card (`fetch_with_ssrf_guard`'s
   `allow_private_origin` is set only for private-NAMED origins).

**Why:** the user prices security controls against their real deployment model
(self-hosted, operator-is-the-trust-boundary, approval gates as the control) —
absolute blocks that serve multi-tenant SaaS postures read as fighting the
product. **How to apply:** default to approval-gates + opt-ins + honest
tagging over hard refusals for operator-initiated capability; put the opt-in
where the operator lives (admin UI registry); make refusals name the knob
([[project_preview_pane]], oidc 9c74673f precedent).

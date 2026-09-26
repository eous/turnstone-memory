---
name: feedback-official-provider-paths-only
description: "New commercial LLM provider spike (OpenAI, xAI...): only the vendor's documented server-to-server API path; unofficial OAuth/cookie flows out of scope."
metadata: 
  node_type: memory
  type: feedback
---

When researching or proposing a new commercial-provider integration (OpenAI, Anthropic, Google, xAI,
etc.), restrict the design to the provider's officially-documented server-to-server path — typically
API key over HTTPS to a documented base URL. Don't propose end-user OAuth flows that exist only via
third-party reverse engineering, however convenient they look.

**Why:** Turnstone is an OSS platform with multi-tenant governance and audit requirements
([[project_design_constraints]]). Building on undocumented auth surfaces means the integration can
break silently when the provider rotates the flow, and it ties cluster-wide credentials to per-user
subscriber accounts — a categorical mismatch with the centralised `config.toml` credential model and
the audit trail. Maintainers also can't promise OSS users a flow the vendor hasn't blessed.

**How to apply:** During boundary spikes for new providers, note any unofficial auth surface as "out of scope" in one line and move on. Don't enumerate verification items, don't sketch the architecture, don't suggest it for Phase 2. If the user later asks "what about OAuth/cookie/etc.", point back to this rule. Exception: if the vendor *officially documents* an OAuth/OIDC flow for server integrations (some enterprise tiers do), that's fair game.

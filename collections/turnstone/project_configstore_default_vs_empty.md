---
name: project_configstore_default_vs_empty
description: "ConfigStore setting with a non-empty default plus empty-means-disable: branch on cs.stored_keys(); get() returns the registry default when unset."
metadata: 
  node_type: memory
  type: project
---

`ConfigStore.get(key)` (`turnstone/core/config_store.py`) returns the **registry
default** for any key with no explicit DB row — not None. So a setting whose
registry default is non-empty (e.g. `tools.searxng_url` = `"http://searxng:8080"`)
cannot distinguish "operator never set it" from "operator explicitly set it to
`''` to disable" via `get()` alone — both read back as a value.

When a setting needs **"empty = disable"** semantics on top of a non-empty
default, branch on `cs.stored_keys()` (the frozenset of explicitly-stored keys):
explicit value (including `""`) wins → else env/config → else the registry
default. That is the canonical `storage → toml → env → default` precedence
([[project_config_to_storage]]).

**Why:** discovered fixing a #545 `/review` finding. `_resolve_search_client`
first did `str(cs.get(...) or "").strip() or None` then an env fallback, which
silently **re-enabled** web search when an operator set `tools.searxng_url=""`
to disable it — the compose `TURNSTONE_SEARXNG_URL` env default backfilled,
violating the documented DB-wins precedence. The old Tavily code hid this
because its registry default was `""` (falsy), so unset and explicit-empty
behaved identically.

**How to apply:** any new ConfigStore setting with a non-empty default AND a
"clear it to turn the feature off" contract must read `stored_keys()`, not just
`get()`. Add a session/service-layer test for the explicit-empty case — unit
tests of the downstream resolver won't catch the wiring bug.

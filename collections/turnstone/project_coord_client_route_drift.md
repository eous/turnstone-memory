---
name: Coord client URL drift caught by live-route test
description: "Adding or changing a _ROUTE_PATHS entry in console/coordinator_client.py (or any client URL table): test by walking live Starlette routes, not literals."
type: project
---
`turnstone/console/coordinator_client.py` carries a `_ROUTE_PATHS` dict mapping verb → URL template.
PR #422 (legacy URL adapter removal) deleted the body-keyed `/v1/api/route/{verb}` routes but the
coord client still pointed at them — `close_workstream` 404'd in production, `send` / `approve` /
`cancel` were equally broken but exercised less often.

**Why:** The pre-existing `test_coordinator_client_route_table_uses_consistent_prefix` only asserted the literal strings matched expected literals — not that those literals were actually mounted. Comment claimed "tested against the live route table" but the test never verified that. PR #424 added `test_route_paths_match_actual_console_mounts` which walks the real Starlette app's `routes` and asserts every `_ROUTE_PATHS` entry corresponds to an actually mounted route. Catches future URL unification drift at test time.

**How to apply:** When adding a new entry to `_ROUTE_PATHS` (or any client-side URL table that needs to align with mounted routes), add a route-existence test that walks the live route table — not just a literal assertion. Pattern:

```python
from starlette.routing import Mount, Route
def _walk(routes, prefix=""):
    for r in routes:
        if isinstance(r, Mount):
            yield from _walk(r.routes, prefix=prefix + r.path)
        elif isinstance(r, Route):
            yield prefix + r.path
mounted = set(_walk(app.routes))
for key, template in _ROUTE_PATHS.items():
    assert template in mounted, f"_ROUTE_PATHS[{key!r}] = {template!r} not mounted"
```

Path-keyed templates with `{ws_id}` substitute via `template.format(ws_id=...)` at call time in `_post`; body-keyed paths (only `delete` and `close_all_children` survive) work through the same helper unchanged.

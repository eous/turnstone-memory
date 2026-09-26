---
name: feedback_no_tool_result_pruning_prefix_cache
description: In-place pruning/stubbing of old tool results was tried in earlier Turnstone versions and thrashed prefix caching; never propose it as a context-reclaim mechanism
metadata:
  type: feedback
---

Earlier Turnstone versions discarded old dead tool results in place to reclaim context. The
maintainer (2026-09-18) ruled it out: it thrashed prefix caching and drastically increased cost.
Compaction is the accepted way to reclaim context because it flushes the cache ONCE and the summary
becomes the new stable prefix.

**Why:** Prompt/prefix caches key on a byte prefix. Editing any earlier message (stubbing a tool
result, rewriting a span) invalidates every token after the edit point, so incremental or age-based
pruning walks the invalidation point forward each turn and the session pays full input price every
turn. Append-only injections (trailing nudges, system turns) are cache-safe; in-place edits are not.

**How to apply:** When suggesting context-reclaim designs (model-invoked "release these tool
results", per-result stubbing, rolling eviction), don't. Prefer rare, boundary-timed compaction with
a server-side floor, and any per-turn signal to the model must be appended at the tail, never
written into the prefix. See [[project_902_memory_index]] for the stable-prefix design and
[[feedback_context_shares_conservative]] for the share rules.

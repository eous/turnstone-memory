---
name: project_902_memory_index
description: "#902 memory index (1.8): redirected 2026-07-26 so a complete, unfiltered index in the stable prefix REPLACES composition-time snippets; bodies on demand."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-26T18:40:38.333Z
---

#902 REDIRECTED (the maintainer 2026-07-26, prompted by stable-prefix/prompt-cache
economics): the memory index now REPLACES composition-time snippet injection
instead of riding alongside it. IN SCOPE FOR 1.8 STABLE (scoped 2026-07-26,
same day). I redrafted the issue body (original preserved in edit history); measurement plan uses existing plumbing (memory.composition
log, cache_read/cache_creation usage fields, + new fetch-rate telemetry).

Mechanism facts that drove the ruling:
- System message composes ONCE at first real user message then freezes for
  cache stability (send() recompose gate, session.py ~6186-6197); the only
  memory-driven recompose after that is a memory DELETION (the maintainer
  2026-07-26). Its comment
  names "per-turn refresh" as a pending redesign on another branch — that
  redesign is SUPERSEDED by #902 (index dissolves the frozen-stale vs
  refresh-cache-bust fork).
- Snippets were 500-char truncations selected by the OPENING message only.
- New shape: stable index in prefix; bodies on demand via memory(action=...);
  score_memories repurposed as tail-side POINTER-NUDGE generator (pointers may
  be speculative, bodies never; appends, never rewrites prefix). Pinned tier =
  open scope call (a set, not a ranking → cache-stable).
- Index is COMPLETE, no BM25 filter on the catalogue (the maintainer 2026-07-26: ideally every entry
  goes in) — filtering would reintroduce invisibility + prefix churn. Cap pressure = condensing
  mechanisms (issue lists the set): hook budget, cold-first notification evidence, save-time
  backpressure, propose-approve condensing, ROLLUP LINES (group entries into one index line, members
  stay fetchable by name → cap compresses representation, never membership → index stays complete
  under any cap). Rejected: relevance-filtered index, auto-eviction archive, auto-prune. UI verb:
  "condense"/"curate", NOT "compaction" (overloads the session-level mechanism;
  [[feedback_operator_ui_plain_language]]).

Rerank consumer map (audited 2026-07-26; corrects my own earlier statements):
- Score-FLOOR exists ONLY at memory composition (`_bm25_reranker(thr)` +
  rerank_filters). web_search / tool search / skills search rerank with NO
  floor — but every path top-k cuts AFTER the reorder, so rank decides cut
  membership anyway. bm25.py reorder mode BACKFILLS omissions and falls back
  to BM25 order on empty/error (test-pinned); filter mode honors empty.
- BM25 admission gate = any positive score (one lexical token overlap).
- memory(action='search') is tsvector-based, UNRERANKED today — under #902 it
  becomes the primary recall path; wiring rerank in is the natural follow-up
  (where #914's tier slots).
- #915: skill-search floor (the maintainer: skill search should have a floor at minimum) —
  filter-mode empty-result semantics fit; probe set was designed to approximate the skill/tool
  domain; per-call index build → no stale-closure issue (unlike ToolSearchManager, whose reranker
  closure is captured at construction — flagged in #915 open questions).

Related: [[project_memory_relevance_pipeline]] · [[project_prefill_only_rerank]]
· [[project_mid_conversation_system_messages]] · [[project_compaction_visibility]]

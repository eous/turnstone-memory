---
name: project_coord_child_addressing
description: "Coordinator child ws_id addressing (wait/inspect not_found, did-you-mean): fixed v1.6.0 (d0e9aa3); mutable name addressing REJECTED, hex prefix dropped."
metadata: 
  node_type: memory
  type: project
---

Field incident (2026-06-10, found while staging a README hero-image run): a flash-tier coordinator
(DeepSeek-V4-Flash) hand-copied a child ws_id and collapsed its `aaa` run to `a` (30 chars) —
tokenizer char-run blindness means the model can't perceive the diff even when re-checking, and it
kept self-copying the bad id over the correct one sitting in a fresh list_workstreams result. Old
tooling: inspect "not found", wait "(workstream denied: not in coordinator subtree or does not
exist)", mode=all burned the full timeout, mode=all ALSO completed "successfully" with a denied
member mixed in → silent lane loss; the user read it as the coordinator having lost its connection
to the child.

Fix LANDED on main — `d0e9aa3` + follow-up `3803feb` (uniform not_found wait-entry
keys + ws_ids param precision), shipped in v1.6.0: boundary validation
(32-hex pass-through / legacy exact-id / else did-you-mean ≤3 + child roster),
denied→not_found rename, wait fail-fast on unobservable members, inspect user_id
parity (#506 gap closed), session exec keeps structured recovery payload.

**Decisions that are NOT in the code:**
- **Name addressing rejected** — names are mutable (title generator writes `title`,
  `update_workstream_name` exists, UI label = `ev.name || ev.title`) and non-unique
  per parent; stale-name resolution on close/send = wrong-sibling misfire.
- **Unique-id-PREFIX addressing (git-style, ≥8 hex) designed, then dropped** by user
  in favor of minimal 1+2+4; if ever revisited, prefix is the safe shorthand (immutable,
  ambiguity→error, no oracle) — name addressing would first require freezing names of
  coordinator-spawned children against the titler.
- **Hex→word bijective aliases = issue #698** ([[project_harness_compiler_dialect_stack]]): the immutable id stays canonical, the word is a derived display handle expanded before execution — provably lossless, so it ships free of the soundness gate (unlike the rejected mutable names-as-addresses).
- **Open thread:** model-facing `name` column vs user-facing `title` label diverge —
  two identity views of one child; mild model-confusion generator, parked.
- Spawn alias errors ("Unknown model alias: sonnet") are raised node-side in
  model_registry; listing valid aliases in the deny reason is a separate cross-service
  improvement, not done.

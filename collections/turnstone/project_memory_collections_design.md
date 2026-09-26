---
name: project_memory_collections_design
description: "Per-persona memory collections (#684): SUPERSEDED, never built; Projects (#724) took the role, #683 shipped a toggle; persona and skill stay DETACHED."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-20T17:04:33.002Z
---

**RESOLVED, condensed 2026-07-06 (was a 150-line exploratory design doc; the
proposal below was superseded before it was built — this is now a historical
breadcrumb, not an active design).**

**What actually shipped instead:** the topical-memory bucket became a first-class **Project** (#724,
migration 062, decoupled from persona — see `project_projects_feature_design`), which took the
topical axis this file proposed giving to per-persona "collections." On the persona side, #683
shipped only a simple **memory on/off toggle** (own-hands-only) — not the elaborate
collection/lifespan/creation- authority model designed below. **GitHub #684 ("Memory collections for
personas & projects") superseded 2026-07-02**, body left as the decomposition record. No open work
remains against this design.

**Durable decision worth keeping (still may be referenced elsewhere): Persona
vs Skill → DETACH (user, 2026-06-20).** Personas get their own shape, not
fitted into skills — reversing an earlier "extend skill.md" concept. Rationale:
different questions — skill = "what does it know / steered toward"
(augmentation, N-per-session, composable); persona = "who is it / what can it
see / where its memory lives" (identity + capability envelope, 1-per-session).
Detach the ENTITY, reuse the infra (scanner, parser, import/export, search,
admin). Runtime: persona ⊕ skill(s) still compose (persona = identity/envelope,
skills = layered augmentation). This shaped how #683 (Personas) was ultimately
built — cross-check against
[[project_skillmd_refactor]] before assuming it's settled further.

**Other locked reasoning from the original design, for reference only (none of this was built as a
"collection" — Projects took the role instead):** recall would have been `global ∪ user(owner) ∪
persona-collection`; collection 1:1 with persona (auto-bounds namespace, no sprawl to police);
collection as an attribute on existing scopes, not a 4th scope enum; lifespan durable|episodic;
coordinator-as-persistence-point for project memory (workers keep role-craft in their own persona
collection, hand findings up the orchestration channel rather than through shared memory). The
motivating failure was topical content written into global memory and then recalled into unrelated
contexts. Projects (#724) provide an explicit topical scope; [[reference_memory_store_maintenance]]
covers scope-aware maintenance.

Cross-refs: [[reference_memory_store_maintenance]] · [[project_memory_relevance_pipeline]] ·
[[project_design_constraints]].

---
name: project_admin_shelf_redesign
description: "Adding a console admin dialog or hatch shelf (Service Hatch SHIPPED PR #647, 06-10): pane-scoped shelf, not a popup modal; keep the clip/label/nesting rules."
metadata: 
  node_type: memory
  type: project
---

**SHIPPED.** v1 (floating-modal reskin) was REJECTED by the user as not L-shell-level (the user
asked to move away from popups toward something integrated, such as a sliding tool shelf). v2 — the
"Service Hatch" shelf system — replaced all 35 legacy popup modals (30 console + 5 ui) across 22
commits (`fe05bbe7..4e635ca6`), merged to main as **PR #647 (2026-06-10, 1.6.0rc2)**. Console is now
100% on the hatch system, zero legacy modal machinery.

**Design (two required layers):**
1. **Container tiering** — create/edit/inspect moved to a right-docked, PANE-SCOPED,
   non-modal **shelf** (`dialog.show()` mounted inside the pane element, `inert` on
   sibling content, splits work by construction). Confirms + show-once dialogs STAY
   small centered `showModal()` (top-layer, destructive-safety wants blocking
   semantics) — ~8 of 35 stayed dialogs.
2. **Smart inputs** ("the system already knows") — expert-knowledge fields get
   builder-compiles-to-raw / autofill-from-code / live read-out with a raw-form
   escape hatch: cron builder + NEXT RUNS read-out (Schedules), capability matrix +
   known-model autofill (Models), priority-neighbor match strip (Policies).

**Durable patterns (verified live, keep applying to future UI work):**
- Pane-host clipping is always `overflow:clip`, never `hidden` (paint-clip vs a
  hidden *scrollable* container — the latter silently ate focus-scroll).
- Any visually-hidden abspos input (toggle-switch/`.cap`/segmented-option) MUST have
  a **positioned label**, or focus-into-view scrolls the wrong ancestor.
- Shelves MUST be direct hatch-host children — a nested shelf inerts ITSELF (`inert`
  inherits down; bit the admin Judge tab's nested HR/OGP shelves).
- `.hatch [hidden]` needs `display:none !important` (toggle-switch inline-flex
  defeats plain `hidden`).
- Screenshot gates need `--force-prefers-reduced-motion` (entrance animations race
  `--screenshot`); the livepass console harness wraps fragments in the real L-shell
  chain, not a bespoke height pin.
- Models tab uses SPARSE-OVERRIDE persistence (only saved-explicit + user-toggled
  keys written) so known-model rows keep tracking upstream table updates.

**Process notes (reusable for future large-surface UI sweeps):** built via sequenced
implementer agents against LOCAL, judgment-transferring briefs (`docs/design/
shelf-sweep-brief.md`, `skill-editor-shelf-brief.md`, `phase3-ui-dialogs-brief.md`) —
the pattern [[feedback_fresh_briefing_vs_agent]] cites as "judgment work CAN delegate
when the brief pre-makes design decisions." Dual-designer review (primed Fable +
cold Sonnet) adjudicated the post-teardown pass; when the two reviewers conflicted,
checking the CSS cascade (not re-guessing) resolved it.

**Post-merge fix:** a scroll-regression round (`da86f44c`) fixed the manage pane
losing its scroller + the docked shelf shoving off-head on focus-into-view of hidden
inputs — root cause was exactly the two clipping/label rules above, learned the hard
way; they're now the standing rules for any new hatch surface.

**Remaining:** polish backlog (sticky colheaders, scrollbar theming, light scrim
weight) tracked in [[project_1_7_roadmap]]'s polish section, not here.
Related: [[project_frontend_lshell_renovation]], [[project_model_modal_kind_redesign]].

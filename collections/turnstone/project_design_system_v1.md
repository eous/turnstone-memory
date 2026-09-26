---
name: Design system v1 (Claude Design handoff)
description: "Frontend CSS or 'is this view on design v1?': the [data-design=v1] opt-in is GONE since #431, one unified default system; never reintroduce a gate."
type: project
---

**Phase 1 SHIPPED #389 (`78865c7`) 2026-04-15** as an OPT-IN system: files under
`shared_static/design/` (`tokens`/`typography`, `primitives/*`, `chrome/*`,
`patterns/*`), every rule scoped `[data-design="v1"]`. Phases #391/#392/#393
opted chat + coordinator views in.

**UNIFIED #431 (`cc20c70`) 2026-04-27 — the opt-in is GONE.** #431 stripped the
`[data-design="v1"]` attribute from ~400 rules and merged `shared_static/design/*`
into the pre-v1 sheets (tokens+typography → `base.css`; appbar/panel/buttons/
pills/field → `ui-base.css`; message primitives → `chat.css`); #433/#434 cleaned
up cascade-flip + legacy dual-classing. **No `data-design` attribute remains in
code** (`grep data-design turnstone/` → 0). So: there is ONE design system, it is
the default, and "is this view on v1?" is no longer a meaningful question — every
view renders the unified sheets. Don't reintroduce a `[data-design=*]` gate or
describe v1 as scoped/opt-in.

Coordinator vs interactive web UI still differ by CSS **vocabulary**, not version:
`.coord-tool-*` (coordinator.css) vs `.ts-approval-*` (ui/style.css) are two
divergent class sets for the same concepts — that divergence (not any v1 flag) is
the real cost of a coordinator↔interactive renderer port. See
[[project_early_paint_tool_calls]].

Durable house-style rules (still hold, now applied globally, not gate-scoped):
- **Approve = amber (warn-tinted), not green** — approvals signal "needs
  attention". Accent hue ~70; `--ok` hue 150.
- **Desktop-only** on the coord/console surfaces: `min-width ~1280px`, no responsive.
- **`color-mix` must use `in srgb`** (never oklch/oklab); raw color defs use `oklch()` fine.
- **No icon library** — Unicode glyphs only; brand mark is conic-gradient CSS.
- **WCAG 1.4.1**: k-badges carry glyph prefixes (`▲ tools`, `◆ policy`, `■ query`);
  pills pulse to encode state without color dependence.
- Theme default DARK; light requires explicit `[data-theme="light"]` (`theme.js`).
- SSE wire / approval POST / TS SDK / OpenAPI unaffected — re-skins rendering only.

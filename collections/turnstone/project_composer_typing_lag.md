---
name: project_composer_typing_lag
description: "Composer typing lag on long sessions: root cause is the shell grid's auto rows, not missing containment; contain:strict hurts; fixed on dev and in v1.8.5."
metadata:
  node_type: memory
  type: project
  modified: 2026-09-25T05:08:12.036Z
---

A user report (09-24) blamed the uncontained `.pane-messages` flex column plus
`Composer.autoResize`'s per-keystroke `height:auto` + `scrollHeight` read, and offered a console
snippet (`contain: strict` + `field-sizing` + a rAF resize). Measured in headless Chrome 148 and
Firefox 156 with the real InteractivePane in the production shell DOM:

- **Root cause: the shell grids' implicit `auto` rows** (`.app`, `.panes` in shell.css). Sizing
  an auto row asks for the item's max-content height, so every layout pass (keystroke, streamed
  token, tool chunk) re-measured the whole transcript through the nested flex columns. Fix =
  `grid-template-rows: minmax(0, 1fr)` on BOTH (either alone keeps ~85-100% of the cost). Chrome
  @3000 msgs: 54 -> 0.8 ms/keystroke, stream frame 16 -> 9.6 ms; Firefox @300: 31 -> 0.7 ms.
  Pixel-identical at wide widths in both engines. **Split view never had it** (absolutely
  positioned sections are not grid items), so it hits the default single-pane mode.
- **`contain` on the transcript does nothing in Chrome and is catastrophic in Firefox**
  (`contain: strict` @3000: ~360 ms/keystroke vs 14 on dev). Never add it as a perf fix here.
- rAF-coalesced autoResize: no gain (slightly worse). Block-flow scroller: helps less than the
  grid fix and changes row spacing (margin collapse), so not used.
- Composer: native `field-sizing: content` behind `CSS.supports` (class
  `.composer-input--autosize`) for ONE-ROW fields only (content sizing ignores `rows`, so the
  rows:3 home launcher keeps the measuring path, byte-identical to dev); JS measuring path is the
  fallback. Multi-line drafts 8 -> 0.9 ms/key @3000. It also fixes a dev bug: in Firefox the
  measuring collapse clamped the scroll offset and autoscroll switched off on every keystroke of a
  multi-line draft (39/40 keys); 0 after.
- **Empty field fits its CURRENT placeholder** (designer gate: accepted as better than dev, full
  hint readable). Unprimed reviewers re-raised it in all 4 rounds, twice claiming dev "always sized
  an empty field to one row" - false: dev fits the placeholder at every send (clear), just never
  re-fits on later swaps. Rationale now lives in the chat.css comment. Rejected alternatives:
  `:placeholder-shown { field-sizing: fixed }` (made dev's first-load one-row+scrollbar wart
  permanent); a 3-line placeholder cap (added then DELETED: padding-coupled selector + clipped the
  send-blocked hint; its guarded case is a 200x150 split cell during another participant's turn,
  where the row incl. Stop can still be pushed below the cell).
- Coordinator pane (timed 09-24, same probe, real createCoordinatorPane): console keystroke
  10 -> 0.9 ms @3000 (block-flow transcript = cheaper re-measure than interactive's flex column);
  standalone /coordinator page has no shell grid (single-line ~1 ms already), 4-line 4.5 -> 0.8;
  Firefox autoscroll loss 39/40 -> 0 in both. Chrome STREAMING unchanged (~10 ms/frame @3000,
  5 reps each; standalone ~9 ms too) = its own per-frame render cost growing with transcript
  length, not the shell. Neither pane has transcript windowing on dev.
- The repo perf page (`scripts/livepass.py --perf`) mounted the pane in a fixed-size flex box, so
  it could never see this; the branch moves it into the shell chain and adds a keystroke row.

**Why:** the July audit ([[project_frontend_long_session_audit]]) already flagged the autoResize
reflow but planned to fix it with containment in #755, which never reached dev.

**How to apply:** for frontend layout-cost work, measure in the production shell chain, not a
bare mount; check grid/flex ancestors for content-sized tracks before reaching for `contain`.
Probe method + engine gotchas: [[reference_headless_chrome_frontend_render]].

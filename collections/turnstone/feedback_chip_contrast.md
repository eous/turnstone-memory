---
name: feedback-chip-contrast
description: "Tinting small chips/badges to show state (grant/revoke/active): background alpha >=0.15 plus a same-hue border and a glyph; sub-0.10 reads as noise."
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-07-26T00:21:58.940Z
---

When using a tinted background to convey state on small chips/badges (e.g. drawer perm chips with grant/revoke variants), keep alpha ≥0.15 and pair with a border at ≥0.5 alpha in the same hue. Don't reach for sub-0.10 alphas — at chip size those wash out against the surrounding surface and the state stops reading.

**Why:** During verification of the builtin role-overrides work the user flagged weak contrast on the chip palette I'd shipped with alpha 0.05/0.06 backgrounds. The chips were technically tinted but visually indistinguishable from the baseline neutral chips — the state information was lost.

**How to apply:**
- Chip state backgrounds: `rgba(<hue>, 0.15)` minimum, `rgba(<hue>, 0.55)` on the border
- Chip text: bump from `var(--fg-dim)` to `var(--fg)` (or the state hue itself) so the label is readable against the page bg
- Recessed surface (drawer, inset card): prefer `rgba(0,0,0,0.04)` over `var(--bg-highlight)` in light theme — the latter is too close to `--bg` to read as a step
- Always pair colour state with a glyph (`+`, `−`, `•`) or text — colour alone fails for accessibility AND for any environment where the alpha doesn't render true

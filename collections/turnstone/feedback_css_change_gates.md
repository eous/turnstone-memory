---
name: feedback_css_change_gates
description: "After any CSS change: diff css_specificity_audit.py against the base tree, then gate on a designer-agent review: findings, resolutions pass, final pass."
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-09-05T05:34:43.482Z
---

Two gates the maintainer asked for on 2026-09-04 while fixing #1092 (light-theme kind hue contrast):
run scripts/css_specificity_audit.py after changing CSS, and finish with a designer-agent review.

**Why:** the audit catches cascade flips that only show visually (PR #431/#433
history); the designer review on #1090 found 5 majors that the code reviewers
missed ([[project_scheduled_launcher_kind]]).

**How to apply:**
- Calibration (the maintainer 2026-09-13, hatch.css hint/collapse fixes): the gate is findings → a
  resolutions pass → done. When each resolution is already verified by computed styles or
  renders (wide render byte-identical, narrow renders eyeballed, audit diff clean), a THIRD
  designer pass on the fixed tree is excessive — commit instead of re-reviewing.
- Run `python3 scripts/css_specificity_audit.py` on the working tree AND on
  the stashed base tree, then diff the two reports. The script is not in CI
  and exits 1 on main as of 2026-09-04 with 10 known ID-tier findings
  (`#theme-toggle` outranking `.header-btn` colour/font-size/line-height/
  transition on both index.html files; `#admin-mcp .admin-toolbar` gap in a
  media query). All look like deliberate scoped overrides except that the
  toggle's `color: var(--fg)` also pins the `.header-btn:hover` brightening.
  Exit status alone therefore proves nothing; a clean change is one whose
  report differs from base only in line numbers.
- Close with a `designer` agent review briefed with the diff, the measured
  numbers and headless-Chrome renders (light AND dark;
  [[reference_headless_chrome_frontend_render]]).
- Light-theme hue tokens (`--accent` #745415, `--cyan` #155e75, `--blue`
  #075985) were cut for 12px text on a 15% tint to clear 4.5:1; the chip-tint
  floor stays 0.15 ([[feedback_chip_contrast]]), so fix contrast in the token,
  never by thinning the tint. The amber sits at hue 40 (brand is 35) because
  a hue-35 amber at that lightness renders chocolate, verified by side-by-side
  headless render. The rail brand mark's far gradient stop is the per-theme
  `--brand-mark-end` token. #1094 (stacked on the same branch) then moved
  the rest of the hex family one step (green #065f46, red #991b1b, yellow
  #92400e, magenta #6d28d9, discord #4338ca, slack #9d174d) so the light
  palette is one tier; light `--yellow-glow` is 0.2 alpha because yellow
  text sits on it. Measure glow pairings at the GLOW alpha (0.25), not the
  15% chip tint — the second designer round caught that miss. The oklch
  `--ok/--warn/--err/--think` family is separate and untouched.
- **Designer review is a gate, not a report** (the maintainer 2026-09-05, status-bar
  approval chip): run it three times on the same agent — findings on the
  committed diff, then SendMessage the proposed resolution of each finding
  (including the ones you reject, with the measured reason) for
  ACCEPT/BLOCK, then a final PASS/BLOCK pass on the fixed tree. Measure the
  designer's numbers before accepting them: on the chip it assumed the status
  bar repaints per token (it repaints once per generation commit, and not at
  all while a gate is open), which withdrew its live-region restructure
  finding. Its arithmetic and contrast findings were right.
- The oklch `--warn` family now has `--warn-text` (base.css, both themes):
  ink for text ON `--warn-tint`, mirroring `--ok-text`. `--warn` itself is
  3.3:1 on the light tint; use `--warn-text` for any text on a warn tint
  (the rail badge and the approval chip do). Dark value equals `--warn` but
  is written as a literal so a `--warn` retune can't move chip ink.

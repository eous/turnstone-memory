---
name: project_backdrop_filter_input_lag
description: "Typing lag under a backdrop-filter overlay/dialog/scrim: compositor re-blurs it every frame."
metadata:
  node_type: memory
  type: project
  modified: 2026-10-09T20:10:00.000Z
---

A report (10-09, reproduced in Firefox) of slow typing in the login form. It was presumed to be the
transcript re-measure bug ([[project_composer_typing_lag]]), but measurement refuted that. The
cause is `#login-overlay { backdrop-filter: blur(8px) }` (base.css), a full-viewport layer.

- **Main thread is cheap:** 0.2-0.5 ms per login keystroke with 0, 300 or 3000 messages (27k
  nodes) behind the overlay. The grid fix holds, and the transcript is not re-measured.
- **The compositor pays.** Any frame with damage, including each keystroke and caret blink,
  re-blurs the whole filter area. Headless Chrome 148 with software compositing, 1440x761 @2x:
  viz `DirectRenderer::DrawFrame` took 130 ms per frame with the blur and 1.2 ms without it.
  Typing ran at 7.7 fps with the blur and 60 fps without. The @1x figures were 30 fps at
  1440x761 and 19 fps at 1920x941. Headless Firefox 157 typed at 26-30 fps with the blur and 60
  without.
- **Moving the blur to a separate layer behind the box did not help** (same fps). Damage in layers
  above a pixel-moving backdrop filter still re-runs it. Cost scales with area x DPR, not
  radius: the pane scrim's 2px blur was as slow per pixel as the overlay's 8px.
- **Sibling surfaces have the same defect.** `.hatch--dialog::backdrop` blur(6px) is full
  viewport: new-workstream and rename dialogs typed at 7.3 fps @2x versus 60 without.
  `.pane-scrim` blur(2px) is pane-sized and sits behind every console admin and governance shelf
  form: 9.7 fps @2x versus 60. `#kb-overlay` blur(4px) has no inputs, so it costs only while
  something behind it changes.
- GPU compositing is much cheaper. The lag is worst with software compositing (Firefox software
  WebRender, Chrome without GPU) and on HiDPI displays.

**Fix (PR #1333, branch fix/login-input-slow, 10-09):** the maintainer approved removing all four blurs. The
renders then showed the conversation readable through the 85% login tint, so the maintainer ruled
the sign-in overlay opaque. It now uses `color-mix(in srgb, #000 85%, var(--bg))`, derived from
`--bg` rather than copied, after an opaque literal fallback so an engine that drops the mix still
cannot show the gate transparent. The designer gate raised the dark `.pane-scrim` from 0.45 to 0.55
and passed the dialog backdrop, the kb overlay and the light scrim with their tints unchanged.
`test_no_backdrop_filter` (tests/test_shell_js.py) scans first-party CSS, HTML and JS, with comments
stripped; 11 mutation controls behaved.

**#1332, on the same branch:** modal dialogs painted above the gate (top layer) and left the
sign-in form inert. `showLogin()` now closes every `dialog:modal`, with the selector guarded in
try/catch so an engine without `:modal` still shows the gate. All modals open through hatch
`openDialog`, so busy, focus and onClose run as for any dismissal. Shelves stay open. Closing
the modal exposed Escape reaching hatch's document listener, which closes the topmost shelf
behind the gate (it already did with no modal open). The fix is an overlay-level keydown that
clears the error and stops propagation. The token dialog now clears its text on close. Review
suggested making the gate a native modal `<dialog>`, which would make the page behind inert.
The maintainer chose "contain Escape" only (10-09): the native dialog would touch four readers
of `#login-overlay`'s `style.display` (kb.js, interactive.js, console app.js twice). A
successful sign-in does not reload, so dialogs kept open under a gate would reappear for the
next user. The livepass console `?open=schedule-*` drivers had thrown a TypeError (no
`schedule_builder.js`, no `#schedule-when-template`); the harness now loads both, and
`tests/test_livepass_console.py` pins it.

**Why:** a blur over a large area looks static but is recomputed on every changed frame. That
fails the composer-lag lesson of checking what a keystroke makes the engine redo, at the
compositor stage instead of layout.

**How to apply:** do not add `backdrop-filter` to large or full-viewport surfaces. Dim with an
opaque or translucent background instead. For input-lag reports, measure frame pacing and the
viz draw time, not only main-thread keystroke cost. Method:
[[reference_headless_chrome_frontend_render]].

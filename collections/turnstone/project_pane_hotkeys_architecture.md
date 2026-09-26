---
name: project_pane_hotkeys_architecture
description: "Adding or changing a pane keyboard shortcut: shell.js PANE_MENU_ACCELS is the single source (PR #776); modifier is Ctrl on macOS, Alt on Windows/Linux."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-20T17:01:47.495Z
---

Pane/workstream keyboard accelerators (PR #776, 2026-07-05, branch `fix/pane-hotkeys-browser-accelerator-conflict`).

**The browser-owns-a-modifier gotcha:** on Windows/Linux `Ctrl` IS the browser's own accelerator (Ctrl+T new tab, Ctrl+W close tab, Ctrl+1-9 switch tab) — those chords never reach the page. macOS browsers own `Cmd` instead, leaving `Ctrl` free. So pane hotkeys **must pick the modifier per platform**: `Ctrl` on macOS, `Alt` on Windows/Linux. `IS_MAC = navigator.platform.indexOf("Mac") > -1`. Dashboard stays on `Ctrl+D` on every platform (cancelable everywhere; `Alt+D` = browser focus-address-bar, unreclaimable).

**Single source of truth = `shared_static/shell.js`.** It owns `PANE_MENU_ACCELS` (the accel registry), `paneAccelBadge(id)` (platform-aware badge string), `paneAccelFor(e)` (keydown→accel), and `inEditable(el)` (typing guard, exposed on `window.TS_SHELL`). The per-pane tab-menu items in `convTabMenu` carry a stable `accel:` tag + `key: paneAccelBadge(...)`; ONE shared keydown handler in `mountShell` runs the **active pane's own `tabMenu()` item by accel** — so a badge can never advertise a chord the handler ignores, and each surface contributes only the items it supports.

**Why this mattered:** shortcuts were previously declared in THREE drifted places — the `?` overlay (`index.html`), each `app.js` keydown handler, and the tab-menu badges. The console fell to `convTabMenu`'s node-proxy **fallback lane** (no `window.forkWorkstream`/etc. globals), which silently dropped every badge + Fork; its `Ctrl+W` just closed the browser tab. The two lanes (globals vs node-proxy fallback) are how server-vs-console verb routing differs — see [[project_frontend_lshell_renovation]].

**Split of responsibility:** shell.js owns the per-pane MENU accels (close-pane, edit/refresh title, fork, delete) for BOTH surfaces. Each surface's `app.js` keeps only its GLOBAL accels — new / switch / dashboard (server: `ui/static/app.js` over the `workstreams` roster; console: `console/static/app.js` over `pm.statefulTabs()`). No key overlap → no double-fire.

**Durable conventions established:**
- `Mod+W` = **Close pane** (drop the tab, session keeps running) everywhere — matches its badge + universal Ctrl+W convention. Previously the standalone's Ctrl+W *stopped the session* (`closeWorkstream`); stopping is now the un-hotkeyed "Close workstream" menu item.
- `Ctrl+T` / `Ctrl+D` yield to text editing when a field is focused (macOS Cocoa transpose / delete-forward bindings) via `TS_SHELL.inEditable`; switch (`Mod+1-9`) and close (`Mod+W`) do NOT overlap text editing so they work while composing.
- **Console omits Fork** (no console fork/new-session surface yet — deferred, tracked in **issue #777**; `PANE_MENU_ACCELS.fork` already exists so `Mod+Shift+F` + badge light up for free once the fallback lane can offer Fork). New workstream is also server-only.

Guards live in `tests/test_app_js.py` + `tests/test_shell_js.py` (static string-presence, no JS test framework). `openPopupMenu` (pane.js) renders only `label/key/action/cls/separator`; the `accel` tag is inert to it.

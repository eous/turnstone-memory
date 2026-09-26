---
name: headless-chrome-renders-the-frontend-in-sandbox-server-boot-blocker-doesn-t-apply
description: "Frontend render check when the server won't boot: google-chrome --headless in the sandbox renders a file:// or loopback harness; no CDP, never pkill -f chrome."
metadata: 
  node_type: memory
  type: reference
---

`/usr/bin/google-chrome` (also `-stable`) **is installed in the sandbox.** The recurring
"coord/interactive frontend is browser-only-verifiable, the server won't boot (Postgres/psycopg +
no LLM)" constraint applies to a *live-server* render — NOT to a static `file://` render. So
frontend rendering, CSS, and client-side logic CAN be verified in-sandbox.

**Technique (per another session, 2026-05-29):**
```
PROF=$(mktemp -d /tmp/crp.XXXXXX)
timeout 30 /usr/bin/google-chrome --headless=new --no-sandbox --disable-gpu --hide-scrollbars \
  --force-color-profile=srgb --user-data-dir="$PROF" --allow-file-access-from-files \
  --virtual-time-budget=1800 --window-size=1000,440 --screenshot=/tmp/out.png \
  "file:///tmp/harness.html"
# structure (no pixels): swap --screenshot for --dump-dom > /tmp/dom.html
```
Then `Read /tmp/out.png` (the Read tool views PNGs) and/or grep the dumped DOM.

**Harness recipe for a real app page (e.g. `coordinator/index.html`, `ui/index.html`):**
- Copy the page's DOM scaffold; rewrite `/shared/*` + `/static/*` href/src to absolute
  `file://<turnstone checkout>/turnstone/{shared_static,console/static,ui/static}/...` paths
  (`--allow-file-access-from-files` lets file:// pull file:// resources).
- Set the page's data attr (coord reads `document.documentElement.dataset.wsId`).
- BEFORE the app script, inject mocks: `window.authFetch`/`fetch` returning canned `/history` +
  ws-snapshot JSON (coord's `getJSON` uses `authFetch` when present — behavior confirmed 2026-07-06,
  but the line number drifts with every edit to `coordinator.js`; it was ~1874 as of this memory's
  writing and is ~2155 now, so grep for `function getJSON` rather than trusting either number), and a
  no-op `window.EventSource` so `connectSSE()` doesn't hit the network. Force `.msg-actions
  { opacity:1 }` to make hover-revealed affordance buttons visible in the screenshot.

**Verifies:** CSS rendering (e.g. the ported icon glyphs + edit-form), the render path
(`refetchHistory` over a canned `/history`), affordance attachment, turn-count DOM math.
**Does NOT verify:** the live server round-trip (POST rewind → server → `clear_ui` SSE) — that
still needs a running server. So it's a strong pre-handoff check, not a full substitute for the
user's integration smoke. See [[project_command_verb_lift]] (PR #598 — user smoked manually
that time, but this would have caught CSS/render bugs earlier).

**Gotchas (2026-05-28, MCP-admin kebab work — PR #599):**
- **Never `pkill -f chrome`** to clean up — the bash command line itself contains "chrome", so
  `pkill -f chrome` matches and kills its own shell (exit 137/144, empty output; reads as a
  mysterious hang). Use a fresh `--user-data-dir=$(mktemp -d)` per run to dodge singleton-lock
  collisions instead of killing.
- **`--remote-debugging-port` / CDP is blocked** in the sandbox — launching with it kills the
  shell (signal). No Puppeteer-style WS driving; `--screenshot` and `--dump-dom` only.
- **Headless fires a `resize` during initial layout settling**, which dismisses any JS-opened
  transient UI (dropdown/popover/menu) before `--screenshot` captures it. To shoot an *open*
  state, hardcode the open class in a static-markup harness (CSS-only). To test *interactive* JS,
  run a **synchronous self-test**: dispatch `.click()`/`new KeyboardEvent('keydown',…)` (handlers
  fire synchronously), write pass/fail into the DOM immediately, then read it via `--dump-dom`
  (immune to the artifact). This verified the kebab open/close/Escape/arrow-nav 15/15.
- **`--window-size` is honored by `--screenshot` but NOT `--dump-dom`** (dump reports ~500–780px
  regardless) — measure viewport-dependent layout (e.g. an off-screen-clip / flip) via
  `--screenshot`, or read `window.innerWidth` inside the harness.

**Real-page load-order harness (2026-06-09, the technique that caught a both-deployments boot
failure the mocked harness could not):** a harness that mocks the `TS_APP`/`TS_ADMIN` seams
verifies shell *behavior* but structurally cannot catch classic-vs-module **load-order** breaks —
it never runs the real app.js/admin.js/governance.js parse phase. Complement it with a
real-page harness: take the real `index.html`, inject ONLY (a) a first-in-head error collector
(`window.__errors` + `error`/`unhandledrejection` listeners) + `fetch`/`EventSource` mocks, and
(b) a last-in-body `<script type="module">` assertion block; serve the REAL file layout over
loopback HTTP (`/tmp/srv` with `static`/`shared` symlinks + `python3 -m http.server`) because
absolute-path dynamic imports (`import("/static/...")`) don't survive file:// URL rewriting
(the specifier lives in JS, not HTML). Assert: `__errors` empty, `TS_APP.boot` defined,
`TS_SHELL` mounted, panes/overlay present.
- **Gotcha:** `mountShell()` is async (console awaits the coordinator dynamic import) and
  shell.js calls it without await — an assertion module that samples at eval time races it
  and false-FAILs. Poll (`for (...) if (window.TS_SHELL) break; await setTimeout 25ms`) —
  `--virtual-time-budget` fast-forwards the polling.
- The class of bug this catches: top-level `const X = bridgedGlobal(...)` in a classic bundle
  (a *declaration* whose initializer executes at parse). Audit greps that filter out
  `const|let|var` lines miss exactly these — grep for `^(const|let|var)\s+\w+\s*=[^=].*\b(NAMES)\b`
  too.

**Timing probes + a second engine (2026-09-24, composer typing lag — [[project_composer_typing_lag]]):**
- Per-keystroke cost: focus the textarea, `document.execCommand("insertText", false, ch)` (the
  editing path a real keystroke takes; input listeners fire), then force the remaining layout
  (`document.documentElement.offsetHeight`), then time the next frame's rendering as rAF ->
  MessageChannel-post delta. Report results by POST to a loopback sink (no CDP needed).
- **Headless Firefox works** (`/usr/bin/firefox` is a snap wrapper, 156 on 09-24):
  `firefox --headless --no-remote --profile <dir> --width W --height H URL`. The snap cannot read
  a profile under /tmp ("Could not find profile folder") - put it under
  `~/snap/firefox/common/`. Write `user.js` with `privacy.reduceTimerPrecision=false` for sub-ms
  timings.
- Chrome headless will not go below ~500px window width: squeeze the page's own grid column to
  test narrow panes. Set `data-theme` in a head script before first paint - flipping it from a
  module script leaves colour transitions mid-flight and pixel diffs go full-frame.

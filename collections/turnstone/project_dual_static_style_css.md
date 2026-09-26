---
name: project_dual_static_style_css
description: "CSS for renderer.js output or anything a coordinator/console user sees: /static/style.css differs per server; put it in shared_static/chat.css (PR #809)."
metadata: 
  node_type: memory
  type: project
---

**Trap:** there are TWO `style.css` files served at the same URL `/static/style.css`:
- `turnstone/ui/static/style.css` — main server (`server.py`, `/static` → `ui/static/`), loaded by `ui/static/index.html`.
- `turnstone/console/static/style.css` — console server (`console/server.py`, `_STATIC_DIR = parent/"static"`, `/static` → `console/static/`), loaded by BOTH `console/static/index.html` AND `console/static/coordinator/index.html`.

They are independent regular files (not symlinks) and drift. A visual rule added to only one silently applies on only that surface. Both servers mount `/shared` → `shared_static/` (the ONE shared dir).

**Rule:** any rule that must render identically on the server UI, the console, AND the coordinator belongs in a `shared_static/*.css` (`base.css` for palette vars, `chat.css` for message/code styling — both loaded by all three index.html), NOT in either `style.css`.

**Bug this caused (fixed 2026-07-08):** hljs syntax highlighting looked dead on the coordinator/console for several releases — highlight.js still emitted `<span class="hljs-*">` (postRenderHljs runs on every surface; hljs global loads on all three), but the `.hljs-*` token-COLOR rules lived only in `ui/static/style.css`, so coordinator spans fell back to `--fg` = flat monospace. Fix: moved the whole hljs theme block into `shared_static/chat.css`. Verified via headless-chrome harness on the coordinator CSS set ([[reference_headless_chrome_frontend_render]]): `.hljs-keyword` computed color went `--fg` → `--magenta` (dark AND light theme).

**Same bug class, also fixed same PR:** the OTHER renderer.js outputs were UI-only too — `.katex-display`/`.katex-error` and `.mermaid-container`/`svg`/`-loading`/`-error`. These RENDER on the console (mermaid draws a self-contained SVG; vendored `katex.min.css` draws glyphs), so they weren't invisible like hljs — but the app-level frame was missing: no `overflow-x:auto` scroll container + no `svg{max-width:100%}`, so **wide diagrams/equations overflowed the pane** on console/coordinator, and loading/error states were unstyled. Moved those wrappers into `chat.css` too. Rule of thumb: **anything that decorates renderer.js output (`.hljs-*`, `.katex-*`, `.mermaid-*`, `.msg-body …`) belongs in shared CSS.** Note the coordinator does NOT load `preview.css` either (only the console + ui do), so preview.css is not a valid shared home.

**Shipped as PR #809** (branch `fix/coordinator-renderer-theme`, off post-1.7.1 main): moved hljs + katex + mermaid renderer-output CSS into shared `chat.css`, restated the mermaid width-clamp for the preview pane (`.preview-markdown`), and dropped the redundant `background` on `.msg.assistant pre code.hljs` (it painted a `--code-bg` box inside the console's `--panel` pad band — a seam the adversarial review caught). Single-agent adversarial review = approve, no blockers; 198 JS/CSS tests pass.

Sibling drift-class of [[project_dual_schema_parity]]. When touching `ui/static/style.css` for anything a coordinator user also sees, ask "does the console load this?" — it doesn't.

---
name: reference_github_markdown_math_rendering
description: "LaTeX in a GitHub-rendered Markdown file (HYPOTHESIS.md): only $`…`$ inline and ```math fences at top level; bare $…$ / $$ gets Markdown-processed; probe with gh api markdown."
metadata:
  type: reference
---

GitHub runs Markdown inside bare `$…$` and `$$…$$` math before its math renderer sees the
text (measured 2026-10-10 through `gh api markdown`, issue #1341). Two consequences: an
underscore between punctuation (`}_{`) can open or close emphasis, so two such spans in one
paragraph turn into `<em>` and neither is recognised as math at all; and CommonMark backslash
escapes strip the backslash from `\{ \! \, \; \#` inside both the inline and the display
form. GitHub's protected forms pass the content through verbatim: `` $`…`$ `` inline and a
```` ```math ```` fence for display. A ```` ```math ```` fence indented inside a list item renders
as a plain code block, so display math has to sit at top level.

**Probe:** `gh api markdown --input body.json` (mode `gfm`) reproduces the site's math
handling. Every recognised span comes back wrapped in
`<math-renderer class="js-inline-math|js-display-math">`, with `<` and `>` double-escaped
(`&amp;lt;`) in both forms, so compare after unescaping twice. Rendering the whole file and
checking that each source span appears verbatim inside a renderer element is a complete check
(HYPOTHESIS.md: 692/780 spans before the #1341 fix, 780/780 after).

**Trade-off:** the protected forms are GitHub's and GitLab's syntax only. Viewers that
implement the common `$…$` / `$$…$$` convention (an editor's Markdown preview, Obsidian,
pandoc) show the backtick form as a dollar sign, a code span of raw LaTeX and another dollar
sign, and the fence as a plain code block. No form renders on both, because GitHub's
emphasis pairing runs before any math syntax is recognised; GitHub is the only place
HYPOTHESIS.md is published, so it wins. State this trade-off whenever the forms are chosen.

**How to apply:** HYPOTHESIS.md uses only the protected forms, and `lint_hypothesis.py`
sections A/B flag any bare dollar as a residue. Write new math in any GitHub-rendered doc the
same way. Related: [[project_harness_hypothesis_doc]].

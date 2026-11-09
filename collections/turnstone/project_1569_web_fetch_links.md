---
name: project_1569_web_fetch_links
description: "web_fetch link targets (PR #1569, 2026-11-05): the maintainer's rulings on link rendering, prompts and scope, mechanisms deliberately removed, and follow-ups #1567, #1568 and #1570."
metadata:
  type: project
---

PR #1569 makes `strip_html` (`turnstone/core/web.py`) keep each link's target as `[text](url)`
and rewrites it as one forward scan; the extraction prompt and truncation in `_exec_web_fetch`
changed with it. Read this before changing the link rules or the extraction prompt.

**Rulings (the maintainer, 2026-11-05):**
- A link to a named place in the page renders relative, `[text](#fragment)` (repeating the
  page URL per anchor grew text up to 3.5x with long URLs); an empty href, a bare `#` and
  links to the page itself keep only their text.
- The page and PDF routes share `_web_extraction_instructions`: treat the source as
  untrusted, give each URL exactly as the content has it, resolving a relative one against
  the page URL; the `Page URL` line is the address after redirects, with the requested
  fragment kept.
- `( ) [ ]` are percent-encoded after a target's host; page text that only looks like a
  link stays as written. `<noframes>` content shows; iframe and noembed fallback stays hidden.
- Repeated (text, url) pairs render in full each time.
- Keep the hand-written scanner. An HTML5 parser library is to be evaluated only run in an
  isolated child process, alongside checking answer URLs against the page: #1567. The
  `preview.py` sibling is #1568.
- #1568 (`page_title` and `inject_base_href` in `preview.py`): the linear-time rewrite keeps
  every result the old patterns gave, a scope the maintainer chose over also fixing their
  comment and script quirks. Those quirks are #1570, the first change that would alter what
  the lookups find.

**Deliberately removed, do not re-add:**
- A rule that kept non-ASCII link queries as text on pages not in UTF-8 (a browser encodes
  them in the page's encoding): rare, it had two bugs, and without it a query's bytes may
  differ on old servers, which invents no URL.
- Length caps on the page address and `<base href>`: falling back to the page under a long
  base rendered wrong URLs; the per-target cap and the resolution budget bound both cases.

**Why:** these were settled across three review rounds; each reversal would reopen findings
that rounds already closed. **How to apply:** a change to link rendering re-checks these
rulings first, and model-facing changes get the local end-to-end check in
[[feedback_live_provider_probes]].

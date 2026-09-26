---
name: feedback-context-shares-conservative
description: "Introducing or touching any per-result or per-document share of the context window: default 20%, never 50%; argue any larger number to the maintainer first."
metadata:
  type: feedback
---

No single tool result, and by default no single admitted document, should be allowed 50% of the
context window. The maintainer (2026-09-02, on finding diff_file at the ordinary 50% share): nothing
should be allowed 50% of the context window, and the default should be 20% across the board unless
there is an argument against it.

**Why:** a batch of results must leave room for its siblings and for the
model's own turn; one result also rides the event stream as a single event.
A generous default is the kind of number that ships unexamined because it was
"the ordinary case".

**How to apply:** when introducing or touching a share/percentage of context
(tool-result caps, session ceilings, retention, document budgets), start at
20% and put any larger number in front of the maintainer with the argument, rather
than leaving 50% as the default. Existing exceptions with an argument stated:
the web_fetch extraction-lane document budget and user-attached PDF text
(`_WEB_FETCH_DOCUMENT_CONTEXT_SHARE`, `_PDF_ATTACHMENT_CONTEXT_SHARE`, both
0.5). Verify current constants and their caller-specific rationale before changing those exceptions.

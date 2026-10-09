---
name: feedback_clean_inputs_keep_model_words
description: "Trust-boundary cleaning (fence defang, token removal) near replayed history: clean only incoming text, never a model's words; a framework model gets cleaned input, its output kept."
metadata:
  type: feedback
---

The rule (maintainer, #1291, 2026-10-07): clean what comes in, and never edit what the model
wrote. The fold, the sender-label pass and reasoning replay leave assistant turns, reasoning and
tool-call arguments as written; tool results, attachments and other participants' messages are
cleaned. Outside text that the framework composes into a turn those passes skip is cleaned where
it is composed (`ChatSession._clean_incoming_text`): a compaction summary's verbatim carries, a
hosted search's citations footer, a queued interjection's system turn. A framework model counts
as a model: the compaction summarizer reads cleaned blocks (`_summary_blocks`) and its summary is
saved as written. A side agent caught that cleaning the summary's output edited a model's words;
the maintainer agreed.

**Why:** an honest ledger (the model reads its history as it happened), and the token-keyed trust
declaration holds only if no outside text carries the token in.

**How to apply:** any new path that writes outside text into an assistant or system turn cleans
at composition; any framework model whose output replays gets its input cleaned, not its output;
provider metadata appended to a model's output (a footer) is outside text. Declaration wording
must not be readable as covering where the real fence sits (after user and tool turns, a
web_search tool result included): key distrust on a position the fold never uses ("inside one
of your own earlier turns"), and probe new wording on the local model. Residual, documented:
hosted-search results and citations in native blocks replay as returned. Related:
[[feedback_honest_ledger_over_cost]].

---
name: project_1281_openai_hosted_item_replay
description: "OpenAI Responses hosted-item replay (#1281, 10-05): replay shapes the API accepts, its one namespace rule, why search results/sources are not replayed, the capability gate."
metadata:
  node_type: memory
  type: project
  modified: 2026-10-06T20:30:04.101Z
---

**API facts (live-probed 2026-10-05, gpt-6-astra, `store: false`).** Replayed
`web_search_call`, `tool_search_call` and `tool_search_output` items are accepted in every
shape tried: with or without ids, with reasoning replay off, any status (failed, in_progress,
incomplete), the hosted tool absent from the request, a lone half of a tool search, an empty or
duplicate load, a loaded tool now undeferred or gone, a web search without `action`, and a
`namespace` with no load on the wire. Rejections (400): once a `tool_search_output` has loaded
a deferred tool, a later `function_call` to it without `namespace` ("Missing namespace for
function_call 'X'. It does not exist in the default namespace."), unless the tool is also
offered undeferred; a tool_search_call without `arguments`; a tool_search_output without
`tools`; any id OpenAI did not mint ("Expected an ID that begins with 'ws'", and a right prefix
with foreign characters still fails). A call before the load is fine. A top-level deferred
function's namespace is its own name; a namespace tool's members take the namespace name
(OpenAI's tool-search guide shows both). OpenAI's conversation-state guide says stateless
requests should preserve every output item.

**What a replayed search shows the model (probed 10-05, no search tool on the follow-up):** its
queries and opened pages (it quoted them exactly; +52 input tokens per item). NOT its `results`
or `action.sources`: both come back only via `include` (`web_search_call.results`,
`web_search_call.action.sources`) and are accepted on input but stripped (identical input tokens,
the model reports them not visible). With `store: false`, what a search found survives only in
the model's reply and reasoning. Lesson: an earlier probe "proved" results were visible because
the follow-up still offered web search and the model searched again; probe a replayed tool's
visibility with that tool removed from the request.

**Fix (branch fix/1281-openai-hosted-replay, PR #1285).** Hosted items replay in native position for a
model whose CAPABILITY row runs the tool (not the request's tool list, for prefix stability);
compat endpoints and any provider_name other than `openai` (xAI) replay none. Ids are never
sent: the compat Responses provider reports `openai` and migration 060 tags legacy xAI rows
`openai`, so foreign ids can sit in "native" rows. Items missing a required field are omitted
and a search action of unknown type is dropped, each logged once (INFO). A native call keeps
its namespace; `_namespace_loaded_calls` (in place, so `assistant_item_ends` holds) gives calls
lacking one the namespace of the earlier load. `model_dump` writes `async_` inside loaded tool
definitions; projection respells it `async`.

**Maintainer ruling (10-05): honesty over cost optimizations (HYPOTHESIS.md).** Replayed loads
are NOT trimmed to the tools a request offers and repeated loads are NOT deduplicated: either
rewrites what a past search found. Dispatch refuses calls to tools no longer offered.

**Evidence.** Re-search after a tool search: 3/3 later turns before, 0/3 after. A foreign
call to a loaded tool: 200 with the pass, 400 without. Offline: every stored request on this
lane, rebuilt with both converters, differs only by the added `web_search_call` items. No stored
request on this lane had a tool search fire.

**Why it matters:** a persona visibility set forces client-side tool search, so native
tool-search items never exist in such a workstream; a replayed load cannot re-expose a hidden
tool. A load whose tool is now gone is still replayed (API accepts), but the model does not treat
it as callable: live 10-06, gpt-6-astra never called the gone tool in 4 of 4 runs, even when asked
by exact name; its hosted search found nothing and it declined. Decided 10-06: replayed loads stay
as they were and no note is added when the catalog changes; #1287 makes the dispatch refusal say
the tool is not available, on every lane (reached on Anthropic and local lanes, not on this one).
But nothing tells this lane's model the tool was removed: in 1 of 6 runs, after its search came
back empty, astra called its own earlier, real result invalid. Proposed fix, mirroring #1286: a
"no longer available" stub for each tool a replayed load names that the request lacks; it needs a
live probe of a top-level stub beside the load's namespace (findings on #1281; tracked in #1294).
The context estimate does not count replayed hosted items (#1188 design needed).

**How to apply:** a Responses 400 about a missing namespace is this rule; check that every
call after a `tool_search_output` carries one. Related: [[project_anthropic_deferred_server_tool_calls]].

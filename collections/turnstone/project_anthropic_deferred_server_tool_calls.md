---
name: project_anthropic_deferred_server_tool_calls
description: "Anthropic web_search mixed with client tool calls comes back unrun and runs on the next request; user text before then 400s every request. Wire repair built 10-05, live-probed."
metadata:
  node_type: memory
  type: project
  modified: 2026-10-06T20:10:04.957Z
---

**API rule (documented, server-tools page "Mixing server tools and client tools in one turn";
live-probed 2026-10-05 on claude-opus-5-5):** a response that calls a client tool and a server
tool together ends `stop_reason=tool_use` with the `server_tool_use` UNRUN. The API runs it when
the next request's follow-up holds nothing but `tool_result` blocks (a trailing system message
is fine), and that reply OPENS with the result. Any text after the results ends the turn:
``web_search tool use with id ... was found without a corresponding web_search_tool_result
block``, reported at the API's grouped index (`messages.1` = the whole first tool loop).
Deferred pairs are common in stored history and replay fine when the follow-up holds only
results. The incident was a continuation
request that failed for an unrelated reason, followed by a user message asking the model to
recover: that text landed after the unanswered call.

**Other probed facts:** a result whose `server_tool_use` is not before it 400s (`... must have a
corresponding server_tool_use block before it`). A server result after a client `tool_use` in
the same turn 400s as the client error (`tool_use ids were found without tool_result blocks
immediately after`). A synthesized `web_search_tool_result_error` with code `unavailable`
(documented "an internal error occurred"; an empty list would mean "ran, matched nothing") is
accepted when the pair sits before the turn's client calls. A citation with no result on the
wire is accepted (200).

**Fix built 2026-10-05 (branch fix/anthropic-unresumable-server-tool-use, PR #1282):**
`_pair_server_tool_blocks` in `_anthropic.py` runs on the final converted wire. An unanswered
call that can no longer run gets the `unavailable` result, moved ahead of the first client
call. A non-web_search server call gets dropped (no known error shape). A result without its
call is dropped (the mid-turn compaction split). Placement and merge re-run until stable.
Citations are left alone. The persisted rows are untouched, matching lowering.py's
synth-transient-at-send policy.

**Evidence:** live end-to-end through `create_streaming`. The incident request and a
real compaction split both 400 on dev and 200 with the fix. Offline: every historical request
point from `conversations` was rebuilt with the dev converter (`git show dev:...` via importlib)
and the fixed one; the outputs were identical except for the stuck workstream. Reuse this
instrument for converter changes. Behavior: across 4 variants x 2 scenarios x 5 samples
(unavailable / dropped / with or without an operator note), the model re-searched 40/40 and
never claimed search was down.

**Why not keep pairs whole at compaction:** deferral chains run 1-4 steps. Keeping them would
retain tens to hundreds of thousands of extra characters in the tail and defeat a mid-turn
compaction.
The summarizer never reads server-tool blocks anyway, so the dropped results lose nothing a
summary keeps.

**Adjacent, not fixed:** approval feedback ("y, use full path") is folded as a USER turn after
the tool results (session.py "Seam 2"). That closes such a turn in NORMAL operation: dev bricks;
the fix answers the search `unavailable` instead of running it. Probed 10-05 (opus-5-5, 5 samples
each). Feedback INSIDE the tool_result keeps the turn open (the pending search runs) and steering
feedback is followed ("pass verbose=true" 11/12). Feedback adding a NEW step ("run lint first")
is ignored 0/10, with the model saying it came from the tool output, not the user. As user text
after the result (today) or as a system note, it was followed 5/5; the system note also keeps
the turn open. So moving feedback into tool results regresses the feature. The system-note route
works on native rows but lifts user text to operator role, which conflicts with the "genuine USER
turn" ruling at the Seam 2 site, and the fold path would put it inside the tool_result anyway.
`pause_turn` is unhandled (raw reason ends the turn). Retry re-runs from the last user message.
(The missing `tool_search_tool_result` block type first noted here was fixed in the same branch;
see "Native tool search" below.)

**OpenAI Responses lane has no analog (checked 2026-10-05):** hosted web search runs inline.
Every stored `web_search_call` is `completed`, even in turns that also return function calls.
Turnstone never replays hosted items ("Hosted tool output remains omitted"), with `store: false`
plus encrypted reasoning. OpenAI's own pairing rule (a reasoning item needs its required
following item) tolerates the omitted search: in stored gpt-6-astra history with replay on,
requests carrying many such reasoning items all succeeded, and a live replay of one of them on
10-05 returned 200. Chat Completions lanes have no hosted tools.

**Native tool search (review round 1, fixed in the same branch on the maintainer's P0 ruling).**
`tool_search_tool_result` was missing from `ANTHROPIC_VALID_BLOCK_TYPES`, so dev filtered it out.
Live probe: the first follow-up still worked (200) because the API re-ran the search, but every
later request 400'd (`tool_search_tool_bm25 tool use ... without a corresponding
tool_search_tool_result block`). Any workstream where native tool search fires (more than 20
tools, `auto`) bricked. Probes on 10-05: replay with the result kept passes on later turns; a
delayed tool-search call answered with `tool_search_tool_result_error` / `unavailable` passes;
a deferred tool used after its search was dropped passes (the model re-searches). OpenAI hosted
tool search (`tool_search_call` / `tool_search_output`, omitted on replay) is accepted on later
turns too, but the model re-searches 3/3; replaying them needs the function_call's native
`namespace` (else 400) and then stops the re-search (0/3). Filed as #1281 (separate PR); see
[[project_1281_openai_hosted_item_replay]].

**Round 2 (10-05).** The maintainer resumed the stuck workstream on the branch, and the model
itself caught a misleading history. The API shows `unavailable` as "The web_search tool is
unavailable. Do not try to use it again this turn." Interleaved repairs (call, error, call,
error) made two parallel searches read as a retry after being told not to: the model said so
5/5 when asked. Grouped (calls, then errors, the API's own parallel shape): 0/5. So answered
calls go as one group. The API also rejects a SECOND result for an answered call (live 400).
Pre-fix tool-search histories contain that, because the API re-ran the search. A kept result
now uses up its call (`awaiting` set). One registry (`_SERVER_TOOL_RESULT_TYPES`) drives the
valid set and the answers. Lesson: probe the model's reading of a repaired history, not only
API acceptance.

**More probes (10-05, claude-opus-5-5, while scoping #1281).** Server blocks in history are
accepted when the request no longer offers that server tool (web_search, tool search). Replayed
search results ARE in the model's context (one search: 7,417 input tokens vs 436 without the
blocks), unlike OpenAI. But a replayed `tool_search_tool_result` whose `tool_reference` names a
tool the request does not offer 400s ("Tool reference 'X' not found in available tools"), with or
without the tool search tool: an MCP server going offline, or another user's per-user tool on a
shared workstream, would fail every request once #1282 replays the result. A stub definition
with that name ("This tool is no longer available.", deferred or plain) is accepted; the model
still tried to call it once. A thinking block with a signature another endpoint produced
(bogus or empty) 400s ("Invalid `signature` in `thinking` block"): `anthropic` and
`anthropic-compatible` share one replay family, so with reasoning replay on, a compat lane's
thinking blocks would brick a later Claude request.

**Follow-up (PR #1286, built on #1282 at 0780c10d).** The provider appends a plain stub
("This tool is no longer available.", empty schema; plain because an all-deferred tool list
400s) for each `tool_reference` name the request's tools lack, one per name, logged once per
(name, search id). The session's client-side tool-search branch also offers the deferred
definitions of tools that replayed native searches loaded (active lane's replay family only,
read per request, never recorded as discovered, persona filter still applies), so only names the
catalog lost get stubs. One shared reader, `tool_search_references` in `_anthropic.py`, feeds
both. Review lesson: "not in this request" is not "gone" on a client-side lane. Persona fact
(corrected 10-05): most personas are unrestricted (`tool_allowlist` NULL, so `_persona_tools`
is None), and native tool search runs in those sessions; only an allowlist forces client-side
search (or none without `tool_search`). Stamps are immutable and forks copy them verbatim
(`clone_workstream_transaction`). Dispatch (`_prepare_tool_item`) does not check the allowlist,
BY DESIGN: docs/personas.md says visibility is behavior shaping, not a security boundary; approval,
judge, policy and RBAC enforce. Probe 10-05: Claude, astra and local Qwen all declined to call an
unoffered tool under injection (0/9). Do not report it as a gap.

**#1287, re-scoped with the maintainer 10-06.** Lane parity is not a goal: the stub exists only
because the API 400s without a definition, and the model called it anyway (3/3). The real gap is
that catalog swaps are silent on every lane (`_on_mcp_tools_changed`; the catalog follows the
sender via `bind_acting_user`, so shared workstreams and coordinators swap it routinely). The fix
belongs in the dispatch refusal (`_prepare_tool_item`), which reads as a misspelled name and
lists every built-in preparer plus the sender's MCP tools instead of the tools offered. A system
note at swap time was considered and not preferred: MCP thread mid-turn, a note pair at each
change of sender, and no sign a note before the call changes behavior.

**#1287 as built (10-06).** `_unavailable_tool_error` lists the offer outright (active tools minus
deferred and revoked; a task agent's own list rides `_prepare_tool_for_principal(offered=)`),
points to tool search for deferred tools, names "another user" as a cause only once
`_shared_workstream` latches (a live Qwen reply passed that guess to a one-person chat), and drops
"misspelled" for an exactly offered name. Live smoke through real `ChatSession` turns: Qwen and
claude-opus-5-5 called the gone tool and explained the refusal accurately; probe B, neither
claude-opus-5-5 nor gpt-6-astra called an unloaded deferred tool directly (declined, or searched
first), so listing deferred names would be safe but saves nothing; left to tool search. Ruled by
the maintainer: the list's two unlocked catalog reads can skew one refusal under a concurrent MCP
publish, which is accepted as eventual consistency; do not re-raise it in review.

**How to apply:** a 400 naming a `srvtoolu_` id is this class. Look for a `server_tool_use`
without a later result before suspecting the stream accumulator, which keeps every raw block.
Related: [[project_server_tool_usage_inflates_context]],
[[project_mid_conversation_system_messages]].

---
name: project_1201_deepseek_responses_reasoning_replay
description: "PR #1201: DeepSeek 'reasoning_text must be passed back' 400 on Responses tool rounds; the author rewrote it 09-25 into a first-class switchyard provider."
metadata: 
  node_type: memory
  type: project
  modified: 2026-09-26T00:43:40.141Z
---

**Superseded PR content (2026-09-25):** the author (RedEyeNinja-BKK) replaced the branch with one
commit, 2e96c821 on dev 02f3e652: a first-class `switchyard` provider (`_switchyard.py`, joins
LOCAL_PROVIDERS, explicit `api_surface` chat/responses, passes a native reasoning item through
whole, drops and reports foreign replay state). The synthesis fix analysed below is gone; the
replay research moved to #1202 and #1203. Max review run 2026-09-25 (15 findings; JSON kept at
the session scratchpad only). Verdict facts, re-measured on 2e96c821: the reasoning "crossing"
(~300 of 413 lines, ~535 test lines) changes no request byte (0 diffs in 84,860 builds vs an
identity bypass); the only wire-affecting line is the `provider_name` override, which makes
`switchyard` a new producer stamp, so moving a live Responses row to or from openai-compatible
drops every earlier reasoning item and the assistant `phase` (the DeepSeek 400 again). The loss
report has no reader and is inaccurate; default posture still replays nothing
(OPENAI_COMPAT_DEFAULT.supports_reasoning_replay=False). Lower-altitude fix the review proposed:
give compat Responses lanes their own producer identity (or derive native_producer from the
lane binding) instead of a new provider name — which key is right stays open (a per-alias key
would break intended sharing), so don't ask the contributor for it.

**Reply-alignment facts (Fable-checked + re-verified 09-25):** the PR's `_switchyard.py:3`
docstring credits "maintainer direction, 2026-09-21 — Turn IR -> lowering -> provider"; no
maintainer text says that (the phrase is docs/architecture.md's layering description) — a reply
must disown it. Public precedent: #1077 (eous 09-05, not_planned: existing configurable
OpenAI-compatible path, no dedicated integration; cite the principle) and #710. #1203's own data shows the parent
adapter replays native items unchanged, contradicting the PR's "dismantled" premise. Literal
replay recipe on dev: Models-tab definition (config.toml cannot set `replay_reasoning_to_model`),
provider openai-compatible, capabilities JSON `{"server_compat": {"api_surface": "responses"},
"supports_reasoning_replay": true}`, replay toggle on; never run live against DeepSeek by us.

**Decision 2026-09-25 (the maintainer):** reply posted as issuecomment-5841628268 and the PR closed:
named provider declined (#1077 line), docstring attribution disowned, "dismantled" premise
answered with #1203 data + the row-move finding, the openai-compatible recipe given (hedged), the
identity wart acknowledged with no schedule, live DeepSeek acceptance invited on #1202; caveated
as preliminary (Switchyard not yet run by us). Switchyard internals (read at 9cf6fadf, 09-23):
capabilities are route-level reject-only gates (tool_calling/reasoning/vision; context_window
advertised, not enforced), targets carry no capability data, routing is mostly two-tier
(stage_router heuristics, LLM-judged solve probability, escalation); N-way only via custom
llm_classifier groups or the experimental prefill_router. No capability matrix.

Investigated 2026-09-20 for the maintainer, who asked whether the report was a real bug, user error,
or a router bug.

**Upstream facts.** The 400 text `The reasoning_text in the thinking mode must be passed back to
the API.` is DeepSeek's own (V4 thinking mode on its Responses-compatible endpoint; the chat
surface says `reasoning_content`). Documented contract: once `tools` is present, every assistant
turn must carry reasoning; an EMPTY reasoning value is accepted (chat surface, community curl).
Not a router bug. The author (RedEyeNinja-BKK) runs api.deepseek.com direct HTTPS (#937).

**Turnstone facts (verified by code + hermetic run).**
- Responses lane replays reasoning only from a native `reasoning` block with a string `id`,
  same producer (`_assistant_items_for_input`); chat-lane `reasoning_text` synth blocks and
  Anthropic `thinking` blocks are NOT replayed. Replay needs BOTH `replay_reasoning_to_model`
  (alias flag, default off) AND `supports_reasoning_replay` (no DeepSeek caps row → only via the
  capabilities JSON override). With either off, EVERY DeepSeek thinking tool round 400s.
- Compaction does NOT produce the PR's claimed shape: `_compact_messages_impl` emits
  `[summary_user, summary_asst(text only)] + preserved tail (verbatim, native reasoning intact)`;
  reopen rebuilds `[label, marker-as-assistant, tail rows]`. The real post-compaction history
  still replays the tool-call turn's `rs_` item (demo: dev == PR output on that shape).
- Reasoning-less tool-call turns DO arise from cross-lane/cross-surface resumes (goldens
  `native_reasoning`/`native_orphan` are Anthropic-shaped turns on the Responses lane) and any
  turn where no `reasoning` item was captured.
- The PR's fix inserts `{"type":"reasoning","id":"rs_roundrepair_<sha>","content":[reasoning_text]}`
  with NO `encrypted_content` while `_build_kwargs` always sends `store: false`. Real OpenAI rejects
  an unpersisted `rs_` id under `store:false` (`Item with id 'rs_...' not found. Items are not
  persisted when store is set to false`), so the fix trades a DeepSeek 400 for an OpenAI 400 on the
  same shapes (goldens are `gpt-5` requests). Unverified: whether gpt-5.4+ at effort `none`
  emits reasoning items (if not, every tool round on that default would hit it).

**Why:** the review question recurs (DeepSeek/Kimi-style "reasoning must be passed back" rules
vs OpenAI's item-id validation); the two contracts conflict on the same wire.
**How to apply:** a fix must be provider-scoped (DeepSeek/compat only, never the commercial
OpenAI lane) and prefer an empty reasoning value over placeholder prose; a candidate root-cause
lever is replaying the chat-lane `reasoning_text` synth block on the Responses surface.
Related: [[project_973_no_thinking_posture_hosted_lanes]], [[feedback_measure_before_accepting_a_finding]].

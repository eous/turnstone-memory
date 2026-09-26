---
name: project-965-reasoning-seam
description: "#965 inline <think> segregation: SHIPPED as PR #970 (2026-08-04); run-bounded split inside drain_stream, orphan closes pass through; replay residual is #971."
metadata: 
  node_type: memory
  type: project
  modified: 2026-08-05T07:21:09.300Z
---

#965 (inline-reasoning segregation at the Turn-IR seam; closes #940). Design +
two-agent gap verification DONE 2026-08-04. Design: local
`docs/design/965-reasoning-seam.md`; full interaction graph:
`docs/design/965-dataflow-map.md` (dataflow-mapper output, 10 edges, all
dispositioned). Lineage: [[project_937_midstream_transport_retry]] (the
filing session), #827 closed / #832 open.

**Design decisions (rationale in the doc):**
- Home = INSIDE `drain_stream` between content join and citations-footer fold
  (_protocol.py ~298) — footer is web-controlled text and must never be
  scanned; post-drain placement can't distinguish it. NOT model_turn.
- One-shot `split_inline_reasoning(text) -> (content, reasoning)` lives in
  `streaming_text.py` beside the splitter. Fast path = byte-identical when no
  tag present. **Orphan-close seed rule**: earliest tag in text is a CLOSE →
  start in_think=True (chat-template pre-injected `<think>`; title lane's
  rfind defense promoted to the seam; streaming form cannot do this).
  `.strip()` only when extraction fired. MUST call flush_pending (12-char
  carry). Extracted appends AFTER server-parsed reasoning → rides
  finalize_provider_blocks → reasoning_text synth → native lane; model_turn
  needs ZERO changes.
- Deletions: title strip + orphan-close loop (session.py:3979-83), summarizer
  (:8923), `_strip_reasoning` (:7788) + comment ~950, AND **optimizer's 5
  private regexes** (309/459/801/918/1060). ThinkTagSplitter import stays
  (interactive 8103). Perception keeps its whitespace strip.
- In-scope riders: perception `describe_cached` must NOT cache empty text
  (module-global cache, no invalidation path — think-only pass would poison
  permanently); synth-bail gets a chars-only debug log (never log reasoning
  text — audit-log-discipline pin).

**Issue-audit corrections (post on the issue at PR time):** optimizer row
"no strip" is WRONG — 5 cross-vocab regexes, grep-blind because the pattern
`<(?:think|reasoning)>` never contains literal `<think`. Lesson: grep audits
miss non-literal constructions of the searched token. task_agent has a 4th
read (salvage :17741-44 via t.text); judge also reads at 1474/1480/1530.

**Emptiness reclassification** = biggest delta class: think-only responses
now yield EMPTY content in 7 lanes; every `or`-fallback branch becomes
reachable. Notables: web_fetch flips to honest error card (is_error=True —
release-note); intent judge takes the empty-retry ladder (up to 3 extra
calls, no turn budget); optimizer `:457` observer-WIPE latent bug fixed by
side effect, `:1056` empty-prompt tree node → honest run stop; textless-final
walk class (optimizer analyst, eval _finish) gains all-think members → can
select an OLDER turn's text (named, not fixed — the maintainer may rule).
`{"content":"", "tool_calls":[...]}` wire shape closed by prevalence
(every prose-less tool turn today).

**R1 residual [HIGH] → FILE FOLLOW-UP ISSUE at PR time**: anthropic-compatible
lane replays `_provider_content` verbatim (_anthropic.py:648-49); raw text
block keeps tags (:1062-70); replay strip covers only thinking/redacted. So
drained MULTI-TURN loops (task_agent/judge/optimizer/eval) on that lane still
replay tags intra-loop, and the reasoning_text synth drops as foreign. All
CONTENT exits are fixed regardless (= the #940 harm). Fix is adapter-side
native-lane policy on unsigned text blocks — own issue, not a rider.

**R2 accepted**: literal `<think>` in legitimate prose is misrouted (content
truncated at the tag) — same family as the field-proven interactive splitter;
SOFTER than today's title/summarizer strips (text preserved in reasoning lane
vs deleted); new only for the 7 unstripped lanes.

**Riders approved by the maintainer 2026-08-04 (aiming for the best outcome, not the minimum)**: A =
`last_assistant_text()` → trajectory.py (3 sites: optimizer :794, eval :784, task_agent salvage
:17741 — names the textless-final class, one home); B = guard :599 getattr → typed access; C =
**inline-reasoning dialect conformance catalog** (`tests/_reasoning_dialect.py`: case table of
dialect utterances → expected lanes; ONE shared `think_tag_provider()` fake; splitter one-shot,
drain, per-lane pins, and later #832 streaming pins ALL draw from it). The maintainer's insight: C
is the test-side mirror of the Turn IR dialect concept — HYPOTHESIS.md grounding now a design-doc
section (segregation = a piece of readout R mis-located into 9 consumers; R1 = a #699-family
native-lane leak, cite in follow-up issue). Deferred to own rounds: JSON-from-LLM-text unification
(guard/judge/optimizer 3 impls, behavior-touching), RecordingUI consolidation (#937 follow-up).

**Test intel**: 3 title tests (test_session.py:1799-1885) route through
drain_stream and pin the seed rule for free (hand-traced by mapper);
test_drain_stream.py:245-256 already pins footer-only byte-exactness;
compaction suites patch `_utility_completion` so the summarizer pin needs a
real fake provider; only 4 test files contain literal tags. Guard-judge
`empty_response` persists as tier="llm_error" (distinct, non-shadowing,
session.py:10367-79). Favorable: seam STRENGTHENS
test_reasoning_audit_log_discipline (title/judge/eval/optimizer log sites).

**IMPLEMENTATION (2026-08-04, branch `fix/965-reasoning-seam`)**: COMMITTED
`a949c6c3` (21 files, +796/−106), NOT pushed. Full suite 10,583 passed
(main baseline 10,518); only failures = the 3 environmental
test_server_live items, identical on main. ruff+mypy green. Queued for PR
time (the maintainer's go): push, file R1/#699 follow-up issue, correct the #965
issue table (optimizer row), release notes (web_fetch error-card flip,
cross-vocab close). **Debug lesson worth its
weight**: first full-suite run failed 6 `test_sse_recovery_e2e` tests via
ORDER interference — root cause: `create_provider("openai-compatible")`
returns a PROCESS-WIDE SINGLETON, and `_make_session()` over a MagicMock
client resolves it as `session._provider`; my tests wrote
`session._provider.create_streaming = MagicMock(...)` → poisoned every later
session in the run (e2e servers resolve the same instance; their scripted
flows never fired → 45s predicate timeouts ×6). Fix = per-test provider
fake object assigned to `session._provider` (judge-suite pattern);
`_seam_provider` helper docstring in test_session.py records the rule.
NEVER mutate attributes on a session's resolved provider in tests.
Attribution method that worked: isolated-file runs pass ≠ innocence — run
[my tests + victim suite] pairs, then bisect to one test, then probe
process globals (threads clean → provider singleton identity check).

**XHIGH REVIEW ROUND (2026-08-04, review run): 15 findings (12 correctness,
3 cleanup), all fixed same round.** HEADLINE REVERSAL: **the orphan-close
seed rule was DELETED** — it was my scope creep beyond the issue's
feed+flush proposal, and review CONFIRMED by execution that a quoted
`</think>` in web-controlled text (page cited by web_fetch, content echoed
by the guard judge) wiped everything before it. Rule now: orphan closes
pass through byte-identical (quoted-tag safety); title lane reinstated its
LOCAL rfind peel as display formatting (carve-out: cosmetic peeling ≠
segregation). Quoted-OPEN truncation retained as R2 (interactive parity;
guard degradation fail-safe). Other fixes: or-fallback ordering
(normalize-then-fallback, both optimizer sites — whitespace-only +
fence-on-fallback); footer NEVER folds onto empty content (replaced the
old byte-match pin consciously); analyst/eval read LAST turn only (no
walk-back — stale narration must never pose as the diagnosis);
last_assistant_text = salvage-only, strip-aware; perception bounded
negative cache (_EMPTY_RETRY_LIMIT=3); reasoning append "\n\n" boundary;
summarizer local .strip(); synth-bail log moved to drain_stream
conditioned on inline-extracted+native-block (model_turn version fired
every routine Anthropic/Responses turn); REASONING_BEARING_BLOCK_TYPES
moved to _protocol. **Durable lesson: a "whole-text-only rule" the
streaming form can't express should have been a red flag — divergence
from the field-proven form was itself the bug.**

**XHIGH ROUND 2: 13 distinct (all in round-1 fix code — the
seam held); 12 fixed, 1 no_change_needed (summarizer any-close = the ruled
cross-vocab delta).** Fixes: footer guard blankness not truthiness;
residue trim BY LINE (`strip_blank_edge_lines` — .strip() was eating
code-block indentation); `_empty_counts` capped + heal-on-hit;
`final_assistant_text()` in trajectory.py (analyst+eval adopt; kills the
unpinned-rewrite gap AND the dup); `_strip_markdown_fence()` one rule for
4 optimizer sites; `has_reasoning_bearing_block()` + `_logger()` in
_protocol; drain docstring conditional-fold contract; EQUIVALENCE_CASES
alias dropped; docstrings narrowed. **TWO DEBUG GOTCHAS**: (1) `ruff
format --check` belongs in the gate run — Bash/python3-script file edits
BYPASS the format hook (Write/Edit trigger it, scripts don't); (2) the
working copy was found checked out to MAIN mid-session (reflog: external
checkout after my amend) — my first format-gate probe measured main and
"refuted" a real finding. ALWAYS `git branch --show-current` before
probing a finding against the tree.

**XHIGH ROUND 3: 8 distinct (3 correctness, 5 cleanup), 0
refuted; all fixed.** HEADLINE: **run-bounded splitting** — drain closes a
content run at interleaving signals (tool-call deltas, reasoning_delta)
and splits each run independently, mirroring interactive's
flush-and-reset; my original "the whole content string splits
identically" analysis was WRONG (unterminated `<think>` before tool calls
swallowed the post-call answer). **Durable lesson: an equivalence property
fed only content-only streams is structurally blind to interleaved-shape
divergence — parity proofs need the full signal alphabet.** Other fixes:
perception counter pressure MEMOIZES (never evicts live counters — churn
eviction re-billed forever); `extracted.strip()` gate; server.py notify
hook = the THIRD hand-rolled final-say walk, adopted final_assistant_text
(deltas: Turn.text ""-join flatten + whitespace→fallback, pinned);
think_tag_stream adopted in optimizer suite; ALL_TAGS; footer check
behind `trailing_info_parts`. Round trajectory 15→13→8; round 4 =
convergence candidate.

**XHIGH ROUND 4: 3 distinct (2 correctness, 1 cleanup), all
fixed.** Both correctness = round-3 segmentation composition bugs: (1)
combined content+tools chunk closed the run BEFORE feeding its content
(interactive order: reasoning→content→tools; a same-chunk `</think>`
stranded as a literal orphan); (2) per-run edge trim ate genuine
paragraph separators at run boundaries (fix: split runs `trim=False`,
join, ONE outer strip_blank_edge_lines when any run consumed).
Cross-referencing docstrings for the same-named console dict-walk
(`coordinator_client._last_assistant_text` — deliberate list-content-skip
+ tri-state, kept divergent). Trajectory 15→13→8→3. **Working in
dedicated worktree scratchpad/ts-965 now — the shared /mnt/git checkout
was externally switched to main TWICE mid-session; worktree needs `uv
sync --all-extras` (extras-pruning gotcha) before mypy.** Round 5 =
convergence candidate again.

**XHIGH ROUND 5: 6 (4 correctness, 2 cleanup) —
SIMPLIFICATION ROUND.** Trajectory 15→13→8→3→6; the rise = the perception
retry ladder's THIRD consecutive round of confirmed races →
[[feedback_nonconverging_reviews_mean_simplify]] applied: **ladder
DELETED** (counter/limit/pressure/heal all gone) → simplest race-safe
semantic: memoize every completed result immediately incl. empty, ONE
commit-lock guard (empty never clobbers a racer's real description — a
race that exists on MAIN, now closed); transient-empty pin residual
ACCEPTED (= main's shipped behavior; remediation is server-side,
live-verified). Also: blankness gates completed on task_agent ×3 +
web_fetch (inherited gap); consumed-detection = total-length compare;
shared `seam_provider()` fake. **Durable lesson: a mechanism that
generates confirmed findings in three consecutive review rounds is
itself the bug — replace it with the semantics you can hold in one
lock, don't patch the fourth race.**

**SHIPPED 2026-08-04**: PR #970 (base main), commits `9d224a32` (the
campaign, squashed) + `99660fd9` (title both-vocabulary pin). CHANGELOG
Unreleased→Fixed carries both release notes (web_fetch error-card flip,
cross-vocab close). **R1 residual filed as #971** (anthropic-compatible
native lane replays tags in drained multi-turn loops; #699 family; live
vLLM `/v1/messages` exhibit + full surface matrix in the issue body).
Audit-table correction posted on #965 (optimizer row: 5 private regexes,
grep-blind because `<(?:think|reasoning)>` contains no literal `<think`
— audit for what code DOES, not the token it matches).
**Copilot PR review: 1 inline finding, REFUTED** — claimed the title
lane's per-vocabulary peel loop double-peels and can discard title text
between `</reasoning>` and `</think>`. It cannot: after cut 1 the
remainder begins after the last `</think>`, so a `</reasoning>` still in
it is necessarily later ⇒ the sequence ≡ one cut after whichever close
is last. Proved by exhaustive token arrangements + 200k randomized
fragment strings (probe: scratchpad/probe_title_peel.py), replied with
the argument, thread resolved. The equivalence WAS unpinned though →
`99660fd9` adds both orderings ([[feedback_docs_are_not_review_immunity]]
in action: a refuted finding still earns a pin when it exposes missing
coverage).

**XHIGH ROUND 6: FIRST ZERO-CORRECTNESS ROUND — 4 cleanup
only, all fixed.** Headline: the amended commit MESSAGE still described
the deleted retry ladder (amend --no-edit through design churn = artifact
drift; **lesson: re-read the commit body after every simplification
round**). Also deletion-first again: `trim=` parameter REMOVED —
split_inline_reasoning is a pure raw split (equivalence property now
EXACT), drain owns the tree's single trim; `_non_blank_or()` helper;
test hygiene. **Shell-script edits kept silently no-oping on
formatter-reflowed blocks (s.replace mismatches print success anyway) —
use Read+Edit for surgical test/code changes, scripts only for
verified-unique replacements.** Trajectory 15→13→8→3→6→0c. Round 7 =
closing convergence round.

**LIVE VALIDATION (2026-08-04, the maintainer's LAN proxy)**: endpoint =
LiteLLM gateway → `anthropic/qwen3.6-27b` (anthropic-surface backend, no
reasoning parser). Findings: (1) raw NON-streaming = the orphan-close
dialect 6/6 runs (no open tag — template pre-injects; `</think>` +
answer) — the seed rule's exact field case; (2) **modality asymmetry**:
on `stream=true` the SAME server emits NO tags and NO reasoning field —
pure untagged narration in content (verified raw urllib, zero turnstone
code). Since every turnstone path streams (post-#831), THIS server config
never shows turnstone a tag — untagged narration has no in-band signal
and is out of any tag-based rule's reach (server-side remediation:
backend reasoning parser → Path 1, or a tag-passing server à la #940's
LM Studio). (3) Live-derived replay: real captured tagged bytes through
production model_turn in 5 random chunkings → content == answer exactly,
reasoning → native reasoning_text, 5/5 PASS. Initial smoke "FAIL" was a
wrong expectation (fast-path passthrough of untagged content is CORRECT),
not a code failure.

**Port-8000 attribution (vLLM direct, same session)** — full surface
matrix for parserless qwen3.6-27b: chat surface = untagged narration BOTH
modalities (no signal ever); **/v1/messages NON-stream = orphan `</think>`
INSIDE a plain text block** (the R1/#699 exhibit shape, live); /v1/messages
STREAM = untagged text_deltas — so the modality asymmetry is vLLM-internal
on the anthropic surface, and LiteLLM :4000 was translating faithfully.
Since turnstone always streams, THIS server never shows turnstone a tag on
any lane. anthropic-compatible lane validated live end-to-end (model_turn
over /v1/messages: content+native+finish+usage healthy). **Remediation
VERIFIED live**: `chat_template_kwargs {"enable_thinking": false}` →
clean 225-char answer, no narration — supported today via ModelCapabilities
thinking_mode="manual" + template key, i.e., a model-definition fix, no
code. Probe scripts in session scratchpad (probe_965_modes/stream,
live_965_replay, live_965_anthropic_lane).

**#827 mined (the maintainer's pointer, 2026-08-04)** — same-shaped closed campaign;
four patterns adopted into the design: (1) "decisions for review to hold the
line" block (6 lines: seam stays policy-free / NO operator toggle — parity
with interactive / no per-lane variants / provider_blocks untouched here /
vocabulary frozen / deletion set TOTAL); (2) acceptance-coverage audit table
mapping #965's acceptance items → design sections with named deviations
(title deltas ×3, synth-bail residual, web_fetch reclassification
release-note) — the #831 "deviation noted in PR" discipline; (3) #827's
four-role caller taxonomy (γ-judges / π-utility / child-harness task agents /
meter eval) explains formally why one readout pass covers nine lanes; (4)
optional NON-GATING live smoke on dev-node Qwen3-class server (the "1c"
pattern — never a push blocker).

Stale-doc hazard: `docs/design/opus5-seam-graph.md` cites dead line numbers +
a phantom doctor.py lane — do not cross-check against it.

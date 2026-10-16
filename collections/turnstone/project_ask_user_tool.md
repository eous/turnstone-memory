---
name: project_ask_user_tool
description: "#1340 ask_user tool (branch feat/ask-user-tool, 2026-10-09): the rulings (non-blocking, bottom pane, preview in v1, top-level web and CLI only) and why it does not ride the approval gate."
metadata:
  type: project
---

A built-in interactive tool that shows the user one to four multiple-choice questions, each with
an optional per-option preview, a free-text "own answer" field, and a "Let's talk about it"
escape. Scoped 2026-10-09 on branch `feat/ask-user-tool` (base a937e6ad on dev). The LOCAL design
note is `docs/design/ask-user-tool.md` in that branch's checkout; the public form is issue #1340.

**Rulings (the maintainer, 2026-10-09):**
1. Non-blocking: the tool call returns at once with a note telling the model to end its turn; the
   answer arrives as the user's next message. No pause primitive, no answer endpoint, no timeout.
2. The form is a pane BELOW the conversation (the preview pane's pattern with a "down" split;
   `openPaneBeside` is hard-coded to "right" today and grows a direction argument).
3. Per-option preview is in v1 (markdown through the sanctioned renderer lane).
4. Offered only to top-level interactive sessions with the web or CLI client type: not chat or
   scheduled client types, not coordinator-spawned children, not coordinators or task agents. The
   executor returns an "unavailable" note as a backstop elsewhere.
5. Any participant who may send a message may answer; the answer is an ordinary user turn, so
   sender attribution is the existing one ([[project_multiuser_attribution_ux]]).

**Design facts worth keeping.** The first draft blocked the executor on a cycle in the approval
registry. It deliberately did not ride the approval gate itself because the gate has many paths
that resolve a pending item with no human (intent judge, Smart Approvals, tool policies,
skip-permissions, Always grants, the unattended grant after a watch restore, channel-bot and eval
auto-approve), each of which would have answered a question with nothing. The maintainer then
asked whether blocking was an assumption; it was, and dropping it removed the whole pause
primitive. The descriptor rides the tool turn's meta side channel as a sibling of the preview
descriptor ([[project_preview_pane]]) rather than overloading it: previews carry a content-addressed
blob and the question has no bytes. The `on_tool_result` keyword ripple across every UI
implementer and test stub is the same class of change open_preview made.

**Why:** these settle the shape; re-asking costs the maintainer a round.
**How to apply:** build to the rulings; raise only new decisions. The note lists seven minor ones
with recommendations (descriptor channel, direct send, pane auto-close, preview rendering, split
ratio, tool-search threshold at 20 built-ins, the optional header label). Related:
[[feedback_minimal_scope_first]], [[feedback_push_back]].

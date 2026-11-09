---
name: project_tool_call_full_view
description: "Full tool-call view on web cards (1.9.3, 2026-11-03): rulings (inline, separate arguments/result controls, stored result only) and the arguments-field boundary."
metadata:
  type: project
---

The community's top 1.9.3 request (2026-11-03): see a tool call's complete arguments and result on
the web cards. Before this, text was cut in four places: each tool's preparer in
`core/session.py` (MCP values at 200 chars, web_fetch URL at 80 with no ellipsis, queries at 80),
the interactive history replay (`synthToolItem`, 77 chars + "..."), the coordinator pane (the
one-line header only, CSS ellipsis, never the preview), and the coordinator's 64 KiB result cap.

**Rulings (maintainer, 2026-11-03):**
- **Inline**, not a dialog or side pane.
- **Separate controls.** "full call" on the call line opens only the complete arguments; each
  result box has its own expand/collapse, shown only when the result overflows its box. One button
  for both was chosen first, then reversed: checking a file path would unfold a 3,000-line read.
- **Stored result only.** The UI shows every character the model saw. Executor output past the
  model's context budget is still discarded by design (#883); storing it was offered and declined
  for 1.9.3.

**Boundary:** the workstream's own live tool events gain `arguments` (the model's raw text, the
same string `/history` already serves from the stored turn). Every other surface that carries a
pending approval (the node-level `approve_request` event, the `/v1/api/dashboard` payload) stays
header/preview only; don't widen them without a ruling.

Non-goals for v1: CLI and Discord/Slack cards, rewriting each preparer's one-line summary, copy
buttons, the coordinator children-tree approval block.

**How to apply:** when touching tool-card rendering, keep one builder per concern in
`shared_static/conversation.js` so both panes, replay and sub-agent rows share it
([[feedback_task_agents_share_main_paths]]); keep [[feedback_minimal_scope_first]] for follow-ups.

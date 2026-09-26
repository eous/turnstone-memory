---
name: project_command_verb_lift
description: "/rewind or /retry handlers or a Copilot /route/ auth-bypass flag: #549 DONE via PR #598; keep bare .msg.user rewind selector; the flag is a false positive."
metadata: 
  type: project
  modified: 2026-07-20T16:59:43.414Z
---

**DONE — issue #549 (2026-05-29).** PRs #595 (REST-first history convergence) + #596 (history wire-shape unification) + #598 (the verb lift, Closes #549) + #600 (affordance-CSS consolidation) all merged. (File renamed 2026-07-01 from `project_command_verb_unlifted.md` — the "unlifted" name described the pre-fix state.)

Durable decisions/patterns:
- `/rewind` (body `{turns:N}`) and `/retry` (no body) are now path-keyed handlers in `SharedSessionVerbHandlers` (`session_routes.py`), templated on `make_close_handler`/`make_cancel_handler` — same mold as cancel/approve/close. The old body-keyed `/v1/api/command` rejects rewind/retry with HTTP 400 (BREAKING). The CLI string path (`session.handle_command` branches) is KEPT for the terminal.
- Handler mutates `session.rewind(n)`/`.retry()` DIRECTLY (not `handle_command`), always emits `clear_ui` (incl. rewind-to-zero, per PR #503), audits `conversation.rewind`/`retry`.
- Perm gates: interactive = in-handler `conversation.modify`; coord = `admin.coordinator` (parity with coord's other verbs).
- Frontend: interactive (`class Pane` — **moved `ui/static/app.js` → `shared_static/interactive.js` = `window.InteractivePane`** in L-shell 5a; the window bridge was later retired when both deployments went ESM) and coord (`coordinator.js`, module closure) are SEPARATE — coord got a local mirror (factored `refetchHistory()` out of `init()`, `clear_ui`/`replay_truncated` cases). Affordance CSS lives in shared `chat.css` (#600 verbatim move; the design-token vocab is distinct values, not aliases).
- Rewind turn-boundary selector is bare `.msg.user` (counts system-nudges, matching server `_find_turn_boundaries`) — the `:not(.system-nudge)` "over-count fix" was a parity reversal, do NOT apply.
- Known false positive: Copilot recurrently flags `/route/` proxy verbs as auth-bypass — the console proxy re-mints the user's own scopes and the node re-gates, same as close/cancel/approve.

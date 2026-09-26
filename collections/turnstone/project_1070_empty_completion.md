---
name: project_1070_empty_completion
description: "#1070 empty-completion recovery (fix/1070-empty-completion worktree): design shape, review findings from 09-05, and the two rulings from the corrective pass."
metadata: 
  node_type: memory
  type: project
  modified: 2026-09-06T01:37:59.115Z
---

Issue #1070: a provider returned finish_reason "stop" with reasoning only (no answer, no tool
call) and the coordinator committed it as a turn and parked idle. Branch fix/1070-empty-completion
(worktree <worktree>, off main f0d4f957) adds a structural
`is_empty_completion` predicate in model_turn and raises `_EmptyCompletionError` into the existing
mid-stream re-issue ladder (shares `_MID_STREAM_RETRIES` = 2). Re-issue only when the adapter
reported `native_tools_enabled is False` (new `ProviderRequestMetrics.native_tools_enabled` via
`request_uses_native_tools`); otherwise or on exhaustion the turn enters error, never idle.
Rejected attempts publish usage and feed the per-completion token budget. Side changes: chat-lane
`delta.refusal` renders as "[Refused: …]" and flips stop to content_filter; Anthropic `pause_turn`
passes through raw; both judges refuse to parse content_filter/length before reading a verdict.

Unprimed /review on 2026-09-05 (0 critical / 0 major / 8 minor / 3 nit): two findings blunt the
recovery itself. `defer_loading` on client function tools makes the chat lane report server tools
(tool-search sessions never re-issue); the rejected-usage commit runs inside the except arm and a
raising `_commit_for_generation` displaces the model error and skips stream_end. The
`_promote_dead_partial` change makes a zero-text transport death + Stop write a marker row (matches
a pre-existing HEAD comment; needs a pin, not a revert).

**Why:** the review ran while the authoring session was still self-reviewing in the same worktree;
the tree moved three times (18:00, 18:16, 18:23) and its `.venv` symlink vanished mid-run.

**How to apply:** the corrective pass (2026-09-05 18:50) settled both rulings: (1) an empty-string
chat `refusal` field is NOT a refusal (only non-empty text flips stop to content_filter), while a
Responses `response.refusal.done` event is a refusal even when empty; (2) empty completions keep the
shared two-re-issue budget, documented at the predicate as bounding attempts, not wall time. All
review findings have pinning tests in tests/test_empty_completion.py. Before reviewing a worktree
another session may own, capture the diff to the scratchpad first and re-compare at the end; see
[[feedback_freeze_tree_during_review]] and [[feedback_large_review_orchestration]].

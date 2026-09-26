---
name: project_1050_anthropic_sdk_v1
description: "#1050 Anthropic SDK v1 / HTTPX2 migration (09-12): temperature via extra_body with operator precedence, credential-header refusal, version floor, unverified live compat."
metadata: 
  node_type: memory
  type: project
  modified: 2026-09-13T04:28:15.999Z
---

**Built 2026-09-12; ON DEV since 09-13 (PR #1161, rebase-merged by the maintainer, branch
auto-deleted) together with the workspace-scoping and console-fix commits.**
Pin `anthropic>=1,<2` (lock 1.5.0); `distro` dropped from the lock; `httpx` stays for
Turnstone-owned clients (#1011). One unprimed /review round: 5 findings (3 minor, 2 nit), all
fixed in-branch except the fixed 0.5 s sleep in the loopback close test (kept: it buys
scenario determinism, a poll has no observable signal).

**Decisions (facts, not status):**
- SDK v1 removed `temperature`/`top_p`/`top_k` from the Messages signatures (typed kwarg =
  TypeError). The Anthropic lane carries capability-gated temperature in `extra_body`, merged
  BEFORE operator `server_compat` extra_params, so an operator pin of `temperature` wins —
  same precedence the OpenAI lanes get because both SDKs shallow-merge `extra_body` OVER typed
  kwargs (verified openai 3.8 + anthropic 1.5). `None` still omits; enabled thinking still
  forces 1.0 (pre-existing pin, `test_opus_4_6_still_has_temperature`). Eight
  `anthropic_hoist__*` goldens moved `temperature: 1.0` into `extra_body`; nothing else.
- Credential headers are REFUSED in `extra_headers` on every adapter
  (`_protocol.refuse_credential_headers`, exported from `turnstone.core.providers`): both SDKs
  merge caller headers over their own credential header case-insensitively, EVEN over a
  `with_options(api_key=...)` minted token (verified on anthropic 1.5 AND 0.117, openai 3.8 —
  the old model_turn docstring "the SDK silently drops an injected x-api-key" was false before
  the bump). Raise, never drop: a drop would reinstate the false invariant one layer down.
- Floor is the major (`>=1,<2`), not 1.5: nothing above 1.0 is required (block_binding rides the
  plain thinking dict — typed only in the beta namespace even on 1.5; stop_details via getattr).
- Real-SDK Anthropic tests inject `httpx2.Client`/`MockTransport` (v1 rejects `httpx.Client` at
  construction with a TypeError naming httpx2). Shared helper
  `tests/_wire_capture.anthropic_body_capture_client(captured, sse=...)` records body + headers.
- `transport_guarded` already caught both `httpx.TransportError` and `httpx2.TransportError`
  (#1009/#1010); only docstrings changed. Mid-body death escapes `messages.stream()` as
  `httpx2.ReadError`, one request, no SDK re-request; `stream.close()` from another thread still
  aborts a blocked read (cancel_ref shape); the loopback cross-thread close test now has an
  Anthropic lane (reader loops to the first CONTENT chunk — the adapter yields a usage-only
  chunk for message_start first).

**Unverified / follow-ups (the maintainer decides):**
- Live smoke PASSED 09-12 on the real API (the maintainer's 1-day key, ~60 tokens): registry create_client +
  with_options credential copy + drain_stream(transport_guarded(...)) + doctor probe; haiku-4-5 with
  extra_body temperature 0.5, sonnet-4-6 with forced 1.0 + adaptive + effort low, sonnet-5 with no
  sampling field — all stop/"ok". Only `TestLiveCompatStream` (needs a vLLM box) stays unrun.
  Gotcha seen on a second key: an org-level key NOT scoped to a workspace gets a 400 demanding the
  `anthropic-workspace-id` header; Turnstone has no operator field for it (SDK 1.x types it as
  `workspace_id` on Messages calls) — worth its own issue, out of #1050 scope.
- anthropic 1.5's `StopReason` adds `model_context_window_exceeded`; `_normalize_finish_reason`
  passes unknown reasons verbatim and the drain gate treats any finish as complete — filed as
  #1162 (09-13). An external PR (#1163) mapped it to `length`; the maintainer: close with thanks, do it in-house. DESIGN (branch
  fix/1162-context-window-stop-reason, stacked on the #1050 branch): the adapter RAISES
  `providers.ContextWindowExceededError` at the terminal message_delta (partial chunks already
  yielded), and `session._is_ctx_overflow` recognizes it BY CLASS NAME via `_CTX_OVERFLOW_EXC_NAMES`
  (session.py has no provider imports; it classifies by name) — parity with the 400 overflow: the
  send loop's compact-and-retry arm and the task_agent arm recover a complete answer; `length`
  would have told operators to raise max_tokens. The drain ladder never re-issues it (not in
  retryable_error_names). Pinned in tests/test_context_window_stop_reason.py (real SDK over mock
  transport + real adapter under the session loop). Review round: yield the terminal usage BEFORE
  raising (billed spend must reach accounting). PR #1164 against dev.
- `uv sync --frozen --all-extras` after checkout: the venv must carry anthropic 1.x or the
  boundary tests fail at client construction.

Related: [[project_973_no_thinking_posture_hosted_lanes]] (temperature-gate smell, Anthropic
side), [[feedback_never_pin_temperature]], [[feedback_sdk_boundary_testing]],
[[project_898_model_provider_obo]] (with_options credential path), [[feedback_check_pins_before_fixing_findings]].

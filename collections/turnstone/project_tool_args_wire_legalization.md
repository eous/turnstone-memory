---
name: project_tool_args_wire_legalization
description: "Malformed tool-call args 400ing every send on vLLM deepseek_v4: FIXED PR #778 via lowering.sanitize_tool_call_arguments; legalize to {} on the wire copy only."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-20T17:02:48.811Z
---

**Incident (node-4, 2026-07-05):** deepseek-v4-flash on vLLM 400'd every send on a long conversation. vLLM traceback = `deepseek_v4.render` → `chat_utils._postprocess_messages` → `json.loads(content)` → `JSONDecodeError: Unterminated string`. NOT context overflow.

**Root cause:** a `bash` tool call whose `arguments` was an unterminated JSON string (`{"command": "cat /va…`) with a **non-`length` finish reason** was committed verbatim and replayed every turn. turnstone only dropped malformed tool calls on `finish_reason == "length"` (`session.py` `_stream_response` ~6503) and on cancel; a `stop`/`tool_calls` finish reason with bad JSON slipped through. `_prepare_tool` salvages bad args for **execution only** — never rewrites the stored `arguments` — and the answering "retry" result means it's not an orphan, so `lowering.repair_wire_messages` (orphans only) never touched it. Poison pill wedged in history → every replay 400s.

**Durable quirk:** vLLM's `deepseek_v4` renderer **re-parses tool-call `arguments` as JSON at request-render time**; most renderers (and the OpenAI-native path) pass `arguments` as an opaque string. **Provider-asymmetric:** the Anthropic converter already self-heals (`args_str = fn.get("arguments","{}"); try json.loads except (JSONDecodeError,TypeError): {}` in `_anthropic.py` ~635); the OpenAI/vLLM outbound path passes args verbatim (only inbound touch is `_openai_chat.py:85`). Empty `""` args (no-arg calls) are a latent sibling — `json.loads("")` also raises. Sibling of the "vLLM 400-vs-500 asymmetry" in [[project_compaction_rehydration_deadlock]].

**Fix — PR #778 (2026-07-05):** `lowering.sanitize_tool_call_arguments` = **third wire-neutral pass** (fold → legalize → repair), wired into `_prepare_wire_messages` before `repair_wire_messages`. Legalizes any `arguments` that isn't a JSON-object string to `"{}"`. **Non-destructive / faithful:** mutates the transient wire copy only — the canonical `Turn` keeps the raw output (same "synth-transient @ send" philosophy as orphan repair; the design-spirit argument for putting it in lowering, not at construction). Copy-on-write + identity-preserving. Shared `wire_valid_arguments` predicate + `tool_args_preview` reused by a non-destructive source-side `stream.tool_args_malformed` warning at the accumulator. Wedged live sessions self-recover on next send (no DB edit). Also converted `lowering.py` to structlog. Copilot-review round: `tool_args_preview` scrubs secrets via `output_guard.redact_credentials` (over the full value, before the 120-char cap) + collapses all control chars to a single line — mirrors the established `audit._scrub_string`; reuse that for any model/user-controlled string headed to logs.

**Follow-on (2026-07-05, verified via `gh`):** this log-scrubbing landing point (`redact_credentials`) turned out to have false positives + a perf issue, triggering a dedicated credential-redaction hardening pass right after on `feat/credential-redaction-hardening` — PR #780 (client-side redaction for tool-call cards) and #781 (bounded key/token prefixes, perf hoist, x-api-key coverage) both shipped 2026-07-05; #779 (an earlier draft of #780) superseded. Not this file's subject, but same code path — check that branch/thread before touching `redact_credentials`/`tool_args_preview` again.

Related: [[project_canonical_trajectory_redesign]] (wire mutation only in lowering), [[reference_provider_capabilities]].

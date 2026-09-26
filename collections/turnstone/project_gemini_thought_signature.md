---
name: gemini-thought-signature-round-trip
description: "Gemini 400 'missing thought_signature' on tool calls, or GoogleProvider round-trips: SHIPPED PR #328 via provider_blocks lane hooks in _google.py."
metadata: 
  node_type: memory
  type: project
---

**Date:** 2026-04-06
**Status:** Merged in PR #328

## Problem

Gemini's OpenAI-compat endpoint requires `thought_signature` on tool-call objects
to survive the round-trip. The Chat Completions provider cherry-picks only standard
fields (id, type, function), dropping it. Multi-tool conversations fail with
`400 INVALID_ARGUMENT: Function call is missing a thought_signature`.

## Solution

GoogleProvider uses the same `provider_blocks` / `_provider_content` fidelity lane
that Anthropic uses for `signature` round-tripping:

- **Non-streaming**: `_extract_tool_calls` hook on base class. Google overrides to
  capture raw dicts via `model_dump()` into `provider_blocks`.
- **Streaming**: `_iter_stream` tap pattern — wraps raw SDK stream to accumulate
  extras from `__pydantic_extra__`, delegates to `super()._iter_stream()`, attaches
  `provider_blocks` on finish-reason chunk.
- **Next turn**: `_prepare_messages` hook strips `_provider_content` and reconstructs
  tool_calls from the stored raw data (with thought_signature).

## Key design decisions

- **Hooks on base class, not flags**: `_prepare_messages` and `_extract_tool_calls`
  are overridable hooks, not capability flags. Zero impact on OpenAI/vLLM.
- **Tap pattern for streaming**: Avoids duplicating the entire `_iter_stream` loop.
  The tap generator wraps the raw stream, captures extras, yields chunks unchanged
  to the base class.
- **`urlparse().hostname.endswith()`**: googleapis.com auto-detection in model_registry
  uses proper hostname parsing (CodeQL requirement, not substring match).

## Files

- `turnstone/core/providers/_openai_chat.py` — `_prepare_messages`, `_extract_tool_calls` hooks
- `turnstone/core/providers/_google.py` — overrides + tap-pattern `_iter_stream`
- `turnstone/core/model_registry.py` — `.googleapis.com` auto-detect

Canonical instance of the IR **'leak'** ([[project_harness_compiler_dialect_stack]], #699): an opaque provider field needing the side-lane to round-trip = an over-lowered neutral block a richer block dialect would absorb.

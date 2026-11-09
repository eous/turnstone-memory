---
name: feedback_json_decode_recursion_error
description: "Guarding json.loads/resp.json(): catch RecursionError too (3.13 near 10k levels), check the fallback doesn't loosen a control, and cap depth where recursive code walks parsed input."
metadata:
  type: feedback
---

JSON nested too deeply for the parser raises `RecursionError`, a `RuntimeError` rather than a
`ValueError`, so a decode guard of `except (TypeError, ValueError)` lets it escape. Python 3.13,
the project's floor, raises it at about 10,000 levels. Python 3.14, which the Docker image ships,
raises "Stack overflow ... while decoding" only when the thread's C stack runs out (about 200,000
levels on a worker thread), so the dev venv rarely shows the problem.

**Why:** it came up twice in October 2026. A node's `/health` reply stopped the doctor's version
scan (commit 71634950). Then the review of the #1416 fix found that a hand-edited coordinator task
blob would have passed the decode guard and been reported to the model as a storage outage to
retry. The #1456 sweep (2026-10-22) found 124 more handlers missing it, and its review found a
fallback that loosened a control and walkers that fail on input deep but still parseable.

**How to apply:**
- Treat a `RecursionError` from decoding as unparseable, in the same branch as malformed JSON:
  the value is corrupt. It is not a failed read and not a retryable error.
- Test it by patching the decoder to raise, because a 3.14 venv parses deep test input. Seed a
  value that is otherwise valid, so the test fails if the patch stops applying.
  `tests/_deep_json.py` (`too_deep_to_parse`) does this since #1456.
- `tests/test_json_decode_guards.py` scans the package and fails on a parse whose decode-error
  handler (`try` or `contextlib.suppress`) misses RecursionError. It can't see a guard in a caller:
  a parse helper whose callers catch ValueError translates RecursionError itself.
- Check the fallback, not only the catch. In the #1456 sweep a skill's `allowed_tools` fell back to
  a comma split when it failed to parse, so a value too deep for one node's parser (valid where a
  3.14 console wrote it) granted tools nobody listed. A fallback that reinterprets raw text must
  grant nothing for a value that looks like JSON.
- Parsing is not the only limit. Values 1,000-10,000 levels deep parse, then fail code that walks
  them one level per call: Python's recursion limit (~1,000), `copy.deepcopy` (two frames per
  level, ~500), the MCP client's serializer (255). Cap depth where the input enters (a model's tool
  arguments: 100 levels, `MAX_TOOL_ARGUMENT_DEPTH`), measured iteratively; the remaining reachable
  walkers are #1458.

Related: [[feedback_failed_read_is_not_a_value]].

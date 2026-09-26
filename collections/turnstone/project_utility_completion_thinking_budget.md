---
name: project_utility_completion_thinking_budget
description: "_utility_completion (title/compaction/web-fetch) empty on thinking models: budget max_tokens for a full think pass; code never sets temperature or effort."
metadata: 
  node_type: memory
  type: project
---

`_utility_completion` (title gen, compaction, web-fetch extraction, and the same shape sub-agents
use) shares the **session's own model**, which may be a **thinking model**. A small `max_tokens`
lets the reasoning pass consume the *entire* budget inside an unclosed `<think>` block →
`finish_reason=length`, **empty `content`** → the feature silently no-ops. There is **no portable
switch to disable thinking** (`enable_thinking` is Qwen-only; commercial providers each differ), so
the fix is always: give reasoning room (generous `max_tokens`) + read post-think `content`, never
`reasoning_content`.

**Symptom signature when debugging:** an auxiliary feature returns nothing/empty on local models but works on commercial ones; logs show an LLM call that took seconds and produced `raw=""`.

Concrete: auto-title + refresh were "mostly broken" because `_generate_title` capped at `max_tokens=200` (fixed → `_TITLE_MAX_TOKENS=2048`, then sanitize `content`: strip `<think>…</think>`, keep `[^\w\s]`-removed words, truncate to 80 = the alias cap). Web-fetch extraction already carried the "generous max_tokens so thinking models don't starve the visible answer" comment; compaction uses `compact_max_tokens`. **Title was the lone outlier.** When adding any new `_utility_completion` caller, budget for reasoning + visible output, not just the output.

Surfaced via #676 (eager auto-title trigger made the fire-and-fail visible across the dashboard as
`ws-xxxx` rows) but the root cause is model+budget, so it hit refresh equally. See
[[project_canonical_trajectory_redesign]] neighbours.

**Companion convention (same change): NO utility call hard-codes `temperature` — period.** `_utility_completion(temperature=None)` defaults to `self.temperature` (the operator/`[models.*]`-registry value the main turn uses); all three callers — title, web-fetch extraction, AND compaction — pass nothing and defer. User's firm rule (2026-06-27): setting temperature without model context breaks too many things now — thinking models, GPT-5/O-series no-temp, Claude-with-thinking pin-1.0 — so the registry is the *single* explicit place temperature is set; code never picks a constant. A max-effort review argued for pinning compaction/web-fetch low for summary faithfulness; user explicitly REJECTED that (registry value wins even for faithfulness-critical paths — an operator's explicit choice). Only pass an explicit temperature with a concrete, model-aware reason.

**Effort update (2026-07-13, #827 round-2 + follow-up ruling): the "low stays" convention is SUPERSEDED — code supplies NO effort value at all, not even a default-if-unconfigured.** Local lanes forward effort verbatim with no defined vocabulary/floor, so any code token is unsafe (and flips manual-thinking toggles). Utility lanes now budget for a full thinking pass at the model's own default instead: `_TITLE_MAX_TOKENS` 2048→**8192** + the title prompt enforces a **hard 3-word maximum** (visible answer trivially cheap; think pass carries the rest). Output guard keeps 512 and degrades visibly (labelled llm_error → heuristic tier) — remediation = effort on the guard's model alias. The empty-content signature in this memory is still the thing to watch; the fix lever is now operator alias/model-definition effort + generous budgets, never code. See [[feedback_never_pin_temperature]].

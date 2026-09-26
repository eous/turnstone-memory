---
name: project_857_cwd_tool_notes
description: "#857 cwd-in-context, SHIPPED PR #871: cwd/workspace facts ride fs tool descriptions (apply_cwd_context), never the system prompt; grants → #872."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-20T16:55:46.063Z
---

# #857 working-directory lowering — implemented via tool schemas (2026-07-19)

Shipped in **PR #871** (2026-07-19; rebase hashes on main: `46030824` feature / `8d1190d1` R1 fixes / `c4d180aa` consolidation). Full suite 9600 green, all CI green (3.13 did NOT hit the 20m timeout this time). Review converged: R1 = 0 correctness/3 quality, R2 = 0 correctness/1 quality (all fixed, none declined). PR bot feedback: Copilot 0 comments; github-code-quality 1 FP ("unused global `_workspace_dir_loaded`" — the memoization latch, read at the `if` on every call; same FP class as #844's load-bearing-await batch) → replied + resolved via resolveReviewThread. **Fix direction 2 split to #872** (per the maintainer's call when they challenged "Closes #857": the title violation — π drops a known coordinate — is fixed; the grant is s-augmentation, now first-class in the tracker with the full 2026-07-13 design in its body).

**The design ruling (the maintainer, twice-asserted)**: cwd/workspace facts live in the **fs tool descriptions**, NOT the system-prompt CONTEXT block — the workspace hint does not belong in the system prompt, as not every persona needs it. I first implemented Session-Context placement (gated on an fs-tool set); they redirected mid-session. Durable rule extracted to [[feedback_tool_relevant_facts_in_tool_schemas]].

**Shape**:
- `cwd_note` / `workspace_note` metadata templates in the 6 fs tool JSONs (bash/read_file/write_file/edit_file/search/diff_file); `{working_dir}`/`{workspace_dir}` substituted via `str.replace` (NOT format — prose may carry `${VAR}` braces). Stripped from wire schema by `_META_KEYS`.
- `tools.apply_cwd_context()`: deep-copies noted tools (fs dicts are SHARED across TOOLS/INTERACTIVE_TOOLS/TASK_AGENT_TOOLS and aliased through merge_mcp_tools — in-place append would corrupt the constants), passes note-less through by reference; NOT idempotent — pristine bases only.
- `ChatSession._set_interactive_tools(mcp_tools)`: THE single assignment path for both lanes (`_tools` + `_task_tools`), all 5 interactive build sites route through it (`[]` = no-MCP; merge with [] == fresh copy). `_apply_cwd_notes` computes guarded `os.getcwd()` (OSError→"", MCP bg-thread rebuilds) + `get_workspace_dir()` isdir-filtered, dropped when == cwd. Assignment-time by design: byte-stable tools block for provider prompt caches; `_render_agent_tool_descriptions` re-derive preserves-not-reapplies.
- `config.get_workspace_dir()`: `[tools] workspace_dir` → `$TURNSTONE_WORKSPACE`, cached (searxng pattern). Dockerfile `ENV TURNSTONE_WORKSPACE=/workspace`. docs/docker.md "Working directory" section (cwd=/data, `working_dir: /workspace` compose override, SQLite-`.turnstone.db`-in-cwd caveat); docs/tools.md metadata table synced to all 8 _META_KEYS.
- bash.json also dropped stale "for man pages use man instead" (man tool no longer exists — the maintainer caught mid-session) and its cwd_note states fresh-shell-per-call (cd does not persist).

**Why schema placement won** (vs my Session-Context recommendation): intrinsic gating (persona hides tool → note goes with it; no parallel gate-set drift); task-agent children carry their own notes via `_task_tools` regardless of parent persona visibility (killed the composer design's E5 corner); survives eval `system_prompt_override`. Costs accepted: cwd path rides every request's tools block (provider-logging disclosure — accepted, model could always `pwd`); ~15-25 tokens × 6 descriptions.

**Two dataflow maps** (local-only, gitignored): `docs/design/857-cwd-lowering-dataflow.md` (composer seam, superseded) + `857-cwd-toolschema-dataflow.md` (tool pipeline seam — has the full `self._tools`/`_task_tools` site table, aliasing proofs, provider passthrough verification).

**Deferred / open**:
- The "real fix" remains [[project_workstream_working_dir_grants]] (per-workstream launch-time grant + path confinement); this change is the informational layer only — grant work should replace the VALUE SOURCE (grant dir instead of getcwd) at `_apply_cwd_notes`.
- judge.py / optimizer.py / doctor.py own separate prompt assemblies that still lack cwd (mapper E4, out of scope, unfiled).
- eval non-skill lane uses `system_prompt_override` — notes still present (tool schemas), a correctness gain noted in the map.
- `test_mcp_client.py:689` identity assert became a names assertion (session lists are fresh copies now).
- Backport: undecided/undiscussed; main-only for now (stable/1.7 is the only patched line).

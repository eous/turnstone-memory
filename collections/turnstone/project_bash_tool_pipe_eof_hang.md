---
name: project_bash_tool_pipe_eof_hang
description: "Workstream stuck running after a bash tool call backgrounded a daemon: FIXED by PR #816 (_exec_bash killpg on every exit); opt-in background calls are #817."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-20T16:57:27.739Z
---

A `bash` tool call that backgrounds a **long-lived process** (`python -m http.server &`, a dev server, any daemon) wedges the entire workstream **forever**, and the tool's timeout does NOT save it.

**Mechanism** (`_exec_bash`, session.py ~14040–14105): spawns `bash <script>` with stdout/stderr `PIPE` + `start_new_session=True`, then reads `for line in proc.stdout` (14079) and a `drain_stderr` thread (14054) **until pipe EOF**. A backgrounded child inherits a copy of the pipe write-end, so EOF never arrives → both reads block indefinitely. The watchdog `_on_timeout` (14064) **early-returns when the tracked bash already exited** (`if proc.poll() is not None: return`) — which is exactly what happens after `<server> &` hands control back — so `timeout = item.get("timeout") or self.tool_timeout` **never fires**. task_agent bash uses the SAME `_exec_bash`, so its bash calls have the identical defeatable timeout. Stuck tool → sub-agent (`_run_agent`) future never resolves → parent `send-worker-<ws>` blocks in `_execute_tools` (result_iterator) → ws pinned in `state=running`, `updated` frozen. This is orthogonal to the model — GPT-5.6 just happened to run a `scripts/livepass.py` UX-preview harness.

**Fingerprint:** ws stuck `running` + `updated` frozen; NO CPU spin (event loop idle in `ep_poll`); NO direct child of the server proc (the tracked bash exited; survivors reparented to `ppid=1`); a half-open CLOSE-WAIT LLM socket is a **red herring** (pooled debris, not the block).

**Diagnosis playbook:** `sudo py-spy dump --pid <server>` (ptrace_scope=1 → needs sudo; install isolated with `uv tool install py-spy`, no venv touch). Look for `_exec_bash`/`drain_stderr` on a `send-worker-*` / `ThreadPoolExecutor` thread. Confirm the orphan: collect `/proc/<server>/fd` `pipe:[inode]` set, scan all `/proc/*/fd` for another pid holding the same inode → that pid (its process group, same as the tracked bash's session) still holds the write-end.

**Recovery observed in the 2026-07-09 investigation:** after identifying the leaked process group,
terminating that group closed the inherited pipes. EOF then let the tool and parent workstream
finish without a server restart. The reproducer was a background HTTP server in a disposable test
directory. Recovery alone did not fix the underlying bug; the process could be launched again until
the lifecycle fix below landed.

**Fix — PR #816 (2026-07-09, branch `fix/bash-tool-pipe-eof-hang` off `main`, worktree `<worktree>`; 2 commits: `fix(bash)` + `docs(changelog)` sync of 1.7.1–1.7.3 notes from stable/1.7):** rewrote `_exec_bash` to drain stdout+stderr in daemon threads and wait on the tracked PROCESS bounded by `tool_timeout` (keyed on process exit, never pipe EOF), then `killpg` the whole session group on EVERY exit path — reaps backgrounded survivors, forces EOF, no leaks. Deleted the buggy `threading.Timer`/`_on_timeout` early-return. Added `errors="replace"` to Popen — a single fable code-review caught that the drain's `except (ValueError, OSError)` was swallowing `UnicodeDecodeError` (a ValueError) → silent total output loss reported as clean success. Tests: `tests/test_bash_tool_background_hang.py` (hang, timeout, undecodable, streaming, cancel-mid-bash). **Decision:** background processes are KILLED on tool-call completion (nothing persists across calls; documented in bash.json + CHANGELOG). First-class opt-in "background this tool call" (a `background: true` param, wanted on task_agents too) is tracked as **issue #817** — SEPARATE larger effort, not built. Related: [[feedback_asyncio_timeout_vs_wait_for]], [[project_flaky_ci_hang_asyncio_sleep]].

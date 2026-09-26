---
name: feedback-type-checking-import-runtime-blindness
description: "Using at runtime a name imported only under TYPE_CHECKING (or moving an import there): mypy stays green but it NameErrors; grep uses, test rare arms."
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-07-26T00:37:16.325Z
---

A name imported under `if TYPE_CHECKING:` satisfies mypy for **runtime**
expression uses too, not just annotations — mypy does not model the guard's
runtime falseness. Strict mode stays green while the code `NameError`s in
production.

**Why:** Found by a sanity design pass on the compaction-visibility branch
(round 9, F1): `session_routes.py` imports `threading` only under
TYPE_CHECKING; the planned `ws._pending_drain is threading.current_thread()`
inside the drain's last-resort `except` handler would have NameErrored at
runtime — inside the exception handler, masking the original exception and
wedging the slot the handler exists to free — with `mypy --strict` fully
green. Worst-case placement: guard code in rarely-executed error arms, where
no test executes the line unless one is written deliberately.

**How to apply:**
- When writing a runtime reference to any module/type in a file, check
  whether its import sits under TYPE_CHECKING before trusting mypy.
- When moving an import INTO a TYPE_CHECKING block, grep the file for
  runtime uses of that name first.
- Rare code paths that use such names (except arms, defensive branches)
  need a test that executes the line — F821 (ruff) catches undefined
  names but NOT this case, since the name *is* defined at module scope
  for the checker's purposes.

Related: [[feedback_pre_commit_gates]], [[project_compaction_visibility]].

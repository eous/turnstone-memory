@AGENTS.md

## Memory setup

From a Turnstone checkout, use the README's setup command to add a read-only pointer to that
checkout's `CLAUDE.local.md`. This repository's instructions load directly when working here.
Setup preserves existing auto-memory directories and user settings.

`MEMORY.md` indexes are generated from descriptions. When asked to edit a shared memory, update
its own file and run `python3 scripts/index.py`; skip manual pointer edits to the index.
If `index.py --check` warns about the 200-line or 25 KB auto-memory limit, group older entries in
a hub or shorten descriptions.

Local refresh hooks are optional and never publish. Cloud sessions stay read-only: propose
memory additions in the final response for the maintainer to review. Authorized local edits
use the manual contribution workflow in the README.

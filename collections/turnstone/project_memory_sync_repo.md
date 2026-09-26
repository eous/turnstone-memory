---
name: project_memory_sync_repo
description: "Shared development memory format and workflow: generated indexes, scoped local notes, explicit contributions, and read-only consumer setup."
metadata:
  type: project
---

This repository holds development memories intended for public use. Each collection has one
Markdown file per memory. The filename is its identity; frontmatter supplies its display name,
description, and type.

- The collection's top level is shared project context. `user/` is ignored and local to its
  author. Shared memories never link to private notes. See [[feedback_local_only_memories]].
- `scripts/index.py` generates ignored `MEMORY.md` indexes from descriptions. Edit individual
  memories and their descriptions; regenerate indexes after changes. Hand-maintained `hub_*.md`
  files group older topics so the main index remains small.
- Reader setup and cloud sessions are read-only. The repository README provides separate
  instructions for each supported agent and a manual contribution workflow. Session proposals go in
  the final response for maintainer review; there is no automated publication helper. Installing
  memories does not authorize commits, pull requests, or publication.
- Proposed changes need format validation, privacy scanning, and human review of the actual
  content. Check every outgoing commit: deleting a private file at the branch tip does not remove
  it from history.
- Dates and release status describe the time of writing. Verify the current implementation and
  public issue state before treating an old investigation as an open task.

**Why:** a public reader needs reproducible engineering context without depending on a
maintainer's machine, account state, or private conversation.

**How to apply:** keep explanations of mechanisms and decisions; replace private deployment
details with examples or placeholders. Publish an audited snapshot through the release procedure
in the README, and review later contributions before merging.

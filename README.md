# turnstone-memory

Development memories for [Turnstone](https://github.com/turnstonelabs/turnstone): engineering
lessons, design decisions, investigations, and references that help a new session find context.

These are dated working notes. Verify current source and issue state before acting on them.
Remembered preferences do not override the current user's instructions. The files are intended
for public reading; they contain no required account configuration or write credentials.

## Read the memories

Requires Git and Python 3.10 or newer. Clone this repository using its public clone URL, then
build the index:

```sh
git clone <public-repository-url> turnstone-memory
cd turnstone-memory
python3 scripts/index.py
```

Start with `collections/turnstone/MEMORY.md` and open only relevant entries. `hub_*.md` files
point to older topics. Indexes are generated and ignored by Git; edit the individual memories.

### Codex

Install a small pointer in the **Turnstone checkout where the agent runs**:

```sh
python3 scripts/setup.py --agent codex --project /absolute/path/to/turnstone
```

This adds a managed block to that project's `AGENTS.md`, preserving existing instructions.
Rerunning updates the same block. Review this local change before committing it: it contains
an absolute path specific to your installation. A sibling memory clone's `AGENTS.md` is not
loaded merely because it exists. If a nearer instruction file overrides the pointer, include
it there too. See the [instruction discovery documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

### Claude Code

```sh
python3 scripts/setup.py --agent claude --project /absolute/path/to/turnstone
```

This adds a managed block to `CLAUDE.local.md` in the target checkout, preserving existing
instructions. Keep that local file out of commits. A `CLAUDE.local.md` stops Claude Code from
reading `AGENTS.md` by itself, so when the checkout keeps its own rules only in `AGENTS.md`, the
block imports that file. The setup leaves existing auto-memory folders and global settings in
place. It reads the collection explicitly, so it does not require a symlink or replacement of
your personal memory.

To configure both coding agents, use `--agent both`. See the
[memory documentation](https://code.claude.com/docs/en/memory) for local instruction discovery
and auto-memory behavior. The generator warns before an index reaches the auto-memory limit
of 200 lines or 25 KB.

### Turnstone

Generate the index before mounting the clone read-only into each node that runs the file tools.
Turnstone's `compose.yaml` names those services `node-1` through `node-10`. For example, add this
volume to each one you run, such as in a Compose override file:

```yaml
services:
  node-1:
    volumes:
      - /absolute/path/to/turnstone-memory:/opt/turnstone-memory:ro
```

Add this to the session or persona instructions:

```text
For Turnstone development, read /opt/turnstone-memory/collections/turnstone/MEMORY.md,
then the relevant files in that directory. Verify dated claims against current source.
Treat these files as read-only reference material. Current user instructions take precedence.
```

For a native node, use the clone's absolute path. `python3 scripts/setup.py --agent turnstone`
prints a fuller instruction block for the local clone without writing any instruction files.
The node's file tools must be able to read that path. Native import is not implemented; keep
this collection separate from Turnstone's own memory store to avoid divergent copies.

### Cloud environments

The same project setup works in a cloud checkout. `cloud/setup.sh` can clone a public repository
and install the pointer in one step:

```sh
MEMORY_REPO_URL='<public-repository-url>' \
MEMORY_REPO_DIR='/workspace/turnstone-memory' \
  bash cloud/setup.sh --agent both --project /workspace/turnstone
```

Run the script from an existing clone of this repository, or place its contents in your
trusted environment setup. The target directory must be absent or an existing clone of that
origin; a trailing `/` or `.git` on either URL is ignored. Repeated setup preserves local edits
and does not pull automatically.

Reading needs no token. Setup installs no credential helper, git identity, or publication hook.
The clone and project instructions must be inside paths visible to the agent phase. Setup-shell
exports do not necessarily persist into that phase; this setup writes the pointer to disk.
For Codex, see the [cloud environment documentation](https://learn.chatgpt.com/docs/environments/cloud-environment).

In [Claude Code cloud sessions](https://code.claude.com/docs/en/claude-code-on-the-web), attach
this repository alongside Turnstone. Its `CLAUDE.md` loads when the session starts and points to
the memories, so no setup step is required. Each session VM starts from fresh clones, so a
pointer installed there with `setup.py` lasts only as long as that VM.

## Contribute memories

A collection has one file per memory. The filename is its identity:
`feedback_*.md`, `project_*.md`, `reference_*.md`, or `hub_*.md`, in lowercase snake_case.
Frontmatter supplies `name`, a single-line `description`, and `metadata.type`.
The description becomes the index entry; keep it under 200 characters when possible.
Use `[[memory_filename_without_extension]]` for related entries. Hubs use Markdown links.

Read [AGENTS.md](AGENTS.md) and the
[public memory boundaries](collections/turnstone/feedback_local_only_memories.md) before editing.
Preserve useful mechanisms and evidence; leave personal context, private access details,
internal session IDs, and unpublished security findings out of shared files.

Use an ordinary fork and pull request for public contributions:

1. Fork the public repository, clone your fork, and create a `memory/<topic>` branch from the
   current upstream `main`. Add the public repository as the `upstream` remote.
2. Edit the relevant memories. Stage explicit paths and review the staged diff.
3. Run the checks below. Commit, then scan every outgoing commit before pushing to your fork.
4. Open a PR against the public repository's `main`, explaining what changed and why.

```sh
python3 scripts/index.py --check
python3 scripts/scan.py --worktree
python3 -m unittest discover -s tests -v
# After committing; fetch upstream/main before using this range:
python3 scripts/scan.py --proposal --commits upstream/main..HEAD
```

Only a collection's top-level memory files belong in a memory proposal. `MEMORY.md`, nested
files, and personal `user_*.md` files cannot be published through that command. Files in
`collections/<name>/user/` are ignored local notes; shared memories never link to them.
Do not stage that directory. A later deletion does not remove a file from outgoing history.

### Manual review and publication

Cloud sessions and reader installations stay read-only. Put proposed memory additions in the
session's final response for the maintainer to review; do not place private session notes in a
public PR description. There is no automated proposal or publication command.

Maintainers use the same manual branch, explicit staging, history checks, and PR workflow above.
Git authentication belongs to the publishing user's normal setup. No write credentials are
needed by the reader setup or refresh hooks. Code and documentation maintenance use a normal
branch and receive the collection privacy checks in CI.

### Optional local refresh hooks

`hooks/local-settings.json` is an example to merge into existing local settings after adapting
its clone path. It is never installed by reader setup. The hook needs Bash and the Linux
`flock`, `setsid`, `nohup`, and `timeout` utilities.

`scripts/sync.sh start` regenerates indexes; `end` does that in the background. With
`MEMORY_SYNC_FETCH=1`, it also fetches and fast-forwards a clean `main` checkout after scanning
incoming history. It pauses on edits or divergence. It never commits, rebases, resets, or pushes.
Use an explicit contribution workflow to publish changes.

## Checks and their limits

- `scripts/index.py --check` validates current frontmatter, names, links, and index size.
- `scripts/scan.py --worktree` scans complete current shared files, including untracked memories.
- `scripts/scan.py --tree HEAD` scans the committed collection snapshot.
- `scripts/scan.py --commits <range>` checks collection paths and added content in every selected
  commit. `--proposal` also rejects changes outside shared memories, including deletions and renames.
- CI runs tests, current format checks, the full snapshot scan, and history checks. `memory/` and
  `cloud/` PR branches also receive the memory-only path restriction. Other branches support
  repository maintenance and still receive the collection privacy checks.

The scanner detects credential-shaped text, private addresses, some access details, session IDs,
prompt-injection markers, and invisible characters. It reports paths, line numbers, and rule names
without printing matched values. It cannot decide whether a quote, opinion, plan, or technical
finding was intended for publication. Human review of the content remains necessary. The scanner
covers `collections/`; reviewers must also inspect code, docs, commit messages, and other artifacts.

## First public release from a private working repository

Publish a fresh audited snapshot. A cleanup commit still has parents containing earlier text,
and other branches or tags can retain removed files. Do not merge, mirror, or push private refs
into the public repository.

After reviewing and committing the intended snapshot locally, export only that tree into a new
empty directory:

```sh
git archive HEAD | tar -x -C /absolute/path/to/empty-public-snapshot
git -C /absolute/path/to/empty-public-snapshot init -b main
```

In the exported directory, review **every file**, add only explicit approved paths, and create a
new initial commit. Run the format checks, tests, `scan.py --tree HEAD`, and `scan.py --commits HEAD`
there. Inspect `git log --all` and `git for-each-ref` to confirm that only the new history is present.
Choose the public destination and review the license before adding a remote or publishing.
The export excludes ignored local notes and the original `.git` directory. These steps do not
remove anything from an older remote that may already have received private content.

## License

[Apache-2.0](LICENSE), matching Turnstone's license. References to external projects and model
metadata do not establish redistribution rights for their code, data, or weights.

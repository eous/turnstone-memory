#!/usr/bin/env python3
"""Install a small, read-only memory pointer in a project's agent instructions."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
START = "<!-- turnstone-memory:start -->"
END = "<!-- turnstone-memory:end -->"


def instructions(memory_dir: Path) -> str:
    collection = memory_dir / "collections" / "turnstone"
    if any(ord(c) < 32 or c == "`" for c in str(collection)):
        raise ValueError("memory path cannot contain control characters or backticks")
    return (
        "## Turnstone development memories\n\n"
        f"Read `{collection / 'MEMORY.md'}` at the start of Turnstone work, then open only\n"
        "the relevant memory files. Resolve filenames and links relative to that collection.\n"
        "These are dated development notes: verify current code and public issue state.\n"
        "Current user instructions take precedence over remembered preferences.\n"
        "This installation is read-only. Editing or publishing memories needs an explicit\n"
        "request; consult the memory repository's AGENTS.md when asked to contribute.\n"
        "Local user/ notes are outside this shared installation.\n"
    )


def tracked(project: Path, target: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(project), "ls-files", "--error-unmatch", "--", target.name],
        capture_output=True,
    )
    return result.returncode == 0


def exclude(project: Path, target: Path) -> None:
    """Keep a file holding local paths out of the project's commits."""
    git = ["git", "-C", str(project), "rev-parse"]
    result = subprocess.run(
        [*git, "--git-path", "info/exclude"], capture_output=True, text=True
    )
    if result.returncode:
        return  # not a git checkout: nothing to keep it out of
    path = Path(result.stdout.strip())
    if not path.is_absolute():
        path = project / path
    # Patterns are anchored at the top of the work tree, not at a subdirectory
    # project, and glob characters in its directory names must match literally.
    prefix = subprocess.run(
        [*git, "--show-prefix"], capture_output=True, text=True, check=True
    ).stdout.rstrip("\n")
    entry = "/" + "".join(f"\\{c}" if c in "\\*?[" else c for c in prefix + target.name)
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    if entry not in lines:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join([*lines, entry]) + "\n", encoding="utf-8")


def own_rules(text: str) -> bool:
    """Whether instructions hold anything besides this setup's block."""
    if START in text and END in text:
        text = text[: text.index(START)] + text[text.index(END) + len(END) :]
    return bool(text.strip())


def install(target: Path, content: str) -> None:
    if target.is_symlink():
        raise ValueError(f"refusing to replace an instruction symlink: {target}")
    project = target.parent
    # The block names a local path; it must never land in a committed file.
    if tracked(project, target):
        raise ValueError(
            f"{target.name} is tracked in {project}; add the memory pointer to a local file instead"
        )
    exclude(project, target)
    text = target.read_text(encoding="utf-8") if target.exists() else ""
    block = f"{START}\n{content.rstrip()}\n{END}"
    if START in text or END in text:
        if (
            text.count(START) != 1
            or text.count(END) != 1
            or text.index(END) < text.index(START)
        ):
            raise ValueError(
                f"malformed managed block in {target}; resolve it before setup"
            )
        updated = text[: text.index(START)] + block + text[text.index(END) + len(END) :]
    else:
        separator = "" if not text else ("\n" if text.endswith("\n") else "\n\n")
        updated = text + separator + block + "\n"
    if updated != text:
        target.write_text(updated, encoding="utf-8")
    print(f"Memory instructions: {target}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--agent", required=True, choices=("codex", "claude", "both", "turnstone")
    )
    parser.add_argument(
        "--project", type=Path, help="target checkout for project instructions"
    )
    parser.add_argument("--memory-dir", type=Path, default=REPO_DIR)
    args = parser.parse_args()
    memory_dir = args.memory_dir.expanduser().resolve()
    if not (memory_dir / "collections" / "turnstone").is_dir():
        parser.error("--memory-dir must contain collections/turnstone")
    if args.agent != "turnstone" and (
        args.project is None or not args.project.expanduser().is_dir()
    ):
        parser.error("--project must name an existing checkout")
    content = instructions(memory_dir)
    if args.agent == "turnstone":
        # Can run against a read-only mount after generating its index on the host.
        print(content, end="")
        return 0
    subprocess.run(
        [sys.executable, str(memory_dir / "scripts" / "index.py")], check=True
    )
    project = args.project.expanduser().resolve()
    targets = []
    if args.agent in ("codex", "both"):
        targets.append(project / "AGENTS.md")
    for target in targets:
        install(target, content)
    if args.agent in ("claude", "both"):
        claude = content
        # A CLAUDE.local.md stops Claude Code from reading AGENTS.md by itself; import
        # the project's own AGENTS.md rules unless a CLAUDE.md stands in for them.
        agents = project / "AGENTS.md"
        rules = agents.read_text(encoding="utf-8") if agents.is_file() else ""
        claude_md = (project / "CLAUDE.md", project / ".claude" / "CLAUDE.md")
        if own_rules(rules) and not any(path.exists() for path in claude_md):
            claude = "@AGENTS.md\n\n" + content
        install(project / "CLAUDE.local.md", claude)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"setup failed: {error}", file=sys.stderr)
        sys.exit(1)

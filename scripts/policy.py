#!/usr/bin/env python3
"""Shared path policy for memory contributions and publication checks."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

MEMORY_PATH = re.compile(
    r"collections/[a-z0-9]+(?:_[a-z0-9]+)*/"
    r"(?:feedback|project|reference|hub)_[a-z0-9]+(?:_[a-z0-9]+)*[.]md"
)
NUL = chr(0)


def git(repo: Path, *args: str) -> str:
    # Bytes, then decode: text mode would translate a bare CR into a newline and
    # hide exactly the characters the scanner looks for.
    out = subprocess.run(
        ["git", "-C", str(repo), "-c", "core.quotePath=false", *args],
        check=True,
        capture_output=True,
    ).stdout
    return out.decode("utf-8", errors="replace")


def paths(output: str) -> list[str]:
    return [path for path in output.split(NUL) if path]


def allowed(path: str) -> bool:
    return MEMORY_PATH.fullmatch(path) is not None


def path_problems(names: list[str], *, proposal: bool = False) -> list[str]:
    return [
        f"{path!r}: only shared top-level memory files are allowed"
        for path in names
        if (proposal or path == "collections" or path.startswith("collections/"))
        and not allowed(path)
    ]


def changed_paths(repo: Path, *diff_args: str) -> list[str]:
    return paths(
        git(repo, "diff", "--no-renames", "--name-only", "-z", *diff_args, "--")
    )


def working_paths(repo: Path) -> list[str]:
    """All modified or untracked paths admitted by git, including staged deletions."""
    return sorted(
        set(changed_paths(repo))
        | set(changed_paths(repo, "--cached"))
        | set(paths(git(repo, "ls-files", "--others", "--exclude-standard", "-z")))
    )


def entries(repo: Path, revision: str | None = None) -> list[tuple[str, str, str]]:
    """Return mode, object ID and path from a tree or the current index."""
    if revision is None:
        output = git(repo, "ls-files", "--stage", "-z", "--", "collections")
    else:
        output = git(repo, "ls-tree", "-r", "-z", revision, "--", "collections")
    result = []
    for entry in paths(output):
        header, path = entry.split("\t", 1)
        fields = header.split()
        result.append((fields[0], fields[1] if revision is None else fields[2], path))
    return result


def tree_problems(repo: Path, revision: str | None = None) -> list[str]:
    records = entries(repo, revision)
    return path_problems([path for _, _, path in records]) + [
        f"{path!r}: memory must be a regular non-executable file"
        for mode, _, path in records
        if mode != "100644"
    ]


def commit_base(repo: Path, commit: str) -> str:
    parents = git(repo, "rev-list", "--parents", "-n", "1", commit).split()[1:]
    if parents:
        return parents[0]
    return git(repo, "hash-object", "-t", "tree", "/dev/null").strip()


def commit_problems(repo: Path, commit: str, *, proposal: bool = False) -> list[str]:
    # Full trees catch pre-existing private files. Changed paths include deleted
    # files and both sides of renames, even if they vanish by the branch tip.
    return tree_problems(repo, commit) + path_problems(
        changed_paths(repo, commit_base(repo, commit), commit), proposal=proposal
    )

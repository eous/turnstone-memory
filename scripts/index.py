#!/usr/bin/env python3
"""Generate each collection's MEMORY.md from its memory files.

A collection's top level holds the shared memories (turnstone's project scope);
its user/ directory holds local-only ones (user scope), gitignored. No index is
tracked: every consumer builds its own. This script builds the ones Claude Code
sessions read, one line per memory from its description, grouped by type:
MEMORY.md for the shared set, and user/MEMORY.md for the local set. Files a
hub_*.md links to are listed through that hub instead, keeping the index short.

    index.py            write the indexes in every collection
    index.py --stdout   print the shared index instead of writing
    index.py --check    validate frontmatter, names and links; exit 1 on errors
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

COLLECTIONS = Path(__file__).resolve().parent.parent / "collections"
INDEX = "MEMORY.md"
LOCAL = "user"
# Shared memories never use the user_ type: facts about the user belong in user/.
SHARED_NAME = re.compile(r"(?:feedback|project|reference|hub)(?:_[a-z0-9]+)+[.]md")
NAME = re.compile(r"(?:feedback|project|reference|user|hub)(?:_[a-z0-9]+)+[.]md")
LINK = re.compile(r"\]\(([^)\s]+\.md)\)")
# [[file_name]] links between memories. File names always carry a type_ prefix, so
# requiring an underscore skips code such as dict[[str]] or arr[[0]].
WIKILINK = re.compile(r"\[\[([a-z0-9]+(?:_[a-z0-9]+)+)\]\]")
# NUL and other control bytes make git treat a memory as binary.
# CR and DEL can hide text in a terminal diff; C1 controls are never legitimate prose.
CONTROL = frozenset(
    chr(c) for c in [*range(32), 127, *range(128, 160)] if c not in (9, 10)
)
# Consumers that show one line per memory display the description itself.
DESCRIPTION_WARN_CHARS = 200
# Claude Code loads only the first 200 lines or 25KB of MEMORY.md and drops the rest
# silently; warn with headroom so growth shows up before truncation does.
INDEX_WARN_BYTES = 22_000
INDEX_WARN_LINES = 180
SECTIONS = {
    "feedback": "Working rules",
    "project": "Project state",
    "reference": "References",
    "user": "About the user",
}


@dataclass
class Memory:
    path: Path
    text: str
    fields: dict[str, str]
    problems: list[str]

    @property
    def kind(self) -> str:
        return self.fields.get("type") or self.path.stem.split("_", 1)[0]

    def line(self) -> str:
        return f"- {self.path.name} — {self.fields.get('description', '')}".rstrip(" —")


def load(path: Path) -> Memory:
    raw = path.read_bytes()
    problems = []
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        # Tolerated here so one broken file never stops the index; --check reports it.
        text = raw.decode("utf-8", errors="replace")
        problems.append("not valid UTF-8")
    if CONTROL.intersection(text):
        problems.append("contains control bytes")
    return Memory(path, text, frontmatter(text, problems), problems)


def frontmatter(text: str, problems: list[str]) -> dict[str, str]:
    """Top-level keys, plus `type` from a nested metadata block."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields: dict[str, str] = {}
    last_top = ""
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        key, sep, value = line.partition(":")
        indented = line.startswith((" ", "\t"))
        if last_top == "description" and line.strip() and (indented or not sep):
            # A wrapped or block-scalar description can't serve as an index line.
            problems.append("description must be a single plain line")
            last_top = ""
        if not sep:
            continue
        if not indented:
            last_top = key.strip()
            fields[last_top] = value.strip().strip("\"'")
        elif key.strip() == "type" and "type" not in fields:
            fields["type"] = value.strip().strip("\"'")
    return {}


def memories(directory: Path) -> list[Memory]:
    if not directory.is_dir():
        return []
    # Regular files only: editor lock links and stray directories are not memories.
    paths = sorted(directory.glob("*.md"))
    return [
        load(p) for p in paths if p.name != INDEX and p.is_file() and not p.is_symlink()
    ]


def collections() -> list[Path]:
    return sorted(p for p in COLLECTIONS.iterdir() if p.is_dir())


def hub_members(shared: list[Memory]) -> set[str]:
    return {
        t
        for m in shared
        if m.path.name.startswith("hub_")
        for t in LINK.findall(m.text)
    }


def render_list(title: str, items: list[Memory], footer: list[str], note: str) -> str:
    groups: dict[str, list[str]] = {name: [] for name in SECTIONS.values()}
    hubs: list[str] = []
    for m in items:
        if m.path.name.startswith("hub_"):
            hubs.append(m.line())
        else:
            groups.setdefault(SECTIONS.get(m.kind, "Other"), []).append(m.line())
    out = [f"# {title}", "", note]
    for name, lines in [
        *groups.items(),
        ("Hubs (older memories, read on demand)", hubs + footer),
    ]:
        if lines:
            out += ["", f"## {name}", *lines]
    return "\n".join(out) + "\n"


def render(collection: Path, shared: list[Memory], local: list[Memory]) -> str:
    members = hub_members(shared)
    # Hubs always stay listed, so hubs that link each other can't all vanish.
    listed = [
        m
        for m in shared
        if (m.path.name.startswith("hub_") or m.path.name not in members)
        and not m.path.name.startswith("user_")
    ]
    misplaced = [m for m in shared if m.path.name.startswith("user_")]
    footer = (
        [f"- {LOCAL}/{INDEX} — {len(local)} local-only memories on this machine"]
        if local
        else []
    )
    note = (
        "Generated from each memory's description by scripts/index.py at every sync; edits here"
        " are overwritten. Change a memory by editing its own file."
    )
    text = render_list(f"{collection.name} memory", listed, footer, note)
    if misplaced:
        # Auto-memory writes user-type notes at the top level; they belong in user/.
        text += (
            "\n## Misplaced: move these into user/\n"
            + "\n".join(m.line() for m in misplaced)
            + "\n"
        )
    return text


def render_local(collection: Path, local: list[Memory]) -> str:
    note = (
        "Local-only memories (gitignored, never pushed). Generated by scripts/index.py at every"
        " sync; edits here are overwritten."
    )
    return render_list(f"{collection.name} memory, local only", local, [], note)


def write_atomically(path: Path, text: str) -> None:
    # Sessions may read the index at any moment; never expose a partial file.
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".MEMORY.", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)
    # mkstemp creates 0600; match what a plain write would give under the umask.
    umask = os.umask(0)
    os.umask(umask)
    os.chmod(tmp, 0o666 & ~umask)
    os.replace(tmp, path)


def size_warning(collection: Path, text: str) -> str | None:
    size, lines = len(text.encode()), text.count("\n")
    if size <= INDEX_WARN_BYTES and lines <= INDEX_WARN_LINES:
        return None
    return (
        f"warning: {collection.name}/{INDEX} is {size} bytes, {lines} lines; Claude Code loads only"
        " 25KB or 200 lines: move older memories into a hub or shorten descriptions"
    )


def check(collection: Path) -> int:
    shared, local = memories(collection), memories(collection / LOCAL)
    shared_stems = {m.path.stem for m in shared}
    shared_names = {m.path.name for m in shared}
    local_stems = {m.path.stem for m in local}
    errors: list[str] = []
    for m in shared + local:
        is_shared = m.path.parent == collection
        where = str(m.path.relative_to(collection.parent))
        errors += [f"{where}: {problem}" for problem in m.problems]
        if is_shared and m.path.name.startswith("user_"):
            errors.append(
                f"{where}: user_ memories are about the user; move it into {LOCAL}/"
            )
        elif not (SHARED_NAME if is_shared else NAME).fullmatch(m.path.name):
            errors.append(
                f"{where}: file name must be lowercase snake_case with a type prefix"
            )
        if m.fields.get("description", "")[:1] in (">", "|"):
            errors.append(f"{where}: description must be a single plain line")
        for key in ("name", "description"):
            if not m.fields.get(key):
                errors.append(f"{where}: frontmatter is missing {key}")
        length = len(m.fields.get("description", ""))
        if length > DESCRIPTION_WARN_CHARS:
            print(
                f"warning: {where}: description is {length} characters; keep it to one line"
            )
        # Shared memories may link only to shared ones: user/ never reaches the
        # remote, and its file names would reveal what it holds.
        known = shared_stems if is_shared else shared_stems | local_stems
        for target in sorted(set(WIKILINK.findall(m.text)) - known):
            errors.append(
                f"{where}: [[{target}]] names no {'shared ' if is_shared else ''}memory"
            )
        if is_shared:
            # Any mention counts, not only links: a user/ file name alone reveals its topic.
            for stem in sorted(local_stems):
                if re.search(rf"(?<![a-z0-9_]){re.escape(stem)}(?![a-z0-9_])", m.text):
                    errors.append(f"{where}: mentions the local-only memory {stem}")
        if is_shared and m.path.name.startswith("hub_"):
            for target in sorted(set(LINK.findall(m.text)) - shared_names):
                errors.append(
                    f"{where}: links to {target}, which is not a shared memory"
                )
    for stem in sorted(shared_stems & local_stems):
        errors.append(f"{collection.name}: {stem} exists both shared and in {LOCAL}/")
    warning = size_warning(collection, render(collection, shared, local))
    if warning:
        print(warning)
    for error in errors:
        print(error)
    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--stdout", action="store_true")
    # CI runs a trusted copy of this script against a pull request's checkout.
    parser.add_argument(
        "--root", type=Path, help="repository to index (default: this one)"
    )
    args = parser.parse_args()
    if args.root:
        global COLLECTIONS
        COLLECTIONS = args.root.resolve() / "collections"
    if args.check:
        return max((check(c) for c in collections()), default=0)
    for collection in collections():
        shared, local = memories(collection), memories(collection / LOCAL)
        text = render(collection, shared, local)
        if args.stdout:
            print(text, end="")
            continue
        write_atomically(collection / INDEX, text)
        if local:
            write_atomically(
                collection / LOCAL / INDEX, render_local(collection, local)
            )
        warning = size_warning(collection, text)
        if warning:
            print(warning)
    return 0


if __name__ == "__main__":
    sys.exit(main())

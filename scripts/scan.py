#!/usr/bin/env python3
"""Heuristic scan of lines a change adds to collections/.

A backstop for credentials and access details that belong in a local-only
user/ file; it cannot judge strategy, plans or opinions. The patterns
describe shapes only, never real values, and a hit reports file, line and
rule name without echoing the matched text, so the scan itself discloses
nothing (its output can land in CI logs).

    scan.py origin/main HEAD            net change between two points
    scan.py --cached origin/main        staged changes
    scan.py --commits origin/main..HEAD every commit in a range, one at a time

    scan.py --proposal --commits RANGE  also forbid changes outside shared memories
    scan.py --worktree                 scan current shared files, including new ones
    scan.py --tree HEAD                scan a complete committed collection snapshot

    scan.py --repo PATH ...             check another checkout (CI runs a trusted copy)

Other arguments go to `git diff`. Path policy is checked in every selected commit.
Exit 1 when anything matches.
"""

from __future__ import annotations

import codecs
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

import policy

REPO_DIR = Path(__file__).resolve().parent.parent

ALNUM_BEFORE = "(?<![A-Za-z0-9])"
ALNUM_AFTER = "(?![A-Za-z0-9])"
BASE58 = "[a-km-zA-HJ-NP-Z1-9]"
GUID = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
PRIVATE_IPV4 = (
    "(10([.][0-9]{1,3}){3}|192[.]168([.][0-9]{1,3}){2}|172[.](1[6-9]|2[0-9]|3[01])([.][0-9]{1,3}){2}"
    # CGNAT, used by overlay VPNs.
    "|100[.](6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])([.][0-9]{1,3}){2})"
)
EMAIL_CHARS = "A-Za-z0-9._%+-"
# A value worth flagging: 12+ non-space characters with a letter and a digit,
# not a placeholder such as <key>, ${VAR}, $VAR or ***.
SECRET_VALUE = "(?![<$*{])(?=[^ \"'`]*[0-9])(?=[^ \"'`]*[A-Za-z])[^ \"'`]{12,}"

RULES = {
    "internal session identifier": re.compile(r"originSessionId\s*:"),
    "private key block": re.compile("-----BEGIN [A-Z ]*PRIVATE KEY"),
    "API token": re.compile(
        ALNUM_BEFORE + "(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"
        "|sk-[A-Za-z0-9_-]{20,}|[sr]k_(live|test)_[A-Za-z0-9]{16,}|xox[abpr]-[A-Za-z0-9-]{10,}"
        "|(AKIA|ASIA)[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|glpat-[A-Za-z0-9_-]{20,}"
        "|hf_[A-Za-z0-9]{30,}|eyJ[A-Za-z0-9_-]{10,}[.]eyJ[A-Za-z0-9_-]{10,}"
        # Three-part dot-separated bot tokens, and client secrets carrying a Q~ marker.
        "|[MN][A-Za-z0-9_-]{23,25}[.][A-Za-z0-9_-]{6}[.][A-Za-z0-9_-]{27,}"
        "|[A-Za-z0-9_.-]{3}[0-9]Q~[A-Za-z0-9_.~-]{30,})"
        "|(?i:bearer) +[A-Za-z0-9._~+/-]{20,}"
    ),
    "credential assignment": re.compile(
        "(?<![A-Za-z0-9_-])(?i:[A-Za-z0-9_-]*(password|passwd|pass|pwd|secret|token|credential|dsn|authorization|jwt|key)"
        "[A-Za-z0-9_-]*)[\"']? *[:=] *[\"']?" + SECRET_VALUE
    ),
    "credentials in a URL": re.compile(
        "[A-Za-z][A-Za-z0-9+.-]*://[^/ :@]+:(?![<$*{])[^/ @]+@"
        "|(?i:[?&](token|key|secret|password|auth|api_key|access_token)=)(?![<$*{])[^& ]{8,}"
    ),
    "bitcoin address": re.compile(
        ALNUM_BEFORE + "((?i:bc1)[a-zA-Z0-9]{25,60}"
        # Legacy addresses mix cases; requiring both rules out hex hashes.
        f"|[13](?={BASE58}*[A-HJ-NP-Z])(?={BASE58}*[a-km-z]){BASE58}{{25,34}})"
        + ALNUM_AFTER
    ),
    "ssh login or port": re.compile(
        "ssh +([^ ]+ +)*([A-Za-z0-9._-]+@[A-Za-z0-9.-]+|-p *[0-9]+)"
        "|(?i:ssh[ _-]?(on )?(port)?) *[:=]? *[0-9]{2,5}(?![0-9])"
    ),
    # A CIDR range (172.16.0.0/12 in a firewall rule) names a network, not a host.
    "private address": re.compile("(?<![0-9.])" + PRIVATE_IPV4 + "(?![0-9]|/[0-9])"),
    # Borrowed from turnstone's output guard: text that tries to steer a model.
    # Memories load as trusted context, so a saved one is a poisoning risk.
    "prompt-injection marker": re.compile(
        "(?i:ignore +((your|all|any|my|the) +)?((previous|prior|earlier|existing) +)?instructions"
        "|disregard +(all +)?(previous|prior)|forget your rules|new instructions *:"
        "|from now on you (are|will|must|should)|your new (role|identity|persona) is"
        "|i am your (new )?(admin|operator|developer|creator))"
        "|"
        + "|".join(
            map(re.escape, ["<|im_start|>system", "<|im_sep|>", "[SYSTEM]", "[INST]"])
        )
    ),
    # Markdown ways of writing one: **Password:** x, `x` in a code span, "the password is x".
    "labelled secret": re.compile(
        "(?i:password|passwd|passphrase|secret|token|api[ _-]?key)[*]{0,2} *(:|=| is | was )[*]{0,2}"
        " *[`\"']?(?=[^ \"'`*]*[0-9])(?=[^ \"'`*]*[A-Za-z])[^ \"'`*<${]{12,}"
    ),
    "large encoded blob": re.compile("[A-Za-z0-9+/]{200,}={0,2}"),
    # Database clients take the password glued to -p: mysql -u root -pS3cret.
    "password flag": re.compile(
        "(?i:mysql|mariadb|mysqldump|mysqladmin)[^|;&]*? -p(?=[^ ]*[0-9])(?=[^ ]*[A-Za-z])[^ ]{8,}"
    ),
    "directory or tenant ID": re.compile(
        "(?i:tenant)[^.]{0,40}" + ALNUM_BEFORE + "[0-9a-fA-F]{8}"
        "|(?i:client[ _-]?id|directory|subscription|app[ _-]?id)[^.]{0,40}(?i:"
        + GUID
        + ")"
    ),
    "email address": re.compile(
        f"(?<![{EMAIL_CHARS}])(?!git@|noreply@)[{EMAIL_CHARS}]+@"
        "(?!([A-Za-z0-9-]+[.])*(noreply|example)[.])[A-Za-z0-9-]+([.][A-Za-z0-9-]+)*[.][A-Za-z]{2,}"
    ),
}
# NUL and other control bytes make git and editors treat a memory as binary; CR and
# DEL can overwrite text in a terminal diff; C1 controls and invisible format
# characters (zero-width, bidi, tag characters) hide text from review.
CONTROL = frozenset(chr(c) for c in [*range(32), 127, *range(128, 160)] if c != 9)


def invisible(text: str) -> bool:
    return any(c in CONTROL or unicodedata.category(c) == "Cf" for c in text)


def git(*args: str) -> str:
    return policy.git(REPO_DIR, *args)


def scan_line(path: str, line_no: int, line: str) -> list[str]:
    hits = []
    if invisible(line):
        hits.append(f"{path!r}:{line_no}: control or invisible character")
    return hits + [
        f"{path!r}:{line_no}: {name}"
        for name, rule in RULES.items()
        if rule.search(line)
    ]


def scan_text(path: str, text: str) -> list[str]:
    return [
        hit
        for line_no, line in enumerate(text.split("\n"), 1)
        for hit in scan_line(path, line_no, line)
    ]


def header_path(raw: str) -> str:
    """Path from a `+++` header; git C-quotes names with quotes, backslashes or control bytes."""
    # Git appends a tab after names that contain a space.
    raw = raw.rstrip("\t")
    if raw.startswith('"') and raw.endswith('"'):
        raw = codecs.escape_decode(raw[1:-1].encode())[0].decode(
            "utf-8", errors="replace"
        )
    return raw[2:] if raw.startswith("b/") else ""


def scan_diff(*diff_args: str) -> list[str]:
    # Pin every option that changes diff output, so user config can't hide lines:
    # --text keeps "binary" files (one NUL byte is enough) in the diff, fixed
    # prefixes keep the file headers parseable, and no renames means a moved
    # file shows its full content.
    diff = git(
        "diff",
        "--unified=0",
        "--no-color",
        "--text",
        "--no-ext-diff",
        "--no-textconv",
        "--no-renames",
        "--src-prefix=a/",
        "--dst-prefix=b/",
        *diff_args,
        "--",
        "collections",
    )
    hits: list[str] = []
    path, line_no, in_header = "", 0, False
    for line in diff.split("\n"):
        # Header lines only occur between "diff --git" and the first hunk, so an
        # added line that happens to start with "++ " is never mistaken for one.
        if line.startswith("diff --git "):
            path, in_header = "", True
        elif in_header and line.startswith("+++ "):
            path = header_path(line[4:])
        elif line.startswith("@@"):
            in_header = False
            line_no = int(re.search("[+]([0-9]+)", line).group(1)) - 1  # type: ignore[union-attr]
        elif not in_header and line.startswith("+") and path:
            line_no += 1
            hits += scan_line(path, line_no, line[1:])
    return hits


def main() -> int:
    global REPO_DIR
    args = sys.argv[1:]
    # CI runs a trusted copy of this script against a pull request's checkout.
    if args[:1] == ["--repo"]:
        if len(args) < 2:
            raise ValueError("--repo needs a path")
        REPO_DIR = Path(args[1]).resolve()
        args = args[2:]
    proposal = "--proposal" in args
    if proposal:
        args.remove("--proposal")
    if args[:1] == ["--commits"]:
        if len(args) != 2 or args[1].startswith("-"):
            raise ValueError("--commits needs one revision or range")
        hits = []
        for commit in git("rev-list", "--reverse", args[1]).split():
            base = policy.commit_base(REPO_DIR, commit)
            problems = policy.commit_problems(REPO_DIR, commit, proposal=proposal)
            hits += [
                f"{commit[:8]} {hit}" for hit in problems + scan_diff(base, commit)
            ]
    elif args[:1] == ["--tree"]:
        if len(args) != 2 or args[1].startswith("-") or proposal:
            raise ValueError("--tree needs one revision; --proposal needs --commits")
        hits = policy.tree_problems(REPO_DIR, args[1])
        for _, oid, path in policy.entries(REPO_DIR, args[1]):
            hits += scan_text(path, git("cat-file", "blob", oid))
    elif args == ["--worktree"] and not proposal:
        hits = policy.tree_problems(REPO_DIR)
        names = sorted(
            {path for _, _, path in policy.entries(REPO_DIR)}
            | {
                path
                for path in policy.working_paths(REPO_DIR)
                if path == "collections" or path.startswith("collections/")
            }
        )
        hits += policy.path_problems(names)
        for path in names:
            file = REPO_DIR / path
            if file.is_symlink():
                hits.append(f"{path!r}: memory must be a regular file")
            elif file.is_file():
                if file.stat().st_mode & 0o111:
                    hits.append(f"{path!r}: memory must be non-executable")
                try:
                    # read_bytes: read_text would turn a bare CR into a newline.
                    hits += scan_text(path, file.read_bytes().decode("utf-8"))
                except UnicodeDecodeError:
                    hits.append(f"{path!r}: not valid UTF-8")
        # The index is what the next commit records; it can differ from the working copy.
        for _, oid, path in policy.entries(REPO_DIR):
            hits += [
                f"{hit} (staged)"
                for hit in scan_text(path, git("cat-file", "blob", oid))
            ]
    else:
        if proposal:
            raise ValueError("--proposal requires --commits")
        hits = scan_diff(*args) + policy.tree_problems(REPO_DIR)
        hits += policy.path_problems(policy.changed_paths(REPO_DIR, *args))
    for hit in dict.fromkeys(hits):
        print(hit)
    return 1 if hits else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValueError as error:
        # Our own usage messages; they carry no repository content.
        print(f"scan failed: {error}")
        sys.exit(1)
    except subprocess.CalledProcessError as error:
        # Name the git command, but don't echo its stderr or any file contents into CI logs.
        print(f"scan failed: git {' '.join(error.cmd[5:7])} exited {error.returncode}")
        sys.exit(1)
    except OSError as error:
        print(f"scan failed: {error.strerror} ({error.filename})")
        sys.exit(1)

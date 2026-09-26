"""Publication regressions use disposable git repositories and a local bare remote."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]

MEMORY = "collections/turnstone/project_example.md"
TEXT = "---\nname: example\ndescription: Example development lesson\nmetadata:\n  type: project\n---\n\nA useful engineering lesson.\n"


class RepositoryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="turnstone-memory-tests-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.remote = self.root / "remote.git"
        self.repo.mkdir()
        self.command("git", "init", "-q", "-b", "main", str(self.repo))
        self.command("git", "init", "-q", "--bare", "-b", "main", str(self.remote))
        self.git("config", "user.name", "Review fixture")
        self.git("config", "user.email", "review@example.test")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.hooksPath", str(self.root / "empty-hooks"))
        shutil.copytree(
            SOURCE / "scripts",
            self.repo / "scripts",
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        shutil.copytree(SOURCE / "cloud", self.repo / "cloud")
        shutil.copyfile(SOURCE / ".gitignore", self.repo / ".gitignore")
        self.write(MEMORY, TEXT)
        self.write("README.md", "Fixture documentation.\n")
        self.git(
            "add",
            "--",
            "scripts",
            "cloud",
            ".gitignore",
            "collections/turnstone/project_example.md",
            "README.md",
        )
        self.git("commit", "-qm", "Initial fixture")
        self.git("remote", "add", "origin", str(self.remote))
        self.git("push", "-q", "-u", "origin", "main")
        self.base = self.git("rev-parse", "HEAD").strip()

    def command(self, *args, check=True, env=None, cwd=None):
        return subprocess.run(
            args,
            cwd=cwd or self.repo,
            env=env,
            check=check,
            text=True,
            capture_output=True,
        )

    def git(self, *args):
        return self.command("git", *args).stdout

    def write(self, path, text):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def commit(self, *paths):
        self.git("add", "-f", "--", *paths)
        self.git("commit", "-qm", "Update fixture")

    def scan(self, *args):
        return self.command(
            sys.executable, str(self.repo / "scripts/scan.py"), *args, check=False
        )

    def state(self):
        return (
            self.git("rev-parse", "HEAD"),
            self.git("branch", "--show-current"),
            self.git("diff", "--cached"),
            self.git("diff"),
            self.git("ls-remote", "origin"),
        )


class ScanTests(RepositoryTest):
    def test_private_file_in_root_commit_is_rejected(self):
        private = "collections/turnstone/user/project_private.md"
        self.write(private, TEXT)
        self.git("add", "-f", "--", private)
        self.git("commit", "--amend", "--no-edit", "-q")
        result = self.scan("--commits", "HEAD")
        self.assertEqual(result.returncode, 1)
        self.assertIn("only shared top-level", result.stdout)

    def test_private_file_added_then_deleted_stays_rejected(self):
        private = "collections/turnstone/user/project_private.md"
        self.write(private, TEXT + "Ordinary private planning text.\n")
        self.commit(private)
        self.git("rm", private)
        self.git("commit", "-qm", "Remove fixture note")
        self.assertEqual(self.scan("--tree", "HEAD").returncode, 0)
        result = self.scan("--commits", f"{self.base}..HEAD")
        self.assertEqual(result.returncode, 1)
        self.assertIn("only shared top-level", result.stdout)
        self.assertNotIn("Ordinary private planning", result.stdout)

    def test_secret_added_then_deleted_is_redacted_in_report(self):
        secret = "ghp_" + "A1" * 20
        self.write(MEMORY, TEXT + secret + "\n")
        self.commit(MEMORY)
        self.write(MEMORY, TEXT)
        self.commit(MEMORY)
        result = self.scan("--commits", f"{self.base}..HEAD")
        self.assertEqual(result.returncode, 1)
        self.assertIn("API token", result.stdout)
        self.assertNotIn(secret, result.stdout)

    def test_transient_nonmemory_changes_fail_proposal_only(self):
        self.write("scratch.txt", "Ordinary draft\n")
        self.commit("scratch.txt")
        self.git("rm", "scratch.txt")
        self.git("commit", "-qm", "Remove draft")
        revisions = f"{self.base}..HEAD"
        self.assertEqual(self.scan("--commits", revisions).returncode, 0)
        self.assertEqual(self.scan("--proposal", "--commits", revisions).returncode, 1)

    def test_rename_checks_both_sides(self):
        self.git("mv", "README.md", "collections/turnstone/reference_readme.md")
        self.git("commit", "-qm", "Move documentation")
        result = self.scan("--proposal", "--commits", f"{self.base}..HEAD")
        self.assertEqual(result.returncode, 1)
        self.assertIn("README.md", result.stdout)

    def test_root_and_merged_private_history(self):
        self.git("checkout", "-qb", "side")
        private = "collections/turnstone/user/project_private.md"
        self.write(private, TEXT)
        self.commit(private)
        self.git("rm", private)
        self.git("commit", "-qm", "Remove private fixture")
        self.git("checkout", "main")
        self.write(MEMORY, TEXT + "Main branch lesson.\n")
        self.commit(MEMORY)
        self.git("merge", "--no-ff", "-qm", "Merge fixture", "side")
        self.assertEqual(self.scan("--commits", "HEAD").returncode, 1)
        self.assertEqual(self.scan("--tree", "HEAD").returncode, 0)

    def test_reserved_paths_and_symlinks(self):
        for path in (
            "collections/turnstone/MEMORY.md",
            "collections/turnstone/user_private.md",
        ):
            with self.subTest(path=path):
                self.write(path, TEXT)
                self.commit(path)
                self.assertEqual(self.scan("--tree", "HEAD").returncode, 1)
                self.git("rm", path)
                self.git("commit", "-qm", "Remove invalid fixture")
        link = self.repo / "collections/turnstone/reference_link.md"
        link.symlink_to("../../README.md")
        self.commit(str(link.relative_to(self.repo)))
        self.assertIn("regular non-executable", self.scan("--tree", "HEAD").stdout)

    def test_binary_and_header_shaped_content_cannot_hide_tokens(self):
        secret = "ghp_" + "B2" * 20
        self.write(MEMORY, TEXT + chr(0) + "\n++ " + secret + "\n")
        self.commit(MEMORY)
        result = self.scan("--commits", f"{self.base}..HEAD")
        self.assertEqual(result.returncode, 1)
        self.assertIn("control or invisible", result.stdout)
        self.assertIn("API token", result.stdout)
        self.assertNotIn(secret, result.stdout)

    def test_untracked_memory_scanned_and_normal_history_passes(self):
        self.write(MEMORY, TEXT + "A second lesson.\n")
        self.commit(MEMORY)
        self.assertEqual(
            self.scan("--proposal", "--commits", f"{self.base}..HEAD").returncode, 0
        )
        self.write("collections/turnstone/project_new.md", TEXT + "ghp_" + "C3" * 20)
        self.assertEqual(self.scan("--worktree").returncode, 1)

    def test_session_metadata_rejected(self):
        self.write(MEMORY, TEXT + "originSessionId: synthetic-session\n")
        self.assertIn("internal session identifier", self.scan("--worktree").stdout)


if __name__ == "__main__":
    unittest.main()

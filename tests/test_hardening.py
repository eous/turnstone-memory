"""Index, scanner, refresh and setup edge cases found in review."""

from __future__ import annotations

import os
import shutil
import sys
import unittest

from test_publication import MEMORY, SOURCE, TEXT, RepositoryTest

TOKEN = "gh" + "p_" + "A" * 36


def memory(name: str, body: str) -> str:
    return f"---\nname: {name}\ndescription: {name} lesson\nmetadata:\n  type: project\n---\n\n{body}\n"


class IndexTests(RepositoryTest):
    def index(self, *args):
        return self.command(
            sys.executable, str(self.repo / "scripts/index.py"), *args, check=False
        )

    def test_hubs_that_link_each_other_stay_listed(self):
        self.write(
            "collections/turnstone/hub_one.md",
            memory("hub_one", "[a](project_example.md) [b](hub_two.md)"),
        )
        self.write(
            "collections/turnstone/hub_two.md", memory("hub_two", "[c](hub_one.md)")
        )
        out = self.index("--stdout").stdout
        self.assertIn("hub_one.md", out)
        self.assertIn("hub_two.md", out)
        self.assertNotIn("- project_example.md", out)

    def test_top_level_user_memory_is_flagged_for_user_dir(self):
        self.write(
            "collections/turnstone/user_role.md", memory("user_role", "Background.")
        )
        result = self.index("--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("move it into user/", result.stdout)
        self.assertIn("Misplaced: move these into user/", self.index("--stdout").stdout)

    def test_carriage_return_and_c1_controls_fail_check(self):
        for char in (chr(13), chr(127), chr(0x9B)):
            self.write(MEMORY, TEXT + "Harmless summary." + char + "Hidden text\n")
            result = self.index("--check")
            self.assertEqual(result.returncode, 1, repr(char))
            self.assertIn("control bytes", result.stdout)


class ScannerTests(RepositoryTest):
    def test_staged_secret_is_scanned_even_if_working_copy_differs(self):
        self.write(MEMORY, TEXT + TOKEN + "\n")
        self.git("add", "--", MEMORY)
        self.write(MEMORY, TEXT)
        result = self.scan("--worktree")
        self.assertEqual(result.returncode, 1)
        self.assertIn("(staged)", result.stdout)

    def test_carriage_return_is_flagged(self):
        self.write(MEMORY, TEXT + "Summary." + chr(13) + "Hidden\n")
        self.assertIn("control or invisible", self.scan("--worktree").stdout)

    def test_password_flags_and_short_names(self):
        for line in ("export DB_PASS=hunter2hunter22", "mysql -u root -pS3cretPass9"):
            self.write(MEMORY, TEXT + line + "\n")
            self.assertEqual(self.scan("--worktree").returncode, 1, line)

    def test_usage_errors_are_shown(self):
        result = self.scan("--commits")
        self.assertEqual(result.returncode, 1)
        self.assertIn("--commits needs one revision or range", result.stdout)

    def test_trusted_copy_checks_another_checkout(self):
        trusted = self.root / "trusted"
        shutil.copytree(
            SOURCE / "scripts",
            trusted / "scripts",
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        self.write(MEMORY, TEXT + TOKEN + "\n")
        self.commit(MEMORY)
        result = self.command(
            sys.executable,
            str(trusted / "scripts/scan.py"),
            "--repo",
            str(self.repo),
            "--commits",
            "HEAD~1..HEAD",
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("API token", result.stdout)
        clean = self.command(
            sys.executable,
            str(trusted / "scripts/index.py"),
            "--check",
            "--root",
            str(self.repo),
            check=False,
        )
        self.assertEqual(clean.returncode, 0)


class RefreshTests(RepositoryTest):
    def sync(self):
        env = dict(os.environ, MEMORY_REPO_DIR=str(self.repo), MEMORY_SYNC_FETCH="1")
        env.pop("MEMORY_SYNC_LOCKED", None)
        return self.command(
            "bash", str(self.repo / "scripts/sync.sh"), "start", env=env
        )

    def test_incoming_script_change_waits_for_manual_pull(self):
        publisher = self.root / "publisher"
        self.command("git", "clone", "-q", str(self.remote), str(publisher))
        for key, value in (
            ("user.name", "r"),
            ("user.email", "r@example.test"),
            ("commit.gpgsign", "false"),
        ):
            self.command("git", "config", key, value, cwd=publisher)
        (publisher / "scripts/index.py").write_text(
            (publisher / "scripts/index.py").read_text() + "\n# changed\n"
        )
        self.command("git", "commit", "-qam", "Change a script", cwd=publisher)
        self.command("git", "push", "-q", "origin", "main", cwd=publisher)
        result = self.sync()
        self.assertIn("pull by hand", result.stdout)
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), self.base)


class SetupSafetyTests(RepositoryTest):
    def setup_cmd(self, project, agent="both"):
        return self.command(
            sys.executable,
            str(self.repo / "scripts/setup.py"),
            "--agent",
            agent,
            "--project",
            str(project),
            check=False,
        )

    def git_project(self, name):
        project = self.root / name
        project.mkdir()
        self.command("git", "init", "-q", str(project))
        return project

    def test_tracked_instruction_file_is_refused(self):
        project = self.git_project("tracked")
        (project / "AGENTS.md").write_text("Public rules.\n")
        self.command("git", "-C", str(project), "add", "AGENTS.md")
        result = self.setup_cmd(project, agent="codex")
        self.assertEqual(result.returncode, 1)
        self.assertEqual((project / "AGENTS.md").read_text(), "Public rules.\n")

    def test_created_files_are_excluded_from_the_project(self):
        project = self.git_project("fresh")
        self.assertEqual(self.setup_cmd(project).returncode, 0)
        status = self.command("git", "-C", str(project), "status", "--porcelain").stdout
        self.assertEqual(status, "")

    def test_claude_local_imports_agents_when_project_has_no_claude_md(self):
        project = self.git_project("agents-only")
        (project / "AGENTS.md").write_text("# Existing rules\n")
        self.command("git", "-C", str(project), "add", "AGENTS.md")
        self.assertEqual(self.setup_cmd(project, agent="claude").returncode, 0)
        self.assertIn("@AGENTS.md", (project / "CLAUDE.local.md").read_text())


if __name__ == "__main__":
    unittest.main()

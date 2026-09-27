"""Reader setup and refresh never publish or replace existing private memory."""

from __future__ import annotations

import os
import sys
import unittest

from test_publication import MEMORY, SOURCE, TEXT, RepositoryTest


class SetupTests(RepositoryTest):
    def test_cloud_read_setup_without_token_is_repeatable(self):
        project = self.root / "project with spaces"
        project.mkdir()
        (project / "AGENTS.md").write_text("# Existing rules\nKeep this instruction.\n")
        (project / "CLAUDE.local.md").write_text("Local instructions.\n")
        clone = self.root / "reader clone"
        env = dict(
            os.environ, MEMORY_REPO_URL=str(self.remote), MEMORY_REPO_DIR=str(clone)
        )
        env.pop("MEMORY_REPO_TOKEN", None)
        command = (
            "bash",
            str(SOURCE / "cloud/setup.sh"),
            "--agent",
            "both",
            "--project",
            str(project),
        )
        self.command(*command, env=env)
        first = {p.name: p.read_text() for p in project.iterdir()}
        (clone / MEMORY).write_text(TEXT + "Local reader edit.\n")
        self.command(*command, env=env)
        self.assertEqual(first, {p.name: p.read_text() for p in project.iterdir()})
        self.assertTrue(
            first["AGENTS.md"].startswith("# Existing rules\nKeep this instruction.\n")
        )
        self.assertEqual(first["AGENTS.md"].count("<!-- turnstone-memory:start -->"), 1)
        self.assertIn("read-only", first["CLAUDE.local.md"])
        self.assertTrue((clone / "collections/turnstone/MEMORY.md").is_file())
        self.assertIn("Local reader edit", (clone / MEMORY).read_text())
        self.assertEqual(
            self.command("git", "-C", str(clone), "rev-parse", "HEAD").stdout.strip(),
            self.base,
        )
        self.assertNotIn(
            "credential",
            self.command("git", "-C", str(clone), "config", "--local", "--list").stdout,
        )

    def test_cloud_setup_matches_origin_without_git_suffix(self):
        project = self.root / "project"
        project.mkdir()
        clone = self.root / "hosted clone"

        def setup(url):
            env = dict(os.environ, MEMORY_REPO_URL=url, MEMORY_REPO_DIR=str(clone))
            return self.command(
                "bash",
                str(SOURCE / "cloud/setup.sh"),
                "--agent",
                "claude",
                "--project",
                str(project),
                env=env,
                check=False,
            )

        self.assertEqual(setup(str(self.remote)).returncode, 0)
        # Hosted sessions may record the origin without .git or with a trailing slash.
        bare = str(self.remote)[: -len(".git")]
        self.command("git", "-C", str(clone), "remote", "set-url", "origin", bare)
        self.assertEqual(setup(str(self.remote) + "/").returncode, 0)
        other = setup(str(self.root / "other.git"))
        self.assertEqual(other.returncode, 1)
        self.assertIn("different origin", other.stderr)

    def test_setup_rejects_broken_markers_and_instruction_symlink(self):
        project = self.root / "target"
        project.mkdir()
        target = project / "AGENTS.md"
        target.write_text("Original\n<!-- turnstone-memory:start -->\n")
        args = (
            sys.executable,
            str(self.repo / "scripts/setup.py"),
            "--agent",
            "codex",
            "--project",
            str(project),
        )
        before = target.read_text()
        self.assertEqual(self.command(*args, check=False).returncode, 1)
        self.assertEqual(target.read_text(), before)
        target.unlink()
        actual = project / "shared-instructions"
        actual.write_text("Keep these rules.\n")
        target.symlink_to(actual)
        self.assertEqual(self.command(*args, check=False).returncode, 1)
        self.assertEqual(actual.read_text(), "Keep these rules.\n")

    def test_turnstone_prompt_does_not_write_to_mount(self):
        before = self.state()
        result = self.command(
            sys.executable, str(self.repo / "scripts/setup.py"), "--agent", "turnstone"
        )
        self.assertIn(str(self.repo / "collections/turnstone/MEMORY.md"), result.stdout)
        self.assertIn("read-only", result.stdout)
        self.assertEqual(self.state(), before)
        self.assertFalse((self.repo / "collections/turnstone/MEMORY.md").exists())

    def test_default_sync_preserves_staged_work_and_remote(self):
        self.write(MEMORY, TEXT + "Local lesson.\n")
        self.write("README.md", "Unrelated staged documentation.\n")
        self.git("add", "--", "README.md")
        before = self.state()
        self.sync()
        self.assertEqual(self.state(), before)
        self.assertTrue((self.repo / "collections/turnstone/MEMORY.md").is_file())

    def test_sync_leaves_an_empty_cherry_pick_in_progress(self):
        self.git("commit", "--allow-empty", "-qm", "Empty fixture change")
        empty = self.git("rev-parse", "HEAD").strip()
        self.git("branch", "-m", "empty-change")
        self.git("checkout", "-qb", "main", self.base)
        result = self.command("git", "cherry-pick", empty, check=False)
        self.assertNotEqual(result.returncode, 0)
        before = self.state()
        result = self.sync(fetch=True)
        self.assertIn("git operation is in progress", result.stdout)
        self.assertEqual(self.state(), before)
        self.assertEqual(self.git("rev-parse", "CHERRY_PICK_HEAD").strip(), empty)

    def test_index_ignores_editor_symlinks_and_directories(self):
        collection = self.repo / "collections/turnstone"
        (collection / ".#project_example.md").symlink_to("absent-lock-target")
        (collection / "reference_directory.md").mkdir()
        self.command(sys.executable, str(self.repo / "scripts/index.py"), "--check")
        result = self.command(
            sys.executable, str(self.repo / "scripts/index.py"), "--stdout"
        )
        self.assertIn("project_example.md", result.stdout)
        self.assertNotIn("reference_directory", result.stdout)
        self.assertNotIn(".#project_example", result.stdout)

    def test_shared_plain_text_cannot_name_known_private_notes(self):
        self.write("collections/turnstone/user/project_private.md", TEXT)
        self.write(MEMORY, TEXT + "Details are in project_private.md.\n")
        result = self.command(
            sys.executable, str(self.repo / "scripts/index.py"), "--check", check=False
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("mentions the local-only memory", result.stdout)

    def test_unknown_memory_prefix_fails_format_check(self):
        self.write("collections/turnstone/unrelated_example.md", TEXT)
        result = self.command(
            sys.executable, str(self.repo / "scripts/index.py"), "--check", check=False
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("type prefix", result.stdout)

    def sync(self, fetch=False):
        env = dict(
            os.environ,
            MEMORY_REPO_DIR=str(self.repo),
            MEMORY_SYNC_FETCH="1" if fetch else "0",
        )
        env.pop("MEMORY_SYNC_LOCKED", None)
        return self.command(
            "bash", str(self.repo / "scripts/sync.sh"), "start", env=env
        )

    def publish_fixture_updates(self, private=False):
        publisher = self.root / "publisher"
        self.command("git", "clone", "-q", str(self.remote), str(publisher))
        for key, value in (
            ("user.name", "Review fixture"),
            ("user.email", "review@example.test"),
            ("commit.gpgsign", "false"),
            ("core.hooksPath", str(self.root / "empty-hooks")),
        ):
            self.command("git", "config", key, value, cwd=publisher)
        path = "collections/turnstone/user/project_private.md" if private else MEMORY
        target = publisher / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(TEXT + "Incoming fixture lesson.\n")
        self.command("git", "add", "-f", "--", path, cwd=publisher)
        self.command("git", "commit", "-qm", "Update fixture", cwd=publisher)
        if private:
            self.command("git", "rm", path, cwd=publisher)
            self.command(
                "git", "commit", "-qm", "Remove private fixture", cwd=publisher
            )
        self.command("git", "push", "-q", "origin", "main", cwd=publisher)
        return self.command("git", "rev-parse", "HEAD", cwd=publisher).stdout.strip()

    def test_opt_in_refresh_checks_deleted_private_history(self):
        self.publish_fixture_updates(private=True)
        result = self.sync(fetch=True)
        self.assertIn("failed checks", result.stdout)
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), self.base)

    def test_opt_in_refresh_accepts_valid_memory_updates(self):
        head = self.publish_fixture_updates()
        self.sync(fetch=True)
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), head)
        self.assertIn("Incoming fixture lesson", (self.repo / MEMORY).read_text())


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import argparse
import importlib.util
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "context_kit.py"
SPEC = importlib.util.spec_from_file_location("context_kit_cli", SCRIPT)
assert SPEC and SPEC.loader
context_kit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(context_kit)


class ContextKitCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "project"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def init_args(self, profile: str, *, dry_run: bool = False) -> argparse.Namespace:
        return argparse.Namespace(
            root=self.root,
            project_id="example-project",
            name="Example Project",
            goal="Provide one durable example.",
            profile=profile,
            dry_run=dry_run,
            feature=[],
        )

    def test_init_and_validate_every_profile(self) -> None:
        for profile in ["minimal", "repository", "multi-repo"]:
            with self.subTest(profile=profile):
                with tempfile.TemporaryDirectory() as directory:
                    self.root = Path(directory) / "project"
                    context_kit.init_project(self.init_args(profile))
                    context_kit.validate_project(self.root)
                    manifest = context_kit.load_json(
                        self.root / ".hermes" / "context-kit.json"
                    )
                    self.assertEqual(manifest["profile"], profile)

    def test_init_dry_run_does_not_write(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            context_kit.init_project(self.init_args("repository", dry_run=True))
        self.assertFalse(self.root.exists())
        self.assertIn("create .hermes/context-kit.json", output.getvalue())

    def test_repository_profile_adds_selected_optional_feature(self) -> None:
        args = self.init_args("repository")
        args.feature = ["checkpoints"]
        context_kit.init_project(args)
        self.assertTrue((self.root / ".hermes" / "checkpoints" / "README.md").is_file())
        context_kit.validate_project(self.root)

    def test_init_never_overwrites_existing_context(self) -> None:
        self.root.mkdir()
        (self.root / "PROJECT.md").write_text("existing\n", encoding="utf-8")
        with self.assertRaisesRegex(context_kit.ContextKitError, "overwrite"):
            context_kit.init_project(self.init_args("minimal"))
        self.assertEqual(
            (self.root / "PROJECT.md").read_text(encoding="utf-8"),
            "existing\n",
        )

    def test_init_rejects_symlinked_internal_write_path(self) -> None:
        self.root.mkdir()
        with tempfile.TemporaryDirectory() as outside:
            try:
                (self.root / ".hermes").symlink_to(
                    Path(outside), target_is_directory=True
                )
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            with self.assertRaisesRegex(context_kit.ContextKitError, "symlink"):
                context_kit.init_project(self.init_args("minimal"))

    def test_repository_profile_rejects_stale_active_task_mirror(self) -> None:
        context_kit.init_project(self.init_args("repository"))
        state = self.root / ".hermes" / "state.md"
        state.write_text(
            state.read_text(encoding="utf-8").replace(
                "Active Task: None", "Active Task: TASK-001"
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(context_kit.ContextKitError, "differs"):
            context_kit.validate_project(self.root)

    def test_legacy_migration_check_is_read_only(self) -> None:
        files = context_kit.static_files(
            "example-project",
            "Example Project",
            "Provide one durable example.",
            context_kit.profile_definition("repository"),
            context_kit.kit_version(),
        )
        del files[".hermes/context-kit.json"]
        for relative, content in files.items():
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        args = argparse.Namespace(
            root=self.root,
            profile=None,
            check=True,
            apply=False,
        )
        context_kit.migrate_project(args)
        self.assertFalse((self.root / ".hermes" / "context-kit.json").exists())

    def test_legacy_repository_migration_can_apply_adoption_manifest(self) -> None:
        context_kit.init_project(self.init_args("repository"))
        adoption = self.root / ".hermes" / "context-kit.json"
        adoption.unlink()
        args = argparse.Namespace(
            root=self.root,
            profile=None,
            check=False,
            apply=True,
        )
        context_kit.migrate_project(args)
        self.assertTrue(adoption.is_file())
        context_kit.validate_project(self.root)

    def test_failed_legacy_migration_removes_its_new_manifest(self) -> None:
        context_kit.init_project(self.init_args("repository"))
        adoption = self.root / ".hermes" / "context-kit.json"
        adoption.unlink()
        state = self.root / ".hermes" / "state.md"
        state.write_text(
            state.read_text(encoding="utf-8").replace(
                "Active Task: None", "Active Task: TASK-404"
            ),
            encoding="utf-8",
        )
        args = argparse.Namespace(
            root=self.root,
            profile=None,
            check=False,
            apply=True,
        )
        with self.assertRaises(context_kit.ContextKitError):
            context_kit.migrate_project(args)
        self.assertFalse(adoption.exists())

    def test_validator_requires_the_pinned_kit_release(self) -> None:
        context_kit.init_project(self.init_args("minimal"))
        adoption = self.root / ".hermes" / "context-kit.json"
        manifest = context_kit.load_json(adoption)
        manifest["kit_version"] = "9.9.9"
        adoption.write_text(
            context_kit.json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(context_kit.ContextKitError, "differs from validator"):
            context_kit.validate_project(self.root)

    def test_multi_repo_lock_requires_portable_repository_url(self) -> None:
        context_kit.init_project(self.init_args("multi-repo"))
        lock_path = self.root / "components" / "lock.json"
        lock = context_kit.load_json(lock_path)
        lock["components"] = [
            {"name": "component-a", "source_revision": "a" * 40}
        ]
        lock_path.write_text(
            context_kit.json.dumps(lock, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(context_kit.ContextKitError, "invalid component"):
            context_kit.validate_project(self.root)

    def test_legacy_multi_repo_migration_requires_manual_lock_split(self) -> None:
        self.root.mkdir()
        (self.root / "PROJECT.md").write_text(
            "# Example\n\nProject ID: example-project\nName: Example\nStatus: Active\n",
            encoding="utf-8",
        )
        (self.root / "tasks" / "system").mkdir(parents=True)
        (self.root / "components").mkdir()
        (self.root / "components" / "lock.yaml").write_text(
            "components:\n", encoding="utf-8"
        )
        args = argparse.Namespace(
            root=self.root,
            profile=None,
            check=True,
            apply=False,
        )
        output = io.StringIO()
        with redirect_stdout(output):
            context_kit.migrate_project(args)
        self.assertIn("manual migration required", output.getvalue())
        self.assertFalse((self.root / ".hermes" / "context-kit.json").exists())


if __name__ == "__main__":
    unittest.main()

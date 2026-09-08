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

    def init_args(
        self,
        profile: str,
        *,
        dry_run: bool = False,
        runtime_adapter: list[str] | None = None,
        workflow_adapter: str | None = None,
    ) -> argparse.Namespace:
        return argparse.Namespace(
            root=self.root,
            project_id="example-project",
            name="Example Project",
            goal="Provide one durable example.",
            profile=profile,
            dry_run=dry_run,
            feature=[],
            runtime_adapter=runtime_adapter or [],
            workflow_adapter=workflow_adapter,
        )

    def migration_args(
        self,
        *,
        apply: bool,
        runtime_adapter: list[str] | None = None,
        workflow_adapter: str | None = None,
    ) -> argparse.Namespace:
        return argparse.Namespace(
            root=self.root,
            profile=None,
            check=not apply,
            apply=apply,
            to_spec=2,
            runtime_adapter=runtime_adapter or [],
            workflow_adapter=workflow_adapter,
        )

    def write_legacy_repository(self, *, active_task: str = "None") -> None:
        files = {
            "PROJECT.md": (
                "# Example Project\n\nProject ID: example-project\n"
                "Name: Example Project\nStatus: Active\n"
            ),
            "AGENTS.md": "# Legacy runtime instructions\n",
            ".hermes/context-kit.json": context_kit.json.dumps(
                {
                    "schema_version": 1,
                    "spec_version": 1,
                    "kit_version": "0.2.0",
                    "profile": "repository",
                    "features": ["tasks", "decisions"],
                    "extensions": {},
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            ".hermes/state.md": (
                "# Project State\n\nProject: example-project\nStatus: Active\n"
                f"Active Task: {active_task}\n"
            ),
            ".hermes/context-index.md": (
                "# Project Context Index\n\n"
                "| [`context-kit.json`](./context-kit.json) | Pinned | Adoption | Validate |\n"
            ),
            "tasks/README.md": "# Task Index\n",
            "tasks/current.md": "# Current Task\n\nActive Task: None\n",
            "docs/decisions/README.md": "# Decision Index\n",
        }
        for relative, content in files.items():
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

    def test_neutral_init_and_validate_every_profile(self) -> None:
        for profile in ["minimal", "repository", "multi-repo"]:
            with self.subTest(profile=profile):
                with tempfile.TemporaryDirectory() as directory:
                    self.root = Path(directory) / "project"
                    context_kit.init_project(self.init_args(profile))
                    context_kit.validate_project(self.root)
                    manifest = context_kit.load_json(
                        self.root / ".context-kit" / "manifest.json"
                    )
                    self.assertEqual(manifest["profile"], profile)
                    self.assertEqual(manifest["spec_version"], 2)
                    self.assertEqual(manifest["runtime_adapters"], [])
                    self.assertIsNone(manifest["workflow_adapter"])
                    self.assertFalse((self.root / "AGENTS.md").exists())
                    self.assertFalse((self.root / ".hermes").exists())

    def test_core_scaffold_has_no_legacy_runtime_namespace(self) -> None:
        scaffold = context_kit.KIT_ROOT / "templates" / "project-context"
        legacy_paths = [
            str(path.relative_to(scaffold))
            for path in scaffold.rglob("*")
            if path.is_file() and ".hermes" in path.relative_to(scaffold).parts
        ]
        self.assertEqual(legacy_paths, [])

    def test_init_dry_run_does_not_write(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            context_kit.init_project(self.init_args("repository", dry_run=True))
        self.assertFalse(self.root.exists())
        self.assertIn("create .context-kit/manifest.json", output.getvalue())

    def test_repository_profile_adds_selected_optional_feature(self) -> None:
        args = self.init_args("repository")
        args.feature = ["checkpoints"]
        context_kit.init_project(args)
        self.assertTrue(
            (self.root / ".context-kit" / "checkpoints" / "README.md").is_file()
        )
        context_kit.validate_project(self.root)

    def test_codex_adapter_adds_runtime_entrypoint(self) -> None:
        context_kit.init_project(
            self.init_args(
                "repository",
                runtime_adapter=["codex"],
                workflow_adapter="github",
            )
        )
        self.assertTrue((self.root / "AGENTS.md").is_file())
        manifest = context_kit.load_json(
            self.root / ".context-kit" / "manifest.json"
        )
        self.assertEqual(
            manifest["runtime_adapters"], [{"name": "codex", "version": 1}]
        )
        self.assertEqual(
            manifest["workflow_adapter"], {"name": "github", "version": 1}
        )
        context_kit.validate_project(self.root)

    def test_hermes_adapter_does_not_copy_operator_soul(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            context_kit.init_project(
                self.init_args("minimal", runtime_adapter=["hermes"])
            )
        self.assertFalse((self.root / "SOUL.md").exists())
        manifest = context_kit.load_json(
            self.root / ".context-kit" / "manifest.json"
        )
        self.assertEqual(
            manifest["runtime_adapters"], [{"name": "hermes", "version": 2}]
        )
        adapter = context_kit.runtime_adapter_definition("hermes")
        self.assertEqual(adapter["operator_templates"], [])
        self.assertIn("Hermes Skill-first setup", output.getvalue())
        self.assertIn("optional after Skill verification", output.getvalue())

    def test_duplicate_runtime_adapter_is_rejected(self) -> None:
        with self.assertRaisesRegex(context_kit.ContextKitError, "must be unique"):
            context_kit.init_project(
                self.init_args("minimal", runtime_adapter=["codex", "codex"])
            )

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
                (self.root / ".context-kit").symlink_to(
                    Path(outside), target_is_directory=True
                )
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            with self.assertRaisesRegex(context_kit.ContextKitError, "symlink"):
                context_kit.init_project(self.init_args("minimal"))

    def test_absolute_internal_path_is_rejected(self) -> None:
        with self.assertRaisesRegex(context_kit.ContextKitError, "must be relative"):
            context_kit.require_safe_target(self.root, "/tmp/outside")
        with self.assertRaises(context_kit.ContextKitError):
            context_kit.require_safe_target(self.root, ".git/config")

    def test_repository_profile_rejects_stale_active_task_mirror(self) -> None:
        context_kit.init_project(self.init_args("repository"))
        state = self.root / ".context-kit" / "state.md"
        state.write_text(
            state.read_text(encoding="utf-8").replace(
                "Active Task: None", "Active Task: TASK-001"
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(context_kit.ContextKitError, "differs"):
            context_kit.validate_project(self.root)

    def test_legacy_v1_requires_explicit_migration(self) -> None:
        self.write_legacy_repository()
        with self.assertRaisesRegex(context_kit.ContextKitError, "legacy v1"):
            context_kit.validate_project(self.root)

    def test_legacy_migration_check_is_read_only(self) -> None:
        self.write_legacy_repository()
        output = io.StringIO()
        with redirect_stdout(output):
            context_kit.migrate_project(self.migration_args(apply=False))
        self.assertFalse((self.root / ".context-kit").exists())
        self.assertIn("retain legacy .hermes files", output.getvalue())

    def test_legacy_repository_migration_can_apply_v2_manifest(self) -> None:
        self.write_legacy_repository()
        legacy_path = self.root / ".hermes" / "context-kit.json"
        legacy = context_kit.load_json(legacy_path)
        legacy["features"].append("checkpoints")
        legacy["extensions"] = {"example": {"enabled": True}}
        legacy_path.write_text(
            context_kit.json.dumps(legacy, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        checkpoint = self.root / ".hermes" / "checkpoints" / "archive" / "old.md"
        checkpoint.parent.mkdir(parents=True)
        checkpoint.write_text("# Historical checkpoint\n", encoding="utf-8")
        checkpoint_index = self.root / ".hermes" / "checkpoints" / "README.md"
        checkpoint_index.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_index.write_text("# Checkpoint Index\n", encoding="utf-8")
        context_kit.migrate_project(
            self.migration_args(apply=True, runtime_adapter=["hermes"])
        )
        adoption = self.root / ".context-kit" / "manifest.json"
        self.assertTrue(adoption.is_file())
        self.assertTrue((self.root / ".hermes" / "context-kit.json").is_file())
        self.assertTrue(
            (self.root / ".context-kit" / "checkpoints" / "archive" / "old.md").is_file()
        )
        self.assertEqual(
            context_kit.load_json(adoption)["extensions"],
            {"example": {"enabled": True}},
        )
        context_kit.validate_project(self.root)

    def test_failed_legacy_migration_removes_new_v2_files(self) -> None:
        self.write_legacy_repository(active_task="TASK-404")
        with self.assertRaises(context_kit.ContextKitError):
            context_kit.migrate_project(self.migration_args(apply=True))
        self.assertFalse((self.root / ".context-kit" / "manifest.json").exists())
        self.assertTrue((self.root / ".hermes" / "context-kit.json").is_file())

    def test_legacy_codex_adapter_requires_review_of_existing_instructions(self) -> None:
        self.write_legacy_repository()
        with self.assertRaisesRegex(
            context_kit.ContextKitError, "requires reviewed codex adapter integration"
        ):
            context_kit.migrate_project(
                self.migration_args(apply=False, runtime_adapter=["codex"])
            )

    def test_validator_requires_the_pinned_kit_release(self) -> None:
        context_kit.init_project(self.init_args("minimal"))
        adoption = self.root / ".context-kit" / "manifest.json"
        manifest = context_kit.load_json(adoption)
        manifest["kit_version"] = "9.9.9"
        adoption.write_text(
            context_kit.json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(context_kit.ContextKitError, "differs from validator"):
            context_kit.validate_project(self.root)

    def test_unknown_runtime_adapter_is_rejected(self) -> None:
        context_kit.init_project(self.init_args("minimal"))
        adoption = self.root / ".context-kit" / "manifest.json"
        manifest = context_kit.load_json(adoption)
        manifest["runtime_adapters"] = [{"name": "unknown", "version": 1}]
        adoption.write_text(
            context_kit.json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        with self.assertRaises(context_kit.ContextKitError):
            context_kit.validate_project(self.root)

    def test_unknown_workflow_adapter_is_rejected(self) -> None:
        context_kit.init_project(self.init_args("minimal"))
        adoption = self.root / ".context-kit" / "manifest.json"
        manifest = context_kit.load_json(adoption)
        manifest["workflow_adapter"] = {"name": "unknown", "version": 1}
        adoption.write_text(
            context_kit.json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        with self.assertRaises(context_kit.ContextKitError):
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
        output = io.StringIO()
        with redirect_stdout(output):
            context_kit.migrate_project(self.migration_args(apply=False))
        self.assertIn("manual migration required", output.getvalue())
        self.assertFalse((self.root / ".context-kit").exists())


if __name__ == "__main__":
    unittest.main()

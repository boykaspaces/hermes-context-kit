from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = (
    Path(__file__).parents[1]
    / "adapters"
    / "runtime"
    / "hermes"
    / "scripts"
    / "runtime_setup.py"
)
SPEC = importlib.util.spec_from_file_location("context_kit_hermes_setup", SCRIPT)
assert SPEC and SPEC.loader
setup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(setup)


class HermesRuntimeSetupTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.contract = copy.deepcopy(setup.load_contract())
        self.clean_source = mock.patch.object(setup, "source_status", return_value="")
        self.clean_source.start()
        hermes_home = self.root / "home" / "hermes" / ".hermes"
        workspace = self.root / "workspace"
        self.contract["paths"] = {
            "hermes_home": str(hermes_home),
            "skill_root": str(hermes_home / "skills"),
            "soul": str(hermes_home / "SOUL.md"),
            "workspace_root": str(workspace),
            "workspace_identity": str(workspace / ".hermes" / "WORKSPACE_ID"),
            "workspace_registry": str(workspace / ".hermes" / "WORKSPACES.md"),
        }
        self.contract["installation"]["manifest"] = str(
            hermes_home / "context-kit-install.json"
        )
        self.config = {
            "schema_version": 1,
            "workspace_id": "test-hermes",
            "source_revision": setup.checkout_revision(),
            "capabilities": ["project-context"],
            "soul_preference": "offer",
        }

    def tearDown(self) -> None:
        self.clean_source.stop()
        self.temp.cleanup()

    def test_public_contract_fixes_solution_paths_and_optional_soul(self) -> None:
        contract = setup.load_contract()
        self.assertEqual(contract["paths"]["hermes_home"], "/home/hermes/.hermes")
        self.assertEqual(contract["paths"]["workspace_root"], "/workspace")
        self.assertEqual(contract["paths"]["skill_root"], "/home/hermes/.hermes/skills")
        self.assertFalse(contract["soul"]["required"])
        self.assertEqual(contract["soul"]["default_action"], "offer")

    def test_capabilities_select_only_needed_skills(self) -> None:
        self.assertEqual(
            setup.selected_skills(self.config, self.contract),
            ["project-context-management"],
        )
        self.config["capabilities"].extend(["skill-authoring", "multi-repo"])
        self.assertEqual(
            setup.selected_skills(self.config, self.contract),
            [
                "project-context-management",
                "skill-authoring",
                "multi-repo-system-management",
            ],
        )

    def test_configuration_requires_project_context_and_full_revision(self) -> None:
        invalid = dict(self.config)
        invalid["capabilities"] = ["skill-authoring"]
        with self.assertRaisesRegex(setup.SetupError, "capabilities"):
            setup.load_config_from_data(invalid, self.contract, label="test")
        invalid = dict(self.config)
        invalid["source_revision"] = "main"
        with self.assertRaisesRegex(setup.SetupError, "full lowercase"):
            setup.load_config_from_data(invalid, self.contract, label="test")

    def test_plan_contains_exact_inventory_and_never_requires_soul(self) -> None:
        plan = setup.build_plan(self.config, self.contract)
        self.assertEqual(plan["soul"]["status"], "optional-not-applied")
        self.assertFalse(plan["soul"]["required"])
        skill = plan["skills"][0]
        self.assertIn("SKILL.md", skill["inventory"])
        self.assertEqual(
            skill["target"],
            str(Path(self.contract["paths"]["skill_root"]) / skill["name"]),
        )

    def test_dirty_checkout_is_not_an_immutable_install_source(self) -> None:
        with mock.patch.object(setup, "source_status", return_value=" M skills/example"):
            with self.assertRaisesRegex(setup.SetupError, "uncommitted or untracked"):
                setup.build_plan(self.config, self.contract)

    def test_install_and_verify_skill_first_without_soul(self) -> None:
        plan = setup.build_plan(self.config, self.contract)
        actions = setup.install_skills(plan, apply=True)
        actions += setup.configure_workspace(plan, apply=True)
        self.assertTrue(any(action.startswith("install ") for action in actions))
        result = setup.verify_runtime(
            plan, config_path=Path("/tmp/runtime config.json")
        )
        self.assertTrue(result["ready"], result["problems"])
        self.assertFalse(result["soul"]["required"])
        self.assertTrue(result["soul"]["user_choice_required"])
        self.assertEqual(result["soul"]["status"], "optional-not-checked")
        self.assertIn(
            "soul --config '/tmp/runtime config.json'",
            result["soul"]["preview_command"],
        )
        self.assertTrue(result["soul"]["apply_command"].endswith(" --apply"))
        self.assertFalse(Path(plan["paths"]["soul"]).exists())

    def test_different_installed_skill_requires_explicit_replace(self) -> None:
        plan = setup.build_plan(self.config, self.contract)
        target = Path(plan["skills"][0]["target"])
        target.mkdir(parents=True)
        (target / "SKILL.md").write_text("different\n", encoding="utf-8")
        with self.assertRaisesRegex(setup.SetupError, "--replace"):
            setup.install_skills(plan, apply=False)

    def test_optional_soul_preview_and_apply_preserve_user_content(self) -> None:
        soul_path = Path(self.contract["paths"]["soul"])
        soul_path.parent.mkdir(parents=True)
        soul_path.write_text("# My Identity\n\nKeep this.\n", encoding="utf-8")
        preview = setup.apply_soul(self.config, self.contract, apply=False)
        self.assertIn("context-kit:hermes:start", preview)
        self.assertIn("test-hermes", preview)
        self.assertEqual(
            soul_path.read_text(encoding="utf-8"), "# My Identity\n\nKeep this.\n"
        )
        setup.apply_soul(self.config, self.contract, apply=True)
        applied = soul_path.read_text(encoding="utf-8")
        self.assertIn("# My Identity", applied)
        self.assertIn("Keep this.", applied)
        self.assertEqual(applied.count("context-kit:hermes:start"), 1)
        setup.apply_soul(self.config, self.contract, apply=True)
        self.assertEqual(
            soul_path.read_text(encoding="utf-8").count("context-kit:hermes:start"),
            1,
        )
        backups = list(
            (Path(self.contract["paths"]["hermes_home"]) / "context-kit-backups").rglob(
                "SOUL.before-*.md"
            )
        )
        self.assertEqual(len(backups), 1)
        self.assertIn("Keep this.", backups[0].read_text(encoding="utf-8"))

    def test_config_schema_and_example_are_parseable(self) -> None:
        adapter = SCRIPT.parents[1]
        schema = json.loads((adapter / "runtime-config.schema.json").read_text())
        example = json.loads(
            (adapter / "templates" / "runtime-config.example.json").read_text()
        )
        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
        self.assertEqual(example["soul_preference"], "offer")


if __name__ == "__main__":
    unittest.main()

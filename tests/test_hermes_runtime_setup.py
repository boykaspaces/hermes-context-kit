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
            "source_checkout": str(setup.KIT_ROOT.resolve()),
            "skill_root": str(hermes_home / "skills"),
            "soul": str(hermes_home / "SOUL.md"),
            "workspace_root": str(workspace),
            "workspace_identity": str(workspace / ".hermes" / "WORKSPACE_ID"),
            "workspace_registry": str(workspace / ".hermes" / "WORKSPACES.md"),
        }
        self.contract["installation"]["manifest"] = str(
            hermes_home / "context-kit-install.json"
        )
        self.contract["installation"]["transaction_root"] = str(
            hermes_home / "context-kit-transactions"
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
        self.assertEqual(
            contract["paths"]["source_checkout"],
            "/workspace/.context-kit/sources/hermes-context-kit",
        )
        self.assertEqual(
            contract["installation"]["agent_mechanism"]["support"],
            "unsupported-for-release-install",
        )
        self.assertTrue(
            contract["installation"]["operator_mechanism"]["transactional"]
        )
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
        self.assertIn("SKILL.md", skill["runtime_inventory"])
        self.assertEqual(skill["source_validation_inventory"], {})
        self.assertEqual(
            skill["target"],
            str(Path(self.contract["paths"]["skill_root"]) / skill["name"]),
        )

    def test_dirty_checkout_is_not_an_immutable_install_source(self) -> None:
        with mock.patch.object(setup, "source_status", return_value=" M skills/example"):
            with self.assertRaisesRegex(setup.SetupError, "uncommitted or untracked"):
                setup.build_plan(self.config, self.contract)

    def test_source_checkout_must_use_the_contract_path_and_a_git_commit(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["paths"]["source_checkout"] = str(self.root / "different-source")
        with self.assertRaisesRegex(setup.SetupError, "contract requires"):
            setup.build_plan(self.config, contract)
        with mock.patch.object(setup, "checkout_revision", return_value=None):
            with self.assertRaisesRegex(setup.SetupError, "immutable Git commit"):
                setup.build_plan(self.config, self.contract)

    def test_tests_are_source_validation_not_runtime_inventory(self) -> None:
        self.config["capabilities"].append("multi-repo")
        plan = setup.build_plan(self.config, self.contract)
        skill = next(
            item for item in plan["skills"] if item["name"] == "multi-repo-system-management"
        )
        self.assertNotIn(
            "tests/test_validate_multi_repo_context.py", skill["runtime_inventory"]
        )
        self.assertIn(
            "tests/test_validate_multi_repo_context.py",
            skill["source_validation_inventory"],
        )
        self.assertLessEqual(len(skill["runtime_inventory"]), 20)

    def test_install_and_verify_skill_first_without_soul(self) -> None:
        self.config["capabilities"].append("multi-repo")
        plan = setup.build_plan(self.config, self.contract)
        actions = setup.install_runtime(plan, apply=True)
        self.assertTrue(any("fresh: install" in action for action in actions))
        result = setup.verify_runtime(
            plan, config_path=Path("/tmp/runtime config.json")
        )
        self.assertTrue(result["ready"], result["problems"])
        self.assertEqual(result["install_state"], "ready")
        self.assertFalse(result["soul"]["required"])
        self.assertTrue(result["soul"]["user_choice_required"])
        self.assertEqual(result["soul"]["status"], "optional-not-checked")
        self.assertIn(
            "soul --config '/tmp/runtime config.json'",
            result["soul"]["preview_command"],
        )
        self.assertTrue(result["soul"]["apply_command"].endswith(" --apply"))
        self.assertFalse(Path(plan["paths"]["soul"]).exists())
        manifest = json.loads(
            Path(plan["installation"]["manifest"]).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["install_state"], "ready")
        project_context = (
            Path(plan["skills"][0]["target"]) / "SKILL.md"
        ).read_text(encoding="utf-8")
        multi_repo = (
            Path(plan["skills"][1]["target"]) / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("\nversion: 2.1.0\n", project_context)
        self.assertIn("\nplatforms: [linux, macos, windows]\n", project_context)
        self.assertIn("\ntags: [project-management, context", project_context)
        self.assertIn("\nmetadata:\n  context-kit:\n", project_context)
        self.assertIn(
            "\nrelated_skills: [project-context-management]\n", multi_repo
        )
        self.assertFalse(
            (Path(plan["skills"][1]["target"]) / "tests").exists()
        )

    def test_install_classifies_fresh_identical_and_unexpected_files(self) -> None:
        plan = setup.build_plan(self.config, self.contract)
        actions, _ = setup.classify_install(plan, replace=False)
        self.assertTrue(actions[0].startswith("fresh: install "))
        setup.install_runtime(plan, apply=True)
        actions, _ = setup.classify_install(plan, replace=False)
        self.assertTrue(actions[0].startswith("identical: unchanged "))
        unexpected = Path(plan["skills"][0]["target"]) / "tests" / "source_test.py"
        unexpected.parent.mkdir()
        unexpected.write_text("source-only\n", encoding="utf-8")
        with self.assertRaisesRegex(setup.SetupError, "--replace"):
            setup.classify_install(plan, replace=False)
        self.assertFalse(setup.verify_runtime(plan)["ready"])

    def test_different_installed_skill_requires_explicit_replace(self) -> None:
        plan = setup.build_plan(self.config, self.contract)
        target = Path(plan["skills"][0]["target"])
        target.mkdir(parents=True)
        (target / "SKILL.md").write_text("different\n", encoding="utf-8")
        with self.assertRaisesRegex(setup.SetupError, "--replace"):
            setup.install_runtime(plan, apply=False)

    def test_failure_rolls_back_all_skills_and_previous_manifest(self) -> None:
        self.config["capabilities"].append("skill-authoring")
        plan = setup.build_plan(self.config, self.contract)
        originals: dict[Path, str] = {}
        for skill in plan["skills"]:
            target = Path(skill["target"])
            target.mkdir(parents=True)
            content = f"---\nname: {skill['name']}\ndescription: old\n---\nold\n"
            (target / "SKILL.md").write_text(content, encoding="utf-8")
            originals[target] = content
        manifest_path = Path(plan["installation"]["manifest"])
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        previous = '{"schema_version": 1, "legacy": true}\n'
        manifest_path.write_text(previous, encoding="utf-8")
        original_workspace = setup.configure_workspace

        def fail_after_activation(candidate, *, apply):
            if apply:
                raise setup.SetupError("injected workspace failure")
            return original_workspace(candidate, apply=False)

        with mock.patch.object(setup, "configure_workspace", side_effect=fail_after_activation):
            with self.assertRaisesRegex(setup.SetupError, "rolled back"):
                setup.install_runtime(plan, apply=True, replace=True)
        self.assertEqual(manifest_path.read_text(encoding="utf-8"), previous)
        for target, content in originals.items():
            self.assertEqual((target / "SKILL.md").read_text(encoding="utf-8"), content)

    def test_ready_transaction_can_be_explicitly_rolled_back(self) -> None:
        plan = setup.build_plan(self.config, self.contract)
        setup.install_runtime(plan, apply=True)
        actions = setup.rollback_runtime(plan, apply=False)
        self.assertTrue(any(action.startswith("rollback ") for action in actions))
        setup.rollback_runtime(plan, apply=True)
        self.assertFalse(Path(plan["skills"][0]["target"]).exists())
        result = setup.verify_runtime(plan)
        self.assertFalse(result["ready"])
        self.assertEqual(result["install_state"], "incomplete")

    def test_interrupted_transaction_blocks_install_until_rollback(self) -> None:
        plan = setup.build_plan(self.config, self.contract)
        setup.install_runtime(plan, apply=True)
        manifest_path = Path(plan["installation"]["manifest"])
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["install_state"] = "staging"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        journal_path = Path(manifest["transaction_dir"]) / "journal.json"
        journal = json.loads(journal_path.read_text(encoding="utf-8"))
        journal["state"] = "staging"
        journal["requested_manifest"] = manifest
        journal_path.write_text(json.dumps(journal), encoding="utf-8")
        with self.assertRaisesRegex(setup.SetupError, "run rollback"):
            setup.install_runtime(plan, apply=True)
        self.assertFalse(setup.verify_runtime(plan)["ready"])
        setup.rollback_runtime(plan, apply=True)
        self.assertFalse(Path(plan["skills"][0]["target"]).exists())

    def test_tampered_transaction_paths_are_not_rolled_back(self) -> None:
        plan = setup.build_plan(self.config, self.contract)
        setup.install_runtime(plan, apply=True)
        manifest_path = Path(plan["installation"]["manifest"])
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["install_state"] = "staging"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        journal_path = Path(manifest["transaction_dir"]) / "journal.json"
        journal = json.loads(journal_path.read_text(encoding="utf-8"))
        journal["state"] = "staging"
        journal["requested_manifest"] = manifest
        journal["skills"][0]["target"] = str(self.root / "outside-target")
        journal_path.write_text(json.dumps(journal), encoding="utf-8")
        with self.assertRaisesRegex(setup.SetupError, "invalid paths"):
            setup.rollback_runtime(plan, apply=True)
        self.assertTrue(Path(plan["skills"][0]["target"]).exists())

    def test_legacy_manifest_never_proves_v3_readiness(self) -> None:
        plan = setup.build_plan(self.config, self.contract)
        setup.install_runtime(plan, apply=True)
        manifest_path = Path(plan["installation"]["manifest"])
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["schema_version"] = 1
        manifest.pop("install_state")
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        result = setup.verify_runtime(plan)
        self.assertFalse(result["ready"])
        self.assertTrue(
            any("schema is not 2" in problem for problem in result["problems"])
        )

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

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "validate_multi_repo_context.py"
SPEC = importlib.util.spec_from_file_location("multi_repo_validator", SCRIPT)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class MultiRepoValidatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "tasks" / "system").mkdir(parents=True)
        (self.root / "PROJECT.md").write_text(
            "# Integration\n\nProject ID: integration-project\n",
            encoding="utf-8",
        )
        (self.root / "tasks" / "README.md").write_text(
            "# Task Index\n\n| Task | Status |\n|---|---|\n| TASK-001 | Blocked |\n",
            encoding="utf-8",
        )
        (self.root / "tasks" / "current.md").write_text(
            "# Current Task\n\nActive Task: TASK-001\n",
            encoding="utf-8",
        )
        (self.root / "tasks" / "TASK-001.md").write_text(
            "# TASK-001: Integrate\n\n"
            "Status: Blocked\n"
            "Type: System\n\n"
            "## Goal\n\nIntegrate components.\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_repository_accepts_blocked_current_system_task(self) -> None:
        validator.validate_repository(self.root)

    def test_repository_accepts_standalone_component_task(self) -> None:
        task = self.root / "tasks" / "TASK-001.md"
        task.write_text(task.read_text().replace("Type: System", "Type: Component"), encoding="utf-8")
        validator.validate_repository(self.root)

    def test_repository_rejects_terminal_current_task(self) -> None:
        task = self.root / "tasks" / "TASK-001.md"
        task.write_text(task.read_text().replace("Blocked", "Completed"), encoding="utf-8")
        index = self.root / "tasks" / "README.md"
        index.write_text(index.read_text().replace("Blocked", "Completed"), encoding="utf-8")
        with self.assertRaises(validator.ValidationError):
            validator.validate_repository(self.root)

    def test_handoff_requires_immutable_revision(self) -> None:
        handoff = {
            "schema_version": 1,
            "component": {
                "repository": "component-a",
                "task": "component-a:TASK-001",
            },
            "parent_system_task": "integration-project:TASK-001",
            "source": {
                "repository_url": "https://example.invalid/component-a.git",
                "branch": "feature/work",
                "revision": "a" * 40,
            },
            "validation": [{"command": "./validate.sh", "result": "passed"}],
            "documentation_updated": True,
            "integration_requirements": [],
            "rollback_revision": "b" * 40,
            "contains_secrets": False,
        }
        path = self.root / "handoff.json"
        path.write_text(json.dumps(handoff), encoding="utf-8")
        validator.validate_handoff(path)
        handoff["source"]["revision"] = "main"
        path.write_text(json.dumps(handoff), encoding="utf-8")
        with self.assertRaises(validator.ValidationError):
            validator.validate_handoff(path)

    def test_locked_system_revision_must_match_lock(self) -> None:
        manifest = {
            "schema_version": 1,
            "system_task": "integration-project:TASK-001",
            "system_id": "example-system",
            "integration_project": "integration-project",
            "components": [
                {
                    "repository": "component-a",
                    "task": None,
                    "task_absence_reason": "work-predates-protocol",
                    "repository_url": "https://example.invalid/component-a.git",
                    "branch": "main",
                    "revision": "a" * 40,
                    "delivery_state": "locked",
                }
            ],
            "integration": {
                "state": "pending",
                "validation_evidence": [],
                "deployment_evidence": [],
                "rollback": None,
            },
        }
        manifest_path = self.root / "tasks" / "system" / "TASK-001.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        lock_path = self.root / "components.lock.yaml"
        lock_path.write_text(
            "components:\n  - name: component-a\n    source_revision: " + "a" * 40 + "\n",
            encoding="utf-8",
        )
        validator.validate_system_task(self.root, "TASK-001", manifest_path, lock_path)
        lock_path.write_text(
            "components:\n  - name: component-a\n    source_revision: " + "b" * 40 + "\n",
            encoding="utf-8",
        )
        with self.assertRaises(validator.ValidationError):
            validator.validate_system_task(self.root, "TASK-001", manifest_path, lock_path)


if __name__ == "__main__":
    unittest.main()

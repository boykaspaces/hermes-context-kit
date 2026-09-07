from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


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
        (self.root / "evidence").mkdir()
        for evidence_name in ["system-acceptance.txt", "production-release.json", "acceptance.txt"]:
            (self.root / "evidence" / evidence_name).write_text("recorded\n", encoding="utf-8")
        (self.root / "docs").mkdir()
        (self.root / "docs" / "rollback.md").write_text("# Rollback\n", encoding="utf-8")
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
            "Type: System\n"
            "System Manifest: `tasks/system/TASK-001.json`\n\n"
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
        lock_path = self.root / "components" / "lock.yaml"
        lock_path.parent.mkdir()
        lock_path.write_text(
            "components:\n  - name: component-a\n    source_revision: " + "a" * 40 + "\n",
            encoding="utf-8",
        )
        validator.validate_system_task(self.root, "TASK-001", manifest_path, lock_path)
        manifest["components"][0]["delivery_state"] = "merged"
        lock_path.write_text(
            "components:\n  - name: component-a\n    source_revision: " + "b" * 40 + "\n",
            encoding="utf-8",
        )
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(validator.ValidationError, "differs from component lock"):
            validator.validate_system_task(self.root, "TASK-001", manifest_path, lock_path)
        manifest["components"][0]["delivery_state"] = "pending"
        manifest["components"][0]["revision"] = None
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(validator.ValidationError, "must be a non-empty string"):
            validator.validate_system_task(self.root, "TASK-001", manifest_path, lock_path)
        del manifest["components"][0]["revision"]
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(validator.ValidationError, "canonical schema"):
            validator.validate_system_task(self.root, "TASK-001", manifest_path, lock_path)
        manifest["components"][0]["delivery_state"] = "locked"
        manifest["components"][0]["revision"] = "a" * 40
        lock_path.write_text(
            "components:\n  - name: component-a\n    source_revision: " + "a" * 40 + "\n",
            encoding="utf-8",
        )
        manifest["integration"]["state"] = "verified"
        manifest["integration"]["validation_evidence"] = ["evidence/system-acceptance.txt"]
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        validator.validate_system_task(self.root, "TASK-001", manifest_path, lock_path)
        lock_path.write_text(
            "components:\n"
            "  - name: component-a\n"
            "    source_revision: " + "a" * 40 + "\n"
            "  - name: unrelated-component\n"
            "    source_revision: " + "b" * 40 + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(validator.ValidationError, "exactly match manifest components"):
            validator.validate_system_task(self.root, "TASK-001", manifest_path, lock_path)
        lock_path.write_text(
            "components:\n  - name: component-a\n    source_revision: " + "b" * 40 + "\n",
            encoding="utf-8",
        )
        with self.assertRaises(validator.ValidationError):
            validator.validate_system_task(self.root, "TASK-001", manifest_path, lock_path)

    def test_completed_v1_task_accepts_matching_lock_snapshot(self) -> None:
        task_path = self.root / "tasks" / "TASK-001.md"
        task_path.write_text(
            task_path.read_text(encoding="utf-8").replace(
                "Status: Blocked", "Status: Completed"
            ),
            encoding="utf-8",
        )
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
                "state": "verified",
                "validation_evidence": ["historical validation summary"],
                "deployment_evidence": [],
                "rollback": None,
            },
        }
        manifest_path = self.root / "tasks" / "system" / "TASK-001.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        lock_path = self.root / "components" / "locks" / "TASK-001.yaml"
        lock_path.parent.mkdir(parents=True)
        lock_path.write_text(
            "components:\n  - name: component-a\n    source_revision: "
            + "a" * 40
            + "\n",
            encoding="utf-8",
        )
        validator.validate_system_task(
            self.root, "TASK-001", manifest_path, lock_path
        )

    def test_verified_integration_rejects_pending_component(self) -> None:
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
                    "revision": None,
                    "delivery_state": "pending",
                }
            ],
            "integration": {
                "state": "verified",
                "validation_evidence": ["evidence/system-acceptance.txt"],
                "deployment_evidence": [],
                "rollback": None,
            },
        }
        manifest_path = self.root / "tasks" / "system" / "TASK-001.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(
            validator.ValidationError,
            "verified integration requires every component to be locked or later",
        ):
            validator.validate_system_task(self.root, "TASK-001", manifest_path, None)

    def test_deployed_integration_requires_deployed_components(self) -> None:
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
                    "revision": None,
                    "delivery_state": "pending",
                }
            ],
            "integration": {
                "state": "deployed",
                "validation_evidence": ["evidence/system-acceptance.txt"],
                "deployment_evidence": ["evidence/production-release.json"],
                "rollback": "docs/rollback.md",
            },
        }
        manifest_path = self.root / "tasks" / "system" / "TASK-001.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(
            validator.ValidationError,
            "deployed integration requires every component to be deployed",
        ):
            validator.validate_system_task(self.root, "TASK-001", manifest_path, None)

    def test_deployed_integration_accepts_deployed_components(self) -> None:
        revision = "a" * 40
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
                    "revision": revision,
                    "delivery_state": "deployed",
                }
            ],
            "integration": {
                "state": "deployed",
                "validation_evidence": ["evidence/system-acceptance.txt"],
                "deployment_evidence": ["evidence/production-release.json"],
                "rollback": "docs/rollback.md",
            },
        }
        manifest_path = self.root / "tasks" / "system" / "TASK-001.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        lock_path = self.root / "components" / "lock.yaml"
        lock_path.parent.mkdir()
        lock_path.write_text(
            "components:\n  - name: component-a\n    source_revision: " + revision + "\n",
            encoding="utf-8",
        )
        validator.validate_system_task(self.root, "TASK-001", manifest_path, lock_path)
        manifest["integration"]["validation_evidence"] = [None]
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(validator.ValidationError, "must be a non-empty string"):
            validator.validate_system_task(self.root, "TASK-001", manifest_path, lock_path)
        manifest["integration"]["validation_evidence"] = ["evidence/system-acceptance.txt"]
        manifest["integration"]["rollback"] = True
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(validator.ValidationError, "must be a non-empty string"):
            validator.validate_system_task(self.root, "TASK-001", manifest_path, lock_path)

    def test_system_task_template_uses_canonical_manifest_path(self) -> None:
        template = (SCRIPT.parents[1] / "templates" / "system-task.md").read_text(encoding="utf-8")
        self.assertEqual(template.count("tasks/system/TASK-{{task_id}}.json"), 2)
        self.assertNotIn("`system/TASK-{{task_id}}.json`", template)

    def test_component_lock_template_has_supported_shape(self) -> None:
        template = (SCRIPT.parents[1] / "templates" / "component-lock.yaml").read_text(encoding="utf-8")
        rendered = template.replace("{{component_project_id}}", "component-a").replace(
            "{{full_40_character_commit_sha}}", "a" * 40
        )
        lock_path = self.root / "components" / "lock.yaml"
        lock_path.parent.mkdir()
        lock_path.write_text(rendered, encoding="utf-8")
        self.assertEqual(validator.load_lock(lock_path), {"component-a": "a" * 40})

    def test_lock_allows_consumer_owned_metadata(self) -> None:
        lock_path = self.root / "components" / "lock.yaml"
        lock_path.parent.mkdir()
        lock_path.write_text(
            "schema_version: 1\n"
            "project_id: integration-project\n"
            "components:\n"
            "  - name: component-a\n"
            "    repository: https://example.invalid/component-a.git\n"
            "    source_revision: " + "a" * 40 + "\n"
            "    deployed:\n"
            "      status: deployed\n"
            "      revision: " + "a" * 40 + "\n"
            "updated: 2026-09-07\n",
            encoding="utf-8",
        )
        self.assertEqual(validator.load_lock(lock_path), {"component-a": "a" * 40})

        json_path = self.root / "components.lock.json"
        json_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "components": [
                        {
                            "name": "component-a",
                            "repository_url": "https://example.invalid/component-a.git",
                            "source_revision": "a" * 40,
                            "extensions": {"deployment": "consumer-owned"},
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        self.assertEqual(validator.load_lock(json_path), {"component-a": "a" * 40})

    def test_yaml_lock_rejects_malformed_or_incomplete_entries(self) -> None:
        lock_path = self.root / "components" / "lock.yaml"
        lock_path.parent.mkdir()
        invalid_locks = [
            "components:\n  - name: component-a\n  - name: component-b\n    source_revision: "
            + "b" * 40
            + "\n",
            "components:\n  - name: component-a\n    source_revision: "
            + "a" * 40
            + "\n  - name: component-a\n    source_revision: "
            + "b" * 40
            + "\n",
            "components:\n  - name: component-a\n  - name: COMPONENT-B\n    source_revision: "
            + "b" * 40
            + "\n",
        ]
        for content in invalid_locks:
            with self.subTest(content=content):
                lock_path.write_text(content, encoding="utf-8")
                with self.assertRaises(validator.ValidationError):
                    validator.load_lock(lock_path)

    def test_system_task_rejects_noncanonical_manifest_location_or_pointer(self) -> None:
        wrong_path = self.root / "wrong-location.json"
        wrong_path.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(validator.ValidationError, "manifest must be stored"):
            validator.validate_system_task(self.root, "TASK-001", wrong_path, None)

        task_path = self.root / "tasks" / "TASK-001.md"
        task_path.write_text(
            task_path.read_text().replace(
                "tasks/system/TASK-001.json", "system/TASK-001.json"
            ),
            encoding="utf-8",
        )
        canonical_path = self.root / "tasks" / "system" / "TASK-001.json"
        canonical_path.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(validator.ValidationError, "System Manifest must point"):
            validator.validate_system_task(self.root, "TASK-001", canonical_path, None)

    def test_system_task_accepts_markdown_manifest_link(self) -> None:
        task_path = self.root / "tasks" / "TASK-001.md"
        task_path.write_text(
            task_path.read_text().replace(
                "`tasks/system/TASK-001.json`",
                "[system/TASK-001.json](./system/TASK-001.json)",
            ),
            encoding="utf-8",
        )
        manifest_path = self._write_manifest(self._basic_manifest())
        validator.validate_system_task(self.root, "TASK-001", manifest_path, None)

    def test_system_task_rejects_canonical_manifest_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as outside:
            outside_manifest = Path(outside) / "TASK-001.json"
            outside_manifest.write_text("{}", encoding="utf-8")
            manifest_path = self.root / "tasks" / "system" / "TASK-001.json"
            manifest_path.symlink_to(outside_manifest)
            with self.assertRaisesRegex(validator.ValidationError, "must not use symlinks"):
                validator.validate_system_task(self.root, "TASK-001", manifest_path, None)

    def test_unchanged_component_accepts_completed_prior_state_without_id_ordering(self) -> None:
        revision = "a" * 40
        (self.root / "tasks" / "TASK-999.md").write_text(
            "# TASK-999: Earlier integration\n\n"
            "Status: Completed\n"
            "Type: System\n"
            "System Manifest: `tasks/system/TASK-999.json`\n",
            encoding="utf-8",
        )
        source_manifest = {
            "schema_version": 1,
            "system_task": "integration-project:TASK-999",
            "system_id": "example-system",
            "integration_project": "integration-project",
            "components": [
                {
                    "repository": "component-a",
                    "task": None,
                    "task_absence_reason": "work-predates-protocol",
                    "repository_url": "https://example.invalid/component-a.git",
                    "branch": "main",
                    "revision": revision,
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
        (self.root / "tasks" / "system" / "TASK-999.json").write_text(
            json.dumps(source_manifest), encoding="utf-8"
        )
        manifest = {
            "schema_version": 1,
            "system_task": "integration-project:TASK-001",
            "system_id": "example-system",
            "integration_project": "integration-project",
            "components": [
                {
                    "repository": "component-a",
                    "task": None,
                    "task_absence_reason": "no-component-change",
                    "source_system_task": "integration-project:TASK-999",
                    "repository_url": "https://example.invalid/component-a.git",
                    "branch": "main",
                    "revision": revision,
                    "delivery_state": "merged",
                }
            ],
            "integration": {
                "state": "pending",
                "validation_evidence": [],
                "deployment_evidence": [],
                "rollback": None,
            },
        }
        path = self.root / "tasks" / "system" / "TASK-001.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        validator.validate_system_task(self.root, "TASK-001", path, None)

        manifest["components"][0]["source_system_task"] = "other-project:TASK-999"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(
            validator.ValidationError,
            "source_system_task must belong to integration project",
        ):
            validator.validate_system_task(self.root, "TASK-001", path, None)

        del manifest["components"][0]["source_system_task"]
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(validator.ValidationError):
            validator.validate_system_task(self.root, "TASK-001", path, None)

    def test_pointer_rejects_non_http_and_non_relative_forms(self) -> None:
        invalid = [
            "file:///etc/passwd",
            "ftp://example.com/result.txt",
            "javascript:alert(1)",
            "C:\\Windows\\result.txt",
            "https://example.com/result with spaces.txt",
            "https://:443/result.txt",
            "https://example.com:notaport/result.txt",
            "https://user@example.com/result.txt",
            "https://[::1/result.txt",
            "https://%2fetc/result.txt",
            "/etc/passwd",
            "../outside.txt",
            "//example.com/result.txt",
            "evidence/result.txt?download=1",
            "evidence/%2e%2e/outside.txt",
            "evidence//result.txt",
            "evidence/result.txt#https://example.com",
            "evidence/result.txt#?download=1",
            "evidence/result.txt#/outside",
            "#summary",
        ]
        for pointer in invalid:
            with self.subTest(pointer=pointer):
                with self.assertRaises(validator.ValidationError):
                    validator.require_pointer(pointer, "evidence")
        self.assertEqual(
            validator.require_pointer("evidence/result.json#summary", "evidence"),
            "evidence/result.json#summary",
        )
        self.assertEqual(
            validator.require_pointer("https://example.com/result.json?raw=1#summary", "evidence"),
            "https://example.com/result.json?raw=1#summary",
        )

    def test_json_lock_rejects_incomplete_core_fields(self) -> None:
        lock_path = self.root / "components.lock.json"
        invalid = [
            {
                "schema_version": 1,
                "components": [
                    {"name": "component-a", "source_revision": "a" * 40}
                ],
            },
        ]
        for lock in invalid:
            with self.subTest(lock=lock):
                lock_path.write_text(json.dumps(lock), encoding="utf-8")
                with self.assertRaises(validator.ValidationError):
                    validator.load_lock(lock_path)

    def test_json_lock_rejects_duplicate_object_keys(self) -> None:
        lock_path = self.root / "components.lock.json"
        lock_path.write_text(
            '{"components":[{"name":"component-a","name":"component-b",'
            '"source_revision":"' + "a" * 40 + '"}]}',
            encoding="utf-8",
        )
        with self.assertRaisesRegex(validator.ValidationError, "duplicate JSON key"):
            validator.load_lock(lock_path)

    def test_git_verification_requires_exact_clean_checkout(self) -> None:
        revision = "a" * 40
        clean_head = mock.Mock(returncode=0, stdout=revision + "\n", stderr="")
        clean_status = mock.Mock(returncode=0, stdout="", stderr="")
        with mock.patch.object(
            validator.subprocess, "run", side_effect=[clean_head, clean_status]
        ):
            validator.verify_git_checkout(self.root, revision, "component-a")

        wrong_head = mock.Mock(returncode=0, stdout="b" * 40 + "\n", stderr="")
        with mock.patch.object(validator.subprocess, "run", return_value=wrong_head):
            with self.assertRaisesRegex(validator.ValidationError, "differs"):
                validator.verify_git_checkout(self.root, revision, "component-a")

        dirty_status = mock.Mock(returncode=0, stdout=" M PROJECT.md\n", stderr="")
        with mock.patch.object(
            validator.subprocess, "run", side_effect=[clean_head, dirty_status]
        ):
            with self.assertRaisesRegex(validator.ValidationError, "dirty"):
                validator.verify_git_checkout(self.root, revision, "component-a")

    def test_unchanged_component_rejects_noncompleted_or_invalid_source(self) -> None:
        self.test_unchanged_component_accepts_completed_prior_state_without_id_ordering()
        source_task = self.root / "tasks" / "TASK-999.md"
        source_task.write_text(
            source_task.read_text().replace("Status: Completed", "Status: Planned"),
            encoding="utf-8",
        )
        path = self.root / "tasks" / "system" / "TASK-001.json"
        current_manifest = json.loads(path.read_text(encoding="utf-8"))
        current_manifest["components"][0]["source_system_task"] = "integration-project:TASK-999"
        path.write_text(json.dumps(current_manifest), encoding="utf-8")
        with self.assertRaisesRegex(validator.ValidationError, "completed prior Task"):
            validator.validate_system_task(self.root, "TASK-001", path, None)

        source_task.write_text(
            source_task.read_text().replace("Status: Planned", "Status: Completed"),
            encoding="utf-8",
        )
        source_manifest_path = self.root / "tasks" / "system" / "TASK-999.json"
        source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
        source_manifest["schema_version"] = 2
        source_manifest_path.write_text(json.dumps(source_manifest), encoding="utf-8")
        with self.assertRaisesRegex(validator.ValidationError, "schema_version must be 1"):
            validator.validate_system_task(self.root, "TASK-001", path, None)

    def test_unchanged_component_source_requires_task_relationship_fields(self) -> None:
        self.test_unchanged_component_accepts_completed_prior_state_without_id_ordering()
        path = self.root / "tasks" / "system" / "TASK-001.json"
        current_manifest = json.loads(path.read_text(encoding="utf-8"))
        current_manifest["components"][0]["source_system_task"] = "integration-project:TASK-999"
        path.write_text(json.dumps(current_manifest), encoding="utf-8")
        source_path = self.root / "tasks" / "system" / "TASK-999.json"
        source_manifest = json.loads(source_path.read_text(encoding="utf-8"))
        del source_manifest["components"][0]["task_absence_reason"]
        source_path.write_text(json.dumps(source_manifest), encoding="utf-8")
        with self.assertRaisesRegex(validator.ValidationError, "canonical schema"):
            validator.validate_system_task(self.root, "TASK-001", path, None)

    def test_unchanged_component_rejects_source_symlinks(self) -> None:
        self.test_unchanged_component_accepts_completed_prior_state_without_id_ordering()
        path = self.root / "tasks" / "system" / "TASK-001.json"
        current = json.loads(path.read_text(encoding="utf-8"))
        current["components"][0]["source_system_task"] = "integration-project:TASK-999"
        path.write_text(json.dumps(current), encoding="utf-8")

        with tempfile.TemporaryDirectory() as outside:
            outside_root = Path(outside)
            source_task = self.root / "tasks" / "TASK-999.md"
            external_task = outside_root / "TASK-999.md"
            external_task.write_text(source_task.read_text(encoding="utf-8"), encoding="utf-8")
            source_task.unlink()
            source_task.symlink_to(external_task)
            with self.assertRaisesRegex(validator.ValidationError, "must not use symlinks"):
                validator.validate_system_task(self.root, "TASK-001", path, None)
            source_task.unlink()
            source_task.write_text(external_task.read_text(encoding="utf-8"), encoding="utf-8")

            source_manifest = self.root / "tasks" / "system" / "TASK-999.json"
            external_manifest = outside_root / "TASK-999.json"
            external_manifest.write_text(source_manifest.read_text(encoding="utf-8"), encoding="utf-8")
            source_manifest.unlink()
            source_manifest.symlink_to(external_manifest)
            with self.assertRaisesRegex(validator.ValidationError, "must not use symlinks"):
                validator.validate_system_task(self.root, "TASK-001", path, None)

    def test_source_manifest_enforces_integration_invariants(self) -> None:
        self.test_unchanged_component_accepts_completed_prior_state_without_id_ordering()
        path = self.root / "tasks" / "system" / "TASK-001.json"
        current = json.loads(path.read_text(encoding="utf-8"))
        current["components"][0]["source_system_task"] = "integration-project:TASK-999"
        path.write_text(json.dumps(current), encoding="utf-8")
        source_path = self.root / "tasks" / "system" / "TASK-999.json"
        source = json.loads(source_path.read_text(encoding="utf-8"))
        source["integration"]["state"] = "verified"
        source["integration"]["validation_evidence"] = []
        source["components"].append(
            {
                "repository": "component-b",
                "task": None,
                "task_absence_reason": "work-predates-protocol",
                "repository_url": "https://example.invalid/component-b.git",
                "branch": "main",
                "revision": None,
                "delivery_state": "pending",
            }
        )
        source_path.write_text(json.dumps(source), encoding="utf-8")
        with self.assertRaisesRegex(validator.ValidationError, "requires validation evidence"):
            validator.validate_system_task(self.root, "TASK-001", path, None)

    def test_locked_component_requires_lock_argument(self) -> None:
        revision = "a" * 40
        manifest = {
            "schema_version": 1,
            "system_task": "integration-project:TASK-001",
            "system_id": "example-system",
            "integration_project": "integration-project",
            "components": [{
                "repository": "component-a",
                "task": None,
                "task_absence_reason": "work-predates-protocol",
                "repository_url": "https://example.invalid/component-a.git",
                "branch": "main",
                "revision": revision,
                "delivery_state": "locked",
            }],
            "integration": {
                "state": "verified",
                "validation_evidence": ["evidence/acceptance.txt"],
                "deployment_evidence": [],
                "rollback": None,
            },
        }
        path = self.root / "tasks" / "system" / "TASK-001.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(validator.ValidationError, "requires a component lock"):
            validator.validate_system_task(self.root, "TASK-001", path, None)

    def test_source_manifest_evidence_uses_integration_root_trust_boundary(self) -> None:
        self.test_unchanged_component_accepts_completed_prior_state_without_id_ordering()
        current_path = self.root / "tasks" / "system" / "TASK-001.json"
        current = json.loads(current_path.read_text(encoding="utf-8"))
        current["components"][0]["source_system_task"] = "integration-project:TASK-999"
        current_path.write_text(json.dumps(current), encoding="utf-8")
        source_path = self.root / "tasks" / "system" / "TASK-999.json"
        source = json.loads(source_path.read_text(encoding="utf-8"))
        source["integration"]["state"] = "verified"
        source["integration"]["validation_evidence"] = ["evidence/source-result.txt"]
        source_path.write_text(json.dumps(source), encoding="utf-8")

        with self.assertRaisesRegex(validator.ValidationError, "regular file"):
            validator.validate_system_task(self.root, "TASK-001", current_path, None)

        with tempfile.TemporaryDirectory() as outside:
            external = Path(outside) / "source-result.txt"
            external.write_text("passed\n", encoding="utf-8")
            (self.root / "evidence" / "source-result.txt").symlink_to(external)
            with self.assertRaisesRegex(validator.ValidationError, "symlink"):
                validator.validate_system_task(self.root, "TASK-001", current_path, None)

    def test_handoff_rejects_unknown_fields_and_common_secrets(self) -> None:
        handoff = {
            "schema_version": 1,
            "component": {"repository": "component-a", "task": "component-a:TASK-001"},
            "parent_system_task": "integration-project:TASK-001",
            "source": {
                "repository_url": "https://example.invalid/component-a.git",
                "branch": "main",
                "revision": "a" * 40,
            },
            "validation": [{"command": "./validate.sh", "result": "passed"}],
            "documentation_updated": True,
            "integration_requirements": [],
            "rollback_revision": None,
            "contains_secrets": False,
        }
        path = self.root / "handoff-secret.json"
        for secret in [
            "xoxb-1234567890-abcdefghijklmnop",
            "eyJabcdefghijk.abcdefghijklmnop.abcdefghijklmnop",
            "password=supersecret",
            "DEPLOY_CREDENTIAL=correct-horse-battery-staple ./validate.sh",
        ]:
            with self.subTest(secret=secret):
                candidate = dict(handoff)
                candidate["unexpected"] = secret
                path.write_text(json.dumps(candidate), encoding="utf-8")
                with self.assertRaises(validator.ValidationError):
                    validator.validate_handoff(path)

    def test_handoff_rejects_unsafe_urls_unbounded_requirements_and_command_secrets(self) -> None:
        handoff = {
            "schema_version": 1,
            "component": {"repository": "component-a", "task": "component-a:TASK-001"},
            "parent_system_task": "integration-project:TASK-001",
            "source": {
                "repository_url": "https://example.invalid/component-a.git",
                "branch": "main",
                "revision": "a" * 40,
            },
            "validation": [{"command": "./validate.sh", "result": "passed"}],
            "documentation_updated": True,
            "integration_requirements": ["run acceptance"],
            "rollback_revision": None,
            "contains_secrets": False,
        }
        path = self.root / "handoff.json"
        mutations = [
            ("userinfo URL", lambda value: value["source"].update(repository_url="https://user@example.invalid/a.git")),
            ("non-http URL", lambda value: value["source"].update(repository_url="ssh://example.invalid/a.git")),
            ("malformed authority", lambda value: value["source"].update(repository_url="https://example.invalid:notaport/a.git")),
            ("non-string requirement", lambda value: value.update(integration_requirements=[{"action": "run"}])),
            ("unbounded requirement", lambda value: value.update(integration_requirements=["x" * 4097])),
            ("requirement secret", lambda value: value.update(integration_requirements=["password=supersecret"])),
            ("command secret", lambda value: value.update(validation=[{"command": "TOKEN=ghp_" + "a" * 24, "result": "passed"}])),
            ("generic credential assignment", lambda value: value.update(validation=[{"command": "DEPLOY_CREDENTIAL=correct-horse-battery-staple ./validate.sh", "result": "passed"}])),
        ]
        for label, mutate in mutations:
            with self.subTest(label=label):
                candidate = json.loads(json.dumps(handoff))
                mutate(candidate)
                path.write_text(json.dumps(candidate), encoding="utf-8")
                with self.assertRaises(validator.ValidationError):
                    validator.validate_handoff(path)

        credential_assignment = json.loads(json.dumps(handoff))
        credential_assignment["validation"][0]["command"] = (
            "DEPLOY_CREDENTIAL=correct-horse-battery-staple ./validate.sh"
        )
        path.write_text(json.dumps(credential_assignment), encoding="utf-8")
        with self.assertRaisesRegex(validator.ValidationError, "secret-like material"):
            validator.validate_handoff(path)

    def test_system_task_requires_canonical_regular_lock_without_symlinks(self) -> None:
        revision = "a" * 40
        manifest = self._basic_manifest(revision=revision, delivery_state="locked")
        manifest_path = self._write_manifest(manifest)
        with tempfile.TemporaryDirectory() as outside:
            outside_lock = Path(outside) / "lock.yaml"
            self._write_lock(outside_lock, revision)
            with self.assertRaisesRegex(validator.ValidationError, "components/lock.yaml"):
                validator.validate_system_task(self.root, "TASK-001", manifest_path, outside_lock)

            lock_path = self.root / "components" / "lock.yaml"
            lock_path.parent.mkdir()
            lock_path.symlink_to(outside_lock)
            with self.assertRaisesRegex(validator.ValidationError, "symlink"):
                validator.validate_system_task(self.root, "TASK-001", manifest_path, lock_path)

    def test_component_checkout_and_task_reject_symlinks(self) -> None:
        component = self.root / "component-a"
        (component / "tasks").mkdir(parents=True)
        (component / "PROJECT.md").write_text("Project ID: component-a\n", encoding="utf-8")
        component_task = component / "tasks" / "TASK-002.md"
        component_task.write_text(
            "# TASK-002: Build\n\nStatus: Completed\nType: Component\n"
            "Parent System Task: integration-project:TASK-001\n",
            encoding="utf-8",
        )
        manifest = self._basic_manifest(task="component-a:TASK-002")
        manifest_path = self._write_manifest(manifest)

        with tempfile.TemporaryDirectory() as outside:
            outside_root = Path(outside) / "component-a"
            outside_root.symlink_to(component, target_is_directory=True)
            with self.assertRaisesRegex(validator.ValidationError, "component root.*symlink"):
                validator.validate_system_task(
                    self.root, "TASK-001", manifest_path, None, {"component-a": outside_root}
                )

            external_task = Path(outside) / "TASK-002.md"
            external_task.write_text(component_task.read_text(encoding="utf-8"), encoding="utf-8")
            component_task.unlink()
            component_task.symlink_to(external_task)
            with self.assertRaisesRegex(validator.ValidationError, "Component Task.*symlink"):
                validator.validate_system_task(
                    self.root, "TASK-001", manifest_path, None, {"component-a": component}
                )

    @unittest.skipIf(os.name == "nt", "Windows symlink creation is permission-dependent")
    def test_platform_symlink_ancestor_does_not_invalidate_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as outside:
            outside_root = Path(outside)
            real_parent = outside_root / "real"
            checkout = real_parent / "checkout"
            checkout.mkdir(parents=True)
            alias_parent = outside_root / "alias"
            alias_parent.symlink_to(real_parent, target_is_directory=True)
            candidate = alias_parent / "checkout"
            self.assertEqual(
                validator.require_repository_directory(candidate, "integration root"),
                candidate,
            )

    def test_repository_relative_evidence_must_be_regular_integration_file(self) -> None:
        revision = "a" * 40
        manifest = self._basic_manifest(revision=revision, delivery_state="locked")
        manifest["integration"]["state"] = "verified"
        manifest["integration"]["validation_evidence"] = ["evidence/result.txt"]
        manifest_path = self._write_manifest(manifest)
        lock_path = self.root / "components" / "lock.yaml"
        self._write_lock(lock_path, revision)

        with self.assertRaisesRegex(validator.ValidationError, "regular file"):
            validator.validate_system_task(self.root, "TASK-001", manifest_path, lock_path)

        with tempfile.TemporaryDirectory() as outside:
            external = Path(outside) / "result.txt"
            external.write_text("passed\n", encoding="utf-8")
            evidence = self.root / "evidence" / "result.txt"
            evidence.parent.mkdir(exist_ok=True)
            evidence.symlink_to(external)
            with self.assertRaisesRegex(validator.ValidationError, "symlink"):
                validator.validate_system_task(self.root, "TASK-001", manifest_path, lock_path)

    def test_system_manifest_rejects_unknown_fields_and_malformed_component_identity(self) -> None:
        manifest = self._basic_manifest()
        manifest["unexpected"] = True
        path = self._write_manifest(manifest)
        with self.assertRaisesRegex(validator.ValidationError, "canonical schema"):
            validator.validate_system_task(self.root, "TASK-001", path, None)

        del manifest["unexpected"]
        manifest["components"][0]["repository"] = "../component-a"
        path = self._write_manifest(manifest)
        with self.assertRaises(validator.ValidationError):
            validator.validate_system_task(self.root, "TASK-001", path, None)

    def test_json_lock_rejects_malformed_component_identity(self) -> None:
        path = self.root / "components.lock.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "components": [
                        {
                            "name": "../component-a",
                            "repository_url": "https://example.invalid/component-a.git",
                            "source_revision": "a" * 40,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(validator.ValidationError, "invalid format"):
            validator.load_lock(path)

    def test_cli_preserves_lock_and_component_root_symlink_evidence(self) -> None:
        with mock.patch.object(validator, "validate_system_task") as validate:
            old_argv = list(validator.sys.argv)
            validator.sys.argv = [
                str(SCRIPT), "system-task", "--root", str(self.root), "--task", "TASK-001",
                "--manifest", str(self.root / "tasks/system/TASK-001.json"),
                "--lock", str(self.root / "components/lock.yaml"),
                "--component-root", "component-a=component-link",
            ]
            try:
                self.assertEqual(validator.main(), 0)
            finally:
                validator.sys.argv = old_argv
            args = validate.call_args.args
            self.assertEqual(args[3], self.root / "components/lock.yaml")
            self.assertEqual(args[4]["component-a"], Path("component-link"))

    def test_v2_separates_deployment_applicability_from_acceptance(self) -> None:
        revisions = {"runtime-a": "a" * 40, "governance-b": "b" * 40}
        component_roots = {}
        for repository, task_id in [("runtime-a", "TASK-002"), ("governance-b", "TASK-003")]:
            component_root = self.root / repository
            (component_root / "tasks").mkdir(parents=True)
            (component_root / "PROJECT.md").write_text(
                f"Project ID: {repository}\n", encoding="utf-8"
            )
            (component_root / "tasks" / f"{task_id}.md").write_text(
                f"# {task_id}: Build\n\n"
                "Status: Completed\n"
                "Type: Component\n"
                "Parent System Task: integration-project:TASK-001\n",
                encoding="utf-8",
            )
            component_roots[repository] = component_root

        manifest = {
            "schema_version": 2,
            "system_task": "integration-project:TASK-001",
            "system_id": "example-system",
            "integration_project": "integration-project",
            "extensions": {"owner": "integration-test"},
            "components": [
                {
                    "repository": "runtime-a",
                    "task": "runtime-a:TASK-002",
                    "repository_url": "https://example.invalid/runtime-a.git",
                    "branch": "main",
                    "revision": revisions["runtime-a"],
                    "source_state": "merged",
                    "acceptance_state": "verified",
                    "deployment": {
                        "applicability": "required",
                        "state": "deployed",
                        "evidence": [
                            {
                                "ref": "evidence/production-release.json",
                                "summary": "Runtime A is deployed.",
                            }
                        ],
                    },
                    "extensions": {},
                },
                {
                    "repository": "governance-b",
                    "task": "governance-b:TASK-003",
                    "repository_url": "https://example.invalid/governance-b.git",
                    "branch": "main",
                    "revision": revisions["governance-b"],
                    "source_state": "merged",
                    "acceptance_state": "locked",
                    "deployment": {
                        "applicability": "not-applicable",
                        "state": "not-applicable",
                        "evidence": [],
                    },
                    "extensions": {"role": "governance"},
                },
            ],
            "integration": {
                "verification_state": "verified",
                "validation_evidence": [
                    {
                        "ref": "evidence/system-acceptance.txt",
                        "summary": "The locked graph passed integration acceptance.",
                    }
                ],
                "deployment_state": "deployed",
                "deployment_evidence": [
                    {"ref": "evidence/production-release.json"}
                ],
                "rollback": {"ref": "docs/rollback.md"},
                "extensions": {},
            },
        }
        manifest_path = self._write_manifest(manifest)
        lock_path = self.root / "components" / "lock.json"
        lock_path.parent.mkdir()
        lock_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "components": [
                        {
                            "name": name,
                            "repository_url": f"https://example.invalid/{name}.git",
                            "source_revision": revision,
                        }
                        for name, revision in revisions.items()
                    ],
                }
            ),
            encoding="utf-8",
        )
        validator.validate_system_task(
            self.root,
            "TASK-001",
            manifest_path,
            lock_path,
            component_roots,
        )

    def test_v2_rejects_false_deployed_integration(self) -> None:
        component_root = self.root / "runtime-a"
        (component_root / "tasks").mkdir(parents=True)
        (component_root / "PROJECT.md").write_text(
            "Project ID: runtime-a\n", encoding="utf-8"
        )
        (component_root / "tasks" / "TASK-002.md").write_text(
            "# TASK-002: Build\n\n"
            "Status: Completed\n"
            "Type: Component\n"
            "Parent System Task: integration-project:TASK-001\n",
            encoding="utf-8",
        )
        manifest = {
            "schema_version": 2,
            "system_task": "integration-project:TASK-001",
            "system_id": "example-system",
            "integration_project": "integration-project",
            "components": [
                {
                    "repository": "runtime-a",
                    "task": "runtime-a:TASK-002",
                    "repository_url": "https://example.invalid/runtime-a.git",
                    "branch": "main",
                    "revision": None,
                    "source_state": "pending",
                    "acceptance_state": "pending",
                    "deployment": {
                        "applicability": "required",
                        "state": "pending",
                        "evidence": [],
                    },
                }
            ],
            "integration": {
                "verification_state": "pending",
                "validation_evidence": [],
                "deployment_state": "deployed",
                "deployment_evidence": [
                    {"ref": "evidence/production-release.json"}
                ],
                "rollback": {"ref": "docs/rollback.md"},
            },
        }
        path = self._write_manifest(manifest)
        with self.assertRaisesRegex(validator.ValidationError, "all required components"):
            validator.validate_system_task(
                self.root,
                "TASK-001",
                path,
                None,
                {"runtime-a": component_root},
            )

    def test_v2_evidence_requires_a_stable_ref(self) -> None:
        value = {"summary": "A narrative is not evidence."}
        with self.assertRaisesRegex(validator.ValidationError, "must contain ref"):
            validator.require_evidence_v2(value, "evidence", self.root)

    def _basic_manifest(
        self,
        *,
        task: str | None = None,
        revision: str | None = None,
        delivery_state: str = "pending",
    ) -> dict[str, object]:
        component = {
            "repository": "component-a",
            "task": task,
            "repository_url": "https://example.invalid/component-a.git",
            "branch": "main",
            "revision": revision,
            "delivery_state": delivery_state,
        }
        if task is None:
            component["task_absence_reason"] = "work-predates-protocol"
        return {
            "schema_version": 1,
            "system_task": "integration-project:TASK-001",
            "system_id": "example-system",
            "integration_project": "integration-project",
            "components": [component],
            "integration": {
                "state": "pending",
                "validation_evidence": [],
                "deployment_evidence": [],
                "rollback": None,
            },
        }

    def _write_manifest(self, manifest: dict[str, object]) -> Path:
        path = self.root / "tasks" / "system" / "TASK-001.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return path

    @staticmethod
    def _write_lock(path: Path, revision: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "components:\n  - name: component-a\n    source_revision: " + revision + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()

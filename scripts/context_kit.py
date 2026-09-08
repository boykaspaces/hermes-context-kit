#!/usr/bin/env python3
"""Bootstrap, inspect, validate, and plan Context Kit project adoption."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


KIT_ROOT = Path(__file__).resolve().parents[1]
VERSION_RE = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?")
PROJECT_ID_RE = re.compile(r"^Project ID:\s*([a-z0-9][a-z0-9-]*)\s*$", re.MULTILINE)
PROJECT_NAME_RE = re.compile(r"^Name:\s*(\S.*?)\s*$", re.MULTILINE)
PROJECT_STATUS_RE = re.compile(r"^Status:\s*(Active|Paused|Archived)\s*$", re.MULTILINE)
STATE_PROJECT_RE = re.compile(r"^Project:\s*([a-z0-9][a-z0-9-]*)\s*$", re.MULTILINE)
ACTIVE_TASK_RE = re.compile(r"^Active Task:\s*(\S+)\s*$", re.MULTILINE)
TASK_STATUS_RE = re.compile(
    r"^Status:\s*(Planned|In Progress|Blocked|Completed|Cancelled)\s*$",
    re.MULTILINE,
)
TASK_ID_RE = re.compile(r"TASK-\d{3,}")
SHA_RE = re.compile(r"[0-9a-f]{40}")
FEATURES = {"tasks", "decisions", "checkpoints", "memory", "multi-repo"}
MANIFEST_PATH = ".context-kit/manifest.json"
LEGACY_MANIFEST_PATH = ".hermes/context-kit.json"
ARTIFACT_PATHS = {
    "project": "PROJECT.md",
    "manifest": MANIFEST_PATH,
    "state": ".context-kit/state.md",
    "context-index": ".context-kit/index.md",
    "task-index": "tasks/README.md",
    "current-task": "tasks/current.md",
    "system-task-index": "tasks/system/README.md",
    "decision-index": "docs/decisions/README.md",
    "component-lock": "components/lock.json",
    "checkpoint-index": ".context-kit/checkpoints/README.md",
    "memory-index": ".context-kit/memory/README.md",
}
FEATURE_ARTIFACTS = {
    "checkpoints": ["checkpoint-index"],
    "memory": ["memory-index"],
}


class ContextKitError(Exception):
    """One actionable conformance or safety failure."""


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContextKitError(f"cannot read {path}: {exc}") from exc


def load_json(path: Path) -> Any:
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ContextKitError(f"{path}: duplicate JSON key {key!r}")
            result[key] = value
        return result

    try:
        return json.loads(read_text(path), object_pairs_hook=unique_object)
    except json.JSONDecodeError as exc:
        raise ContextKitError(f"invalid JSON {path}: {exc}") from exc


def kit_version() -> str:
    value = read_text(KIT_ROOT / "VERSION").strip()
    if not VERSION_RE.fullmatch(value):
        raise ContextKitError(f"{KIT_ROOT / 'VERSION'}: invalid release version")
    return value


def is_http_url(value: Any) -> bool:
    if not isinstance(value, str) or any(character.isspace() for character in value):
        return False
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        parsed.port
    except ValueError:
        return False
    return (
        parsed.scheme in {"http", "https"}
        and bool(parsed.netloc)
        and hostname is not None
        and hostname.isascii()
        and parsed.username is None
        and parsed.password is None
    )


def profile_definition(name: str) -> dict[str, Any]:
    path = KIT_ROOT / "profiles" / name / "profile.json"
    data = load_json(path)
    if (
        not isinstance(data, dict)
        or data.get("schema_version") != 2
        or data.get("name") != name
        or not isinstance(data.get("features"), list)
        or not isinstance(data.get("optional_features"), list)
        or not isinstance(data.get("required_artifacts"), list)
    ):
        raise ContextKitError(f"{path}: invalid profile definition")
    return data


def runtime_adapter_definition(name: str) -> dict[str, Any]:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
        raise ContextKitError(f"invalid runtime adapter name {name!r}")
    path = KIT_ROOT / "adapters" / "runtime" / name / "adapter.json"
    data = load_json(path)
    required = {
        "schema_version",
        "kind",
        "name",
        "version",
        "description",
        "project_templates",
        "operator_templates",
    }
    if (
        not isinstance(data, dict)
        or set(data) != required
        or data.get("schema_version") != 1
        or data.get("kind") != "runtime"
        or data.get("name") != name
        or not isinstance(data.get("version"), int)
        or data["version"] < 1
        or not isinstance(data.get("description"), str)
        or not isinstance(data.get("project_templates"), list)
        or not isinstance(data.get("operator_templates"), list)
    ):
        raise ContextKitError(f"{path}: invalid runtime adapter definition")
    for template in data["project_templates"] + data["operator_templates"]:
        if not isinstance(template, dict) or set(template) != {"source", "target"}:
            raise ContextKitError(f"{path}: invalid project template")
        for key in ("source", "target"):
            value = template[key]
            parts = Path(value).parts if isinstance(value, str) else ()
            if (
                not isinstance(value, str)
                or Path(value).is_absolute()
                or not parts
                or parts[0] == ".git"
                or any(part in {"", ".", ".."} for part in parts)
            ):
                raise ContextKitError(f"{path}: invalid project template {key}")
        source = path.parent / template["source"]
        if source.is_symlink() or not source.is_file():
            raise ContextKitError(f"{path}: missing regular template {template['source']}")
    return data


def workflow_adapter_definition(name: str) -> dict[str, Any]:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
        raise ContextKitError(f"invalid workflow adapter name {name!r}")
    path = KIT_ROOT / "adapters" / "workflow" / name / "adapter.json"
    data = load_json(path)
    required = {"schema_version", "kind", "name", "version", "description"}
    if (
        not isinstance(data, dict)
        or set(data) != required
        or data.get("schema_version") != 1
        or data.get("kind") != "workflow"
        or data.get("name") != name
        or not isinstance(data.get("version"), int)
        or data["version"] < 1
        or not isinstance(data.get("description"), str)
    ):
        raise ContextKitError(f"{path}: invalid workflow adapter definition")
    return data


def lexical_absolute(path: Path) -> Path:
    return Path(os.path.abspath(path))


def require_root(root: Path) -> Path:
    candidate = lexical_absolute(root)
    if candidate.is_symlink():
        raise ContextKitError(f"{candidate}: project root must not be a symlink")
    if not candidate.is_dir():
        raise ContextKitError(f"{candidate}: project root must be a directory")
    return candidate


def require_project_file(root: Path, relative: str) -> Path:
    parts = Path(relative).parts
    if Path(relative).is_absolute() or not parts or parts[0] == ".git":
        raise ContextKitError(f"{relative}: project path must be relative")
    path = root / relative
    cursor = root
    for part in Path(relative).parts:
        if part in {"", ".", ".."}:
            raise ContextKitError(f"{relative}: invalid project path")
        cursor /= part
        if cursor.is_symlink():
            raise ContextKitError(f"{relative}: must not cross a symlink")
    if not path.is_file():
        raise ContextKitError(f"{relative}: required regular file is missing")
    return path


def require_safe_target(root: Path, relative: str) -> Path:
    parts = Path(relative).parts
    if Path(relative).is_absolute() or not parts or parts[0] == ".git":
        raise ContextKitError(f"{relative}: write target must be relative")
    cursor = root
    for part in Path(relative).parts:
        if part in {"", ".", ".."}:
            raise ContextKitError(f"{relative}: invalid project path")
        cursor /= part
        if cursor.is_symlink():
            raise ContextKitError(f"{relative}: write target must not cross a symlink")
    return cursor


def adoption_manifest(
    version: str,
    profile: dict[str, Any],
    optional_features: list[str] | None = None,
    runtime_adapters: list[dict[str, Any]] | None = None,
    workflow_adapter: dict[str, Any] | None = None,
    extensions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    selected = list(profile["features"])
    for feature in optional_features or []:
        if feature not in selected:
            selected.append(feature)
    return {
        "schema_version": 2,
        "spec_version": 2,
        "kit_version": version,
        "profile": profile["name"],
        "features": selected,
        "runtime_adapters": [
            {"name": adapter["name"], "version": adapter["version"]}
            for adapter in runtime_adapters or []
        ],
        "workflow_adapter": (
            {
                "name": workflow_adapter["name"],
                "version": workflow_adapter["version"],
            }
            if workflow_adapter is not None
            else None
        ),
        "extensions": extensions or {},
    }


def project_markdown(project_id: str, name: str, goal: str, profile: str) -> str:
    entries = [
        "| [`.context-kit/manifest.json`](./.context-kit/manifest.json) | Adopted protocol, release, profile, and adapters | Validating or upgrading context |",
        "| [`.context-kit/state.md`](./.context-kit/state.md) | Current project summary | Asking what is active now |",
    ]
    if profile != "minimal":
        entries.extend(
            [
                "| [`.context-kit/index.md`](./.context-kit/index.md) | Current-first context router | Entering or resuming project work |",
                "| [`tasks/current.md`](./tasks/current.md) | Primary active Task pointer | Continuing the current workstream |",
                "| [`docs/decisions/README.md`](./docs/decisions/README.md) | Durable decision index | Work depends on a lasting decision |",
            ]
        )
    return (
        f"# {name}\n\n"
        f"Project ID: {project_id}\n"
        f"Name: {name}\n"
        "Status: Active\n\n"
        "## Goal\n\n"
        f"{goal}\n\n"
        "## Context entry points\n\n"
        "| Artifact | Purpose | Read when |\n"
        "|---|---|---|\n"
        + "\n".join(entries)
        + "\n"
    )


def state_markdown(project_id: str, goal: str) -> str:
    return (
        "# Project State\n\n"
        f"Project: {project_id}\n"
        "Status: Active\n"
        "Active Task: None\n\n"
        "## Current summary\n\n"
        f"{goal}\n\n"
        "## Primary focus\n\n"
        "No active Task. Create one only when meaningful work needs persistent tracking.\n"
    )


def context_index(project_id: str, profile: str) -> str:
    rows = [
        "| [`../PROJECT.md`](../PROJECT.md) | Stable | Project identity and entry pointers | Entering the project |",
        "| [`manifest.json`](./manifest.json) | Pinned | Adopted protocol, release, profile, and adapters | Validating or upgrading context |",
        "| [`state.md`](./state.md) | Current | Project-level current summary | Asking for current state |",
        "| [`../tasks/current.md`](../tasks/current.md) | Current | Primary active Task pointer | Resuming current work |",
        "| [`../tasks/README.md`](../tasks/README.md) | Active index | Task routing | Reviewing or switching workstreams |",
        "| [`../docs/decisions/README.md`](../docs/decisions/README.md) | Active index | Durable decisions | Work depends on a lasting constraint |",
    ]
    if profile == "multi-repo":
        rows.append(
            "| [`../tasks/system/README.md`](../tasks/system/README.md) | Active index | System Task manifests | Coordinating repositories |"
        )
    return (
        "# Project Context Index\n\n"
        f"Project: {project_id}\n\n"
        "| ID or file | Status | Description | Read when |\n"
        "|---|---|---|---|\n"
        + "\n".join(rows)
        + "\n"
    )


def static_files(
    project_id: str,
    name: str,
    goal: str,
    profile: dict[str, Any],
    version: str,
    optional_features: list[str] | None = None,
    runtime_adapters: list[dict[str, Any]] | None = None,
    workflow_adapter: dict[str, Any] | None = None,
) -> dict[str, str]:
    profile_name = profile["name"]
    files = {
        "PROJECT.md": project_markdown(project_id, name, goal, profile_name),
        MANIFEST_PATH: json.dumps(
            adoption_manifest(
                version,
                profile,
                optional_features,
                runtime_adapters,
                workflow_adapter,
            ), indent=2, sort_keys=True
        )
        + "\n",
        ".context-kit/state.md": state_markdown(project_id, goal),
    }
    if profile_name != "minimal":
        files.update(
            {
                ".context-kit/index.md": context_index(project_id, profile_name),
                "tasks/README.md": (
                    "# Task Index\n\n## In Progress\n\nNone.\n\n"
                    "## Blocked\n\nNone.\n\n## Planned\n\nNone.\n\n"
                    "## Completed\n\nNone.\n"
                ),
                "tasks/current.md": "# Current Task\n\nActive Task: None\n",
                "docs/decisions/README.md": (
                    "# Decision Index\n\n## Active\n\nNone.\n\n"
                    "## Proposed\n\nNone.\n\n"
                    "## Superseded, Deprecated, or Rejected\n\nNone.\n"
                ),
            }
        )
    if profile_name == "multi-repo":
        files.update(
            {
                "tasks/system/README.md": (
                    "# System Task Manifest Index\n\n"
                    "Add one `TASK-NNN.json` entry for each System or Deployment Task.\n"
                ),
                "components/lock.json": json.dumps(
                    {"schema_version": 1, "components": []},
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
            }
        )
    selected_features = set(profile["features"]) | set(optional_features or [])
    if "checkpoints" in selected_features:
        files[".context-kit/checkpoints/README.md"] = (
            "# Checkpoint Index\n\nCurrent: None\nCurrent Task: None\n"
            "Status: Current\nArchive: `archive/`\n"
        )
    if "memory" in selected_features:
        files[".context-kit/memory/README.md"] = (
            "# Project Memory Index\n\nNo project memory entries.\n"
        )
    values = {
        "project_id": project_id,
        "project_name": name,
        "project_goal": goal,
    }
    for adapter in runtime_adapters or []:
        adapter_root = KIT_ROOT / "adapters" / "runtime" / adapter["name"]
        for template in adapter["project_templates"]:
            target = template["target"]
            if target in files:
                raise ContextKitError(
                    f"runtime adapter {adapter['name']} conflicts at {target}"
                )
            rendered = read_text(adapter_root / template["source"])
            for key, value in values.items():
                rendered = rendered.replace("{{" + key + "}}", value)
            files[target] = rendered
    return files


def validate_adoption(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    if not (root / MANIFEST_PATH).is_file() and (root / LEGACY_MANIFEST_PATH).is_file():
        raise ContextKitError(
            f"{LEGACY_MANIFEST_PATH}: legacy v1 adoption; run migrate --to-spec 2"
        )
    manifest_path = require_project_file(root, MANIFEST_PATH)
    data = load_json(manifest_path)
    required = {
        "schema_version",
        "spec_version",
        "kit_version",
        "profile",
        "features",
        "runtime_adapters",
        "workflow_adapter",
    }
    allowed = required | {"extensions"}
    if not isinstance(data, dict) or not required <= set(data) or not set(data) <= allowed:
        raise ContextKitError(f"{manifest_path}: invalid adoption manifest fields")
    if data["schema_version"] != 2 or data["spec_version"] != 2:
        raise ContextKitError(f"{manifest_path}: unsupported adoption/spec version")
    if not isinstance(data["kit_version"], str) or not VERSION_RE.fullmatch(data["kit_version"]):
        raise ContextKitError(f"{manifest_path}: invalid kit_version")
    if data["kit_version"] != kit_version():
        raise ContextKitError(
            f"{manifest_path}: pinned Kit {data['kit_version']} differs from "
            f"validator {kit_version()}; use the pinned release or migrate"
        )
    if data.get("extensions", {}) is not None and not isinstance(data.get("extensions", {}), dict):
        raise ContextKitError(f"{manifest_path}: extensions must be an object")
    profile_name = data.get("profile")
    if profile_name not in {"minimal", "repository", "multi-repo"}:
        raise ContextKitError(f"{manifest_path}: unknown profile {profile_name!r}")
    profile = profile_definition(profile_name)
    features = data.get("features")
    required_features = set(profile["features"])
    optional_features = set(profile["optional_features"])
    if (
        not isinstance(features, list)
        or len(features) != len(set(features))
        or any(feature not in FEATURES for feature in features)
        or not required_features <= set(features)
        or not set(features) <= required_features | optional_features
    ):
        raise ContextKitError(f"{manifest_path}: features differ from profile")
    runtime_adapters = data.get("runtime_adapters")
    if not isinstance(runtime_adapters, list):
        raise ContextKitError(f"{manifest_path}: runtime_adapters must be a list")
    names: set[str] = set()
    for adapter in runtime_adapters:
        if (
            not isinstance(adapter, dict)
            or set(adapter) != {"name", "version"}
            or not isinstance(adapter.get("name"), str)
            or not isinstance(adapter.get("version"), int)
        ):
            raise ContextKitError(f"{manifest_path}: invalid runtime adapter entry")
        if adapter["name"] in names:
            raise ContextKitError(
                f"{manifest_path}: duplicate runtime adapter {adapter['name']}"
            )
        definition = runtime_adapter_definition(adapter["name"])
        if definition["version"] != adapter["version"]:
            raise ContextKitError(
                f"{manifest_path}: runtime adapter {adapter['name']} version differs"
            )
        names.add(adapter["name"])
    workflow_adapter = data.get("workflow_adapter")
    if workflow_adapter is not None:
        if (
            not isinstance(workflow_adapter, dict)
            or set(workflow_adapter) != {"name", "version"}
            or not isinstance(workflow_adapter.get("name"), str)
            or not isinstance(workflow_adapter.get("version"), int)
        ):
            raise ContextKitError(f"{manifest_path}: invalid workflow adapter")
        definition = workflow_adapter_definition(workflow_adapter["name"])
        if definition["version"] != workflow_adapter["version"]:
            raise ContextKitError(
                f"{manifest_path}: workflow adapter {workflow_adapter['name']} version differs"
            )
    return data, profile


def validate_project(root_arg: Path) -> None:
    root = require_root(root_arg)
    adoption, profile = validate_adoption(root)
    for artifact in profile["required_artifacts"]:
        relative = ARTIFACT_PATHS.get(artifact)
        if relative is None:
            raise ContextKitError(f"profile defines unknown artifact {artifact!r}")
        require_project_file(root, relative)
    for feature in adoption["features"]:
        for artifact in FEATURE_ARTIFACTS.get(feature, []):
            require_project_file(root, ARTIFACT_PATHS[artifact])

    project_text = read_text(root / "PROJECT.md")
    project_match = PROJECT_ID_RE.search(project_text)
    if not project_match or not PROJECT_NAME_RE.search(project_text):
        raise ContextKitError("PROJECT.md: missing stable project identity")
    if not PROJECT_STATUS_RE.search(project_text):
        raise ContextKitError("PROJECT.md: invalid or missing project Status")
    project_id = project_match.group(1)

    state_text = read_text(root / ".context-kit/state.md")
    state_project = STATE_PROJECT_RE.search(state_text)
    active_state = ACTIVE_TASK_RE.search(state_text)
    if not state_project or state_project.group(1) != project_id or not active_state:
        raise ContextKitError(".context-kit/state.md: project identity or Active Task differs")

    if profile["name"] != "minimal":
        current_text = read_text(root / "tasks/current.md")
        active_current = ACTIVE_TASK_RE.search(current_text)
        if not active_current or active_current.group(1) != active_state.group(1):
            raise ContextKitError("tasks/current.md: Active Task differs from project state")
        active = active_current.group(1)
        if active != "None":
            if not TASK_ID_RE.fullmatch(active):
                raise ContextKitError("tasks/current.md: invalid Active Task")
            task_path = require_project_file(root, f"tasks/{active}.md")
            status = TASK_STATUS_RE.search(read_text(task_path))
            if not status or status.group(1) not in {"In Progress", "Blocked"}:
                raise ContextKitError(f"{task_path}: active Task must be In Progress or Blocked")
            if active not in read_text(root / "tasks/README.md"):
                raise ContextKitError(f"tasks/README.md: {active} is not indexed")

    if profile["name"] == "multi-repo":
        lock = load_json(root / "components/lock.json")
        if not isinstance(lock, dict) or lock.get("schema_version") != 1:
            raise ContextKitError("components/lock.json: invalid schema")
        components = lock.get("components")
        if not isinstance(components, list):
            raise ContextKitError("components/lock.json: components must be a list")
        names: set[str] = set()
        for component in components:
            if (
                not isinstance(component, dict)
                or not {"name", "repository_url", "source_revision"} <= set(component)
                or not isinstance(component["name"], str)
                or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", component["name"])
                or not is_http_url(component["repository_url"])
                or not isinstance(component["source_revision"], str)
                or not SHA_RE.fullmatch(component["source_revision"])
            ):
                raise ContextKitError("components/lock.json: invalid component entry")
            if component["name"] in names:
                raise ContextKitError(
                    f"components/lock.json: duplicate component {component['name']}"
                )
            names.add(component["name"])
    print(f"context-kit-ok: {project_id} ({profile['name']})")


def init_project(args: argparse.Namespace) -> None:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", args.project_id):
        raise ContextKitError("project ID must use lowercase letters, digits, and hyphens")
    version = kit_version()
    profile = profile_definition(args.profile)
    root = lexical_absolute(args.root)
    if root.exists() and (root.is_symlink() or not root.is_dir()):
        raise ContextKitError(f"{root}: target must be a directory, not a symlink")
    requested_features = args.feature or []
    adapter_names = getattr(args, "runtime_adapter", []) or []
    if len(adapter_names) != len(set(adapter_names)):
        raise ContextKitError("runtime adapters must be unique")
    runtime_adapters = [runtime_adapter_definition(name) for name in adapter_names]
    workflow_name = getattr(args, "workflow_adapter", None)
    workflow_adapter = (
        workflow_adapter_definition(workflow_name) if workflow_name else None
    )
    unsupported = sorted(set(requested_features) - set(profile["optional_features"]))
    if unsupported:
        raise ContextKitError(
            f"profile {args.profile} does not allow optional features: {', '.join(unsupported)}"
        )
    files = static_files(
        args.project_id,
        args.name,
        args.goal,
        profile,
        version,
        requested_features,
        runtime_adapters,
        workflow_adapter,
    )
    for relative in files:
        require_safe_target(root, relative)
    conflicts = [
        relative
        for relative, content in files.items()
        if (root / relative).exists()
        and (
            not (root / relative).is_file()
            or read_text(root / relative) != content
        )
    ]
    if conflicts:
        raise ContextKitError(
            "initialization would overwrite existing paths: " + ", ".join(conflicts)
        )
    pending = [relative for relative in files if not (root / relative).exists()]
    if args.dry_run:
        print(f"would initialize {args.project_id} with profile {args.profile}")
        for relative in pending:
            print(f"create {relative}")
        print_runtime_next_steps(adapter_names)
        return
    root.mkdir(parents=True, exist_ok=True)
    for relative in pending:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(files[relative], encoding="utf-8")
    validate_project(root)
    print_runtime_next_steps(adapter_names)


def print_runtime_next_steps(adapter_names: list[str]) -> None:
    if "hermes" in adapter_names:
        print(
            "next: complete Hermes Skill-first setup with "
            "adapters/runtime/hermes/scripts/runtime_setup.py"
        )
        print(
            "optional after Skill verification: show the SOUL reinforcement "
            "and apply it only if the user chooses"
        )


def infer_profile(root: Path) -> str:
    if (root / "tasks" / "system").is_dir() or (root / "components" / "lock.yaml").is_file():
        return "multi-repo"
    if (root / "tasks").is_dir() or (root / "docs" / "decisions").is_dir():
        return "repository"
    return "minimal"


def legacy_features(root: Path, manifest: dict[str, Any] | None) -> list[str]:
    if manifest is not None:
        features = manifest.get("features")
        if not isinstance(features, list) or any(
            not isinstance(feature, str) or feature not in FEATURES
            for feature in features
        ):
            raise ContextKitError(f"{LEGACY_MANIFEST_PATH}: invalid features")
        return features
    inferred: list[str] = []
    checks = {
        "checkpoints": ".hermes/checkpoints/README.md",
        "memory": ".hermes/memory/README.md",
    }
    for feature, relative in checks.items():
        if (root / relative).is_file():
            inferred.append(feature)
    return inferred


def migration_files(
    root: Path,
    profile: dict[str, Any],
    features: list[str],
    runtime_adapters: list[dict[str, Any]],
    workflow_adapter: dict[str, Any] | None = None,
    extensions: dict[str, Any] | None = None,
) -> dict[str, str]:
    files = {
        MANIFEST_PATH: json.dumps(
            adoption_manifest(
                kit_version(),
                profile,
                features,
                runtime_adapters,
                workflow_adapter,
                extensions,
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    }
    mappings = {
        ".hermes/state.md": ".context-kit/state.md",
        ".hermes/context-index.md": ".context-kit/index.md",
        ".hermes/checkpoints/README.md": ".context-kit/checkpoints/README.md",
        ".hermes/memory/README.md": ".context-kit/memory/README.md",
    }
    for source_relative, target_relative in mappings.items():
        source = root / source_relative
        if source.is_symlink():
            raise ContextKitError(f"{source_relative}: migration source must not be a symlink")
        if source.is_file():
            content = read_text(source)
            if target_relative == ".context-kit/index.md":
                content = content.replace("context-kit.json", "manifest.json")
            files[target_relative] = content
    for tree_name in ("checkpoints", "memory"):
        source_root = root / ".hermes" / tree_name
        if source_root.is_symlink():
            raise ContextKitError(
                f".hermes/{tree_name}: migration source must not be a symlink"
            )
        if not source_root.is_dir():
            continue
        for source in sorted(source_root.rglob("*")):
            relative = source.relative_to(source_root)
            if source.is_symlink():
                raise ContextKitError(
                    f".hermes/{tree_name}/{relative}: migration source must not be a symlink"
                )
            if source.is_file():
                target_relative = str(Path(".context-kit") / tree_name / relative)
                files[target_relative] = read_text(source)
    for adapter in runtime_adapters:
        adapter_root = KIT_ROOT / "adapters" / "runtime" / adapter["name"]
        for template in adapter["project_templates"]:
            target = template["target"]
            existing = root / target
            if existing.is_symlink():
                raise ContextKitError(f"{target}: adapter target must not be a symlink")
            if existing.is_file():
                expected = read_text(adapter_root / template["source"])
                if read_text(existing) != expected:
                    raise ContextKitError(
                        f"{target}: requires reviewed {adapter['name']} adapter integration"
                    )
                continue
            if target in files:
                raise ContextKitError(
                    f"runtime adapter {adapter['name']} conflicts at {target}"
                )
            files[target] = read_text(adapter_root / template["source"])
    return files


def migrate_project(args: argparse.Namespace) -> None:
    root = require_root(args.root)
    adoption_path = root / MANIFEST_PATH
    if adoption_path.exists():
        validate_project(root)
        print("already adopted; no migration required")
        return
    require_project_file(root, "PROJECT.md")
    legacy_path = root / LEGACY_MANIFEST_PATH
    legacy_manifest = load_json(legacy_path) if legacy_path.is_file() else None
    if legacy_manifest is not None:
        if (
            not isinstance(legacy_manifest, dict)
            or legacy_manifest.get("schema_version") != 1
            or legacy_manifest.get("spec_version") != 1
        ):
            raise ContextKitError(f"{LEGACY_MANIFEST_PATH}: unsupported legacy manifest")
        legacy_extensions = legacy_manifest.get("extensions", {})
        if not isinstance(legacy_extensions, dict):
            raise ContextKitError(f"{LEGACY_MANIFEST_PATH}: extensions must be an object")
    else:
        legacy_extensions = {}
    profile_name = args.profile or (
        legacy_manifest.get("profile") if legacy_manifest is not None else infer_profile(root)
    )
    profile = profile_definition(profile_name)
    if profile_name == "multi-repo" and not (root / "components" / "lock.json").is_file():
        print("manual migration required: project uses legacy components/lock.yaml")
        print("create components/lock.json from accepted source revisions before applying")
        return
    adapter_names = getattr(args, "runtime_adapter", []) or []
    if len(adapter_names) != len(set(adapter_names)):
        raise ContextKitError("runtime adapters must be unique")
    runtime_adapters = [runtime_adapter_definition(name) for name in adapter_names]
    workflow_name = getattr(args, "workflow_adapter", None)
    workflow_adapter = (
        workflow_adapter_definition(workflow_name) if workflow_name else None
    )
    features = legacy_features(root, legacy_manifest)
    files = migration_files(
        root,
        profile,
        features,
        runtime_adapters,
        workflow_adapter,
        legacy_extensions,
    )
    missing_artifacts = [
        ARTIFACT_PATHS[artifact]
        for artifact in profile["required_artifacts"]
        if artifact != "manifest"
        and not (root / ARTIFACT_PATHS[artifact]).is_file()
        and ARTIFACT_PATHS[artifact] not in files
    ]
    if missing_artifacts:
        raise ContextKitError(
            "migration requires existing owners: " + ", ".join(missing_artifacts)
        )
    conflicts = [
        relative
        for relative, content in files.items()
        if (root / relative).exists()
        and (
            not (root / relative).is_file()
            or read_text(root / relative) != content
        )
    ]
    if conflicts:
        raise ContextKitError(
            "migration would overwrite existing paths: " + ", ".join(conflicts)
        )
    pending = [relative for relative in files if not (root / relative).exists()]
    print(f"would migrate profile {profile_name} to project spec v2")
    for relative in pending:
        print(f"create {relative}")
    if legacy_manifest is not None:
        print("retain legacy .hermes files for reviewed removal after validation")
        print("next: review project/runtime links, then remove legacy duplicates in the accepted proposal")
    if args.apply:
        for relative in pending:
            require_safe_target(root, relative)
        created: list[Path] = []
        try:
            for relative in pending:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("x", encoding="utf-8") as handle:
                    handle.write(files[relative])
                created.append(target)
            validate_project(root)
        except ContextKitError:
            for target in reversed(created):
                if target.is_file() and not target.is_symlink():
                    target.unlink()
            raise
        except OSError as exc:
            for target in reversed(created):
                if target.is_file() and not target.is_symlink():
                    target.unlink()
            raise ContextKitError(f"cannot apply migration: {exc}") from exc


def doctor_project(root: Path) -> None:
    try:
        validate_project(root)
    except ContextKitError as exc:
        print(f"context-kit-doctor: {exc}", file=sys.stderr)
        print(
            "next: run migrate --check for a legacy project or repair the reported owner",
            file=sys.stderr,
        )
        raise


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="initialize a new project without overwriting files")
    init.add_argument("--root", type=Path, required=True)
    init.add_argument("--project-id", required=True)
    init.add_argument("--name", required=True)
    init.add_argument("--goal", required=True)
    init.add_argument(
        "--profile",
        choices=["minimal", "repository", "multi-repo"],
        default="minimal",
    )
    init.add_argument(
        "--feature",
        action="append",
        choices=["checkpoints", "memory"],
        default=[],
        help="enable one optional feature; may be repeated",
    )
    init.add_argument(
        "--runtime-adapter",
        action="append",
        default=[],
        help="bind one runtime adapter; may be repeated",
    )
    init.add_argument(
        "--workflow-adapter",
        help="bind one workflow adapter",
    )
    init.add_argument("--dry-run", action="store_true")

    validate = commands.add_parser("validate", help="validate an adopted project")
    validate.add_argument("--root", type=Path, required=True)

    doctor = commands.add_parser("doctor", help="diagnose one adoption without mutation")
    doctor.add_argument("--root", type=Path, required=True)

    migrate = commands.add_parser("migrate", help="plan or apply legacy adoption metadata")
    migrate.add_argument("--root", type=Path, required=True)
    migrate.add_argument("--profile", choices=["minimal", "repository", "multi-repo"])
    migrate.add_argument("--to-spec", type=int, choices=[2], default=2)
    migrate.add_argument(
        "--runtime-adapter",
        action="append",
        default=[],
        help="bind one runtime adapter; may be repeated",
    )
    migrate.add_argument(
        "--workflow-adapter",
        help="bind one workflow adapter",
    )
    mode = migrate.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "init":
            init_project(args)
        elif args.command == "validate":
            validate_project(args.root)
        elif args.command == "doctor":
            doctor_project(args.root)
        else:
            migrate_project(args)
    except ContextKitError as exc:
        if args.command != "doctor":
            print(f"context-kit failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

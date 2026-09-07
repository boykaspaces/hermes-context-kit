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
FEATURE_PATHS = {
    "checkpoints": [".hermes/checkpoints/README.md"],
    "memory": [".hermes/memory/README.md"],
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


def profile_definition(name: str) -> dict[str, Any]:
    path = KIT_ROOT / "profiles" / name / "profile.json"
    data = load_json(path)
    if (
        not isinstance(data, dict)
        or data.get("schema_version") != 1
        or data.get("name") != name
        or not isinstance(data.get("features"), list)
        or not isinstance(data.get("optional_features"), list)
        or not isinstance(data.get("required_paths"), list)
    ):
        raise ContextKitError(f"{path}: invalid profile definition")
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
    cursor = root
    for part in Path(relative).parts:
        if part in {"", ".", ".."}:
            raise ContextKitError(f"{relative}: invalid project path")
        cursor /= part
        if cursor.is_symlink():
            raise ContextKitError(f"{relative}: write target must not cross a symlink")
    return cursor


def adoption_manifest(
    version: str, profile: dict[str, Any], optional_features: list[str] | None = None
) -> dict[str, Any]:
    selected = list(profile["features"])
    for feature in optional_features or []:
        if feature not in selected:
            selected.append(feature)
    return {
        "schema_version": 1,
        "spec_version": 1,
        "kit_version": version,
        "profile": profile["name"],
        "features": selected,
        "extensions": {},
    }


def project_markdown(project_id: str, name: str, goal: str, profile: str) -> str:
    entries = [
        "| [`.hermes/state.md`](./.hermes/state.md) | Current project summary | Asking what is active now |"
    ]
    if profile != "minimal":
        entries.extend(
            [
                "| [`.hermes/context-index.md`](./.hermes/context-index.md) | Current-first context router | Entering or resuming project work |",
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


def agents_markdown(profile: str) -> str:
    extra = ""
    if profile == "multi-repo":
        extra = (
            "- Use the multi-repository profile for System Tasks, immutable "
            "component locks, Handoffs, and integration evidence.\n"
        )
    return (
        "# Repository AI Instructions\n\n"
        "- Start with `PROJECT.md` and follow the narrowest current pointer.\n"
        "- Read `.hermes/context-kit.json` before changing project context.\n"
        "- Source and configuration own implementation truth.\n"
        "- Task files own work status; ADRs own durable decisions; indexes own navigation only.\n"
        "- Never infer current state from timestamps, filename ordering, Git ref names, or conversation recency.\n"
        "- Update affected indexes whenever a path, status, or pointer changes.\n"
        "- Never commit credentials, local runtime data, or environment overrides.\n"
        + extra
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
) -> dict[str, str]:
    profile_name = profile["name"]
    files = {
        "PROJECT.md": project_markdown(project_id, name, goal, profile_name),
        "AGENTS.md": agents_markdown(profile_name),
        ".hermes/context-kit.json": json.dumps(
            adoption_manifest(version, profile, optional_features), indent=2, sort_keys=True
        )
        + "\n",
        ".hermes/state.md": state_markdown(project_id, goal),
    }
    if profile_name != "minimal":
        files.update(
            {
                ".hermes/context-index.md": context_index(project_id, profile_name),
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
        files[".hermes/checkpoints/README.md"] = (
            "# Checkpoint Index\n\nCurrent: None\nCurrent Task: None\n"
            "Status: Current\nArchive: `archive/`\n"
        )
    if "memory" in selected_features:
        files[".hermes/memory/README.md"] = (
            "# Project Memory Index\n\nNo project memory entries.\n"
        )
    return files


def validate_adoption(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest_path = require_project_file(root, ".hermes/context-kit.json")
    data = load_json(manifest_path)
    required = {"schema_version", "spec_version", "kit_version", "profile", "features"}
    allowed = required | {"extensions"}
    if not isinstance(data, dict) or not required <= set(data) or not set(data) <= allowed:
        raise ContextKitError(f"{manifest_path}: invalid adoption manifest fields")
    if data["schema_version"] != 1 or data["spec_version"] != 1:
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
    return data, profile


def validate_project(root_arg: Path) -> None:
    root = require_root(root_arg)
    adoption, profile = validate_adoption(root)
    for relative in profile["required_paths"]:
        require_project_file(root, relative)
    for feature in adoption["features"]:
        for relative in FEATURE_PATHS.get(feature, []):
            require_project_file(root, relative)

    project_text = read_text(root / "PROJECT.md")
    project_match = PROJECT_ID_RE.search(project_text)
    if not project_match or not PROJECT_NAME_RE.search(project_text):
        raise ContextKitError("PROJECT.md: missing stable project identity")
    if not PROJECT_STATUS_RE.search(project_text):
        raise ContextKitError("PROJECT.md: invalid or missing project Status")
    project_id = project_match.group(1)

    state_text = read_text(root / ".hermes/state.md")
    state_project = STATE_PROJECT_RE.search(state_text)
    active_state = ACTIVE_TASK_RE.search(state_text)
    if not state_project or state_project.group(1) != project_id or not active_state:
        raise ContextKitError(".hermes/state.md: project identity or Active Task differs")

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
                or not {"name", "source_revision"} <= set(component)
                or not isinstance(component["name"], str)
                or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", component["name"])
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
        return
    root.mkdir(parents=True, exist_ok=True)
    for relative in pending:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(files[relative], encoding="utf-8")
    validate_project(root)


def infer_profile(root: Path) -> str:
    if (root / "tasks" / "system").is_dir() or (root / "components" / "lock.yaml").is_file():
        return "multi-repo"
    if (root / "tasks").is_dir() or (root / "docs" / "decisions").is_dir():
        return "repository"
    return "minimal"


def migrate_project(args: argparse.Namespace) -> None:
    root = require_root(args.root)
    adoption_path = root / ".hermes" / "context-kit.json"
    if adoption_path.exists():
        validate_project(root)
        print("already adopted; no migration required")
        return
    require_project_file(root, "PROJECT.md")
    profile_name = args.profile or infer_profile(root)
    profile = profile_definition(profile_name)
    if profile_name == "multi-repo" and not (root / "components" / "lock.json").is_file():
        print("manual migration required: project uses legacy components/lock.yaml")
        print("create components/lock.json from accepted source revisions before applying")
        return
    version = kit_version()
    inferred_features = []
    for feature, paths in FEATURE_PATHS.items():
        if all((root / relative).is_file() for relative in paths):
            inferred_features.append(feature)
    rendered = (
        json.dumps(
            adoption_manifest(version, profile, inferred_features),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    print(f"would adopt profile {profile_name}")
    print("create .hermes/context-kit.json")
    if args.apply:
        require_safe_target(root, ".hermes/context-kit.json")
        adoption_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with adoption_path.open("x", encoding="utf-8") as handle:
                handle.write(rendered)
            validate_project(root)
        except ContextKitError:
            if adoption_path.is_file() and not adoption_path.is_symlink():
                adoption_path.unlink()
            raise
        except OSError as exc:
            if adoption_path.is_file() and not adoption_path.is_symlink():
                adoption_path.unlink()
            raise ContextKitError(f"cannot write {adoption_path}: {exc}") from exc


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
    init.add_argument("--dry-run", action="store_true")

    validate = commands.add_parser("validate", help="validate an adopted project")
    validate.add_argument("--root", type=Path, required=True)

    doctor = commands.add_parser("doctor", help="diagnose one adoption without mutation")
    doctor.add_argument("--root", type=Path, required=True)

    migrate = commands.add_parser("migrate", help="plan or apply legacy adoption metadata")
    migrate.add_argument("--root", type=Path, required=True)
    migrate.add_argument("--profile", choices=["minimal", "repository", "multi-repo"])
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

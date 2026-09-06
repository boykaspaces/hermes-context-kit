#!/usr/bin/env python3
"""Offline validator for multi-repository Task context."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


TASK_ID_RE = re.compile(r"TASK-\d{3,}")
CANONICAL_TASK_RE = re.compile(r"[a-z0-9][a-z0-9-]*:TASK-\d{3,}")
SHA_RE = re.compile(r"[0-9a-f]{40}")
PROJECT_ID_RE = re.compile(r"^Project ID:\s*([a-z0-9][a-z0-9-]*)\s*$", re.MULTILINE)
FIELD_RE = re.compile(r"^([A-Za-z][A-Za-z ]+):\s*(.*?)\s*$", re.MULTILINE)
TASK_STATUSES = {"Planned", "In Progress", "Blocked", "Completed", "Cancelled"}
TASK_TYPES = {"Component", "System", "Deployment"}
DELIVERY_STATES = {"pending", "handoff-ready", "merged", "locked", "verified", "deployed"}
LOCKED_STATES = {"locked", "verified", "deployed"}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)


class ValidationError(Exception):
    pass


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValidationError(f"cannot read {path}: {exc}") from exc


def load_json(path: Path) -> Any:
    try:
        return json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON {path}: {exc}") from exc


def project_id(root: Path) -> str:
    match = PROJECT_ID_RE.search(read_text(root / "PROJECT.md"))
    if not match:
        raise ValidationError(f"{root / 'PROJECT.md'} has no valid Project ID")
    return match.group(1)


def task_fields(path: Path) -> dict[str, str]:
    text = read_text(path)
    heading = re.search(r"^#\s+(TASK-\d{3,}):", text, re.MULTILINE)
    if not heading:
        raise ValidationError(f"{path} has no stable TASK heading")
    if heading.group(1) != path.stem:
        raise ValidationError(f"{path}: heading ID differs from filename")
    fields = dict(FIELD_RE.findall(text))
    status = fields.get("Status")
    if status not in TASK_STATUSES:
        raise ValidationError(f"{path}: invalid Status {status!r}")
    task_type = fields.get("Type")
    if task_type is not None and task_type not in TASK_TYPES:
        raise ValidationError(f"{path}: invalid Type {task_type!r}")
    parent = fields.get("Parent System Task")
    if parent is not None and not CANONICAL_TASK_RE.fullmatch(parent):
        raise ValidationError(f"{path}: invalid Parent System Task {parent!r}")
    return {"id": heading.group(1), **fields}


def task_files(root: Path) -> list[Path]:
    tasks_root = root / "tasks"
    paths = sorted(tasks_root.glob("TASK-*.md"))
    completed = tasks_root / "completed"
    if completed.is_dir():
        paths.extend(sorted(completed.glob("TASK-*.md")))
    return paths


def validate_repository(root: Path) -> None:
    pid = project_id(root)
    index_path = root / "tasks" / "README.md"
    current_path = root / "tasks" / "current.md"
    index = read_text(index_path)
    current = read_text(current_path)
    seen: dict[str, dict[str, str]] = {}
    for path in task_files(root):
        fields = task_fields(path)
        task_id = fields["id"]
        if task_id in seen:
            raise ValidationError(f"duplicate Task ID {task_id}")
        seen[task_id] = fields
        if task_id not in index:
            raise ValidationError(f"{task_id} is missing from {index_path}")
        index_lines = [line for line in index.splitlines() if task_id in line]
        if not any(fields["Status"] in line for line in index_lines):
            raise ValidationError(f"{task_id}: Task Index status differs from Task file")
    match = re.search(r"^Active Task:\s*(\S+)\s*$", current, re.MULTILINE)
    if not match:
        raise ValidationError(f"{current_path}: missing Active Task pointer")
    active = match.group(1)
    if active != "None":
        if not TASK_ID_RE.fullmatch(active) or active not in seen:
            raise ValidationError(f"{current_path}: unresolved active Task {active!r}")
        if seen[active]["Status"] not in {"In Progress", "Blocked"}:
            raise ValidationError(f"{current_path}: active Task has terminal/non-active status")
    state_path = root / ".hermes" / "state.md"
    if state_path.is_file():
        state_match = re.search(r"^Active Task:\s*(\S+)\s*$", read_text(state_path), re.MULTILINE)
        if not state_match or state_match.group(1) != active:
            raise ValidationError(f"{state_path}: Active Task differs from {current_path}")
    print(f"repository-context-ok: {pid}")


def require_string(value: Any, label: str, pattern: re.Pattern[str] | None = None) -> str:
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{label} must be a non-empty string")
    if pattern is not None and not pattern.fullmatch(value):
        raise ValidationError(f"{label} has invalid format: {value!r}")
    return value


def reject_secrets(data: Any, label: str) -> None:
    rendered = json.dumps(data, sort_keys=True)
    for pattern in SECRET_PATTERNS:
        if pattern.search(rendered):
            raise ValidationError(f"{label} contains secret-like material")


def validate_handoff(path: Path) -> None:
    data = load_json(path)
    if data.get("schema_version") != 1:
        raise ValidationError("handoff schema_version must be 1")
    component = data.get("component")
    source = data.get("source")
    if not isinstance(component, dict) or not isinstance(source, dict):
        raise ValidationError("handoff component and source must be objects")
    component_name = require_string(component.get("repository"), "component.repository")
    component_task = require_string(component.get("task"), "component.task", CANONICAL_TASK_RE)
    if component_task.split(":", 1)[0] != component_name:
        raise ValidationError("component.task project differs from component.repository")
    require_string(data.get("parent_system_task"), "parent_system_task", CANONICAL_TASK_RE)
    require_string(source.get("repository_url"), "source.repository_url")
    require_string(source.get("branch"), "source.branch")
    require_string(source.get("revision"), "source.revision", SHA_RE)
    validation = data.get("validation")
    if not isinstance(validation, list) or not validation:
        raise ValidationError("handoff validation must contain at least one result")
    for result in validation:
        if not isinstance(result, dict) or result.get("result") != "passed":
            raise ValidationError("handoff validation results must be passed objects")
        require_string(result.get("command"), "validation.command")
    if data.get("documentation_updated") is not True:
        raise ValidationError("documentation_updated must be true")
    if not isinstance(data.get("integration_requirements"), list):
        raise ValidationError("integration_requirements must be a list")
    rollback = data.get("rollback_revision")
    if rollback is not None:
        require_string(rollback, "rollback_revision", SHA_RE)
    if data.get("contains_secrets") is not False:
        raise ValidationError("contains_secrets must be false")
    reject_secrets(data, str(path))
    print(f"handoff-ok: {path}")


def load_lock(path: Path) -> dict[str, str]:
    if path.suffix == ".json":
        data = load_json(path)
        components = data.get("components") if isinstance(data, dict) else None
        if not isinstance(components, list):
            raise ValidationError("JSON lock has no components list")
        result = {}
        for item in components:
            if not isinstance(item, dict):
                raise ValidationError("JSON lock component must be an object")
            name = require_string(item.get("name"), "lock component name")
            revision = require_string(item.get("source_revision"), f"lock revision for {name}", SHA_RE)
            if name in result:
                raise ValidationError(f"duplicate lock component {name}")
            result[name] = revision
        return result

    result: dict[str, str] = {}
    current: str | None = None
    for line in read_text(path).splitlines():
        name_match = re.fullmatch(r"\s{2}- name:\s*([a-z0-9][a-z0-9-]*)\s*", line)
        if name_match:
            current = name_match.group(1)
            if current in result:
                raise ValidationError(f"duplicate lock component {current}")
            continue
        revision_match = re.fullmatch(r"\s{4}source_revision:\s*([0-9a-f]{40})\s*", line)
        if revision_match and current is not None:
            result[current] = revision_match.group(1)
    if not result:
        raise ValidationError(f"no supported component revisions found in {path}")
    return result


def validate_system_task(
    root: Path,
    task_id: str,
    manifest_path: Path,
    lock_path: Path | None,
    component_roots: dict[str, Path] | None = None,
) -> None:
    pid = project_id(root)
    task_path = root / "tasks" / f"{task_id}.md"
    fields = task_fields(task_path)
    if fields.get("Type") not in {"System", "Deployment"}:
        raise ValidationError(f"{task_path}: System Task must declare Type: System or Deployment")

    data = load_json(manifest_path)
    if data.get("schema_version") != 1:
        raise ValidationError("system manifest schema_version must be 1")
    expected = f"{pid}:{task_id}"
    if data.get("system_task") != expected:
        raise ValidationError(f"system_task must be {expected}")
    if data.get("integration_project") != pid:
        raise ValidationError(f"integration_project must be {pid}")
    require_string(data.get("system_id"), "system_id")
    components = data.get("components")
    resolved_component_roots = component_roots or {}
    if not isinstance(components, list) or not components:
        raise ValidationError("system manifest must declare components")
    locks = load_lock(lock_path) if lock_path is not None else {}
    seen: set[str] = set()
    for item in components:
        if not isinstance(item, dict):
            raise ValidationError("system component must be an object")
        repository = require_string(item.get("repository"), "component.repository")
        if repository in seen:
            raise ValidationError(f"duplicate system component {repository}")
        seen.add(repository)
        require_string(item.get("repository_url"), f"{repository}.repository_url")
        require_string(item.get("branch"), f"{repository}.branch")
        task = item.get("task")
        if task is None:
            absence_reason = item.get("task_absence_reason")
            if absence_reason not in {"work-predates-protocol", "no-component-change"}:
                raise ValidationError(f"{repository}: missing Task without an allowed reason")
            if absence_reason == "no-component-change":
                require_string(
                    item.get("source_system_task"),
                    f"{repository}.source_system_task",
                    CANONICAL_TASK_RE,
                )
        else:
            canonical_task = require_string(task, f"{repository}.task", CANONICAL_TASK_RE)
            task_project, component_task_id = canonical_task.split(":", 1)
            if task_project != repository:
                raise ValidationError(f"{repository}: Task project differs from component identity")
            if repository not in resolved_component_roots:
                raise ValidationError(f"{repository}: component root is required to verify Task relationship")
            component_root = resolved_component_roots[repository]
            if project_id(component_root) != repository:
                raise ValidationError(f"{repository}: component root Project ID differs")
            component_fields = task_fields(component_root / "tasks" / f"{component_task_id}.md")
            if component_fields.get("Type") != "Component":
                raise ValidationError(f"{canonical_task}: child Task must declare Type: Component")
            if component_fields.get("Parent System Task") != expected:
                raise ValidationError(f"{canonical_task}: parent differs from {expected}")
        state = item.get("delivery_state")
        if state not in DELIVERY_STATES:
            raise ValidationError(f"{repository}: invalid delivery_state {state!r}")
        revision = item.get("revision")
        if state != "pending":
            require_string(revision, f"{repository}.revision", SHA_RE)
        if state in LOCKED_STATES:
            if repository not in locks:
                raise ValidationError(f"{repository}: absent from component lock")
            if locks[repository] != revision:
                raise ValidationError(f"{repository}: manifest revision differs from component lock")

    integration = data.get("integration")
    if not isinstance(integration, dict):
        raise ValidationError("integration must be an object")
    state = integration.get("state")
    if state not in {"pending", "verified", "deployed"}:
        raise ValidationError(f"invalid integration state {state!r}")
    validation = integration.get("validation_evidence")
    deployment = integration.get("deployment_evidence")
    if not isinstance(validation, list) or not isinstance(deployment, list):
        raise ValidationError("integration evidence fields must be lists")
    if state in {"verified", "deployed"} and not validation:
        raise ValidationError("verified integration requires validation evidence")
    if state == "deployed" and (not deployment or not integration.get("rollback")):
        raise ValidationError("deployed integration requires deployment evidence and rollback")
    reject_secrets(data, str(manifest_path))
    print(f"system-task-ok: {expected}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    repository = subparsers.add_parser("repository")
    repository.add_argument("--root", type=Path, required=True)
    handoff = subparsers.add_parser("handoff")
    handoff.add_argument("--file", type=Path, required=True)
    system = subparsers.add_parser("system-task")
    system.add_argument("--root", type=Path, required=True)
    system.add_argument("--task", required=True)
    system.add_argument("--manifest", type=Path, required=True)
    system.add_argument("--lock", type=Path)
    system.add_argument(
        "--component-root",
        action="append",
        default=[],
        metavar="PROJECT_ID=PATH",
        help="component checkout used to verify a child Task relationship",
    )
    args = parser.parse_args()

    try:
        if args.command == "repository":
            validate_repository(args.root.resolve())
        elif args.command == "handoff":
            validate_handoff(args.file.resolve())
        else:
            if not TASK_ID_RE.fullmatch(args.task):
                raise ValidationError(f"invalid Task ID {args.task!r}")
            component_roots: dict[str, Path] = {}
            for entry in args.component_root:
                if "=" not in entry:
                    raise ValidationError(f"invalid --component-root {entry!r}")
                component_name, component_path = entry.split("=", 1)
                if not component_name or not component_path or component_name in component_roots:
                    raise ValidationError(f"invalid --component-root {entry!r}")
                component_roots[component_name] = Path(component_path).resolve()
            validate_system_task(
                args.root.resolve(),
                args.task,
                args.manifest.resolve(),
                args.lock.resolve() if args.lock else None,
                component_roots,
            )
    except ValidationError as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

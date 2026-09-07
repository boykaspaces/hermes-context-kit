#!/usr/bin/env python3
"""Offline validator for multi-repository Task context."""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


TASK_ID_RE = re.compile(r"TASK-\d{3,}")
CANONICAL_TASK_RE = re.compile(r"[a-z0-9][a-z0-9-]*:TASK-\d{3,}")
SHA_RE = re.compile(r"[0-9a-f]{40}")
PROJECT_ID_VALUE_RE = re.compile(r"[a-z0-9][a-z0-9-]*")
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
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    re.compile(
        r"(?i)\b(?:password|passwd|api[_-]?key|access[_-]?token|secret)\b\s*[:=]\s*['\"]?[^\s'\",}]{6,}"
    ),
    re.compile(
        r"(?i)\b[A-Za-z_][A-Za-z0-9_]*(?:credential|password|passwd|secret|token|api[_-]?key|access[_-]?key)[A-Za-z0-9_]*\s*[:=]\s*['\"]?[^\s'\",}]{6,}"
    ),
)
MAX_STRING_LENGTH = 4096


class ValidationError(Exception):
    pass


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValidationError(f"cannot read {path}: {exc}") from exc


def load_json(path: Path) -> Any:
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValidationError(f"invalid JSON {path}: duplicate JSON key {key!r}")
            result[key] = value
        return result

    try:
        return json.loads(read_text(path), object_pairs_hook=unique_object)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON {path}: {exc}") from exc


def lexical_absolute(path: Path) -> Path:
    """Collapse dot segments without following symlinks."""
    return Path(os.path.abspath(path))


def reject_symlink_path(path: Path, label: str) -> None:
    """Reject a supplied trust-boundary path that is itself a symlink.

    Parent directories are outside the repository trust boundary. Inspecting
    them rejects legitimate platform aliases such as macOS /var -> /private/var
    without improving protection for files reached inside the repository.
    """
    if path.is_symlink():
        raise ValidationError(f"{label} must not use symlinks")


def require_repository_file(root: Path, path: Path, label: str) -> Path:
    """Require a regular in-repository file reached without a symlink."""
    canonical_root = lexical_absolute(root)
    candidate = lexical_absolute(path if path.is_absolute() else canonical_root / path)
    try:
        relative = candidate.relative_to(canonical_root)
    except ValueError as exc:
        raise ValidationError(f"{label} must be stored inside the repository") from exc
    reject_symlink_path(canonical_root, label)
    cursor = canonical_root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValidationError(f"{label} must not use symlinks")
    if not cursor.is_file():
        raise ValidationError(f"{label} must be a regular file")
    return cursor


def require_repository_directory(path: Path, label: str) -> Path:
    candidate = lexical_absolute(path)
    reject_symlink_path(candidate, label)
    if not candidate.is_dir():
        raise ValidationError(f"{label} must be a directory")
    return candidate


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


def require_string(
    value: Any,
    label: str,
    pattern: re.Pattern[str] | None = None,
    max_length: int = MAX_STRING_LENGTH,
) -> str:
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{label} must be a non-empty string")
    if len(value) > max_length:
        raise ValidationError(f"{label} exceeds the maximum length of {max_length}")
    if any(ord(character) < 32 and character not in "\t\n\r" for character in value):
        raise ValidationError(f"{label} contains control characters")
    if pattern is not None and not pattern.fullmatch(value):
        raise ValidationError(f"{label} has invalid format: {value!r}")
    for secret_pattern in SECRET_PATTERNS:
        if secret_pattern.search(value):
            raise ValidationError(f"{label} contains secret-like material")
    return value


def require_http_url(value: Any, label: str) -> str:
    url = require_string(value, label)
    if any(character.isspace() for character in url) or "\\" in url:
        raise ValidationError(f"{label} must be a structurally valid HTTP(S) URL")
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        parsed.port
    except ValueError as exc:
        raise ValidationError(f"{label} has an invalid URL authority") from exc
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or hostname is None
        or parsed.username is not None
        or parsed.password is not None
        or not hostname.isascii()
        or "%" in hostname
    ):
        raise ValidationError(f"{label} must be a structurally valid HTTP(S) URL without userinfo")
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        labels = hostname.rstrip(".").split(".")
        if not labels or any(
            not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", part)
            for part in labels
        ):
            raise ValidationError(f"{label} has an invalid URL hostname")
    return url


def require_pointer(value: Any, label: str, root: Path | None = None) -> str:
    pointer = require_string(value, label)
    if any(character.isspace() for character in pointer) or "\\" in pointer:
        raise ValidationError(f"{label} contains whitespace or a backslash")
    try:
        parsed = urlsplit(pointer)
    except ValueError as exc:
        raise ValidationError(f"{label} has an invalid URL authority") from exc
    if parsed.scheme:
        require_http_url(pointer, label)
        if "%" in parsed.path or (
            parsed.fragment and not re.fullmatch(r"[A-Za-z0-9._~-]+", parsed.fragment)
        ):
            raise ValidationError(
                f"{label} must be an HTTP(S) URL or repository-relative file pointer"
            )
        return pointer
    if parsed.netloc or parsed.query:
        raise ValidationError(f"{label} has an invalid repository-relative pointer")
    if parsed.fragment and not re.fullmatch(r"[A-Za-z0-9._~-]+", parsed.fragment):
        raise ValidationError(f"{label} has an invalid repository-relative fragment")
    target = parsed.path
    if not target or ":" in target or "%" in target:
        raise ValidationError(f"{label} has an invalid repository-relative pointer")
    path = Path(target)
    if (
        path.is_absolute()
        or any(part in {"", ".", ".."} for part in target.split("/"))
        or any(part in {".", ".."} for part in path.parts)
    ):
        raise ValidationError(f"{label} must be an HTTP(S) URL or repository-relative file pointer")
    if root is not None:
        require_repository_file(root, root / path, label)
    return pointer


def resolve_task_manifest_pointer(value: Any, task_path: Path, root: Path) -> str:
    """Return one Task manifest pointer as a repository-relative path.

    Task metadata may use a plain/code-spanned repository-relative path or a
    Markdown link whose target is relative to the Task file.
    """
    raw = require_string(value, "System Manifest").strip()
    if raw.startswith("`") and raw.endswith("`") and len(raw) > 2:
        raw = raw[1:-1].strip()
    markdown = re.fullmatch(r"\[[^\]]+\]\(([^)]+)\)", raw)
    if markdown:
        target = markdown.group(1).strip()
        base = task_path.parent
    else:
        target = raw
        base = root
    if not target or any(character.isspace() for character in target):
        raise ValidationError(f"{task_path}: invalid System Manifest pointer")
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        raise ValidationError(f"{task_path}: System Manifest must be repository-relative")
    candidate = lexical_absolute(base / target)
    canonical_root = lexical_absolute(root)
    try:
        return candidate.relative_to(canonical_root).as_posix()
    except ValueError as exc:
        raise ValidationError(
            f"{task_path}: System Manifest must be stored inside the repository"
        ) from exc


def reject_secrets(data: Any, label: str) -> None:
    rendered = json.dumps(data, sort_keys=True)
    for pattern in SECRET_PATTERNS:
        if pattern.search(rendered):
            raise ValidationError(f"{label} contains secret-like material")


def require_component_schema(item: Any, label: str) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise ValidationError(f"{label} must be an object")
    base = {"repository", "task", "repository_url", "branch", "revision", "delivery_state"}
    if item.get("task") is not None:
        expected = base
    elif item.get("task_absence_reason") == "no-component-change":
        expected = base | {"task_absence_reason", "source_system_task"}
    else:
        expected = base | {"task_absence_reason"}
    if set(item) != expected:
        raise ValidationError(f"{label} fields must exactly match the canonical schema")
    return item


def require_integration_schema(value: Any, label: str) -> dict[str, Any]:
    expected = {"state", "validation_evidence", "deployment_evidence", "rollback"}
    if not isinstance(value, dict) or set(value) != expected:
        raise ValidationError(f"{label} fields must exactly match the canonical schema")
    return value


def validate_handoff(path: Path) -> None:
    data = load_json(path)
    expected_keys = {
        "schema_version",
        "component",
        "parent_system_task",
        "source",
        "validation",
        "documentation_updated",
        "integration_requirements",
        "rollback_revision",
        "contains_secrets",
    }
    if not isinstance(data, dict) or set(data) != expected_keys:
        raise ValidationError("handoff fields must exactly match the canonical schema")
    if data.get("schema_version") != 1:
        raise ValidationError("handoff schema_version must be 1")
    component = data.get("component")
    source = data.get("source")
    if not isinstance(component, dict) or not isinstance(source, dict):
        raise ValidationError("handoff component and source must be objects")
    if set(component) != {"repository", "task"}:
        raise ValidationError("handoff component fields must exactly match the canonical schema")
    if set(source) != {"repository_url", "branch", "revision"}:
        raise ValidationError("handoff source fields must exactly match the canonical schema")
    component_name = require_string(
        component.get("repository"), "component.repository", PROJECT_ID_VALUE_RE
    )
    component_task = require_string(component.get("task"), "component.task", CANONICAL_TASK_RE)
    if component_task.split(":", 1)[0] != component_name:
        raise ValidationError("component.task project differs from component.repository")
    require_string(data.get("parent_system_task"), "parent_system_task", CANONICAL_TASK_RE)
    require_http_url(source.get("repository_url"), "source.repository_url")
    require_string(source.get("branch"), "source.branch")
    require_string(source.get("revision"), "source.revision", SHA_RE)
    validation = data.get("validation")
    if not isinstance(validation, list) or not validation:
        raise ValidationError("handoff validation must contain at least one result")
    for result in validation:
        if (
            not isinstance(result, dict)
            or set(result) != {"command", "result"}
            or result.get("result") != "passed"
        ):
            raise ValidationError("handoff validation results must be passed objects")
        require_string(result.get("command"), "validation.command")
    if data.get("documentation_updated") is not True:
        raise ValidationError("documentation_updated must be true")
    requirements = data.get("integration_requirements")
    if not isinstance(requirements, list):
        raise ValidationError("integration_requirements must be a list")
    for index, requirement in enumerate(requirements):
        require_string(requirement, f"integration_requirements[{index}]")
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
        if not isinstance(data, dict):
            raise ValidationError("JSON lock must be an object")
        if not isinstance(components, list):
            raise ValidationError("JSON lock has no components list")
        result = {}
        for item in components:
            if not isinstance(item, dict):
                raise ValidationError("JSON lock component must be an object")
            if not {"name", "source_revision"} <= set(item):
                raise ValidationError("JSON lock component is missing a core field")
            name = require_string(
                item.get("name"), "lock component name", PROJECT_ID_VALUE_RE
            )
            revision = require_string(item.get("source_revision"), f"lock revision for {name}", SHA_RE)
            if name in result:
                raise ValidationError(f"duplicate lock component {name}")
            result[name] = revision
        return result

    result: dict[str, str] = {}
    names: set[str] = set()
    current: str | None = None
    components_seen = False
    in_components = False
    for line_number, line in enumerate(read_text(path).splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line == "components:":
            if components_seen or current is not None or names:
                raise ValidationError(f"{path}:{line_number}: duplicate or misplaced components key")
            components_seen = True
            in_components = True
            continue
        if not line.startswith(" ") and in_components:
            if current is not None:
                raise ValidationError(f"lock component {current} has no source_revision")
            in_components = False
            current = None
        if not in_components:
            continue
        name_match = re.fullmatch(r"  - name:\s*([a-z0-9][a-z0-9-]*)\s*", line)
        if name_match:
            if not components_seen:
                raise ValidationError(f"{path}:{line_number}: component appears before components key")
            if current is not None:
                raise ValidationError(f"lock component {current} has no source_revision")
            current = name_match.group(1)
            if current in names:
                raise ValidationError(f"duplicate lock component {current}")
            names.add(current)
            continue
        revision_match = re.fullmatch(r"    source_revision:\s*([0-9a-f]{40})\s*", line)
        if revision_match:
            if current is None:
                raise ValidationError(f"{path}:{line_number}: source_revision has no component")
            result[current] = revision_match.group(1)
            current = None
            continue
        if line.startswith("    ") or line.startswith("      "):
            continue
        raise ValidationError(f"{path}:{line_number}: unsupported component lock syntax")
    if current is not None:
        raise ValidationError(f"lock component {current} has no source_revision")
    if not components_seen or not result:
        raise ValidationError(f"no supported component revisions found in {path}")
    return result


def require_evidence_v2(value: Any, label: str, root: Path) -> dict[str, Any]:
    if not isinstance(value, dict) or not {"ref"} <= set(value) or not set(value) <= {
        "ref",
        "summary",
    }:
        raise ValidationError(f"{label} must contain ref and optional summary")
    require_pointer(value.get("ref"), f"{label}.ref", root)
    if value.get("summary") is not None:
        require_string(value.get("summary"), f"{label}.summary")
    return value


def validate_system_task_v2(
    root: Path,
    task_id: str,
    task_path: Path,
    manifest_path: Path,
    lock_path: Path | None,
    component_roots: dict[str, Path],
    data: dict[str, Any],
    pid: str,
) -> None:
    expected_fields = {
        "schema_version",
        "system_task",
        "system_id",
        "integration_project",
        "components",
        "integration",
    }
    if set(data) != expected_fields:
        raise ValidationError("v2 system manifest fields must exactly match the canonical schema")
    expected = f"{pid}:{task_id}"
    if data.get("system_task") != expected:
        raise ValidationError(f"system_task must be {expected}")
    if data.get("integration_project") != pid:
        raise ValidationError(f"integration_project must be {pid}")
    require_string(data.get("system_id"), "system_id")

    components = data.get("components")
    if not isinstance(components, list) or not components:
        raise ValidationError("v2 system manifest must declare components")

    locks: dict[str, str] = {}
    if lock_path is not None:
        expected_lock = lexical_absolute(root / "components" / "lock.json")
        if lexical_absolute(lock_path) != expected_lock:
            raise ValidationError("v2 component lock must be stored at components/lock.json")
        lock_path = require_repository_file(root, expected_lock, "v2 component lock")
        locks = load_lock(lock_path)

    seen: set[str] = set()
    acceptance_states: list[str] = []
    deployments: list[dict[str, Any]] = []
    for index, item in enumerate(components):
        label = f"components[{index}]"
        if not isinstance(item, dict):
            raise ValidationError(f"{label} must be an object")
        base_fields = {
            "repository",
            "task",
            "repository_url",
            "branch",
            "revision",
            "source_state",
            "acceptance_state",
            "deployment",
        }
        optional_fields = {"extensions"}
        if item.get("task") is None:
            optional_fields.add("task_absence_reason")
            if item.get("task_absence_reason") == "no-component-change":
                optional_fields.add("source_system_task")
        if not base_fields <= set(item) or not set(item) <= base_fields | optional_fields:
            raise ValidationError(f"{label} fields do not match the v2 component schema")
        if item.get("extensions") is not None and not isinstance(item.get("extensions"), dict):
            raise ValidationError(f"{label}.extensions must be an object")

        repository = require_string(
            item.get("repository"), f"{label}.repository", PROJECT_ID_VALUE_RE
        )
        if repository in seen:
            raise ValidationError(f"duplicate system component {repository}")
        seen.add(repository)
        require_http_url(item.get("repository_url"), f"{repository}.repository_url")
        require_string(item.get("branch"), f"{repository}.branch")

        task = item.get("task")
        if task is None:
            reason = item.get("task_absence_reason")
            if reason not in {"work-predates-protocol", "no-component-change"}:
                raise ValidationError(f"{repository}: missing Task without an allowed reason")
            if reason == "no-component-change":
                source = require_string(
                    item.get("source_system_task"),
                    f"{repository}.source_system_task",
                    CANONICAL_TASK_RE,
                )
                if source.split(":", 1)[0] != pid or source == expected:
                    raise ValidationError(
                        f"{repository}.source_system_task must identify another Task in {pid}"
                    )
        else:
            canonical_task = require_string(task, f"{repository}.task", CANONICAL_TASK_RE)
            task_project, component_task_id = canonical_task.split(":", 1)
            if task_project != repository:
                raise ValidationError(f"{repository}: Task project differs from component identity")
            if repository not in component_roots:
                raise ValidationError(
                    f"{repository}: not_checked: component root is required to verify Task relationship"
                )
            component_root = require_repository_directory(
                component_roots[repository], f"{repository}: component root"
            )
            component_project = require_repository_file(
                component_root,
                component_root / "PROJECT.md",
                f"{repository}: component PROJECT.md",
            )
            if project_id(component_project.parent) != repository:
                raise ValidationError(f"{repository}: component root Project ID differs")
            component_task = require_repository_file(
                component_root,
                component_root / "tasks" / f"{component_task_id}.md",
                f"{canonical_task}: Component Task",
            )
            component_fields = task_fields(component_task)
            if component_fields.get("Type") != "Component":
                raise ValidationError(f"{canonical_task}: child Task must declare Type: Component")
            if component_fields.get("Parent System Task") != expected:
                raise ValidationError(f"{canonical_task}: parent differs from {expected}")

        source_state = item.get("source_state")
        acceptance_state = item.get("acceptance_state")
        if source_state not in {"pending", "handoff-ready", "merged"}:
            raise ValidationError(f"{repository}: invalid source_state {source_state!r}")
        if acceptance_state not in {"pending", "locked", "verified"}:
            raise ValidationError(
                f"{repository}: invalid acceptance_state {acceptance_state!r}"
            )
        revision = item.get("revision")
        if source_state != "pending" or acceptance_state != "pending":
            require_string(revision, f"{repository}.revision", SHA_RE)
        if acceptance_state != "pending" and source_state == "pending":
            raise ValidationError(
                f"{repository}: accepted component cannot have pending source_state"
            )
        if acceptance_state in {"locked", "verified"}:
            if lock_path is None:
                raise ValidationError(
                    f"{repository}: locked or verified acceptance requires a component lock"
                )
            if locks.get(repository) != revision:
                raise ValidationError(
                    f"{repository}: manifest revision differs from component lock"
                )
        acceptance_states.append(acceptance_state)

        deployment = item.get("deployment")
        if not isinstance(deployment, dict) or set(deployment) != {
            "applicability",
            "state",
            "evidence",
        }:
            raise ValidationError(f"{repository}.deployment has invalid fields")
        applicability = deployment.get("applicability")
        deployment_state = deployment.get("state")
        evidence = deployment.get("evidence")
        if not isinstance(evidence, list):
            raise ValidationError(f"{repository}.deployment.evidence must be a list")
        for evidence_index, evidence_item in enumerate(evidence):
            require_evidence_v2(
                evidence_item,
                f"{repository}.deployment.evidence[{evidence_index}]",
                root,
            )
        if applicability == "not-applicable":
            if deployment_state != "not-applicable" or evidence:
                raise ValidationError(
                    f"{repository}: not-applicable deployment must have no deployment evidence"
                )
        elif applicability == "required":
            if deployment_state not in {"pending", "deployed"}:
                raise ValidationError(f"{repository}: invalid required deployment state")
            if deployment_state == "deployed" and not evidence:
                raise ValidationError(
                    f"{repository}: deployed component requires deployment evidence"
                )
        else:
            raise ValidationError(f"{repository}: invalid deployment applicability")
        deployments.append(deployment)

    if lock_path is not None and set(locks) != seen:
        raise ValidationError(
            "v2 component lock must exactly match manifest components; "
            f"missing={sorted(seen - set(locks))}, extra={sorted(set(locks) - seen)}"
        )

    integration = data.get("integration")
    required_integration = {
        "verification_state",
        "validation_evidence",
        "deployment_state",
        "deployment_evidence",
        "rollback",
    }
    if (
        not isinstance(integration, dict)
        or not required_integration <= set(integration)
        or not set(integration) <= required_integration | {"extensions"}
    ):
        raise ValidationError("integration fields do not match the v2 schema")
    if integration.get("extensions") is not None and not isinstance(
        integration.get("extensions"), dict
    ):
        raise ValidationError("integration.extensions must be an object")
    verification_state = integration.get("verification_state")
    deployment_state = integration.get("deployment_state")
    validation_evidence = integration.get("validation_evidence")
    deployment_evidence = integration.get("deployment_evidence")
    rollback = integration.get("rollback")
    if verification_state not in {"pending", "verified"}:
        raise ValidationError("invalid integration verification_state")
    if deployment_state not in {"pending", "deployed", "not-applicable"}:
        raise ValidationError("invalid integration deployment_state")
    if not isinstance(validation_evidence, list) or not isinstance(
        deployment_evidence, list
    ):
        raise ValidationError("integration evidence fields must be lists")
    for index, evidence_item in enumerate(validation_evidence):
        require_evidence_v2(evidence_item, f"integration.validation_evidence[{index}]", root)
    for index, evidence_item in enumerate(deployment_evidence):
        require_evidence_v2(evidence_item, f"integration.deployment_evidence[{index}]", root)
    if rollback is not None:
        require_evidence_v2(rollback, "integration.rollback", root)
    if verification_state == "verified" and (
        not validation_evidence
        or any(state not in {"locked", "verified"} for state in acceptance_states)
    ):
        raise ValidationError(
            "verified integration requires evidence and every component locked or verified"
        )

    required_deployments = [
        deployment
        for deployment in deployments
        if deployment["applicability"] == "required"
    ]
    if deployment_state == "not-applicable" and required_deployments:
        raise ValidationError(
            "not-applicable integration deployment cannot contain required components"
        )
    if deployment_state == "deployed" and (
        not required_deployments
        or any(deployment["state"] != "deployed" for deployment in required_deployments)
        or not deployment_evidence
        or rollback is None
    ):
        raise ValidationError(
            "deployed integration requires all required components deployed, evidence, and rollback"
        )
    reject_secrets(data, str(manifest_path))
    print(f"system-task-v2-ok: {expected}")


def validate_system_task(
    root: Path,
    task_id: str,
    manifest_path: Path,
    lock_path: Path | None,
    component_roots: dict[str, Path] | None = None,
) -> None:
    root = require_repository_directory(root, "integration root")
    pid = project_id(root)
    task_path = root / "tasks" / f"{task_id}.md"
    fields = task_fields(task_path)
    if fields.get("Type") not in {"System", "Deployment"}:
        raise ValidationError(f"{task_path}: System Task must declare Type: System or Deployment")

    relative_manifest = f"tasks/system/{task_id}.json"
    expected_manifest_path = lexical_absolute(root / relative_manifest)
    provided_manifest_path = lexical_absolute(manifest_path)
    if provided_manifest_path != expected_manifest_path:
        raise ValidationError(f"manifest must be stored at {relative_manifest}")
    manifest_path = require_repository_file(
        root, expected_manifest_path, f"manifest storage at {relative_manifest}"
    )
    task_path = require_repository_file(root, task_path, "System Task")
    declared_manifest = resolve_task_manifest_pointer(
        fields.get("System Manifest"), task_path, root
    )
    if declared_manifest != relative_manifest:
        raise ValidationError(f"{task_path}: System Manifest must point to {relative_manifest}")

    data = load_json(manifest_path)
    if isinstance(data, dict) and data.get("schema_version") == 2:
        validate_system_task_v2(
            root,
            task_id,
            task_path,
            manifest_path,
            lock_path,
            component_roots or {},
            data,
            pid,
        )
        return
    if not isinstance(data, dict) or set(data) != {
        "schema_version",
        "system_task",
        "system_id",
        "integration_project",
        "components",
        "integration",
    }:
        raise ValidationError("system manifest fields must exactly match the canonical schema")
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
    locks: dict[str, str] = {}
    if lock_path is not None:
        expected_lock_path = lexical_absolute(root / "components" / "lock.yaml")
        if lexical_absolute(lock_path) != expected_lock_path:
            raise ValidationError("component lock must be stored at components/lock.yaml")
        lock_path = require_repository_file(root, expected_lock_path, "component lock")
        locks = load_lock(lock_path)
    seen: set[str] = set()
    component_states: list[str] = []
    for item in components:
        item = require_component_schema(item, "system component")
        repository = require_string(
            item.get("repository"), "component.repository", PROJECT_ID_VALUE_RE
        )
        if repository in seen:
            raise ValidationError(f"duplicate system component {repository}")
        seen.add(repository)
        require_http_url(item.get("repository_url"), f"{repository}.repository_url")
        require_string(item.get("branch"), f"{repository}.branch")
        task = item.get("task")
        if task is None:
            absence_reason = item.get("task_absence_reason")
            if absence_reason not in {"work-predates-protocol", "no-component-change"}:
                raise ValidationError(f"{repository}: missing Task without an allowed reason")
            if absence_reason == "no-component-change":
                source_system_task = require_string(
                    item.get("source_system_task"),
                    f"{repository}.source_system_task",
                    CANONICAL_TASK_RE,
                )
                source_project, source_task_id = source_system_task.split(":", 1)
                if source_project != pid:
                    raise ValidationError(
                        f"{repository}.source_system_task must belong to integration project {pid}"
                    )
                if source_task_id == task_id:
                    raise ValidationError(
                        f"{repository}.source_system_task must reference a different prior Task"
                    )
                source_task_paths = [
                    path for path in task_files(root) if path.stem == source_task_id
                ]
                if len(source_task_paths) != 1:
                    raise ValidationError(
                        f"{repository}.source_system_task must resolve to exactly one Task"
                    )
                source_task_path = require_repository_file(
                    root,
                    source_task_paths[0],
                    f"{repository}.source_system_task Task",
                )
                source_fields = task_fields(source_task_path)
                if source_fields.get("Type") not in {"System", "Deployment"}:
                    raise ValidationError(
                        f"{repository}.source_system_task must reference a System or Deployment Task"
                    )
                if source_fields.get("Status") != "Completed":
                    raise ValidationError(
                        f"{repository}.source_system_task must reference a completed prior Task"
                    )
                expected_source_manifest = f"tasks/system/{source_task_id}.json"
                source_manifest_pointer = resolve_task_manifest_pointer(
                    source_fields.get("System Manifest"), source_task_path, root
                )
                if source_manifest_pointer != expected_source_manifest:
                    raise ValidationError(
                        f"{repository}.source_system_task must declare {expected_source_manifest}"
                    )
                source_manifest_path = root / "tasks" / "system" / f"{source_task_id}.json"
                source_manifest_path = require_repository_file(
                    root,
                    source_manifest_path,
                    f"{repository}.source_system_task manifest",
                )
                source_manifest = load_json(source_manifest_path)
                if not isinstance(source_manifest, dict) or set(source_manifest) != {
                    "schema_version",
                    "system_task",
                    "system_id",
                    "integration_project",
                    "components",
                    "integration",
                }:
                    raise ValidationError(
                        f"{repository}.source_system_task manifest fields must exactly match the canonical schema"
                    )
                if source_manifest.get("schema_version") != 1:
                    raise ValidationError(
                        f"{repository}.source_system_task manifest schema_version must be 1"
                    )
                if source_manifest.get("system_task") != source_system_task:
                    raise ValidationError(
                        f"{repository}.source_system_task manifest identity differs"
                    )
                if source_manifest.get("integration_project") != pid:
                    raise ValidationError(
                        f"{repository}.source_system_task manifest project differs"
                    )
                if source_manifest.get("system_id") != data.get("system_id"):
                    raise ValidationError(
                        f"{repository}.source_system_task belongs to a different system"
                    )
                current_revision = require_string(
                    item.get("revision"), f"{repository}.revision", SHA_RE
                )
                source_components = source_manifest.get("components")
                if not isinstance(source_components, list) or not source_components:
                    raise ValidationError(
                        f"{repository}.source_system_task manifest must declare components"
                    )
                source_seen: set[str] = set()
                for source_component in source_components:
                    source_component = require_component_schema(
                        source_component, f"{repository}.source_system_task component"
                    )
                    source_repository = require_string(
                        source_component.get("repository"),
                        f"{repository}.source_system_task component.repository",
                        PROJECT_ID_VALUE_RE,
                    )
                    if source_repository in source_seen:
                        raise ValidationError(
                            f"{repository}.source_system_task has duplicate component {source_repository}"
                        )
                    source_seen.add(source_repository)
                    require_http_url(
                        source_component.get("repository_url"),
                        f"{source_repository}.source repository_url",
                    )
                    require_string(
                        source_component.get("branch"),
                        f"{source_repository}.source branch",
                    )
                    source_component_task = source_component.get("task")
                    if source_component_task is None:
                        source_absence_reason = source_component.get("task_absence_reason")
                        if source_absence_reason not in {
                            "work-predates-protocol",
                            "no-component-change",
                        }:
                            raise ValidationError(
                                f"{source_repository}: missing Task without an allowed reason"
                            )
                        if source_absence_reason == "no-component-change":
                            require_string(
                                source_component.get("source_system_task"),
                                f"{source_repository}.source source_system_task",
                                CANONICAL_TASK_RE,
                            )
                    else:
                        canonical_source_task = require_string(
                            source_component_task,
                            f"{source_repository}.source task",
                            CANONICAL_TASK_RE,
                        )
                        if canonical_source_task.split(":", 1)[0] != source_repository:
                            raise ValidationError(
                                f"{source_repository}: source Task project differs from component identity"
                            )
                    source_state = source_component.get("delivery_state")
                    if source_state not in DELIVERY_STATES:
                        raise ValidationError(
                            f"{source_repository}.source delivery_state is invalid"
                        )
                    if source_state != "pending":
                        require_string(
                            source_component.get("revision"),
                            f"{source_repository}.source revision",
                            SHA_RE,
                        )
                source_integration = require_integration_schema(
                    source_manifest.get("integration"),
                    f"{repository}.source_system_task integration",
                )
                if source_integration.get("state") not in {"pending", "verified", "deployed"}:
                    raise ValidationError(
                        f"{repository}.source_system_task integration state is invalid"
                    )
                if not isinstance(source_integration.get("validation_evidence"), list) or not isinstance(
                    source_integration.get("deployment_evidence"), list
                ):
                    raise ValidationError(
                        f"{repository}.source_system_task evidence fields must be lists"
                    )
                source_component_states = [
                    component.get("delivery_state") for component in source_components
                ]
                source_integration_state = source_integration.get("state")
                source_validation = source_integration.get("validation_evidence")
                source_deployment = source_integration.get("deployment_evidence")
                for index, pointer in enumerate(source_validation):
                    require_pointer(
                        pointer, f"{repository}.source validation_evidence[{index}]", root
                    )
                for index, pointer in enumerate(source_deployment):
                    require_pointer(
                        pointer, f"{repository}.source deployment_evidence[{index}]", root
                    )
                if source_integration.get("rollback") is not None:
                    require_pointer(
                        source_integration.get("rollback"), f"{repository}.source rollback", root
                    )
                if source_integration_state in {"verified", "deployed"} and not source_validation:
                    raise ValidationError(
                        f"{repository}.source verified integration requires validation evidence"
                    )
                if source_integration_state == "verified" and any(
                    source_state not in LOCKED_STATES for source_state in source_component_states
                ):
                    raise ValidationError(
                        f"{repository}.source verified integration has an unlocked component"
                    )
                if source_integration_state == "deployed":
                    if not source_deployment or not source_integration.get("rollback"):
                        raise ValidationError(
                            f"{repository}.source deployed integration requires deployment evidence and rollback"
                        )
                    require_pointer(
                        source_integration.get("rollback"),
                        f"{repository}.source rollback",
                        root,
                    )
                    if any(source_state != "deployed" for source_state in source_component_states):
                        raise ValidationError(
                            f"{repository}.source deployed integration has a non-deployed component"
                        )
                source_matches = [
                    component
                    for component in source_components
                    if isinstance(component, dict)
                    and component.get("repository") == repository
                    and component.get("revision") == current_revision
                    and component.get("delivery_state") in LOCKED_STATES
                ]
                if len(source_matches) != 1:
                    raise ValidationError(
                        f"{repository}.source_system_task does not own the accepted revision"
                    )
        else:
            canonical_task = require_string(task, f"{repository}.task", CANONICAL_TASK_RE)
            task_project, component_task_id = canonical_task.split(":", 1)
            if task_project != repository:
                raise ValidationError(f"{repository}: Task project differs from component identity")
            if repository not in resolved_component_roots:
                raise ValidationError(f"{repository}: component root is required to verify Task relationship")
            component_root = require_repository_directory(
                resolved_component_roots[repository], f"{repository}: component root"
            )
            component_project_file = require_repository_file(
                component_root, component_root / "PROJECT.md", f"{repository}: component PROJECT.md"
            )
            if project_id(component_project_file.parent) != repository:
                raise ValidationError(f"{repository}: component root Project ID differs")
            component_task_path = require_repository_file(
                component_root,
                component_root / "tasks" / f"{component_task_id}.md",
                f"{canonical_task}: Component Task",
            )
            component_fields = task_fields(component_task_path)
            if component_fields.get("Type") != "Component":
                raise ValidationError(f"{canonical_task}: child Task must declare Type: Component")
            if component_fields.get("Parent System Task") != expected:
                raise ValidationError(f"{canonical_task}: parent differs from {expected}")
        state = item.get("delivery_state")
        if state not in DELIVERY_STATES:
            raise ValidationError(f"{repository}: invalid delivery_state {state!r}")
        component_states.append(state)
        revision = item.get("revision")
        if state != "pending":
            require_string(revision, f"{repository}.revision", SHA_RE)
        if lock_path is not None:
            require_string(revision, f"{repository}.revision", SHA_RE)
            if repository not in locks:
                raise ValidationError(f"{repository}: absent from component lock")
            if locks[repository] != revision:
                raise ValidationError(f"{repository}: manifest revision differs from component lock")

    if lock_path is not None and set(locks) != seen:
        missing = sorted(seen - set(locks))
        extra = sorted(set(locks) - seen)
        raise ValidationError(f"component lock must exactly match manifest components; missing={missing}, extra={extra}")

    if any(component_state in LOCKED_STATES for component_state in component_states) and lock_path is None:
        raise ValidationError("locked or later component state requires a component lock")

    integration = require_integration_schema(data.get("integration"), "integration")
    state = integration.get("state")
    if state not in {"pending", "verified", "deployed"}:
        raise ValidationError(f"invalid integration state {state!r}")
    validation = integration.get("validation_evidence")
    deployment = integration.get("deployment_evidence")
    if not isinstance(validation, list) or not isinstance(deployment, list):
        raise ValidationError("integration evidence fields must be lists")
    for index, pointer in enumerate(validation):
        require_pointer(pointer, f"integration.validation_evidence[{index}]", root)
    for index, pointer in enumerate(deployment):
        require_pointer(pointer, f"integration.deployment_evidence[{index}]", root)
    if state in {"verified", "deployed"} and not validation:
        raise ValidationError("verified integration requires validation evidence")
    if state == "verified" and any(
        component_state not in LOCKED_STATES for component_state in component_states
    ):
        raise ValidationError("verified integration requires every component to be locked or later")
    if state == "deployed" and (not deployment or not integration.get("rollback")):
        raise ValidationError("deployed integration requires deployment evidence and rollback")
    if integration.get("rollback") is not None:
        require_pointer(integration.get("rollback"), "integration.rollback", root)
    if state == "deployed" and any(
        component_state != "deployed" for component_state in component_states
    ):
        raise ValidationError("deployed integration requires every component to be deployed")
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
                component_roots[component_name] = Path(component_path)
            validate_system_task(
                args.root,
                args.task,
                args.manifest,
                args.lock if args.lock else None,
                component_roots,
            )
    except ValidationError as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

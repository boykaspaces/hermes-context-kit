#!/usr/bin/env python3
"""Plan, install, and verify the opinionated Context Kit Hermes runtime."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


ADAPTER_ROOT = Path(__file__).resolve().parents[1]
KIT_ROOT = ADAPTER_ROOT.parents[2]
CONTRACT_PATH = ADAPTER_ROOT / "runtime-contract.json"
CONFIG_FIELDS = {
    "schema_version",
    "workspace_id",
    "source_revision",
    "capabilities",
    "soul_preference",
}
REVISION_RE = re.compile(r"[0-9a-f]{40}")
WORKSPACE_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
IGNORED_FILES = {".DS_Store"}
RUNTIME_DIRECTORIES = {"assets", "references", "scripts", "templates"}
RUNTIME_METADATA_FIELDS = (
    "version",
    "author",
    "platforms",
    "tags",
    "related_skills",
)


class SetupError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SetupError(f"{path}: cannot load JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SetupError(f"{path}: expected a JSON object")
    return data


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    contract = load_json(path)
    required = {"schema_version", "name", "paths", "capabilities", "installation", "soul"}
    if contract.get("schema_version") != 2 or contract.get("name") != "hermes":
        raise SetupError(f"{path}: unsupported Hermes runtime contract")
    if not required <= set(contract):
        raise SetupError(f"{path}: missing runtime contract fields")
    expected_paths = {
        "hermes_home": "/home/hermes/.hermes",
        "source_checkout": "/workspace/.context-kit/sources/hermes-context-kit",
        "skill_root": "/home/hermes/.hermes/skills",
        "soul": "/home/hermes/.hermes/SOUL.md",
        "workspace_root": "/workspace",
        "workspace_identity": "/workspace/.hermes/WORKSPACE_ID",
        "workspace_registry": "/workspace/.hermes/WORKSPACES.md",
    }
    if contract["paths"] != expected_paths:
        raise SetupError(f"{path}: Hermes solution paths differ from the fixed contract")
    expected_installation = {
        "agent_mechanism": {
            "name": "skill_manage",
            "reason": (
                "The current tool cannot import an immutable checkout tree and "
                "accepts only model-supplied file bodies in allowlisted runtime "
                "directories."
            ),
            "support": "unsupported-for-release-install",
        },
        "manifest": "/home/hermes/.hermes/context-kit-install.json",
        "operator_mechanism": {
            "name": "runtime_setup.py",
            "support": "required",
            "transactional": True,
        },
        "runtime_directories": ["references", "templates", "scripts", "assets"],
        "transaction_root": "/home/hermes/.hermes/context-kit-transactions",
    }
    if contract["installation"] != expected_installation:
        raise SetupError(f"{path}: Hermes installation contract differs")
    soul = contract["soul"]
    if soul.get("required") is not False or soul.get("default_action") != "offer":
        raise SetupError(f"{path}: SOUL must be optional and offered by default")
    capabilities = contract["capabilities"]
    if not isinstance(capabilities, dict) or "project-context" not in capabilities:
        raise SetupError(f"{path}: project-context capability is required")
    if capabilities["project-context"].get("required") is not True:
        raise SetupError(f"{path}: project-context capability must be required")
    return contract


def load_config(path: Path, contract: dict[str, Any]) -> dict[str, Any]:
    return load_config_from_data(load_json(path), contract, label=str(path))


def load_config_from_data(
    config: dict[str, Any], contract: dict[str, Any], *, label: str
) -> dict[str, Any]:
    unknown = set(config) - CONFIG_FIELDS
    required = {"schema_version", "workspace_id", "source_revision", "capabilities"}
    if unknown or not required <= set(config):
        detail = f" unknown={sorted(unknown)}" if unknown else ""
        raise SetupError(f"{label}: invalid runtime configuration fields{detail}")
    if config["schema_version"] != 1:
        raise SetupError(f"{label}: unsupported configuration schema")
    if not isinstance(config["workspace_id"], str) or not WORKSPACE_ID_RE.fullmatch(
        config["workspace_id"]
    ):
        raise SetupError(f"{label}: invalid workspace_id")
    if not isinstance(config["source_revision"], str) or not REVISION_RE.fullmatch(
        config["source_revision"]
    ):
        raise SetupError(f"{label}: source_revision must be a full lowercase commit SHA")
    capabilities = config["capabilities"]
    if (
        not isinstance(capabilities, list)
        or len(capabilities) != len(set(capabilities))
        or "project-context" not in capabilities
        or any(name not in contract["capabilities"] for name in capabilities)
    ):
        raise SetupError(f"{label}: invalid or duplicate capabilities")
    soul_preference = config.get("soul_preference", "offer")
    if soul_preference not in {"offer", "declined", "requested"}:
        raise SetupError(f"{label}: invalid soul_preference")
    config["soul_preference"] = soul_preference
    return config


def selected_skills(config: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for capability in config["capabilities"]:
        for skill in contract["capabilities"][capability]["skills"]:
            if skill not in result:
                result.append(skill)
    return result


def checkout_revision(root: Path = KIT_ROOT) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    revision = result.stdout.strip()
    return revision if REVISION_RE.fullmatch(revision) else None


def source_status(root: Path = KIT_ROOT) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def require_selected_source(
    config: dict[str, Any], contract: dict[str, Any], root: Path = KIT_ROOT
) -> None:
    expected_root = Path(contract["paths"]["source_checkout"])
    if root.resolve() != expected_root.resolve():
        raise SetupError(
            f"source checkout is {root.resolve()}, but the Hermes contract requires "
            f"{expected_root.resolve()}"
        )
    actual = checkout_revision(root)
    if actual is None:
        raise SetupError("cannot verify an immutable Git commit for the source checkout")
    if actual != config["source_revision"]:
        raise SetupError(
            f"source checkout is {actual}, but configuration selects "
            f"{config['source_revision']}"
        )
    status = source_status(root)
    if status is None:
        raise SetupError("cannot verify that the Context Kit checkout is immutable")
    if status:
        raise SetupError("Context Kit checkout has uncommitted or untracked changes")


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def render_hermes_skill_md(content: str, *, label: str) -> str:
    if not content.startswith("---\n") or "\n---\n" not in content[4:]:
        raise SetupError(f"{label}: malformed Skill frontmatter")
    frontmatter, body = content[4:].split("\n---\n", 1)
    lines = frontmatter.splitlines()
    try:
        metadata_index = lines.index("metadata:")
        context_index = lines.index("  context-kit:", metadata_index + 1)
    except ValueError as exc:
        raise SetupError(f"{label}: missing metadata.context-kit") from exc
    context_values: dict[str, str] = {}
    for line in lines[context_index + 1 :]:
        if not line.startswith("    "):
            break
        key, separator, value = line.strip().partition(":")
        if separator and value.strip():
            context_values[key] = value.strip()
    missing = [key for key in RUNTIME_METADATA_FIELDS if key not in context_values]
    if missing:
        raise SetupError(
            f"{label}: metadata.context-kit missing {', '.join(missing)}"
        )
    top_level: dict[str, str] = {}
    for line in lines:
        if line.startswith(" "):
            continue
        key, separator, value = line.partition(":")
        if separator and value.strip():
            top_level[key] = value.strip()
    additions: list[str] = []
    for key in RUNTIME_METADATA_FIELDS:
        expected = context_values[key]
        if key in top_level and top_level[key] != expected:
            raise SetupError(f"{label}: top-level {key} conflicts with Context Kit metadata")
        if key not in top_level:
            additions.append(f"{key}: {expected}")
    rendered = lines[:metadata_index] + additions + lines[metadata_index:]
    return "---\n" + "\n".join(rendered) + "\n---\n" + body


def is_runtime_path(relative: str) -> bool:
    parts = Path(relative).parts
    return relative == "SKILL.md" or bool(parts and parts[0] in RUNTIME_DIRECTORIES)


def source_skill_inventories(path: Path) -> tuple[dict[str, str], dict[str, str]]:
    if path.is_symlink() or not (path / "SKILL.md").is_file():
        raise SetupError(f"{path}: missing SKILL.md")
    runtime_inventory: dict[str, str] = {}
    source_validation_inventory: dict[str, str] = {}
    for item in sorted(path.rglob("*")):
        if item.is_symlink():
            raise SetupError(f"{item}: Skill inventory must not contain symlinks")
        if not item.is_file() or item.name in IGNORED_FILES or item.suffix == ".pyc":
            continue
        if "__pycache__" in item.parts:
            continue
        relative = item.relative_to(path).as_posix()
        if is_runtime_path(relative):
            if relative == "SKILL.md":
                rendered = render_hermes_skill_md(
                    item.read_text(encoding="utf-8"), label=str(item)
                )
                runtime_inventory[relative] = hash_text(rendered)
            else:
                runtime_inventory[relative] = hash_file(item)
        else:
            source_validation_inventory[relative] = hash_file(item)
    return runtime_inventory, source_validation_inventory


def installed_skill_inventory(path: Path) -> dict[str, str]:
    if path.is_symlink() or not (path / "SKILL.md").is_file():
        raise SetupError(f"{path}: missing SKILL.md")
    inventory: dict[str, str] = {}
    for item in sorted(path.rglob("*")):
        if item.is_symlink():
            raise SetupError(f"{item}: installed Skill must not contain symlinks")
        if not item.is_file() or item.name in IGNORED_FILES or item.suffix == ".pyc":
            continue
        if "__pycache__" in item.parts:
            continue
        relative = item.relative_to(path).as_posix()
        if not is_runtime_path(relative):
            raise SetupError(f"{item}: unexpected non-runtime file in installed Skill")
        inventory[relative] = hash_file(item)
    return inventory


def build_plan(
    config: dict[str, Any], contract: dict[str, Any], root: Path = KIT_ROOT
) -> dict[str, Any]:
    require_selected_source(config, contract, root)
    skill_root = Path(contract["paths"]["skill_root"])
    skills: list[dict[str, Any]] = []
    for name in selected_skills(config, contract):
        source = root / "skills" / name
        runtime_inventory, source_validation_inventory = source_skill_inventories(
            source
        )
        skills.append(
            {
                "name": name,
                "source": str(source),
                "target": str(skill_root / name),
                "runtime_inventory": runtime_inventory,
                "source_validation_inventory": source_validation_inventory,
            }
        )
    return {
        "runtime": "hermes",
        "source_revision": config["source_revision"],
        "workspace_id": config["workspace_id"],
        "capabilities": config["capabilities"],
        "paths": contract["paths"],
        "installation": contract["installation"],
        "skills": skills,
        "soul": {
            "required": False,
            "preference": config["soul_preference"],
            "status": "optional-not-applied",
            "next": "review the soul command after Skills pass verification",
        },
    }


def atomic_write(path: Path, content: str, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as target:
            target.write(content)
            target.flush()
            os.fsync(target.fileno())
        os.chmod(temporary, path.stat().st_mode & 0o777 if path.exists() else mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def remove_tree(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def write_runtime_skill(source: Path, target: Path) -> None:
    target.mkdir(parents=True)
    runtime_inventory, _ = source_skill_inventories(source)
    for relative in runtime_inventory:
        source_file = source / relative
        target_file = target / relative
        target_file.parent.mkdir(parents=True, exist_ok=True)
        if relative == "SKILL.md":
            rendered = render_hermes_skill_md(
                source_file.read_text(encoding="utf-8"), label=str(source_file)
            )
            atomic_write(target_file, rendered, mode=source_file.stat().st_mode & 0o777)
        else:
            shutil.copy2(source_file, target_file)


def classify_install(
    plan: dict[str, Any], *, replace: bool
) -> tuple[list[str], list[dict[str, Any]]]:
    actions: list[str] = []
    entries: list[dict[str, Any]] = []
    for skill in plan["skills"]:
        source = Path(skill["source"])
        target = Path(skill["target"])
        if target.is_symlink():
            raise SetupError(f"{target}: refusing a symlinked Skill target")
        if not target.exists():
            state = "fresh"
        else:
            try:
                actual = installed_skill_inventory(target)
            except SetupError:
                actual = {}
            state = "identical" if actual == skill["runtime_inventory"] else "different"
        if state == "different" and not replace:
            raise SetupError(
                f"{target}: existing Skill differs; review it and rerun with --replace"
            )
        verb = "unchanged" if state == "identical" else "install"
        actions.append(f"{state}: {verb} {source} -> {target}")
        entries.append(
            {
                "skill": skill,
                "source": source,
                "target": target,
                "state": state,
            }
        )
    return actions, entries


def manifest_payload(
    plan: dict[str, Any], *, install_state: str, transaction_dir: Path | None
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": 2,
        "runtime": "hermes",
        "install_state": install_state,
        "source_revision": plan["source_revision"],
        "workspace_id": plan["workspace_id"],
        "capabilities": plan["capabilities"],
        "skills": [
            {
                "name": item["name"],
                "runtime_inventory": item["runtime_inventory"],
                "source_validation_inventory": item[
                    "source_validation_inventory"
                ],
            }
            for item in plan["skills"]
        ],
    }
    if transaction_dir is not None:
        payload["transaction_dir"] = str(transaction_dir)
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    atomic_write(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def load_transaction_journal(
    plan: dict[str, Any], manifest: dict[str, Any]
) -> tuple[Path, dict[str, Any]]:
    transaction = manifest.get("transaction_dir")
    transaction_root = Path(plan["installation"]["transaction_root"])
    transaction_dir = Path(transaction) if isinstance(transaction, str) else None
    if (
        transaction_dir is None
        or not transaction_dir.is_absolute()
        or transaction_dir.parent != transaction_root
        or transaction_dir.is_symlink()
        or not transaction_dir.is_dir()
    ):
        raise SetupError("install manifest has an invalid transaction_dir")
    journal_path = transaction_dir / "journal.json"
    journal = load_json(journal_path)
    if journal.get("schema_version") != 1 or journal.get("state") not in {
        "staging",
        "ready",
        "rolled-back",
        "rollback-failed",
    }:
        raise SetupError(f"{journal_path}: invalid transaction journal state")
    journal_skills = journal.get("skills")
    if not isinstance(journal_skills, list) or len(journal_skills) != len(
        plan["skills"]
    ):
        raise SetupError(f"{journal_path}: invalid transaction Skill entries")
    planned = {item["name"]: item for item in plan["skills"]}
    seen: set[str] = set()
    for entry in journal_skills:
        if not isinstance(entry, dict):
            raise SetupError(f"{journal_path}: invalid transaction Skill entry")
        name = entry.get("name")
        if name not in planned or name in seen:
            raise SetupError(f"{journal_path}: unexpected transaction Skill {name!r}")
        seen.add(name)
        expected = planned[name]
        expected_paths = {
            "target": expected["target"],
            "staging": str(transaction_dir / "staging" / name),
            "backup": str(transaction_dir / "backups" / name),
        }
        if any(entry.get(key) != value for key, value in expected_paths.items()):
            raise SetupError(f"{journal_path}: invalid paths for Skill {name}")
        if not isinstance(entry.get("had_target"), bool) or not isinstance(
            entry.get("changed"), bool
        ):
            raise SetupError(f"{journal_path}: invalid flags for Skill {name}")
    previous_manifest = journal.get("previous_manifest")
    expected_previous = transaction_dir / "previous-manifest.json"
    if previous_manifest is not None and previous_manifest != str(expected_previous):
        raise SetupError(f"{journal_path}: invalid previous manifest path")
    if previous_manifest is not None and not expected_previous.is_file():
        raise SetupError(f"{expected_previous}: previous manifest is missing")
    requested = journal.get("requested_manifest")
    if not isinstance(requested, dict):
        raise SetupError(f"{journal_path}: requested manifest is missing")
    for key in ("runtime", "source_revision", "workspace_id", "capabilities", "skills"):
        if requested.get(key) != manifest.get(key):
            raise SetupError(f"{journal_path}: requested manifest {key} differs")
    return journal_path, journal


def rollback_transaction(
    manifest_path: Path, journal_path: Path, *, failure: str | None = None
) -> list[str]:
    journal = load_json(journal_path)
    actions: list[str] = []
    errors: list[str] = []
    for entry in reversed(journal["skills"]):
        if not entry["changed"]:
            continue
        target = Path(entry["target"])
        backup = Path(entry["backup"])
        try:
            if entry["had_target"]:
                if backup.exists():
                    remove_tree(target)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(backup, target)
                    actions.append(f"restored {target}")
            elif target.exists() or target.is_symlink():
                remove_tree(target)
                actions.append(f"removed {target}")
        except OSError as exc:
            errors.append(f"{target}: {exc}")
    previous_manifest = journal.get("previous_manifest")
    if errors:
        failed = journal["requested_manifest"]
        failed["install_state"] = "failed"
        failed["failure"] = "; ".join(errors)
        write_json(manifest_path, failed)
        journal["state"] = "rollback-failed"
        journal["failure"] = failure or failed["failure"]
        write_json(journal_path, journal)
        raise SetupError("transaction rollback failed: " + "; ".join(errors))
    if previous_manifest:
        previous = Path(previous_manifest).read_text(encoding="utf-8")
        atomic_write(manifest_path, previous)
    else:
        failed = journal["requested_manifest"]
        failed["install_state"] = "failed"
        failed["failure"] = failure or "installation rolled back"
        write_json(manifest_path, failed)
    journal["state"] = "rolled-back"
    if failure:
        journal["failure"] = failure
    write_json(journal_path, journal)
    return actions


def install_runtime(
    plan: dict[str, Any], *, apply: bool, replace: bool = False
) -> list[str]:
    actions, entries = classify_install(plan, replace=replace)
    actions += configure_workspace(plan, apply=False)
    if not apply:
        return actions
    manifest_path = Path(plan["installation"]["manifest"])
    if manifest_path.exists():
        current = load_json(manifest_path)
        if current.get("install_state") == "staging":
            raise SetupError(
                f"{manifest_path}: interrupted transaction; run rollback before installing"
            )
    transaction_root = Path(plan["installation"]["transaction_root"])
    transaction_root.mkdir(parents=True, exist_ok=True)
    transaction_dir = Path(
        tempfile.mkdtemp(prefix=f"{plan['source_revision'][:12]}.", dir=transaction_root)
    )
    previous_manifest: Path | None = None
    if manifest_path.exists():
        previous_manifest = transaction_dir / "previous-manifest.json"
        atomic_write(previous_manifest, manifest_path.read_text(encoding="utf-8"))
    journal_entries: list[dict[str, Any]] = []
    for entry in entries:
        changed = entry["state"] != "identical"
        staging = transaction_dir / "staging" / entry["skill"]["name"]
        backup = transaction_dir / "backups" / entry["skill"]["name"]
        if changed:
            write_runtime_skill(entry["source"], staging)
            if installed_skill_inventory(staging) != entry["skill"]["runtime_inventory"]:
                raise SetupError(f"{entry['source']}: staged runtime inventory differs")
        journal_entries.append(
            {
                "name": entry["skill"]["name"],
                "target": str(entry["target"]),
                "staging": str(staging),
                "backup": str(backup),
                "had_target": entry["target"].exists(),
                "changed": changed,
            }
        )
    requested_manifest = manifest_payload(
        plan, install_state="staging", transaction_dir=transaction_dir
    )
    journal = {
        "schema_version": 1,
        "state": "staging",
        "previous_manifest": str(previous_manifest) if previous_manifest else None,
        "requested_manifest": requested_manifest,
        "skills": journal_entries,
    }
    journal_path = transaction_dir / "journal.json"
    write_json(journal_path, journal)
    write_json(manifest_path, requested_manifest)
    try:
        for entry in journal_entries:
            if not entry["changed"]:
                continue
            target = Path(entry["target"])
            backup = Path(entry["backup"])
            staging = Path(entry["staging"])
            target.parent.mkdir(parents=True, exist_ok=True)
            if entry["had_target"]:
                backup.parent.mkdir(parents=True, exist_ok=True)
                os.replace(target, backup)
            os.replace(staging, target)
        configure_workspace(plan, apply=True)
        problems = runtime_content_problems(plan)
        if problems:
            raise SetupError("; ".join(problems))
        ready = manifest_payload(
            plan, install_state="ready", transaction_dir=transaction_dir
        )
        journal["state"] = "ready"
        journal["requested_manifest"] = ready
        write_json(journal_path, journal)
        write_json(manifest_path, ready)
    except Exception as exc:
        rollback_transaction(manifest_path, journal_path, failure=str(exc))
        raise SetupError(f"installation failed and was rolled back: {exc}") from exc
    return actions


def configure_workspace(plan: dict[str, Any], *, apply: bool) -> list[str]:
    identity = Path(plan["paths"]["workspace_identity"])
    registry = Path(plan["paths"]["workspace_registry"])
    expected = plan["workspace_id"] + "\n"
    if identity.exists() and identity.read_text(encoding="utf-8") != expected:
        raise SetupError(f"{identity}: existing workspace identity differs")
    actions = []
    if not identity.exists():
        actions.append(f"create {identity}")
        if apply:
            atomic_write(identity, expected)
    else:
        actions.append(f"unchanged {identity}")
    if not registry.exists():
        actions.append(f"create {registry}")
        if apply:
            atomic_write(
                registry,
                "# Hermes Workspace Registry\n\n"
                "| Project ID | Name | Path | Status | Active Task |\n"
                "|---|---|---|---|---|\n",
            )
    else:
        actions.append(f"unchanged {registry}")
    return actions


def render_soul(config: dict[str, Any], contract: dict[str, Any]) -> str:
    template = (ADAPTER_ROOT / contract["soul"]["template"]).read_text(encoding="utf-8")
    values = {"workspace_id": config["workspace_id"]}
    for key, value in contract["paths"].items():
        values[key] = value
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    start = contract["soul"]["managed_block_start"]
    end = contract["soul"]["managed_block_end"]
    return f"{start}\n{template.strip()}\n{end}\n"


def apply_soul(config: dict[str, Any], contract: dict[str, Any], *, apply: bool) -> str:
    soul_path = Path(contract["paths"]["soul"])
    block = render_soul(config, contract)
    if not apply:
        return block
    existing = soul_path.read_text(encoding="utf-8") if soul_path.exists() else ""
    start = contract["soul"]["managed_block_start"]
    end = contract["soul"]["managed_block_end"]
    if (start in existing) != (end in existing):
        raise SetupError(f"{soul_path}: incomplete Context Kit managed block")
    if start in existing:
        before, remainder = existing.split(start, 1)
        _, after = remainder.split(end, 1)
        updated = before.rstrip() + "\n\n" + block + after.lstrip("\n")
    else:
        updated = existing.rstrip() + ("\n\n" if existing.strip() else "") + block
    if updated == existing:
        return f"optional SOUL reinforcement already current at {soul_path}"
    if soul_path.exists():
        existing_hash = hashlib.sha256(existing.encode("utf-8")).hexdigest()[:12]
        backup = (
            Path(contract["paths"]["hermes_home"])
            / "context-kit-backups"
            / config["source_revision"]
            / f"SOUL.before-{existing_hash}.md"
        )
        if backup.exists() and backup.read_text(encoding="utf-8") != existing:
            raise SetupError(f"{backup}: existing SOUL backup differs")
        if not backup.exists():
            atomic_write(backup, existing)
    atomic_write(soul_path, updated)
    return f"updated optional SOUL reinforcement at {soul_path}"


def runtime_content_problems(plan: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    for skill in plan["skills"]:
        target = Path(skill["target"])
        try:
            actual = installed_skill_inventory(target)
        except SetupError as exc:
            problems.append(str(exc))
            continue
        if actual != skill["runtime_inventory"]:
            problems.append(f"{target}: installed runtime inventory differs")
    identity = Path(plan["paths"]["workspace_identity"])
    if not identity.is_file():
        problems.append(f"{identity}: workspace identity missing")
    elif identity.read_text(encoding="utf-8") != plan["workspace_id"] + "\n":
        problems.append(f"{identity}: workspace identity differs")
    registry = Path(plan["paths"]["workspace_registry"])
    if not registry.is_file():
        problems.append(f"{registry}: workspace registry missing")
    return problems


def manifest_problems(plan: dict[str, Any]) -> list[str]:
    manifest_path = Path(plan["installation"]["manifest"])
    if not manifest_path.is_file():
        return [f"{manifest_path}: install manifest missing"]
    try:
        manifest = load_json(manifest_path)
    except SetupError as exc:
        return [str(exc)]
    problems: list[str] = []
    if manifest.get("schema_version") != 2:
        problems.append(f"{manifest_path}: install manifest schema is not 2")
    if manifest.get("install_state") != "ready":
        problems.append(
            f"{manifest_path}: install_state is {manifest.get('install_state')!r}, not 'ready'"
        )
    expected = manifest_payload(plan, install_state="ready", transaction_dir=None)
    for key in (
        "runtime",
        "source_revision",
        "workspace_id",
        "capabilities",
        "skills",
    ):
        if manifest.get(key) != expected[key]:
            problems.append(f"{manifest_path}: {key} differs from the selected plan")
    try:
        journal_path, journal = load_transaction_journal(plan, manifest)
    except SetupError as exc:
        problems.append(f"{manifest_path}: {exc}")
    else:
        if journal.get("state") != "ready":
            problems.append(f"{journal_path}: transaction is not ready")
        if journal.get("requested_manifest") != manifest:
            problems.append(f"{journal_path}: ready manifest differs from transaction")
    return problems


def verify_runtime(
    plan: dict[str, Any], *, config_path: Path | None = None
) -> dict[str, Any]:
    problems = runtime_content_problems(plan) + manifest_problems(plan)
    soul: dict[str, Any] = {
        "required": False,
        "status": "optional-not-checked",
        "user_choice_required": True,
        "next": "show the optional SOUL preview to the user and apply it only if they choose",
    }
    if config_path is not None:
        script = shlex.quote(str(Path(__file__)))
        config = shlex.quote(str(config_path))
        soul["preview_command"] = (
            f"python3 {script} soul --config {config}"
        )
        soul["apply_command"] = (
            f"python3 {script} soul --config {config} --apply"
        )
    return {
        "ready": not problems,
        "install_state": "ready" if not problems else "incomplete",
        "problems": problems,
        "skills": [item["name"] for item in plan["skills"]],
        "soul": soul,
    }


def rollback_runtime(plan: dict[str, Any], *, apply: bool) -> list[str]:
    manifest_path = Path(plan["installation"]["manifest"])
    manifest = load_json(manifest_path)
    if manifest.get("install_state") not in {"staging", "ready"}:
        raise SetupError(f"{manifest_path}: no staging or ready transaction to roll back")
    expected = manifest_payload(plan, install_state=manifest["install_state"], transaction_dir=None)
    for key in ("runtime", "source_revision", "workspace_id", "capabilities", "skills"):
        if manifest.get(key) != expected[key]:
            raise SetupError(f"{manifest_path}: {key} differs from rollback plan")
    journal_path, journal = load_transaction_journal(plan, manifest)
    actions = [
        f"rollback {entry['target']}"
        for entry in reversed(journal["skills"])
        if entry["changed"]
    ]
    if not apply:
        return actions
    return rollback_transaction(manifest_path, journal_path)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    configure = commands.add_parser("configure")
    configure.add_argument("--output", type=Path, required=True)
    configure.add_argument("--workspace-id", required=True)
    configure.add_argument(
        "--capability",
        action="append",
        choices=["project-context", "skill-authoring", "multi-repo"],
        default=[],
    )
    configure.add_argument(
        "--soul-preference",
        choices=["offer", "declined", "requested"],
        default="offer",
    )
    for name in ("plan", "install", "verify", "rollback", "soul"):
        command = commands.add_parser(name)
        command.add_argument("--config", type=Path, required=True)
        if name in {"install", "rollback", "soul"}:
            command.add_argument("--apply", action="store_true")
        if name == "install":
            command.add_argument("--replace", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        contract = load_contract()
        if args.command == "configure":
            if args.output.exists():
                raise SetupError(f"{args.output}: refusing to overwrite existing configuration")
            revision = checkout_revision()
            if revision is None:
                raise SetupError("cannot resolve an immutable commit from this checkout")
            capabilities = ["project-context"]
            for capability in args.capability:
                if capability not in capabilities:
                    capabilities.append(capability)
            candidate = {
                "schema_version": 1,
                "workspace_id": args.workspace_id,
                "source_revision": revision,
                "capabilities": capabilities,
                "soul_preference": args.soul_preference,
            }
            candidate = load_config_from_data(candidate, contract, label=str(args.output))
            require_selected_source(candidate, contract)
            atomic_write(args.output, json.dumps(candidate, indent=2, sort_keys=True) + "\n")
            print(f"created {args.output}")
            print(f"next: {Path(__file__).name} plan --config {args.output}")
            return 0
        config = load_config(args.config, contract)
        plan = build_plan(config, contract)
        if args.command == "plan":
            print(json.dumps(plan, indent=2, sort_keys=True))
        elif args.command == "install":
            for action in install_runtime(plan, apply=args.apply, replace=args.replace):
                print(action)
            if not args.apply:
                print("dry-run only; rerun with --apply on the Hermes host")
            else:
                print("runtime package committed with install_state ready")
            print("SOUL is optional and was not modified. Review it with the soul command.")
        elif args.command == "verify":
            result = verify_runtime(plan, config_path=args.config)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["ready"] else 1
        elif args.command == "rollback":
            for action in rollback_runtime(plan, apply=args.apply):
                print(action)
            if not args.apply:
                print("dry-run only; rerun rollback with --apply on the Hermes host")
        else:
            if config["soul_preference"] == "declined" and args.apply:
                raise SetupError("SOUL was explicitly declined in the runtime configuration")
            print(apply_soul(config, contract, apply=args.apply))
            if not args.apply:
                print(
                    "SOUL is optional. Apply only after the user chooses it: "
                    f"{Path(__file__).name} soul --config {args.config} --apply"
                )
        return 0
    except SetupError as exc:
        print(f"context-kit-hermes-error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

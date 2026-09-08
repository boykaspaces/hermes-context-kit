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
    if contract.get("schema_version") != 1 or contract.get("name") != "hermes":
        raise SetupError(f"{path}: unsupported Hermes runtime contract")
    if not required <= set(contract):
        raise SetupError(f"{path}: missing runtime contract fields")
    expected_paths = {
        "hermes_home": "/home/hermes/.hermes",
        "skill_root": "/home/hermes/.hermes/skills",
        "soul": "/home/hermes/.hermes/SOUL.md",
        "workspace_root": "/workspace",
        "workspace_identity": "/workspace/.hermes/WORKSPACE_ID",
        "workspace_registry": "/workspace/.hermes/WORKSPACES.md",
    }
    if contract["paths"] != expected_paths:
        raise SetupError(f"{path}: Hermes solution paths differ from the fixed contract")
    expected_installation = {
        "agent_mechanism": "skill_manage",
        "manifest": "/home/hermes/.hermes/context-kit-install.json",
        "operator_mechanism": "copy-from-immutable-checkout",
        "preserve_skill_tree": True,
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
    actual = checkout_revision(root)
    if actual is not None and actual != config["source_revision"]:
        raise SetupError(
            f"source checkout is {actual}, but configuration selects "
            f"{config['source_revision']}"
        )
    if actual is None and config["source_revision"] == "0" * 40:
        raise SetupError("replace the example source_revision with an accepted commit SHA")
    if actual is not None:
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


def skill_inventory(path: Path) -> dict[str, str]:
    if path.is_symlink() or not (path / "SKILL.md").is_file():
        raise SetupError(f"{path}: missing SKILL.md")
    inventory: dict[str, str] = {}
    for item in sorted(path.rglob("*")):
        if item.is_symlink():
            raise SetupError(f"{item}: Skill inventory must not contain symlinks")
        if not item.is_file() or item.name in IGNORED_FILES or item.suffix == ".pyc":
            continue
        if "__pycache__" in item.parts:
            continue
        inventory[item.relative_to(path).as_posix()] = hash_file(item)
    return inventory


def build_plan(
    config: dict[str, Any], contract: dict[str, Any], root: Path = KIT_ROOT
) -> dict[str, Any]:
    require_selected_source(config, contract, root)
    skill_root = Path(contract["paths"]["skill_root"])
    skills: list[dict[str, Any]] = []
    for name in selected_skills(config, contract):
        source = root / "skills" / name
        skills.append(
            {
                "name": name,
                "source": str(source),
                "target": str(skill_root / name),
                "inventory": skill_inventory(source),
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


def install_skills(
    plan: dict[str, Any], *, apply: bool, replace: bool = False
) -> list[str]:
    actions: list[str] = []
    pending: list[tuple[dict[str, Any], Path, Path, Path | None]] = []
    for skill in plan["skills"]:
        source = Path(skill["source"])
        target = Path(skill["target"])
        expected = skill["inventory"]
        if target.is_symlink():
            raise SetupError(f"{target}: refusing a symlinked Skill target")
        if target.exists():
            try:
                actual = skill_inventory(target)
            except SetupError:
                actual = {}
            if actual == expected:
                actions.append(f"unchanged {target}")
                continue
            if not replace:
                raise SetupError(
                    f"{target}: existing Skill differs; review it and rerun with --replace"
                )
            backup = (
                Path(plan["paths"]["hermes_home"])
                / "context-kit-backups"
                / plan["source_revision"]
                / target.name
            )
            if backup.exists() or backup.is_symlink():
                raise SetupError(f"{backup}: backup already exists; review before replacing")
        else:
            backup = None
        actions.append(f"install {source} -> {target}")
        pending.append((skill, source, target, backup))
    if not apply:
        return actions
    for skill, source, target, backup in pending:
        target.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f".{target.name}.", dir=target.parent))
        try:
            shutil.rmtree(staging)
            shutil.copytree(
                source,
                staging,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
            )
            if skill_inventory(staging) != skill["inventory"]:
                raise SetupError(f"{source}: staged Skill inventory differs")
        except Exception:
            if staging.exists():
                shutil.rmtree(staging)
            raise
        if backup is not None:
            backup.parent.mkdir(parents=True, exist_ok=True)
            os.replace(target, backup)
        os.replace(staging, target)
    if apply:
        manifest_path = Path(plan["installation"]["manifest"])
        manifest = {
            "schema_version": 1,
            "runtime": "hermes",
            "source_revision": plan["source_revision"],
            "workspace_id": plan["workspace_id"],
            "capabilities": plan["capabilities"],
            "skills": [
                {"name": item["name"], "inventory": item["inventory"]}
                for item in plan["skills"]
            ],
        }
        atomic_write(manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
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


def verify_runtime(
    plan: dict[str, Any], *, config_path: Path | None = None
) -> dict[str, Any]:
    problems: list[str] = []
    for skill in plan["skills"]:
        target = Path(skill["target"])
        try:
            actual = skill_inventory(target)
        except SetupError as exc:
            problems.append(str(exc))
            continue
        if actual != skill["inventory"]:
            problems.append(f"{target}: installed inventory differs")
    identity = Path(plan["paths"]["workspace_identity"])
    if not identity.is_file():
        problems.append(f"{identity}: workspace identity missing")
    elif identity.read_text(encoding="utf-8") != plan["workspace_id"] + "\n":
        problems.append(f"{identity}: workspace identity differs")
    registry = Path(plan["paths"]["workspace_registry"])
    if not registry.is_file():
        problems.append(f"{registry}: workspace registry missing")
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
        "problems": problems,
        "skills": [item["name"] for item in plan["skills"]],
        "soul": soul,
    }


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
    for name in ("plan", "install", "verify", "soul"):
        command = commands.add_parser(name)
        command.add_argument("--config", type=Path, required=True)
        if name in {"install", "soul"}:
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
            for action in install_skills(plan, apply=args.apply, replace=args.replace):
                print(action)
            for action in configure_workspace(plan, apply=args.apply):
                print(action)
            if not args.apply:
                print("dry-run only; rerun with --apply on the Hermes host")
            print("SOUL is optional and was not modified. Review it with the soul command.")
        elif args.command == "verify":
            result = verify_runtime(plan, config_path=args.config)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["ready"] else 1
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

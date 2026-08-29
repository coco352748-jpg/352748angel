#!/usr/bin/env python3
"""Read-only route dependency preflight for the clone-kk2 V7 runtime."""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import sys
import tomllib
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = SKILL_ROOT / "references" / "KK2_ROUTE_DEPENDENCIES.toml"
HOLD_EXIT = 3


class PreflightError(ValueError):
    """Raised when the dependency manifest cannot be interpreted safely."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as stream:
            manifest = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise PreflightError(f"cannot read dependency manifest: {exc}") from exc
    if not isinstance(manifest, dict):
        raise PreflightError("dependency manifest must be a TOML table")
    if manifest.get("schema_version") != 1:
        raise PreflightError("unsupported dependency manifest schema_version")
    for key in ("embedded_rq_templ", "routes", "dependencies"):
        if not isinstance(manifest.get(key), dict):
            raise PreflightError(f"manifest.{key} must be a table")
    return manifest


def safe_relative_path(raw: object, label: str) -> PurePosixPath:
    if not isinstance(raw, str) or not raw:
        raise PreflightError(f"{label} must be a non-empty relative path")
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts:
        raise PreflightError(f"{label} must not escape the declared root")
    return path


def parse_frontmatter_name(data: bytes) -> str | None:
    try:
        lines = data.decode("utf-8-sig").splitlines()
    except UnicodeDecodeError:
        return None
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if stripped.startswith("name:"):
            value = stripped.split(":", 1)[1].strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            return value or None
    return None


def resolve_embedded_path(skill_root: Path, raw: object, label: str) -> Path:
    return skill_root.joinpath(*safe_relative_path(raw, label).parts)


def check_embedded_engine(config: object, skill_root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "HOLD",
        "resolution_policy": None,
        "external_lookup": False,
        "checks": {},
        "reasons": [],
    }
    if not isinstance(config, dict):
        result["reasons"].append("embedded_rq_templ config is missing")
        return result

    result["resolution_policy"] = config.get("resolution_policy")
    policy_ok = (
        config.get("resolution_policy") == "EMBEDDED_ONLY"
        and config.get("external_lookup") == "FORBIDDEN"
    )
    result["checks"]["embedded_only_policy"] = policy_ok
    if not policy_ok:
        result["reasons"].append("embedded rq-templ policy is not locked to EMBEDDED_ONLY")

    try:
        archive = resolve_embedded_path(
            skill_root, config.get("archive_path"), "embedded_rq_templ.archive_path"
        )
        instruction = resolve_embedded_path(
            skill_root,
            config.get("root_instruction_path"),
            "embedded_rq_templ.root_instruction_path",
        )
        materializer = resolve_embedded_path(
            skill_root,
            config.get("materializer_path"),
            "embedded_rq_templ.materializer_path",
        )
        member = safe_relative_path(
            config.get("bundle_root_instruction_member"),
            "embedded_rq_templ.bundle_root_instruction_member",
        ).as_posix()
    except PreflightError as exc:
        result["reasons"].append(str(exc))
        return result

    expected_archive_hash = config.get("archive_sha256")
    expected_instruction_hash = config.get("root_instruction_sha256")
    expected_materializer_hash = config.get("materializer_sha256")
    expected_tree_hash = config.get("bundle_tree_sha256")
    expected_count = config.get("bundle_file_count")

    try:
        archive_hash = sha256_file(archive)
        instruction_bytes = instruction.read_bytes()
        instruction_hash = sha256_bytes(instruction_bytes)
        materializer_hash = sha256_file(materializer)
    except OSError as exc:
        result["reasons"].append(f"cannot read embedded rq-templ component: {exc}")
        return result

    result["archive"] = str(archive)
    result["actual_archive_sha256"] = archive_hash
    result["actual_root_instruction_sha256"] = instruction_hash
    result["actual_materializer_sha256"] = materializer_hash
    result["checks"]["archive_sha256"] = archive_hash == expected_archive_hash
    result["checks"]["root_instruction_sha256"] = (
        instruction_hash == expected_instruction_hash
    )
    result["checks"]["materializer_sha256"] = (
        materializer_hash == expected_materializer_hash
    )

    try:
        with zipfile.ZipFile(archive) as bundle:
            infos = bundle.infolist()
            names = [info.filename for info in infos]
            duplicate_names = sorted(name for name, count in Counter(names).items() if count > 1)
            unsafe_names = sorted(
                name
                for name in names
                if PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts
            )
            symlink_names = sorted(
                info.filename
                for info in infos
                if stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK
            )
            first_bad_member = bundle.testzip()
            files = sorted((info for info in infos if not info.is_dir()), key=lambda item: item.filename)
            aggregate = hashlib.sha256()
            member_hashes: dict[str, str] = {}
            for info in files:
                digest = sha256_bytes(bundle.read(info))
                member_hashes[info.filename] = digest
                aggregate.update(f"{digest}  ./{info.filename}\n".encode("utf-8"))
            tree_hash = aggregate.hexdigest()
            bundle_instruction = bundle.read(member)
    except (OSError, KeyError, zipfile.BadZipFile, RuntimeError) as exc:
        result["reasons"].append(f"cannot validate embedded rq-templ archive: {exc}")
        return result

    result["actual_bundle_file_count"] = len(files)
    result["actual_bundle_tree_sha256"] = tree_hash
    result["checks"].update(
        {
            "zip_crc": first_bad_member is None,
            "zip_duplicate_names": not duplicate_names,
            "zip_safe_paths": not unsafe_names,
            "zip_no_symlinks": not symlink_names,
            "bundle_file_count": len(files) == expected_count,
            "bundle_tree_sha256": tree_hash == expected_tree_hash,
            "root_instruction_byte_exact": bundle_instruction == instruction_bytes,
        }
    )
    if duplicate_names:
        result["duplicate_names"] = duplicate_names
    if unsafe_names:
        result["unsafe_names"] = unsafe_names
    if symlink_names:
        result["symlink_names"] = symlink_names
    if first_bad_member is not None:
        result["first_bad_member"] = first_bad_member

    failed = sorted(name for name, passed in result["checks"].items() if not passed)
    if failed:
        result["reasons"].append("embedded checks failed: " + ", ".join(failed))
    else:
        result["status"] = "PASS"
    return result


def check_candidate(candidate: object, allowed_names: set[str]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "HOLD",
        "priority": None,
        "package": None,
        "root": None,
        "contract_path": None,
        "expected_sha256": None,
        "actual_sha256": None,
        "frontmatter_name": None,
        "reasons": [],
    }
    if not isinstance(candidate, dict):
        result["reasons"].append("candidate must be a table")
        return result

    result["priority"] = candidate.get("priority")
    result["package"] = candidate.get("package")
    result["root"] = candidate.get("root")
    result["contract_path"] = candidate.get("contract_path")
    result["expected_sha256"] = candidate.get("contract_sha256")

    if not isinstance(result["priority"], int):
        result["reasons"].append("priority must be an integer")
    if not isinstance(result["package"], str) or not result["package"]:
        result["reasons"].append("package must be a non-empty string")
    if not isinstance(result["root"], str) or not result["root"]:
        result["reasons"].append("root must be a non-empty absolute path")
        return result

    root = Path(result["root"])
    if not root.is_absolute():
        result["reasons"].append("root must be absolute")
        return result
    try:
        relative = safe_relative_path(result["contract_path"], "candidate.contract_path")
    except PreflightError as exc:
        result["reasons"].append(str(exc))
        return result
    contract = root.joinpath(*relative.parts)
    result["resolved_contract"] = str(contract)

    try:
        data = contract.read_bytes()
    except OSError as exc:
        result["reasons"].append(f"cannot read contract: {exc}")
        return result
    actual_hash = sha256_bytes(data)
    actual_name = parse_frontmatter_name(data)
    result["actual_sha256"] = actual_hash
    result["frontmatter_name"] = actual_name
    if actual_hash != result["expected_sha256"]:
        result["reasons"].append("contract sha256 mismatch")
    if actual_name not in allowed_names:
        result["reasons"].append("frontmatter name is not allowed")
    if not result["reasons"]:
        result["status"] = "PASS"
    return result


def check_dependency(dependency_id: str, config: object, required: bool) -> dict[str, Any]:
    result: dict[str, Any] = {
        "dependency_id": dependency_id,
        "required": required,
        "status": "HOLD" if required else "SKIPPED",
        "selected_candidate": None,
        "candidates": [],
        "reasons": [],
    }
    if not required:
        result["reasons"].append("conditional dependency not enabled for this route")
        return result
    if not isinstance(config, dict):
        result["reasons"].append("dependency is not declared in the manifest")
        return result

    raw_names = config.get("allowed_names")
    if not isinstance(raw_names, list) or not raw_names or not all(
        isinstance(name, str) and name for name in raw_names
    ):
        result["reasons"].append("allowed_names must be a non-empty string list")
        return result
    allowed_names = set(raw_names)
    candidates = config.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        result["reasons"].append("no exact local candidates are declared")
        return result

    checked = [check_candidate(candidate, allowed_names) for candidate in candidates]
    checked.sort(
        key=lambda item: (
            item.get("priority") if isinstance(item.get("priority"), int) else sys.maxsize,
            str(item.get("package")),
        )
    )
    result["candidates"] = checked
    passing = [candidate for candidate in checked if candidate["status"] == "PASS"]
    if not passing:
        result["reasons"].append("no pinned local candidate matches its contract")
        return result
    selected = passing[0]
    result["selected_candidate"] = {
        key: selected.get(key)
        for key in (
            "priority",
            "package",
            "root",
            "resolved_contract",
            "actual_sha256",
            "frontmatter_name",
        )
    }
    result["status"] = "PASS"
    return result


def preflight(
    manifest: dict[str, Any],
    skill_root: Path,
    route_name: str,
    enabled_conditionals: set[str] | None = None,
) -> dict[str, Any]:
    enabled = set(enabled_conditionals or set())
    routes = manifest.get("routes", {})
    route = routes.get(route_name) if isinstance(routes, dict) else None
    if not isinstance(route, dict):
        raise PreflightError(f"unknown route: {route_name}")
    required = route.get("required")
    conditional = route.get("conditional")
    if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
        raise PreflightError(f"routes.{route_name}.required must be a string list")
    if not isinstance(conditional, list) or not all(
        isinstance(item, str) for item in conditional
    ):
        raise PreflightError(f"routes.{route_name}.conditional must be a string list")
    unknown_enabled = sorted(enabled - set(conditional) - set(required))
    if unknown_enabled:
        raise PreflightError(
            f"route {route_name} does not declare conditional dependencies: "
            + ", ".join(unknown_enabled)
        )

    embedded = check_embedded_engine(manifest.get("embedded_rq_templ"), skill_root)
    dependency_configs = manifest.get("dependencies", {})
    dependency_ids = list(dict.fromkeys([*required, *conditional]))
    dependencies: dict[str, Any] = {}
    for dependency_id in dependency_ids:
        is_required = dependency_id in required or dependency_id in enabled
        config = (
            dependency_configs.get(dependency_id)
            if isinstance(dependency_configs, dict)
            else None
        )
        dependencies[dependency_id] = check_dependency(
            dependency_id, config, is_required
        )

    boot_status = embedded["status"]
    route_dependencies_pass = all(
        item["status"] == "PASS"
        for item in dependencies.values()
        if item["required"]
    )
    route_status = (
        "PASS" if boot_status == "PASS" and route_dependencies_pass else "HOLD"
    )
    holds: list[dict[str, str]] = []
    if boot_status != "PASS":
        holds.append(
            {
                "scope": "BOOT",
                "component": "embedded_rq_templ",
                "reason": "; ".join(embedded["reasons"]),
            }
        )
    for dependency_id, item in dependencies.items():
        if item["required"] and item["status"] != "PASS":
            holds.append(
                {
                    "scope": f"ROUTE:{route_name}",
                    "component": dependency_id,
                    "reason": "; ".join(item["reasons"]),
                }
            )

    return {
        "schema_version": manifest.get("schema_version"),
        "manifest_id": manifest.get("manifest_id"),
        "pack_version": manifest.get("pack_version"),
        "status": route_status,
        "boot_status": boot_status,
        "route": route_name,
        "route_status": route_status,
        "mismatch_policy": manifest.get("mismatch_policy"),
        "enabled_conditionals": sorted(enabled),
        "embedded_rq_templ": embedded,
        "dependencies": dependencies,
        "holds": holds,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Dependency TOML; defaults to the clone-kk2 embedded manifest",
    )
    parser.add_argument("--route", required=True, help="One exact rq-templ route")
    parser.add_argument(
        "--require-writing",
        action="store_true",
        help="Enable the route's conditional rq-writing/rq-wri dependency",
    )
    parser.add_argument(
        "--require-nak",
        action="store_true",
        help="Enable the route's conditional rq-nak dependency",
    )
    parser.add_argument(
        "--indent", type=int, default=2, help="JSON indentation; use 0 for compact output"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    enabled: set[str] = set()
    if args.require_writing:
        enabled.add("rq-writing")
    if args.require_nak:
        enabled.add("rq-nak")
    try:
        manifest = load_manifest(args.manifest)
        result = preflight(manifest, args.manifest.resolve().parent.parent, args.route, enabled)
    except PreflightError as exc:
        result = {
            "status": "HOLD",
            "boot_status": "HOLD",
            "route": args.route,
            "route_status": "HOLD",
            "holds": [{"scope": "PREFLIGHT", "component": "manifest", "reason": str(exc)}],
        }
        print(json.dumps(result, ensure_ascii=False, indent=args.indent or None, sort_keys=True))
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=args.indent or None, sort_keys=True))
    return 0 if result["route_status"] == "PASS" else HOLD_EXIT


if __name__ == "__main__":
    raise SystemExit(main())

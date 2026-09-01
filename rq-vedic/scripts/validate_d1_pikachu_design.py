#!/usr/bin/env python3
"""Validate the D1 PIKACHU menu, layer matrix, and exact SC8 bindings."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from typing import Any


EXPECTED_LEVELS = ["ELIVEDIC", "ELICOLLEGE", "ELIPHD"]
EXPECTED_HOUSES = [f"{number}H" for number in range(1, 13)]
EXPECTED_MODULES = ["RASHI", "BHAVA", "CO2", "NAK", "pada", "Circuit"]
EXPECTED_ROUTE = [
    "1",
    "2",
    "3",
    "4",
    "D-1",
    "5-4",
    "6",
    "7",
    "8",
    "9",
    "10",
    "12",
    "13",
    "14",
    "17",
    "18",
    "19",
    "20",
    "21",
]
EXPECTED_PRE_INTERPRETATION_CALLS = ["$rq-sc8-13ab", "$rq-sc8-14ab", "$rq-sc8-01"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def zip_members(path: Path) -> set[str]:
    with zipfile.ZipFile(path) as archive:
        return set(archive.namelist())


def zip_text(path: Path, member: str) -> str:
    with zipfile.ZipFile(path) as archive:
        return archive.read(member).decode("utf-8")


def menu_calls(matrix: dict[str, Any]) -> list[str]:
    calls: list[str] = []
    houses = matrix["houses"]
    modules = [module["token"] for module in matrix["modules"]]
    for level in matrix["levels"]:
        prefix = level["id"]
        calls.append(f"{prefix} D1")
        calls.extend(f"{prefix} {house}" for house in houses)
        calls.extend(f"{prefix} {module}" for module in modules)
    return calls


def user_literal_menu_calls(matrix: dict[str, Any]) -> list[str]:
    calls: list[str] = []
    houses = matrix["houses"]
    modules = [module["token"] for module in matrix["modules"]]
    for level in matrix["levels"]:
        canonical = level["id"]
        calls.append(f"{canonical} D1")
        prefix = "ELI VEDIC" if canonical == "ELIVEDIC" else canonical
        calls.extend(f"{prefix} {house}" for house in houses)
        calls.extend(f"{prefix} {module}" for module in modules)
    return calls


def validate(matrix: dict[str, Any], sc8_root: Path) -> dict[str, Any]:
    errors: list[str] = []

    levels = [level["id"] for level in matrix.get("levels", [])]
    houses = matrix.get("houses", [])
    modules = [module["token"] for module in matrix.get("modules", [])]
    route = matrix.get("layer_engine", {}).get("route", [])

    if levels != EXPECTED_LEVELS:
        errors.append(f"level order mismatch: {levels}")
    if houses != EXPECTED_HOUSES:
        errors.append(f"house order mismatch: {houses}")
    if modules != EXPECTED_MODULES:
        errors.append(f"module order mismatch: {modules}")
    if route != EXPECTED_ROUTE:
        errors.append(f"19-layer route mismatch: {route}")

    calls = menu_calls(matrix)
    literal_calls = user_literal_menu_calls(matrix)
    if len(calls) != 57 or len(set(calls)) != 57:
        errors.append(f"menu view count/uniqueness mismatch: {len(calls)}/{len(set(calls))}")
    if len(literal_calls) != 57 or len(set(literal_calls)) != 57:
        errors.append(
            "user literal menu count/uniqueness mismatch: "
            f"{len(literal_calls)}/{len(set(literal_calls))}"
        )
    elivedic = matrix.get("levels", [{}])[0]
    if elivedic.get("aliases") != ["ELI VEDIC"]:
        errors.append("ELIVEDIC must preserve the literal alias ELI VEDIC")

    projection = matrix.get("menu_projection", {})
    per_level = projection.get("per_level", {})
    expected_core_cells = len(EXPECTED_HOUSES) * len(EXPECTED_MODULES) * len(EXPECTED_LEVELS)
    expected_views = (1 + len(EXPECTED_HOUSES) + len(EXPECTED_MODULES)) * len(EXPECTED_LEVELS)
    expected_layer_packets = len(EXPECTED_ROUTE) * len(EXPECTED_LEVELS)

    if per_level.get("view_count") != 19:
        errors.append("per-level view_count must be 19")
    if projection.get("total_menu_view_count") != expected_views:
        errors.append("total_menu_view_count must be 57")
    if projection.get("core_cell_count") != expected_core_cells:
        errors.append("core_cell_count must be 216")
    if matrix.get("layer_engine", {}).get("layer_packet_count") != expected_layer_packets:
        errors.append("layer_packet_count must be 57")
    if projection.get("cartesian_layer_view_expansion") != "PROHIBITED":
        errors.append("Cartesian menu-view x layer expansion is not prohibited")

    source_binding = matrix.get("source_binding", {})
    if source_binding.get("call") != "$rq-sc8-01":
        errors.append("source call must be $rq-sc8-01")
    package = sc8_root / source_binding.get("package", "")
    core_members: set[str] = set()
    if not package.is_file():
        errors.append(f"missing D1 package: {package}")
    else:
        package_hash = sha256(package)
        if package_hash != source_binding.get("package_sha256"):
            errors.append(f"D1 package hash mismatch: {package_hash}")
        core_members = zip_members(package)

    pre_entries = source_binding.get("pre_interpretation_source_order", [])
    pre_calls = [entry.get("call") for entry in pre_entries]
    if pre_calls != EXPECTED_PRE_INTERPRETATION_CALLS:
        errors.append(f"pre-interpretation source order mismatch: {pre_calls}")
    for expected_position, entry in enumerate(pre_entries, start=1):
        if entry.get("position") != expected_position:
            errors.append(f"pre-interpretation position mismatch: {entry.get('call')}")
        archive_text = entry.get("archive")
        if not archive_text:
            errors.append(f"pre-interpretation archive missing: {entry.get('call')}")
            continue
        archive_path = sc8_root / archive_text
        if not archive_path.is_file():
            errors.append(f"pre-interpretation archive not found: {archive_path}")
            continue
        archive_hash = sha256(archive_path)
        if archive_hash != entry.get("archive_sha256"):
            errors.append(f"pre-interpretation archive hash mismatch: {entry.get('call')}")
        member = entry.get("member")
        if member and member not in zip_members(archive_path):
            errors.append(f"pre-interpretation member missing: {entry.get('call')}:{member}")
    if source_binding.get("pre_interpretation_handoff_lock") != "VARGA_MINI_TO_VARGA_FULL_TO_D1_PIKACHU":
        errors.append("pre-interpretation Varga handoff lock missing")
    if source_binding.get("source_lane_merge") != "PROHIBITED":
        errors.append("pre-interpretation Source lane merge must be prohibited")
    if source_binding.get("evidence_double_count") != "PROHIBITED":
        errors.append("pre-interpretation evidence double count must be prohibited")

    bindings = matrix.get("layer_source_bindings", [])
    bound_layers = [binding.get("layer") for binding in bindings]
    if bound_layers != EXPECTED_ROUTE:
        errors.append(f"layer source binding order mismatch: {bound_layers}")
    if len(bound_layers) != len(set(bound_layers)):
        errors.append("duplicate layer source binding")

    bound_member_count = 0
    external_text_by_layer: dict[str, str] = {}
    for binding in bindings:
        layer = binding.get("layer")
        members = binding.get("members", [])
        bound_member_count += len(members)
        if binding.get("source_call") == "$rq-sc8-01":
            missing = sorted(set(members) - core_members)
            if missing:
                errors.append(f"layer {layer} missing core members: {missing}")
            continue

        archive_text = binding.get("archive")
        if not archive_text:
            errors.append(f"layer {layer} lacks external archive binding")
            continue
        archive_path = sc8_root / archive_text
        if not archive_path.is_file():
            errors.append(f"layer {layer} missing archive: {archive_path}")
            continue
        archive_hash = sha256(archive_path)
        if archive_hash != binding.get("archive_sha256"):
            errors.append(f"layer {layer} archive hash mismatch: {archive_hash}")
        missing = sorted(set(members) - zip_members(archive_path))
        if missing:
            errors.append(f"layer {layer} missing external members: {missing}")
        elif len(members) == 1:
            external_text_by_layer[str(layer)] = zip_text(archive_path, members[0])

    module_members = {
        member
        for module in matrix.get("modules", [])
        for member in module.get("source_members", [])
    }
    missing_module_members = sorted(module_members - core_members)
    if missing_module_members:
        errors.append(f"module source members missing: {missing_module_members}")

    excluded = {entry.get("member") for entry in matrix.get("excluded_default_evidence", [])}
    default_bound = {
        member
        for binding in bindings
        if binding.get("source_call") == "$rq-sc8-01"
        for member in binding.get("members", [])
    }
    leaked = sorted(excluded & default_bound)
    if leaked:
        errors.append(f"excluded combined evidence was rebound: {leaked}")

    yoga_text = external_text_by_layer.get("20", "")
    transit_text = external_text_by_layer.get("21", "")
    if "01. 라시 (D1)" not in yoga_text:
        errors.append("layer 20 D1 Yoga locator missing")
    if "《01 RASHI (T) / TRANSIT RASHI D1》" not in transit_text:
        errors.append("layer 21 transit D1 locator missing")
    if "TRANSIT_DATE_TIME=10-Aug-2026 06:47:36 PM" not in transit_text:
        errors.append("layer 21 transit snapshot mismatch")

    rashi_member = "02_1A_D1_RaShi_12H_AppLieD_R.txt"
    rashi_text = zip_text(package, rashi_member) if package.is_file() and rashi_member in core_members else ""
    cross_lane_checks = [
        "Rahu 26:33:09" in rashi_text,
        "Ketu 26:33:09" in rashi_text,
        "Rahu(R) | Degree=24:58:08" in transit_text,
        "Ketu(R) | Degree=24:58:08" in transit_text,
        "SL Ju" in rashi_text,
        "SL=Ra" in transit_text,
    ]
    layer_21 = next((binding for binding in bindings if binding.get("layer") == "21"), {})
    declared_differences = layer_21.get("known_cross_lane_differences", [])
    if len(declared_differences) != 4 or not all(cross_lane_checks):
        errors.append("known layer 21 natal-reference differences are not exactly locked")
    if layer_21.get("natal_reference_overwrite") != "PROHIBITED":
        errors.append("layer 21 natal reference overwrite must be prohibited")

    return {
        "status": "PASS" if not errors else "FAIL",
        "design_id": matrix.get("schema_version"),
        "source_call": source_binding.get("call"),
        "menu_view_count": len(calls),
        "user_literal_menu_view_count": len(literal_calls),
        "core_cell_count": expected_core_cells,
        "layer_count": len(route),
        "layer_packet_count": expected_layer_packets,
        "bound_member_count": bound_member_count,
        "source_package_member_count": len(core_members),
        "known_cross_lane_difference_count": len(declared_differences),
        "checks": {
            "exact_d1_package_hash": not any("D1 package hash mismatch" in error for error in errors),
            "exact_source_members": not any("missing" in error for error in errors),
            "menu_views_unique": len(calls) == len(set(calls)) == 57,
            "user_literal_aliases_valid": len(literal_calls) == len(set(literal_calls)) == 57,
            "no_cartesian_expansion": projection.get("cartesian_layer_view_expansion") == "PROHIBITED",
            "layer_order_exact": route == EXPECTED_ROUTE,
            "varga_pre_interpretation_order_locked": pre_calls == EXPECTED_PRE_INTERPRETATION_CALLS,
            "layer_21_difference_locked": len(declared_differences) == 4 and all(cross_lane_checks),
        },
        "errors": errors,
        "runtime_state": matrix.get("completion_states", {}),
    }


def main() -> int:
    script_path = Path(__file__).resolve()
    skill_root = script_path.parents[1]
    default_matrix = skill_root / "references" / "d1-pikachu-analysis-matrix.json"
    default_sc8_root = script_path.parents[2] / "rq-sc8"

    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, default=default_matrix)
    parser.add_argument("--sc8-root", type=Path, default=default_sc8_root)
    args = parser.parse_args()

    result = validate(load_json(args.matrix), args.sc8_root.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

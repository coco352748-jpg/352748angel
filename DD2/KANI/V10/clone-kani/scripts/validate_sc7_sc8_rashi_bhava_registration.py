#!/usr/bin/env python3
"""Validate the hash-locked SC7↔SC8 Rashi/Bhava work registration.

This validator proves registration and source inventory only. It deliberately
does not claim that the bidirectional grammar or either runner has executed.
Standard output is one deterministic JSON object.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA_VERSION = "KANI_SC7_SC8_BIDIRECTIONAL_GRAMMAR_REGISTRATION_V1"
REGISTRATION_ID = "KANI-SC7-SC8-RASHI-BHAVA-20260830-001"
REGISTRATION_PATH = "references/v10_runtime/sc7_sc8_rashi_bhava_registration.json"
D_ORDER = [
    "D1", "D9", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D10",
    "D11", "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60",
]
SOURCE_KEYS = ("sc7_master_zip", "sc8_master_zip")

REQUIRED_WORK_TOKENS = (
    "WORK_INSTRUCTION_ID=KANI_SC7_SC8_RASHI_BHAVA_BIDIRECTIONAL_GRAMMAR_V1",
    "REGISTRATION_STATE=REGISTERED_FIRST_UNEXECUTED_JOB",
    "EXECUTION_STATE=NOT_EXECUTED",
    "V9_BASELINE=READ_ONLY",
    "TARGET=SC7_TO_SC8_AND_SC8_TO_SC7_REPRODUCIBLE_GRAMMAR",
    "LANE_SCOPE=RASHI_THEN_BHAVA_THEN_RASHI_BHAVA_BINDING",
    "OCR_ROLE=VOID_AS_PRIMARY_TASK",
    "ASTROLOGY_RECALCULATION=FORBIDDEN",
    "PER_CHART_HARDCODING=FORBIDDEN",
    "GRAMMAR_VALIDATOR_ROLE=FINAL_ACCEPTANCE_GATE_ONLY",
    "Reverse(Forward(SC7)) = SC7",
    "Forward(Reverse(SC8)) = SC8",
    "GRAMMAR_EXTRACTION=NOT_EXECUTED",
    "ROUND_TRIP_480=HOLD_UNEXECUTED",
    "FULL_PHYSICAL_600=HOLD_UNEXECUTED",
    "NEW_PUBLIC_CALL_KEY=HOLD_UNTIL_SEPARATE_USER_REQUEST",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_safe_relative(relative: Any) -> bool:
    if not isinstance(relative, str) or not relative:
        return False
    parsed = PurePosixPath(relative)
    return not parsed.is_absolute() and ".." not in parsed.parts and relative == parsed.as_posix()


def check_bound_file(root: Path, record: Any, errors: list[str], label: str) -> Path | None:
    if not isinstance(record, dict):
        errors.append(f"{label}:record")
        return None
    relative = record.get("path")
    if not is_safe_relative(relative):
        errors.append(f"{label}:unsafe_path")
        return None
    path = root / relative
    if not path.is_file() or path.is_symlink():
        errors.append(f"{label}:missing_or_symlink")
        return None
    try:
        path.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (OSError, ValueError):
        errors.append(f"{label}:resolved_path_escape")
        return None
    if path.stat().st_size != record.get("bytes"):
        errors.append(f"{label}:bytes")
    if sha256_file(path) != record.get("sha256"):
        errors.append(f"{label}:sha256")
    return path


def member_metadata(source_key: str, filename: str) -> tuple[str, str, int | None] | None:
    if source_key == "sc7_master_zip":
        match = re.fullmatch(r"07_1AB_(D\d+)_RaShi_Sc_\.txt", filename)
        if match:
            return "RASHI", match.group(1), None
        match = re.fullmatch(r"01_2AB_(D\d+)_Bhava_Sc_\.txt", filename)
        if match:
            return "BHAVA", match.group(1), None
    elif source_key == "sc8_master_zip":
        match = re.fullmatch(r"02_(\d+)A_(D\d+)_RaShi_12H_AppLieD_R\.txt", filename)
        if match:
            return "RASHI", match.group(2), int(match.group(1))
        match = re.fullmatch(r"02_(\d+)B_(D\d+)_Bha_12H_AppLieD_R\.txt", filename)
        if match:
            return "BHAVA", match.group(2), int(match.group(1))
    return None


def exact_anchor_index(lines: list[str], heading: str) -> int | None:
    """Return the index of one exact canonical heading, rejecting duplicates."""
    matches = [index for index, line in enumerate(lines) if line == heading]
    if len(matches) != 1:
        return None
    return matches[0]


def validate_sc7_house_sections(text: str, lane: str | None) -> tuple[bool, int]:
    """Bind SC7 coverage to its canonical 12-row source-board sections."""
    lines = text.splitlines()
    if lane == "RASHI":
        anchor = exact_anchor_index(lines, "Visible Rashi Chart Snapshot")
        if anchor is None:
            return False, 0
        rows = lines[anchor + 1 : anchor + 13]
        if len(rows) != 12:
            return False, 0
        for house, line in enumerate(rows, 1):
            if re.fullmatch(
                rf"- {house}H [^ =\r\n]+ = \S(?:.*\S)?", line
            ) is None:
                return False, 0
        if lines[anchor + 13 : anchor + 15] != [
            "- Wheel Readability = FULL",
            "- Wheel Lock Status = LOCKED / SCREENSHOT_VERIFIED",
        ]:
            return False, 0
        return True, 12

    if lane == "BHAVA":
        distribution_anchor = exact_anchor_index(lines, "Visible House Distribution")
        if distribution_anchor is None:
            return False, 0
        distribution = lines[distribution_anchor + 1 : distribution_anchor + 13]
        if len(distribution) != 12:
            return False, 0
        for house, line in enumerate(distribution, 1):
            if re.fullmatch(rf"- {house}H = \S(?:.*\S)?", line) is None:
                return False, 0
        if (
            distribution_anchor + 13 >= len(lines)
            or lines[distribution_anchor + 13] != ""
        ):
            return False, 0

        structure_anchor = exact_anchor_index(lines, "Visible Bhava Structure")
        if structure_anchor is None:
            return False, 0
        structure = lines[structure_anchor + 1 : structure_anchor + 14]
        if len(structure) != 13 or structure[0] != "- Bhava System = Equal Houses":
            return False, 0
        for house, line in enumerate(structure[1:], 1):
            if re.fullmatch(
                rf"- {house}H Begin .+ / Middle .+ / End .+", line
            ) is None:
                return False, 0
        return True, 12

    return False, 0


def validate_sc8_house_sections(text: str, lane: str | None) -> tuple[bool, int]:
    """Require one ordered, lane-bound 2-1H..2-12H applied-slot sequence."""
    expected_lane = {"RASHI": "RASHI", "BHAVA": "BHAVA"}.get(lane)
    if expected_lane is None:
        return False, 0
    observed: list[int] = []
    for line in text.splitlines():
        match = re.fullmatch(
            r"2-(1[0-2]|[1-9])H\. (?:D1 SINGLE HOUSE|"
            r"TARGET D-CHART SINGLE TARGET HOUSE) (RASHI|BHAVA) SLOT(?: APPLIED)?",
            line,
        )
        if match:
            if match.group(2) != expected_lane:
                return False, 0
            observed.append(int(match.group(1)))
    return observed == list(range(1, 13)), 12 if observed == list(range(1, 13)) else 0


def validate_archive(path: Path, source_key: str, errors: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "crc": "FAIL",
        "d_order": [],
        "directories": 0,
        "text_files": 0,
        "rashi_files": 0,
        "bhava_files": 0,
        "pairs": 0,
        "utf8_files": 0,
        "house_slot_files": 0,
        "house_slot_units": 0,
        "filename_d_bindings": 0,
    }
    try:
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                errors.append(f"{source_key}:crc")
                return result
            result["crc"] = "PASS"
            infos = archive.infolist()
            directory_names = [info.filename for info in infos if info.is_dir()]
            file_infos = [info for info in infos if not info.is_dir()]
            result["directories"] = len(directory_names)
            result["text_files"] = len(file_infos)

            if directory_names != [f"{d}/" for d in D_ORDER]:
                errors.append(f"{source_key}:directory_order")
            if len(file_infos) != 40:
                errors.append(f"{source_key}:text_file_count")

            observed_d_order: list[str] = []
            by_d: dict[str, list[tuple[str, str | None]]] = {d: [] for d in D_ORDER}
            for info in file_infos:
                parsed = PurePosixPath(info.filename)
                if (
                    parsed.is_absolute()
                    or ".." in parsed.parts
                    or len(parsed.parts) != 2
                    or parsed.suffix != ".txt"
                    or info.file_size <= 0
                ):
                    errors.append(f"{source_key}:unsafe_or_invalid_member:{info.filename}")
                    continue
                dchart, filename = parsed.parts
                if dchart not in by_d:
                    errors.append(f"{source_key}:unexpected_d:{dchart}")
                    continue
                if not observed_d_order or observed_d_order[-1] != dchart:
                    if dchart in observed_d_order:
                        errors.append(f"{source_key}:noncontiguous_d:{dchart}")
                    else:
                        observed_d_order.append(dchart)
                metadata = member_metadata(source_key, filename)
                lane: str | None = None
                if metadata is None:
                    errors.append(f"{source_key}:unrecognized_member:{info.filename}")
                else:
                    lane, embedded_d, serial = metadata
                    if embedded_d != dchart:
                        errors.append(f"{source_key}:filename_d_mismatch:{info.filename}")
                    elif serial is not None and serial != int(dchart[1:]):
                        errors.append(f"{source_key}:filename_serial_mismatch:{info.filename}")
                    else:
                        result["filename_d_bindings"] += 1

                try:
                    text = archive.read(info).decode("utf-8")
                except (KeyError, RuntimeError, UnicodeDecodeError) as error:
                    errors.append(
                        f"{source_key}:utf8:{info.filename}:{type(error).__name__}"
                    )
                else:
                    result["utf8_files"] += 1
                    if source_key == "sc7_master_zip":
                        house_slots_valid, house_units = validate_sc7_house_sections(
                            text, lane
                        )
                    else:
                        house_slots_valid, house_units = validate_sc8_house_sections(
                            text, lane
                        )
                    if house_slots_valid:
                        result["house_slot_files"] += 1
                        result["house_slot_units"] += house_units
                    else:
                        errors.append(f"{source_key}:house_slots:{info.filename}")
                by_d[dchart].append((filename, lane))

            result["d_order"] = observed_d_order
            if observed_d_order != D_ORDER:
                errors.append(f"{source_key}:file_d_order")

            for dchart in D_ORDER:
                rows = by_d[dchart]
                lanes = [lane for _, lane in rows]
                if len(rows) != 2 or lanes.count("RASHI") != 1 or lanes.count("BHAVA") != 1:
                    errors.append(f"{source_key}:lane_pair:{dchart}")
                    continue
                result["pairs"] += 1
                result["rashi_files"] += 1
                result["bhava_files"] += 1
    except (OSError, zipfile.BadZipFile, RuntimeError) as error:
        errors.append(f"{source_key}:zip:{type(error).__name__}")
    return result


def validate(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    registration_path = root / REGISTRATION_PATH
    if not registration_path.is_file() or registration_path.is_symlink():
        return {
            "schema_version": "KANI_SC7_SC8_REGISTRATION_VALIDATION_V1",
            "status": "FAIL",
            "errors": ["registration:missing_or_symlink"],
        }
    try:
        registration = json.loads(registration_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return {
            "schema_version": "KANI_SC7_SC8_REGISTRATION_VALIDATION_V1",
            "status": "FAIL",
            "errors": [f"registration:json:{type(error).__name__}"],
        }

    if not (
        registration.get("schema_version") == SCHEMA_VERSION
        and registration.get("registration_id") == REGISTRATION_ID
        and registration.get("status") == "REGISTERED_HASH_LOCKED_FIRST_UNEXECUTED_JOB"
        and registration.get("authority") == {
            "kind": "CURRENT_USER_EXPLICIT_DIRECT",
            "request": "$clone-kani 등록해줘",
            "scope": "REGISTER_WORK_INSTRUCTION_AND_SOURCE_CORPUS",
        }
    ):
        errors.append("registration:header")

    scope = registration.get("scope", {})
    expected_scope = {
        "subject": "HYEWON",
        "lane_order": ["RASHI", "BHAVA", "RASHI_BHAVA_BINDING"],
        "d_order": D_ORDER,
        "dcharts": 20,
        "registered_lanes": 2,
        "paired_lane_artifacts": 40,
        "d_h_lane_units": 480,
        "source_text_files": 80,
        "physical_full_corpus": 600,
        "physical_3p_preserved_operationally_void": 20,
        "active_non_3p_corpus": 580,
    }
    if scope != expected_scope:
        errors.append("registration:scope")

    if registration.get("target_invariants") != [
        "Reverse(Forward(SC7)) = SC7",
        "Forward(Reverse(SC8)) = SC8",
    ]:
        errors.append("registration:target_invariants")

    execution = registration.get("execution", {})
    if not (
        execution.get("grammar_extraction") == "NOT_EXECUTED"
        and execution.get("registration")
        == "PASS_WHEN_V10_HASH_LOCK_AND_BOOT_VALIDATION_PASS"
        and execution.get("first_real_job")
        == "SC7_SC8_RASHI_BHAVA_BIDIRECTIONAL_GRAMMAR_EXTRACTION"
        and execution.get("forward_runner") == "NOT_CREATED"
        and execution.get("reverse_runner") == "NOT_CREATED"
        and execution.get("round_trip_480") == "HOLD_UNEXECUTED"
        and execution.get("full_physical_600") == "HOLD_UNEXECUTED"
        and execution.get("active_non_3p_580") == "HOLD_UNEXECUTED_FOR_THIS_GRAMMAR"
        and execution.get("new_public_call_key") == "HOLD_UNTIL_SEPARATE_USER_REQUEST"
    ):
        errors.append("registration:execution_state")

    boundaries = registration.get("boundary_locks", {})
    if not (
        boundaries.get("v9_baseline") == "READ_ONLY"
        and boundaries.get("ocr_primary_task") == "VOID"
        and boundaries.get("astrology_recalculation") == "FORBIDDEN"
        and boundaries.get("per_chart_hardcoding") == "FORBIDDEN"
        and boundaries.get("grammar_validator_role") == "FINAL_ACCEPTANCE_GATE_ONLY"
        and boundaries.get("three_p_reactivation")
        == "FORBIDDEN_WITHOUT_SEPARATE_USER_AUTHORITY"
        and boundaries.get("final_fna98_runtime")
        == "HOLD_UNTIL_EXISTING_REAL_RUNTIME_GATES_PASS"
    ):
        errors.append("registration:boundary_locks")

    if registration.get("registered_target_outputs") != [
        "SC7_SC8_RASHI_BHAVA_BIDIRECTIONAL_GRAMMAR.md",
        "sc7_sc8_rashi_bhava_grammar.yaml",
        "deterministic_forward_runner",
        "deterministic_reverse_runner",
        "coverage_report.json",
        "hold_registry.json",
        "20D_forward_reverse_evidence_ledger",
    ]:
        errors.append("registration:registered_target_outputs")

    work_path = check_bound_file(root, registration.get("work_instruction"), errors, "work_instruction")
    if work_path is not None:
        try:
            work_text = work_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            errors.append(f"work_instruction:read:{type(error).__name__}")
        else:
            for token in REQUIRED_WORK_TOKENS:
                if token not in work_text:
                    errors.append(f"work_instruction:token:{token}")

    archives: dict[str, dict[str, Any]] = {}
    sources = registration.get("sources", {})
    if set(sources) != set(SOURCE_KEYS):
        errors.append("registration:source_inventory")
    if not (
        sources.get("sc7_master_zip", {}).get("role") == "SC7_SOURCE_SIDE"
        and sources.get("sc8_master_zip", {}).get("role") == "SC8_PIKACHU_SIDE"
    ):
        errors.append("registration:source_roles")
    for source_key in SOURCE_KEYS:
        path = check_bound_file(root, sources.get(source_key), errors, source_key)
        if path is not None:
            archives[source_key] = validate_archive(path, source_key, errors)

    if set(archives) == set(SOURCE_KEYS):
        for source_key in SOURCE_KEYS:
            result = archives[source_key]
            if not (
                result.get("crc") == "PASS"
                and result.get("d_order") == D_ORDER
                and result.get("directories") == 20
                and result.get("text_files") == 40
                and result.get("rashi_files") == 20
                and result.get("bhava_files") == 20
                and result.get("pairs") == 20
                and result.get("utf8_files") == 40
                and result.get("house_slot_files") == 40
                and result.get("house_slot_units") == 480
                and result.get("filename_d_bindings") == 40
            ):
                errors.append(f"{source_key}:inventory_summary")

    source_text_files = sum(row.get("text_files", 0) for row in archives.values())
    paired_lane_artifacts = (
        min(row.get("text_files", 0) for row in archives.values())
        if len(archives) == 2
        else 0
    )
    d_h_lane_units = (
        min(row.get("house_slot_units", 0) for row in archives.values())
        if len(archives) == 2
        else 0
    )
    dcharts_per_archive = (
        min(row.get("directories", 0) for row in archives.values())
        if len(archives) == 2
        else 0
    )

    return {
        "schema_version": "KANI_SC7_SC8_REGISTRATION_VALIDATION_V1",
        "status": "PASS" if not errors else "FAIL",
        "registration_id": registration.get("registration_id"),
        "registration_state": registration.get("status"),
        "execution_state": execution.get("grammar_extraction"),
        "counts": {
            "archives": len(archives),
            "dcharts_per_archive": dcharts_per_archive,
            "paired_lane_artifacts": paired_lane_artifacts,
            "d_h_lane_units": d_h_lane_units,
            "source_text_files": source_text_files,
            "physical_full_corpus": scope.get("physical_full_corpus"),
            "physical_3p_operationally_void": scope.get(
                "physical_3p_preserved_operationally_void"
            ),
            "active_non_3p_corpus": scope.get("active_non_3p_corpus"),
        },
        "d_order": D_ORDER,
        "archives": archives,
        "errors": sorted(set(errors)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="clone-kani skill root (default: script parent)",
    )
    args = parser.parse_args()
    try:
        result = validate(args.root.resolve())
    except Exception as error:  # Keep stdout machine-readable under all failures.
        result = {
            "schema_version": "KANI_SC7_SC8_REGISTRATION_VALIDATION_V1",
            "status": "FAIL",
            "errors": [f"unexpected:{type(error).__name__}:{error}"],
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

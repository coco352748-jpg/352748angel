#!/usr/bin/env python3
"""Build the deterministic KANI V10 execution-evidence manifest.

V10 is an additive E5/E6 evidence overlay.  This builder never mutates V9 and
never promotes the user-controlled final gate.  Optional E5/E6 validation
artifacts are recorded as pending until they exist; once they appear, a stale
manifest fails ``--check`` and must be rebuilt so the new bytes are hash-bound.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "KANI_CAUSAL_RESTORE_V10_MANIFEST_V1"
EXPECTED_V9_TREE_SHA256 = "913cb921f9d5f97b351a4455f3e05cb1d441a00cec24291caf78eac5a690c0d9"

CLAIMS = {
    "SECOND_RESTORE": "EVIDENCE_REVIEW",
    "V10": "EXPECTED_VALUE_BOUND",
    "FINAL_PASS": "HOLD_USER_REVIEW_OF_RECORD_REPLAY_EVIDENCE",
    "V9_BASELINE": "PRESERVED_NOT_OVERWRITTEN",
    "E5_E6_OVERLAY": "ADD_TO_V9_DO_NOT_OVERWRITE",
    "GLOBAL_29_LANE_E5": "HOLD_28_JUDGMENT_TO_SENTENCE_LANES_UNTESTED",
    "REAL_LONG_DRIFT": "HOLD_REAL_LONG_DRIFT_NOT_PROVEN",
}

PATHS = {
    "v9_baseline": "references/v9_baseline",
    "historical_v9_e5": "references/v9_closure_runs/run_20260829_vas26/e5",
    "historical_v9_e6": "references/v9_closure_runs/run_20260829_vas26/e6",
    "v10_e5": "references/v10_runs/run_20260830_vas27/e5",
    "v10_e6": "references/v10_runs/run_20260830_vas27/e6",
    "v10_e5_validation": "references/v10_runtime/e5_independent_validation.json",
    "v10_e6_validation": "references/v10_runtime/e6_independent_validation.json",
    "protocol": "references/KANI_CAUSAL_RESTORE_V10_PROTOCOL.md",
    "router": "references/DATASET_TO_PIKACHU_JUDGMENT_ROUTER_V10.json",
    "source_registry": "references/v10_sources/user_upload_20260830/manifest.json",
    "audit_sidecar": "references/v10_runtime/v9_e5_e6_audit_sidecar.json",
    "admission": "references/v10_runtime/vas27_admission_and_scope.json",
    "sc7_router": "references/KANI_SECOND_ACTION_ROUTER_V2.json",
    "sc7_run_manifest": "references/v10_runtime/router_run/router_run_manifest.json",
    "sc7_records": "references/v10_runtime/router_run/router_records.jsonl",
    "sc7_source_index": "references/v10_runtime/router_run/source_index.json",
    "sc7_validation": "references/v10_runtime/independent_router_report.json",
    "sc7_validation_ledger": "references/v10_runtime/independent_router_replay.jsonl",
}

EXPECTED_SOURCE_FILES = {
    "HYEWON_VAS25_D1-D60_♤.txt": (2025, "CALIBRATION_SOURCE_HISTORY"),
    "HEAWON_VAS25_CO2_99_♤.txt": (2025, "CALIBRATION_EXPECTED_STRUCTURE_HISTORY"),
    "HYEWON_VAS26_D1-D60_♤.txt": (2026, "V9_E5_SOURCE_AND_CALIBRATION_HISTORY"),
    "HEAWON_VAS26_CO2_99_♤.txt": (2026, "CALIBRATION_EXPECTED_STRUCTURE_HISTORY"),
    "HYEWON_VAS27_D1-D60_♤.txt": (2027, "V10_E5_EXECUTION_DATASET"),
    "HEAWON_VAS27_CO2_99_♤.txt": (2027, "V10_E5_HASH_LOCKED_EXPECTED_PIKACHU_SENTENCES"),
}

IMPLEMENTATION_PATHS = {
    "e5_producer": "scripts/run_kani_v10_e5.py",
    "e5_independent_validator": "scripts/validate_kani_v10_e5.py",
    "e6_producer": "scripts/run_kani_v10_e6.py",
    "e6_independent_validator": "scripts/validate_kani_v10_e6.py",
    "sc7_calibration_producer": "scripts/run_kani_v10_router.py",
    "sc7_calibration_validator": "scripts/validate_kani_v10_router.py",
    "v10_manifest_builder": "scripts/build_kani_v10_manifest.py",
    "v10_runtime_validator": "scripts/validate_kani_v10_runtime.py",
    "skill_entrypoint": "SKILL.md",
    "boot_validator": "scripts/validate_kani_boot.py",
    "agent_interface": "agents/openai.yaml",
}


class ManifestError(ValueError):
    """Raised when present evidence violates its locked contract."""


def compact_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def pretty_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ManifestError(f"invalid JSON artifact {path}: {error}") from error


def jsonl_count(path: Path) -> int:
    raw = path.read_bytes()
    if not raw or not raw.endswith(b"\n"):
        raise ManifestError(f"JSONL artifact must be non-empty and LF-terminated: {path}")
    count = 0
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ManifestError(f"invalid UTF-8 JSONL artifact {path}: {error}") from error
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line:
            raise ManifestError(f"blank JSONL row is forbidden: {path}:{line_number}")
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise ManifestError(f"invalid JSONL artifact {path}:{line_number}: {error}") from error
        if not isinstance(row, dict):
            raise ManifestError(f"JSONL object required: {path}:{line_number}")
        count += 1
    return count


def file_record(root: Path, relative: str, *, optional: bool = False) -> dict[str, Any]:
    path = root / relative
    if not path.is_file():
        if optional:
            return {"availability": "MISSING_PENDING", "path": relative}
        raise ManifestError(f"required artifact missing: {relative}")
    if path.is_symlink():
        raise ManifestError(f"artifact symlink is forbidden: {relative}")
    return {
        "availability": "PRESENT",
        "path": relative,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def tree_snapshot(directory: Path) -> dict[str, dict[str, Any]]:
    if not directory.is_dir():
        raise ManifestError(f"directory missing: {directory}")
    rows: dict[str, dict[str, Any]] = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ManifestError(f"tree symlink is forbidden: {path}")
        if path.is_file():
            rows[path.relative_to(directory).as_posix()] = {
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
    if not rows:
        raise ManifestError(f"directory contains no files: {directory}")
    return rows


def tree_id(files: dict[str, dict[str, Any]]) -> str:
    return sha256_bytes(compact_json(files))


def directory_record(root: Path, relative: str, *, optional: bool = False) -> dict[str, Any]:
    directory = root / relative
    if not directory.is_dir():
        if optional:
            return {"availability": "MISSING_PENDING", "path": relative}
        raise ManifestError(f"required directory missing: {relative}")
    files = tree_snapshot(directory)
    return {
        "availability": "PRESENT",
        "path": relative,
        "file_count": len(files),
        "bytes": sum(row["bytes"] for row in files.values()),
        "tree_sha256": tree_id(files),
        "files": files,
    }


def verify_artifact_map(base: Path, artifact_map: Any, label: str) -> None:
    if not isinstance(artifact_map, dict) or not artifact_map:
        raise ManifestError(f"{label} has no artifact map")
    for relative, metadata in artifact_map.items():
        if not isinstance(relative, str) or not isinstance(metadata, dict):
            raise ManifestError(f"{label} has a malformed artifact row")
        path = base / relative
        if not path.is_file():
            raise ManifestError(f"{label} artifact missing: {relative}")
        if path.is_symlink():
            raise ManifestError(f"{label} artifact symlink is forbidden: {relative}")
        if sha256_file(path) != metadata.get("sha256"):
            raise ManifestError(f"{label} artifact hash mismatch: {relative}")
        if metadata.get("bytes") is not None and path.stat().st_size != metadata.get("bytes"):
            raise ManifestError(f"{label} artifact size mismatch: {relative}")


def verify_sha_sidecar(path: Path, expected: str, label: str) -> None:
    if not path.is_file():
        raise ManifestError(f"{label} SHA sidecar missing")
    expected_text = f"{expected}  {path.stem}.json\n"
    if path.read_text(encoding="utf-8") != expected_text:
        raise ManifestError(f"{label} SHA sidecar mismatch")


def build_v9_baseline(root: Path) -> dict[str, Any]:
    relative = PATHS["v9_baseline"]
    record = directory_record(root, relative)
    if record["tree_sha256"] != EXPECTED_V9_TREE_SHA256:
        raise ManifestError("immutable V9 baseline tree hash changed")
    expected_names = {
        "DD2_FINAL_CLOSURE_WORK_INSTRUCTION_FNA98.txt",
        "KANI_JUDGMENT_PROTOCOL_V3.md",
        "decision_runtime.json",
        "judgment_protocol_v3.json",
        "kani_v9_manifest.json",
        "monotonic_checkpoint.json",
    }
    if set(record["files"]) != expected_names:
        raise ManifestError("immutable V9 baseline file set changed")
    manifest_path = root / relative / "kani_v9_manifest.json"
    v9_manifest = read_json(manifest_path)
    verify_artifact_map(manifest_path.parent, v9_manifest.get("artifacts"), "V9 baseline")
    record.update({
        "expected_tree_sha256": EXPECTED_V9_TREE_SHA256,
        "unchanged": True,
        "overwrite_count": 0,
        "manifest_sha256": sha256_file(manifest_path),
        "judgment_restore_status": v9_manifest.get("judgment_restore_status"),
    })
    return record


def build_historical_closure(root: Path, sidecar: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for stage in ("e5", "e6"):
        relative = PATHS[f"historical_v9_{stage}"]
        record = directory_record(root, relative)
        manifest_path = root / relative / f"{stage}_manifest.json"
        manifest = read_json(manifest_path)
        verify_artifact_map(manifest_path.parent, manifest.get("artifacts"), f"historical V9 {stage.upper()}")
        manifest_sha = sha256_file(manifest_path)
        sidecar_stage = sidecar.get(stage, {})
        if sidecar_stage.get("artifact_sha256") != manifest_sha:
            raise ManifestError(f"audit sidecar does not bind historical V9 {stage.upper()} manifest")
        verify_sha_sidecar(manifest_path.with_suffix(".sha256"), manifest_sha, f"historical V9 {stage.upper()}")
        record.update({
            "manifest_sha256": manifest_sha,
            "original_declared_status": sidecar_stage.get("original_declared_status"),
            "v10_authoritative_status": sidecar_stage.get("v10_authoritative_status"),
        })
        result[stage] = record
    return result


def validate_source_registry(root: Path, registry_path: Path) -> dict[str, dict[str, Any]]:
    registry = read_json(registry_path)
    rows = registry.get("files")
    if not (
        registry.get("schema_version") == "KANI_V10_USER_SOURCE_REGISTRY_V1"
        and registry.get("status") == "PASS_EXACT_USER_UPLOAD_BYTES_PRESERVED"
        and isinstance(rows, list)
        and len(rows) == 6
    ):
        raise ManifestError("V10 source registry contract is invalid")
    names = [row.get("filename") for row in rows if isinstance(row, dict)]
    if set(names) != set(EXPECTED_SOURCE_FILES) or len(names) != 6:
        raise ManifestError("V10 source registry file set is not the exact six-file contract")
    actual: dict[str, dict[str, Any]] = {}
    for row in rows:
        filename = row["filename"]
        relative = Path(filename)
        if relative.is_absolute() or len(relative.parts) != 1 or relative.name != filename:
            raise ManifestError(f"unsafe registered V10 source filename: {filename!r}")
        expected_year, expected_role = EXPECTED_SOURCE_FILES[filename]
        if row.get("year") != expected_year or row.get("role") != expected_role:
            raise ManifestError(f"registered V10 source role/year mismatch: {filename}")
        path = registry_path.parent / filename
        if not path.is_file() or path.is_symlink():
            raise ManifestError(f"registered V10 source missing or symlinked: {filename}")
        raw = path.read_bytes()
        metadata = {
            "bytes": len(raw),
            "lines": raw.count(b"\n"),
            "sha256": sha256_bytes(raw),
        }
        for field in ("bytes", "lines", "sha256"):
            if metadata[field] != row.get(field):
                raise ManifestError(f"registered V10 source {field} mismatch: {filename}")
        actual[filename] = metadata
    return actual


def build_core(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    core: dict[str, Any] = {}
    for key in ("protocol", "router", "source_registry", "audit_sidecar", "admission"):
        core[key] = file_record(root, PATHS[key], optional=(key in {"protocol", "admission"}))

    router_path = root / PATHS["router"]
    router = read_json(router_path)
    if not (
        router.get("schema_version") == "DATASET_TO_PIKACHU_JUDGMENT_ROUTER_V10"
        and router.get("status") == "EXPECTED_VALUE_BOUND__SECOND_RESTORE_EVIDENCE_REVIEW"
        and router.get("scope", {}).get("expected_total_records") == 114
        and len(router.get("boundary_tests", [])) == 9
        and len(set(router.get("boundary_tests", []))) == 9
    ):
        raise ManifestError("V10 Dataset-to-Pikachu router contract is invalid")

    registry_path = root / PATHS["source_registry"]
    source_files = validate_source_registry(root, registry_path)

    sidecar = read_json(root / PATHS["audit_sidecar"])
    if not (
        sidecar.get("schema_version") == "KANI_V10_V9_CLOSURE_AUDIT_V1"
        and sidecar.get("status") == "PASS_CORRECTION_RECORDED"
        and sidecar.get("immutability", {}).get("edit_v9_baseline_bytes") == "FORBIDDEN"
        and sidecar.get("immutability", {}).get("edit_existing_v9_closure_bytes") == "FORBIDDEN"
        and sidecar.get("e6", {}).get("real_long_drift_status") == "HOLD_UNEXECUTED"
    ):
        raise ManifestError("V9 E5/E6 audit sidecar contract is invalid")

    admission_path = root / PATHS["admission"]
    if admission_path.is_file():
        admission = read_json(admission_path)
        if not (
            admission.get("schema_version") == "KANI_V10_VAS27_ADMISSION_V1"
            and admission.get("status") == "PASS_FOR_EXPECTED_VALUE_BOUND_EVIDENCE_REVIEW"
            and admission.get("terminal_states") == {
                "FINAL_PASS": CLAIMS["FINAL_PASS"],
                "SECOND_RESTORE": CLAIMS["SECOND_RESTORE"],
                "V10": CLAIMS["V10"],
            }
            and admission.get("scope", {}).get("global_sentence_routes_tested") == 1
            and admission.get("scope", {}).get("global_sentence_routes_untested") == 28
        ):
            raise ManifestError("V10 VAS27 admission contract is invalid")
    core["source_files"] = source_files
    return core, sidecar


def validation_pass(document: dict[str, Any]) -> bool:
    return document.get("status") == "PASS"


def producer_not_imported(document: dict[str, Any]) -> bool:
    value = document.get("producer_imported")
    if value is None:
        value = document.get("oracle_policy", {}).get("producer_imported")
    return value is False


def build_v10_e5(root: Path, v9_baseline: dict[str, Any]) -> dict[str, Any]:
    relative = PATHS["v10_e5"]
    record = directory_record(root, relative, optional=True)
    if record["availability"] == "MISSING_PENDING":
        record["independent_validation"] = file_record(
            root, PATHS["v10_e5_validation"], optional=True
        )
        return record

    manifest_path = root / relative / "e5_manifest.json"
    if not manifest_path.is_file():
        record["availability"] = "INCOMPLETE_PENDING"
        record["independent_validation"] = file_record(
            root, PATHS["v10_e5_validation"], optional=True
        )
        return record
    manifest = read_json(manifest_path)
    verify_artifact_map(manifest_path.parent, manifest.get("artifacts"), "V10 E5")
    if not (
        manifest.get("schema_version") == "KANI_V10_E5_EXECUTION_OVERLAY_V1"
        and manifest.get("status") == "PASS_EXECUTION_EVIDENCE_114_OF_114"
        and manifest.get("second_restore") == CLAIMS["SECOND_RESTORE"]
        and manifest.get("v10") == CLAIMS["V10"]
        and manifest.get("final_pass") == CLAIMS["FINAL_PASS"]
        and manifest.get("global_29_lane_e5") == CLAIMS["GLOBAL_29_LANE_E5"]
        and manifest.get("overlay") == CLAIMS["E5_E6_OVERLAY"]
        and manifest.get("counts", {}).get("total_records") == 114
        and manifest.get("counts", {}).get("expected_exact_sentences") == 114
        and manifest.get("v9_baseline", {}).get("state") == CLAIMS["V9_BASELINE"]
        and manifest.get("v9_baseline", {}).get("manifest_sha256") == v9_baseline.get("manifest_sha256")
    ):
        raise ManifestError("V10 E5 execution manifest contract is invalid")
    run_payload = {**manifest, "run_id": None}
    if manifest.get("run_id") != sha256_bytes(compact_json(run_payload)):
        raise ManifestError("V10 E5 run_id is invalid")
    registry = read_json(root / PATHS["source_registry"])
    registry_by_name = {row["filename"]: row for row in registry.get("files", [])}
    source_inventory = manifest.get("source_inventory", {})
    if not (
        manifest.get("router", {}).get("sha256") == sha256_file(root / PATHS["router"])
        and manifest.get("source_registry_sha256") == sha256_file(root / PATHS["source_registry"])
        and set(source_inventory) == set(EXPECTED_SOURCE_FILES)
        and all(
            source_inventory[name].get("sha256") == registry_by_name[name].get("sha256")
            and source_inventory[name].get("bytes") == registry_by_name[name].get("bytes")
            and source_inventory[name].get("role") == registry_by_name[name].get("role")
            and source_inventory[name].get("year") == registry_by_name[name].get("year")
            for name in EXPECTED_SOURCE_FILES
        )
    ):
        raise ManifestError("V10 E5 router/source bindings are invalid")
    ledger_path = manifest_path.parent / "e5_decision_ledger.jsonl"
    if jsonl_count(ledger_path) != 114:
        raise ManifestError("V10 E5 decision ledger does not contain 114 records")
    record.update({
        "manifest_sha256": sha256_file(manifest_path),
        "status": manifest.get("status"),
        "records": 114,
    })

    validation = file_record(root, PATHS["v10_e5_validation"], optional=True)
    if validation["availability"] == "PRESENT":
        report = read_json(root / PATHS["v10_e5_validation"])
        ledger_path = manifest_path.parent / "e5_decision_ledger.jsonl"
        if not (
            report.get("schema_version") == "KANI_V10_E5_INDEPENDENT_VALIDATION_V1"
            and validation_pass(report)
            and producer_not_imported(report)
            and report.get("e5_status") == "PASS_EXECUTION_EVIDENCE_114_OF_114"
            and report.get("second_restore") == CLAIMS["SECOND_RESTORE"]
            and report.get("v10") == CLAIMS["V10"]
            and report.get("final_pass") == CLAIMS["FINAL_PASS"]
            and report.get("validated_run_id") == manifest.get("run_id")
            and report.get("ledger_sha256") == sha256_file(ledger_path)
            and report.get("router_sha256") == sha256_file(root / PATHS["router"])
            and report.get("source_dataset_sha256")
            == manifest.get("source_inventory", {}).get("HYEWON_VAS27_D1-D60_♤.txt", {}).get("sha256")
            and report.get("counts") == {
                "bhava_records": 50,
                "expected_exact_sentence_replays": 114,
                "rashi_records": 64,
                "stored_records": 114,
                "total_derived_records": 114,
            }
            and report.get("errors") == []
            and report.get("oracle_policy", {}).get("expected_opened_after_independent_render") is True
        ):
            raise ManifestError("V10 E5 independent validation contract is invalid")
        validation["schema_version"] = report.get("schema_version")
        validation["status"] = "PASS"
    record["independent_validation"] = validation
    return record


def boundary_pass_count(document: Any) -> tuple[int | None, int | None]:
    """Extract a declared or explicit 9/9 count without trusting one key shape."""
    if not isinstance(document, dict):
        return None, None
    candidate_pairs = (
        (document.get("passed"), document.get("total")),
        (document.get("pass_count"), document.get("test_count")),
        (document.get("passed_tests"), document.get("total_tests")),
        (document.get("counts", {}).get("passed"), document.get("counts", {}).get("total")),
        (
            document.get("counts", {}).get("passed_boundary_tests"),
            document.get("counts", {}).get("boundary_tests"),
        ),
    )
    for passed, total in candidate_pairs:
        if isinstance(passed, int) and isinstance(total, int):
            return passed, total
    for key in ("tests", "results", "boundary_tests"):
        rows = document.get(key)
        if isinstance(rows, list):
            passed = sum(
                1
                for row in rows
                if isinstance(row, dict)
                and (row.get("status") == "PASS" or row.get("passed") is True)
            )
            return passed, len(rows)
        if isinstance(rows, dict):
            passed = rows.get("pass_count", rows.get("passed"))
            total = rows.get("test_count", rows.get("total"))
            if isinstance(passed, int) and isinstance(total, int):
                return passed, total
    return None, None


def build_v10_e6(root: Path) -> dict[str, Any]:
    relative = PATHS["v10_e6"]
    record = directory_record(root, relative, optional=True)
    if record["availability"] == "MISSING_PENDING":
        record["independent_validation"] = file_record(
            root, PATHS["v10_e6_validation"], optional=True
        )
        return record

    manifest_path = root / relative / "e6_manifest.json"
    if not manifest_path.is_file():
        record["availability"] = "INCOMPLETE_PENDING"
        record["independent_validation"] = file_record(
            root, PATHS["v10_e6_validation"], optional=True
        )
        return record
    manifest = read_json(manifest_path)
    verify_artifact_map(manifest_path.parent, manifest.get("artifacts"), "V10 E6")
    if not (
        manifest.get("schema_version") == "KANI_V10_E6_REOPEN_OVERLAY_V1"
        and manifest.get("status") == "PASS_REOPEN_EVIDENCE_9_OF_9"
        and manifest.get("second_restore") == CLAIMS["SECOND_RESTORE"]
        and manifest.get("v10") == CLAIMS["V10"]
        and manifest.get("final_pass") == CLAIMS["FINAL_PASS"]
        and manifest.get("global_29_lane_e5") == CLAIMS["GLOBAL_29_LANE_E5"]
        and manifest.get("real_long_drift") == CLAIMS["REAL_LONG_DRIFT"]
        and manifest.get("inputs", {}).get("v9_baseline_tree_sha256") == EXPECTED_V9_TREE_SHA256
    ):
        raise ManifestError("V10 E6 reopen manifest contract is invalid")
    run_payload = {**manifest, "run_id": None}
    if manifest.get("run_id") != sha256_bytes(compact_json(run_payload)):
        raise ManifestError("V10 E6 run_id is invalid")
    e5_manifest_path = root / PATHS["v10_e5"] / "e5_manifest.json"
    e5_manifest = read_json(e5_manifest_path)
    expected_inputs = {
        "audit_sidecar_sha256": sha256_file(root / PATHS["audit_sidecar"]),
        "calibration_independent_ledger_sha256": sha256_file(root / PATHS["sc7_validation_ledger"]),
        "calibration_independent_report_sha256": sha256_file(root / PATHS["sc7_validation"]),
        "calibration_manifest_sha256": sha256_file(root / PATHS["sc7_run_manifest"]),
        "router_sha256": sha256_file(root / PATHS["router"]),
        "source_registry_sha256": sha256_file(root / PATHS["source_registry"]),
        "v9_baseline_tree_sha256": EXPECTED_V9_TREE_SHA256,
        "v9_e5_manifest_sha256": sha256_file(
            root / PATHS["historical_v9_e5"] / "e5_manifest.json"
        ),
        "v9_e6_manifest_sha256": sha256_file(
            root / PATHS["historical_v9_e6"] / "e6_manifest.json"
        ),
    }
    if not (
        manifest.get("inputs") == expected_inputs
        and manifest.get("entry_condition", {}).get("e5_manifest_sha256") == sha256_file(e5_manifest_path)
        and manifest.get("entry_condition", {}).get("e5_run_id") == e5_manifest.get("run_id")
        and manifest.get("entry_condition", {}).get("e5_status") == e5_manifest.get("status")
        and manifest.get("protected_input_change_count") == 0
    ):
        raise ManifestError("V10 E6 protected input bindings are invalid")
    boundary_path = manifest_path.parent / "boundary_test_9of9.json"
    if not boundary_path.is_file():
        raise ManifestError("V10 E6 boundary_test_9of9.json is missing")
    passed, total = boundary_pass_count(read_json(boundary_path))
    if (passed, total) != (9, 9):
        raise ManifestError("V10 E6 boundary evidence is not 9/9")
    record.update({
        "manifest_sha256": sha256_file(manifest_path),
        "status": manifest.get("status"),
        "boundary_tests": {"passed": passed, "total": total},
    })

    validation = file_record(root, PATHS["v10_e6_validation"], optional=True)
    if validation["availability"] == "PRESENT":
        report = read_json(root / PATHS["v10_e6_validation"])
        boundary_sha = sha256_file(boundary_path)
        if not (
            report.get("schema_version") == "KANI_V10_E6_INDEPENDENT_VALIDATION_V1"
            and validation_pass(report)
            and producer_not_imported(report)
            and report.get("validated_run_id") == manifest.get("run_id")
            and report.get("e6_manifest_sha256") == sha256_file(manifest_path)
            and report.get("boundary_9of9_sha256") == boundary_sha
            and boundary_pass_count(report) == (9, 9)
            and report.get("errors") == []
        ):
            raise ManifestError("V10 E6 independent validation contract is invalid")
        validation["schema_version"] = report.get("schema_version")
        validation["status"] = "PASS"
    record["independent_validation"] = validation
    return record


def build_sc7_calibration(root: Path) -> dict[str, Any]:
    artifacts = {
        key: file_record(root, PATHS[key])
        for key in (
            "sc7_router",
            "sc7_run_manifest",
            "sc7_records",
            "sc7_source_index",
            "sc7_validation",
            "sc7_validation_ledger",
        )
    }
    run_manifest = read_json(root / PATHS["sc7_run_manifest"])
    sc7_router = read_json(root / PATHS["sc7_router"])
    if not (
        sc7_router.get("schema_version") == "KANI_SECOND_ACTION_ROUTER_V2"
        and sc7_router.get("router_id") == "KANI_SECOND_ACTION_ROUTER_V2"
        and sc7_router.get("terminal_version_boundary") == "LOCKED_NO_AUTOMATIC_V11"
    ):
        raise ManifestError("SC7 calibration router contract is invalid")
    run_base = (root / PATHS["sc7_run_manifest"]).parent
    for key in ("records", "source_index"):
        metadata = run_manifest.get(key, {})
        path = run_base / str(metadata.get("path", ""))
        if not path.is_file() or sha256_file(path) != metadata.get("sha256"):
            raise ManifestError(f"SC7 calibration {key} hash binding is invalid")
        if path.stat().st_size != metadata.get("bytes"):
            raise ManifestError(f"SC7 calibration {key} size binding is invalid")
    if not (
        run_manifest.get("schema_version") == "KANI_V10_ROUTER_RUN_V1"
        and run_manifest.get("status") == "PASS_TESTED_SCOPE_240"
        and run_manifest.get("counts", {}).get("records") == 240
        and run_manifest.get("counts", {}).get("exact_sentence_replay") == 240
        and jsonl_count(root / PATHS["sc7_records"]) == 240
    ):
        raise ManifestError("SC7 calibration producer contract is invalid")
    run_id = run_manifest.get("run_id")
    run_core = dict(run_manifest)
    run_core.pop("run_id", None)
    if run_id != sha256_bytes(compact_json(run_core)):
        raise ManifestError("SC7 calibration run_id is invalid")
    if not (
        run_manifest.get("router", {}).get("sha256") == sha256_file(root / PATHS["sc7_router"])
        and run_manifest.get("retained_v9_manifest", {}).get("sha256")
        == sha256_file(root / PATHS["v9_baseline"] / "kani_v9_manifest.json")
    ):
        raise ManifestError("SC7 calibration authority binding is invalid")

    report = read_json(root / PATHS["sc7_validation"])
    ledger_meta = report.get("independent_ledger", {})
    ledger_path = root / PATHS["sc7_validation_ledger"]
    if not (
        report.get("schema_version") == "KANI_V10_INDEPENDENT_REPLAY_REPORT_V1"
        and report.get("status") == "PASS"
        and report.get("producer_imported") is False
        and report.get("counts", {}).get("records") == 240
        and report.get("counts", {}).get("exact_replay") == 240
        and ledger_meta.get("records") == 240
        and ledger_meta.get("bytes") == ledger_path.stat().st_size
        and ledger_meta.get("sha256") == sha256_file(ledger_path)
        and jsonl_count(ledger_path) == 240
        and report.get("template_sha256") == run_manifest.get("router", {}).get("template_sha256")
    ):
        raise ManifestError("SC7 independent calibration replay contract is invalid")
    return {
        "status": "PASS_CALIBRATION_240_OF_240",
        "scope": "BOUNDARY_CALIBRATION_NOT_GLOBAL_E5_PROMOTION",
        "records": 240,
        "exact_replay": 240,
        "artifacts": artifacts,
    }


def component_state(record: dict[str, Any]) -> str:
    return str(record.get("availability", "MISSING_PENDING"))


def build_manifest(root: Path) -> dict[str, Any]:
    core, sidecar = build_core(root)
    v9_baseline = build_v9_baseline(root)
    historical = build_historical_closure(root, sidecar)
    v10_e5 = build_v10_e5(root, v9_baseline)
    v10_e6 = build_v10_e6(root)
    sc7 = build_sc7_calibration(root)
    implementation_bindings = {
        "status": "HASH_LOCKED_EXECUTABLES_AND_ENTRYPOINTS",
        "artifacts": {
            key: file_record(root, relative)
            for key, relative in IMPLEMENTATION_PATHS.items()
        },
    }

    pending: list[str] = []
    for key in ("protocol", "admission"):
        if component_state(core[key]) != "PRESENT":
            pending.append(key)
    for stage, record in (("v10_e5", v10_e5), ("v10_e6", v10_e6)):
        if component_state(record) != "PRESENT":
            pending.append(stage)
        if component_state(record.get("independent_validation", {})) != "PRESENT":
            pending.append(f"{stage}_independent_validation")

    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "engine": "KANI_CAUSAL_RESTORE_V10",
        "purpose": "SECOND_RESTORE_ROUTER_EXECUTION_EVIDENCE_BOARD",
        "claims": CLAIMS,
        "bundle_completeness": (
            "EVIDENCE_PRESENT_AWAITING_USER_REVIEW"
            if not pending
            else "PENDING_OPTIONAL_EXECUTION_ARTIFACTS"
        ),
        "pending_components": sorted(pending),
        "v9_baseline": v9_baseline,
        "historical_v9_e5_e6": historical,
        "v10_core": core,
        "v10_e5_overlay": v10_e5,
        "v10_e6_overlay": v10_e6,
        "sc7_calibration": sc7,
        "implementation_bindings": implementation_bindings,
        "technical_build_status": "PASS",
        "promotion_authority": "CURRENT_USER_EXPLICIT_ONLY",
    }
    manifest["manifest_id"] = sha256_bytes(compact_json(manifest))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="clone-kani skill root (default: script parent)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="manifest path (default: ROOT/references/v10_runtime/kani_v10_manifest.json)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare the on-disk manifest with current artifacts without writing",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    output = args.output or (root / "references" / "v10_runtime" / "kani_v10_manifest.json")
    if not output.is_absolute():
        output = root / output
    try:
        manifest = build_manifest(root)
        stable_manifest = build_manifest(root)
        if stable_manifest != manifest:
            raise ManifestError("artifact tree changed during manifest build")
        if args.check:
            if not output.is_file():
                result = {"status": "FAIL", "errors": ["manifest file missing"], "path": str(output)}
                print(json.dumps(result, ensure_ascii=False, sort_keys=True))
                return 1
            current = output.read_bytes()
            expected = pretty_json(manifest)
            if current != expected:
                result = {
                    "status": "FAIL",
                    "errors": ["manifest differs from current deterministic artifact snapshot"],
                    "path": str(output),
                    "expected_manifest_id": manifest["manifest_id"],
                }
                print(json.dumps(result, ensure_ascii=False, sort_keys=True))
                return 1
            result = {
                "status": "PASS",
                "path": str(output),
                "manifest_id": manifest["manifest_id"],
                "bundle_completeness": manifest["bundle_completeness"],
                "pending_components": manifest["pending_components"],
            }
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
            return 0

        output.parent.mkdir(parents=True, exist_ok=True)
        temporary_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=output.parent,
                prefix=f".{output.name}.",
                suffix=".tmp",
                delete=False,
            ) as stream:
                temporary_name = stream.name
                stream.write(pretty_json(manifest))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_name, output)
            temporary_name = None
        finally:
            if temporary_name is not None:
                Path(temporary_name).unlink(missing_ok=True)
        result = {
            "status": "PASS",
            "path": str(output),
            "manifest_id": manifest["manifest_id"],
            "bundle_completeness": manifest["bundle_completeness"],
            "pending_components": manifest["pending_components"],
        }
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (ManifestError, OSError) as error:
        print(json.dumps({"status": "FAIL", "errors": [str(error)]}, ensure_ascii=False, sort_keys=True))
        return 1


if __name__ == "__main__":
    sys.exit(main())

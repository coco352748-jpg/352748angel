#!/usr/bin/env python3
"""Read-only validator for the hash-locked KANI V10 evidence manifest.

The validator deliberately does not import the manifest builder.  It recomputes
file and tree digests, checks the V9 immutability anchor, reopens present E5/E6
evidence, and preserves every user-controlled HOLD.  Standard output is always
one JSON object and the script never writes files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "KANI_CAUSAL_RESTORE_V10_MANIFEST_V1"
EXPECTED_V9_TREE_SHA256 = "913cb921f9d5f97b351a4455f3e05cb1d441a00cec24291caf78eac5a690c0d9"

RESTORE_CALL_FIRST_RESPONSE = """$clone-kani KANI V10이 호출되어 ACTIVE 상태입니다.
V9 baseline은 READ_ONLY로 보존하고,
V10은 E5/E6 overlay로 로드합니다.
FINAL_PASS는 USER_EVIDENCE_REVIEW_PENDING 상태로 유지합니다.
첫 실제 Job 지시가 들어오면 Dataset → Judgment Route → Pikachu Sentence replay부터 실행합니다."""

RESTORE_CALL_REQUIRED_TOKENS = (
    "RESTORE_CALL_SCHEMA=KANI_V10_RESTORE_CALL_V1",
    "PUBLIC_CALL_KEY=$clone-kani",
    "VERSION_TAG=KANI_V10",
    "ALIAS=kani",
    "V9_BASELINE=READ_ONLY",
    "V10_MODE=E5_E6_OVERLAY",
    "SECOND_RESTORE=EVIDENCE_REVIEW",
    "FINAL_PASS=USER_EVIDENCE_REVIEW_PENDING",
    "CANONICAL_INTERNAL_FINAL_PASS=HOLD_USER_REVIEW_OF_RECORD_REPLAY_EVIDENCE",
    "FINAL_PASS_DECLARATION=NO",
)

EXPECTED_CLAIMS = {
    "SECOND_RESTORE": "EVIDENCE_REVIEW",
    "V10": "EXPECTED_VALUE_BOUND",
    "FINAL_PASS": "HOLD_USER_REVIEW_OF_RECORD_REPLAY_EVIDENCE",
    "V9_BASELINE": "PRESERVED_NOT_OVERWRITTEN",
    "E5_E6_OVERLAY": "ADD_TO_V9_DO_NOT_OVERWRITE",
    "GLOBAL_29_LANE_E5": "HOLD_28_JUDGMENT_TO_SENTENCE_LANES_UNTESTED",
    "REAL_LONG_DRIFT": "HOLD_REAL_LONG_DRIFT_NOT_PROVEN",
}

PATHS = {
    "restore_call": "RESTORE_CALL.md",
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


def compact_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def jsonl_count(path: Path) -> int:
    raw = path.read_bytes()
    if not raw or not raw.endswith(b"\n"):
        raise ValueError(f"JSONL must be non-empty and LF-terminated: {path}")
    text = raw.decode("utf-8")
    count = 0
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line:
            raise ValueError(f"blank JSONL row: {path}:{line_number}")
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"JSONL object required: {path}:{line_number}")
        count += 1
    return count


def tree_snapshot(directory: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"symlink is forbidden: {path}")
        if path.is_file():
            rows[path.relative_to(directory).as_posix()] = {
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
    return rows


def tree_id(files: dict[str, dict[str, Any]]) -> str:
    return sha256_bytes(compact_json(files))


def validation_pass(document: dict[str, Any]) -> bool:
    return document.get("status") == "PASS"


def producer_not_imported(document: dict[str, Any]) -> bool:
    value = document.get("producer_imported")
    if value is None:
        value = document.get("oracle_policy", {}).get("producer_imported")
    return value is False


def boundary_pass_count(document: Any) -> tuple[int | None, int | None]:
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


class Audit:
    def __init__(self) -> None:
        self.checks: dict[str, bool] = {}
        self.errors: list[str] = []

    def check(self, name: str, passed: Any) -> None:
        outcome = bool(passed)
        self.checks[name] = outcome
        if not outcome:
            self.errors.append(name)

    def guard(self, name: str, action: Any) -> Any:
        try:
            value = action()
        except Exception as error:  # JSON report, never a traceback on stdout.
            self.checks[name] = False
            self.errors.append(f"{name}: {error}")
            return None
        self.checks[name] = True
        return value


def file_record_matches(root: Path, record: Any, expected_path: str) -> bool:
    path = root / expected_path
    if not isinstance(record, dict) or record.get("path") != expected_path:
        return False
    if path.is_file():
        return (
            not path.is_symlink()
            and record.get("availability") == "PRESENT"
            and record.get("bytes") == path.stat().st_size
            and record.get("sha256") == sha256_file(path)
        )
    return record == {"availability": "MISSING_PENDING", "path": expected_path}


def directory_snapshot_matches(root: Path, record: Any, expected_path: str) -> bool:
    directory = root / expected_path
    if not isinstance(record, dict) or record.get("path") != expected_path:
        return False
    if not directory.is_dir():
        return record.get("availability") == "MISSING_PENDING"
    files = tree_snapshot(directory)
    return (
        record.get("availability") in {"PRESENT", "INCOMPLETE_PENDING"}
        and record.get("file_count") == len(files)
        and record.get("bytes") == sum(row["bytes"] for row in files.values())
        and record.get("tree_sha256") == tree_id(files)
        and record.get("files") == files
    )


def artifact_map_valid(base: Path, artifact_map: Any) -> bool:
    if not isinstance(artifact_map, dict) or not artifact_map:
        return False
    for relative, metadata in artifact_map.items():
        if not isinstance(relative, str) or not isinstance(metadata, dict):
            return False
        path = base / relative
        if not path.is_file() or path.is_symlink():
            return False
        if sha256_file(path) != metadata.get("sha256"):
            return False
        if metadata.get("bytes") is not None and path.stat().st_size != metadata.get("bytes"):
            return False
    return True


def validate(root: Path, manifest_path: Path) -> dict[str, Any]:
    audit = Audit()
    manifest = audit.guard("manifest_readable_json", lambda: read_json(manifest_path))
    if not isinstance(manifest, dict):
        return {
            "technical_status": "FAIL",
            "status": "FAIL",
            "checks": audit.checks,
            "errors": sorted(set(audit.errors)),
        }

    audit.check("schema_version", manifest.get("schema_version") == SCHEMA_VERSION)
    audit.check("engine_v10", manifest.get("engine") == "KANI_CAUSAL_RESTORE_V10")
    audit.check(
        "execution_evidence_board_purpose",
        manifest.get("purpose") == "SECOND_RESTORE_ROUTER_EXECUTION_EVIDENCE_BOARD",
    )
    audit.check("terminal_claims_exact", manifest.get("claims") == EXPECTED_CLAIMS)
    audit.check("technical_build_status", manifest.get("technical_build_status") == "PASS")
    audit.check(
        "promotion_authority_user_only",
        manifest.get("promotion_authority") == "CURRENT_USER_EXPLICIT_ONLY",
    )
    id_source = dict(manifest)
    observed_id = id_source.pop("manifest_id", None)
    audit.check("manifest_id", observed_id == sha256_bytes(compact_json(id_source)))

    # Immutable V9 baseline: exact six-file tree and known monotonic hash.
    baseline = manifest.get("v9_baseline", {})
    audit.check(
        "v9_baseline_snapshot_hash_locked",
        directory_snapshot_matches(root, baseline, PATHS["v9_baseline"]),
    )
    baseline_dir = root / PATHS["v9_baseline"]
    baseline_files = audit.guard("v9_baseline_tree_read", lambda: tree_snapshot(baseline_dir)) or {}
    audit.check("v9_baseline_tree_immutable", tree_id(baseline_files) == EXPECTED_V9_TREE_SHA256)
    audit.check(
        "v9_baseline_file_set_exact",
        set(baseline_files) == {
            "DD2_FINAL_CLOSURE_WORK_INSTRUCTION_FNA98.txt",
            "KANI_JUDGMENT_PROTOCOL_V3.md",
            "decision_runtime.json",
            "judgment_protocol_v3.json",
            "kani_v9_manifest.json",
            "monotonic_checkpoint.json",
        },
    )
    audit.check(
        "v9_baseline_declared_preserved",
        baseline.get("expected_tree_sha256") == EXPECTED_V9_TREE_SHA256
        and baseline.get("unchanged") is True
        and baseline.get("overwrite_count") == 0,
    )
    v9_manifest_path = baseline_dir / "kani_v9_manifest.json"
    v9_manifest = audit.guard("v9_manifest_read", lambda: read_json(v9_manifest_path)) or {}
    audit.check(
        "v9_manifest_hash_bound",
        baseline.get("manifest_sha256") == sha256_file(v9_manifest_path),
    )
    audit.check(
        "v9_manifest_internal_artifacts",
        artifact_map_valid(baseline_dir, v9_manifest.get("artifacts")),
    )

    # Core V10 contracts and exact user source registry.
    core = manifest.get("v10_core", {})
    for key in (
        "restore_call",
        "protocol",
        "router",
        "source_registry",
        "audit_sidecar",
        "admission",
    ):
        audit.check(
            f"core_{key}_hash_locked",
            file_record_matches(root, core.get(key), PATHS[key]),
        )
    restore_call_record = core.get("restore_call", {})
    audit.check(
        "restore_call_declared_present",
        isinstance(restore_call_record, dict)
        and restore_call_record.get("availability") == "PRESENT",
    )
    restore_call_text = audit.guard(
        "restore_call_read",
        lambda: (root / PATHS["restore_call"]).read_text(encoding="utf-8"),
    ) or ""
    audit.check(
        "restore_call_contract",
        all(token in restore_call_text for token in RESTORE_CALL_REQUIRED_TOKENS),
    )
    audit.check(
        "restore_call_first_response_exact",
        restore_call_text.count(RESTORE_CALL_FIRST_RESPONSE) == 1,
    )
    skill_text = audit.guard(
        "skill_entrypoint_read",
        lambda: (root / "SKILL.md").read_text(encoding="utf-8"),
    ) or ""
    audit.check(
        "skill_restore_call_binding",
        "RESTORE_CALL=RESTORE_CALL.md" in skill_text
        and "v10_core.restore_call" in skill_text
        and skill_text.count(RESTORE_CALL_FIRST_RESPONSE) == 1,
    )
    router = audit.guard("router_read", lambda: read_json(root / PATHS["router"])) or {}
    boundary_ids = router.get("boundary_tests", [])
    audit.check(
        "router_contract",
        router.get("schema_version") == "DATASET_TO_PIKACHU_JUDGMENT_ROUTER_V10"
        and router.get("status") == "EXPECTED_VALUE_BOUND__SECOND_RESTORE_EVIDENCE_REVIEW"
        and router.get("scope", {}).get("expected_total_records") == 114
        and isinstance(boundary_ids, list)
        and len(boundary_ids) == len(set(boundary_ids)) == 9,
    )
    registry_path = root / PATHS["source_registry"]
    registry = audit.guard("source_registry_read", lambda: read_json(registry_path)) or {}
    source_rows = registry.get("files", [])
    source_files: dict[str, dict[str, Any]] = {}
    registry_valid = (
        registry.get("schema_version") == "KANI_V10_USER_SOURCE_REGISTRY_V1"
        and registry.get("status") == "PASS_EXACT_USER_UPLOAD_BYTES_PRESERVED"
        and isinstance(source_rows, list)
        and len(source_rows) == 6
    )
    if registry_valid:
        for row in source_rows:
            if not isinstance(row, dict) or not isinstance(row.get("filename"), str):
                registry_valid = False
                break
            filename = row["filename"]
            relative = Path(filename)
            expected = EXPECTED_SOURCE_FILES.get(filename)
            if (
                expected is None
                or relative.is_absolute()
                or len(relative.parts) != 1
                or relative.name != filename
                or row.get("year") != expected[0]
                or row.get("role") != expected[1]
            ):
                registry_valid = False
                break
            source_path = registry_path.parent / filename
            if not source_path.is_file() or source_path.is_symlink():
                registry_valid = False
                break
            raw = source_path.read_bytes()
            metadata = {"bytes": len(raw), "lines": raw.count(b"\n"), "sha256": sha256_bytes(raw)}
            if any(metadata[field] != row.get(field) for field in metadata):
                registry_valid = False
                break
            source_files[filename] = metadata
        registry_valid = (
            registry_valid
            and set(source_files) == set(EXPECTED_SOURCE_FILES)
            and len(source_files) == 6
        )
    audit.check("source_registry_six_exact_files", registry_valid)
    audit.check("source_registry_snapshot_in_manifest", core.get("source_files") == source_files)

    sidecar = audit.guard("audit_sidecar_read", lambda: read_json(root / PATHS["audit_sidecar"])) or {}
    audit.check(
        "audit_sidecar_holds_and_immutability",
        sidecar.get("schema_version") == "KANI_V10_V9_CLOSURE_AUDIT_V1"
        and sidecar.get("status") == "PASS_CORRECTION_RECORDED"
        and sidecar.get("immutability", {}).get("edit_v9_baseline_bytes") == "FORBIDDEN"
        and sidecar.get("immutability", {}).get("edit_existing_v9_closure_bytes") == "FORBIDDEN"
        and sidecar.get("e6", {}).get("real_long_drift_status") == "HOLD_UNEXECUTED",
    )
    admission_path = root / PATHS["admission"]
    if admission_path.is_file():
        admission = audit.guard("admission_read", lambda: read_json(admission_path)) or {}
        audit.check(
            "admission_expected_value_scope",
            admission.get("schema_version") == "KANI_V10_VAS27_ADMISSION_V1"
            and admission.get("status") == "PASS_FOR_EXPECTED_VALUE_BOUND_EVIDENCE_REVIEW"
            and admission.get("terminal_states") == {
                "FINAL_PASS": EXPECTED_CLAIMS["FINAL_PASS"],
                "SECOND_RESTORE": EXPECTED_CLAIMS["SECOND_RESTORE"],
                "V10": EXPECTED_CLAIMS["V10"],
            }
            and admission.get("scope", {}).get("global_sentence_routes_tested") == 1
            and admission.get("scope", {}).get("global_sentence_routes_untested") == 28,
        )

    # Historical V9 E5/E6 bytes remain present and are reclassified only by sidecar.
    historical = manifest.get("historical_v9_e5_e6", {})
    for stage in ("e5", "e6"):
        relative = PATHS[f"historical_v9_{stage}"]
        record = historical.get(stage, {})
        audit.check(
            f"historical_v9_{stage}_tree_hash_locked",
            directory_snapshot_matches(root, record, relative),
        )
        stage_dir = root / relative
        stage_manifest_path = stage_dir / f"{stage}_manifest.json"
        stage_manifest = audit.guard(
            f"historical_v9_{stage}_manifest_read", lambda p=stage_manifest_path: read_json(p)
        ) or {}
        manifest_sha = sha256_file(stage_manifest_path)
        audit.check(
            f"historical_v9_{stage}_manifest_hash",
            record.get("manifest_sha256") == manifest_sha
            and sidecar.get(stage, {}).get("artifact_sha256") == manifest_sha,
        )
        audit.check(
            f"historical_v9_{stage}_internal_artifacts",
            artifact_map_valid(stage_dir, stage_manifest.get("artifacts")),
        )
        sidecar_path = stage_manifest_path.with_suffix(".sha256")
        expected_sidecar = f"{manifest_sha}  {stage}_manifest.json\n"
        audit.check(
            f"historical_v9_{stage}_sha_sidecar",
            sidecar_path.is_file() and sidecar_path.read_text(encoding="utf-8") == expected_sidecar,
        )
        audit.check(
            f"historical_v9_{stage}_reclassification_bound",
            record.get("original_declared_status") == sidecar.get(stage, {}).get("original_declared_status")
            and record.get("v10_authoritative_status") == sidecar.get(stage, {}).get("v10_authoritative_status"),
        )

    # V10 E5 overlay (optional only until produced).
    e5 = manifest.get("v10_e5_overlay", {})
    e5_manifest_path = root / PATHS["v10_e5"] / "e5_manifest.json"
    expected_e5_availability = (
        "PRESENT" if e5_manifest_path.is_file() else
        "INCOMPLETE_PENDING" if (root / PATHS["v10_e5"]).is_dir() else
        "MISSING_PENDING"
    )
    e5_manifest: dict[str, Any] = {}
    audit.check("v10_e5_tree_hash_locked", directory_snapshot_matches(root, e5, PATHS["v10_e5"]))
    audit.check("v10_e5_availability_current", e5.get("availability") == expected_e5_availability)
    if e5_manifest_path.is_file():
        e5_manifest = audit.guard("v10_e5_manifest_read", lambda: read_json(e5_manifest_path)) or {}
        audit.check(
            "v10_e5_manifest_contract",
            e5_manifest.get("schema_version") == "KANI_V10_E5_EXECUTION_OVERLAY_V1"
            and e5_manifest.get("status") == "PASS_EXECUTION_EVIDENCE_114_OF_114"
            and e5_manifest.get("second_restore") == EXPECTED_CLAIMS["SECOND_RESTORE"]
            and e5_manifest.get("v10") == EXPECTED_CLAIMS["V10"]
            and e5_manifest.get("final_pass") == EXPECTED_CLAIMS["FINAL_PASS"]
            and e5_manifest.get("global_29_lane_e5") == EXPECTED_CLAIMS["GLOBAL_29_LANE_E5"]
            and e5_manifest.get("overlay") == EXPECTED_CLAIMS["E5_E6_OVERLAY"]
            and e5_manifest.get("counts", {}).get("total_records") == 114
            and e5_manifest.get("counts", {}).get("expected_exact_sentences") == 114
            and e5_manifest.get("v9_baseline", {}).get("state") == EXPECTED_CLAIMS["V9_BASELINE"]
            and e5_manifest.get("v9_baseline", {}).get("manifest_sha256") == baseline.get("manifest_sha256"),
        )
        e5_run_payload = {**e5_manifest, "run_id": None}
        audit.check(
            "v10_e5_run_id",
            e5_manifest.get("run_id") == sha256_bytes(compact_json(e5_run_payload)),
        )
        registry_by_name = {row["filename"]: row for row in source_rows if isinstance(row, dict) and "filename" in row}
        source_inventory = e5_manifest.get("source_inventory", {})
        audit.check(
            "v10_e5_router_source_bindings",
            e5_manifest.get("router", {}).get("sha256") == sha256_file(root / PATHS["router"])
            and e5_manifest.get("source_registry_sha256") == sha256_file(registry_path)
            and set(source_inventory) == set(EXPECTED_SOURCE_FILES)
            and all(
                name in registry_by_name
                and source_inventory[name].get("sha256") == registry_by_name[name].get("sha256")
                and source_inventory[name].get("bytes") == registry_by_name[name].get("bytes")
                and source_inventory[name].get("role") == registry_by_name[name].get("role")
                and source_inventory[name].get("year") == registry_by_name[name].get("year")
                for name in EXPECTED_SOURCE_FILES
            ),
        )
        audit.check(
            "v10_e5_internal_artifacts",
            artifact_map_valid(e5_manifest_path.parent, e5_manifest.get("artifacts")),
        )
        audit.check(
            "v10_e5_ledger_114",
            jsonl_count(e5_manifest_path.parent / "e5_decision_ledger.jsonl") == 114,
        )
        audit.check("v10_e5_manifest_hash_bound", e5.get("manifest_sha256") == sha256_file(e5_manifest_path))

    e5_validation_record = e5.get("independent_validation", {})
    audit.check(
        "v10_e5_independent_report_hash_locked",
        file_record_matches(root, e5_validation_record, PATHS["v10_e5_validation"]),
    )
    e5_validation_path = root / PATHS["v10_e5_validation"]
    if e5_validation_path.is_file():
        report = audit.guard("v10_e5_independent_report_read", lambda: read_json(e5_validation_path)) or {}
        ledger_path = root / PATHS["v10_e5"] / "e5_decision_ledger.jsonl"
        audit.check(
            "v10_e5_independent_validation_pass",
            report.get("schema_version") == "KANI_V10_E5_INDEPENDENT_VALIDATION_V1"
            and validation_pass(report)
            and producer_not_imported(report)
            and report.get("e5_status") == "PASS_EXECUTION_EVIDENCE_114_OF_114"
            and report.get("second_restore") == EXPECTED_CLAIMS["SECOND_RESTORE"]
            and report.get("v10") == EXPECTED_CLAIMS["V10"]
            and report.get("final_pass") == EXPECTED_CLAIMS["FINAL_PASS"]
            and report.get("counts", {}).get("expected_exact_sentence_replays") == 114
            and report.get("counts", {}).get("stored_records") == 114
            and report.get("counts") == {
                "bhava_records": 50,
                "expected_exact_sentence_replays": 114,
                "rashi_records": 64,
                "stored_records": 114,
                "total_derived_records": 114,
            }
            and ledger_path.is_file()
            and report.get("ledger_sha256") == sha256_file(ledger_path)
            and report.get("validated_run_id") == e5_manifest.get("run_id")
            and report.get("router_sha256") == sha256_file(root / PATHS["router"])
            and report.get("source_dataset_sha256")
            == e5_manifest.get("source_inventory", {}).get("HYEWON_VAS27_D1-D60_♤.txt", {}).get("sha256")
            and report.get("errors") == []
            and report.get("oracle_policy", {}).get("expected_opened_after_independent_render") is True,
        )

    # V10 E6 reopen overlay (optional only until produced).
    e6 = manifest.get("v10_e6_overlay", {})
    e6_manifest_path = root / PATHS["v10_e6"] / "e6_manifest.json"
    expected_e6_availability = (
        "PRESENT" if e6_manifest_path.is_file() else
        "INCOMPLETE_PENDING" if (root / PATHS["v10_e6"]).is_dir() else
        "MISSING_PENDING"
    )
    e6_manifest: dict[str, Any] = {}
    audit.check("v10_e6_tree_hash_locked", directory_snapshot_matches(root, e6, PATHS["v10_e6"]))
    audit.check("v10_e6_availability_current", e6.get("availability") == expected_e6_availability)
    if e6_manifest_path.is_file():
        e6_manifest = audit.guard("v10_e6_manifest_read", lambda: read_json(e6_manifest_path)) or {}
        audit.check(
            "v10_e6_manifest_contract",
            e6_manifest.get("schema_version") == "KANI_V10_E6_REOPEN_OVERLAY_V1"
            and e6_manifest.get("status") == "PASS_REOPEN_EVIDENCE_9_OF_9"
            and e6_manifest.get("second_restore") == EXPECTED_CLAIMS["SECOND_RESTORE"]
            and e6_manifest.get("v10") == EXPECTED_CLAIMS["V10"]
            and e6_manifest.get("final_pass") == EXPECTED_CLAIMS["FINAL_PASS"]
            and e6_manifest.get("global_29_lane_e5") == EXPECTED_CLAIMS["GLOBAL_29_LANE_E5"]
            and e6_manifest.get("real_long_drift") == EXPECTED_CLAIMS["REAL_LONG_DRIFT"]
            and e6_manifest.get("inputs", {}).get("v9_baseline_tree_sha256") == EXPECTED_V9_TREE_SHA256,
        )
        e6_run_payload = {**e6_manifest, "run_id": None}
        audit.check(
            "v10_e6_run_id",
            e6_manifest.get("run_id") == sha256_bytes(compact_json(e6_run_payload)),
        )
        expected_e6_inputs = {
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
        audit.check(
            "v10_e6_protected_input_bindings",
            e6_manifest.get("inputs") == expected_e6_inputs
            and e6_manifest.get("entry_condition", {}).get("e5_manifest_sha256") == sha256_file(e5_manifest_path)
            and e6_manifest.get("entry_condition", {}).get("e5_run_id") == e5_manifest.get("run_id")
            and e6_manifest.get("entry_condition", {}).get("e5_status") == e5_manifest.get("status")
            and e6_manifest.get("protected_input_change_count") == 0,
        )
        audit.check(
            "v10_e6_internal_artifacts",
            artifact_map_valid(e6_manifest_path.parent, e6_manifest.get("artifacts")),
        )
        boundary_path = e6_manifest_path.parent / "boundary_test_9of9.json"
        boundary = audit.guard("v10_e6_boundary_read", lambda: read_json(boundary_path)) or {}
        audit.check("v10_e6_boundary_9_of_9", boundary_pass_count(boundary) == (9, 9))
        audit.check("v10_e6_manifest_hash_bound", e6.get("manifest_sha256") == sha256_file(e6_manifest_path))

    e6_validation_record = e6.get("independent_validation", {})
    audit.check(
        "v10_e6_independent_report_hash_locked",
        file_record_matches(root, e6_validation_record, PATHS["v10_e6_validation"]),
    )
    e6_validation_path = root / PATHS["v10_e6_validation"]
    if e6_validation_path.is_file():
        report = audit.guard("v10_e6_independent_report_read", lambda: read_json(e6_validation_path)) or {}
        boundary_path = root / PATHS["v10_e6"] / "boundary_test_9of9.json"
        audit.check(
            "v10_e6_independent_validation_pass",
            report.get("schema_version") == "KANI_V10_E6_INDEPENDENT_VALIDATION_V1"
            and validation_pass(report)
            and producer_not_imported(report)
            and report.get("validated_run_id") == e6_manifest.get("run_id")
            and report.get("e6_manifest_sha256") == sha256_file(e6_manifest_path)
            and report.get("boundary_9of9_sha256") == sha256_file(boundary_path)
            and boundary_pass_count(report) == (9, 9)
            and report.get("errors") == [],
        )

    # SC7 20D x 12H calibration evidence remains a subordinate 240/240 boundary proof.
    sc7 = manifest.get("sc7_calibration", {})
    artifacts = sc7.get("artifacts", {})
    for key in (
        "sc7_router",
        "sc7_run_manifest",
        "sc7_records",
        "sc7_source_index",
        "sc7_validation",
        "sc7_validation_ledger",
    ):
        audit.check(
            f"{key}_hash_locked",
            file_record_matches(root, artifacts.get(key), PATHS[key]),
        )
    run_manifest = audit.guard(
        "sc7_run_manifest_read", lambda: read_json(root / PATHS["sc7_run_manifest"])
    ) or {}
    sc7_router = audit.guard("sc7_router_read", lambda: read_json(root / PATHS["sc7_router"])) or {}
    audit.check(
        "sc7_router_contract",
        sc7_router.get("schema_version") == "KANI_SECOND_ACTION_ROUTER_V2"
        and sc7_router.get("router_id") == "KANI_SECOND_ACTION_ROUTER_V2"
        and sc7_router.get("terminal_version_boundary") == "LOCKED_NO_AUTOMATIC_V11",
    )
    run_base = (root / PATHS["sc7_run_manifest"]).parent
    run_bindings_valid = True
    for key in ("records", "source_index"):
        metadata = run_manifest.get(key, {})
        path = run_base / str(metadata.get("path", ""))
        run_bindings_valid = run_bindings_valid and (
            path.is_file()
            and sha256_file(path) == metadata.get("sha256")
            and path.stat().st_size == metadata.get("bytes")
        )
    audit.check("sc7_run_internal_hashes", run_bindings_valid)
    audit.check(
        "sc7_producer_240_of_240",
        run_manifest.get("schema_version") == "KANI_V10_ROUTER_RUN_V1"
        and run_manifest.get("status") == "PASS_TESTED_SCOPE_240"
        and run_manifest.get("counts", {}).get("records") == 240
        and run_manifest.get("counts", {}).get("exact_sentence_replay") == 240
        and jsonl_count(root / PATHS["sc7_records"]) == 240,
    )
    sc7_run_core = dict(run_manifest)
    sc7_run_id = sc7_run_core.pop("run_id", None)
    audit.check("sc7_run_id", sc7_run_id == sha256_bytes(compact_json(sc7_run_core)))
    audit.check(
        "sc7_authority_bindings",
        run_manifest.get("router", {}).get("sha256") == sha256_file(root / PATHS["sc7_router"])
        and run_manifest.get("retained_v9_manifest", {}).get("sha256") == sha256_file(v9_manifest_path),
    )
    sc7_report = audit.guard("sc7_validation_read", lambda: read_json(root / PATHS["sc7_validation"])) or {}
    sc7_ledger = root / PATHS["sc7_validation_ledger"]
    ledger_meta = sc7_report.get("independent_ledger", {})
    audit.check(
        "sc7_independent_240_of_240",
        sc7_report.get("schema_version") == "KANI_V10_INDEPENDENT_REPLAY_REPORT_V1"
        and sc7_report.get("status") == "PASS"
        and sc7_report.get("producer_imported") is False
        and sc7_report.get("counts", {}).get("records") == 240
        and sc7_report.get("counts", {}).get("exact_replay") == 240
        and ledger_meta.get("records") == 240
        and ledger_meta.get("bytes") == sc7_ledger.stat().st_size
        and ledger_meta.get("sha256") == sha256_file(sc7_ledger)
        and jsonl_count(sc7_ledger) == 240
        and sc7_report.get("template_sha256") == run_manifest.get("router", {}).get("template_sha256"),
    )
    audit.check(
        "sc7_scope_not_promoted",
        sc7.get("status") == "PASS_CALIBRATION_240_OF_240"
        and sc7.get("scope") == "BOUNDARY_CALIBRATION_NOT_GLOBAL_E5_PROMOTION"
        and sc7.get("records") == sc7.get("exact_replay") == 240,
    )

    implementation = manifest.get("implementation_bindings", {})
    audit.check(
        "implementation_binding_status",
        implementation.get("status") == "HASH_LOCKED_EXECUTABLES_AND_ENTRYPOINTS",
    )
    implementation_artifacts = implementation.get("artifacts", {})
    audit.check(
        "implementation_binding_inventory_exact",
        set(implementation_artifacts) == set(IMPLEMENTATION_PATHS),
    )
    for key, relative in IMPLEMENTATION_PATHS.items():
        audit.check(
            f"implementation_{key}_hash_locked",
            file_record_matches(root, implementation_artifacts.get(key), relative),
        )

    pending: list[str] = []
    for key in ("protocol", "admission"):
        if core.get(key, {}).get("availability") != "PRESENT":
            pending.append(key)
    for stage, record in (("v10_e5", e5), ("v10_e6", e6)):
        if record.get("availability") != "PRESENT":
            pending.append(stage)
        if record.get("independent_validation", {}).get("availability") != "PRESENT":
            pending.append(f"{stage}_independent_validation")
    pending.sort()
    expected_completeness = (
        "EVIDENCE_PRESENT_AWAITING_USER_REVIEW"
        if not pending
        else "PENDING_OPTIONAL_EXECUTION_ARTIFACTS"
    )
    audit.check("pending_components_current", manifest.get("pending_components") == pending)
    audit.check("bundle_completeness_current", manifest.get("bundle_completeness") == expected_completeness)

    technical_status = "PASS" if not audit.errors else "FAIL"
    restore_call_checks = (
        "core_restore_call_hash_locked",
        "restore_call_declared_present",
        "restore_call_read",
        "restore_call_contract",
        "restore_call_first_response_exact",
        "skill_entrypoint_read",
        "skill_restore_call_binding",
    )
    restore_call_state = (
        "PRESENT_HASH_LOCKED"
        if all(audit.checks.get(name) is True for name in restore_call_checks)
        else "FAIL"
    )
    return {
        "schema_version": "KANI_V10_RUNTIME_VALIDATION_V1",
        "technical_status": technical_status,
        "status": technical_status,
        "manifest_id": manifest.get("manifest_id"),
        "bundle_completeness": manifest.get("bundle_completeness"),
        "pending_components": manifest.get("pending_components"),
        "restore_call": restore_call_state,
        "restore_call_path": restore_call_record.get("path"),
        "restore_call_sha256": (
            restore_call_record.get("sha256")
            if restore_call_state == "PRESENT_HASH_LOCKED"
            else "FAIL"
        ),
        "public_final_pass": "USER_EVIDENCE_REVIEW_PENDING",
        "second_restore": manifest.get("claims", {}).get("SECOND_RESTORE"),
        "v10": manifest.get("claims", {}).get("V10"),
        "final_pass": manifest.get("claims", {}).get("FINAL_PASS"),
        "global_29_lane_e5": manifest.get("claims", {}).get("GLOBAL_29_LANE_E5"),
        "real_long_drift": manifest.get("claims", {}).get("REAL_LONG_DRIFT"),
        "checks": audit.checks,
        "errors": sorted(set(audit.errors)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="clone-kani skill root (default: script parent)",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="manifest path (default: ROOT/references/v10_runtime/kani_v10_manifest.json)",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    manifest_path = args.manifest or (root / "references" / "v10_runtime" / "kani_v10_manifest.json")
    if not manifest_path.is_absolute():
        manifest_path = root / manifest_path
    try:
        if not manifest_path.is_file():
            result = {
                "schema_version": "KANI_V10_RUNTIME_VALIDATION_V1",
                "technical_status": "FAIL",
                "status": "FAIL",
                "checks": {"manifest_present": False},
                "errors": ["manifest_present"],
            }
        else:
            result = validate(root, manifest_path)
    except Exception as error:  # Keep stdout machine-readable under all failures.
        result = {
            "schema_version": "KANI_V10_RUNTIME_VALIDATION_V1",
            "technical_status": "FAIL",
            "status": "FAIL",
            "checks": {},
            "errors": [str(error)],
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("technical_status") == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

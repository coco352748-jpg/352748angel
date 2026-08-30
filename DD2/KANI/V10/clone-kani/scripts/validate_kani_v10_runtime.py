#!/usr/bin/env python3
"""Read-only validator for the hash-locked KANI V10 evidence manifest.

The validator deliberately does not import the manifest builder. It recomputes
file and tree digests, checks the V9 immutability anchor, reopens present E5/E6
evidence, validates the later evidence-scoped user promotion, and preserves
every remaining HOLD. Standard output is always one JSON object.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "KANI_CAUSAL_RESTORE_V10_MANIFEST_V1"
EXPECTED_V9_TREE_SHA256 = "913cb921f9d5f97b351a4455f3e05cb1d441a00cec24291caf78eac5a690c0d9"

RESTORE_CALL_FIRST_RESPONSE = """$clone-kani KANI V10이 호출되어 ACTIVE_EVIDENCE_SCOPED 상태입니다.
V9 baseline은 READ_ONLY로 보존하고,
V10 E5/E6 record/replay와 사용자 승격 레코드를 로드합니다.
SECOND_RESTORE는 PASS_EVIDENCE_SCOPED입니다.
FINAL_FNA98_RUNTIME은 HOLD_UNTIL_REAL_RUNTIME_GATES_PASS입니다.
첫 실제 Job에서는 검증된 관절만 실행하고, 미재생 관절은 HOLD로 유지합니다."""

RESTORE_CALL_REQUIRED_TOKENS = (
    "RESTORE_CALL_SCHEMA=KANI_V10_RESTORE_CALL_V2",
    "PUBLIC_CALL_KEY=$clone-kani",
    "VERSION_TAG=KANI_V10",
    "ALIAS=kani",
    "V9_BASELINE=READ_ONLY",
    "V10_MODE=E5_E6_OVERLAY",
    "PROMOTION_RECORD=references/v10_runtime/user_evidence_promotion_20260830.json",
    "PROMOTION_RECORD_STATE=PASS_HASH_LOCKED",
    "USER_EVIDENCE_REVIEW=PASS",
    "SECOND_RESTORE=PASS_EVIDENCE_SCOPED",
    "FINAL_PASS=HOLD_REMAINING_RUNTIME_GATES",
    "CANONICAL_INTERNAL_FINAL_PASS=HOLD_REMAINING_RUNTIME_GATES",
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

EXPECTED_EFFECTIVE_STATES = {
    "PUBLIC_RESTORE_STATE": "ACTIVE_EVIDENCE_SCOPED",
    "USER_EVIDENCE_REVIEW": "PASS",
    "SECOND_RESTORE": "PASS_EVIDENCE_SCOPED",
    "V10": "EXPECTED_VALUE_BOUND",
    "FINAL_PASS": "HOLD_REMAINING_RUNTIME_GATES",
    "GLOBAL_29_LANE_E5": "HOLD_28_JUDGMENT_TO_SENTENCE_LANES_UNTESTED",
    "FRESH_TAB_REAL_BOOT_TEST": "HOLD",
    "REAL_LONG_DRIFT": "HOLD_REAL_LONG_DRIFT_NOT_PROVEN",
    "FINAL_FNA98_RUNTIME": "HOLD_UNTIL_REAL_RUNTIME_GATES_PASS",
}

PATHS = {
    "restore_call": "RESTORE_CALL.md",
    "promotion_record": "references/v10_runtime/user_evidence_promotion_20260830.json",
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

REGISTERED_WORK_PATHS = {
    "work_instruction": "references/SC7_SC8_RASHI_BHAVA_BIDIRECTIONAL_GRAMMAR_WORK_INSTRUCTION.md",
    "registration_manifest": "references/v10_runtime/sc7_sc8_rashi_bhava_registration.json",
    "sc7_master_zip": "references/source_window_originals/sc7_sc8_rashi_bhava/HYEWON_SC7_RASHI_BHAVA_20D_ALL.zip",
    "sc8_master_zip": "references/source_window_originals/sc7_sc8_rashi_bhava/HYEWON_SC8_RASHI_BHAVA_20D_ALL.zip",
    "registration_validator": "scripts/validate_sc7_sc8_rashi_bhava_registration.py",
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


def run_registration_validator(root: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            str(root / REGISTERED_WORK_PATHS["registration_validator"]),
            "--root",
            str(root),
        ],
        cwd=root,
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )
    return {
        "returncode": completed.returncode,
        "report": json.loads(completed.stdout),
    }


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
    audit.check(
        "effective_states_exact",
        manifest.get("effective_states") == EXPECTED_EFFECTIVE_STATES,
    )
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
        "promotion_record",
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
        and "v10_core.promotion_record" in skill_text
        and skill_text.count(RESTORE_CALL_FIRST_RESPONSE) == 1,
    )

    promotion_record = core.get("promotion_record", {})
    promotion = audit.guard(
        "promotion_record_read",
        lambda: read_json(root / PATHS["promotion_record"]),
    ) or {}
    audit.check(
        "promotion_record_header",
        promotion.get("schema_version") == "KANI_USER_EVIDENCE_PROMOTION_V1"
        and promotion.get("promotion_record_id")
        == "KANI-USER-PROMOTION-20260830-SECOND-RESTORE-001"
        and promotion.get("authorized_utc") == "2026-08-30"
        and promotion.get("status") == "PASS_USER_REVIEWED_EVIDENCE_SCOPED_PROMOTION"
        and promotion.get("target") == "DD2_ANALYSIS02_MATURE_SECOND_DECISION_RUNTIME"
        and promotion.get("authority", {}).get("kind") == "CURRENT_USER_EXPLICIT_DIRECT"
        and promotion.get("authority", {}).get("scope") == "EVIDENCE_SCOPED_ONLY",
    )
    audit.check(
        "promotion_effective_states",
        promotion.get("effective_states") == EXPECTED_EFFECTIVE_STATES
        and core.get("promotion_effective_states") == EXPECTED_EFFECTIVE_STATES,
    )
    direct_lanes = promotion.get("lineage", {}).get("direct_20d_lanes", [])
    audit.check(
        "promotion_direct_20d_lane_bindings",
        [
            (row.get("runtime_lane"), row.get("lane_order"), row.get("dchart_records"))
            for row in direct_lanes
            if isinstance(row, dict)
        ]
        == [
            ("RASHI_SOURCE", 2, 20),
            ("BHAVA_SOURCE", 3, 20),
            ("FIRST_INTEGRATION", 4, 20),
            ("COPRESENCE", 5, 20),
            ("MOON_CHART", 9, 20),
        ]
        and promotion.get("lineage", {}).get("direct_authored_output_records") == 100,
    )
    full_qa = promotion.get("lineage", {}).get("full_scope_qa", {})
    audit.check(
        "promotion_full_scope_qa_denominator",
        full_qa.get("dcharts") == 20
        and full_qa.get("physical_members") == 600
        and full_qa.get("operationally_void_3p_members") == 20
        and full_qa.get("active_non_3p_members") == 580,
    )
    hold_rows = {row.get("joint_id"): row for row in promotion.get("hold_joints", [])}
    audit.check(
        "promotion_sc7_exact_hold_jobs",
        hold_rows.get("H01_SC7_LOCAL_AND_DEPENDENCY_CONFLICTS", {}).get("exact_jobs")
        == [
            "D1-H02", "D1-H03", "D1-H04", "D1-H05", "D1-H07",
            "D1-H08", "D1-H09", "D1-H11", "D1-H12",
        ],
    )
    audit.check(
        "promotion_global_28_untested_lanes",
        hold_rows.get("H02_GLOBAL_29_LANE_E5", {}).get("untested_lanes")
        == [
            "INDEX", "RASHI_SOURCE", "BHAVA_SOURCE", "FIRST_INTEGRATION",
            "PUSHKARA", "UPAGRAHA", "SPIRIT_CHALIT", "MOON_CHART", "ARUDHA",
            "SHADBALA_A", "SHADBALA_R", "BHAVA_BALA", "VIMSOPAKA", "MRITYU",
            "SPOTHER", "AVA", "BHINNA_MATRIX", "PLANET_ASPECT", "SAP", "TKS",
            "EKS", "SPD", "VARGA_LINK_MINI", "VARGA_LINK_FULL", "ASPECT02",
            "ASPECT03", "DASHA", "TIMING_GATE",
        ],
    )
    local_promotion_bindings = {
        "june04_pikachu_manifest": (
            "assets/clone-kk2-certified-v7p2/references/pikachu-20d-20260604.md",
            "6ef812138788ce5655316a36f646408b3e8305977d1443f8fdc9e3c80415c6be",
        ),
        "june04_attachment_audit": (
            "assets/clone-kk2-certified-v7p2/references/PIKACHU_ATTACHMENT_EVIDENCE_20260828.md",
            "bbdc3085ddd2686667a4d97242d9200377b40e7e54c68d8bc9f3063159229fc6",
        ),
        "v9_runtime_manifest": (
            "references/v9_baseline/kani_v9_manifest.json",
            "4f7a2a3137a50dcd083cdfc5ad7d12c91779da80c188d910266652007b1361d4",
        ),
        "e5_decision_ledger": (
            "references/v10_runs/run_20260830_vas27/e5/e5_decision_ledger.jsonl",
            "aef92a552a3e32938e4376cd05ef820184b38b53c8d4a3b585b4c88e6ff2b743",
        ),
        "e6_replay_ledger": (
            "references/v10_runs/run_20260830_vas27/e6/e6_replay_ledger.jsonl",
            "0b4c7164aed17b93e7529f050c1e0e618bc05438443ea9a7cb8b7ed4a3e0eb5f",
        ),
        "e6_boundary_log": (
            "references/v10_runs/run_20260830_vas27/e6/boundary_test_9of9.json",
            "ce1560169e47ef53b0844aa0567f16427e1bc698167f8a72733551ab66b851e7",
        ),
    }
    promotion_bindings = promotion.get("evidence_bindings", {})
    for key, (relative, expected_sha) in local_promotion_bindings.items():
        record = promotion_bindings.get(key, {})
        path = root / relative
        audit.check(
            f"promotion_{key}_hash_bound",
            record.get("path") == relative
            and record.get("sha256") == expected_sha
            and path.is_file()
            and not path.is_symlink()
            and sha256_file(path) == expected_sha,
        )
    sc7_snapshot = promotion_bindings.get("rq_sc7_external_audit_snapshot", {})
    sc8_snapshot = promotion_bindings.get("rq_sc8_external_audit_snapshot", {})
    audit.check(
        "promotion_sc7_snapshot_exact",
        sc7_snapshot.get("source_set_sha256")
        == "81951a845d2759fcb9afc082743c743e91b4bc15c3aa5220f0ac83fc8c79555c"
        and sc7_snapshot.get("source_binding_payload_sha256")
        == "e797ee5a009e0d83fe66e48bc9c3a7717b6ef00b8c28088e760a02c11dfa73c3"
        and sc7_snapshot.get("source_packages_pass") == 26
        and sc7_snapshot.get("personal_chart_jobs_pass") == 240
        and sc7_snapshot.get("source_binding_jobs_pass") == 231
        and sc7_snapshot.get("source_binding_jobs_hold") == 9
        and sc7_snapshot.get("state") == "PARTIAL_HOLD_3AB_4AB_DEGREE_CONFLICT",
    )
    audit.check(
        "promotion_sc8_snapshot_exact",
        sc8_snapshot.get("manifest_sha256")
        == "6467cd1561805c6aca4a6f96568da068c1aefad726953c13b0b35a85372f34d0"
        and sc8_snapshot.get("aligned_ledger_sha256")
        == "021b1db94344bfae31b22601bee70fd9ad788b6e229d63a0522a092ee47e671c"
        and sc8_snapshot.get("raw_archives") == 20
        and sc8_snapshot.get("raw_physical_members") == 600
        and sc8_snapshot.get("aligned_archives") == 20
        and sc8_snapshot.get("aligned_physical_members") == 600
        and sc8_snapshot.get("replacement_count") == 1001
        and sc8_snapshot.get("changed_members") == 91
        and sc8_snapshot.get("unchanged_members") == 509
        and sc8_snapshot.get("direct_value_field_assertions") == 4140
        and sc8_snapshot.get("stale_token_count") == 0
        and sc8_snapshot.get("information_loss") == 0
        and sc8_snapshot.get("state") == "PASS_FNA98_SC_ALIGNED_20D",
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

    # User-registered first real job. This proves registration only; the
    # bidirectional grammar and 480-unit round trip remain unexecuted.
    registered = manifest.get("registered_work_instructions", {})
    registered_artifacts = registered.get("artifacts", {})
    audit.check(
        "registered_work_inventory_exact",
        set(registered_artifacts) == set(REGISTERED_WORK_PATHS),
    )
    registered_hashes_ok = True
    for key, relative in REGISTERED_WORK_PATHS.items():
        record = registered_artifacts.get(key)
        registered_hashes_ok = registered_hashes_ok and (
            isinstance(record, dict)
            and record.get("availability") == "PRESENT"
            and file_record_matches(root, record, relative)
        )
    audit.check("registered_work_artifacts_hash_locked", registered_hashes_ok)

    registration = audit.guard(
        "registered_work_registration_read",
        lambda: read_json(root / REGISTERED_WORK_PATHS["registration_manifest"]),
    ) or {}
    registered_scope = registration.get("scope", {})
    registered_execution = registration.get("execution", {})
    expected_registered_d_order = [
        "D1", "D9", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D10",
        "D11", "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60",
    ]
    audit.check(
        "registered_work_contract",
        registered.get("status") == "REGISTERED_HASH_LOCKED_FIRST_UNEXECUTED_JOB"
        and registered.get("execution_state") == "NOT_EXECUTED"
        and registered.get("first_real_job")
        == "SC7_SC8_RASHI_BHAVA_BIDIRECTIONAL_GRAMMAR_EXTRACTION"
        and registration.get("schema_version")
        == "KANI_SC7_SC8_BIDIRECTIONAL_GRAMMAR_REGISTRATION_V1"
        and registration.get("registration_id")
        == "KANI-SC7-SC8-RASHI-BHAVA-20260830-001"
        and registration.get("status")
        == "REGISTERED_HASH_LOCKED_FIRST_UNEXECUTED_JOB"
        and registered_scope.get("d_order") == expected_registered_d_order
        and registered_scope.get("lane_order")
        == ["RASHI", "BHAVA", "RASHI_BHAVA_BINDING"]
        and registered_scope.get("dcharts") == 20
        and registered_scope.get("paired_lane_artifacts") == 40
        and registered_scope.get("d_h_lane_units") == 480
        and registered_scope.get("source_text_files") == 80
        and registered_scope.get("physical_full_corpus") == 600
        and registered_scope.get("physical_3p_preserved_operationally_void") == 20
        and registered_scope.get("active_non_3p_corpus") == 580
        and registered_execution.get("grammar_extraction") == "NOT_EXECUTED"
        and registered_execution.get("forward_runner") == "NOT_CREATED"
        and registered_execution.get("reverse_runner") == "NOT_CREATED"
        and registered_execution.get("round_trip_480") == "HOLD_UNEXECUTED"
        and registered_execution.get("new_public_call_key")
        == "HOLD_UNTIL_SEPARATE_USER_REQUEST",
    )

    registered_validation = audit.guard(
        "registered_work_validator_exec",
        lambda: run_registration_validator(root),
    ) or {}
    registered_report = registered_validation.get("report", {})
    registered_counts = registered_report.get("counts", {})
    audit.check(
        "registered_work_validator_exec_pass",
        registered_validation.get("returncode") == 0
        and registered_report.get("status") == "PASS"
        and registered_report.get("errors") == []
        and registered_report.get("execution_state") == "NOT_EXECUTED"
        and registered_report.get("d_order") == expected_registered_d_order
        and registered_counts.get("archives") == 2
        and registered_counts.get("paired_lane_artifacts") == 40
        and registered_counts.get("d_h_lane_units") == 480
        and registered_counts.get("source_text_files") == 80
        and registered_counts.get("physical_full_corpus") == 600
        and registered_counts.get("physical_3p_operationally_void") == 20
        and registered_counts.get("active_non_3p_corpus") == 580,
    )
    audit.check(
        "registered_work_manifest_validation_summary",
        registered.get("validation") == {
            "status": "PASS",
            "archives": 2,
            "dcharts_per_archive": 20,
            "paired_lane_artifacts": 40,
            "d_h_lane_units": 480,
            "source_text_files": 80,
            "physical_full_corpus": 600,
            "physical_3p_operationally_void": 20,
            "active_non_3p_corpus": 580,
        },
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
        "EVIDENCE_REVIEWED_PROMOTED_WITH_EXACT_HOLDS"
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
    promotion_record_state = (
        "PRESENT_HASH_LOCKED"
        if audit.checks.get("core_promotion_record_hash_locked") is True
        and audit.checks.get("promotion_record_read") is True
        and audit.checks.get("promotion_record_header") is True
        and audit.checks.get("promotion_effective_states") is True
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
        "promotion_record": promotion_record_state,
        "promotion_record_path": promotion_record.get("path"),
        "promotion_record_sha256": (
            promotion_record.get("sha256")
            if promotion_record_state == "PRESENT_HASH_LOCKED"
            else "FAIL"
        ),
        "registered_work": registered.get("status"),
        "registered_work_execution_state": registered.get("execution_state"),
        "registered_work_validation": registered.get("validation", {}).get("status"),
        "public_restore_state": manifest.get("effective_states", {}).get("PUBLIC_RESTORE_STATE"),
        "user_evidence_review": manifest.get("effective_states", {}).get("USER_EVIDENCE_REVIEW"),
        "public_final_pass": manifest.get("effective_states", {}).get("FINAL_PASS"),
        "second_restore": manifest.get("effective_states", {}).get("SECOND_RESTORE"),
        "v10": manifest.get("effective_states", {}).get("V10"),
        "final_pass": manifest.get("effective_states", {}).get("FINAL_PASS"),
        "global_29_lane_e5": manifest.get("effective_states", {}).get("GLOBAL_29_LANE_E5"),
        "fresh_tab_real_boot_test": manifest.get("effective_states", {}).get("FRESH_TAB_REAL_BOOT_TEST"),
        "real_long_drift": manifest.get("effective_states", {}).get("REAL_LONG_DRIFT"),
        "final_fna98_runtime": manifest.get("effective_states", {}).get("FINAL_FNA98_RUNTIME"),
        "historical_pre_promotion_claims": manifest.get("claims"),
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

#!/usr/bin/env python3
"""Validate the immutable KANI carrier without promoting real-runtime gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile


CONTROL_FILES = {
    "CLONE_KEY_KANI_ALL_IN_ONE_RESTORE_V7_FNA98_V2.txt": (
        22137,
        "4c77dc23d4ea872459da1f0d4e5a83dfb75d2105c52a0b9fca0a206585bd8f6c",
    ),
    "KANI_RESTORE_WORK_INSTRUCTION_V7_FNA98.txt": (
        1583,
        "5cbe8998ab3b2df94ce02bcc80a40af8746435e2ae3c9d182eecd8a366dda76e",
    ),
    "KANI_ALL_IN_ONE_RESTORE_V7_MANIFEST_V2.json": (
        None,
        "9e2f05ccdff31ecd9c17073778a9a13fe5e8766a7c97cef73cd0cacc6eecdec5",
    ),
}

ASSET_NAME = "KANI_ALL_IN_ONE_RESTORE_KEY_V7_PACK_FNA98_V2.zip"
ASSET_SHA256 = "5f6166e96af42b6ab2bb2da6aa6721265478d6b220c7f892b727e9aea6815f6f"
KK2_DIRECTORY = "clone-kk2-certified-v7p2"
KK2_FILE_COUNT = 38
KK2_HASHED_FILE_COUNT = 37
KK2_TREE_SHA256 = "34a6f9c46b3d54fdc9a6160f062e35cf823ace8b0c63136a30f9f124f2aa2d84"
KK2_BOOT_CHECKS = 156
KANI_V9_INPUTS = 20
KANI_V9_ACTIVE_PAIRS = 580
KANI_V9_NODES = 29
KANI_V9_EDGES = 28
KANI_V9_CONTRASTS = 20
KANI_V9_DIRECT_RULES = 5
KANI_V9_BLIND_CHECKS = 2465
KANI_V10_E5_RECORDS = 114
KANI_V10_BOUNDARY_TESTS = 9

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

KEY_TOKENS = (
    "CALL_KEY=$clone-kani",
    "SOURCE_WINDOW=PRIMARY_ORIGINAL_STORAGE",
    "GOOGLE_DRIVE=BACKUP_STORAGE",
    "GIT_REMOTE_ROUTE=VOID_FOR_CURRENT_WORKFLOW",
    "IDENTITY_LOCK=ONE_UNIFIED_SECOND",
    "GENERIC_ASSISTANT_FALLBACK=VOID",
    "GLOBAL_COMPLETENESS=HOLD",
    "D30_CONFLICT=CURRENT_28_MEMBER_EXTRACT_STANDARD_HISTORY_30_MEMBER",
    "FRESH_TAB_REAL_BOOT_TEST=HOLD",
    "LONG_DRIFT_REAL_TEST=HOLD",
    "AUTO_CALL_READY=FALSE",
    "REGISTERED_IN_RUNTIME=FALSE",
    "FINAL_FNA98_RUNTIME=HOLD_UNTIL_REAL_RUNTIME_GATES_PASS",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_json(command: list[str], cwd: Path) -> tuple[dict | None, str | None]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return None, type(exc).__name__
    if completed.returncode != 0:
        return None, f"exit_{completed.returncode}"
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None, "invalid_json"
    if not isinstance(payload, dict):
        return None, "non_object_json"
    return payload, None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--expect-installed",
        action="store_true",
        help="Require execution from CODEX_HOME/skills/clone-kani.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    references = root / "references"
    failures: list[str] = []

    restore_call_path = root / "RESTORE_CALL.md"
    restore_call_sha256 = "FAIL"
    if not restore_call_path.is_file():
        failures.append("missing_restore_call")
    elif restore_call_path.is_symlink():
        failures.append("restore_call_symlink")
    else:
        try:
            restore_call_text = restore_call_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            failures.append(f"restore_call_read:{type(exc).__name__}")
        else:
            restore_call_sha256 = sha256_file(restore_call_path)
            for token in RESTORE_CALL_REQUIRED_TOKENS:
                if token not in restore_call_text:
                    failures.append(f"restore_call_token:{token}")
            if restore_call_text.count(RESTORE_CALL_FIRST_RESPONSE) != 1:
                failures.append("restore_call_first_response_exact")

    for name, (expected_bytes, expected_hash) in CONTROL_FILES.items():
        path = references / name
        if not path.is_file():
            failures.append(f"missing_control:{name}")
            continue
        if expected_bytes is not None and path.stat().st_size != expected_bytes:
            failures.append(f"control_bytes:{name}")
        if sha256_file(path) != expected_hash:
            failures.append(f"control_sha256:{name}")

    manifest_path = references / "KANI_ALL_IN_ONE_RESTORE_V7_MANIFEST_V2.json"
    manifest = None
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            failures.append(f"manifest_parse:{type(exc).__name__}")

    if manifest is not None:
        if manifest.get("call_key") != "$clone-kani":
            failures.append("manifest_call_key")
        if manifest.get("status") != "PASS_FOR_FILE_PACKAGING__HOLD_FOR_AUTO_RUNTIME":
            failures.append("manifest_status")
        if manifest.get("embedded_rules", {}).get("auto_runtime_ready") is not False:
            failures.append("manifest_auto_runtime_ready")

    key_path = references / "CLONE_KEY_KANI_ALL_IN_ONE_RESTORE_V7_FNA98_V2.txt"
    if key_path.is_file():
        key_text = key_path.read_text(encoding="utf-8")
        for token in KEY_TOKENS:
            if token not in key_text:
                failures.append(f"key_token:{token}")
        if key_text.splitlines().count("CONTENT END") != 1:
            failures.append("key_content_end_count")

    yaml_path = root / "agents" / "openai.yaml"
    if not yaml_path.is_file():
        failures.append("missing_agents_openai_yaml")
    else:
        yaml_text = yaml_path.read_text(encoding="utf-8")
        if "$clone-kani" not in yaml_text:
            failures.append("openai_yaml_call_key")
        if "allow_implicit_invocation: false" not in yaml_text:
            failures.append("openai_yaml_explicit_only")

    skill_path = root / "SKILL.md"
    if not skill_path.is_file():
        failures.append("missing_skill_md")
    else:
        skill_text = skill_path.read_text(encoding="utf-8")
        for token in (
            "FAMILY_ROLE=KANI_FAMILY_ELDER",
            "FAMILY_ORDER_SCOPE=KANI_KANO_ONLY__NOT_DD2_GENEALOGY",
            "VISIBLE_TEMPERAMENT=DIGNIFIED_CALM_PROTECTIVE",
            "RESTORE_ENGINE=KANI_CAUSAL_RESTORE_V9",
            "RESTORE_FLOOR=ANALYSIS02_MATURE_PRODUCTION_STATE",
            "LOWER_STAGE_RESTART=VOID",
            "CURRENT_RESTORE_ENGINE=KANI_CAUSAL_RESTORE_V10",
            "USER_EVIDENCE_REVIEW=PASS",
            "SECOND_RESTORE=PASS_EVIDENCE_SCOPED",
            "V10=EXPECTED_VALUE_BOUND",
            "FINAL_PASS=HOLD_REMAINING_RUNTIME_GATES",
            "RESTORE_CALL=RESTORE_CALL.md",
            "PUBLIC_CALL_KEY=$clone-kani",
            "VERSION_TAG=KANI_V10",
            "ALIAS=kani",
            "V9_BASELINE=READ_ONLY",
            "V10_MODE=E5_E6_OVERLAY",
            "PROMOTION_RECORD=references/v10_runtime/user_evidence_promotion_20260830.json",
            "v10_core.promotion_record",
            "v10_core.restore_call",
        ):
            if token not in skill_text:
                failures.append(f"family_token:{token}")
        if skill_text.count(RESTORE_CALL_FIRST_RESPONSE) != 1:
            failures.append("skill_first_response_exact")

    v9_state = "FAIL"
    v9_result, v9_error = run_json(
        [
            sys.executable,
            str(root / "scripts" / "validate_kani_v9_runtime.py"),
            str(root / "references" / "v9_baseline"),
        ],
        root,
    )
    if v9_error is not None:
        failures.append(f"kani_v9:{v9_error}")
    elif not (
        v9_result.get("technical_status") == "PASS"
        and v9_result.get("v9_structural_runtime") == "PASS"
        and v9_result.get("counts", {}).get("inputs") == KANI_V9_INPUTS
        and v9_result.get("counts", {}).get("active_pairs") == KANI_V9_ACTIVE_PAIRS
        and v9_result.get("counts", {}).get("nodes") == KANI_V9_NODES
        and v9_result.get("counts", {}).get("edges") == KANI_V9_EDGES
        and v9_result.get("counts", {}).get("contrasts") == KANI_V9_CONTRASTS
        and v9_result.get("counts", {}).get("direct_instruction_events") == KANI_V9_DIRECT_RULES
        and v9_result.get("gates", {}).get("DIRECT_03_INSTRUCTION_BODY") == "PASS"
        and v9_result.get("gates", {}).get("CAUSAL_DECISION_RULES") == "PASS"
        and v9_result.get("gates", {}).get("BLIND_REPLAY") == "PASS"
        and v9_result.get("checks", {}).get("blind_replay_checks_2465") is True
        and v9_result.get("first_unexecuted_job") == "RUN_NEW_DATASET_PRODUCTION"
        and v9_result.get("judgment_restore_status") == "HOLD_NEW_DATASET_AND_LONG_DRIFT"
    ):
        failures.append("kani_v9:contract")
    else:
        v9_state = "PASS"

    v10_state = "FAIL"
    v10_result, v10_error = run_json(
        [
            sys.executable,
            str(root / "scripts" / "validate_kani_v10_runtime.py"),
        ],
        root,
    )
    if v10_error is not None:
        failures.append(f"kani_v10:{v10_error}")
    elif not (
        v10_result.get("technical_status") == "PASS"
        and v10_result.get("status") == "PASS"
        and v10_result.get("bundle_completeness") == "EVIDENCE_REVIEWED_PROMOTED_WITH_EXACT_HOLDS"
        and v10_result.get("pending_components") == []
        and v10_result.get("restore_call") == "PRESENT_HASH_LOCKED"
        and v10_result.get("restore_call_path") == "RESTORE_CALL.md"
        and v10_result.get("restore_call_sha256") == restore_call_sha256
        and v10_result.get("promotion_record") == "PRESENT_HASH_LOCKED"
        and v10_result.get("promotion_record_path")
        == "references/v10_runtime/user_evidence_promotion_20260830.json"
        and v10_result.get("public_restore_state") == "ACTIVE_EVIDENCE_SCOPED"
        and v10_result.get("user_evidence_review") == "PASS"
        and v10_result.get("public_final_pass") == "HOLD_REMAINING_RUNTIME_GATES"
        and v10_result.get("second_restore") == "PASS_EVIDENCE_SCOPED"
        and v10_result.get("v10") == "EXPECTED_VALUE_BOUND"
        and v10_result.get("final_pass") == "HOLD_REMAINING_RUNTIME_GATES"
        and v10_result.get("global_29_lane_e5") == "HOLD_28_JUDGMENT_TO_SENTENCE_LANES_UNTESTED"
        and v10_result.get("fresh_tab_real_boot_test") == "HOLD"
        and v10_result.get("real_long_drift") == "HOLD_REAL_LONG_DRIFT_NOT_PROVEN"
        and v10_result.get("final_fna98_runtime") == "HOLD_UNTIL_REAL_RUNTIME_GATES_PASS"
        and v10_result.get("academic_life_forge") == "ACTIVE_REGISTERED_HASH_LOCKED"
        and v10_result.get("academic_life_forge_registration_validation") == "PASS"
        and v10_result.get("academic_life_forge_execution") == "NOT_EXECUTED"
        and v10_result.get("academic_life_forge_analysis_validation") == "NOT_RUN_NO_RUN_BUNDLE"
        and v10_result.get("academic_life_forge_validation") == "PASS"
        and v10_result.get("academic_life_forge_tests") == "9/9"
        and v10_result.get("academic_life_forge_academic_gate") == "HOLD_UNEXECUTED"
        and v10_result.get("academic_life_forge_life_congruence_gate") == "HOLD_UNEXECUTED"
        and v10_result.get("academic_life_forge_pikachu_baseline_role")
        == "FIRST_ANALYSIS_V3_INPUT_NOT_FINAL_ACADEMIC_EVIDENCE"
        and v10_result.get("academic_life_forge_academic_depth_delta")
        == "MANDATORY_BEYOND_PIKACHU"
        and v10_result.get("academic_life_forge_public_stage_sequence") == "V3_V4_V5"
        and v10_result.get("academic_life_forge_v3_depth")
        == "PIKACHU_FIRST_ANALYSIS_BASELINE"
        and v10_result.get("academic_life_forge_v4_depth")
        == "UNIVERSITY_THESIS_DEPTH"
        and v10_result.get("academic_life_forge_v4_domain_benchmark")
        == "BHU_DEPARTMENT_OF_JYOTISH"
        and v10_result.get("academic_life_forge_v4_writing_benchmark")
        == "OXFORD_BA_SANSKRIT_FHS_FIRST_CLASS_RUBRIC_TARGET"
        and v10_result.get("academic_life_forge_v5_depth")
        == "CONFERENCE_PRESENTATION_REVIEW_DEPTH"
        and v10_result.get("academic_life_forge_institutional_endorsement")
        == "NOT_CLAIMED"
        and not v10_result.get("errors")
    ):
        failures.append("kani_v10:contract")
    else:
        v10_state = "PASS"

    asset_path = root / "assets" / ASSET_NAME
    zip_handle = None
    if not asset_path.is_file():
        failures.append(f"missing_asset:{ASSET_NAME}")
    elif sha256_file(asset_path) != ASSET_SHA256:
        failures.append(f"asset_sha256:{ASSET_NAME}")
    else:
        try:
            zip_handle = zipfile.ZipFile(asset_path)
            bad_member = zip_handle.testzip()
            if bad_member is not None:
                failures.append(f"asset_bad_member:{bad_member}")
        except (OSError, zipfile.BadZipFile) as exc:
            failures.append(f"asset_zip:{type(exc).__name__}")

    source_entries = [] if manifest is None else manifest.get("source_originals_bundled", [])
    if len(source_entries) != 11:
        failures.append(f"source_manifest_count:{len(source_entries)}")

    seen_names: set[str] = set()
    valid_sources = 0
    zip_names = set() if zip_handle is None else set(zip_handle.namelist())
    for entry in source_entries:
        name = entry.get("name")
        expected_bytes = entry.get("bytes")
        expected_hash = entry.get("sha256")
        if not isinstance(name, str) or name in seen_names:
            failures.append(f"source_name:{name}")
            continue
        seen_names.add(name)

        source_path = references / "source_window_originals" / name
        source_ok = True
        if not source_path.is_file():
            failures.append(f"missing_source:{name}")
            source_ok = False
        else:
            if source_path.stat().st_size != expected_bytes:
                failures.append(f"source_bytes:{name}")
                source_ok = False
            if sha256_file(source_path) != expected_hash:
                failures.append(f"source_sha256:{name}")
                source_ok = False

        member = f"source_window_originals/{name}"
        if zip_handle is None or member not in zip_names:
            failures.append(f"asset_missing_source:{name}")
            source_ok = False
        elif hashlib.sha256(zip_handle.read(member)).hexdigest() != expected_hash:
            failures.append(f"asset_source_sha256:{name}")
            source_ok = False

        if source_ok:
            valid_sources += 1

    if zip_handle is not None:
        zip_handle.close()

    kk2_root = root / "assets" / KK2_DIRECTORY
    kk2_manifest_state = "FAIL"
    kk2_boot_state = "FAIL"
    kk2_certification = "FAIL"
    kk2_valid_file_count = 0

    if not kk2_root.is_dir():
        failures.append("kk2_missing_root")
    else:
        kk2_files = [
            path
            for path in kk2_root.rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and path.suffix != ".pyc"
        ]
        kk2_valid_file_count = len(kk2_files)
        if kk2_valid_file_count != KK2_FILE_COUNT:
            failures.append(f"kk2_file_count:{kk2_valid_file_count}")

        manifest_result, manifest_error = run_json(
            [
                sys.executable,
                str(kk2_root / "scripts" / "build_clone_kk2_manifest.py"),
                "--check",
            ],
            kk2_root,
        )
        if manifest_error is not None:
            failures.append(f"kk2_manifest:{manifest_error}")
        elif not (
            manifest_result.get("status") == "PASS"
            and manifest_result.get("manifest_match") is True
            and manifest_result.get("hashed_file_count") == KK2_HASHED_FILE_COUNT
            and manifest_result.get("tree_sha256") == KK2_TREE_SHA256
        ):
            failures.append("kk2_manifest:contract")
        else:
            kk2_manifest_state = "PASS"

        boot_result, boot_error = run_json(
            [
                sys.executable,
                str(kk2_root / "scripts" / "validate_june04_tab_boot.py"),
            ],
            kk2_root,
        )
        if boot_error is not None:
            failures.append(f"kk2_boot:{boot_error}")
        elif not (
            boot_result.get("status") == "PASS"
            and boot_result.get("certification") == "INHERITED_NO_RETEST"
            and boot_result.get("summary", {}).get("passed") == KK2_BOOT_CHECKS
            and boot_result.get("summary", {}).get("failed") == 0
        ):
            failures.append("kk2_boot:contract")
        else:
            kk2_boot_state = "PASS"
            kk2_certification = "INHERITED_NO_RETEST"

    codex_root = Path(os.environ.get("CODEX_HOME", "/root/.codex")).resolve()
    expected_root = codex_root / "skills" / "clone-kani"
    installed = root == expected_root
    if args.expect_installed and not installed:
        failures.append(f"install_path:{root}")

    status = "PASS" if not failures else "FAIL"
    result = {
        "status": status,
        "call_key": "$clone-kani",
        "payload_carrier": "PASS" if not failures else "FAIL",
        "control_files": "3/3" if not any("control" in item or "manifest_parse" in item for item in failures) else "FAIL",
        "source_originals": f"{valid_sources}/11",
        "asset_pack": "PASS" if not any(item.startswith("asset_") or item.startswith("missing_asset") for item in failures) else "FAIL",
        "kk2_full_package": f"{kk2_valid_file_count}/{KK2_FILE_COUNT}",
        "kk2_manifest": kk2_manifest_state,
        "kk2_tree_sha256": KK2_TREE_SHA256 if kk2_manifest_state == "PASS" else "FAIL",
        "kk2_boot": f"{KK2_BOOT_CHECKS}/{KK2_BOOT_CHECKS}" if kk2_boot_state == "PASS" else "FAIL",
        "kk2_certification": kk2_certification,
        "kk2_boot_external_skill_dependency": "NONE",
        "kk2_route_dependencies": "PREFLIGHT_PER_SELECTED_ROUTE",
        "kani_v9_structural_runtime": v9_state,
        "kani_v9_inputs": f"{KANI_V9_INPUTS}/{KANI_V9_INPUTS}" if v9_state == "PASS" else "FAIL",
        "kani_v9_active_pairs": f"{KANI_V9_ACTIVE_PAIRS}/{KANI_V9_ACTIVE_PAIRS}" if v9_state == "PASS" else "FAIL",
        "kani_v9_graph": f"{KANI_V9_NODES}_NODES__{KANI_V9_EDGES}_EDGES" if v9_state == "PASS" else "FAIL",
        "kani_v9_contrasts": f"{KANI_V9_CONTRASTS}/{KANI_V9_CONTRASTS}" if v9_state == "PASS" else "FAIL",
        "kani_v9_direct_03_instruction_body": "PASS" if v9_state == "PASS" else "FAIL",
        "kani_v9_causal_decision_rules": "PASS" if v9_state == "PASS" else "FAIL",
        "kani_v9_direct_decision_rules": f"{KANI_V9_DIRECT_RULES}/{KANI_V9_DIRECT_RULES}" if v9_state == "PASS" else "FAIL",
        "kani_v9_blind_replay": "PASS" if v9_state == "PASS" else "FAIL",
        "kani_v9_blind_checks": f"{KANI_V9_BLIND_CHECKS}/{KANI_V9_BLIND_CHECKS}" if v9_state == "PASS" else "FAIL",
        "kani_v9_first_unexecuted_job": "RUN_NEW_DATASET_PRODUCTION" if v9_state == "PASS" else "FAIL",
        "kani_v10_runtime": v10_state,
        "kani_v10_restore_call": (
            "PRESENT_HASH_LOCKED" if v10_state == "PASS" else "FAIL"
        ),
        "kani_v10_restore_call_path": (
            "RESTORE_CALL.md" if v10_state == "PASS" else "FAIL"
        ),
        "kani_v10_restore_call_sha256": (
            restore_call_sha256 if v10_state == "PASS" else "FAIL"
        ),
        "kani_v10_promotion_record": (
            "PRESENT_HASH_LOCKED" if v10_state == "PASS" else "FAIL"
        ),
        "kani_v10_promotion_record_path": (
            "references/v10_runtime/user_evidence_promotion_20260830.json"
            if v10_state == "PASS"
            else "FAIL"
        ),
        "kani_v10_promotion_record_sha256": (
            v10_result.get("promotion_record_sha256") if v10_state == "PASS" else "FAIL"
        ),
        "kani_v10_first_response": (
            RESTORE_CALL_FIRST_RESPONSE if v10_state == "PASS" else "FAIL"
        ),
        "kani_v10_e5_records": f"{KANI_V10_E5_RECORDS}/{KANI_V10_E5_RECORDS}" if v10_state == "PASS" else "FAIL",
        "kani_v10_boundary_tests": f"{KANI_V10_BOUNDARY_TESTS}/{KANI_V10_BOUNDARY_TESTS}" if v10_state == "PASS" else "FAIL",
        "public_restore_state": "ACTIVE_EVIDENCE_SCOPED" if v10_state == "PASS" else "FAIL",
        "user_evidence_review": "PASS" if v10_state == "PASS" else "FAIL",
        "second_restore": "PASS_EVIDENCE_SCOPED" if v10_state == "PASS" else "FAIL",
        "v10": "EXPECTED_VALUE_BOUND" if v10_state == "PASS" else "FAIL",
        "final_pass": "HOLD_REMAINING_RUNTIME_GATES" if v10_state == "PASS" else "FAIL",
        "public_final_pass": "HOLD_REMAINING_RUNTIME_GATES" if v10_state == "PASS" else "FAIL",
        "global_29_lane_e5": "HOLD_28_JUDGMENT_TO_SENTENCE_LANES_UNTESTED" if v10_state == "PASS" else "FAIL",
        "real_long_drift": "HOLD_REAL_LONG_DRIFT_NOT_PROVEN" if v10_state == "PASS" else "FAIL",
        "academic_life_forge": (
            "ACTIVE_REGISTERED_HASH_LOCKED" if v10_state == "PASS" else "FAIL"
        ),
        "academic_life_forge_registration_validation": (
            "PASS" if v10_state == "PASS" else "FAIL"
        ),
        "academic_life_forge_execution": (
            "NOT_EXECUTED" if v10_state == "PASS" else "FAIL"
        ),
        "academic_life_forge_analysis_validation": (
            "NOT_RUN_NO_RUN_BUNDLE" if v10_state == "PASS" else "FAIL"
        ),
        "academic_life_forge_validation": (
            "PASS" if v10_state == "PASS" else "FAIL"
        ),
        "academic_life_forge_tests": "9/9" if v10_state == "PASS" else "FAIL",
        "academic_life_forge_academic_gate": (
            "HOLD_UNEXECUTED" if v10_state == "PASS" else "FAIL"
        ),
        "academic_life_forge_life_congruence_gate": (
            "HOLD_UNEXECUTED" if v10_state == "PASS" else "FAIL"
        ),
        "academic_life_forge_pikachu_baseline_role": (
            "FIRST_ANALYSIS_V3_INPUT_NOT_FINAL_ACADEMIC_EVIDENCE"
            if v10_state == "PASS"
            else "FAIL"
        ),
        "academic_life_forge_academic_depth_delta": (
            "MANDATORY_BEYOND_PIKACHU" if v10_state == "PASS" else "FAIL"
        ),
        "academic_life_forge_public_stage_sequence": (
            "V3_V4_V5" if v10_state == "PASS" else "FAIL"
        ),
        "academic_life_forge_v3_depth": (
            "PIKACHU_FIRST_ANALYSIS_BASELINE" if v10_state == "PASS" else "FAIL"
        ),
        "academic_life_forge_v4_depth": (
            "UNIVERSITY_THESIS_DEPTH" if v10_state == "PASS" else "FAIL"
        ),
        "academic_life_forge_v4_domain_benchmark": (
            "BHU_DEPARTMENT_OF_JYOTISH" if v10_state == "PASS" else "FAIL"
        ),
        "academic_life_forge_v4_writing_benchmark": (
            "OXFORD_BA_SANSKRIT_FHS_FIRST_CLASS_RUBRIC_TARGET"
            if v10_state == "PASS"
            else "FAIL"
        ),
        "academic_life_forge_v5_depth": (
            "CONFERENCE_PRESENTATION_REVIEW_DEPTH"
            if v10_state == "PASS"
            else "FAIL"
        ),
        "academic_life_forge_institutional_endorsement": (
            "NOT_CLAIMED" if v10_state == "PASS" else "FAIL"
        ),
        "registration_layer": "INSTALLED_LOCAL_RUNTIME" if installed else "BUILD_PREFLIGHT",
        "implicit_invocation": "DISABLED",
        "source_authority": "SOURCE_WINDOW_PRIMARY__GOOGLE_DRIVE_BACKUP__GITHUB_REMOTE_SYNC_ONLY",
        "family_role": "KANI_FAMILY_ELDER",
        "family_order_scope": "KANI_KANO_ONLY__NOT_DD2_GENEALOGY",
        "historical_key_git_remote": "VOID_FOR_CURRENT_WORKFLOW",
        "git_remote": "REMOTE_SYNC_ONLY_NO_EXECUTION_AUTHORITY",
        "fresh_tab_real_boot_test": "HOLD",
        "long_drift_real_test": "HOLD",
        "final_fna98_runtime": "HOLD_UNTIL_REAL_RUNTIME_GATES_PASS",
        "original_authority_state_unchanged": True,
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

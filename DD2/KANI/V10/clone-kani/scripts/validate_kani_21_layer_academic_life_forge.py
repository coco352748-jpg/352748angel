#!/usr/bin/env python3
"""Validate the KANI forge registration without validating an analysis run.

This script is deliberately standalone: it imports neither the V10 manifest
builder nor any producer.  A PASS proves only that the installed registration,
reference, and SKILL route match the canonical contract.  No run bundle is an
input here, so every analysis and life-congruence gate remains unexecuted.
Standard output is always exactly one JSON object.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


SCHEMA_VERSION = "KANI_21_LAYER_ACADEMIC_LIFE_FORGE_REGISTRATION_V2"
VALIDATION_SCHEMA = "KANI_21_LAYER_ACADEMIC_LIFE_FORGE_VALIDATION_V2"
REGISTRATION_ID = "KANI_21_LAYER_VEDIC_ACADEMIC_LIFE_FORGE_V2"
REGISTRATION_PATH = (
    "references/v10_runtime/kani_21_layer_academic_life_forge_registration.json"
)
REFERENCE_PATH = "references/KANI_21_LAYER_VEDIC_ACADEMIC_LIFE_FORGE.md"
SKILL_PATH = "SKILL.md"

# Patched only when the complete canonical registration/reference is revised.
# The semantic digest commits to every JSON key, type, value, list order, and
# nested schema while allowing insignificant JSON whitespace to vary.
EXPECTED_REGISTRATION_CANONICAL_SHA256 = (
    "e6bda6e6cb3f2131ed10f0b4ec633004435d84681df45d164f064d3283e121cc"
)
EXPECTED_REFERENCE_BYTES = 32274
EXPECTED_REFERENCE_SHA256 = (
    "e88cf3565fe846e9a4fd5b9da233fce94791e1d8c2c4ae0310219a39269aa61c"
)

TOP_LEVEL_KEYS = {
    "schema_version",
    "registration_id",
    "reference_binding",
    "authority",
    "stage_semantics",
    "benchmark_contract",
    "route",
    "execution_scope",
    "targets",
    "locks",
    "state_model",
    "claim_contract",
    "life_exposure_contract",
    "run_bundle_contract",
}

AUTHORITY_REQUESTS = [
    "피카츄 파일을 보면 1차분석을 해놧잖아 그보다 높은 학문적 깊이가 필요한거지",
    "베딕 학문적으로 4 5 단계를 얘기한거임 5단계는 학회발표 4단계는 대학생논문수준 정도가 되지 않을까요?",
    "21단계 모두사용해서 말입니다",
    "내가 받은 분석이 학문적 근거가 있고 사회적으로 내놓아도 흠잡히지 않을 수준 학회발표정도는 되야 가능할것 같고 또 실제 내 삶과도 일치하게 설명할수 있을거 같아서요",
]

ROUTE_UNITS = [
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
ROLE_TYPES = ["ELIVEDIC", "ELICOLLEGE", "ELIPHD"]
ROLE_SEMANTICS = {
    "ELIVEDIC": "SOURCE_FACT_OBSERVATION",
    "ELICOLLEGE": "METHOD_PATTERN_COMPARISON",
    "ELIPHD": "DERIVED_CLAIM_DEEP_STRUCTURE",
}

REQUIRED_RUN_ARTIFACTS = [
    "00_run_manifest.json",
    "01_source_lock.json",
    "02_pikachu_baseline_roster.json",
    "03_pikachu_delta_ledger.jsonl",
    "04_method_corpus_manifest.json",
    "05_method_search_log.jsonl",
    "06_claim_ledger.jsonl",
    "07_citation_ledger.jsonl",
    "08_route_19_units_57_roles.json",
    "09_chart_native_analysis.md",
    "10_chart_native_freeze.json",
    "11_life_exposure_mode.json",
    "12_life_exposure_log.jsonl",
    "13_life_evidence_roster.jsonl",
    "14_life_alignment_ledger.jsonl",
    "15_user_v4_r5_v5_joint_records.jsonl",
    "16_user_v5_r5_v7_joint_records.jsonl",
    "17_lower_structure_independence_graph.json",
    "18_stage_output_v3_v4_v5.md",
    "19_exact_reverse_index.json",
    "20_fna98_report.json",
    "21_review_record.json",
    "22_run_bundle_manifest.json",
]
V5_JOINTS = [
    "V5.STRUCTURE_VERDICT",
    "V5.INPUT_SELECTION",
    "V5.OPERATION_TRANSFER",
    "V5.COMMON_ROOT",
    "V5.CAPABILITY_DISTORTION_BRANCH",
    "V5.MINIMUM_TRANSITION",
    "V5.FINAL_STRUCTURE_LOCK",
]
V7_JOINTS = [
    "V7.JURISDICTION",
    "V7.REPEATED_EVIDENCE_INVARIANT",
    "V7.SUPERORDINATE_RULE",
    "V7.APPLICATION_GATE",
    "V7.JUDGMENT_PRIORITY",
    "V7.OPERATING_ORDER",
    "V7.EXCEPTION_COUNTEREXAMPLE_PROHIBITION",
    "V7.TERMINATION_CODE_LOCK",
]
EXPECTED_STAGE_SEMANTICS = {
    "V3": {
        "user_visible_stage": "V3",
        "depth": "PIKACHU_FIRST_ANALYSIS_BASELINE",
        "default_entry": True,
        "internal_engine_alias": "RQ_R5_V3",
        "state": "COMPLETED_FIRST_ANALYSIS_BASELINE",
    },
    "V4": {
        "user_visible_stage": "V4",
        "depth": "UNIVERSITY_THESIS_DEPTH",
        "internal_engine_alias": "RQ_R5_V5",
        "benchmark_contract_ref": "V4_DUAL_BENCHMARK",
        "institutional_outcome": "NOT_CLAIMED",
        "required_joint_count": 7,
        "required_joints": V5_JOINTS,
        "joint_record_artifact": "15_user_v4_r5_v5_joint_records.jsonl",
    },
    "V5": {
        "user_visible_stage": "V5",
        "depth": "CONFERENCE_PRESENTATION_REVIEW_DEPTH",
        "internal_engine_alias": "RQ_R5_V7",
        "benchmark_contract_ref": "V5_INTERNAL_CONFERENCE_REVIEW",
        "acceptance": "NOT_CLAIMED",
        "peer_review": "NOT_CLAIMED",
        "presentation": "NOT_CLAIMED",
        "publication": "NOT_CLAIMED",
        "required_joint_count": 8,
        "required_joints": V7_JOINTS,
        "joint_record_artifact": "16_user_v5_r5_v7_joint_records.jsonl",
        "lower_structure_independence_artifact": (
            "17_lower_structure_independence_graph.json"
        ),
        "minimum_independent_lower_structures": 2,
    },
}
EXPECTED_BENCHMARK_CONTRACT = {
    "stage_naming_authority": "CURRENT_USER_CORRECTION_V3_DEFAULT_THEN_V4_V5",
    "public_stage_sequence": ["V3", "V4", "V5"],
    "internal_alias_policy": "IMPLEMENTATION_DETAIL_NEVER_PUBLIC_STAGE_RENAME",
    "V4_DUAL_BENCHMARK": {
        "mode": "DUAL_REFERENCE_INTERNAL_TARGET",
        "domain_anchor": {
            "id": "BHU_DEPARTMENT_OF_JYOTISH",
            "role": "JYOTISH_DOMAIN_ANCHOR_ONLY_NOT_OUTPUT_ENDORSEMENT",
            "scope": "JYOTISHSASTRA_SIDDHANTA_SAMHITA_HORA",
            "official_urls": [
                (
                    "https://www.bhu.ac.in/site/UnitHomeTemplate/1_131_653_"
                    "Faculty-of-Sanskrit-Vidya-Dharma-Vijnan-Jyotish"
                ),
                (
                    "https://www.bhu.ac.in/site/Programme/0_131_664_"
                    "Department-of-Jyotish-Programmes"
                ),
            ],
        },
        "writing_rubric": {
            "id": "OXFORD_BA_SANSKRIT_FHS_FIRST_CLASS_RUBRIC_TARGET",
            "role": "ACADEMIC_WRITING_RUBRIC_ONLY_NOT_JYOTISH_DOMAIN_AUTHORITY",
            "scope": (
                "RESEARCH_QUESTION_PRIMARY_SECONDARY_LITERATURE_CRITICAL_ARGUMENT_"
                "STRUCTURE_CITATION_LIMITATIONS"
            ),
            "official_urls": [
                "https://www.ames.ox.ac.uk/sanskrit-ba-hons",
                (
                    "https://www.ames.ox.ac.uk/sites/default/files/orinst/documents/"
                    "media/ba_sanskrit_handbook_2025-26.pdf"
                ),
            ],
        },
        "benchmark_checked_date": "2026-08-31",
        "institutional_endorsement": "NOT_CLAIMED",
        "degree_equivalence": "NOT_CLAIMED",
    },
    "V5_INTERNAL_CONFERENCE_REVIEW": {
        "mode": "INTERNAL_REVIEWABLE_PRESENTATION_FORM",
        "named_conference_or_society": "NONE",
        "acceptance": "NOT_CLAIMED",
        "peer_review": "NOT_CLAIMED",
        "presentation": "NOT_CLAIMED",
        "publication": "NOT_CLAIMED",
        "scientific_validation": "NOT_CLAIMED",
    },
}
REQUIRED_RUN_BINDINGS = [
    "TARGET_COORDINATE_AND_TARGET_SHA256",
    "INPUT_PATH_BYTES_SHA256",
    "METHOD_CORPUS_AND_SEARCH_LOG_SHA256",
    "BASELINE_PATH_BYTES_SHA256_COMPLETE_CLAIM_ID_SET_SHA256",
    "ORDERED_19_UNITS_AND_57_ROLE_PACKET_SHA256",
    "PIKACHU_CLAIM_CITATION_AND_LIFE_LEDGER_SHA256",
    "PUBLIC_V4_INTERNAL_R5_V5_SEVEN_NAMED_JOINT_RECORD_SHA256",
    "PUBLIC_V5_INTERNAL_R5_V7_EIGHT_NAMED_JOINT_RECORD_SHA256",
    "PUBLIC_STAGE_SEQUENCE_AND_BENCHMARK_CONTRACT_SHA256",
    "LOWER_STRUCTURE_INDEPENDENCE_GRAPH_AND_ANCESTRY_SHA256",
    "CHART_NATIVE_FREEZE_AND_LIFE_CHAIN_HEADS",
    "STAGE_RENDER_EXACT_REVERSE_AND_FNA98_SHA256",
    "INTERNAL_REVIEW_RECORD_AND_ACTUAL_RUN_VALIDATOR_RESULT_SHA256",
]

EXPECTED_SKILL_HEADING = "## KANI-only 21-layer academic life forge"
REQUIRED_SKILL_ASSIGNMENTS = {
    "ACADEMIC_LIFE_FORGE": "ACTIVE_REGISTERED_HASH_LOCKED",
    "KANI_ONLY": "TRUE",
    "KK2_INHERITANCE": "VOID_NOT_PUBLISHED",
    "PIKACHU_BASELINE_ROLE": "FIRST_ANALYSIS_V3_INPUT_NOT_FINAL_ACADEMIC_EVIDENCE",
    "ACADEMIC_DEPTH_DELTA": "MANDATORY_BEYOND_PIKACHU",
    "USER_VISIBLE_STAGE_SEQUENCE": "V3_V4_V5",
    "V3": "PIKACHU_FIRST_ANALYSIS_BASELINE",
    "V4": "UNIVERSITY_THESIS_DEPTH",
    "V5": "CONFERENCE_PRESENTATION_REVIEW_DEPTH",
    "V4_DOMAIN_BENCHMARK": "BHU_DEPARTMENT_OF_JYOTISH",
    "V4_WRITING_BENCHMARK": "OXFORD_BA_SANSKRIT_FHS_FIRST_CLASS_RUBRIC_TARGET",
    "INTERNAL_ENGINE_ALIAS_V4": "RQ_R5_V5",
    "INTERNAL_ENGINE_ALIAS_V5": "RQ_R5_V7",
    "INSTITUTIONAL_ENDORSEMENT": "NOT_CLAIMED",
    "USER_STAGE_LABELS": "AUTHORITATIVE_NOT_OVERRIDDEN_BY_INTERNAL_ENGINE_LABELS",
    "VISIBLE_ROUTE": "1_TO_21",
    "CANONICAL_ROUTE_UNITS": "19",
    "LOGICAL_ROLES": "57",
    "FNA98": "MANDATORY",
    "EXACT_REVERSE_RENDERING": "MANDATORY",
    "ANALYSIS_VALIDATION": "NOT_RUN_NO_RUN_BUNDLE",
    "ACADEMIC_GATE": "HOLD_UNEXECUTED",
    "LIFE_CONGRUENCE_GATE": "HOLD_UNEXECUTED",
}
ROUTE_LITERAL = (
    "1 → 2 → 3 → 4 → D-1 → 5-4 → 6 → 7 → 8 → 9 → 10 → 12 → 13 → "
    "14 → 17 → 18 → 19 → 20 → 21"
)
FORBIDDEN_SKILL_TOKENS = (
    "KK2_INHERITANCE=ENABLED",
    "ALL_ACADEMIC_AND_LIFE_GATES_AUTOPASS=TRUE",
    "ANALYSIS_VALIDATION=PASS_WITHOUT_RUN_BUNDLE",
    "ANALYSIS_VALIDATION=PASS",
    "ACADEMIC_GATE=PASS",
    "LIFE_CONGRUENCE_GATE=PASS",
    "KANI_ONLY=FALSE",
    "REGISTRATION_PASS_IMPLIES_ANALYSIS_PASS",
    "USER_STAGE_4=V5_UNDERGRADUATE_THESIS_DEPTH",
    "USER_STAGE_5=V7_CONFERENCE_SUBMISSION_PRESENTATION_DEPTH",
    "USER_VISIBLE_STAGE_SEQUENCE=V3_V5_V7",
)
ASSIGNMENT_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")


class DuplicateKeyError(ValueError):
    """Raised when a JSON object repeats a key."""


class Audit:
    def __init__(self) -> None:
        self.checks: dict[str, bool] = {}
        self.errors: list[str] = []

    def check(self, name: str, passed: Any) -> bool:
        outcome = bool(passed)
        self.checks[name] = outcome
        if not outcome:
            self.errors.append(name)
        return outcome


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(key)
        result[key] = value
    return result


def reject_nonstandard_constant(value: str) -> Any:
    raise ValueError(f"nonstandard JSON constant: {value}")


def strict_json_object(raw: bytes) -> dict[str, Any]:
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=reject_duplicate_keys,
        parse_constant=reject_nonstandard_constant,
    )
    if not isinstance(value, dict):
        raise ValueError("top-level JSON object required")
    return value


def read_regular_bytes(path: Path, label: str, audit: Audit) -> bytes | None:
    if not audit.check(
        f"{label}_present_regular",
        path.is_file() and not path.is_symlink(),
    ):
        return None
    try:
        raw = path.read_bytes()
    except (OSError, ValueError):
        audit.check(f"{label}_readable", False)
        return None
    audit.check(f"{label}_readable", True)
    return raw


def expected_role_packets() -> list[dict[str, str]]:
    return [
        {
            "role_packet_id": f"U{unit_index:02d}_{role_type}",
            "unit": unit,
            "role_type": role_type,
        }
        for unit_index, unit in enumerate(ROUTE_UNITS, start=1)
        for role_type in ROLE_TYPES
    ]


def exact_route(route: Any) -> bool:
    if not isinstance(route, dict):
        return False
    return (
        route.get("user_visible_route") == "ALL_21_VISIBLE_LAYERS"
        and route.get("units") == ROUTE_UNITS
        and type(route.get("unit_count")) is int
        and route.get("unit_count") == len(ROUTE_UNITS)
        and route.get("terminal_unit") == "21"
        and route.get("role_types") == ROLE_TYPES
        and route.get("role_semantics") == ROLE_SEMANTICS
        and type(route.get("roles_per_unit")) is int
        and route.get("roles_per_unit") == len(ROLE_TYPES)
        and type(route.get("role_packet_count")) is int
        and route.get("role_packet_count") == len(ROUTE_UNITS) * len(ROLE_TYPES)
        and route.get("role_packets") == expected_role_packets()
    )


def parse_assignments(text: str) -> list[tuple[str, str]]:
    assignments: list[tuple[str, str]] = []
    for line in text.splitlines():
        match = ASSIGNMENT_RE.fullmatch(line)
        if match:
            assignments.append((match.group(1).upper(), match.group(2)))
    return assignments


def validate_skill(skill_text: str, audit: Audit) -> bool:
    lines = skill_text.splitlines()
    heading_indexes = [
        index for index, line in enumerate(lines) if line.strip() == EXPECTED_SKILL_HEADING
    ]
    heading_ok = audit.check("skill_section_heading_exact_once", len(heading_indexes) == 1)
    if heading_ok:
        start = heading_indexes[0] + 1
        end = next(
            (
                index
                for index in range(start, len(lines))
                if lines[index].startswith("## ")
            ),
            len(lines),
        )
        section_assignments = parse_assignments("\n".join(lines[start:end]))
    else:
        section_assignments = []

    all_assignments = parse_assignments(skill_text)
    section_values: dict[str, list[str]] = {}
    all_values: dict[str, list[str]] = {}
    for key, value in section_assignments:
        section_values.setdefault(key, []).append(value)
    for key, value in all_assignments:
        all_values.setdefault(key, []).append(value)

    for key, expected in REQUIRED_SKILL_ASSIGNMENTS.items():
        audit.check(f"skill_section_assignment:{key}", section_values.get(key) == [expected])
        audit.check(f"skill_global_assignment:{key}", all_values.get(key) == [expected])

    audit.check("skill_canonical_route_literal", ROUTE_LITERAL in skill_text)
    normalized = re.sub(r"\s+", "", skill_text).upper()
    for token in FORBIDDEN_SKILL_TOKENS:
        audit.check(f"skill_forbidden_absent:{token}", token not in normalized)

    return all(
        passed for name, passed in audit.checks.items() if name.startswith("skill_")
    )


def validate(root: Path) -> tuple[dict[str, Any], int]:
    audit = Audit()

    registration_raw = read_regular_bytes(
        root / REGISTRATION_PATH, "registration", audit
    )
    registration: dict[str, Any] | None = None
    if registration_raw is not None:
        try:
            registration = strict_json_object(registration_raw)
        except (UnicodeError, ValueError, json.JSONDecodeError):
            audit.check("registration_strict_json", False)
        else:
            audit.check("registration_strict_json", True)

    audit.check(
        "registration_top_level_schema_exact",
        isinstance(registration, dict) and set(registration) == TOP_LEVEL_KEYS,
    )
    audit.check(
        "registration_schema_version_exact",
        isinstance(registration, dict)
        and registration.get("schema_version") == SCHEMA_VERSION,
    )
    audit.check(
        "registration_id_exact",
        isinstance(registration, dict)
        and registration.get("registration_id") == REGISTRATION_ID,
    )
    semantic_digest = (
        sha256_bytes(canonical_json_bytes(registration))
        if isinstance(registration, dict)
        else "FAIL"
    )
    audit.check(
        "registration_canonical_semantic_digest",
        semantic_digest == EXPECTED_REGISTRATION_CANONICAL_SHA256,
    )

    expected_reference_record = {
        "path": REFERENCE_PATH,
        "bytes": EXPECTED_REFERENCE_BYTES,
        "sha256": EXPECTED_REFERENCE_SHA256,
        "binding_mode": "EXACT_BYTES_SHA256",
    }
    audit.check(
        "registration_reference_record_exact",
        isinstance(registration, dict)
        and registration.get("reference_binding") == expected_reference_record,
    )
    expected_authority = {
        "authority_type": "CURRENT_USER_EXPLICIT_ONLY",
        "authority_count": 4,
        "exact_user_authority_strings": AUTHORITY_REQUESTS,
        "provenance": "IN_TURN_DIRECT_USER_MESSAGES_GIT_COMMITTED_REGISTRATION",
        "scope": "KANI_ONLY_FORGE_DESIGN_AND_REGISTRATION",
        "contract_authority": {
            "machine": "HASH_LOCKED_REGISTRATION_AND_RUN_BUNDLE",
            "human_guidance": REFERENCE_PATH,
            "conflict": "HOLD",
            "registration_scope": "INSTALLATION_ONLY",
            "analysis_validation": "NOT_RUN_NO_RUN_BUNDLE",
        },
    }
    audit.check(
        "registration_authority_exact",
        isinstance(registration, dict)
        and registration.get("authority") == expected_authority,
    )
    route_ok = audit.check(
        "registration_route_19_units_57_roles_exact",
        isinstance(registration, dict) and exact_route(registration.get("route")),
    )
    audit.check(
        "registration_route_authority_exact",
        isinstance(registration, dict)
        and isinstance(registration.get("route"), dict)
        and registration["route"].get("route_authority")
        == "RQ_VEDIC_19_LAYER_V1_PROJECT_PROTOCOL_NOT_CLASSICAL_JYOTISH_CANON",
    )
    stage_semantics = (
        registration.get("stage_semantics") if isinstance(registration, dict) else None
    )
    audit.check(
        "registration_public_v3_v4_v5_stage_semantics_exact",
        stage_semantics == EXPECTED_STAGE_SEMANTICS,
    )
    audit.check(
        "registration_bhu_oxford_benchmark_contract_exact",
        isinstance(registration, dict)
        and registration.get("benchmark_contract") == EXPECTED_BENCHMARK_CONTRACT,
    )
    audit.check(
        "registration_run_bundle_roster_exact",
        isinstance(registration, dict)
        and isinstance(registration.get("run_bundle_contract"), dict)
        and type(
            registration["run_bundle_contract"].get("required_artifact_count")
        )
        is int
        and registration["run_bundle_contract"].get("required_artifact_count")
        == len(REQUIRED_RUN_ARTIFACTS)
        and registration["run_bundle_contract"].get("required_artifacts")
        == REQUIRED_RUN_ARTIFACTS,
    )
    audit.check(
        "registration_run_bundle_bindings_exact",
        isinstance(registration, dict)
        and isinstance(registration.get("run_bundle_contract"), dict)
        and registration["run_bundle_contract"].get("required_bindings")
        == REQUIRED_RUN_BINDINGS
        and registration["run_bundle_contract"].get(
            "pikachu_claim_id_completeness"
        )
        == "EXACT_SET_EQUALITY_NOT_COUNT_EQUALITY"
        and registration["run_bundle_contract"].get("review_record")
        == {
            "path": "21_review_record.json",
            "type": "INTERNAL_RUNTIME_REVIEW_NOT_PEER_REVIEW",
        }
        and registration["run_bundle_contract"].get("readiness_authority")
        == "ACTUAL_RUN_VALIDATOR_ONLY"
        and registration["run_bundle_contract"].get(
            "registration_validator_can_promote_readiness"
        )
        is False,
    )
    audit.check(
        "registration_state_separation_exact",
        isinstance(registration, dict)
        and isinstance(registration.get("state_model"), dict)
        and registration["state_model"].get("initial")
        == {
            "registration_state": "INSTALLED_LOCAL_CONTRACT",
            "registration_validation_state": "PENDING_VALIDATOR_EXECUTION",
            "analysis_state": "NOT_RUN",
            "publication_state": "FORBIDDEN",
            "analysis_validation": "NOT_RUN_NO_RUN_BUNDLE",
            "academic_gate": "HOLD_UNEXECUTED",
            "life_congruence_gate": "HOLD_UNEXECUTED",
        }
        and registration["state_model"].get("separation")
        == "REGISTRATION_NEVER_IMPLIES_ANALYSIS"
        and registration["state_model"].get("registration_scope")
        == "INSTALLATION_ONLY"
        and registration["state_model"].get("readiness_authority")
        == "ACTUAL_RUN_VALIDATOR_ONLY"
        and registration["state_model"].get("registration_validator_authority")
        == "REGISTRATION_SHAPE_AND_HASHES_ONLY",
    )
    audit.check(
        "registration_conflict_lock_exact",
        isinstance(registration, dict)
        and isinstance(registration.get("locks"), dict)
        and registration["locks"].get("conflicts")
        == "LOCAL_HOLD_NO_SILENT_RESOLUTION",
    )
    audit.check(
        "registration_claim_contract_exact",
        isinstance(registration, dict)
        and registration.get("claim_contract")
        == {
            "claim_classes": [
                "PRIOR_ANALYSIS",
                "CHART_FACT",
                "METHOD_CLAIM",
                "DERIVED_INFERENCE",
                "LIFE_ALIGNMENT",
                "LIMITATION",
            ],
            "prior_analysis_binding": (
                "BASELINE_PATH_BYTES_SHA256_COMPLETE_CLAIM_ID_SET_AND_DELTA"
            ),
            "claim_citation_binding": "CLAIM_LEVEL_EXACT_LOCATOR",
            "unsupported_state": "HOLD",
        },
    )
    audit.check(
        "registration_life_exposure_contract_exact",
        isinstance(registration, dict)
        and registration.get("life_exposure_contract")
        == {
            "classifications": [
                "BLIND_CONFIRMATORY",
                "RETROSPECTIVE_EXPLANATORY",
                "PROSPECTIVE",
            ],
            "mode_classification_map": {
                "L0_CLOSED": "PROSPECTIVE",
                "L1_POST_FREEZE_BLIND_COMPARE": "BLIND_CONFIRMATORY",
                "L2_POST_FREEZE_USER_CONTEXT": "RETROSPECTIVE_EXPLANATORY",
                "L3_PREEXPOSED_CONTEXT": "RETROSPECTIVE_EXPLANATORY",
            },
            "retrospective_max_state": "PASS_SCOPED",
            "retrospective_forbidden_language": [
                "VALIDATION",
                "PREDICTION",
                "CAUSAL",
            ],
            "log_state": "MANDATORY",
            "roster_state": "APPEND_ONLY_HASH_CHAIN_TOMBSTONES_DEDUP",
            "dedup_key": "EVIDENCE_ID_PLUS_PAYLOAD_SHA256",
            "conflict_state": "HOLD",
        },
    )

    reference_raw = read_regular_bytes(root / REFERENCE_PATH, "reference", audit)
    reference_ok = audit.check(
        "reference_exact_bytes_sha256",
        reference_raw is not None
        and len(reference_raw) == EXPECTED_REFERENCE_BYTES
        and sha256_bytes(reference_raw) == EXPECTED_REFERENCE_SHA256,
    )

    skill_raw = read_regular_bytes(root / SKILL_PATH, "skill", audit)
    skill_ok = False
    if skill_raw is not None:
        try:
            skill_text = skill_raw.decode("utf-8")
        except UnicodeError:
            audit.check("skill_utf8", False)
        else:
            audit.check("skill_utf8", True)
            skill_ok = validate_skill(skill_text, audit)
    else:
        audit.check("skill_utf8", False)

    passed = bool(audit.checks) and all(audit.checks.values())
    report: dict[str, Any] = {
        "schema_version": VALIDATION_SCHEMA,
        "status": "PASS" if passed else "REVISE",
        "registration_id": REGISTRATION_ID,
        "academic_life_forge": (
            "ACTIVE_REGISTERED_HASH_LOCKED"
            if passed
            else "HOLD_REGISTRATION_INVALID"
        ),
        "registration_validation": "PASS" if passed else "FAIL",
        "execution": "NOT_EXECUTED",
        "analysis_validation": "NOT_RUN_NO_RUN_BUNDLE",
        "academic_gate": "HOLD_UNEXECUTED",
        "life_congruence_gate": "HOLD_UNEXECUTED",
        "public_stage_sequence": "V3_V4_V5" if passed else "FAIL",
        "v3_depth": "PIKACHU_FIRST_ANALYSIS_BASELINE" if passed else "FAIL",
        "v4_depth": "UNIVERSITY_THESIS_DEPTH" if passed else "FAIL",
        "v4_benchmark": (
            "BHU_JYOTISH_DOMAIN_PLUS_OXFORD_BA_SANSKRIT_FHS_FIRST_CLASS_WRITING"
            if passed
            else "FAIL"
        ),
        "v5_depth": "CONFERENCE_PRESENTATION_REVIEW_DEPTH" if passed else "FAIL",
        "institutional_endorsement": "NOT_CLAIMED" if passed else "FAIL",
        "route_units": "19/19" if route_ok else "FAIL",
        "logical_roles": "57/57" if route_ok else "FAIL",
        "reference_binding": (
            "PRESENT_HASH_LOCKED" if reference_ok else "FAIL"
        ),
        "skill_route": "PRESENT_CONFLICT_FREE" if skill_ok else "FAIL",
        "registration_semantic_sha256": semantic_digest,
        "checks": audit.checks,
        "errors": audit.errors,
    }
    return report, 0 if passed else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="KANI skill root (defaults to the validator's installed skill root).",
    )
    args = parser.parse_args()
    try:
        report, code = validate(args.root)
    except Exception as error:  # Preserve the one-object stdout contract.
        report = {
            "schema_version": VALIDATION_SCHEMA,
            "status": "REVISE",
            "registration_id": REGISTRATION_ID,
            "academic_life_forge": "HOLD_REGISTRATION_INVALID",
            "registration_validation": "FAIL",
            "execution": "NOT_EXECUTED",
            "analysis_validation": "NOT_RUN_NO_RUN_BUNDLE",
            "academic_gate": "HOLD_UNEXECUTED",
            "life_congruence_gate": "HOLD_UNEXECUTED",
            "public_stage_sequence": "FAIL",
            "v3_depth": "FAIL",
            "v4_depth": "FAIL",
            "v4_benchmark": "FAIL",
            "v5_depth": "FAIL",
            "institutional_endorsement": "FAIL",
            "route_units": "FAIL",
            "logical_roles": "FAIL",
            "reference_binding": "FAIL",
            "skill_route": "FAIL",
            "registration_semantic_sha256": "FAIL",
            "checks": {},
            "errors": [f"validator_internal:{type(error).__name__}"],
        }
        code = 1
    print(
        json.dumps(
            report,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    )
    return code


if __name__ == "__main__":
    sys.exit(main())

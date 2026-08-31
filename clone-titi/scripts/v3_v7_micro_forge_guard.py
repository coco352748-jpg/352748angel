#!/usr/bin/env python3
"""Audit TITI V3-V7 micro-template design and exact reverse-render bundles.

The guard composes the native TITI micro-design and exact reverse-render
auditors.  It adds the RQ R5 stage/joint registry, the 19-cell sentence-joint
packet, four paragraph functions, version isolation, and inter-joint handoff
checks.  It validates declared provenance; it does not manufacture or bless
missing source values.
"""

from __future__ import annotations

import argparse
import copy
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable


CONTRACT = "TITI_V3_V7_MICRO_FORGE_V1"
MODE = "V3_V7_MICRO_FORGE"
OPERATIONS = {"DESIGN_STAGE", "EXACT_STAGE_REVERSE"}
REGISTRY_CONTRACT = "RQ_R5_V3_V7_SENTENCE_JOINT_REGISTRY_V1"

VERSION_ORDER = ("V3", "V4", "V5", "V6", "V7")
STAGE_MAPPING = {
    "V3": "3",
    "V4": "3.5",
    "V5": "4",
    "V6": "4.5",
    "V7": "5",
}
VERSION_LABELS = {
    "V3": "3단계 심층작동결",
    "V4": "3.5단계 심층촘촘결",
    "V5": "4단계 구조통찰결",
    "V6": "4.5단계 심층통찰결",
    "V7": "5단계 법전결",
}

REQUIRED_CELL_FIELDS = (
    "INPUT_REF",
    "PREVIOUS_OUTPUT",
    "GRAMMATICAL_SUBJECT",
    "SUBJECT_ROLE",
    "PREDICATE",
    "DIRECT_OBJECT",
    "ADVERBIAL_METHOD",
    "CONDITION_GATE",
    "PRE_STATE",
    "TRANSFORMATION",
    "POST_STATE",
    "WHY_LINK",
    "HANDOFF_VALUE",
    "NEXT_SUBJECT_OR_FIELD",
    "RESULT_STAGE",
    "RESULT_BOUNDARY",
    "EVIDENCE_GRADE",
    "STATUS",
    "SURFACE_SCAFFOLD",
)

PARAGRAPH_FUNCTIONS = (
    "QUESTION_AND_PREVIOUS_OUTPUT",
    "SUBJECT_VERB_OBJECT_OPERATION",
    "STATE_TRANSFORMATION_AND_WHY",
    "HANDOFF_AND_RESULT_BOUNDARY",
)

# STATUS controls validation and is never required to occupy an exact surface
# span. SURFACE_SCAFFOLD authorizes the template/literals and is likewise not a
# semantic occurrence. The remaining 17 cells are independently reversible
# surface/semantic occurrences.
CONTROL_CELL_FIELDS = ("STATUS",)
TEMPLATE_AUTHORITY_CELL_FIELDS = ("SURFACE_SCAFFOLD",)
SURFACE_SEMANTIC_CELL_FIELDS = tuple(
    field
    for field in REQUIRED_CELL_FIELDS
    if field not in CONTROL_CELL_FIELDS + TEMPLATE_AUTHORITY_CELL_FIELDS
)
# Alias used by the contract prose and downstream integrations.
SEMANTIC_CELLS = SURFACE_SEMANTIC_CELL_FIELDS
CELL_CLASSES = {
    "surface_semantic": list(SURFACE_SEMANTIC_CELL_FIELDS),
    "control": list(CONTROL_CELL_FIELDS),
    "template_authority": list(TEMPLATE_AUTHORITY_CELL_FIELDS),
}
FUNCTION_CELL_MAP = {
    "QUESTION_AND_PREVIOUS_OUTPUT": [
        "INPUT_REF",
        "PREVIOUS_OUTPUT",
        "CONDITION_GATE",
    ],
    "SUBJECT_VERB_OBJECT_OPERATION": [
        "GRAMMATICAL_SUBJECT",
        "SUBJECT_ROLE",
        "PREDICATE",
        "DIRECT_OBJECT",
        "ADVERBIAL_METHOD",
    ],
    "STATE_TRANSFORMATION_AND_WHY": [
        "PRE_STATE",
        "TRANSFORMATION",
        "POST_STATE",
        "WHY_LINK",
        "EVIDENCE_GRADE",
    ],
    "HANDOFF_AND_RESULT_BOUNDARY": [
        "HANDOFF_VALUE",
        "NEXT_SUBJECT_OR_FIELD",
        "RESULT_STAGE",
        "RESULT_BOUNDARY",
    ],
}
V7_LOWER_FIELDS = ("input", "operation", "transformation", "handoff", "result")
CLAIM_SIGNATURE_FIELDS = (
    "SUBJECT_ROLE",
    "PREDICATE",
    "DIRECT_OBJECT",
    "CONDITION_GATE",
    "PRE_STATE",
    "POST_STATE",
    "RESULT_STAGE",
    "RESULT_BOUNDARY",
)

JOINTS: dict[str, tuple[tuple[str, str, str], ...]] = {
    "V3": (
        ("V3.CENTER_OPERATION", "SOURCE_INPUT", "V3.FIELD_INPUT"),
        ("V3.FIELD_INPUT", "V3.CENTER_OPERATION", "V3.OPERATOR_OBJECT"),
        ("V3.OPERATOR_OBJECT", "V3.FIELD_INPUT", "V3.STATE_TRANSFORMATION"),
        ("V3.STATE_TRANSFORMATION", "V3.OPERATOR_OBJECT", "V3.TRANSFER_CHECKPOINT"),
        ("V3.TRANSFER_CHECKPOINT", "V3.STATE_TRANSFORMATION", "V3.RESULT_BOUNDARY"),
        ("V3.RESULT_BOUNDARY", "V3.TRANSFER_CHECKPOINT", "STAGE_OUTPUT"),
    ),
    "V4": (
        ("V4.SOURCE_ALLOWED_ANSWER", "SOURCE_INPUT", "V4.EVIDENCE_PRECONDITION"),
        ("V4.EVIDENCE_PRECONDITION", "V4.SOURCE_ALLOWED_ANSWER", "V4.DEPENDENCY_AUTHORITY"),
        ("V4.DEPENDENCY_AUTHORITY", "V4.EVIDENCE_PRECONDITION", "V4.ROLE_LAYER_STATE_SEPARATION"),
        ("V4.ROLE_LAYER_STATE_SEPARATION", "V4.DEPENDENCY_AUTHORITY", "V4.MECHANISM_RECONNECTION"),
        ("V4.MECHANISM_RECONNECTION", "V4.ROLE_LAYER_STATE_SEPARATION", "V4.MINIMUM_COUNTEREXAMPLE"),
        ("V4.MINIMUM_COUNTEREXAMPLE", "V4.MECHANISM_RECONNECTION", "V4.CONCLUSION_BOUNDARY"),
        ("V4.CONCLUSION_BOUNDARY", "V4.MINIMUM_COUNTEREXAMPLE", "STAGE_OUTPUT"),
    ),
    "V5": (
        ("V5.STRUCTURE_VERDICT", "SOURCE_INPUT", "V5.INPUT_SELECTION"),
        ("V5.INPUT_SELECTION", "V5.STRUCTURE_VERDICT", "V5.OPERATION_TRANSFER"),
        ("V5.OPERATION_TRANSFER", "V5.INPUT_SELECTION", "V5.COMMON_ROOT"),
        ("V5.COMMON_ROOT", "V5.OPERATION_TRANSFER", "V5.CAPABILITY_DISTORTION_BRANCH"),
        ("V5.CAPABILITY_DISTORTION_BRANCH", "V5.COMMON_ROOT", "V5.MINIMUM_TRANSITION"),
        ("V5.MINIMUM_TRANSITION", "V5.CAPABILITY_DISTORTION_BRANCH", "V5.FINAL_STRUCTURE_LOCK"),
        ("V5.FINAL_STRUCTURE_LOCK", "V5.MINIMUM_TRANSITION", "STAGE_OUTPUT"),
    ),
    "V6": (
        ("V6.OUTER_STRUCTURE", "V5_CONFIRMED_STRUCTURE_OR_SOURCE_INPUT", "V6.INNER_GENERATIVE_MECHANISM"),
        ("V6.INNER_GENERATIVE_MECHANISM", "V6.OUTER_STRUCTURE", "V6.DEEPEST_CORE_JOINT"),
        ("V6.DEEPEST_CORE_JOINT", "V6.INNER_GENERATIVE_MECHANISM", "V6.UPWARD_GENERATION_ORDER"),
        ("V6.UPWARD_GENERATION_ORDER", "V6.DEEPEST_CORE_JOINT", "V6.REALITY_TRIGGER"),
        ("V6.REALITY_TRIGGER", "V6.UPWARD_GENERATION_ORDER", "V6.OBSERVABLE_SIGNAL"),
        ("V6.OBSERVABLE_SIGNAL", "V6.REALITY_TRIGGER", "V6.ACTUAL_CHOICE_ACTION"),
        ("V6.ACTUAL_CHOICE_ACTION", "V6.OBSERVABLE_SIGNAL", "V6.REALITY_BRANCH"),
        ("V6.REALITY_BRANCH", "V6.ACTUAL_CHOICE_ACTION", "V6.CONTROL_POINTS_ORDER"),
        ("V6.CONTROL_POINTS_ORDER", "V6.REALITY_BRANCH", "V6.REALITY_AUDIT_COUNTEREXAMPLE"),
        ("V6.REALITY_AUDIT_COUNTEREXAMPLE", "V6.CONTROL_POINTS_ORDER", "V6.DEEPEST_BOUNDARY"),
        ("V6.DEEPEST_BOUNDARY", "V6.REALITY_AUDIT_COUNTEREXAMPLE", "STAGE_OUTPUT"),
    ),
    "V7": (
        ("V7.JURISDICTION", "SOURCE_GROUP_INPUT", "V7.REPEATED_EVIDENCE_INVARIANT"),
        ("V7.REPEATED_EVIDENCE_INVARIANT", "V7.JURISDICTION", "V7.SUPERORDINATE_RULE"),
        ("V7.SUPERORDINATE_RULE", "V7.REPEATED_EVIDENCE_INVARIANT", "V7.APPLICATION_GATE"),
        ("V7.APPLICATION_GATE", "V7.SUPERORDINATE_RULE", "V7.JUDGMENT_PRIORITY"),
        ("V7.JUDGMENT_PRIORITY", "V7.APPLICATION_GATE", "V7.OPERATING_ORDER"),
        ("V7.OPERATING_ORDER", "V7.JUDGMENT_PRIORITY", "V7.EXCEPTION_COUNTEREXAMPLE_PROHIBITION"),
        ("V7.EXCEPTION_COUNTEREXAMPLE_PROHIBITION", "V7.OPERATING_ORDER", "V7.TERMINATION_CODE_LOCK"),
        ("V7.TERMINATION_CODE_LOCK", "V7.EXCEPTION_COUNTEREXAMPLE_PROHIBITION", "STAGE_OUTPUT"),
    ),
}

EXPECTED_COUNTS = {version: len(joints) for version, joints in JOINTS.items()}
EXPECTED_TOTAL = sum(EXPECTED_COUNTS.values())

GATES = (
    "CONTRACT",
    "MODE",
    "OPERATION",
    "REGISTRY_CANON",
    "VERSION_SET_AND_ORDER",
    "VERSION_SEPARATION",
    "JOINT_COUNT",
    "JOINT_ORDER",
    "REQUIRED_CELL_SET",
    "PARAGRAPH_FUNCTIONS",
    "FUNCTION_CELL_PARTITION",
    "NO_DUPLICATE_CLAIM_PADDING",
    "DIRECTED_TRANSFORMATION",
    "HANDOFF_CHAIN",
    "OCCURRENCE_SENTINEL_UNIQUE",
    "HANDOFF_SEMANTIC_LEDGER",
    "HANDOFF_TEST_TOKEN",
    "V6_LAYER_DISTINCT",
    "CELL_BINDING_BOUNDARY",
    "NO_INVENTED_BINDINGS",
    "DESIGN_NO_FALSE_EXACT",
    "NO_FALSE_EXACT_CLAIM",
    "CHILD_NATIVE_AUDIT",
    "EXACT_NATIVE_ROUNDTRIP",
    "V7_TWO_LOWER_STRUCTURES",
    "OUTPUT_VISIBILITY",
    "FNA98_DENSITY",
    "FNA98_RESOLUTION",
    "FNA98_COMPLETENESS",
)

DESIGN_REF_PREFIXES = (
    "SOURCE_REQUIREMENT:",
    "USER_INPUT:",
    "CURRENT_USER:",
    "SOURCE:",
)
EXACT_REF_PREFIXES = ("SOURCE:", "USER_EXACT:", "CURRENT_USER:")
FORBIDDEN_REF_MARKERS = (
    "INFERRED",
    "CONTEXT_GUESS",
    "MODEL_GENERATED",
    "INVENTED",
    "ASSUMED",
)


def load_bundle(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("forge bundle top level must be an object")
    return payload


def _authorized_ref(value: Any, prefixes: tuple[str, ...]) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    upper = value.strip().upper()
    return upper.startswith(prefixes) and not any(
        marker in upper for marker in FORBIDDEN_REF_MARKERS
    )


def _embedded_registry() -> dict[str, Any]:
    return {
        "contract": REGISTRY_CONTRACT,
        "version_mapping": VERSION_LABELS,
        "required_cell_fields": list(REQUIRED_CELL_FIELDS),
        "paragraph_functions": list(PARAGRAPH_FUNCTIONS),
        "versions": {
            version: {
                "stage": STAGE_MAPPING[version],
                "joint_count": EXPECTED_COUNTS[version],
                "joints": [
                    {"uid": uid, "previous": previous, "next": next_uid}
                    for uid, previous, next_uid in JOINTS[version]
                ],
            }
            for version in VERSION_ORDER
        },
        "total_joint_count": EXPECTED_TOTAL,
    }


def _registry_is_exact(payload: Any) -> tuple[bool, list[str]]:
    failures: list[str] = []
    expected = _embedded_registry()
    if not isinstance(payload, dict):
        return False, ["registry_not_object"]
    if payload.get("contract") != REGISTRY_CONTRACT:
        failures.append("contract")
    if payload.get("version_mapping") != VERSION_LABELS:
        failures.append("version_mapping")
    if payload.get("required_cell_fields") != list(REQUIRED_CELL_FIELDS):
        failures.append("required_cell_fields")
    if payload.get("paragraph_functions") != list(PARAGRAPH_FUNCTIONS):
        failures.append("paragraph_functions")
    if payload.get("total_joint_count") != EXPECTED_TOTAL:
        failures.append("total_joint_count")

    versions = payload.get("versions")
    if not isinstance(versions, dict) or list(versions) != list(VERSION_ORDER):
        failures.append("versions")
    else:
        for version in VERSION_ORDER:
            actual = versions.get(version)
            expected_version = expected["versions"][version]
            if not isinstance(actual, dict):
                failures.append(f"{version}:not_object")
                continue
            if actual.get("stage") != expected_version["stage"]:
                failures.append(f"{version}:stage")
            if actual.get("joint_count") != expected_version["joint_count"]:
                failures.append(f"{version}:joint_count")
            actual_joints = actual.get("joints")
            if not isinstance(actual_joints, list):
                failures.append(f"{version}:joints")
                continue
            normalized = [
                {
                    "uid": joint.get("uid"),
                    "previous": joint.get("previous"),
                    "next": joint.get("next"),
                }
                for joint in actual_joints
                if isinstance(joint, dict)
            ]
            if normalized != expected_version["joints"]:
                failures.append(f"{version}:joint_order_or_links")
    return not failures, failures


def _registry_candidates(explicit: Path | None) -> Iterable[Path]:
    if explicit is not None:
        yield explicit
        return
    environment_path = os.environ.get("RQ_R5_REGISTRY")
    if environment_path:
        yield Path(environment_path)
    script_path = Path(__file__).resolve()
    # When integrated as clone-titi/scripts/<this-file>, rq-r5 is a sibling.
    if len(script_path.parents) >= 3:
        yield script_path.parents[2] / "rq-r5/references/R5_JOINT_REGISTRY.json"
    yield Path("/root/.codex/skills/rq-r5/references/R5_JOINT_REGISTRY.json")
    yield Path("/root/.codex/skills/remote-skills/rq-r5/references/R5_JOINT_REGISTRY.json")


def resolve_registry(explicit: Path | None = None) -> dict[str, Any]:
    attempted: list[str] = []
    invalid: list[str] = []
    seen: set[Path] = set()
    for candidate in _registry_candidates(explicit):
        candidate = candidate.expanduser()
        if candidate in seen:
            continue
        seen.add(candidate)
        attempted.append(str(candidate))
        if not candidate.is_file():
            continue
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            invalid.append(f"{candidate}:{type(exc).__name__}")
            continue
        exact, failures = _registry_is_exact(payload)
        if exact:
            return {
                "status": "PASS",
                "authority": "RQ_R5_EXTERNAL_EXACT",
                "path": str(candidate),
                "failures": [],
            }
        invalid.extend(f"{candidate}:{failure}" for failure in failures)

    if explicit is not None:
        return {
            "status": "REVISE",
            "authority": "EXPLICIT_REGISTRY_REJECTED",
            "path": str(explicit),
            "failures": invalid or ["explicit_registry_missing"],
        }
    return {
        "status": "PASS",
        "authority": "EMBEDDED_EXACT_FALLBACK",
        "path": None,
        "attempted": attempted,
        "ignored_invalid_candidates": invalid,
        "failures": [],
    }


def _load_child_guards() -> tuple[Any | None, Any | None, str | None]:
    candidates: list[Path] = [Path(__file__).resolve().parent]
    configured = os.environ.get("TITI_CHILD_GUARD_DIR")
    if configured:
        candidates.append(Path(configured))
    candidates.append(Path("/root/.codex/skills/remote-skills/clone-titi/scripts"))

    for candidate in candidates:
        text = str(candidate)
        if candidate.is_dir() and text not in sys.path:
            sys.path.insert(0, text)
    try:
        design = importlib.import_module("micro_template_design_guard")
        reverse = importlib.import_module("reverse_render_guard")
    except ImportError as exc:
        return None, None, f"{type(exc).__name__}:{exc}"
    return design, reverse, None


def _child_design_audit(
    child: Any,
    cells: dict[str, Any],
    design_module: Any,
) -> tuple[bool, dict[str, Any], list[str]]:
    failures: list[str] = []
    if not isinstance(child, dict):
        return False, {}, ["child_not_object"]
    report = design_module.audit_design_bundle(child)
    if report.get("status") != "PASS":
        failures.append("native_design_revise")

    slots = child.get("slots")
    roles: dict[str, dict[str, Any]] = {}
    if isinstance(slots, list):
        for slot in slots:
            if isinstance(slot, dict) and isinstance(slot.get("semantic_role"), str):
                role = slot["semantic_role"]
                if role in roles:
                    failures.append(f"duplicate_role:{role}")
                roles[role] = slot
    if set(roles) != set(SURFACE_SEMANTIC_CELL_FIELDS):
        failures.append("child_role_set")
    for field in SURFACE_SEMANTIC_CELL_FIELDS:
        cell = cells.get(field)
        slot = roles.get(field)
        if not isinstance(cell, dict) or not isinstance(slot, dict):
            continue
        if slot.get("input_ref") != cell.get("input_ref"):
            failures.append(f"input_ref_mismatch:{field}")
        if slot.get("value_state") != cell.get("value_state"):
            failures.append(f"value_state_mismatch:{field}")
        if slot.get("occurrence_probe") != cell.get("occurrence_probe"):
            failures.append(f"occurrence_probe_mismatch:{field}")
    scaffold = cells.get("SURFACE_SCAFFOLD", {})
    if (
        child.get("template") != scaffold.get("template_ref")
        or child.get("literal_authority_refs") != scaffold.get("literal_authority")
    ):
        failures.append("template_authority_mismatch")
    return not failures, report, failures


def _child_reverse_audit(
    child: Any,
    cells: dict[str, Any],
    reverse_module: Any,
) -> tuple[bool, dict[str, Any], list[str]]:
    failures: list[str] = []
    if not isinstance(child, dict):
        return False, {}, ["child_not_object"]
    report = reverse_module.audit_bundle(child)
    if report.get("status") != "PASS":
        failures.append("native_reverse_revise")

    records = child.get("records")
    record = records[0] if isinstance(records, list) and len(records) == 1 else None
    if not isinstance(record, dict):
        failures.append("child_record_count")
        return False, report, failures
    slots = record.get("slots")
    roles: dict[str, dict[str, Any]] = {}
    if isinstance(slots, list):
        for slot in slots:
            if isinstance(slot, dict) and isinstance(slot.get("semantic_role"), str):
                role = slot["semantic_role"]
                if role in roles:
                    failures.append(f"duplicate_role:{role}")
                roles[role] = slot
    if set(roles) != set(SURFACE_SEMANTIC_CELL_FIELDS):
        failures.append("child_role_set")
    for field in SURFACE_SEMANTIC_CELL_FIELDS:
        cell = cells.get(field)
        slot = roles.get(field)
        if not isinstance(cell, dict) or not isinstance(slot, dict):
            continue
        if slot.get("value") != cell.get("value"):
            failures.append(f"value_mismatch:{field}")
        if slot.get("source_ref") != cell.get("source_ref"):
            failures.append(f"source_ref_mismatch:{field}")
        if slot.get("occurrence_probe") != cell.get("occurrence_probe"):
            failures.append(f"occurrence_probe_mismatch:{field}")
    scaffold = cells.get("SURFACE_SCAFFOLD", {})
    if (
        record.get("template") != scaffold.get("template_ref")
        or child.get("literal_authority_refs") != scaffold.get("literal_authority")
    ):
        failures.append("template_authority_mismatch")
    return not failures, report, failures


def _audit_v7_lower_structures(
    stage: dict[str, Any], operation: str
) -> tuple[bool, list[str]]:
    lower = stage.get("lower_structures")
    if not isinstance(lower, list) or len(lower) < 2:
        return False, ["fewer_than_two"]
    ids: list[str] = []
    refs: list[str] = []
    failures: list[str] = []
    for index, item in enumerate(lower, start=1):
        if not isinstance(item, dict):
            failures.append(f"item_{index}")
            continue
        structure_id = item.get("structure_id")
        independence = item.get("independence_basis")
        if not isinstance(structure_id, str) or not structure_id.strip():
            failures.append(f"id_{index}")
        else:
            ids.append(structure_id)
        if not isinstance(independence, str) or not independence.strip():
            failures.append(f"independence_{index}")
        fields = item.get("fields")
        if not isinstance(fields, dict) or list(fields) != list(V7_LOWER_FIELDS):
            failures.append(f"field_set_{index}")
            continue
        for field_name in V7_LOWER_FIELDS:
            field = fields.get(field_name)
            if not isinstance(field, dict):
                failures.append(f"{field_name}_{index}")
                continue
            if operation == "DESIGN_STAGE":
                ref = field.get("input_ref")
                ok = (
                    _authorized_ref(ref, DESIGN_REF_PREFIXES)
                    and field.get("value_state") in {"UNBOUND", "HOLD"}
                    and field.get("value") in (None, "")
                )
            else:
                ref = field.get("source_ref")
                ok = (
                    _authorized_ref(ref, EXACT_REF_PREFIXES)
                    and isinstance(field.get("value"), str)
                    and bool(field["value"])
                    and field.get("binding_authority") == "SOURCE_EXACT"
                )
            if not ok:
                failures.append(f"binding_{index}:{field_name}")
            if isinstance(ref, str):
                refs.append(ref)
    if len(ids) != len(set(ids)):
        failures.append("duplicate_structure_id")
    if len(refs) != len(lower) * len(V7_LOWER_FIELDS) or len(refs) != len(set(refs)):
        failures.append("lower_structure_source_refs_not_distinct")
    return not failures, failures


def audit_forge_bundle(
    bundle: dict[str, Any], *, registry_path: Path | None = None
) -> dict[str, Any]:
    failures: list[str] = []
    gates = {gate: True for gate in GATES}
    version_reports: list[dict[str, Any]] = []

    def fail(gate: str, detail: str) -> None:
        gates[gate] = False
        failures.append(f"{gate}:{detail}")

    if bundle.get("contract") != CONTRACT:
        fail("CONTRACT", "bundle")
    if bundle.get("mode") != MODE:
        fail("MODE", "bundle")
    operation = bundle.get("operation")
    if operation not in OPERATIONS:
        fail("OPERATION", "bundle")
        operation = "INVALID"

    registry = resolve_registry(registry_path)
    if registry.get("status") != "PASS":
        fail("REGISTRY_CANON", ",".join(registry.get("failures", [])) or "registry")

    if bundle.get("required_cell_fields") != list(REQUIRED_CELL_FIELDS):
        fail("REQUIRED_CELL_SET", "bundle_registry")
    if bundle.get("paragraph_functions") != list(PARAGRAPH_FUNCTIONS):
        fail("PARAGRAPH_FUNCTIONS", "bundle_registry")
    if bundle.get("cell_classes") != CELL_CLASSES:
        fail("REQUIRED_CELL_SET", "cell_classes")
    visibility = bundle.get("output_visibility")
    if visibility != {
        "show_internal_ids": False,
        "show_numbers": False,
        "show_validation_table": False,
        "render_academic_paragraphs": True,
    }:
        fail("OUTPUT_VISIBILITY", "bundle")

    requested = bundle.get("requested_versions")
    versions = bundle.get("versions")
    if not isinstance(requested, list):
        requested = []
    if not isinstance(versions, list):
        versions = []

    actual_version_names = [
        stage.get("version") if isinstance(stage, dict) else None for stage in versions
    ]
    canonical_subset = [version for version in VERSION_ORDER if version in requested]
    version_set_ok = (
        bool(requested)
        and all(version in VERSION_ORDER for version in requested)
        and len(requested) == len(set(requested))
        and requested == canonical_subset
        and actual_version_names == requested
        and len(actual_version_names) == len(set(actual_version_names))
    )
    if not version_set_ok:
        fail("VERSION_SET_AND_ORDER", "bundle")

    expected_total = sum(EXPECTED_COUNTS.get(version, 0) for version in requested)
    actual_total = sum(
        len(stage.get("joints", []))
        for stage in versions
        if isinstance(stage, dict) and isinstance(stage.get("joints"), list)
    )
    if bundle.get("total_joint_count") != expected_total or actual_total != expected_total:
        fail("JOINT_COUNT", f"bundle:{actual_total}/{expected_total}")

    design_module, reverse_module, child_import_error = _load_child_guards()
    if child_import_error:
        fail("CHILD_NATIVE_AUDIT", child_import_error)
        if operation == "EXACT_STAGE_REVERSE":
            fail("EXACT_NATIVE_ROUNDTRIP", child_import_error)

    seen_joint_uids: set[str] = set()
    seen_occurrence_probes: set[str] = set()
    seen_handoff_test_tokens: set[str] = set()
    seen_claim_signatures: dict[tuple[str, ...], str] = {}
    for stage_index, stage in enumerate(versions, start=1):
        stage_start = len(failures)
        child_summaries: list[dict[str, Any]] = []
        if not isinstance(stage, dict):
            fail("VERSION_SEPARATION", f"stage_{stage_index}_not_object")
            continue
        version = stage.get("version")
        if version not in VERSION_ORDER:
            fail("VERSION_SEPARATION", f"stage_{stage_index}:{version}")
            continue
        if stage.get("stage") != STAGE_MAPPING[version]:
            fail("VERSION_SEPARATION", f"{version}:stage_mapping")
        if stage.get("version_label") != VERSION_LABELS[version]:
            fail("VERSION_SEPARATION", f"{version}:version_label")

        if operation == "DESIGN_STAGE":
            if (
                stage.get("binding_authority") != "SOURCE_REQUIREMENTS_ONLY"
                or stage.get("exact_roundtrip_state")
                != "NOT_APPLICABLE_UNTIL_FILLED"
            ):
                fail("DESIGN_NO_FALSE_EXACT", version)
                fail("NO_FALSE_EXACT_CLAIM", version)
        elif operation == "EXACT_STAGE_REVERSE":
            if (
                stage.get("binding_authority") != "SOURCE_EXACT"
                or stage.get("exact_roundtrip_state")
                != "REQUIRES_EXECUTED_AUDIT"
            ):
                fail("CELL_BINDING_BOUNDARY", f"{version}:exact_authority_or_state")
                fail("NO_FALSE_EXACT_CLAIM", version)

        joints = stage.get("joints")
        if not isinstance(joints, list):
            joints = []
        canonical = JOINTS[version]
        actual_uids = [
            joint.get("uid") if isinstance(joint, dict) else None for joint in joints
        ]
        expected_uids = [joint[0] for joint in canonical]
        if len(joints) != EXPECTED_COUNTS[version]:
            fail("JOINT_COUNT", f"{version}:{len(joints)}/{EXPECTED_COUNTS[version]}")
        if actual_uids != expected_uids:
            fail("JOINT_ORDER", version)

        previous_handoff_value: str | None = None
        previous_handoff_test_token: str | None = None
        derived_handoff_ledger: list[dict[str, str]] = []
        for joint_index, joint in enumerate(joints, start=1):
            if not isinstance(joint, dict):
                fail("REQUIRED_CELL_SET", f"{version}:joint_{joint_index}")
                continue
            uid = joint.get("uid")
            if (
                not isinstance(uid, str)
                or not uid.startswith(f"{version}.")
                or uid in seen_joint_uids
            ):
                fail("VERSION_SEPARATION", f"{version}:joint_{joint_index}:{uid}")
            if isinstance(uid, str):
                seen_joint_uids.add(uid)

            expected_joint = canonical[joint_index - 1] if joint_index <= len(canonical) else None
            if expected_joint is None:
                fail("JOINT_ORDER", f"{version}:extra_{joint_index}")
                continue
            expected_uid, expected_previous, expected_next = expected_joint
            if (
                uid != expected_uid
                or joint.get("previous") != expected_previous
                or joint.get("next") != expected_next
            ):
                fail("JOINT_ORDER", f"{version}:joint_{joint_index}_registry")
            if (
                joint.get("previous_link") != f"{expected_previous}->{expected_uid}"
                or joint.get("handoff_link") != f"{expected_uid}->{expected_next}"
            ):
                fail("HANDOFF_CHAIN", f"{expected_uid}:declared_links")
            if joint.get("paragraph_functions") != list(PARAGRAPH_FUNCTIONS):
                fail("PARAGRAPH_FUNCTIONS", expected_uid)
            function_cell_map = joint.get("function_cell_map")
            flattened_function_cells = (
                [
                    field
                    for function in PARAGRAPH_FUNCTIONS
                    for field in function_cell_map.get(function, [])
                ]
                if isinstance(function_cell_map, dict)
                else []
            )
            if (
                function_cell_map != FUNCTION_CELL_MAP
                or len(flattened_function_cells)
                != len(set(flattened_function_cells))
                or set(flattened_function_cells) != set(SEMANTIC_CELLS)
            ):
                fail("FUNCTION_CELL_PARTITION", expected_uid)

            cells = joint.get("cells")
            if not isinstance(cells, dict):
                cells = {}
            if list(cells) != list(REQUIRED_CELL_FIELDS):
                fail("REQUIRED_CELL_SET", expected_uid)

            for field in REQUIRED_CELL_FIELDS:
                cell = cells.get(field)
                if not isinstance(cell, dict):
                    fail("CELL_BINDING_BOUNDARY", f"{expected_uid}:{field}")
                    continue
                if field == "STATUS":
                    expected_control = (
                        "HOLD"
                        if operation == "DESIGN_STAGE"
                        else "REQUIRES_EXECUTED_AUDIT"
                    )
                    if cell != {"control_state": expected_control}:
                        fail("CELL_BINDING_BOUNDARY", f"{expected_uid}:STATUS")
                        fail("NO_FALSE_EXACT_CLAIM", f"{expected_uid}:STATUS")
                    continue
                if field == "SURFACE_SCAFFOLD":
                    literal_authority = cell.get("literal_authority")
                    if (
                        set(cell) != {"template_ref", "literal_authority"}
                        or not isinstance(cell.get("template_ref"), str)
                        or not cell["template_ref"]
                        or not isinstance(literal_authority, list)
                        or not literal_authority
                        or not all(
                            _authorized_ref(ref, DESIGN_REF_PREFIXES)
                            for ref in literal_authority
                        )
                    ):
                        fail("CELL_BINDING_BOUNDARY", f"{expected_uid}:SURFACE_SCAFFOLD")
                        fail("NO_INVENTED_BINDINGS", f"{expected_uid}:SURFACE_SCAFFOLD")
                    continue

                occurrence_probe = cell.get("occurrence_probe")
                if (
                    not isinstance(occurrence_probe, str)
                    or not occurrence_probe
                    or occurrence_probe in seen_occurrence_probes
                ):
                    fail("OCCURRENCE_SENTINEL_UNIQUE", f"{expected_uid}:{field}")
                elif occurrence_probe in seen_handoff_test_tokens:
                    fail("OCCURRENCE_SENTINEL_UNIQUE", f"{expected_uid}:{field}:handoff_collision")
                else:
                    seen_occurrence_probes.add(occurrence_probe)

                if operation == "DESIGN_STAGE":
                    good = (
                        cell.get("binding_authority") == "SOURCE_REQUIREMENT_ONLY"
                        and cell.get("value_state") in {"UNBOUND", "HOLD"}
                        and cell.get("value") in (None, "")
                        and _authorized_ref(cell.get("input_ref"), DESIGN_REF_PREFIXES)
                    )
                    if not good:
                        fail("CELL_BINDING_BOUNDARY", f"{expected_uid}:{field}:design")
                        fail("NO_INVENTED_BINDINGS", f"{expected_uid}:{field}")
                    if cell.get("value") not in (None, ""):
                        fail("DESIGN_NO_FALSE_EXACT", f"{expected_uid}:{field}:bound")
                        fail("NO_FALSE_EXACT_CLAIM", f"{expected_uid}:{field}:bound")
                elif operation == "EXACT_STAGE_REVERSE":
                    good = (
                        cell.get("binding_authority") == "SOURCE_EXACT"
                        and isinstance(cell.get("value"), str)
                        and bool(cell["value"])
                        and _authorized_ref(cell.get("source_ref"), EXACT_REF_PREFIXES)
                    )
                    if not good:
                        fail("CELL_BINDING_BOUNDARY", f"{expected_uid}:{field}:exact")
                        fail("NO_INVENTED_BINDINGS", f"{expected_uid}:{field}")

            signature_key = "input_ref" if operation == "DESIGN_STAGE" else "value"
            signature = tuple(
                str(cells.get(field, {}).get(signature_key, ""))
                if isinstance(cells.get(field), dict)
                else ""
                for field in CLAIM_SIGNATURE_FIELDS
            )
            if all(signature):
                prior_uid = seen_claim_signatures.get(signature)
                if prior_uid is not None:
                    fail(
                        "NO_DUPLICATE_CLAIM_PADDING",
                        f"{expected_uid}=duplicate_of:{prior_uid}",
                    )
                else:
                    seen_claim_signatures[signature] = expected_uid

            pre_cell = cells.get("PRE_STATE", {})
            post_cell = cells.get("POST_STATE", {})
            transformation_cell = cells.get("TRANSFORMATION", {})
            if operation == "DESIGN_STAGE":
                directed_values = (
                    pre_cell.get("input_ref"),
                    post_cell.get("input_ref"),
                    transformation_cell.get("input_ref"),
                )
            else:
                directed_values = (
                    (pre_cell.get("source_ref"), pre_cell.get("value")),
                    (post_cell.get("source_ref"), post_cell.get("value")),
                    (
                        transformation_cell.get("source_ref"),
                        transformation_cell.get("value"),
                    ),
                )
            if (
                any(value in (None, "", (None, None)) for value in directed_values)
                or len(set(directed_values)) != 3
            ):
                fail("DIRECTED_TRANSFORMATION", expected_uid)

            previous_cell = cells.get("PREVIOUS_OUTPUT", {})
            handoff_cell = cells.get("HANDOFF_VALUE", {})
            if (
                not isinstance(previous_cell, dict)
                or previous_cell.get("link_ref") != expected_previous
                or not isinstance(handoff_cell, dict)
                or handoff_cell.get("link_ref") != expected_next
            ):
                fail("HANDOFF_CHAIN", f"{expected_uid}:cell_links")

            previous_token = previous_cell.get("handoff_test_token")
            handoff_token = handoff_cell.get("handoff_test_token")
            if (
                not isinstance(previous_token, str)
                or not previous_token
                or not isinstance(handoff_token, str)
                or not handoff_token
                or previous_token in seen_occurrence_probes
                or handoff_token in seen_occurrence_probes
            ):
                fail("HANDOFF_TEST_TOKEN", f"{expected_uid}:missing_or_occurrence_collision")
            if joint_index > 1:
                if previous_token != previous_handoff_test_token:
                    fail("HANDOFF_TEST_TOKEN", f"{expected_uid}:token_discontinuity")
                    fail("HANDOFF_SEMANTIC_LEDGER", f"{expected_uid}:token_discontinuity")
                producer_uid = canonical[joint_index - 2][0]
                derived_handoff_ledger.append(
                    {
                        "handoff_test_token": str(previous_token),
                        "producer": f"{producer_uid}.HANDOFF_VALUE",
                        "consumer": f"{expected_uid}.PREVIOUS_OUTPUT",
                    }
                )
                if isinstance(previous_token, str):
                    if previous_token in seen_handoff_test_tokens:
                        fail("HANDOFF_TEST_TOKEN", f"{expected_uid}:edge_token_reused")
                    seen_handoff_test_tokens.add(previous_token)
            previous_handoff_test_token = (
                handoff_token if isinstance(handoff_token, str) else None
            )

            if operation == "EXACT_STAGE_REVERSE":
                current_previous = previous_cell.get("value")
                current_handoff = handoff_cell.get("value")
                if joint_index > 1 and current_previous != previous_handoff_value:
                    fail("HANDOFF_CHAIN", f"{expected_uid}:value_discontinuity")
                previous_handoff_value = (
                    current_handoff if isinstance(current_handoff, str) else None
                )

            child = joint.get("child_bundle")
            child_report: dict[str, Any] = {}
            child_failures: list[str] = []
            child_ok = False
            if operation == "DESIGN_STAGE" and design_module is not None:
                child_ok, child_report, child_failures = _child_design_audit(
                    child, cells, design_module
                )
            elif operation == "EXACT_STAGE_REVERSE" and reverse_module is not None:
                child_ok, child_report, child_failures = _child_reverse_audit(
                    child, cells, reverse_module
                )
            if not child_ok:
                fail(
                    "CHILD_NATIVE_AUDIT",
                    f"{expected_uid}:{','.join(child_failures) or 'unavailable'}",
                )
                if operation == "EXACT_STAGE_REVERSE":
                    fail("EXACT_NATIVE_ROUNDTRIP", expected_uid)
            child_summaries.append(
                {
                    "uid": expected_uid,
                    "status": "PASS" if child_ok else "REVISE",
                    "native_status": child_report.get("status"),
                    "failures": child_failures,
                }
            )

        if stage.get("handoff_test_ledger") != derived_handoff_ledger:
            fail("HANDOFF_SEMANTIC_LEDGER", f"{version}:ledger")

        if version == "V6" and len(joints) >= 3:
            inner_cells = joints[1].get("cells", {}) if isinstance(joints[1], dict) else {}
            deep_cells = joints[2].get("cells", {}) if isinstance(joints[2], dict) else {}
            distinct_fields = (
                "GRAMMATICAL_SUBJECT",
                "DIRECT_OBJECT",
                "TRANSFORMATION",
                "HANDOFF_VALUE",
            )
            if operation == "DESIGN_STAGE":
                same_all = all(
                    isinstance(inner_cells.get(field), dict)
                    and isinstance(deep_cells.get(field), dict)
                    and inner_cells[field].get("input_ref")
                    == deep_cells[field].get("input_ref")
                    for field in distinct_fields
                )
            else:
                same_all = all(
                    isinstance(inner_cells.get(field), dict)
                    and isinstance(deep_cells.get(field), dict)
                    and (
                        inner_cells[field].get("source_ref"),
                        inner_cells[field].get("value"),
                    )
                    == (
                        deep_cells[field].get("source_ref"),
                        deep_cells[field].get("value"),
                    )
                    for field in distinct_fields
                )
            if same_all:
                fail("V6_LAYER_DISTINCT", "V6.INNER_GENERATIVE_MECHANISM=V6.DEEPEST_CORE_JOINT")

        if version == "V7":
            v7_ok, v7_failures = _audit_v7_lower_structures(stage, operation)
            if not v7_ok:
                fail("V7_TWO_LOWER_STRUCTURES", ",".join(v7_failures))

        stage_failures = failures[stage_start:]
        version_reports.append(
            {
                "version": version,
                "stage": STAGE_MAPPING[version],
                "status": "PASS" if not stage_failures else "REVISE",
                "joint_count": len(joints),
                "expected_joint_count": EXPECTED_COUNTS[version],
                "child_audits": child_summaries,
                "failures": stage_failures,
            }
        )

    density_ok = all(
        gates[gate]
        for gate in (
            "JOINT_COUNT",
            "REQUIRED_CELL_SET",
            "PARAGRAPH_FUNCTIONS",
            "FUNCTION_CELL_PARTITION",
            "NO_DUPLICATE_CLAIM_PADDING",
        )
    )
    resolution_ok = all(
        gates[gate]
        for gate in (
            "REGISTRY_CANON",
            "VERSION_SET_AND_ORDER",
            "VERSION_SEPARATION",
            "JOINT_ORDER",
            "OCCURRENCE_SENTINEL_UNIQUE",
            "DIRECTED_TRANSFORMATION",
            "V6_LAYER_DISTINCT",
            "V7_TWO_LOWER_STRUCTURES",
        )
    )
    completeness_gates = [
        "CONTRACT",
        "MODE",
        "OPERATION",
        "HANDOFF_CHAIN",
        "HANDOFF_TEST_TOKEN",
        "HANDOFF_SEMANTIC_LEDGER",
        "CELL_BINDING_BOUNDARY",
        "NO_INVENTED_BINDINGS",
        "CHILD_NATIVE_AUDIT",
        "OUTPUT_VISIBILITY",
        "NO_FALSE_EXACT_CLAIM",
    ]
    if operation == "DESIGN_STAGE":
        completeness_gates.append("DESIGN_NO_FALSE_EXACT")
    elif operation == "EXACT_STAGE_REVERSE":
        completeness_gates.append("EXACT_NATIVE_ROUNDTRIP")
    completeness_ok = all(gates[gate] for gate in completeness_gates)

    for gate, ok in (
        ("FNA98_DENSITY", density_ok),
        ("FNA98_RESOLUTION", resolution_ok),
        ("FNA98_COMPLETENESS", completeness_ok),
    ):
        if not ok:
            gates[gate] = False
            failures.append(f"{gate}:derived")

    if density_ok and resolution_ok and completeness_ok:
        fna98_verdict = (
            "FNA98_DESIGN_READY"
            if operation == "DESIGN_STAGE"
            else "FNA98_SENTENCE_PASS"
        )
    else:
        fna98_verdict = "FNA98_REVISE"

    return {
        "contract": CONTRACT,
        "status": "PASS" if not failures else "REVISE",
        "mode": MODE,
        "operation": operation,
        "registry": registry,
        "requested_versions": requested,
        "version_count": len(versions),
        "joint_count": actual_total,
        "expected_joint_count": expected_total,
        "gates": gates,
        "fna98_quality": {
            "density": "PASS" if density_ok else "REVISE",
            "resolution": "PASS" if resolution_ok else "REVISE",
            "completeness": "PASS" if completeness_ok else "REVISE",
            "verdict": fna98_verdict,
        },
        "fna98_basis": {
            "input_schema": {
                "required_cells": len(REQUIRED_CELL_FIELDS),
                "semantic_surface_cells": len(SEMANTIC_CELLS),
                "control_cells": list(CONTROL_CELL_FIELDS),
                "template_authority_cells": list(TEMPLATE_AUTHORITY_CELL_FIELDS),
                "paragraph_functions": len(PARAGRAPH_FUNCTIONS),
            },
            "density_formula": "JOINT_COUNT & REQUIRED_CELL_SET & PARAGRAPH_FUNCTIONS & FUNCTION_CELL_PARTITION & NO_DUPLICATE_CLAIM_PADDING",
            "resolution_formula": "REGISTRY_CANON & VERSION_SET_AND_ORDER & VERSION_SEPARATION & JOINT_ORDER & OCCURRENCE_SENTINEL_UNIQUE & DIRECTED_TRANSFORMATION & V6_LAYER_DISTINCT & V7_TWO_LOWER_STRUCTURES",
            "completeness_formula": "CONTRACT & MODE & OPERATION & HANDOFF_CHAIN & HANDOFF_TEST_TOKEN & HANDOFF_SEMANTIC_LEDGER & CELL_BINDING_BOUNDARY & NO_INVENTED_BINDINGS & CHILD_NATIVE_AUDIT & OUTPUT_VISIBILITY & NO_FALSE_EXACT_CLAIM & operation_native_gate",
            "declared_quality_values_trusted": False,
        },
        "versions": version_reports,
        "failures": failures,
    }


def _literal_template(slot_uids: list[str]) -> str:
    pieces: list[str] = []
    for index, (field, slot_uid) in enumerate(
        zip(SEMANTIC_CELLS, slot_uids, strict=True)
    ):
        if index:
            pieces.append(" | ")
        pieces.append(f"[{field}]=《{slot_uid}》")
    pieces.append(".")
    return "".join(pieces)


def _design_child(
    version: str, joint_number: int, cells: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    template_id = f"T_{version}_{joint_number:02d}"
    slot_uids = [f"{template_id}.{field}.01" for field in SEMANTIC_CELLS]
    slots: list[dict[str, Any]] = []
    for index, (field, uid) in enumerate(
        zip(SEMANTIC_CELLS, slot_uids, strict=True)
    ):
        slots.append(
            {
                "uid": uid,
                "type": "TEXT",
                "semantic_role": field,
                "required": True,
                "input_ref": cells[field]["input_ref"],
                "operator": "INSERT_EXACT",
                "transformation": "NONE",
                "handoff": slot_uids[index + 1]
                if index + 1 < len(slot_uids)
                else "OUTPUT",
                "result_boundary": f"defines_{field.lower()}_only",
                "value_state": cells[field]["value_state"],
                "occurrence_probe": cells[field]["occurrence_probe"],
            }
        )
    literal_authority_refs = [
        f"CURRENT_USER:{template_id}:literal:{index}"
        for index in range(1, len(SEMANTIC_CELLS) + 2)
    ]
    template = _literal_template(slot_uids)
    return {
        "contract": "TITI_MICRO_TEMPLATE_DESIGN_V1",
        "mode": "MICRO_TEMPLATE_DESIGN",
        "validation_mode": "STRUCTURAL_DESIGN",
        "exact_roundtrip_state": "NOT_APPLICABLE_UNTIL_FILLED",
        "template_id": template_id,
        "target": f"Design the complete {version} joint {joint_number} packet",
        "required_roles": list(SEMANTIC_CELLS),
        "template": template,
        "literal_authority_refs": literal_authority_refs,
        "slots": slots,
        "output_contract": {
            "output_type": "ACADEMIC_PARAGRAPH",
            "required_format": "FOUR_FUNCTION_NON_COMPRESSED",
            "missing_value_policy": "HOLD_SLOT",
            "completion_rule": "ALL_REQUIRED_SLOTS_BOUND",
        },
    }


def _exact_child(
    version: str, joint_number: int, cells: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    record_id = f"R_{version}_{joint_number:02d}"
    slot_uids = [f"{record_id}.{field}.01" for field in SEMANTIC_CELLS]
    template = _literal_template(slot_uids)
    slots: list[dict[str, Any]] = []
    sentence = template
    for field, uid in zip(SEMANTIC_CELLS, slot_uids, strict=True):
        value = cells[field]["value"]
        sentence = sentence.replace(f"《{uid}》", value, 1)
        slots.append(
            {
                "uid": uid,
                "type": "TEXT",
                "semantic_role": field,
                "value": value,
                "source_ref": cells[field]["source_ref"],
                "occurrence_probe": cells[field]["occurrence_probe"],
            }
        )
    literal_authority_refs = [
        f"CURRENT_USER:{record_id}:literal:{index}"
        for index in range(1, len(SEMANTIC_CELLS) + 2)
    ]
    return {
        "contract": "TITI_MICRO_ROUNDTRIP_V1",
        "equality_mode": "EXACT_SURFACE",
        "literal_authority_refs": literal_authority_refs,
        "records": [
            {
                "id": record_id,
                "sentence": sentence,
                "template": template,
                "slots": slots,
            }
        ],
    }


def _sample_stage(version: str, operation: str) -> dict[str, Any]:
    stage_joints: list[dict[str, Any]] = []
    previous_handoff = f"{version}_SOURCE_STAGE_INPUT"
    previous_test_token = f"HT::{version}::SOURCE"
    handoff_test_ledger: list[dict[str, str]] = []
    for joint_number, (uid, previous, next_uid) in enumerate(
        JOINTS[version], start=1
    ):
        cells: dict[str, dict[str, Any]] = {}
        next_handoff = f"{version}_HANDOFF_{joint_number:02d}"
        next_test_token = f"HT::{version}::{joint_number:02d}"
        for field in REQUIRED_CELL_FIELDS:
            if field == "STATUS":
                cells[field] = {
                    "control_state": "HOLD"
                    if operation == "DESIGN_STAGE"
                    else "REQUIRES_EXECUTED_AUDIT"
                }
            elif field == "SURFACE_SCAFFOLD":
                # Filled from the child bundle below; it never becomes a slot.
                cells[field] = {"template_ref": "PENDING", "literal_authority": []}
            elif operation == "DESIGN_STAGE":
                cells[field] = {
                    "input_ref": f"SOURCE_REQUIREMENT:{uid}:{field}",
                    "value_state": "UNBOUND",
                    "binding_authority": "SOURCE_REQUIREMENT_ONLY",
                    "occurrence_probe": f"OCC::{version}::{joint_number:02d}::{field}",
                }
            else:
                value = f"{version}_{joint_number:02d}_{field}_VALUE"
                if field == "PREVIOUS_OUTPUT":
                    value = previous_handoff
                elif field == "HANDOFF_VALUE":
                    value = next_handoff
                cells[field] = {
                    "value": value,
                    "source_ref": f"SOURCE:{uid}:{field}",
                    "binding_authority": "SOURCE_EXACT",
                    "occurrence_probe": f"OCC::{version}::{joint_number:02d}::{field}",
                }
        cells["PREVIOUS_OUTPUT"]["link_ref"] = previous
        cells["HANDOFF_VALUE"]["link_ref"] = next_uid
        cells["PREVIOUS_OUTPUT"]["handoff_test_token"] = previous_test_token
        cells["HANDOFF_VALUE"]["handoff_test_token"] = next_test_token
        child = (
            _design_child(version, joint_number, cells)
            if operation == "DESIGN_STAGE"
            else _exact_child(version, joint_number, cells)
        )
        child_template = (
            child["template"]
            if operation == "DESIGN_STAGE"
            else child["records"][0]["template"]
        )
        cells["SURFACE_SCAFFOLD"] = {
            "template_ref": child_template,
            "literal_authority": child["literal_authority_refs"],
        }
        stage_joints.append(
            {
                "uid": uid,
                "previous": previous,
                "next": next_uid,
                "previous_link": f"{previous}->{uid}",
                "handoff_link": f"{uid}->{next_uid}",
                "paragraph_functions": list(PARAGRAPH_FUNCTIONS),
                "function_cell_map": copy.deepcopy(FUNCTION_CELL_MAP),
                "cells": cells,
                "child_bundle": child,
            }
        )
        if joint_number > 1:
            producer_uid = JOINTS[version][joint_number - 2][0]
            handoff_test_ledger.append(
                {
                    "handoff_test_token": previous_test_token,
                    "producer": f"{producer_uid}.HANDOFF_VALUE",
                    "consumer": f"{uid}.PREVIOUS_OUTPUT",
                }
            )
        previous_handoff = next_handoff
        previous_test_token = next_test_token

    stage: dict[str, Any] = {
        "version": version,
        "stage": STAGE_MAPPING[version],
        "version_label": VERSION_LABELS[version],
        "binding_authority": "SOURCE_REQUIREMENTS_ONLY"
        if operation == "DESIGN_STAGE"
        else "SOURCE_EXACT",
        "exact_roundtrip_state": "NOT_APPLICABLE_UNTIL_FILLED"
        if operation == "DESIGN_STAGE"
        else "REQUIRES_EXECUTED_AUDIT",
        "handoff_test_ledger": handoff_test_ledger,
        "joints": stage_joints,
    }
    if version == "V7":
        stage["lower_structures"] = []
        for suffix in ("A", "B"):
            lower_fields: dict[str, dict[str, Any]] = {}
            for lower_field in V7_LOWER_FIELDS:
                if operation == "DESIGN_STAGE":
                    lower_fields[lower_field] = {
                        "input_ref": f"SOURCE_REQUIREMENT:V7:LOWER_{suffix}:{lower_field}",
                        "value_state": "UNBOUND",
                    }
                else:
                    lower_fields[lower_field] = {
                        "value": f"LOWER_{suffix}_{lower_field.upper()}_EXACT_VALUE",
                        "source_ref": f"SOURCE:V7:LOWER_{suffix}:{lower_field}",
                        "binding_authority": "SOURCE_EXACT",
                    }
            stage["lower_structures"].append(
                {
                    "structure_id": f"LOWER_STRUCTURE_{suffix}",
                    "independence_basis": f"independent_source_and_operation_chain_{suffix}",
                    "fields": lower_fields,
                }
            )
    return stage


def sample_bundle(
    operation: str = "DESIGN_STAGE", versions: Iterable[str] = VERSION_ORDER
) -> dict[str, Any]:
    selected = list(versions)
    if operation not in OPERATIONS:
        raise ValueError(f"unsupported sample operation: {operation}")
    return {
        "contract": CONTRACT,
        "mode": MODE,
        "operation": operation,
        "requested_versions": selected,
        "required_cell_fields": list(REQUIRED_CELL_FIELDS),
        "cell_classes": copy.deepcopy(CELL_CLASSES),
        "paragraph_functions": list(PARAGRAPH_FUNCTIONS),
        "output_visibility": {
            "show_internal_ids": False,
            "show_numbers": False,
            "show_validation_table": False,
            "render_academic_paragraphs": True,
        },
        "total_joint_count": sum(EXPECTED_COUNTS[version] for version in selected),
        "versions": [_sample_stage(version, operation) for version in selected],
    }


def self_test(*, registry_path: Path | None = None) -> dict[str, Any]:
    design = sample_bundle("DESIGN_STAGE")
    exact = sample_bundle("EXACT_STAGE_REVERSE")
    design_report = audit_forge_bundle(design, registry_path=registry_path)
    exact_report = audit_forge_bundle(exact, registry_path=registry_path)

    coverage = {
        f"DESIGN_STAGE:{item['version']}": item["status"]
        for item in design_report.get("versions", [])
    }
    coverage.update(
        {
            f"EXACT_STAGE_REVERSE:{item['version']}": item["status"]
            for item in exact_report.get("versions", [])
        }
    )

    cases: dict[str, tuple[dict[str, Any], str]] = {}

    wrong_order = sample_bundle("DESIGN_STAGE", ["V3"])
    wrong_order["versions"][0]["joints"][0], wrong_order["versions"][0]["joints"][1] = (
        wrong_order["versions"][0]["joints"][1],
        wrong_order["versions"][0]["joints"][0],
    )
    cases["wrong_joint_order"] = (wrong_order, "JOINT_ORDER")

    missing_cell = sample_bundle("DESIGN_STAGE", ["V3"])
    missing_cell["versions"][0]["joints"][0]["cells"].pop("WHY_LINK")
    cases["missing_required_cell"] = (missing_cell, "REQUIRED_CELL_SET")

    bad_functions = sample_bundle("DESIGN_STAGE", ["V4"])
    bad_functions["versions"][0]["joints"][0]["paragraph_functions"].pop()
    cases["missing_paragraph_function"] = (bad_functions, "PARAGRAPH_FUNCTIONS")

    bad_chain = sample_bundle("EXACT_STAGE_REVERSE", ["V5"])
    bad_chain["versions"][0]["joints"][1]["cells"]["PREVIOUS_OUTPUT"]["value"] = "BROKEN_LINK"
    cases["broken_handoff_value"] = (bad_chain, "HANDOFF_CHAIN")

    bound_design = sample_bundle("DESIGN_STAGE", ["V6"])
    bound_design["versions"][0]["joints"][0]["cells"]["INPUT_REF"]["value"] = "INVENTED"
    cases["bound_value_in_design"] = (bound_design, "DESIGN_NO_FALSE_EXACT")

    false_exact = sample_bundle("DESIGN_STAGE", ["V3"])
    false_exact["versions"][0]["exact_roundtrip_state"] = "PASS"
    cases["false_design_exact_claim"] = (false_exact, "DESIGN_NO_FALSE_EXACT")

    changed_sentence = sample_bundle("EXACT_STAGE_REVERSE", ["V4"])
    changed_sentence["versions"][0]["joints"][0]["child_bundle"]["records"][0]["sentence"] += "변조"
    cases["exact_reverse_mutation"] = (changed_sentence, "EXACT_NATIVE_ROUNDTRIP")

    inferred_binding = sample_bundle("EXACT_STAGE_REVERSE", ["V6"])
    inferred_binding["versions"][0]["joints"][0]["cells"]["INPUT_REF"]["source_ref"] = "MODEL_INFERRED:x"
    inferred_binding["versions"][0]["joints"][0]["child_bundle"]["records"][0]["slots"][0]["source_ref"] = "MODEL_INFERRED:x"
    cases["inferred_exact_binding"] = (inferred_binding, "NO_INVENTED_BINDINGS")

    v7_single = sample_bundle("DESIGN_STAGE", ["V7"])
    v7_single["versions"][0]["lower_structures"].pop()
    cases["v7_single_lower_structure"] = (v7_single, "V7_TWO_LOWER_STRUCTURES")

    mixed_version = sample_bundle("DESIGN_STAGE", ["V3"])
    mixed_version["versions"][0]["joints"][0]["uid"] = "V4.SOURCE_ALLOWED_ANSWER"
    cases["mixed_version_joint"] = (mixed_version, "VERSION_SEPARATION")

    bad_partition = sample_bundle("DESIGN_STAGE", ["V3"])
    bad_partition["versions"][0]["joints"][0]["function_cell_map"][
        "QUESTION_AND_PREVIOUS_OUTPUT"
    ].append("DIRECT_OBJECT")
    cases["function_cells_not_exact_partition"] = (
        bad_partition,
        "FUNCTION_CELL_PARTITION",
    )

    duplicate_occurrence = sample_bundle("DESIGN_STAGE", ["V3"])
    first_joint = duplicate_occurrence["versions"][0]["joints"][0]
    duplicate_probe = first_joint["cells"]["INPUT_REF"]["occurrence_probe"]
    first_joint["cells"]["PREVIOUS_OUTPUT"]["occurrence_probe"] = duplicate_probe
    first_joint["child_bundle"]["slots"][1]["occurrence_probe"] = duplicate_probe
    cases["duplicate_occurrence_sentinel"] = (
        duplicate_occurrence,
        "OCCURRENCE_SENTINEL_UNIQUE",
    )

    token_mismatch = sample_bundle("DESIGN_STAGE", ["V4"])
    token_mismatch["versions"][0]["joints"][1]["cells"]["PREVIOUS_OUTPUT"][
        "handoff_test_token"
    ] = "HT::BROKEN"
    cases["handoff_test_token_discontinuity"] = (
        token_mismatch,
        "HANDOFF_TEST_TOKEN",
    )

    v6_same_layer = sample_bundle("DESIGN_STAGE", ["V6"])
    inner = v6_same_layer["versions"][0]["joints"][1]
    deep = v6_same_layer["versions"][0]["joints"][2]
    v6_distinct_fields = (
        "GRAMMATICAL_SUBJECT",
        "DIRECT_OBJECT",
        "TRANSFORMATION",
        "HANDOFF_VALUE",
    )
    deep_slots = {
        slot["semantic_role"]: slot for slot in deep["child_bundle"]["slots"]
    }
    for field in v6_distinct_fields:
        deep["cells"][field]["input_ref"] = inner["cells"][field]["input_ref"]
        deep_slots[field]["input_ref"] = inner["cells"][field]["input_ref"]
    cases["v6_inner_and_deep_layers_collapsed"] = (
        v6_same_layer,
        "V6_LAYER_DISTINCT",
    )

    exact_false_claim = sample_bundle("EXACT_STAGE_REVERSE", ["V3"])
    exact_false_claim["versions"][0]["exact_roundtrip_state"] = "PASS"
    cases["exact_input_claims_pass_before_audit"] = (
        exact_false_claim,
        "NO_FALSE_EXACT_CLAIM",
    )

    v7_duplicate_source = sample_bundle("EXACT_STAGE_REVERSE", ["V7"])
    v7_lower = v7_duplicate_source["versions"][0]["lower_structures"]
    v7_lower[1]["fields"]["input"]["source_ref"] = v7_lower[0]["fields"]["input"]["source_ref"]
    cases["v7_lower_source_ref_not_distinct"] = (
        v7_duplicate_source,
        "V7_TWO_LOWER_STRUCTURES",
    )

    duplicate_claim = sample_bundle("DESIGN_STAGE", ["V3"])
    claim_source = duplicate_claim["versions"][0]["joints"][0]
    claim_clone = duplicate_claim["versions"][0]["joints"][1]
    clone_slots = {
        slot["semantic_role"]: slot for slot in claim_clone["child_bundle"]["slots"]
    }
    for field in CLAIM_SIGNATURE_FIELDS:
        claim_clone["cells"][field]["input_ref"] = claim_source["cells"][field]["input_ref"]
        clone_slots[field]["input_ref"] = claim_source["cells"][field]["input_ref"]
    cases["duplicate_claim_signature_padding"] = (
        duplicate_claim,
        "NO_DUPLICATE_CLAIM_PADDING",
    )

    undirected = sample_bundle("DESIGN_STAGE", ["V4"])
    undirected_joint = undirected["versions"][0]["joints"][0]
    undirected_joint["cells"]["POST_STATE"]["input_ref"] = undirected_joint[
        "cells"
    ]["PRE_STATE"]["input_ref"]
    undirected_slots = {
        slot["semantic_role"]: slot
        for slot in undirected_joint["child_bundle"]["slots"]
    }
    undirected_slots["POST_STATE"]["input_ref"] = undirected_joint["cells"][
        "PRE_STATE"
    ]["input_ref"]
    cases["pre_state_equals_post_state"] = (
        undirected,
        "DIRECTED_TRANSFORMATION",
    )

    fna_density = sample_bundle("DESIGN_STAGE", ["V3"])
    fna_density["versions"][0]["joints"][0]["cells"].pop("DIRECT_OBJECT")
    cases["fna98_density_rejects_sparse_packet"] = (fna_density, "FNA98_DENSITY")

    fna_resolution = sample_bundle("DESIGN_STAGE", ["V3"])
    fna_resolution["versions"][0]["joints"].reverse()
    cases["fna98_resolution_rejects_wrong_joint_order"] = (
        fna_resolution,
        "FNA98_RESOLUTION",
    )

    fna_completeness = sample_bundle("EXACT_STAGE_REVERSE", ["V3"])
    fna_completeness["output_visibility"]["show_internal_ids"] = True
    cases["fna98_completeness_rejects_visible_internal_ids"] = (
        fna_completeness,
        "FNA98_COMPLETENESS",
    )

    invalid_reports: dict[str, dict[str, Any]] = {}
    failures: list[str] = []
    if design_report.get("status") != "PASS":
        failures.append("valid_design_all_versions")
    if exact_report.get("status") != "PASS":
        failures.append("valid_exact_all_versions")
    if design_report.get("fna98_quality", {}).get("verdict") != "FNA98_DESIGN_READY":
        failures.append("valid_design_fna98_ready")
    if design_report.get("fna98_quality", {}).get("verdict") == "FNA98_SENTENCE_PASS":
        failures.append("design_false_fna98_sentence_pass")
    if exact_report.get("fna98_quality", {}).get("verdict") != "FNA98_SENTENCE_PASS":
        failures.append("valid_exact_fna98_sentence_pass")
    expected_coverage = {
        f"{operation}:{version}"
        for operation in ("DESIGN_STAGE", "EXACT_STAGE_REVERSE")
        for version in VERSION_ORDER
    }
    if set(coverage) != expected_coverage or set(coverage.values()) != {"PASS"}:
        failures.append("all_five_stage_coverage")

    for name, (case, expected_gate) in cases.items():
        report = audit_forge_bundle(case, registry_path=registry_path)
        detected = (
            report.get("status") == "REVISE"
            and report.get("gates", {}).get(expected_gate) is False
        )
        invalid_reports[name] = {
            "status": report.get("status"),
            "expected_gate": expected_gate,
            "detected": detected,
        }
        if not detected:
            failures.append(name)

    return {
        "contract": "TITI_V3_V7_MICRO_FORGE_SELF_TEST_V1",
        "status": "PASS" if not failures else "REVISE",
        "expected_joint_counts": EXPECTED_COUNTS,
        "expected_total_joint_count": EXPECTED_TOTAL,
        "all_stage_coverage": coverage,
        "valid_design_status": design_report.get("status"),
        "valid_exact_status": exact_report.get("status"),
        "valid_design_fna98": design_report.get("fna98_quality"),
        "valid_exact_fna98": exact_report.get("fna98_quality"),
        "negative_cases": invalid_reports,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("--bundle", type=Path, required=True)
    audit_parser.add_argument("--registry", type=Path)
    audit_parser.add_argument("--json", action="store_true")
    test_parser = subparsers.add_parser("self-test")
    test_parser.add_argument("--registry", type=Path)
    test_parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        report = (
            audit_forge_bundle(load_bundle(args.bundle), registry_path=args.registry)
            if args.command == "audit"
            else self_test(registry_path=args.registry)
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        report = {
            "contract": CONTRACT,
            "status": "REVISE",
            "failures": [f"INPUT:{type(exc).__name__}:{exc}"],
        }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"TITI_V3_V7_MICRO_FORGE={report['status']}")
        print(f"FAILURES={','.join(report.get('failures', [])) or 'NONE'}")
    return 0 if report.get("status") == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Validate TITI's V3 default lock-sentence calibration profile.

The profile may calibrate sentence and micro structure only. It never carries
chart values, never changes the six R5 V3 joints, and never applies to exact
reverse rendering or V4-V7. This guard validates those boundaries and exposes
the small activation decision used by callers.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any


CONTRACT = "TITI_V3_DEFAULT_LOCK_CALIBRATION_V1"
PROFILE_ID = "TITI_V3_DEFAULT_LOCK_3SET"
AUTHORITY = "CURRENT_USER_DIRECTIVE"
DEFAULT_ANCHOR_ORDER = ("D5-H08", "D4-H10", "D6-H05")
ALLOWED_OPERATION = "DESIGN_STAGE"
V3_JOINT_UIDS = (
    "V3.CENTER_OPERATION",
    "V3.FIELD_INPUT",
    "V3.OPERATOR_OBJECT",
    "V3.STATE_TRANSFORMATION",
    "V3.TRANSFER_CHECKPOINT",
    "V3.RESULT_BOUNDARY",
)
EXCLUDED_OPERATION = "EXACT_STAGE_REVERSE"
EXCLUDED_VERSIONS = ("V4", "V5", "V6", "V7")
DEFAULT_MANIFEST = (
    Path(__file__).resolve().parents[1]
    / "assets"
    / "titi_v3_default_lock_manifest.json"
)

GATES = (
    "SCHEMA",
    "CONTRACT",
    "PROFILE",
    "ACTIVATION_ROUTING",
    "DEFAULT_ANCHOR_ORDER",
    "V3_SCOPE",
    "V3_SIX_JOINTS",
    "EXACT_V3_NOT_EXECUTED",
    "CALIBRATION_USE_BOUNDARY",
    "CALIBRATION_VALUES_VOID",
    "D6_ARCHETYPE_BINDING",
    "D6_CURRENT_SOURCE_ONLY",
    "EXACT_REVERSE_EXCLUDED",
    "V4_V7_EXCLUDED",
    "USER_OVERRIDE",
    "NO_CHART_SPECIFIC_VALUES",
)

TOP_LEVEL_KEYS = {
    "contract",
    "profile_id",
    "authority",
    "activation",
    "v3_stage",
    "calibration",
    "anchor_profiles",
    "archetype_profiles",
    "exclusions",
}
ACTIVATION_KEYS = {
    "task_scope",
    "when_version_omitted",
    "when_version_explicit_v3",
    "user_override",
}
USER_OVERRIDE_KEYS = {
    "allowed",
    "priority",
    "effect",
    "may_change_v3_stage_semantics",
    "may_change_current_target_source",
}
V3_STAGE_KEYS = {
    "stage",
    "joint_count",
    "joint_uids",
    "semantics_authority",
    "exact_output_state",
}
CALIBRATION_KEYS = {
    "default_anchor_order",
    "default_use",
    "calibration_value_state",
    "current_target_value_source",
    "literal_copy_authority",
    "exact_source_text_state",
}
BASE_TARGET_KEYS = {
    "target_id",
    "profile_role",
    "sentence_micro_structure",
    "calibration_value_state",
    "value_source",
}
D6_TARGET_KEYS = BASE_TARGET_KEYS | {
    "archetype_target_id",
    "archetype_scope",
    "archetype_value_state",
    "archetype_value_inheritance",
}
ARCHETYPE_KEYS = {
    "target_id",
    "profile_role",
    "allowed_use",
    "calibration_value_state",
    "semantic_value_authority",
}
EXCLUSION_KEYS = {
    "operations",
    "versions",
    "cross_target_value_inheritance",
    "archetype_value_inheritance",
}

FORBIDDEN_CHART_KEY_FRAGMENTS = (
    "sign",
    "planet",
    "degree",
    "pada",
    "nakshatra",
    "occupant",
    "longitude",
    "house_lord",
)
FORBIDDEN_CHART_TERMS = (
    "sun",
    "moon",
    "mars",
    "mercury",
    "jupiter",
    "venus",
    "saturn",
    "rahu",
    "ketu",
    "uranus",
    "neptune",
    "pluto",
    "aries",
    "taurus",
    "gemini",
    "cancer",
    "leo",
    "virgo",
    "libra",
    "scorpio",
    "sagittarius",
    "capricorn",
    "aquarius",
    "pisces",
    "mesha",
    "vrishabha",
    "mithuna",
    "kataka",
    "karka",
    "simha",
    "kanya",
    "thula",
    "tula",
    "vrischika",
    "dhanus",
    "makara",
    "kumbha",
    "meena",
    "태양",
    "달",
    "화성",
    "수성",
    "목성",
    "금성",
    "토성",
    "라후",
    "케투",
    "양자리",
    "황소자리",
    "쌍둥이자리",
    "게자리",
    "사자자리",
    "처녀자리",
    "천칭자리",
    "전갈자리",
    "사수자리",
    "염소자리",
    "물병자리",
    "물고기자리",
)
DEGREE_PATTERN = re.compile(r"(?:\d+(?:\.\d+)?\s*°|\d{1,3}:\d{2}(?::\d{2})?)")
PADA_PATTERN = re.compile(r"(?:\bP[1-4]\b|\bPada\s*[1-4]\b|파다\s*[1-4])", re.IGNORECASE)


def load_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    """Load a UTF-8 JSON calibration manifest."""

    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("manifest top level must be an object")
    return payload


def _profile_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    profiles = payload.get("anchor_profiles")
    if not isinstance(profiles, list):
        return {}
    return {
        item.get("target_id"): item
        for item in profiles
        if isinstance(item, dict) and isinstance(item.get("target_id"), str)
    }


def _chart_specific_paths(value: Any, path: str = "manifest") -> list[str]:
    failures: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).casefold()
            if any(fragment in normalized for fragment in FORBIDDEN_CHART_KEY_FRAGMENTS):
                failures.append(f"{path}.{key}:forbidden_key")
            failures.extend(_chart_specific_paths(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            failures.extend(_chart_specific_paths(item, f"{path}[{index}]"))
    elif isinstance(value, str):
        folded = value.casefold()
        for term in FORBIDDEN_CHART_TERMS:
            pattern = rf"(?<![a-z0-9]){re.escape(term.casefold())}(?![a-z0-9])"
            if re.search(pattern, folded):
                failures.append(f"{path}:forbidden_term:{term}")
                break
        if DEGREE_PATTERN.search(value):
            failures.append(f"{path}:degree_value")
        if PADA_PATTERN.search(value):
            failures.append(f"{path}:pada_value")
    return failures


def _schema_ok(payload: dict[str, Any]) -> bool:
    if set(payload) != TOP_LEVEL_KEYS:
        return False
    activation = payload.get("activation")
    stage = payload.get("v3_stage")
    calibration = payload.get("calibration")
    exclusions = payload.get("exclusions")
    if not all(isinstance(item, dict) for item in (activation, stage, calibration, exclusions)):
        return False
    if set(activation) != ACTIVATION_KEYS:
        return False
    override = activation.get("user_override")
    if not isinstance(override, dict) or set(override) != USER_OVERRIDE_KEYS:
        return False
    if set(stage) != V3_STAGE_KEYS or set(calibration) != CALIBRATION_KEYS:
        return False
    if set(exclusions) != EXCLUSION_KEYS:
        return False
    profiles = payload.get("anchor_profiles")
    archetypes = payload.get("archetype_profiles")
    if not isinstance(profiles, list) or not isinstance(archetypes, list):
        return False
    if len(profiles) != 3 or len(archetypes) != 1:
        return False
    for profile in profiles:
        if not isinstance(profile, dict):
            return False
        expected = D6_TARGET_KEYS if profile.get("target_id") == "D6-H05" else BASE_TARGET_KEYS
        if set(profile) != expected:
            return False
    return isinstance(archetypes[0], dict) and set(archetypes[0]) == ARCHETYPE_KEYS


def audit_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    """Audit the complete default calibration profile."""

    failures: list[str] = []
    gates = {name: True for name in GATES}

    def fail(gate: str, detail: str) -> None:
        gates[gate] = False
        item = f"{gate}:{detail}"
        if item not in failures:
            failures.append(item)

    if not _schema_ok(payload):
        fail("SCHEMA", "field_set")
    if payload.get("contract") != CONTRACT:
        fail("CONTRACT", "contract")
    if payload.get("profile_id") != PROFILE_ID or payload.get("authority") != AUTHORITY:
        fail("PROFILE", "identity_or_authority")

    activation = payload.get("activation") if isinstance(payload.get("activation"), dict) else {}
    if (
        activation.get("task_scope") != "LOCK_SENTENCE"
        or activation.get("when_version_omitted") != "V3"
        or activation.get("when_version_explicit_v3")
        != "APPLY_DEFAULT_IF_NO_USER_OVERRIDE"
    ):
        fail("ACTIVATION_ROUTING", "default_route")

    override = activation.get("user_override") if isinstance(activation.get("user_override"), dict) else {}
    if (
        override.get("allowed") is not True
        or override.get("priority") != "CURRENT_USER_INSTRUCTION"
        or override.get("effect") != "REPLACE_CALIBRATION_PROFILE_ONLY"
        or override.get("may_change_v3_stage_semantics") is not False
        or override.get("may_change_current_target_source") is not False
    ):
        fail("USER_OVERRIDE", "boundary")

    stage = payload.get("v3_stage") if isinstance(payload.get("v3_stage"), dict) else {}
    if stage.get("stage") != "3" or stage.get("semantics_authority") != "RQ_R5_V3_CANON":
        fail("V3_SCOPE", "stage_or_authority")
    if stage.get("joint_count") != 6 or stage.get("joint_uids") != list(V3_JOINT_UIDS):
        fail("V3_SIX_JOINTS", "registry")
    if stage.get("exact_output_state") != "NOT_EXECUTED":
        fail("EXACT_V3_NOT_EXECUTED", "state")

    calibration = payload.get("calibration") if isinstance(payload.get("calibration"), dict) else {}
    if calibration.get("default_anchor_order") != list(DEFAULT_ANCHOR_ORDER):
        fail("DEFAULT_ANCHOR_ORDER", "order")
    if (
        calibration.get("default_use") != "SENTENCE_MICRO_CALIBRATION_ONLY"
        or calibration.get("current_target_value_source") != "CURRENT_TARGET_SOURCE_ONLY"
        or calibration.get("literal_copy_authority") != "NONE"
        or calibration.get("exact_source_text_state") != "NOT_BOUND"
    ):
        fail("CALIBRATION_USE_BOUNDARY", "scope")
    if calibration.get("calibration_value_state") != "VOID":
        fail("CALIBRATION_VALUES_VOID", "profile")

    profile_map = _profile_map(payload)
    if list(profile_map) != list(DEFAULT_ANCHOR_ORDER):
        fail("DEFAULT_ANCHOR_ORDER", "anchor_profiles")
    for target_id in DEFAULT_ANCHOR_ORDER:
        profile = profile_map.get(target_id, {})
        if (
            profile.get("profile_role") != "V3_DEFAULT_CALIBRATION_ANCHOR"
            or profile.get("sentence_micro_structure") != "CALIBRATION_ONLY"
        ):
            fail("CALIBRATION_USE_BOUNDARY", target_id)
        if profile.get("calibration_value_state") != "VOID":
            fail("CALIBRATION_VALUES_VOID", target_id)
    for target_id in ("D5-H08", "D4-H10"):
        if profile_map.get(target_id, {}).get("value_source") != "CURRENT_TARGET_SOURCE_ONLY":
            fail("CALIBRATION_USE_BOUNDARY", f"{target_id}:value_source")

    d6 = profile_map.get("D6-H05", {})
    if d6.get("value_source") != "CURRENT_D6_SOURCE_ONLY":
        fail("D6_CURRENT_SOURCE_ONLY", "value_source")
    if (
        d6.get("archetype_target_id") != "D5-H05"
        or d6.get("archetype_scope") != ["SENTENCE_STRUCTURE", "MICRO_STRUCTURE"]
        or d6.get("archetype_value_state") != "VOID"
        or d6.get("archetype_value_inheritance") != "PROHIBITED"
    ):
        fail("D6_ARCHETYPE_BINDING", "d6_profile")
    if d6.get("archetype_value_state") != "VOID":
        fail("CALIBRATION_VALUES_VOID", "D6-H05:archetype")

    archetypes = payload.get("archetype_profiles")
    archetype = archetypes[0] if isinstance(archetypes, list) and len(archetypes) == 1 and isinstance(archetypes[0], dict) else {}
    if (
        archetype.get("target_id") != "D5-H05"
        or archetype.get("profile_role") != "D6-H05_ARCHETYPE_ONLY"
        or archetype.get("allowed_use") != ["SENTENCE_STRUCTURE", "MICRO_STRUCTURE"]
        or archetype.get("calibration_value_state") != "VOID"
        or archetype.get("semantic_value_authority") != "NONE"
        or "D5-H05" in DEFAULT_ANCHOR_ORDER
    ):
        fail("D6_ARCHETYPE_BINDING", "archetype_profile")
    if archetype.get("calibration_value_state") != "VOID":
        fail("CALIBRATION_VALUES_VOID", "D5-H05:archetype")

    exclusions = payload.get("exclusions") if isinstance(payload.get("exclusions"), dict) else {}
    if (
        exclusions.get("operations") != [EXCLUDED_OPERATION]
        or exclusions.get("cross_target_value_inheritance") != "PROHIBITED"
        or exclusions.get("archetype_value_inheritance") != "PROHIBITED"
    ):
        fail("EXACT_REVERSE_EXCLUDED", "operation_or_value_boundary")
    if exclusions.get("versions") != list(EXCLUDED_VERSIONS):
        fail("V4_V7_EXCLUDED", "versions")

    chart_paths = _chart_specific_paths(payload)
    if chart_paths:
        fail("NO_CHART_SPECIFIC_VALUES", chart_paths[0])

    return {
        "contract": CONTRACT,
        "status": "PASS" if not failures else "REVISE",
        "profile_id": payload.get("profile_id"),
        "default_anchor_order": calibration.get("default_anchor_order"),
        "v3_joint_count": stage.get("joint_count"),
        "exact_v3_output_state": stage.get("exact_output_state"),
        "calibration_value_state": calibration.get("calibration_value_state"),
        "d6_archetype_target": d6.get("archetype_target_id"),
        "d6_value_source": d6.get("value_source"),
        "gates": gates,
        "failures": failures,
    }


def resolve_activation(
    payload: dict[str, Any],
    *,
    task_scope: str,
    requested_version: str | None = None,
    operation: str = "DESIGN_STAGE",
    user_override: bool = False,
) -> dict[str, Any]:
    """Resolve whether the default profile applies without changing stage semantics."""

    selected_version = requested_version or "V3"
    if operation == EXCLUDED_OPERATION:
        return {
            "state": "EXCLUDED_EXACT_REVERSE",
            "selected_version": selected_version,
            "profile_id": None,
        }
    if operation != ALLOWED_OPERATION:
        return {
            "state": "NOT_APPLICABLE_OPERATION",
            "selected_version": selected_version,
            "profile_id": None,
        }
    if user_override:
        return {
            "state": "USER_OVERRIDE",
            "selected_version": selected_version,
            "profile_id": None,
        }
    if audit_manifest(payload).get("status") != "PASS":
        return {
            "state": "HOLD_INVALID_PROFILE",
            "selected_version": selected_version,
            "profile_id": None,
        }
    if selected_version in EXCLUDED_VERSIONS:
        return {
            "state": "EXCLUDED_VERSION",
            "selected_version": selected_version,
            "profile_id": None,
        }
    if task_scope != payload.get("activation", {}).get("task_scope"):
        return {
            "state": "NOT_APPLICABLE",
            "selected_version": selected_version,
            "profile_id": None,
        }
    if selected_version != "V3":
        return {
            "state": "HOLD_UNSUPPORTED_VERSION",
            "selected_version": selected_version,
            "profile_id": None,
        }
    return {
        "state": "APPLY_DEFAULT",
        "selected_version": "V3",
        "profile_id": payload.get("profile_id"),
        "default_anchor_order": payload.get("calibration", {}).get(
            "default_anchor_order"
        ),
        "exact_v3_output_state": payload.get("v3_stage", {}).get(
            "exact_output_state"
        ),
    }


def self_test(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    """Exercise the valid profile, routing, and fail-closed mutations."""

    payload = load_manifest(path)
    valid = audit_manifest(payload)
    failures: list[str] = []
    if valid.get("status") != "PASS":
        failures.append("valid_manifest")

    routes = {
        "omitted_version": resolve_activation(payload, task_scope="LOCK_SENTENCE"),
        "explicit_v3": resolve_activation(
            payload, task_scope="LOCK_SENTENCE", requested_version="V3"
        ),
        "exact_reverse": resolve_activation(
            payload,
            task_scope="LOCK_SENTENCE",
            requested_version="V3",
            operation="EXACT_STAGE_REVERSE",
        ),
        "v4": resolve_activation(
            payload, task_scope="LOCK_SENTENCE", requested_version="V4"
        ),
        "override": resolve_activation(
            payload,
            task_scope="LOCK_SENTENCE",
            requested_version="V3",
            user_override=True,
        ),
        "reverse_design": resolve_activation(
            payload,
            task_scope="LOCK_SENTENCE",
            requested_version="V3",
            operation="REVERSE_DESIGN",
        ),
    }
    expected_route_states = {
        "omitted_version": "APPLY_DEFAULT",
        "explicit_v3": "APPLY_DEFAULT",
        "exact_reverse": "EXCLUDED_EXACT_REVERSE",
        "v4": "EXCLUDED_VERSION",
        "override": "USER_OVERRIDE",
        "reverse_design": "NOT_APPLICABLE_OPERATION",
    }
    for name, state in expected_route_states.items():
        if routes[name].get("state") != state:
            failures.append(f"route:{name}")

    cases: dict[str, tuple[dict[str, Any], str]] = {}

    wrong_order = copy.deepcopy(payload)
    wrong_order["calibration"]["default_anchor_order"][0:2] = ["D4-H10", "D5-H08"]
    cases["wrong_order"] = (wrong_order, "DEFAULT_ANCHOR_ORDER")

    extra_joint = copy.deepcopy(payload)
    extra_joint["v3_stage"]["joint_count"] = 7
    cases["v3_joint_change"] = (extra_joint, "V3_SIX_JOINTS")

    false_exact = copy.deepcopy(payload)
    false_exact["v3_stage"]["exact_output_state"] = "PASS"
    cases["false_exact_output"] = (false_exact, "EXACT_V3_NOT_EXECUTED")

    bound_value = copy.deepcopy(payload)
    bound_value["anchor_profiles"][0]["calibration_value_state"] = "BOUND"
    cases["bound_calibration_value"] = (bound_value, "CALIBRATION_VALUES_VOID")

    d6_wrong_archetype = copy.deepcopy(payload)
    d6_wrong_archetype["anchor_profiles"][2]["archetype_target_id"] = "D4-H10"
    cases["d6_wrong_archetype"] = (d6_wrong_archetype, "D6_ARCHETYPE_BINDING")

    d6_wrong_source = copy.deepcopy(payload)
    d6_wrong_source["anchor_profiles"][2]["value_source"] = "D5_ARCHETYPE_SOURCE"
    cases["d6_wrong_source"] = (d6_wrong_source, "D6_CURRENT_SOURCE_ONLY")

    exact_enabled = copy.deepcopy(payload)
    exact_enabled["exclusions"]["operations"] = []
    cases["exact_reverse_enabled"] = (exact_enabled, "EXACT_REVERSE_EXCLUDED")

    version_leak = copy.deepcopy(payload)
    version_leak["exclusions"]["versions"].remove("V7")
    cases["v7_not_excluded"] = (version_leak, "V4_V7_EXCLUDED")

    override_disabled = copy.deepcopy(payload)
    override_disabled["activation"]["user_override"]["allowed"] = False
    cases["override_disabled"] = (override_disabled, "USER_OVERRIDE")

    chart_value = copy.deepcopy(payload)
    chart_value["anchor_profiles"][0]["planet"] = "Mars"
    cases["chart_value_added"] = (chart_value, "NO_CHART_SPECIFIC_VALUES")

    negative_cases: dict[str, dict[str, Any]] = {}
    for name, (case, expected_gate) in cases.items():
        report = audit_manifest(case)
        detected = (
            report.get("status") == "REVISE"
            and report.get("gates", {}).get(expected_gate) is False
        )
        negative_cases[name] = {
            "status": report.get("status"),
            "expected_gate": expected_gate,
            "detected": detected,
        }
        if not detected:
            failures.append(name)

    return {
        "contract": "TITI_V3_DEFAULT_LOCK_CALIBRATION_SELF_TEST_V1",
        "status": "PASS" if not failures else "REVISE",
        "valid_manifest_status": valid.get("status"),
        "valid_manifest_gates": valid.get("gates"),
        "activation_routes": routes,
        "negative_cases": negative_cases,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    audit_parser.add_argument("--json", action="store_true")
    test_parser = subparsers.add_parser("self-test")
    test_parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    test_parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        report = (
            audit_manifest(load_manifest(args.manifest))
            if args.command == "audit"
            else self_test(args.manifest)
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
        print(f"TITI_V3_DEFAULT_LOCK={report['status']}")
        print(f"FAILURES={','.join(report.get('failures', [])) or 'NONE'}")
    return 0 if report.get("status") == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

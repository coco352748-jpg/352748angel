#!/usr/bin/env python3
"""Audit source-bounded TITI micro fine-slot template designs."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

from reverse_render_guard import (
    PLACEHOLDER,
    TYPE_NAME,
    capture_sequences,
    split_template,
)


CONTRACT = "TITI_MICRO_TEMPLATE_DESIGN_V1"
TEMPLATE_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
VALUE_STATES = {"UNBOUND", "HOLD"}
OPERATORS = {
    "INSERT_EXACT",
    "SELECT_APPROVED_VARIANT",
    "APPLY_APPROVED_RULE",
    "JOIN_ORDERED_SERIES",
}
GATES = (
    "CONTRACT",
    "MODE",
    "TEMPLATE_ID",
    "TARGET_DEFINED",
    "PLACEHOLDER_SET_AND_ORDER",
    "SLOT_UID_UNIQUE",
    "SLOT_METADATA_COMPLETE",
    "SOURCE_REQUIREMENT_COMPLETE",
    "REQUIRED_ROLE_COVERAGE",
    "LITERAL_AUTHORITY",
    "NO_BOUND_VALUE_IN_DESIGN",
    "NO_FALSE_EXACT_CLAIM",
    "NO_ADJACENT_PLACEHOLDER",
    "NON_DEGENERATE_LITERAL_SCAFFOLD",
    "HANDOFF_CHAIN",
    "OUTPUT_CONTRACT",
    "PROBE_RENDER",
    "PROBE_REVERSE_CAPTURE",
)


def load_bundle(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("design bundle top level must be an object")
    return payload


def render_probe(template: str, uids: list[str], values: list[str]) -> str:
    rendered = template
    for uid, value in zip(uids, values, strict=True):
        rendered = rendered.replace(f"《{uid}》", value, 1)
    return rendered


def audit_design_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    gates = {gate: True for gate in GATES}

    def fail(gate: str, detail: str) -> None:
        gates[gate] = False
        failures.append(f"{gate}:{detail}")

    if bundle.get("contract") != CONTRACT:
        fail("CONTRACT", "bundle")
    if bundle.get("mode") != "MICRO_TEMPLATE_DESIGN" or bundle.get(
        "validation_mode"
    ) != "STRUCTURAL_DESIGN":
        fail("MODE", "bundle")
    if (
        bundle.get("exact_roundtrip_state")
        != "NOT_APPLICABLE_UNTIL_FILLED"
        or "sentence" in bundle
        or "records" in bundle
    ):
        fail("NO_FALSE_EXACT_CLAIM", "bundle")

    template_id = bundle.get("template_id")
    if not isinstance(template_id, str) or not TEMPLATE_ID.fullmatch(template_id):
        fail("TEMPLATE_ID", "bundle")
        template_id = "INVALID"

    target = bundle.get("target")
    if not isinstance(target, str) or not target.strip():
        fail("TARGET_DEFINED", "bundle")

    template = bundle.get("template")
    if not isinstance(template, str) or not template:
        fail("SLOT_METADATA_COMPLETE", "template")
        template = ""

    slots = bundle.get("slots")
    if not isinstance(slots, list) or not slots:
        fail("SLOT_METADATA_COMPLETE", "slots")
        slots = []

    literals, placeholder_uids = split_template(template)
    slot_uids: list[str] = []
    handoffs: dict[str, str] = {}
    slot_reports: list[dict[str, Any]] = []

    for index, raw_slot in enumerate(slots, start=1):
        slot_start = len(failures)
        if not isinstance(raw_slot, dict):
            fail("SLOT_METADATA_COMPLETE", f"slot_{index}")
            continue

        uid = raw_slot.get("uid")
        value_type = raw_slot.get("type")
        semantic_role = raw_slot.get("semantic_role")
        required = raw_slot.get("required")
        input_ref = raw_slot.get("input_ref")
        operator = raw_slot.get("operator")
        transformation = raw_slot.get("transformation")
        handoff = raw_slot.get("handoff")
        result_boundary = raw_slot.get("result_boundary")
        value_state = raw_slot.get("value_state")

        metadata_ok = (
            isinstance(uid, str)
            and uid.startswith(f"{template_id}.")
            and isinstance(value_type, str)
            and bool(TYPE_NAME.fullmatch(value_type))
            and isinstance(semantic_role, str)
            and bool(semantic_role.strip())
            and isinstance(required, bool)
            and isinstance(operator, str)
            and (operator in OPERATORS or operator.startswith("USER_APPROVED:"))
            and isinstance(transformation, str)
            and bool(transformation)
            and isinstance(handoff, str)
            and bool(handoff)
            and isinstance(result_boundary, str)
            and bool(result_boundary.strip())
            and value_state in VALUE_STATES
        )
        if not metadata_ok:
            fail("SLOT_METADATA_COMPLETE", f"slot_{index}")
            continue

        source_ok = (
            isinstance(input_ref, str)
            and bool(input_ref.strip())
            and (
                transformation == "NONE"
                or transformation.startswith("APPROVED_RULE:")
            )
        )
        if not source_ok:
            fail("SOURCE_REQUIREMENT_COMPLETE", uid)

        if "value" in raw_slot and raw_slot.get("value") not in (None, ""):
            fail("NO_BOUND_VALUE_IN_DESIGN", uid)

        if uid in slot_uids:
            fail("SLOT_UID_UNIQUE", uid)
        slot_uids.append(uid)
        handoffs[uid] = handoff
        slot_reports.append(
            {
                "uid": uid,
                "status": "PASS" if len(failures) == slot_start else "REVISE",
                "required": required,
                "value_state": value_state,
                "handoff": handoff,
                "failures": failures[slot_start:],
            }
        )

    if placeholder_uids != slot_uids:
        fail("PLACEHOLDER_SET_AND_ORDER", "template")
    if len(set(placeholder_uids)) != len(placeholder_uids):
        fail("SLOT_UID_UNIQUE", "template_duplicate")

    adjacent = any(literal == "" for literal in literals[1:-1])
    if adjacent:
        fail("NO_ADJACENT_PLACEHOLDER", "template")
    if not placeholder_uids or sum(len(literal) for literal in literals) == 0:
        fail("NON_DEGENERATE_LITERAL_SCAFFOLD", "template")

    required_roles = bundle.get("required_roles")
    actual_required_roles = {
        slot.get("semantic_role")
        for slot in slots
        if isinstance(slot, dict) and slot.get("required") is True
    }
    required_roles_ok = (
        isinstance(required_roles, list)
        and bool(required_roles)
        and all(isinstance(role, str) and bool(role.strip()) for role in required_roles)
        and len(required_roles) == len(set(required_roles))
        and set(required_roles) == actual_required_roles
    )
    if not required_roles_ok:
        fail("REQUIRED_ROLE_COVERAGE", "bundle")

    literal_authority_refs = bundle.get("literal_authority_refs")
    nonempty_literals = [literal for literal in literals if literal]
    literal_authority_ok = (
        isinstance(literal_authority_refs, list)
        and len(literal_authority_refs) == len(nonempty_literals)
        and all(
            isinstance(authority_ref, str) and bool(authority_ref.strip())
            for authority_ref in literal_authority_refs
        )
    )
    if not literal_authority_ok:
        fail("LITERAL_AUTHORITY", "bundle")

    if slot_uids:
        visited: list[str] = []
        current = slot_uids[0]
        while current != "OUTPUT" and current not in visited:
            if current not in handoffs:
                break
            visited.append(current)
            current = handoffs[current]
        chain_ok = (
            current == "OUTPUT"
            and len(visited) == len(slot_uids)
            and set(visited) == set(slot_uids)
        )
        if not chain_ok:
            fail("HANDOFF_CHAIN", "not_one_open_chain")
    else:
        fail("HANDOFF_CHAIN", "slots_missing")

    output_contract = bundle.get("output_contract")
    output_ok = (
        isinstance(output_contract, dict)
        and isinstance(output_contract.get("output_type"), str)
        and bool(output_contract.get("output_type"))
        and isinstance(output_contract.get("required_format"), str)
        and bool(output_contract.get("required_format"))
        and output_contract.get("missing_value_policy") == "HOLD_SLOT"
        and isinstance(output_contract.get("completion_rule"), str)
        and bool(output_contract.get("completion_rule"))
    )
    if not output_ok:
        fail("OUTPUT_CONTRACT", "bundle")

    probe_values = [f"⟦PROBE:{index}:{uid}⟧" for index, uid in enumerate(slot_uids, 1)]
    probe_rendered = ""
    captures: list[list[str]] = []
    if placeholder_uids == slot_uids and slot_uids:
        probe_rendered = render_probe(template, slot_uids, probe_values)
        if PLACEHOLDER.search(probe_rendered):
            fail("PROBE_RENDER", "placeholder_remaining")
        captures = (
            capture_sequences(probe_rendered, literals, len(slot_uids))
            if not adjacent
            else []
        )
        if len(captures) != 1 or captures[0] != probe_values:
            fail("PROBE_REVERSE_CAPTURE", f"capture_count_{len(captures)}")
    else:
        fail("PROBE_RENDER", "slot_order")
        fail("PROBE_REVERSE_CAPTURE", "slot_order")

    return {
        "contract": CONTRACT,
        "status": "PASS" if not failures else "REVISE",
        "template_id": template_id,
        "slot_count": len(slot_uids),
        "required_slot_count": sum(
            1 for slot in slots if isinstance(slot, dict) and slot.get("required") is True
        ),
        "required_role_count": len(actual_required_roles),
        "literal_segment_count": len(nonempty_literals),
        "probe_rendered": bool(probe_rendered),
        "probe_capture_count_capped_at_2": len(captures),
        "gates": gates,
        "slots": slot_reports,
        "failures": failures,
    }


def sample_bundle() -> dict[str, Any]:
    return {
        "contract": CONTRACT,
        "mode": "MICRO_TEMPLATE_DESIGN",
        "validation_mode": "STRUCTURAL_DESIGN",
        "exact_roundtrip_state": "NOT_APPLICABLE_UNTIL_FILLED",
        "template_id": "T1",
        "target": "Produce one source-bounded transfer sentence",
        "required_roles": [
            "actor",
            "input_object",
            "transformation_action",
            "output_result",
        ],
        "template": "《T1.ACTOR.SUBJECT.01》은 《T1.INPUT.OBJECT.01》을 받아 《T1.ACTION.PROCESS.01》한 뒤 《T1.OUTPUT.RESULT.01》로 넘긴다.",
        "literal_authority_refs": [
            "CURRENT_USER:target",
            "CURRENT_USER:format",
            "CURRENT_USER:target",
            "CURRENT_USER:format",
        ],
        "slots": [
            {
                "uid": "T1.ACTOR.SUBJECT.01",
                "type": "NP",
                "semantic_role": "actor",
                "required": True,
                "input_ref": "USER_INPUT:actor",
                "operator": "INSERT_EXACT",
                "transformation": "NONE",
                "handoff": "T1.INPUT.OBJECT.01",
                "result_boundary": "identifies_actor_only",
                "value_state": "UNBOUND",
            },
            {
                "uid": "T1.INPUT.OBJECT.01",
                "type": "OBJECT",
                "semantic_role": "input_object",
                "required": True,
                "input_ref": "USER_INPUT:input_object",
                "operator": "INSERT_EXACT",
                "transformation": "NONE",
                "handoff": "T1.ACTION.PROCESS.01",
                "result_boundary": "identifies_input_only",
                "value_state": "UNBOUND",
            },
            {
                "uid": "T1.ACTION.PROCESS.01",
                "type": "PREDICATE",
                "semantic_role": "transformation_action",
                "required": True,
                "input_ref": "USER_INPUT:approved_action",
                "operator": "INSERT_EXACT",
                "transformation": "NONE",
                "handoff": "T1.OUTPUT.RESULT.01",
                "result_boundary": "states_action_without_result_invention",
                "value_state": "UNBOUND",
            },
            {
                "uid": "T1.OUTPUT.RESULT.01",
                "type": "NP",
                "semantic_role": "output_result",
                "required": True,
                "input_ref": "USER_INPUT:output_result",
                "operator": "INSERT_EXACT",
                "transformation": "NONE",
                "handoff": "OUTPUT",
                "result_boundary": "identifies_output_only",
                "value_state": "UNBOUND",
            },
        ],
        "output_contract": {
            "output_type": "SENTENCE",
            "required_format": "ONE_SENTENCE",
            "missing_value_policy": "HOLD_SLOT",
            "completion_rule": "ALL_REQUIRED_SLOTS_BOUND",
        },
    }


def self_test() -> dict[str, Any]:
    valid = sample_bundle()
    cases: dict[str, tuple[dict[str, Any], str]] = {}

    bound_value = copy.deepcopy(valid)
    bound_value["slots"][0]["value"] = "invented"
    cases["bound_value"] = (bound_value, "NO_BOUND_VALUE_IN_DESIGN")

    missing_source = copy.deepcopy(valid)
    missing_source["slots"][1]["input_ref"] = ""
    cases["missing_source"] = (missing_source, "SOURCE_REQUIREMENT_COMPLETE")

    adjacent = copy.deepcopy(valid)
    adjacent["template"] = "《T1.ACTOR.SUBJECT.01》《T1.INPUT.OBJECT.01》을 받아 《T1.ACTION.PROCESS.01》한 뒤 《T1.OUTPUT.RESULT.01》로 넘긴다."
    cases["adjacent"] = (adjacent, "NO_ADJACENT_PLACEHOLDER")

    handoff_loop = copy.deepcopy(valid)
    handoff_loop["slots"][-1]["handoff"] = "T1.ACTOR.SUBJECT.01"
    cases["handoff_loop"] = (handoff_loop, "HANDOFF_CHAIN")

    wrong_order = copy.deepcopy(valid)
    wrong_order["slots"][0], wrong_order["slots"][1] = (
        wrong_order["slots"][1],
        wrong_order["slots"][0],
    )
    cases["wrong_order"] = (wrong_order, "PLACEHOLDER_SET_AND_ORDER")

    bad_missing_policy = copy.deepcopy(valid)
    bad_missing_policy["output_contract"]["missing_value_policy"] = "GUESS"
    cases["bad_missing_policy"] = (bad_missing_policy, "OUTPUT_CONTRACT")

    missing_role = copy.deepcopy(valid)
    missing_role["required_roles"].pop()
    cases["missing_role"] = (missing_role, "REQUIRED_ROLE_COVERAGE")

    false_exact = copy.deepcopy(valid)
    false_exact["exact_roundtrip_state"] = "PASS"
    cases["false_exact"] = (false_exact, "NO_FALSE_EXACT_CLAIM")

    valid_report = audit_design_bundle(valid)
    failures: list[str] = []
    invalid_reports: dict[str, dict[str, Any]] = {}
    if valid_report.get("status") != "PASS":
        failures.append("valid_case")

    for name, (bundle, expected_gate) in cases.items():
        report = audit_design_bundle(bundle)
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
        "contract": "TITI_MICRO_TEMPLATE_DESIGN_SELF_TEST_V1",
        "status": "PASS" if not failures else "REVISE",
        "valid_case": valid_report.get("status"),
        "invalid_cases": invalid_reports,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("--bundle", type=Path, required=True)
    audit_parser.add_argument("--json", action="store_true")
    test_parser = subparsers.add_parser("self-test")
    test_parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        report = (
            audit_design_bundle(load_bundle(args.bundle))
            if args.command == "audit"
            else self_test()
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        report = {"status": "REVISE", "failures": [f"INPUT:{type(exc).__name__}:{exc}"]}

    if getattr(args, "json", False):
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"TITI_MICRO_TEMPLATE_DESIGN={report['status']}")
        print(f"FAILURES={','.join(report.get('failures', [])) or 'NONE'}")
    return 0 if report.get("status") == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

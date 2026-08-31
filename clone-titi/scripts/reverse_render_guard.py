#!/usr/bin/env python3
"""Audit exact sentence ↔ typed micro fine-slot roundtrips for clone-titi."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any


CONTRACT = "TITI_MICRO_ROUNDTRIP_V1"
EQUALITY_MODE = "EXACT_SURFACE"
PLACEHOLDER = re.compile(r"《([A-Za-z0-9_.-]+)》")
TYPE_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
GATES = (
    "CONTRACT",
    "EQUALITY_MODE",
    "RECORD_ID_UNIQUE",
    "PLACEHOLDER_SET_AND_ORDER",
    "SLOT_UID_UNIQUE",
    "SLOT_METADATA_COMPLETE",
    "NO_ADJACENT_PLACEHOLDER",
    "NON_DEGENERATE_LITERAL_SCAFFOLD",
    "UNIQUE_CAPTURE",
    "EXACT_RENDER",
    "INVERSE_VALUES_AND_ORDER",
)


def load_bundle(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bundle top level must be an object")
    return payload


def split_template(template: str) -> tuple[list[str], list[str]]:
    literals: list[str] = []
    uids: list[str] = []
    cursor = 0
    for match in PLACEHOLDER.finditer(template):
        literals.append(template[cursor : match.start()])
        uids.append(match.group(1))
        cursor = match.end()
    literals.append(template[cursor:])
    return literals, uids


def capture_sequences(
    sentence: str,
    literals: list[str],
    slot_count: int,
    *,
    limit: int = 2,
) -> list[list[str]]:
    """Enumerate up to `limit` non-empty parses using literal boundaries."""

    if slot_count == 0 or len(literals) != slot_count + 1:
        return []
    if not sentence.startswith(literals[0]):
        return []

    results: list[list[str]] = []

    def walk(slot_index: int, position: int, values: list[str]) -> None:
        if len(results) >= limit:
            return
        next_literal = literals[slot_index + 1]
        is_last = slot_index == slot_count - 1

        if is_last:
            if next_literal:
                if not sentence.endswith(next_literal):
                    return
                boundary = len(sentence) - len(next_literal)
                if boundary <= position:
                    return
                results.append(values + [sentence[position:boundary]])
            elif position < len(sentence):
                results.append(values + [sentence[position:]])
            return

        if not next_literal:
            return

        search_from = position + 1
        while True:
            boundary = sentence.find(next_literal, search_from)
            if boundary < 0:
                break
            if boundary > position:
                walk(
                    slot_index + 1,
                    boundary + len(next_literal),
                    values + [sentence[position:boundary]],
                )
            if len(results) >= limit:
                return
            search_from = boundary + 1

    walk(0, len(literals[0]), [])
    return results


def render(template: str, ordered_slots: list[dict[str, Any]]) -> str:
    rendered = template
    for slot in ordered_slots:
        rendered = rendered.replace(f"《{slot['uid']}》", slot["value"], 1)
    return rendered


def audit_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    gates = {gate: True for gate in GATES}
    record_reports: list[dict[str, Any]] = []

    def fail(gate: str, detail: str) -> None:
        gates[gate] = False
        failures.append(f"{gate}:{detail}")

    if bundle.get("contract") != CONTRACT:
        fail("CONTRACT", "bundle")
    if bundle.get("equality_mode") != EQUALITY_MODE:
        fail("EQUALITY_MODE", "bundle")

    records = bundle.get("records")
    if not isinstance(records, list) or not records:
        fail("RECORD_ID_UNIQUE", "records_missing")
        records = []

    seen_record_ids: set[str] = set()
    seen_slot_uids: set[str] = set()

    for index, raw_record in enumerate(records, start=1):
        record_start = len(failures)
        if not isinstance(raw_record, dict):
            fail("SLOT_METADATA_COMPLETE", f"record_{index}_not_object")
            continue

        record_id = raw_record.get("id")
        sentence = raw_record.get("sentence")
        template = raw_record.get("template")
        slots = raw_record.get("slots")

        if not isinstance(record_id, str) or not record_id:
            fail("RECORD_ID_UNIQUE", f"record_{index}_id")
            record_id = f"INVALID_{index}"
        elif record_id in seen_record_ids:
            fail("RECORD_ID_UNIQUE", record_id)
        seen_record_ids.add(record_id)

        if not isinstance(sentence, str) or not isinstance(template, str):
            fail("SLOT_METADATA_COMPLETE", f"{record_id}:sentence_or_template")
            continue
        if not isinstance(slots, list) or not slots:
            fail("SLOT_METADATA_COMPLETE", f"{record_id}:slots")
            slots = []

        literals, placeholder_uids = split_template(template)
        slot_uids: list[str] = []
        slot_values: list[str] = []
        normalized_slots: list[dict[str, Any]] = []

        for slot_index, slot in enumerate(slots, start=1):
            if not isinstance(slot, dict):
                fail("SLOT_METADATA_COMPLETE", f"{record_id}:slot_{slot_index}")
                continue
            uid = slot.get("uid")
            value_type = slot.get("type")
            semantic_role = slot.get("semantic_role")
            value = slot.get("value")
            source_ref = slot.get("source_ref")
            metadata_ok = (
                isinstance(uid, str)
                and bool(uid)
                and uid.startswith(f"{record_id}.")
                and isinstance(value_type, str)
                and bool(TYPE_NAME.fullmatch(value_type))
                and isinstance(semantic_role, str)
                and bool(semantic_role.strip())
                and isinstance(value, str)
                and bool(value)
                and isinstance(source_ref, str)
                and bool(source_ref.strip())
            )
            if not metadata_ok:
                fail("SLOT_METADATA_COMPLETE", f"{record_id}:slot_{slot_index}")
                continue
            if uid in seen_slot_uids:
                fail("SLOT_UID_UNIQUE", uid)
            seen_slot_uids.add(uid)
            slot_uids.append(uid)
            slot_values.append(value)
            normalized_slots.append(slot)

        if placeholder_uids != slot_uids:
            fail("PLACEHOLDER_SET_AND_ORDER", record_id)
        if len(set(placeholder_uids)) != len(placeholder_uids):
            fail("SLOT_UID_UNIQUE", f"{record_id}:template_duplicate")

        adjacent = any(literal == "" for literal in literals[1:-1])
        if adjacent:
            fail("NO_ADJACENT_PLACEHOLDER", record_id)

        literal_chars = sum(len(literal) for literal in literals)
        if not placeholder_uids or literal_chars == 0:
            fail("NON_DEGENERATE_LITERAL_SCAFFOLD", record_id)

        captures = (
            capture_sequences(sentence, literals, len(placeholder_uids))
            if placeholder_uids and not adjacent
            else []
        )
        if len(captures) != 1:
            fail("UNIQUE_CAPTURE", f"{record_id}:{len(captures)}")

        rendered: str | None = None
        if placeholder_uids == slot_uids and len(normalized_slots) == len(slots):
            rendered = render(template, normalized_slots)
        if rendered != sentence:
            fail("EXACT_RENDER", record_id)

        inverse_ok = len(captures) == 1 and captures[0] == slot_values
        if not inverse_ok:
            fail("INVERSE_VALUES_AND_ORDER", record_id)

        local_failures = failures[record_start:]
        record_reports.append(
            {
                "id": record_id,
                "status": "PASS" if not local_failures else "REVISE",
                "slot_count": len(slot_uids),
                "capture_count_capped_at_2": len(captures),
                "render_exact": rendered == sentence,
                "inverse_exact": inverse_ok,
                "failures": local_failures,
            }
        )

    return {
        "contract": CONTRACT,
        "status": "PASS" if not failures else "REVISE",
        "equality_mode": EQUALITY_MODE,
        "record_count": len(records),
        "slot_uid_count": len(seen_slot_uids),
        "gates": gates,
        "records": record_reports,
        "failures": failures,
    }


def self_test() -> dict[str, Any]:
    valid = {
        "contract": CONTRACT,
        "equality_mode": EQUALITY_MODE,
        "records": [
            {
                "id": "S1",
                "sentence": "점유행성 Mars는 11H에 전환압력을 반입한다.",
                "template": "점유행성 《S1.OCCUPANT.PLANET.01》는 《S1.TARGET.HOUSE.01》에 《S1.ACTION.OBJECT.01》을 반입한다.",
                "slots": [
                    {"uid": "S1.OCCUPANT.PLANET.01", "type": "NP", "semantic_role": "occupant", "value": "Mars", "source_ref": "S1:1"},
                    {"uid": "S1.TARGET.HOUSE.01", "type": "NP", "semantic_role": "target_house", "value": "11H", "source_ref": "S1:2"},
                    {"uid": "S1.ACTION.OBJECT.01", "type": "OBJECT", "semantic_role": "input_object", "value": "전환압력", "source_ref": "S1:3"},
                ],
            }
        ],
    }

    cases: dict[str, tuple[dict[str, Any], str]] = {}

    catch_all = copy.deepcopy(valid)
    catch_all["records"][0]["template"] = "《S1.WHOLE.SENTENCE.01》"
    catch_all["records"][0]["slots"] = [
        {"uid": "S1.WHOLE.SENTENCE.01", "type": "CLAUSE", "semantic_role": "whole_sentence", "value": catch_all["records"][0]["sentence"], "source_ref": "S1:all"}
    ]
    cases["catch_all"] = (catch_all, "NON_DEGENERATE_LITERAL_SCAFFOLD")

    adjacent = copy.deepcopy(valid)
    adjacent["records"][0]["sentence"] = "ABBC"
    adjacent["records"][0]["template"] = "A《S1.X.VALUE.01》《S1.Y.VALUE.01》C"
    adjacent["records"][0]["slots"] = [
        {"uid": "S1.X.VALUE.01", "type": "TOKEN", "semantic_role": "x", "value": "B", "source_ref": "S1:x"},
        {"uid": "S1.Y.VALUE.01", "type": "TOKEN", "semantic_role": "y", "value": "B", "source_ref": "S1:y"},
    ]
    cases["adjacent"] = (adjacent, "NO_ADJACENT_PLACEHOLDER")

    ambiguous = copy.deepcopy(valid)
    ambiguous["records"][0]["sentence"] = "A1B2B3C"
    ambiguous["records"][0]["template"] = "A《S1.X.VALUE.01》B《S1.Y.VALUE.01》C"
    ambiguous["records"][0]["slots"] = [
        {"uid": "S1.X.VALUE.01", "type": "TOKEN", "semantic_role": "x", "value": "1", "source_ref": "S1:x"},
        {"uid": "S1.Y.VALUE.01", "type": "TOKEN", "semantic_role": "y", "value": "2B3", "source_ref": "S1:y"},
    ]
    cases["ambiguous"] = (ambiguous, "UNIQUE_CAPTURE")

    changed_value = copy.deepcopy(valid)
    changed_value["records"][0]["slots"][0]["value"] = "Venus"
    cases["changed_value"] = (changed_value, "EXACT_RENDER")

    valid_report = audit_bundle(valid)
    invalid_reports: dict[str, dict[str, Any]] = {}
    failures: list[str] = []
    if valid_report["status"] != "PASS":
        failures.append("valid_case")

    for name, (bundle, expected_gate) in cases.items():
        report = audit_bundle(bundle)
        detected = report["status"] == "REVISE" and report["gates"].get(expected_gate) is False
        invalid_reports[name] = {
            "status": report["status"],
            "expected_gate": expected_gate,
            "detected": detected,
        }
        if not detected:
            failures.append(name)

    return {
        "contract": "TITI_REVERSE_RENDER_GUARD_SELF_TEST_V1",
        "status": "PASS" if not failures else "REVISE",
        "valid_case": valid_report["status"],
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
        if args.command == "audit":
            report = audit_bundle(load_bundle(args.bundle))
        else:
            report = self_test()
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        report = {"status": "REVISE", "failures": [f"INPUT:{type(exc).__name__}:{exc}"]}

    if getattr(args, "json", False):
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"TITI_REVERSE_RENDER={report['status']}")
        print(f"FAILURES={','.join(report.get('failures', [])) or 'NONE'}")
    return 0 if report.get("status") == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

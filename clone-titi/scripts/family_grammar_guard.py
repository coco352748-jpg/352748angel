#!/usr/bin/env python3
"""Validate TITI multi-sentence Family grammar without losing local exactness."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from reverse_render_guard import (
    CONTRACT as LOCAL_CONTRACT,
    EQUALITY_MODE,
    PLACEHOLDER,
    audit_bundle as audit_local_records,
)


FAMILY_CONTRACT = "TITI_FAMILY_GRAMMAR_V1"
GATES = (
    "FAMILY_CONTRACT",
    "EQUALITY_MODE",
    "LOCAL_RECORD_ROUNDTRIP",
    "FAMILY_SLOT_ID_UNIQUE",
    "MEMBER_UID_VALID",
    "MEMBER_UID_UNIQUE",
    "ROLE_TYPE_STABLE",
    "REQUIRED_COVERAGE",
    "LOCAL_SLOT_COVERAGE",
    "VARIANT_ID_UNIQUE",
    "VARIANT_ASSIGNMENT",
    "VARIANT_SKELETON_STABLE",
)


def load_bundle(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("family bundle top level must be an object")
    return payload


def normalized_skeleton(record: dict[str, Any]) -> str:
    slots = record.get("slots", [])
    slot_map = {
        slot.get("uid"): slot
        for slot in slots
        if isinstance(slot, dict) and isinstance(slot.get("uid"), str)
    }
    template = record.get("template")
    if not isinstance(template, str):
        return ""

    def replace(match: re.Match[str]) -> str:
        slot = slot_map.get(match.group(1))
        if not slot:
            return "《INVALID:INVALID》"
        return f"《{slot.get('type')}:{slot.get('semantic_role')}》"

    return PLACEHOLDER.sub(replace, template)


def audit_family_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    gates = {gate: True for gate in GATES}

    def fail(gate: str, detail: str) -> None:
        gates[gate] = False
        failures.append(f"{gate}:{detail}")

    records = bundle.get("records")
    family_id = bundle.get("family_id")
    if (
        bundle.get("contract") != FAMILY_CONTRACT
        or not isinstance(family_id, str)
        or not family_id
        or not isinstance(records, list)
        or len(records) < 2
    ):
        fail("FAMILY_CONTRACT", "bundle")
    if not isinstance(records, list):
        records = []
    if bundle.get("equality_mode") != EQUALITY_MODE:
        fail("EQUALITY_MODE", "bundle")

    local_report = audit_local_records(
        {
            "contract": LOCAL_CONTRACT,
            "equality_mode": EQUALITY_MODE,
            "records": records,
        }
    )
    if local_report.get("status") != "PASS":
        fail("LOCAL_RECORD_ROUNDTRIP", "records")

    record_ids: list[str] = []
    local_slots: dict[str, dict[str, dict[str, Any]]] = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("id"), str):
            continue
        record_id = record["id"]
        record_ids.append(record_id)
        local_slots[record_id] = {
            slot["uid"]: slot
            for slot in record.get("slots", [])
            if isinstance(slot, dict) and isinstance(slot.get("uid"), str)
        }
    record_id_set = set(record_ids)

    family_slots = bundle.get("family_slots")
    if not isinstance(family_slots, list) or not family_slots:
        fail("FAMILY_SLOT_ID_UNIQUE", "missing")
        family_slots = []

    seen_family_slot_ids: set[str] = set()
    mapped_members: set[tuple[str, str]] = set()
    family_slot_reports: list[dict[str, Any]] = []

    for index, family_slot in enumerate(family_slots, start=1):
        if not isinstance(family_slot, dict):
            fail("FAMILY_SLOT_ID_UNIQUE", f"slot_{index}")
            continue
        family_slot_id = family_slot.get("family_slot_id")
        value_type = family_slot.get("type")
        semantic_role = family_slot.get("semantic_role")
        required = family_slot.get("required_across_records")
        members = family_slot.get("members")

        if not isinstance(family_slot_id, str) or not family_slot_id:
            fail("FAMILY_SLOT_ID_UNIQUE", f"slot_{index}")
            family_slot_id = f"INVALID_{index}"
        elif family_slot_id in seen_family_slot_ids:
            fail("FAMILY_SLOT_ID_UNIQUE", family_slot_id)
        seen_family_slot_ids.add(family_slot_id)

        if not isinstance(members, dict) or not members:
            fail("MEMBER_UID_VALID", family_slot_id)
            members = {}
        member_record_ids = set(members)
        if required is True and member_record_ids != record_id_set:
            fail("REQUIRED_COVERAGE", family_slot_id)
        elif required not in (True, False):
            fail("REQUIRED_COVERAGE", f"{family_slot_id}:flag")

        member_ok = True
        for record_id, uid in members.items():
            if (
                record_id not in record_id_set
                or not isinstance(uid, str)
                or uid not in local_slots.get(record_id, {})
            ):
                fail("MEMBER_UID_VALID", f"{family_slot_id}:{record_id}")
                member_ok = False
                continue
            member_key = (record_id, uid)
            if member_key in mapped_members:
                fail("MEMBER_UID_UNIQUE", f"{record_id}:{uid}")
                member_ok = False
            mapped_members.add(member_key)
            local_slot = local_slots[record_id][uid]
            if (
                local_slot.get("type") != value_type
                or local_slot.get("semantic_role") != semantic_role
            ):
                fail("ROLE_TYPE_STABLE", f"{family_slot_id}:{record_id}")
                member_ok = False

        family_slot_reports.append(
            {
                "family_slot_id": family_slot_id,
                "status": "PASS" if member_ok else "REVISE",
                "member_count": len(members),
                "required_across_records": required,
            }
        )

    all_local_members = {
        (record_id, uid)
        for record_id, slots in local_slots.items()
        for uid in slots
    }
    if mapped_members != all_local_members:
        missing = len(all_local_members - mapped_members)
        extra = len(mapped_members - all_local_members)
        fail("LOCAL_SLOT_COVERAGE", f"missing_{missing}:extra_{extra}")

    variants = bundle.get("variants")
    if not isinstance(variants, list) or not variants:
        fail("VARIANT_ID_UNIQUE", "missing")
        variants = []
    record_map = {
        record["id"]: record
        for record in records
        if isinstance(record, dict) and isinstance(record.get("id"), str)
    }
    seen_variant_ids: set[str] = set()
    assigned_records: list[str] = []
    variant_reports: list[dict[str, Any]] = []

    for index, variant in enumerate(variants, start=1):
        if not isinstance(variant, dict):
            fail("VARIANT_ID_UNIQUE", f"variant_{index}")
            continue
        variant_id = variant.get("variant_id")
        variant_record_ids = variant.get("record_ids")
        if not isinstance(variant_id, str) or not variant_id:
            fail("VARIANT_ID_UNIQUE", f"variant_{index}")
            variant_id = f"INVALID_{index}"
        elif variant_id in seen_variant_ids:
            fail("VARIANT_ID_UNIQUE", variant_id)
        seen_variant_ids.add(variant_id)

        if not isinstance(variant_record_ids, list) or not variant_record_ids:
            fail("VARIANT_ASSIGNMENT", variant_id)
            variant_record_ids = []
        if any(record_id not in record_id_set for record_id in variant_record_ids):
            fail("VARIANT_ASSIGNMENT", f"{variant_id}:unknown_record")
        assigned_records.extend(
            record_id for record_id in variant_record_ids if record_id in record_id_set
        )

        skeletons = {
            normalized_skeleton(record_map[record_id])
            for record_id in variant_record_ids
            if record_id in record_map
        }
        skeleton_ok = len(skeletons) == 1 and "" not in skeletons
        if not skeleton_ok:
            fail("VARIANT_SKELETON_STABLE", variant_id)
        skeleton = next(iter(skeletons), "")
        variant_reports.append(
            {
                "variant_id": variant_id,
                "status": "PASS" if skeleton_ok else "REVISE",
                "record_count": len(variant_record_ids),
                "skeleton_sha256": (
                    hashlib.sha256(skeleton.encode("utf-8")).hexdigest()
                    if skeleton
                    else None
                ),
            }
        )

    if len(assigned_records) != len(set(assigned_records)) or set(assigned_records) != record_id_set:
        fail("VARIANT_ASSIGNMENT", "not_exactly_once")

    return {
        "contract": FAMILY_CONTRACT,
        "status": "PASS" if not failures else "REVISE",
        "family_id": family_id,
        "record_count": len(records),
        "family_slot_count": len(family_slots),
        "variant_count": len(variants),
        "local_roundtrip": local_report.get("status"),
        "gates": gates,
        "family_slots": family_slot_reports,
        "variants": variant_reports,
        "failures": failures,
    }


def sample_bundle() -> dict[str, Any]:
    def record(record_id: str, planet: str, house: str, obj: str, particle: str = "는") -> dict[str, Any]:
        return {
            "id": record_id,
            "sentence": f"점유행성 {planet}{particle} {house}에 {obj}을 반입한다.",
            "template": f"점유행성 《{record_id}.OCCUPANT.PLANET.01》{particle} 《{record_id}.TARGET.HOUSE.01》에 《{record_id}.ACTION.OBJECT.01》을 반입한다.",
            "slots": [
                {"uid": f"{record_id}.OCCUPANT.PLANET.01", "type": "NP", "semantic_role": "occupant_planet", "value": planet, "source_ref": f"{record_id}:1"},
                {"uid": f"{record_id}.TARGET.HOUSE.01", "type": "NP", "semantic_role": "target_house", "value": house, "source_ref": f"{record_id}:2"},
                {"uid": f"{record_id}.ACTION.OBJECT.01", "type": "OBJECT", "semantic_role": "input_object", "value": obj, "source_ref": f"{record_id}:3"},
            ],
        }

    return {
        "contract": FAMILY_CONTRACT,
        "equality_mode": EQUALITY_MODE,
        "family_id": "SELF_TEST_FAMILY",
        "records": [record("S1", "Mars", "11H", "전환압력"), record("S2", "Venus", "2H", "관계자원")],
        "family_slots": [
            {"family_slot_id": "OCCUPANT", "type": "NP", "semantic_role": "occupant_planet", "required_across_records": True, "members": {"S1": "S1.OCCUPANT.PLANET.01", "S2": "S2.OCCUPANT.PLANET.01"}},
            {"family_slot_id": "HOUSE", "type": "NP", "semantic_role": "target_house", "required_across_records": True, "members": {"S1": "S1.TARGET.HOUSE.01", "S2": "S2.TARGET.HOUSE.01"}},
            {"family_slot_id": "OBJECT", "type": "OBJECT", "semantic_role": "input_object", "required_across_records": True, "members": {"S1": "S1.ACTION.OBJECT.01", "S2": "S2.ACTION.OBJECT.01"}},
        ],
        "variants": [{"variant_id": "V1", "record_ids": ["S1", "S2"]}],
    }


def self_test() -> dict[str, Any]:
    valid = sample_bundle()
    cases: dict[str, tuple[dict[str, Any], str]] = {}

    role_mismatch = copy.deepcopy(valid)
    role_mismatch["family_slots"][0]["semantic_role"] = "house_lord"
    cases["role_mismatch"] = (role_mismatch, "ROLE_TYPE_STABLE")

    missing_required = copy.deepcopy(valid)
    del missing_required["family_slots"][0]["members"]["S2"]
    cases["missing_required"] = (missing_required, "REQUIRED_COVERAGE")

    unmapped = copy.deepcopy(valid)
    unmapped["family_slots"].pop()
    cases["unmapped"] = (unmapped, "LOCAL_SLOT_COVERAGE")

    duplicate_member = copy.deepcopy(valid)
    duplicate_member["family_slots"].append(
        {"family_slot_id": "OCCUPANT_DUP", "type": "NP", "semantic_role": "occupant_planet", "required_across_records": False, "members": {"S1": "S1.OCCUPANT.PLANET.01"}}
    )
    cases["duplicate_member"] = (duplicate_member, "MEMBER_UID_UNIQUE")

    mixed_variant = copy.deepcopy(valid)
    mixed_variant["records"][1] = sample_bundle()["records"][1]
    mixed_variant["records"][1]["sentence"] = "점유행성 Venus가 2H에 관계자원을 반입한다."
    mixed_variant["records"][1]["template"] = "점유행성 《S2.OCCUPANT.PLANET.01》가 《S2.TARGET.HOUSE.01》에 《S2.ACTION.OBJECT.01》을 반입한다."
    cases["mixed_variant"] = (mixed_variant, "VARIANT_SKELETON_STABLE")

    valid_report = audit_family_bundle(valid)
    failures: list[str] = []
    invalid_reports: dict[str, dict[str, Any]] = {}
    if valid_report.get("status") != "PASS":
        failures.append("valid_case")

    for name, (bundle, expected_gate) in cases.items():
        report = audit_family_bundle(bundle)
        detected = report.get("status") == "REVISE" and report.get("gates", {}).get(expected_gate) is False
        invalid_reports[name] = {
            "status": report.get("status"),
            "expected_gate": expected_gate,
            "detected": detected,
        }
        if not detected:
            failures.append(name)

    return {
        "contract": "TITI_FAMILY_GRAMMAR_SELF_TEST_V1",
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
        report = audit_family_bundle(load_bundle(args.bundle)) if args.command == "audit" else self_test()
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        report = {"status": "REVISE", "failures": [f"INPUT:{type(exc).__name__}:{exc}"]}

    if getattr(args, "json", False):
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"TITI_FAMILY_GRAMMAR={report['status']}")
        print(f"FAILURES={','.join(report.get('failures', [])) or 'NONE'}")
    return 0 if report.get("status") == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

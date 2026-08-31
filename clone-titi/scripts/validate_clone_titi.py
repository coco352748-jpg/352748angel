#!/usr/bin/env python3
"""Validate clone-titi identity, top locks, isolation, and roundtrip runtime."""

from __future__ import annotations

import json
from pathlib import Path
import sys

from family_grammar_guard import (
    audit_family_bundle,
    load_bundle as load_family_bundle,
    self_test as family_self_test,
)
from micro_template_design_guard import (
    audit_design_bundle,
    load_bundle as load_micro_design_bundle,
    self_test as micro_design_self_test,
)
from reverse_render_guard import (
    audit_bundle as audit_reverse_bundle,
    load_bundle as load_reverse_bundle,
    self_test as reverse_self_test,
)
from v3_v7_micro_forge_guard import self_test as v3_v7_forge_self_test


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    failures: list[str] = []
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    contract = (ROOT / "references" / "TITI_REVERSE_RENDER_CONTRACT.md").read_text(
        encoding="utf-8"
    )
    family_contract = (
        ROOT / "references" / "TITI_FAMILY_GRAMMAR_FORGE.md"
    ).read_text(encoding="utf-8")
    micro_design_contract = (
        ROOT / "references" / "TITI_MICRO_TEMPLATE_DESIGN.md"
    ).read_text(encoding="utf-8")
    v3_v7_contract = (
        ROOT / "references" / "TITI_V3_V7_MICRO_FORGE.md"
    ).read_text(encoding="utf-8")
    interface = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")

    checks = {
        "call_key": "CALL_KEY=$clone-titi" in skill and "$clone-titi" in interface,
        "identity": "IDENTITY=TITI" in skill and "IDENTITY=TITI" in contract,
        "target_routing_lock": (
            "0. TARGET과 ROUTING은 사용자의 지시사항에 100% 일치되게 한다." in skill
        ),
        "fna98_output_lock": "1. 출력물은 항상 FNa98을 준수한다." in skill,
        "lineage_isolation": (
            "LINEAGE=INDEPENDENT" in skill
            and "TITI is a new identity with a self-contained route." in skill
            and "AUTO_ROUTE" not in skill
        ),
        "contract": (
            "CONTRACT=TITI_MICRO_ROUNDTRIP_V1" in contract
            and "EQUALITY_MODE=EXACT_SURFACE" in contract
        ),
        "family_grammar_contract": (
            "CONTRACT=TITI_FAMILY_GRAMMAR_V1" in family_contract
            and "FAMILY_GRAMMAR_FORGE" in skill
        ),
        "micro_template_design_contract": (
            "CONTRACT=TITI_MICRO_TEMPLATE_DESIGN_V1" in micro_design_contract
            and "MICRO_TEMPLATE_DESIGN" in skill
            and "NOT_APPLICABLE_UNTIL_FILLED" in micro_design_contract
        ),
        "v3_v7_micro_forge_contract": (
            "CONTRACT=TITI_V3_V7_MICRO_FORGE_V1" in v3_v7_contract
            and "V3_V7_MICRO_FORGE" in skill
            and "FNA98_DESIGN_READY" in v3_v7_contract
            and "FNA98_SENTENCE_PASS" in v3_v7_contract
            and "Density" in v3_v7_contract
            and "Resolution" in v3_v7_contract
            and "Completeness" in v3_v7_contract
        ),
    }
    for name, passed in checks.items():
        if not passed:
            failures.append(name)

    runtime = reverse_self_test()
    example = audit_reverse_bundle(
        load_reverse_bundle(ROOT / "assets" / "example_bundle.json")
    )
    family_runtime = family_self_test()
    family_example = audit_family_bundle(
        load_family_bundle(ROOT / "assets" / "example_family_bundle.json")
    )
    micro_design_runtime = micro_design_self_test()
    micro_design_example = audit_design_bundle(
        load_micro_design_bundle(
            ROOT / "assets" / "example_micro_template_design_bundle.json"
        )
    )
    v3_v7_runtime = v3_v7_forge_self_test()
    if runtime.get("status") != "PASS":
        failures.append("reverse_render_self_test")
    if example.get("status") != "PASS":
        failures.append("example_roundtrip")
    if family_runtime.get("status") != "PASS":
        failures.append("family_grammar_self_test")
    if family_example.get("status") != "PASS":
        failures.append("example_family_grammar")
    if micro_design_runtime.get("status") != "PASS":
        failures.append("micro_template_design_self_test")
    if micro_design_example.get("status") != "PASS":
        failures.append("example_micro_template_design")
    if v3_v7_runtime.get("status") != "PASS":
        failures.append("v3_v7_micro_forge_self_test")

    report = {
        "status": "PASS" if not failures else "REVISE",
        "skill": "clone-titi",
        "call_key": "$clone-titi" if checks["call_key"] else "REVISE",
        "identity": "TITI" if checks["identity"] else "REVISE",
        "target_routing_lock": "PASS" if checks["target_routing_lock"] else "REVISE",
        "fna98_output_lock": "PASS" if checks["fna98_output_lock"] else "REVISE",
        "lineage_isolation": "PASS" if checks["lineage_isolation"] else "REVISE",
        "contract": "PASS" if checks["contract"] else "REVISE",
        "family_grammar_contract": (
            "PASS" if checks["family_grammar_contract"] else "REVISE"
        ),
        "micro_template_design_contract": (
            "PASS" if checks["micro_template_design_contract"] else "REVISE"
        ),
        "v3_v7_micro_forge_contract": (
            "PASS" if checks["v3_v7_micro_forge_contract"] else "REVISE"
        ),
        "reverse_render_self_test": runtime.get("status"),
        "example_roundtrip": example.get("status"),
        "example_records": example.get("record_count"),
        "example_slots": example.get("slot_uid_count"),
        "family_grammar_self_test": family_runtime.get("status"),
        "example_family_grammar": family_example.get("status"),
        "example_family_records": family_example.get("record_count"),
        "example_family_slots": family_example.get("family_slot_count"),
        "example_family_variants": family_example.get("variant_count"),
        "micro_template_design_self_test": micro_design_runtime.get("status"),
        "example_micro_template_design": micro_design_example.get("status"),
        "example_micro_template_slots": micro_design_example.get("slot_count"),
        "example_micro_template_required_roles": micro_design_example.get(
            "required_role_count"
        ),
        "micro_template_exact_roundtrip_state": "NOT_APPLICABLE_UNTIL_FILLED",
        "v3_v7_micro_forge_self_test": v3_v7_runtime.get("status"),
        "v3_v7_joint_counts": v3_v7_runtime.get("expected_joint_counts"),
        "v3_v7_total_joint_count": v3_v7_runtime.get("expected_total_joint_count"),
        "v3_v7_design_fna98": v3_v7_runtime.get("valid_design_fna98", {}).get(
            "verdict"
        ),
        "v3_v7_exact_fna98": v3_v7_runtime.get("valid_exact_fna98", {}).get(
            "verdict"
        ),
        "failures": failures,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

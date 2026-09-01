#!/usr/bin/env python3
"""Validate the rq-vedic master submenu and its non-negotiable routes."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "references" / "vedic-submenu-registry.json"

EXPECTED_LEVELS = ["ELIVEDIC", "ELICOLLEGE", "ELIPHD"]
EXPECTED_D = [
    "D1", "D9", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D10",
    "D11", "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60",
]
EXPECTED_H = [f"{number}H" for number in range(1, 13)]
EXPECTED_MODULE_IDS = {
    "RASHI_BASELINE", "BHAVA_REALITY_POSITION", "RASHI_BHAVA_MOVE_JUDGMENT",
    "CO_PRESENCE_FIELD", "NAKSHATRA_BLOCK", "PADA_BLOCK", "NAKPADA_CIRCUIT",
    "PUSHKARA_REFERENCE", "UPAGRAHA_REFERENCE", "SRIPATHI_CHALIT_REFERENCE",
    "MOON_REFERENCE", "ARUDHA_SURFACE_REPRESENTATION", "STRENGTH_ASPECT_PARENT",
    "SHADBALA_COMPONENT", "DRISHTI_COMPONENT", "PLANET_ASPECT_COMPONENT",
    "BHAVA_BALA_COMPONENT", "BHAVA_ASPECT_COMPONENT", "VIMSOPAKA_COMPONENT",
    "D1_ASPECT_COMPONENT", "HOUSE_FINAL_SYNTHESIS", "MRITYU_LIMITATION_CHECK",
    "SPECIAL_POINT_AUXILIARY", "AVA_RELATIONSHIP_REFERENCE", "BHINNA_LAGNA_ROW",
    "BHINNA_SUN_ROW", "BHINNA_MOON_ROW", "BHINNA_MARS_ROW", "BHINNA_MERCURY_ROW",
    "BHINNA_JUPITER_ROW", "BHINNA_VENUS_ROW", "BHINNA_SATURN_ROW",
    "BHINNA_RAHU_ROW", "BHINNA_KETU_ROW", "SAP_STAGE", "TKS_STAGE", "EKS_STAGE",
    "SPD_STAGE", "VARGA_MINI", "VARGA_FULL", "DASHA_TIME_WINDOW",
    "TIMING_MATCH_GATE", "AVA_POST_TIMING_CONDITION", "YOGA_CONDITION_CHECK",
    "TRANSIT_CONTEXT",
}


def fail(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def norm(token: str) -> str:
    return " ".join(token.split()).casefold()


def main() -> int:
    try:
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        fail(data.get("root_skill") == "rq-vedic", "root skill must be rq-vedic")
        fail(data.get("independent_skill_creation") is False, "levels must remain submenus")

        levels = [entry["name"] for entry in data["levels"]]
        fail(levels == EXPECTED_LEVELS, f"level order mismatch: {levels}")
        fail(data["selectors"]["d_charts"] == EXPECTED_D, "20D selector order mismatch")
        fail(data["selectors"]["houses"] == EXPECTED_H, "12H selector order mismatch")
        fail(data["selectors"].get("void_d_charts") == ["D50"], "D50 must remain VOID")

        modules = data["modules"]
        by_id = {entry["id"]: entry for entry in modules}
        fail(len(by_id) == len(modules), "duplicate canonical module id")
        fail(set(by_id) == EXPECTED_MODULE_IDS, "canonical module set mismatch")
        fail(len(modules) == 45, f"expected 45 canonical modules, got {len(modules)}")

        token_owners: dict[str, str] = {}
        for module in modules:
            fail(module.get("group") in data["module_groups"], f"unknown group: {module['id']}")
            tokens = module.get("tokens")
            fail(isinstance(tokens, list) and tokens, f"module without token: {module['id']}")
            for raw in tokens:
                key = norm(raw)
                previous = token_owners.get(key)
                fail(previous is None or previous == module["id"], f"token collision: {raw}")
                token_owners[key] = module["id"]

        route_checks = {
            "RASHI_BASELINE": "1",
            "BHAVA_REALITY_POSITION": "2",
            "RASHI_BHAVA_MOVE_JUDGMENT": "3",
            "CO_PRESENCE_FIELD": "4",
            "MOON_REFERENCE": "5-4",
            "ARUDHA_SURFACE_REPRESENTATION": "6",
            "AVA_RELATIONSHIP_REFERENCE": "9",
            "VARGA_MINI": "13",
            "VARGA_FULL": "14",
            "DASHA_TIME_WINDOW": "17",
            "TIMING_MATCH_GATE": "18",
            "AVA_POST_TIMING_CONDITION": "19",
            "YOGA_CONDITION_CHECK": "20",
            "TRANSIT_CONTEXT": "21",
        }
        for module_id, route in route_checks.items():
            fail(by_id[module_id].get("master_route") == route, f"route mismatch: {module_id}")

        fail(by_id["YOGA_CONDITION_CHECK"].get("owner_adapter_route") == "21", "Yoga adapter mapping missing")
        fail(by_id["TRANSIT_CONTEXT"].get("owner_adapter_route") == "20", "Transit adapter mapping missing")
        fail(by_id["SPD_STAGE"].get("forbidden_implicit_alias") == "Sdp", "Spd/Sdp boundary missing")
        fail(by_id["VARGA_MINI"].get("legacy_coordinate_adapter") == "0-1", "Varga Mini adapter missing")
        fail(by_id["VARGA_FULL"].get("legacy_coordinate_adapter") == "0-2", "Varga Full adapter missing")

        for filename in (
            "knowledge-engine-contract.md",
            "analysis-operator-contract.md",
            "fna98-end-gate.md",
        ):
            path = ROOT / "references" / filename
            fail(path.is_file() and path.stat().st_size > 0, f"missing reference: {filename}")

        expected_schemas = {
            "source.schema.json": "urn:rq-vedic:schema:source:v1",
            "rule-card.schema.json": "urn:rq-vedic:schema:rule-card:v1",
            "case.schema.json": "urn:rq-vedic:schema:case:v1",
            "execution.schema.json": "urn:rq-vedic:schema:execution:v1",
        }
        for filename, schema_id in expected_schemas.items():
            path = ROOT / "schemas" / filename
            schema = json.loads(path.read_text(encoding="utf-8"))
            fail(schema.get("$id") == schema_id, f"schema id mismatch: {filename}")
            fail(schema.get("type") == "object", f"schema root must be object: {filename}")
            fail(bool(schema.get("required")), f"schema required fields missing: {filename}")

        print("PASS rq-vedic submenu: 1 root + 3 levels + 20D + 12H + 45 modules + 4 DB schemas")
        return 0
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"REVISE: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

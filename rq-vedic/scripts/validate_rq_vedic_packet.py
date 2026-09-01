#!/usr/bin/env python3
"""Validate the structural contract of an RQ Vedic 19-layer packet."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


VALID_LAYER_STATUS = {"PASS", "HOLD", "NOT_APPLICABLE", "CONFLICT"}
VALID_SCHOLAR_STATUS = {"NOT_REQUESTED", "NOT_APPLICABLE", "HOLD", "APPLIED"}
LEVEL_FIELDS = {
    "ELIVEDIC": {"agent_id", "input_refs", "observations", "boundaries", "unknowns", "output_ref"},
    "ELICOLLEGE": {
        "agent_id", "input_ref", "input_refs", "pattern_candidates",
        "supporting_observations", "contrasts", "exceptions",
        "structured_interpretation", "output_ref",
    },
    "ELIPHD": {
        "agent_id", "input_ref", "input_refs", "deep_structure", "causal_joints",
        "counterfactual_limits", "attribution", "recovery",
        "residual_uncertainty", "final_layer_interpretation", "output_ref",
    },
}
HANDOFF_FIELDS = {"from_layer", "to_layer", "passed_refs", "unresolved", "blocked_claims"}
LAYER3_CHECKS = {
    "rashi_raw_preserved", "bhava_raw_preserved", "planet_not_deleted",
    "degree_conflict_propagated", "full_packet_before_role_filter",
}


def load_map() -> dict[str, Any]:
    path = Path(__file__).resolve().parents[1] / "references" / "19-layer-agent-map.json"
    return json.loads(path.read_text(encoding="utf-8"))


def missing(obj: Any, required: set[str]) -> list[str]:
    return sorted(required - set(obj)) if isinstance(obj, dict) else sorted(required)


def validate(packet: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    layer_map = load_map()
    expected_specs = layer_map["layers"]
    expected_route = layer_map["route"]

    if packet.get("protocol_id") != layer_map["protocol_id"]:
        errors.append(f"protocol_id must be {layer_map['protocol_id']}")

    lock = packet.get("chart_input_lock")
    for field in missing(lock, {"status", "target", "source_lanes", "input_refs", "unknowns", "conflicts", "calculation_settings"}):
        errors.append(f"chart_input_lock missing {field}")

    layers = packet.get("layers")
    if not isinstance(layers, list):
        return errors + ["layers must be a list"]
    route = [x.get("layer_id") if isinstance(x, dict) else None for x in layers]
    if route != expected_route:
        errors.append(f"layer route mismatch: expected {expected_route}, got {route}")
    if len(layers) != 19:
        errors.append(f"exactly 19 layers required, got {len(layers)}")

    for index, spec in enumerate(expected_specs):
        if index >= len(layers):
            break
        layer = layers[index]
        layer_id = spec["id"]
        if not isinstance(layer, dict):
            errors.append(f"layer {layer_id} must be an object")
            continue
        if layer.get("status") not in VALID_LAYER_STATUS:
            errors.append(f"layer {layer_id}: invalid status")
        for field in ("method_admission", "source_boundary", "agents", "handoff"):
            if field not in layer:
                errors.append(f"layer {layer_id}: missing {field}")

        agents = layer.get("agents")
        if not isinstance(agents, dict):
            errors.append(f"layer {layer_id}: agents must be an object")
        else:
            for level in layer_map["level_order"]:
                agent = agents.get(level)
                for field in missing(agent, LEVEL_FIELDS[level]):
                    errors.append(f"layer {layer_id} {level}: missing {field}")
                if isinstance(agent, dict) and agent.get("agent_id") != spec["agents"][level]:
                    errors.append(f"layer {layer_id} {level}: wrong agent_id")

        for field in missing(layer.get("handoff"), HANDOFF_FIELDS):
            errors.append(f"layer {layer_id} handoff: missing {field}")

        if layer_id == "3":
            checks = layer.get("boundary_checks")
            for field in missing(checks, LAYER3_CHECKS):
                errors.append(f"layer 3 boundary_checks: missing {field}")
            if isinstance(checks, dict):
                for field in LAYER3_CHECKS:
                    if checks.get(field) is not True:
                        errors.append(f"layer 3 boundary_checks.{field} must be true")

    native_lock = packet.get("chart_native_lock")
    for field in missing(native_lock, {"status", "input_trace_complete", "method_trace_complete", "unresolved", "locked_interpretation_ref"}):
        errors.append(f"chart_native_lock missing {field}")

    overlay = packet.get("scholar_overlay")
    if not isinstance(overlay, dict):
        errors.append("scholar_overlay must be an object")
    else:
        status = overlay.get("status")
        if status not in VALID_SCHOLAR_STATUS:
            errors.append("scholar_overlay has invalid status")
        if status == "APPLIED":
            if not isinstance(native_lock, dict) or native_lock.get("status") != "PASS":
                errors.append("scholar overlay cannot precede chart-native PASS")
            for field in {"scholars", "technical_source_refs", "comparisons", "conflicts", "base_lock_reopened"}:
                if field not in overlay:
                    errors.append(f"scholar_overlay missing {field}")
            if overlay.get("base_lock_reopened") is not False:
                errors.append("base_lock_reopened must be false without user approval")

    if "qa" not in packet:
        errors.append("missing qa")
    return errors


def self_test_packet() -> dict[str, Any]:
    layer_map = load_map()
    route = layer_map["route"]
    layers: list[dict[str, Any]] = []
    for index, spec in enumerate(layer_map["layers"]):
        agents: dict[str, Any] = {}
        for level in layer_map["level_order"]:
            agent = {field: [] for field in LEVEL_FIELDS[level]}
            agent["agent_id"] = spec["agents"][level]
            agent["output_ref"] = f"{spec['id']}:{level}:out"
            if "input_ref" in agent:
                agent["input_ref"] = f"{spec['id']}:previous"
            agents[level] = agent
        layer: dict[str, Any] = {
            "layer_id": spec["id"], "status": "NOT_APPLICABLE",
            "method_admission": spec["default_admission"], "source_boundary": [],
            "agents": agents,
            "handoff": {
                "from_layer": spec["id"],
                "to_layer": route[index + 1] if index + 1 < len(route) else "CHART_NATIVE_INTERPRETATION_LOCK",
                "passed_refs": [], "unresolved": [], "blocked_claims": [],
            },
        }
        if spec["id"] == "3":
            layer["boundary_checks"] = {key: True for key in LAYER3_CHECKS}
        layers.append(layer)
    return {
        "protocol_id": layer_map["protocol_id"],
        "chart_input_lock": {
            "status": "PASS", "target": {}, "source_lanes": {
                "chart_source": {
                    "source_lane_id": None, "source_ref": None,
                    "status": "NOT_SUPPLIED", "authority_boundary": [],
                },
                "domain_coordinate": {
                    "source_lane_id": None, "source_ref": None,
                    "status": "NOT_SUPPLIED", "authority_boundary": [],
                },
            }, "input_refs": [], "unknowns": [],
            "conflicts": [], "calculation_settings": {},
        },
        "layers": layers,
        "chart_native_lock": {
            "status": "HOLD", "input_trace_complete": False,
            "method_trace_complete": False, "unresolved": [],
            "locked_interpretation_ref": None
        },
        "scholar_overlay": {"status": "NOT_REQUESTED"},
        "qa": {"status": "HOLD"},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", nargs="?")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        packet = self_test_packet()
    elif args.packet:
        packet = json.loads(Path(args.packet).read_text(encoding="utf-8"))
    else:
        parser.error("provide a packet path or --self-test")
    errors = validate(packet)
    if errors:
        print("REVISE")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

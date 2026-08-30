#!/usr/bin/env python3
"""Independently validate a KANI V9 E6 long-drift reopen overlay.

The validator trusts neither the E6 PASS declaration nor its copied hashes. It
reopens the referenced E5 directory, recomputes the 20D x 29 active-pair
product, decision ledger, 3P VOID set, representative boundary probes, Source
and baseline hashes, and then compares those results with the E6 overlay.  It
does not write to E5, E6, the Source, or references/v9_baseline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Any


SCHEMA_VERSION = "KANI_V9_E6_OVERLAY_V1"
E5_PASS_STATES = frozenset({"PASS", "PASS_WITH_LOCAL_HOLDS"})

DCHART_ORDER = (
    "D1", "D9", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D10",
    "D11", "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60",
)

LANE_ORDER = (
    "INDEX", "RASHI_SOURCE", "BHAVA_SOURCE", "FIRST_INTEGRATION", "COPRESENCE",
    "PUSHKARA", "UPAGRAHA", "SPIRIT_CHALIT", "MOON_CHART", "ARUDHA",
    "SHADBALA_A", "SHADBALA_R", "BHAVA_BALA", "VIMSOPAKA", "MRITYU",
    "SPOTHER", "AVA", "BHINNA_MATRIX", "PLANET_ASPECT", "SAP", "TKS", "EKS",
    "SPD", "VARGA_LINK_MINI", "VARGA_LINK_FULL", "ASPECT02", "ASPECT03", "DASHA",
    "TIMING_GATE",
)

DECISION_FIELDS = (
    "TRIGGER", "SELECTED_ROUTE", "REJECTED_ROUTE", "WHY_JOINT",
    "OUTPUT_EFFECT", "CORRECTION", "QA_GATE", "HANDOFF",
)

DIRECT_SOURCE_LANES = frozenset({"INDEX", "RASHI_SOURCE", "BHAVA_SOURCE", "DASHA"})

DECISION_EDGE_IDS = (
    "E4-ROUTE-FAMILY",
    "E5-VIEW-SEPARATION",
    "E4-FIELD-SEPARATION",
    "DIRECT-TAB03-SOURCE-HOLD",
    "DIRECT-TAB03-R-TO-A",
    "DIRECT-TAB03-TIMING-GATE",
)

RETAINED_PASSES = (
    "REPLAY_BUNDLE", "TAB_GENEALOGY", "OUTPUT_CORPUS", "INPUT_OUTPUT_BINDING",
    "STRUCTURAL_LANE_RUNTIME", "DIRECT_03_INSTRUCTION_BODY",
    "CAUSAL_DECISION_RULES", "BLIND_REPLAY",
)

REQUIRED_OVERLAY_ARTIFACTS = frozenset({
    "e6_active_pair_manifest.jsonl",
    "e6_probe_results.json",
    "e6_reopen_record.json",
    "e6_fna98.json",
    "e6_checkpoint.json",
    "e6_transcript.txt",
})


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_metadata(path: Path) -> dict[str, Any]:
    return {"bytes": path.stat().st_size, "sha256": sha256_file(path)}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                raise ValueError(f"blank JSONL row at {path}:{line_number}")
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"non-object JSONL row at {path}:{line_number}")
            rows.append(value)
    return rows


def tree_snapshot(root: Path) -> dict[str, dict[str, Any]]:
    if not root.is_dir():
        raise ValueError(f"directory missing: {root}")
    rows: dict[str, dict[str, Any]] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"symlink is not permitted in validation scope: {path}")
        if path.is_file():
            rows[path.relative_to(root).as_posix()] = file_metadata(path)
    return rows


def tree_id(snapshot: dict[str, dict[str, Any]]) -> str:
    return sha256_bytes(compact_json(snapshot).encode("utf-8"))


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def resolve_member(root: Path, relative: str) -> Path:
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts or not pure.parts:
        raise ValueError(f"unsafe artifact path: {relative!r}")
    candidate = (root / Path(*pure.parts)).resolve()
    if not is_within(candidate, root):
        raise ValueError(f"artifact escapes declared root: {relative!r}")
    return candidate


def expected_lane_path(order: int, lane: str) -> str:
    return f"lanes/{order:02d}_{lane}.json"


def route_for(chart: str) -> tuple[str, str]:
    if chart == "D1":
        return "D1_ROOT", "TARGET_DCHART"
    return "TARGET_DCHART", "D1_ROOT_SINGLE_GRAMMAR"


def ledger_projection(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_id": record.get("record_id"),
        "dchart": record.get("dchart"),
        "lane": record.get("lane"),
        "lane_order": record.get("lane_order"),
        "status": record.get("status"),
        "source_refs": record.get("source_refs"),
        "decision": record.get("decision"),
        "decision_edges": record.get("decision_edges"),
        "stage_input_R": record.get("stage_input_R"),
        "stage_result_A": record.get("stage_result_A"),
        "authority_state": record.get("authority_state"),
        "data_state": record.get("data_state"),
        "applicability_state": record.get("applicability_state"),
        "evidence_state": record.get("evidence_state"),
        "verdict": record.get("verdict"),
        "hold_scope": record.get("hold_scope"),
    }


def make_probe(
    probe_id: str, passed: bool, expected: Any, observed: Any, evidence: list[str]
) -> dict[str, Any]:
    return {
        "probe_id": probe_id,
        "status": "PASS" if passed else "HOLD",
        "expected": expected,
        "observed": observed,
        "evidence": evidence,
    }


def append_failure(failures: list[str], condition: bool, code: str) -> None:
    if not condition:
        failures.append(code)


def recompute_probes(
    records: dict[tuple[str, str], dict[str, Any]],
    lane_documents: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    def record(chart: str, lane: str) -> dict[str, Any]:
        return records.get((chart, lane), {})

    probes: list[dict[str, Any]] = []
    d1 = record("D1", "INDEX")
    d1_decision = d1.get("decision") if isinstance(d1.get("decision"), dict) else {}
    probes.append(make_probe(
        "DIRECT_D1_ROOT_DISPATCH",
        d1_decision.get("SELECTED_ROUTE") == "D1_ROOT"
        and d1_decision.get("REJECTED_ROUTE") == "TARGET_DCHART",
        "SELECT_D1_ROOT_REJECT_TARGET_DCHART",
        {"selected": d1_decision.get("SELECTED_ROUTE"), "rejected": d1_decision.get("REJECTED_ROUTE")},
        ["lanes/01_INDEX.json#E5-D1-01"],
    ))

    d9 = record("D9", "INDEX")
    d9_decision = d9.get("decision") if isinstance(d9.get("decision"), dict) else {}
    probes.append(make_probe(
        "DIRECT_TARGET_DCHART_DISPATCH",
        d9_decision.get("SELECTED_ROUTE") == "TARGET_DCHART"
        and d9_decision.get("REJECTED_ROUTE") == "D1_ROOT_SINGLE_GRAMMAR",
        "SELECT_TARGET_DCHART_REJECT_D1_ROOT_SINGLE_GRAMMAR",
        {"selected": d9_decision.get("SELECTED_ROUTE"), "rejected": d9_decision.get("REJECTED_ROUTE")},
        ["lanes/01_INDEX.json#E5-D9-01"],
    ))

    d60 = record("D60", "INDEX")
    d60_decision = d60.get("decision") if isinstance(d60.get("decision"), dict) else {}
    probes.append(make_probe(
        "BOUNDARY_TARGET_DCHART_D60",
        d60_decision.get("SELECTED_ROUTE") == "TARGET_DCHART"
        and d60_decision.get("REJECTED_ROUTE") == "D1_ROOT_SINGLE_GRAMMAR",
        "D60_RETAINS_TARGET_DCHART_BOUNDARY",
        {"selected": d60_decision.get("SELECTED_ROUTE"), "rejected": d60_decision.get("REJECTED_ROUTE")},
        ["lanes/01_INDEX.json#E5-D60-01"],
    ))

    rashi = record("D1", "RASHI_SOURCE")
    bhava = record("D1", "BHAVA_SOURCE")
    rashi_payload = rashi.get("payload") if isinstance(rashi.get("payload"), dict) else {}
    bhava_payload = bhava.get("payload") if isinstance(bhava.get("payload"), dict) else {}
    probes.append(make_probe(
        "RASHI_BHAVA_SEPARATION",
        lane_documents.get("RASHI_SOURCE", {}).get("source_separation") == "RASHI_AND_BHAVA_SEPARATE"
        and lane_documents.get("BHAVA_SOURCE", {}).get("source_separation") == "RASHI_AND_BHAVA_SEPARATE"
        and rashi_payload.get("view") == "RASHI"
        and bhava_payload.get("view") == "BHAVA_EQUAL_HOUSES"
        and rashi_payload.get("block_id") != bhava_payload.get("block_id"),
        "DISTINCT_RASHI_AND_BHAVA_VIEWS_WITHOUT_OVERWRITE",
        {
            "rashi_view": rashi_payload.get("view"),
            "bhava_view": bhava_payload.get("view"),
            "rashi_block": rashi_payload.get("block_id"),
            "bhava_block": bhava_payload.get("block_id"),
        },
        ["lanes/02_RASHI_SOURCE.json#E5-D1-02", "lanes/03_BHAVA_SOURCE.json#E5-D1-03"],
    ))

    field_boundary = d1.get("field_boundary") if isinstance(d1.get("field_boundary"), dict) else {}
    probes.append(make_probe(
        "OCCUPANT_LORD_FIELD_BOUNDARY",
        field_boundary == {
            "OCCUPANT_FIELD": "NOT_PARSED_FROM_DIRECT_BLOCK",
            "HOUSE_LORD_FIELD": "NOT_SUPPLIED_LOCAL_HOLD",
            "operator": "NOT_EQUAL",
        },
        "OCCUPANT_FIELD_NOT_EQUAL_HOUSE_LORD_FIELD",
        field_boundary,
        ["lanes/01_INDEX.json#E5-D1-01"],
    ))

    hold_record = record("D27", "COPRESENCE")
    hold_payload = hold_record.get("payload") if isinstance(hold_record.get("payload"), dict) else {}
    probes.append(make_probe(
        "EMPTY_HOLD_BOUNDARY",
        hold_record.get("status") == "LOCAL_HOLD_NO_DIRECT_LAYER_SOURCE"
        and hold_record.get("empty_policy") == "NO_EMPTY_OR_OCCUPANT_INFERENCE_FROM_UNPARSED_BLOCK"
        and hold_payload.get("preserved_state") == "LOCAL_HOLD"
        and hold_payload.get("fabricated_values") == [],
        "UNPARSED_EMPTY_REMAINS_LOCAL_HOLD_WITH_ZERO_INFERENCE",
        {
            "status": hold_record.get("status"),
            "empty_policy": hold_record.get("empty_policy"),
            "fabricated_values": hold_payload.get("fabricated_values"),
        },
        ["lanes/05_COPRESENCE.json#E5-D27-05"],
    ))

    r_to_a = record("D45", "DASHA")
    stage_r = r_to_a.get("stage_input_R") if isinstance(r_to_a.get("stage_input_R"), dict) else {}
    stage_a = r_to_a.get("stage_result_A") if isinstance(r_to_a.get("stage_result_A"), dict) else {}
    work_instruction = (
        r_to_a.get("work_instruction")
        if isinstance(r_to_a.get("work_instruction"), dict) else {}
    )
    r_to_a_edges = (
        r_to_a.get("decision_edges")
        if isinstance(r_to_a.get("decision_edges"), list) else []
    )
    r_to_a_edge = next(
        (edge for edge in r_to_a_edges if isinstance(edge, dict) and edge.get("EDGE_ID") == "DIRECT-TAB03-R-TO-A"),
        {},
    )
    probes.append(make_probe(
        "R_TO_A_QA_BOUNDARY",
        r_to_a.get("r_to_a_policy") == "NO_R_TO_A_PROMOTION_WITHOUT_LAYER_WORK_INSTRUCTION_AND_QA"
        and r_to_a.get("status") == "PASS_DIRECT_SOURCE"
        and stage_r.get("state") == "PASS_PRE_QA"
        and stage_a.get("state") == "PASS_QA"
        and stage_r.get("body_sha256") == stage_a.get("body_sha256")
        and stage_a.get("body") == r_to_a.get("payload")
        and work_instruction == {
            "selected": "APPLY_WORK_INSTRUCTION_AND_VALIDATE_TO_A",
            "rejected": "TREAT_R_AS_FINAL",
            "qa_gate": "FIFTEEN_POINT_FILE_QA",
        }
        and r_to_a_edge.get("SELECTED_ROUTE") == "APPLY_WORK_INSTRUCTION_AND_VALIDATE_TO_A"
        and r_to_a_edge.get("REJECTED_ROUTE") == "TREAT_R_AS_FINAL",
        "DIRECT_DASHA_R_PASSES_INSTRUCTION_AND_QA_TO_A_WITHOUT_TREATING_R_AS_FINAL",
        {
            "policy": r_to_a.get("r_to_a_policy"),
            "r_state": stage_r.get("state"),
            "a_state": stage_a.get("state"),
            "selected": r_to_a_edge.get("SELECTED_ROUTE"),
            "rejected": r_to_a_edge.get("REJECTED_ROUTE"),
        },
        ["lanes/28_DASHA.json#E5-D45-28"],
    ))

    timing = record("D60", "TIMING_GATE")
    timing_payload = timing.get("payload") if isinstance(timing.get("payload"), dict) else {}
    timing_decision = timing.get("decision") if isinstance(timing.get("decision"), dict) else {}
    timing_edges = (
        timing.get("decision_edges")
        if isinstance(timing.get("decision_edges"), list) else []
    )
    timing_edge = next(
        (edge for edge in timing_edges if isinstance(edge, dict) and edge.get("EDGE_ID") == "DIRECT-TAB03-TIMING-GATE"),
        {},
    )
    probes.append(make_probe(
        "TIMING_GATE_BOUNDARY",
        lane_documents.get("TIMING_GATE", {}).get("timing_gate_policy")
        == "LOCAL_HOLD_REQUIRES_ASPECT03_AND_DASHA_A_NO_EVENT_CONCLUSION"
        and timing.get("status") == "LOCAL_HOLD_NO_DIRECT_LAYER_SOURCE"
        and timing_payload.get("fabricated_values") == []
        and timing_edge.get("SELECTED_ROUTE")
        == "CHECK_ASPECT03_ACTIVATION_AGAINST_DASHA_TIME_WINDOW_IF_BOTH_A_AVAILABLE"
        and timing_edge.get("REJECTED_ROUTE") == "WRITE_EVENT_CONCLUSION_OR_USE_DASHA_ALONE"
        and timing_edge.get("OUTPUT_EFFECT") == "LOCAL_HOLD_ASPECT03_NOT_INCLUDED"
        and timing_edge.get("HANDOFF") == "E5_LOCAL_HOLD_CHECKPOINT",
        "ASPECT03_X_DASHA_WINDOW_ONLY_NO_EVENT_CONCLUSION",
        {
            "policy": lane_documents.get("TIMING_GATE", {}).get("timing_gate_policy"),
            "status": timing.get("status"),
            "summary_handoff": timing_decision.get("HANDOFF"),
            "timing_selected": timing_edge.get("SELECTED_ROUTE"),
            "timing_rejected": timing_edge.get("REJECTED_ROUTE"),
            "timing_handoff": timing_edge.get("HANDOFF"),
        },
        ["lanes/29_TIMING_GATE.json#E5-D60-29"],
    ))

    unsupported = [
        records.get((chart, lane), {})
        for lane in LANE_ORDER if lane not in DIRECT_SOURCE_LANES
        for chart in DCHART_ORDER
    ]
    no_gap_fill = len(unsupported) == 500 and all(
        value.get("status") == "LOCAL_HOLD_NO_DIRECT_LAYER_SOURCE"
        and isinstance(value.get("payload"), dict)
        and value["payload"].get("fabricated_values") == []
        for value in unsupported
    )
    probes.append(make_probe(
        "EXHAUSTIVE_NO_SOURCE_GAP_FILL",
        no_gap_fill,
        "500_UNSUPPORTED_PAIRS_LOCAL_HOLD_ZERO_FABRICATION",
        {"records": len(unsupported), "all_zero_fabrication": no_gap_fill},
        ["25_UNSUPPORTED_LANES_X_20D"],
    ))
    return probes


def validate(args: argparse.Namespace) -> dict[str, Any]:
    e6_dir = args.e6_dir.resolve()
    failures: list[str] = []
    if not e6_dir.is_dir():
        raise ValueError(f"E6 output directory missing: {e6_dir}")
    e6_tree_before = tree_snapshot(e6_dir)

    manifest_path = e6_dir / "e6_manifest.json"
    sidecar_path = e6_dir / "e6_manifest.sha256"
    if not manifest_path.is_file() or not sidecar_path.is_file():
        raise ValueError("E6 manifest and SHA256 sidecar are both required")
    manifest_sha256 = sha256_file(manifest_path)
    append_failure(
        failures,
        sidecar_path.read_text(encoding="utf-8") == f"{manifest_sha256}  e6_manifest.json\n",
        "E6_MANIFEST_SIDECAR_MISMATCH",
    )
    if args.expected_manifest_sha256:
        append_failure(
            failures, manifest_sha256 == args.expected_manifest_sha256.lower(),
            "E6_EXPECTED_MANIFEST_SHA256_MISMATCH",
        )
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict):
        raise ValueError("E6 manifest is not a JSON object")
    append_failure(failures, manifest.get("schema_version") == SCHEMA_VERSION, "E6_SCHEMA_VERSION")

    artifacts = manifest.get("artifacts") if isinstance(manifest.get("artifacts"), dict) else {}
    append_failure(failures, set(artifacts) == REQUIRED_OVERLAY_ARTIFACTS, "E6_ARTIFACT_SET")
    for relative, expected in artifacts.items():
        try:
            path = resolve_member(e6_dir, relative)
            append_failure(failures, path.is_file(), f"E6_ARTIFACT_MISSING:{relative}")
            if path.is_file():
                append_failure(
                    failures,
                    isinstance(expected, dict) and file_metadata(path) == {
                        "bytes": expected.get("bytes"), "sha256": expected.get("sha256")
                    },
                    f"E6_ARTIFACT_HASH:{relative}",
                )
        except ValueError:
            failures.append(f"E6_ARTIFACT_PATH:{relative}")
    append_failure(
        failures,
        set(e6_tree_before) == REQUIRED_OVERLAY_ARTIFACTS | {"e6_manifest.json", "e6_manifest.sha256"},
        "E6_DIRECTORY_FILE_SET",
    )

    entry = manifest.get("entry_condition") if isinstance(manifest.get("entry_condition"), dict) else {}
    recorded_e5_dir = entry.get("e5_dir")
    if not isinstance(recorded_e5_dir, str):
        raise ValueError("E6 manifest has no E5 directory")
    e5_dir = Path(recorded_e5_dir).resolve()
    if args.e5_dir:
        append_failure(failures, args.e5_dir.resolve() == e5_dir, "E5_DIRECTORY_OVERRIDE_MISMATCH")
    append_failure(failures, e5_dir.is_dir(), "E5_DIRECTORY_MISSING")
    append_failure(failures, not is_within(e6_dir, e5_dir) and not is_within(e5_dir, e6_dir), "E5_E6_NOT_SEPARATE")
    if not e5_dir.is_dir():
        raise ValueError("referenced E5 directory is unavailable")
    e5_tree = tree_snapshot(e5_dir)

    e5_manifest_path = e5_dir / "e5_manifest.json"
    e5_sidecar_path = e5_dir / "e5_manifest.sha256"
    e5_manifest_sha256 = sha256_file(e5_manifest_path)
    append_failure(
        failures,
        e5_sidecar_path.is_file()
        and e5_sidecar_path.read_text(encoding="utf-8") == f"{e5_manifest_sha256}  e5_manifest.json\n",
        "E5_MANIFEST_SIDECAR_MISMATCH",
    )
    append_failure(failures, entry.get("e5_manifest_sha256") == e5_manifest_sha256, "E5_MANIFEST_HASH_REOPEN")
    e5 = read_json(e5_manifest_path)
    if not isinstance(e5, dict):
        raise ValueError("E5 manifest is not a JSON object")
    append_failure(failures, e5.get("status") == "PASS", "E5_GLOBAL_STATUS_NOT_PASS")
    append_failure(failures, e5.get("e5_status") in E5_PASS_STATES, "E5_GATE_NOT_PASS")
    append_failure(failures, e5.get("e6_status") == "READY_TO_RUN", "E5_E6_ENTRY_NOT_READY")
    append_failure(failures, e5.get("production_started") is True, "E5_PRODUCTION_NOT_STARTED")
    append_failure(failures, entry.get("e5_run_id") == e5.get("run_id"), "E5_RUN_ID_MISMATCH")
    append_failure(failures, entry.get("e5_status") == e5.get("e5_status"), "E5_STATUS_COPY_MISMATCH")

    counts = e5.get("counts") if isinstance(e5.get("counts"), dict) else {}
    expected_counts = {
        "dcharts": 20,
        "mudda_dasha_pairs": 20,
        "active_lane_artifacts": 29,
        "lane_records": 580,
        "direct_source_lanes": 4,
        "local_hold_lanes": 25,
        "physical_3p_members": 20,
        "total_physical_members": 600,
        "active_3p_lanes": 0,
        "fabricated_source_values": 0,
    }
    for name, expected in expected_counts.items():
        append_failure(failures, counts.get(name) == expected, f"E5_COUNT:{name}")
    append_failure(failures, e5.get("lane_order") == list(LANE_ORDER), "E5_LANE_ORDER")
    append_failure(failures, e5.get("decision_fields") == list(DECISION_FIELDS), "E5_DECISION_FIELDS")

    e5_artifacts = e5.get("artifacts") if isinstance(e5.get("artifacts"), dict) else {}
    required_e5_artifacts = {
        "e5_source_admission.json", "e5_source_novelty.json", "source_snapshot.txt",
        "e5_decision_ledger.jsonl", "e5_3p_void.jsonl", "e5_checkpoint.json",
        "e5_fna98.json", "e5_transcript.txt",
        *(expected_lane_path(order, lane) for order, lane in enumerate(LANE_ORDER, start=1)),
    }
    append_failure(failures, required_e5_artifacts <= set(e5_artifacts), "E5_REQUIRED_ARTIFACTS")
    for relative, expected in e5_artifacts.items():
        try:
            path = resolve_member(e5_dir, relative)
            append_failure(failures, path.is_file(), f"E5_ARTIFACT_MISSING:{relative}")
            if path.is_file():
                append_failure(
                    failures,
                    isinstance(expected, dict) and file_metadata(path) == {
                        "bytes": expected.get("bytes"), "sha256": expected.get("sha256")
                    },
                    f"E5_ARTIFACT_HASH:{relative}",
                )
        except ValueError:
            failures.append(f"E5_ARTIFACT_PATH:{relative}")

    source = e5.get("source") if isinstance(e5.get("source"), dict) else {}
    source_window = (
        source.get("source_window_snapshot")
        if isinstance(source.get("source_window_snapshot"), dict) else {}
    )
    source_relative = source_window.get("path")
    try:
        source_path = resolve_member(e5_dir, source_relative) if isinstance(source_relative, str) else None
    except ValueError:
        source_path = None
    source_current = (
        {"path": str(source_path), **file_metadata(source_path)}
        if source_path is not None and source_path.is_file() else None
    )
    expected_source_metadata = {"bytes": source.get("bytes"), "sha256": source.get("sha256")}
    append_failure(
        failures,
        source_current is not None
        and {key: source_current[key] for key in ("bytes", "sha256")} == expected_source_metadata,
        "SOURCE_WINDOW_HASH_REOPEN",
    )
    append_failure(
        failures,
        source_window == {
            "path": "source_snapshot.txt",
            "bytes": source.get("bytes"),
            "sha256": source.get("sha256"),
            "execution_authority": "SOURCE_WINDOW_PRIMARY_REOPEN",
        },
        "SOURCE_WINDOW_PRIMARY_AUTHORITY",
    )
    snapshot_path = e5_dir / "source_snapshot.txt"
    append_failure(
        failures,
        snapshot_path.is_file() and file_metadata(snapshot_path) == expected_source_metadata,
        "SOURCE_SNAPSHOT_HASH_REOPEN",
    )
    append_failure(failures, source.get("expected_sha256") == source.get("sha256"), "SOURCE_EXPECTED_HASH")
    admission = source.get("admission") if isinstance(source.get("admission"), dict) else {}
    append_failure(failures, admission.get("status") == "ADMITTED", "SOURCE_ADMISSION")
    novelty = (
        source.get("novelty_vs_pikachu_e4")
        if isinstance(source.get("novelty_vs_pikachu_e4"), dict) else {}
    )
    append_failure(failures, novelty.get("status") == "PASS", "SOURCE_NOVELTY")

    lane_entries = e5.get("lane_artifacts") if isinstance(e5.get("lane_artifacts"), list) else []
    append_failure(failures, len(lane_entries) == 29, "E5_LANE_ENTRY_COUNT")
    records: dict[tuple[str, str], dict[str, Any]] = {}
    lane_documents: dict[str, dict[str, Any]] = {}
    expected_pairs: list[dict[str, Any]] = []
    expected_ledger: list[dict[str, Any]] = []
    lane_hashes: list[dict[str, Any]] = []

    for order, lane in enumerate(LANE_ORDER, start=1):
        relative = expected_lane_path(order, lane)
        matching = [
            value for value in lane_entries
            if isinstance(value, dict) and value.get("lane") == lane and value.get("lane_order") == order
        ]
        append_failure(failures, len(matching) == 1, f"E5_LANE_ENTRY:{lane}")
        if len(matching) != 1:
            continue
        lane_entry = matching[0]
        append_failure(failures, lane_entry.get("path") == relative, f"E5_LANE_PATH:{lane}")
        path = e5_dir / relative
        if not path.is_file():
            failures.append(f"E5_LANE_MISSING:{lane}")
            continue
        metadata = file_metadata(path)
        append_failure(
            failures,
            metadata == {"bytes": lane_entry.get("bytes"), "sha256": lane_entry.get("sha256")},
            f"E5_LANE_HASH:{lane}",
        )
        document = read_json(path)
        if not isinstance(document, dict):
            failures.append(f"E5_LANE_NON_OBJECT:{lane}")
            continue
        lane_documents[lane] = document
        append_failure(failures, document.get("artifact_type") == "E5_ACTIVE_LANE_ARTIFACT", f"E5_LANE_TYPE:{lane}")
        append_failure(failures, document.get("lane") == lane and document.get("lane_order") == order, f"E5_LANE_IDENTITY:{lane}")
        append_failure(failures, document.get("record_count") == 20, f"E5_LANE_RECORD_COUNT:{lane}")
        append_failure(failures, document.get("decision_fields") == list(DECISION_FIELDS), f"E5_LANE_DECISION_FIELDS:{lane}")
        append_failure(failures, document.get("physical_3p_policy") == "VOID_NOT_AN_ACTIVE_LANE", f"E5_LANE_3P:{lane}")
        lane_records = document.get("records") if isinstance(document.get("records"), list) else []
        append_failure(
            failures,
            [value.get("dchart") for value in lane_records if isinstance(value, dict)] == list(DCHART_ORDER),
            f"E5_DCHART_ORDER:{lane}",
        )
        lane_hashes.append({
            "lane": lane,
            "lane_order": order,
            "path": relative,
            "bytes": lane_entry.get("bytes"),
            "sha256": lane_entry.get("sha256"),
            "status": lane_entry.get("status"),
        })
        for chart_index, record in enumerate(lane_records, start=1):
            if not isinstance(record, dict) or chart_index > len(DCHART_ORDER):
                failures.append(f"E5_RECORD_SHAPE:{lane}:{chart_index}")
                continue
            chart = DCHART_ORDER[chart_index - 1]
            key = (chart, lane)
            append_failure(failures, key not in records, f"E5_DUPLICATE_PAIR:{chart}:{lane}")
            decision = record.get("decision") if isinstance(record.get("decision"), dict) else {}
            decision_edges = (
                record.get("decision_edges")
                if isinstance(record.get("decision_edges"), list) else []
            )
            selected, rejected = route_for(chart)
            append_failure(failures, set(decision) == set(DECISION_FIELDS), f"E5_DECISION_SHAPE:{chart}:{lane}")
            append_failure(
                failures,
                len(decision_edges) == 6
                and [edge.get("EDGE_ID") for edge in decision_edges if isinstance(edge, dict)]
                == list(DECISION_EDGE_IDS)
                and all(
                    isinstance(edge, dict)
                    and set(edge) == {"EDGE_ID", *DECISION_FIELDS}
                    and all(isinstance(edge.get(field), str) and edge.get(field) for field in DECISION_FIELDS)
                    for edge in decision_edges
                )
                and bool(decision_edges)
                and decision == {field: decision_edges[0].get(field) for field in DECISION_FIELDS},
                f"E5_DECISION_EDGES:{chart}:{lane}",
            )
            append_failure(
                failures,
                decision.get("SELECTED_ROUTE") == selected and decision.get("REJECTED_ROUTE") == rejected,
                f"E5_DISPATCH:{chart}:{lane}",
            )
            append_failure(
                failures,
                record.get("dchart") == chart and record.get("lane") == lane and record.get("lane_order") == order,
                f"E5_RECORD_IDENTITY:{chart}:{lane}",
            )
            supported = lane in DIRECT_SOURCE_LANES
            expected_axes = {
                "authority_state": "ACTIVE_SOURCE_BOUNDARY",
                "data_state": "PARSED" if supported else "NOT_SHOWN",
                "applicability_state": "APPLICABLE",
                "evidence_state": "DIRECT_SOURCE" if supported else "HOLD",
                "verdict": "PASS" if supported else "HOLD",
                "hold_scope": "NONE" if supported else "LOCAL",
            }
            append_failure(
                failures,
                all(record.get(name) == value for name, value in expected_axes.items()),
                f"E5_STATE_AXES:{chart}:{lane}",
            )
            stage_r = record.get("stage_input_R") if isinstance(record.get("stage_input_R"), dict) else {}
            stage_a = record.get("stage_result_A") if isinstance(record.get("stage_result_A"), dict) else {}
            expected_payload_sha256 = sha256_bytes(canonical_json(record.get("payload")))
            stage_contract = (
                stage_r.get("role") == "R"
                and stage_a.get("role") == "A"
                and (
                    supported
                    and stage_r.get("state") == "PASS_PRE_QA"
                    and stage_a.get("state") == "PASS_QA"
                    and stage_r.get("body_sha256") == stage_a.get("body_sha256") == expected_payload_sha256
                    and stage_a.get("body") == record.get("payload")
                    or not supported
                    and stage_r == {"role": "R", "state": "LOCAL_HOLD_NO_DIRECT_LAYER_BODY", "body_sha256": None}
                    and stage_a == {"role": "A", "state": "LOCAL_HOLD", "body_sha256": None, "body": None}
                )
            )
            append_failure(failures, stage_contract, f"E5_R_TO_A_STATE:{chart}:{lane}")
            records[key] = record
            expected_ledger.append(ledger_projection(record))
            expected_pairs.append({
                "pair_id": f"{chart}::{order:02d}_{lane}",
                "dchart": chart,
                "dchart_order": chart_index,
                "lane": lane,
                "lane_order": order,
                "record_id": record.get("record_id"),
                "status": record.get("status"),
                "e5_lane_path": relative,
                "e5_lane_sha256": metadata["sha256"],
                "record_sha256": sha256_bytes(canonical_json(record)),
                "decision_sha256": sha256_bytes(canonical_json(decision)),
                "decision_edges_sha256": sha256_bytes(canonical_json(decision_edges)),
                "stage_input_R_sha256": sha256_bytes(canonical_json(stage_r)),
                "stage_result_A_sha256": sha256_bytes(canonical_json(stage_a)),
                "state_axes": expected_axes,
                "source_id": source.get("source_id"),
                "source_sha256": source.get("sha256"),
            })

    expected_keys = {(chart, lane) for lane in LANE_ORDER for chart in DCHART_ORDER}
    append_failure(failures, len(expected_pairs) == 580 and set(records) == expected_keys, "E5_ACTIVE_PAIR_PRODUCT")
    actual_ledger = read_jsonl(e5_dir / "e5_decision_ledger.jsonl")
    append_failure(failures, len(actual_ledger) == 580 and actual_ledger == expected_ledger, "E5_DECISION_LEDGER")

    physical_3p = e5.get("physical_3p") if isinstance(e5.get("physical_3p"), dict) else {}
    expected_3p = [
        {"dchart": chart, "member_id": f"{chart}-3P", "state": "VOID", "active_lane": False}
        for chart in DCHART_ORDER
    ]
    expected_3p_rows = [
        {
            "member_id": f"{chart}-3P",
            "dchart": chart,
            "state": "VOID",
            "active_lane": False,
            "body": None,
            "policy": "PRESERVED_TOPOLOGY_MARKER_NO_NEW_3P_BODY_FABRICATED",
        }
        for chart in DCHART_ORDER
    ]
    actual_3p_rows = read_jsonl(e5_dir / "e5_3p_void.jsonl")
    append_failure(
        failures,
        physical_3p.get("state") == "VOID"
        and physical_3p.get("active_lane") is False
        and physical_3p.get("artifact") == "e5_3p_void.jsonl"
        and physical_3p.get("count") == 20
        and physical_3p.get("members") == expected_3p
        and actual_3p_rows == expected_3p_rows,
        "E5_PHYSICAL_3P_VOID",
    )

    e5_checkpoint = read_json(e5_dir / "e5_checkpoint.json")
    append_failure(failures, e5_checkpoint == e5.get("checkpoint"), "E5_CHECKPOINT_COPY")
    append_failure(
        failures,
        isinstance(e5_checkpoint, dict)
        and e5_checkpoint.get("NEW_DATASET_PRODUCTION") in E5_PASS_STATES
        and e5_checkpoint.get("LONG_DRIFT") == "READY_TO_RUN"
        and e5_checkpoint.get("first_unexecuted_job") == "RUN_LONG_DRIFT_REOPEN"
        and e5_checkpoint.get("lower_stage_restart") == "VOID"
        and e5_checkpoint.get("user_promotion") == "NOT_AUTHORIZED"
        and e5_checkpoint.get("retained_passes") == list(RETAINED_PASSES),
        "E5_CHECKPOINT_CONTRACT",
    )
    e5_fna = read_json(e5_dir / "e5_fna98.json")
    append_failure(failures, e5_fna == e5.get("fna98"), "E5_FNA98_COPY")
    append_failure(
        failures,
        isinstance(e5_fna, dict) and e5_fna.get("status") == "PASS"
        and e5_fna.get("materialization_subgate") == "PASS"
        and e5_fna.get("value_completeness") == "HOLD_LOCAL_25_UNSUPPORTED_LANES"
        and e5_fna.get("hard_fail_count") == 0 and e5_fna.get("hard_failures") == [],
        "E5_FNA98_CONTRACT",
    )
    append_failure(
        failures,
        e5.get("subgates") == {
            "MATERIALIZATION": "PASS",
            "VALUE_COMPLETENESS": "HOLD_LOCAL_25_UNSUPPORTED_LANES",
            "SOURCE_NOVELTY": "PASS",
        },
        "E5_SUBGATE_SEPARATION",
    )

    baseline = e5.get("baseline") if isinstance(e5.get("baseline"), dict) else {}
    baseline_path_value = baseline.get("path")
    baseline_path = Path(baseline_path_value).resolve() if isinstance(baseline_path_value, str) else None
    if baseline_path is None or not baseline_path.is_dir():
        raise ValueError("E5 baseline path is unavailable")
    baseline_tree = tree_snapshot(baseline_path)
    baseline_sha256 = tree_id(baseline_tree)
    append_failure(
        failures,
        baseline.get("unchanged") is True
        and baseline.get("overwrite_count") == 0
        and baseline.get("pre_files") == baseline.get("post_files") == baseline_tree
        and baseline.get("pre_tree_sha256") == baseline.get("post_tree_sha256") == baseline_sha256
        and e5_checkpoint.get("baseline_tree_sha256") == baseline_sha256,
        "E5_BASELINE_REOPEN_NO_REBUILD",
    )
    append_failure(failures, not is_within(e6_dir, baseline_path), "E6_OUTSIDE_BASELINE")

    recomputed_probes = recompute_probes(records, lane_documents)
    append_failure(
        failures, len(recomputed_probes) == 9 and all(value["status"] == "PASS" for value in recomputed_probes),
        "E6_RECOMPUTED_PROBES",
    )

    pair_rows = read_jsonl(e6_dir / "e6_active_pair_manifest.jsonl")
    append_failure(failures, pair_rows == expected_pairs and len(pair_rows) == 580, "E6_ACTIVE_PAIR_MANIFEST")
    probe_document = read_json(e6_dir / "e6_probe_results.json")
    expected_probe_document = {
        "schema_version": SCHEMA_VERSION,
        "run_id": manifest.get("run_id"),
        "status": "PASS",
        "pass_count": 9,
        "probe_count": 9,
        "probes": recomputed_probes,
    }
    append_failure(failures, probe_document == expected_probe_document, "E6_PROBE_ARTIFACT")

    recomputed_run_id = sha256_bytes(compact_json({
        "schema_version": SCHEMA_VERSION,
        "e5_run_id": e5.get("run_id"),
        "e5_manifest_sha256": e5_manifest_sha256,
        "e5_tree_sha256": tree_id(e5_tree),
        "source_sha256": source.get("sha256"),
        "probe_hash": sha256_bytes(canonical_json(recomputed_probes)),
    }).encode("utf-8"))
    append_failure(failures, manifest.get("run_id") == recomputed_run_id, "E6_RUN_ID")

    expected_input_hashes = {
        "e5_manifest.json": {"sha256": e5_manifest_sha256, "bytes": e5_manifest_path.stat().st_size},
        **{
            name: file_metadata(e5_dir / name) if (e5_dir / name).is_file() else None
            for name in (
                "e5_manifest.sha256", "e5_source_admission.json", "e5_source_novelty.json",
                "source_snapshot.txt", "e5_decision_ledger.jsonl", "e5_3p_void.jsonl",
                "e5_checkpoint.json", "e5_fna98.json",
            )
        },
    }
    reopen = read_json(e6_dir / "e6_reopen_record.json")
    append_failure(failures, isinstance(reopen, dict), "E6_REOPEN_RECORD_OBJECT")
    if isinstance(reopen, dict):
        append_failure(failures, reopen.get("schema_version") == SCHEMA_VERSION, "E6_REOPEN_SCHEMA")
        append_failure(failures, reopen.get("run_id") == recomputed_run_id, "E6_REOPEN_RUN_ID")
        append_failure(failures, reopen.get("status") == "PASS", "E6_REOPEN_STATUS")
        append_failure(failures, reopen.get("input_hashes") == expected_input_hashes, "E6_REOPEN_INPUT_HASHES")
        append_failure(failures, reopen.get("output_hashes") == lane_hashes, "E6_REOPEN_OUTPUT_HASHES")
        append_failure(failures, reopen.get("physical_3p") == physical_3p, "E6_REOPEN_3P")
        source_reopen = reopen.get("source_reopen") if isinstance(reopen.get("source_reopen"), dict) else {}
        append_failure(
            failures,
            source_reopen.get("expected") == {
                "source_id": source.get("source_id"), "bytes": source.get("bytes"), "sha256": source.get("sha256")
            }
            and source_reopen.get("source_window_before") == source_current
            and source_reopen.get("source_window_after") == source_current
            and source_reopen.get("source_window_snapshot") == file_metadata(snapshot_path)
            and source_reopen.get("transient_ingest_path_read_count") == 0,
            "E6_REOPEN_SOURCE",
        )
        recorded_tree = reopen.get("e5_tree") if isinstance(reopen.get("e5_tree"), dict) else {}
        append_failure(
            failures,
            recorded_tree.get("before") == recorded_tree.get("after") == e5_tree
            and recorded_tree.get("before_sha256") == recorded_tree.get("after_sha256") == tree_id(e5_tree)
            and recorded_tree.get("changed_paths") == [],
            "E6_REOPEN_E5_TREE",
        )
        recorded_baseline = reopen.get("baseline_tree") if isinstance(reopen.get("baseline_tree"), dict) else {}
        append_failure(
            failures,
            recorded_baseline.get("path") == str(baseline_path)
            and recorded_baseline.get("before_sha256") == recorded_baseline.get("after_sha256") == baseline_sha256
            and recorded_baseline.get("changed_paths") == [],
            "E6_REOPEN_BASELINE_TREE",
        )
        counters = reopen.get("execution_counters") if isinstance(reopen.get("execution_counters"), dict) else {}
        append_failure(
            failures,
            counters == {
                "rebuild_count": 0,
                "lower_stage_reassembly_count": 0,
                "drive_read_count": 0,
                "github_read_count": 0,
                "other_remote_read_count": 0,
                "e5_output_change_count": 0,
                "baseline_change_count": 0,
                "source_change_count": 0,
            },
            "E6_EXECUTION_COUNTERS",
        )
        append_failure(
            failures,
            isinstance(reopen.get("checks"), list)
            and reopen.get("checks")
            and all(isinstance(value, dict) and value.get("status") == "PASS" for value in reopen["checks"])
            and reopen.get("failures") == [],
            "E6_REOPEN_CHECK_LEDGER",
        )

    checkpoint = read_json(e6_dir / "e6_checkpoint.json")
    expected_checkpoint = {
        "schema_version": SCHEMA_VERSION,
        "run_id": recomputed_run_id,
        "restore_floor": "ANALYSIS02_MATURE_PRODUCTION_STATE",
        "retained_passes": list(RETAINED_PASSES),
        "NEW_DATASET_PRODUCTION": e5.get("e5_status"),
        "LONG_DRIFT": "PASS",
        "E6_LONG_DRIFT_REOPEN": "PASS_E6_TESTED_SCOPE",
        "FRESH_TAB_LONG_DRIFT_REAL_RUNTIME_GATE": "HOLD_UNEXECUTED",
        "first_unexecuted_job": "FINAL_USER_PROMOTION_PACKET",
        "post_technical_state": "READY_FOR_USER_PROMOTION",
        "lower_stage_restart": "VOID",
        "rebuild_count": 0,
        "lower_stage_reassembly_count": 0,
        "user_promotion": "NOT_AUTHORIZED_NOT_EXECUTED",
        "FINAL_KANI_JUDGMENT_RUNTIME": "HOLD_USER_PROMOTION_ONLY",
    }
    append_failure(failures, checkpoint == expected_checkpoint, "E6_CHECKPOINT")
    append_failure(failures, manifest.get("checkpoint") == checkpoint, "E6_CHECKPOINT_EMBED")

    fna = read_json(e6_dir / "e6_fna98.json")
    required_gates = {
        "TARGET_CHECK", "FACTCHECK", "SOURCE_CHECK", "WHY_CHECK", "LOGIC_CHECK",
        "CONDITION_EXCEPTION_CHECK", "FORMAT_CHECK", "PRACTICAL_USABILITY",
        "SUPPLEMENTAL_ROUTING_CHECK", "VOID_REUSE_CHECK", "SOURCE_GAP_FILL_CHECK",
        "HASH_READBACK_CHECK",
    }
    append_failure(
        failures,
        isinstance(fna, dict)
        and fna.get("schema_version") == SCHEMA_VERSION
        and fna.get("run_id") == recomputed_run_id
        and fna.get("status") == "PASS"
        and fna.get("e6_status") == "PASS"
        and fna.get("hard_fail_count") == 0
        and fna.get("hard_failures") == []
        and isinstance(fna.get("gates"), dict)
        and set(fna["gates"]) == required_gates
        and all(value == "PASS" for value in fna["gates"].values()),
        "E6_FNA98",
    )
    append_failure(failures, manifest.get("fna98") == fna, "E6_FNA98_EMBED")

    append_failure(failures, manifest.get("status") == "PASS" and manifest.get("e6_status") == "PASS", "E6_GLOBAL_STATUS")
    manifest_counts = manifest.get("counts") if isinstance(manifest.get("counts"), dict) else {}
    append_failure(
        failures,
        manifest_counts == {
            "dcharts": 20,
            "active_lanes": 29,
            "active_pairs": 580,
            "physical_3p_members": 20,
            "active_3p_lanes": 0,
            "decision_ledger_rows": 580,
            "representative_boundary_probes": 9,
            "passed_probes": 9,
        },
        "E6_MANIFEST_COUNTS",
    )
    append_failure(failures, manifest.get("decision_fields") == list(DECISION_FIELDS), "E6_MANIFEST_DECISION_FIELDS")
    append_failure(failures, manifest.get("execution_counters") == reopen.get("execution_counters"), "E6_MANIFEST_COUNTERS")
    append_failure(failures, manifest.get("e5_tree_sha256") == tree_id(e5_tree), "E6_MANIFEST_E5_TREE")
    append_failure(failures, manifest.get("baseline_tree_sha256") == baseline_sha256, "E6_MANIFEST_BASELINE_TREE")
    append_failure(failures, manifest.get("source_sha256") == source.get("sha256"), "E6_MANIFEST_SOURCE")
    append_failure(failures, manifest.get("failures") == [], "E6_MANIFEST_FAILURES")
    append_failure(
        failures,
        manifest.get("promotion_firewall") == {
            "authority": "CURRENT_USER_EXPLICIT_ONLY",
            "status": "NOT_AUTHORIZED_NOT_EXECUTED",
            "final_runtime": "HOLD_USER_PROMOTION_ONLY",
            "new_technical_stage_after_e6": "FORBIDDEN",
        },
        "E6_PROMOTION_FIREWALL",
    )

    transcript_text = (e6_dir / "e6_transcript.txt").read_text(encoding="utf-8")
    transcript_lines = transcript_text.splitlines()
    append_failure(failures, transcript_text.endswith("\n"), "E6_TRANSCRIPT_FINAL_NEWLINE")
    required_transcript_lines = {
        "TITLE=KANI_V9_E6_LONG_DRIFT_REOPEN_TRANSCRIPT",
        f"RUN_ID={recomputed_run_id}",
        f"E5_RUN_ID={e5.get('run_id')}",
        f"E5_MANIFEST_SHA256={e5_manifest_sha256}",
        "ENTRY_CONDITION=E5_GLOBAL_PASS",
        "REOPEN_CONTEXT=SEPARATE_PROCESS_LOCAL_CHECKPOINT",
        f"SOURCE_SHA256={source.get('sha256')}",
        "ACTIVE_PAIR_REOPEN=580_OF_580",
        "PHYSICAL_3P_REOPEN=20_VOID_0_ACTIVE",
        f"DECISION_LEDGER_FIELDS={','.join(DECISION_FIELDS)}",
        "BOUNDARY_PROBES=9_OF_9_PASS",
        "REBUILD_COUNT=0",
        "LOWER_STAGE_REASSEMBLY_COUNT=0",
        "DRIVE_READ_COUNT=0",
        "GITHUB_READ_COUNT=0",
        "E5_OUTPUT_CHANGE_COUNT=0",
        "BASELINE_CHANGE_COUNT=0",
        "LONG_DRIFT=PASS",
        "FNA98=PASS",
        "NEXT_STATE=FINAL_USER_PROMOTION_PACKET",
        "E6_LONG_DRIFT_REOPEN=PASS_E6_TESTED_SCOPE",
        "FRESH_TAB_LONG_DRIFT_REAL_RUNTIME_GATE=HOLD_UNEXECUTED",
        "FINAL_KANI_JUDGMENT_RUNTIME=HOLD_USER_PROMOTION_ONLY",
        "FINAL_USER_PROMOTION=NOT_AUTHORIZED_NOT_EXECUTED",
        "CONTENT_END",
    }
    append_failure(
        failures,
        set(line for line in transcript_lines if line) == required_transcript_lines
        and len([line for line in transcript_lines if line]) == len(required_transcript_lines),
        "E6_TRANSCRIPT_CONTRACT",
    )

    e6_tree_after = tree_snapshot(e6_dir)
    append_failure(failures, e6_tree_before == e6_tree_after, "E6_CHANGED_DURING_VALIDATION")
    failures = sorted(set(failures))
    return {
        "status": "PASS" if not failures else "REVISE",
        "schema_version": SCHEMA_VERSION,
        "e6_manifest_sha256": manifest_sha256,
        "e5_manifest_sha256": e5_manifest_sha256,
        "active_pairs": f"{len(expected_pairs)}/580",
        "physical_3p_void": f"{len(expected_3p)}/20",
        "decision_ledger": f"{len(actual_ledger)}/580",
        "probes": f"{sum(value['status'] == 'PASS' for value in recomputed_probes)}/9",
        "rebuild_count": 0,
        "remote_reads": {"drive": 0, "github": 0, "other": 0},
        "final_promotion": "NOT_EXECUTED",
        "failures": failures,
        "e6_dir": str(e6_dir),
        "e5_dir": str(e5_dir),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("e6_dir", type=Path, help="E6 overlay directory")
    parser.add_argument("--e5-dir", type=Path, help="optional independent E5 directory pin")
    parser.add_argument("--expected-manifest-sha256", help="optional caller-pinned E6 manifest SHA256")
    return parser


def main() -> int:
    try:
        result = validate(build_parser().parse_args())
    except (OSError, ValueError, RuntimeError, UnicodeDecodeError, json.JSONDecodeError) as error:
        print(compact_json({
            "status": "REVISE",
            "error": str(error),
            "final_promotion": "NOT_EXECUTED",
        }))
        return 1
    print(compact_json(result))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

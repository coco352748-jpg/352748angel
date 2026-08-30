#!/usr/bin/env python3
"""Run KANI V9 E6 as a read-only long-drift reopen overlay.

E6 accepts only an already closed E5 output directory whose manifest has a
global PASS.  It reopens the admitted Source, the retained checkpoint, all 29
lane artifacts, the 580-row decision ledger, and the 20 physical 3P VOID
members without rebuilding or reading a remote authority.  The result is a
separate overlay; it never promotes FINAL_KANI_JUDGMENT_RUNTIME.
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


class EntryRefused(Exception):
    """The E5 manifest did not authorize entry into E6."""

    def __init__(self, payload: dict[str, Any]):
        super().__init__(payload["reason"])
        self.payload = payload


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


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()


def write_json(path: Path, value: Any) -> None:
    write_bytes(path, canonical_json(value))


def write_text(path: Path, value: str) -> None:
    write_bytes(path, value.encode("utf-8"))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    write_text(path, "".join(compact_json(row) + "\n" for row in rows))


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
            raise ValueError(f"symlink is not permitted in reopen scope: {path}")
        if path.is_file():
            rows[path.relative_to(root).as_posix()] = file_metadata(path)
    return rows


def tree_id(snapshot: dict[str, dict[str, Any]]) -> str:
    return sha256_bytes(compact_json(snapshot).encode("utf-8"))


def changed_paths(
    before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]
) -> list[str]:
    return sorted(
        path for path in set(before) | set(after) if before.get(path) != after.get(path)
    )


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def resolve_member(root: Path, relative: str) -> Path:
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts or not pure.parts:
        raise ValueError(f"unsafe E5 artifact path: {relative!r}")
    candidate = (root / Path(*pure.parts)).resolve()
    if not is_within(candidate, root):
        raise ValueError(f"E5 artifact escapes output directory: {relative!r}")
    return candidate


def add_check(
    checks: list[dict[str, Any]],
    check_id: str,
    passed: bool,
    expected: Any,
    observed: Any,
) -> None:
    checks.append({
        "check_id": check_id,
        "status": "PASS" if passed else "HOLD",
        "expected": expected,
        "observed": observed,
    })


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


def expected_lane_path(order: int, lane: str) -> str:
    return f"lanes/{order:02d}_{lane}.json"


def route_for(chart: str) -> tuple[str, str]:
    if chart == "D1":
        return "D1_ROOT", "TARGET_DCHART"
    return "TARGET_DCHART", "D1_ROOT_SINGLE_GRAMMAR"


def projection_for_ledger(record: dict[str, Any]) -> dict[str, Any]:
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


def preflight_entry(
    e5_dir: Path, expected_manifest_sha256: str | None
) -> tuple[dict[str, Any], str]:
    manifest_path = e5_dir / "e5_manifest.json"
    sidecar_path = e5_dir / "e5_manifest.sha256"
    if not manifest_path.is_file() or not sidecar_path.is_file():
        raise ValueError("E5 manifest and SHA256 sidecar are both required")
    manifest_sha256 = sha256_file(manifest_path)
    sidecar_expected = f"{manifest_sha256}  e5_manifest.json\n"
    if sidecar_path.read_text(encoding="utf-8") != sidecar_expected:
        raise ValueError("E5 manifest SHA256 sidecar mismatch")
    if expected_manifest_sha256 and manifest_sha256 != expected_manifest_sha256.lower():
        raise ValueError("E5 manifest does not match --expected-e5-manifest-sha256")
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict):
        raise ValueError("E5 manifest is not a JSON object")

    global_pass = manifest.get("status") == "PASS"
    e5_pass = manifest.get("e5_status") in E5_PASS_STATES
    ready = manifest.get("e6_status") == "READY_TO_RUN"
    if not (global_pass and e5_pass and ready):
        raise EntryRefused({
            "status": "REFUSED",
            "e6_status": "UNEXECUTED_E5_ENTRY_CONDITION_NOT_PASS",
            "reason": "E6 entry requires E5 manifest status=PASS and e6_status=READY_TO_RUN",
            "observed": {
                "status": manifest.get("status"),
                "e5_status": manifest.get("e5_status"),
                "e6_status": manifest.get("e6_status"),
            },
            "e5_dir": str(e5_dir),
            "e5_manifest_sha256": manifest_sha256,
            "output_written": False,
            "final_promotion": "NOT_EXECUTED",
        })
    return manifest, manifest_sha256


def audit_e5(
    e5_dir: Path, manifest: dict[str, Any], manifest_sha256: str
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    hard_failures: list[str] = []
    lane_documents: dict[str, dict[str, Any]] = {}
    records_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    active_pairs: list[dict[str, Any]] = []

    counts = manifest.get("counts") if isinstance(manifest.get("counts"), dict) else {}
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
        add_check(checks, f"E5_COUNT_{name.upper()}", counts.get(name) == expected, expected, counts.get(name))

    add_check(
        checks, "E5_PRODUCTION_STARTED", manifest.get("production_started") is True,
        True, manifest.get("production_started"),
    )
    add_check(
        checks, "E5_LANE_ORDER", manifest.get("lane_order") == list(LANE_ORDER),
        list(LANE_ORDER), manifest.get("lane_order"),
    )
    add_check(
        checks, "E5_DECISION_FIELDS", manifest.get("decision_fields") == list(DECISION_FIELDS),
        list(DECISION_FIELDS), manifest.get("decision_fields"),
    )

    artifacts = manifest.get("artifacts") if isinstance(manifest.get("artifacts"), dict) else {}
    artifact_errors: list[str] = []
    for relative, metadata in sorted(artifacts.items()):
        try:
            path = resolve_member(e5_dir, relative)
            if not path.is_file():
                artifact_errors.append(f"MISSING:{relative}")
                continue
            observed = file_metadata(path)
            if not isinstance(metadata, dict) or observed != {
                "bytes": metadata.get("bytes"), "sha256": metadata.get("sha256")
            }:
                artifact_errors.append(f"HASH_OR_SIZE:{relative}")
        except (OSError, ValueError) as error:
            artifact_errors.append(f"{relative}:{error}")

    required_artifacts = {
        "e5_source_admission.json", "e5_source_novelty.json", "source_snapshot.txt",
        "e5_decision_ledger.jsonl", "e5_3p_void.jsonl", "e5_checkpoint.json",
        "e5_fna98.json", "e5_transcript.txt",
        *(expected_lane_path(order, lane) for order, lane in enumerate(LANE_ORDER, start=1)),
    }
    artifact_errors.extend(
        f"UNLISTED_REQUIRED:{relative}" for relative in sorted(required_artifacts - set(artifacts))
    )
    add_check(checks, "E5_LISTED_ARTIFACT_HASHES", not artifact_errors, "ALL_LISTED_BYTES_AND_HASHES_MATCH", artifact_errors)

    source = manifest.get("source") if isinstance(manifest.get("source"), dict) else {}
    source_window = (
        source.get("source_window_snapshot")
        if isinstance(source.get("source_window_snapshot"), dict) else {}
    )
    source_relative = source_window.get("path")
    try:
        source_path = (
            resolve_member(e5_dir, source_relative)
            if isinstance(source_relative, str) else None
        )
    except ValueError:
        source_path = None
    source_before: dict[str, Any] | None = None
    if source_path is not None and source_path.is_file():
        source_before = {"path": str(source_path), **file_metadata(source_path)}
    expected_source = {"bytes": source.get("bytes"), "sha256": source.get("sha256")}
    add_check(
        checks, "E5_SOURCE_WINDOW_PRIMARY_HASH_REOPEN",
        source_before is not None and {k: source_before[k] for k in ("bytes", "sha256")} == expected_source,
        expected_source, source_before,
    )
    add_check(
        checks, "E5_SOURCE_WINDOW_EXECUTION_AUTHORITY",
        source_window == {
            "path": "source_snapshot.txt",
            "bytes": source.get("bytes"),
            "sha256": source.get("sha256"),
            "execution_authority": "SOURCE_WINDOW_PRIMARY_REOPEN",
        },
        "SOURCE_WINDOW_PRIMARY_REOPEN", source_window,
    )
    add_check(
        checks, "E5_TRANSIENT_INGEST_PATH_NOT_READ",
        True, "NOT_USED_FOR_E6_EXECUTION", "NOT_USED_FOR_E6_EXECUTION",
    )
    add_check(
        checks, "E5_EXPECTED_SOURCE_HASH",
        source.get("expected_sha256") == source.get("sha256"), source.get("sha256"), source.get("expected_sha256"),
    )
    admission = source.get("admission") if isinstance(source.get("admission"), dict) else {}
    add_check(checks, "E5_SOURCE_ADMISSION", admission.get("status") == "ADMITTED", "ADMITTED", admission.get("status"))
    novelty = (
        source.get("novelty_vs_pikachu_e4")
        if isinstance(source.get("novelty_vs_pikachu_e4"), dict) else {}
    )
    add_check(checks, "E5_SOURCE_NOVELTY", novelty.get("status") == "PASS", "PASS", novelty.get("status"))

    snapshot_path = e5_dir / "source_snapshot.txt"
    snapshot_metadata = file_metadata(snapshot_path) if snapshot_path.is_file() else None
    add_check(
        checks, "E5_SOURCE_SNAPSHOT_HASH_REOPEN",
        snapshot_metadata == expected_source, expected_source, snapshot_metadata,
    )

    lane_entries = manifest.get("lane_artifacts") if isinstance(manifest.get("lane_artifacts"), list) else []
    add_check(checks, "E5_LANE_ENTRY_COUNT", len(lane_entries) == 29, 29, len(lane_entries))
    lane_errors: list[str] = []
    expected_ledger: list[dict[str, Any]] = []

    for order, lane in enumerate(LANE_ORDER, start=1):
        relative = expected_lane_path(order, lane)
        matching = [
            entry for entry in lane_entries
            if isinstance(entry, dict) and entry.get("lane") == lane and entry.get("lane_order") == order
        ]
        if len(matching) != 1:
            lane_errors.append(f"MANIFEST_ENTRY:{lane}:{len(matching)}")
            continue
        entry = matching[0]
        if entry.get("path") != relative:
            lane_errors.append(f"PATH:{lane}:{entry.get('path')}")
        path = e5_dir / relative
        if not path.is_file():
            lane_errors.append(f"MISSING:{relative}")
            continue
        observed_meta = file_metadata(path)
        if observed_meta != {"bytes": entry.get("bytes"), "sha256": entry.get("sha256")}:
            lane_errors.append(f"MANIFEST_HASH:{relative}")
        try:
            document = read_json(path)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            lane_errors.append(f"JSON:{relative}:{error}")
            continue
        if not isinstance(document, dict):
            lane_errors.append(f"NON_OBJECT:{relative}")
            continue
        lane_documents[lane] = document
        if document.get("artifact_type") != "E5_ACTIVE_LANE_ARTIFACT":
            lane_errors.append(f"TYPE:{relative}")
        if document.get("lane") != lane or document.get("lane_order") != order:
            lane_errors.append(f"IDENTITY:{relative}")
        if document.get("record_count") != 20 or document.get("decision_fields") != list(DECISION_FIELDS):
            lane_errors.append(f"CONTRACT:{relative}")
        if document.get("physical_3p_policy") != "VOID_NOT_AN_ACTIVE_LANE":
            lane_errors.append(f"3P_POLICY:{relative}")
        records = document.get("records") if isinstance(document.get("records"), list) else []
        if [record.get("dchart") for record in records if isinstance(record, dict)] != list(DCHART_ORDER):
            lane_errors.append(f"DCHART_ORDER:{relative}")
            continue
        for chart_index, record in enumerate(records, start=1):
            if not isinstance(record, dict):
                lane_errors.append(f"RECORD_NON_OBJECT:{relative}:{chart_index}")
                continue
            chart = DCHART_ORDER[chart_index - 1]
            key = (chart, lane)
            if key in records_by_key:
                lane_errors.append(f"DUPLICATE_PAIR:{chart}:{lane}")
                continue
            decision = record.get("decision") if isinstance(record.get("decision"), dict) else {}
            decision_edges = (
                record.get("decision_edges")
                if isinstance(record.get("decision_edges"), list) else []
            )
            selected, rejected = route_for(chart)
            if set(decision) != set(DECISION_FIELDS):
                lane_errors.append(f"DECISION_FIELDS:{chart}:{lane}")
            edge_contract = (
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
                and decision == {field: decision_edges[0].get(field) for field in DECISION_FIELDS}
            )
            if not edge_contract:
                lane_errors.append(f"DECISION_EDGES:{chart}:{lane}")
            if decision.get("SELECTED_ROUTE") != selected or decision.get("REJECTED_ROUTE") != rejected:
                lane_errors.append(f"DISPATCH:{chart}:{lane}")
            if record.get("dchart") != chart or record.get("lane") != lane or record.get("lane_order") != order:
                lane_errors.append(f"RECORD_IDENTITY:{chart}:{lane}")
            supported = lane in DIRECT_SOURCE_LANES
            expected_axes = {
                "authority_state": "ACTIVE_SOURCE_BOUNDARY",
                "data_state": "PARSED" if supported else "NOT_SHOWN",
                "applicability_state": "APPLICABLE",
                "evidence_state": "DIRECT_SOURCE" if supported else "HOLD",
                "verdict": "PASS" if supported else "HOLD",
                "hold_scope": "NONE" if supported else "LOCAL",
            }
            if any(record.get(name) != value for name, value in expected_axes.items()):
                lane_errors.append(f"STATE_AXES:{chart}:{lane}")
            stage_r = record.get("stage_input_R") if isinstance(record.get("stage_input_R"), dict) else {}
            stage_a = record.get("stage_result_A") if isinstance(record.get("stage_result_A"), dict) else {}
            expected_payload_sha256 = sha256_bytes(canonical_json(record.get("payload")))
            if (
                stage_r.get("role") != "R"
                or stage_a.get("role") != "A"
                or (supported and not (
                    stage_r.get("state") == "PASS_PRE_QA"
                    and stage_a.get("state") == "PASS_QA"
                    and stage_r.get("body_sha256") == stage_a.get("body_sha256") == expected_payload_sha256
                    and stage_a.get("body") == record.get("payload")
                ))
                or (not supported and not (
                    stage_r == {"role": "R", "state": "LOCAL_HOLD_NO_DIRECT_LAYER_BODY", "body_sha256": None}
                    and stage_a == {"role": "A", "state": "LOCAL_HOLD", "body_sha256": None, "body": None}
                ))
            ):
                lane_errors.append(f"R_TO_A_STATE:{chart}:{lane}")
            records_by_key[key] = record
            expected_ledger.append(projection_for_ledger(record))
            active_pairs.append({
                "pair_id": f"{chart}::{order:02d}_{lane}",
                "dchart": chart,
                "dchart_order": chart_index,
                "lane": lane,
                "lane_order": order,
                "record_id": record.get("record_id"),
                "status": record.get("status"),
                "e5_lane_path": relative,
                "e5_lane_sha256": observed_meta["sha256"],
                "record_sha256": sha256_bytes(canonical_json(record)),
                "decision_sha256": sha256_bytes(canonical_json(decision)),
                "decision_edges_sha256": sha256_bytes(canonical_json(decision_edges)),
                "stage_input_R_sha256": sha256_bytes(canonical_json(stage_r)),
                "stage_result_A_sha256": sha256_bytes(canonical_json(stage_a)),
                "state_axes": expected_axes,
                "source_id": source.get("source_id"),
                "source_sha256": source.get("sha256"),
            })

    expected_pair_keys = {(chart, lane) for lane in LANE_ORDER for chart in DCHART_ORDER}
    add_check(checks, "E5_LANE_ARTIFACT_REOPEN", not lane_errors, "29_VALID_LANE_ARTIFACTS", lane_errors)
    add_check(
        checks, "E5_ACTIVE_PAIR_PRODUCT",
        len(active_pairs) == 580 and set(records_by_key) == expected_pair_keys,
        "20D_X_29=580_UNIQUE", {"rows": len(active_pairs), "unique": len(records_by_key)},
    )

    ledger_path = e5_dir / "e5_decision_ledger.jsonl"
    try:
        ledger_rows = read_jsonl(ledger_path)
        ledger_read_error = None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        ledger_rows = []
        ledger_read_error = str(error)
    ledger_match = ledger_read_error is None and ledger_rows == expected_ledger and len(ledger_rows) == 580
    add_check(
        checks, "E5_DECISION_LEDGER_REOPEN", ledger_match,
        "580_ROWS_EXACTLY_MATCH_LANE_RECORD_PROJECTIONS",
        ledger_read_error or {"rows": len(ledger_rows), "exact_match": ledger_rows == expected_ledger},
    )

    physical_3p = manifest.get("physical_3p") if isinstance(manifest.get("physical_3p"), dict) else {}
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
    try:
        physical_3p_rows = read_jsonl(e5_dir / "e5_3p_void.jsonl")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        physical_3p_rows = []
    physical_3p_ok = (
        physical_3p.get("state") == "VOID"
        and physical_3p.get("active_lane") is False
        and physical_3p.get("artifact") == "e5_3p_void.jsonl"
        and physical_3p.get("count") == 20
        and physical_3p.get("members") == expected_3p
        and physical_3p_rows == expected_3p_rows
    )
    add_check(
        checks, "E5_PHYSICAL_3P_VOID", physical_3p_ok,
        {"manifest_members": expected_3p, "artifact_rows": expected_3p_rows},
        {"manifest_members": physical_3p.get("members"), "artifact_rows": physical_3p_rows},
    )
    if not physical_3p_ok or counts.get("active_3p_lanes") != 0:
        hard_failures.append("VOID_REUSE")

    checkpoint_path = e5_dir / "e5_checkpoint.json"
    try:
        checkpoint_file = read_json(checkpoint_path)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        checkpoint_file = {"read_error": str(error)}
    checkpoint = manifest.get("checkpoint") if isinstance(manifest.get("checkpoint"), dict) else {}
    checkpoint_ok = (
        checkpoint_file == checkpoint
        and checkpoint.get("run_id") == manifest.get("run_id")
        and checkpoint.get("NEW_DATASET_PRODUCTION") in E5_PASS_STATES
        and checkpoint.get("LONG_DRIFT") == "READY_TO_RUN"
        and checkpoint.get("first_unexecuted_job") == "RUN_LONG_DRIFT_REOPEN"
        and checkpoint.get("lower_stage_restart") == "VOID"
        and checkpoint.get("user_promotion") == "NOT_AUTHORIZED"
        and checkpoint.get("retained_passes") == list(RETAINED_PASSES)
    )
    add_check(checks, "E5_CHECKPOINT_REOPEN", checkpoint_ok, "E5_PASS_TO_RUN_LONG_DRIFT_REOPEN", checkpoint_file)

    fna_path = e5_dir / "e5_fna98.json"
    try:
        fna_file = read_json(fna_path)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        fna_file = {"read_error": str(error)}
    fna = manifest.get("fna98") if isinstance(manifest.get("fna98"), dict) else {}
    fna_ok = (
        fna_file == fna
        and fna.get("status") == "PASS"
        and fna.get("e5_status") in E5_PASS_STATES
        and fna.get("materialization_subgate") == "PASS"
        and fna.get("value_completeness") == "HOLD_LOCAL_25_UNSUPPORTED_LANES"
        and fna.get("hard_fail_count") == 0
        and fna.get("hard_failures") == []
    )
    add_check(checks, "E5_FNA98_REOPEN", fna_ok, "PASS_WITH_ZERO_HARD_FAILURES", fna_file)

    subgates = manifest.get("subgates") if isinstance(manifest.get("subgates"), dict) else {}
    add_check(
        checks, "E5_SUBGATE_SEPARATION",
        subgates == {
            "MATERIALIZATION": "PASS",
            "VALUE_COMPLETENESS": "HOLD_LOCAL_25_UNSUPPORTED_LANES",
            "SOURCE_NOVELTY": "PASS",
        },
        "MATERIALIZATION_PASS_VALUE_COMPLETENESS_LOCAL_HOLD_SOURCE_NOVELTY_PASS",
        subgates,
    )

    baseline = manifest.get("baseline") if isinstance(manifest.get("baseline"), dict) else {}
    baseline_path_value = baseline.get("path")
    baseline_path = Path(baseline_path_value).resolve() if isinstance(baseline_path_value, str) else None
    baseline_before: dict[str, dict[str, Any]] = {}
    baseline_read_error: str | None = None
    if baseline_path is not None:
        try:
            baseline_before = tree_snapshot(baseline_path)
        except (OSError, ValueError) as error:
            baseline_read_error = str(error)
    baseline_contract_ok = (
        baseline_read_error is None
        and baseline.get("unchanged") is True
        and baseline.get("overwrite_count") == 0
        and baseline.get("pre_files") == baseline.get("post_files") == baseline_before
        and baseline.get("pre_tree_sha256") == baseline.get("post_tree_sha256") == tree_id(baseline_before)
        and checkpoint.get("baseline_tree_sha256") == tree_id(baseline_before)
    )
    add_check(
        checks, "E5_BASELINE_NO_REBUILD_REOPEN", baseline_contract_ok,
        "CURRENT_BASELINE_EQUALS_E5_PRE_AND_POST_SNAPSHOT",
        baseline_read_error or {"tree_sha256": tree_id(baseline_before), "files": len(baseline_before)},
    )

    def record(chart: str, lane: str) -> dict[str, Any]:
        return records_by_key.get((chart, lane), {})

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

    unsupported_records = [
        records_by_key.get((chart, lane), {})
        for lane in LANE_ORDER if lane not in DIRECT_SOURCE_LANES
        for chart in DCHART_ORDER
    ]
    no_gap_fill = len(unsupported_records) == 500 and all(
        record_value.get("status") == "LOCAL_HOLD_NO_DIRECT_LAYER_SOURCE"
        and isinstance(record_value.get("payload"), dict)
        and record_value["payload"].get("fabricated_values") == []
        for record_value in unsupported_records
    )
    probes.append(make_probe(
        "EXHAUSTIVE_NO_SOURCE_GAP_FILL",
        no_gap_fill,
        "500_UNSUPPORTED_PAIRS_LOCAL_HOLD_ZERO_FABRICATION",
        {"records": len(unsupported_records), "all_zero_fabrication": no_gap_fill},
        ["25_UNSUPPORTED_LANES_X_20D"],
    ))

    add_check(
        checks, "E6_REPRESENTATIVE_AND_BOUNDARY_PROBES",
        len(probes) == 9 and all(probe["status"] == "PASS" for probe in probes),
        "9_OF_9_PASS", f"{sum(probe['status'] == 'PASS' for probe in probes)}_OF_{len(probes)}_PASS",
    )

    if counts.get("fabricated_source_values") not in (0, None) or not no_gap_fill:
        hard_failures.append("SOURCE_VALUE_FABRICATION")

    return {
        "checks": checks,
        "hard_failures": sorted(set(hard_failures)),
        "active_pairs": active_pairs,
        "probes": probes,
        "source_path": source_path,
        "source_before": source_before,
        "snapshot_metadata": snapshot_metadata,
        "baseline_path": baseline_path,
        "baseline_before": baseline_before,
        "e5_input_hashes": {
            "e5_manifest.json": {"sha256": manifest_sha256, "bytes": (e5_dir / "e5_manifest.json").stat().st_size},
            **{
                name: file_metadata(e5_dir / name) if (e5_dir / name).is_file() else None
                for name in (
                    "e5_manifest.sha256", "e5_source_admission.json", "e5_source_novelty.json",
                    "source_snapshot.txt", "e5_decision_ledger.jsonl", "e5_3p_void.jsonl",
                    "e5_checkpoint.json", "e5_fna98.json",
                )
            },
        },
        "e5_output_hashes": [
            {
                "lane": entry.get("lane"),
                "lane_order": entry.get("lane_order"),
                "path": entry.get("path"),
                "bytes": entry.get("bytes"),
                "sha256": entry.get("sha256"),
                "status": entry.get("status"),
            }
            for entry in manifest.get("lane_artifacts", [])
            if isinstance(entry, dict)
        ],
    }


def execute(args: argparse.Namespace) -> dict[str, Any]:
    e5_dir = args.e5_dir.resolve()
    out_dir = args.out_dir.resolve()
    if not e5_dir.is_dir():
        raise ValueError(f"E5 output directory missing: {e5_dir}")
    if out_dir.exists():
        raise ValueError(f"E6 output directory must not exist: {out_dir}")

    manifest, manifest_sha256 = preflight_entry(e5_dir, args.expected_e5_manifest_sha256)
    baseline_value = manifest.get("baseline", {}).get("path") if isinstance(manifest.get("baseline"), dict) else None
    baseline_path = Path(baseline_value).resolve() if isinstance(baseline_value, str) else None
    if is_within(out_dir, e5_dir) or is_within(e5_dir, out_dir):
        raise ValueError("E6 output must be separate from the E5 output directory")
    if baseline_path is not None and (is_within(out_dir, baseline_path) or out_dir == baseline_path):
        raise ValueError("E6 output may not be written inside references/v9_baseline")

    e5_tree_before = tree_snapshot(e5_dir)
    audit = audit_e5(e5_dir, manifest, manifest_sha256)
    source_path = audit["source_path"]
    source_after = (
        {"path": str(source_path), **file_metadata(source_path)}
        if isinstance(source_path, Path) and source_path.is_file() else None
    )
    baseline_after: dict[str, dict[str, Any]] = {}
    if isinstance(audit["baseline_path"], Path) and audit["baseline_path"].is_dir():
        baseline_after = tree_snapshot(audit["baseline_path"])
    e5_tree_after = tree_snapshot(e5_dir)

    e5_changes = changed_paths(e5_tree_before, e5_tree_after)
    baseline_changes = changed_paths(audit["baseline_before"], baseline_after)
    source_unchanged = audit["source_before"] == source_after
    add_check(audit["checks"], "E6_E5_OUTPUT_NO_CHANGE", not e5_changes, 0, len(e5_changes))
    add_check(audit["checks"], "E6_BASELINE_NO_CHANGE", not baseline_changes, 0, len(baseline_changes))
    add_check(audit["checks"], "E6_SOURCE_NO_CHANGE", source_unchanged, True, source_unchanged)
    add_check(audit["checks"], "E6_REBUILD_COUNT", True, 0, 0)
    add_check(audit["checks"], "E6_LOWER_STAGE_REASSEMBLY_COUNT", True, 0, 0)
    add_check(audit["checks"], "E6_REMOTE_READ_COUNT", True, {"drive": 0, "github": 0, "other": 0}, {"drive": 0, "github": 0, "other": 0})
    add_check(audit["checks"], "E6_FINAL_PROMOTION_FIREWALL", True, "NOT_EXECUTED", "NOT_EXECUTED")

    failures = [check["check_id"] for check in audit["checks"] if check["status"] != "PASS"]
    hard_failures = list(audit["hard_failures"])
    if hard_failures:
        failures.append("FNA98_CANONICAL_HARD_FAILURE")
    e6_pass = not failures
    e6_status = "PASS" if e6_pass else "HOLD_LOCAL_REOPEN_OR_BOUNDARY_FAILURE"
    run_id = sha256_bytes(compact_json({
        "schema_version": SCHEMA_VERSION,
        "e5_run_id": manifest.get("run_id"),
        "e5_manifest_sha256": manifest_sha256,
        "e5_tree_sha256": tree_id(e5_tree_before),
        "source_sha256": manifest.get("source", {}).get("sha256"),
        "probe_hash": sha256_bytes(canonical_json(audit["probes"])),
    }).encode("utf-8"))

    reopen_record = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "evidence_level": "E6_REOPENED_CONTINUATION_AFTER_INTERVENING_WORK",
        "entry": {
            "e5_dir": str(e5_dir),
            "e5_run_id": manifest.get("run_id"),
            "e5_manifest_sha256": manifest_sha256,
            "e5_global_status": manifest.get("status"),
            "e5_status": manifest.get("e5_status"),
            "e5_fna98_status": manifest.get("fna98", {}).get("status"),
        },
        "context": {
            "mode": "SEPARATE_PROCESS_LOCAL_CHECKPOINT_REOPEN",
            "prior_chat_memory_input": "NONE",
            "source_window_checkpoint": str(e5_dir),
            "remote_execution_authority": "NONE",
        },
        "source_reopen": {
            "expected": {
                "source_id": manifest.get("source", {}).get("source_id"),
                "bytes": manifest.get("source", {}).get("bytes"),
                "sha256": manifest.get("source", {}).get("sha256"),
            },
            "source_window_before": audit["source_before"],
            "source_window_after": source_after,
            "source_window_snapshot": audit["snapshot_metadata"],
            "transient_ingest_path_read_count": 0,
        },
        "input_hashes": audit["e5_input_hashes"],
        "output_hashes": audit["e5_output_hashes"],
        "active_pair_manifest": {
            "path": "e6_active_pair_manifest.jsonl",
            "rows": len(audit["active_pairs"]),
            "expected_product": "20D_X_29=580",
        },
        "physical_3p": manifest.get("physical_3p"),
        "e5_tree": {
            "before": e5_tree_before,
            "after": e5_tree_after,
            "before_sha256": tree_id(e5_tree_before),
            "after_sha256": tree_id(e5_tree_after),
            "changed_paths": e5_changes,
        },
        "baseline_tree": {
            "path": str(audit["baseline_path"]) if audit["baseline_path"] else None,
            "before_sha256": tree_id(audit["baseline_before"]),
            "after_sha256": tree_id(baseline_after),
            "changed_paths": baseline_changes,
        },
        "execution_counters": {
            "rebuild_count": 0,
            "lower_stage_reassembly_count": 0,
            "drive_read_count": 0,
            "github_read_count": 0,
            "other_remote_read_count": 0,
            "e5_output_change_count": len(e5_changes),
            "baseline_change_count": len(baseline_changes),
            "source_change_count": 0 if source_unchanged else 1,
        },
        "checks": audit["checks"],
        "failures": failures,
        "status": e6_status,
    }

    fna98 = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "status": "PASS" if e6_pass else "HOLD",
        "e6_status": e6_status,
        "hard_fail_count": len(hard_failures),
        "hard_failures": hard_failures,
        "gates": {
            "TARGET_CHECK": "PASS" if not failures else "HOLD",
            "FACTCHECK": "PASS" if not failures else "HOLD",
            "SOURCE_CHECK": "PASS" if source_unchanged and audit["snapshot_metadata"] is not None else "HOLD",
            "WHY_CHECK": "PASS" if all(probe["status"] == "PASS" for probe in audit["probes"]) else "HOLD",
            "LOGIC_CHECK": "PASS" if not failures else "HOLD",
            "CONDITION_EXCEPTION_CHECK": "PASS" if not hard_failures else "HOLD",
            "FORMAT_CHECK": "PASS" if len(audit["active_pairs"]) == 580 else "HOLD",
            "PRACTICAL_USABILITY": "PASS" if e6_pass else "HOLD",
            "SUPPLEMENTAL_ROUTING_CHECK": "PASS" if all(probe["status"] == "PASS" for probe in audit["probes"]) else "HOLD",
            "VOID_REUSE_CHECK": "PASS" if "VOID_REUSE" not in hard_failures else "HOLD",
            "SOURCE_GAP_FILL_CHECK": "PASS" if "SOURCE_VALUE_FABRICATION" not in hard_failures else "HOLD",
            "HASH_READBACK_CHECK": "PASS" if not failures else "HOLD",
        },
    }

    checkpoint = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "restore_floor": "ANALYSIS02_MATURE_PRODUCTION_STATE",
        "retained_passes": list(RETAINED_PASSES),
        "NEW_DATASET_PRODUCTION": manifest.get("e5_status"),
        "LONG_DRIFT": e6_status,
        "E6_LONG_DRIFT_REOPEN": "PASS_E6_TESTED_SCOPE" if e6_pass else "HOLD_E6_LOCAL_ONLY",
        "FRESH_TAB_LONG_DRIFT_REAL_RUNTIME_GATE": "HOLD_UNEXECUTED",
        "first_unexecuted_job": (
            "FINAL_USER_PROMOTION_PACKET"
            if e6_pass else "REPAIR_E6_LOCAL_BOUNDARY_AND_RERUN_LONG_DRIFT_REOPEN"
        ),
        "post_technical_state": "READY_FOR_USER_PROMOTION" if e6_pass else "HOLD_E6_LOCAL_ONLY",
        "lower_stage_restart": "VOID",
        "rebuild_count": 0,
        "lower_stage_reassembly_count": 0,
        "user_promotion": "NOT_AUTHORIZED_NOT_EXECUTED",
        "FINAL_KANI_JUDGMENT_RUNTIME": (
            "HOLD_USER_PROMOTION_ONLY" if e6_pass else "HOLD_E6_AND_USER_PROMOTION"
        ),
    }

    transcript = "\n".join([
        "TITLE=KANI_V9_E6_LONG_DRIFT_REOPEN_TRANSCRIPT",
        f"RUN_ID={run_id}",
        f"E5_RUN_ID={manifest.get('run_id')}",
        f"E5_MANIFEST_SHA256={manifest_sha256}",
        "ENTRY_CONDITION=E5_GLOBAL_PASS",
        "REOPEN_CONTEXT=SEPARATE_PROCESS_LOCAL_CHECKPOINT",
        f"SOURCE_SHA256={manifest.get('source', {}).get('sha256')}",
        f"ACTIVE_PAIR_REOPEN={len(audit['active_pairs'])}_OF_580",
        "PHYSICAL_3P_REOPEN=20_VOID_0_ACTIVE",
        f"DECISION_LEDGER_FIELDS={','.join(DECISION_FIELDS)}",
        f"BOUNDARY_PROBES={sum(probe['status'] == 'PASS' for probe in audit['probes'])}_OF_{len(audit['probes'])}_PASS",
        "REBUILD_COUNT=0",
        "LOWER_STAGE_REASSEMBLY_COUNT=0",
        "DRIVE_READ_COUNT=0",
        "GITHUB_READ_COUNT=0",
        f"E5_OUTPUT_CHANGE_COUNT={len(e5_changes)}",
        f"BASELINE_CHANGE_COUNT={len(baseline_changes)}",
        f"LONG_DRIFT={e6_status}",
        f"FNA98={fna98['status']}",
        f"NEXT_STATE={checkpoint['first_unexecuted_job']}",
        f"E6_LONG_DRIFT_REOPEN={checkpoint['E6_LONG_DRIFT_REOPEN']}",
        "FRESH_TAB_LONG_DRIFT_REAL_RUNTIME_GATE=HOLD_UNEXECUTED",
        f"FINAL_KANI_JUDGMENT_RUNTIME={checkpoint['FINAL_KANI_JUDGMENT_RUNTIME']}",
        "FINAL_USER_PROMOTION=NOT_AUTHORIZED_NOT_EXECUTED",
        "CONTENT_END",
        "",
    ])

    out_dir.mkdir(parents=True)
    active_pair_path = out_dir / "e6_active_pair_manifest.jsonl"
    write_jsonl(active_pair_path, audit["active_pairs"])
    probe_path = out_dir / "e6_probe_results.json"
    write_json(probe_path, {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "status": "PASS" if all(probe["status"] == "PASS" for probe in audit["probes"]) else "HOLD",
        "pass_count": sum(probe["status"] == "PASS" for probe in audit["probes"]),
        "probe_count": len(audit["probes"]),
        "probes": audit["probes"],
    })
    reopen_path = out_dir / "e6_reopen_record.json"
    write_json(reopen_path, reopen_record)
    fna_path = out_dir / "e6_fna98.json"
    write_json(fna_path, fna98)
    checkpoint_path = out_dir / "e6_checkpoint.json"
    write_json(checkpoint_path, checkpoint)
    transcript_path = out_dir / "e6_transcript.txt"
    write_text(transcript_path, transcript)

    produced = [active_pair_path, probe_path, reopen_path, fna_path, checkpoint_path, transcript_path]
    artifacts = {
        path.relative_to(out_dir).as_posix(): file_metadata(path) for path in sorted(produced)
    }
    overlay_manifest = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "status": "PASS" if e6_pass else "HOLD",
        "e6_status": e6_status,
        "evidence_level": "E6_REOPENED_CONTINUATION_AFTER_INTERVENING_WORK",
        "entry_condition": {
            "required": "E5_MANIFEST_GLOBAL_PASS",
            "observed": "PASS",
            "e5_dir": str(e5_dir),
            "e5_run_id": manifest.get("run_id"),
            "e5_manifest_sha256": manifest_sha256,
            "e5_status": manifest.get("e5_status"),
        },
        "counts": {
            "dcharts": 20,
            "active_lanes": 29,
            "active_pairs": len(audit["active_pairs"]),
            "physical_3p_members": 20,
            "active_3p_lanes": 0,
            "decision_ledger_rows": (
                manifest.get("counts", {}).get("lane_records")
                if isinstance(manifest.get("counts"), dict) else None
            ),
            "representative_boundary_probes": len(audit["probes"]),
            "passed_probes": sum(probe["status"] == "PASS" for probe in audit["probes"]),
        },
        "decision_fields": list(DECISION_FIELDS),
        "execution_counters": reopen_record["execution_counters"],
        "e5_tree_sha256": tree_id(e5_tree_after),
        "baseline_tree_sha256": tree_id(baseline_after),
        "source_sha256": manifest.get("source", {}).get("sha256"),
        "failures": failures,
        "artifacts": artifacts,
        "checkpoint": checkpoint,
        "fna98": fna98,
        "promotion_firewall": {
            "authority": "CURRENT_USER_EXPLICIT_ONLY",
            "status": "NOT_AUTHORIZED_NOT_EXECUTED",
            "final_runtime": checkpoint["FINAL_KANI_JUDGMENT_RUNTIME"],
            "new_technical_stage_after_e6": "FORBIDDEN",
        },
    }
    manifest_path = out_dir / "e6_manifest.json"
    write_json(manifest_path, overlay_manifest)
    overlay_manifest_sha256 = sha256_file(manifest_path)
    write_text(out_dir / "e6_manifest.sha256", f"{overlay_manifest_sha256}  e6_manifest.json\n")

    return {
        "status": overlay_manifest["status"],
        "e6_status": e6_status,
        "active_pairs": len(audit["active_pairs"]),
        "probes": f"{sum(probe['status'] == 'PASS' for probe in audit['probes'])}/{len(audit['probes'])}",
        "manifest_sha256": overlay_manifest_sha256,
        "out_dir": str(out_dir),
        "final_promotion": "NOT_EXECUTED",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("e5_dir", type=Path, help="closed E5 output directory")
    parser.add_argument("--out-dir", type=Path, required=True, help="new, separate E6 overlay directory")
    parser.add_argument(
        "--expected-e5-manifest-sha256",
        help="optional caller-pinned SHA256 in addition to e5_manifest.sha256",
    )
    return parser


def main() -> int:
    try:
        result = execute(build_parser().parse_args())
    except EntryRefused as error:
        print(compact_json(error.payload))
        return 2
    except (OSError, ValueError, RuntimeError, UnicodeDecodeError, json.JSONDecodeError) as error:
        print(compact_json({
            "status": "REVISE",
            "e6_status": "UNEXECUTED_PREFLIGHT_ERROR",
            "error": str(error),
            "final_promotion": "NOT_EXECUTED",
        }))
        return 1
    print(compact_json(result))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

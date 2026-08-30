#!/usr/bin/env python3
"""Independently validate a KANI V9 E5 overlay.

Exit codes: 0=PASS, 2=truthful HOLD, 1=REVISE (integrity/contract error).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from run_kani_v9_e5 import (
    DECISION_FIELDS,
    DCHART_ORDER,
    DIRECT_SOURCE_LANES,
    LANE_ORDER,
    SCHEMA_VERSION,
    SOURCE_DCHART_ORDER,
    artifact_metadata,
    audit_source_novelty,
    build_lane_artifact,
    canonical_json,
    compact_json,
    evaluate_source_admission,
    lane_filename,
    parse_source_pairs,
    sha256_bytes,
    sha256_file,
    tree_id,
    tree_snapshot,
    verify_baseline_contract,
)


DEFAULT_BASELINE = Path(__file__).resolve().parent.parent / "references" / "v9_baseline"


def add_error(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def read_json(path: Path, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        errors.append(f"cannot read {path.name}: {error}")
        return None


def read_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as stream:
            for number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError("row is not an object")
                rows.append(value)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        errors.append(f"cannot read {path.name}: {error}")
    return rows


def compare(label: str, actual: Any, expected: Any, errors: list[str]) -> None:
    if actual != expected:
        errors.append(f"{label} mismatch")


def expected_parse_summary(pairs: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
    return {
        "status": "PASS",
        "dcharts": list(DCHART_ORDER),
        "source_section_order": list(SOURCE_DCHART_ORDER),
        "runtime_record_order": list(DCHART_ORDER),
        "rashi_blocks": 20,
        "bhava_blocks": 20,
        "mudda_dasha_pairs": 20,
        "pair_count": 20,
        "block_hashes": {
            chart: {
                "RASHI": pairs[chart]["RASHI"]["sha256"],
                "BHAVA": pairs[chart]["BHAVA"]["sha256"],
                "DASHA": pairs[chart]["DASHA"]["sha256"],
            }
            for chart in DCHART_ORDER
        },
    }


def validate_decision(decision: Any, label: str, errors: list[str]) -> None:
    if not isinstance(decision, dict):
        errors.append(f"{label} decision is not an object")
        return
    missing = [field for field in DECISION_FIELDS if not decision.get(field)]
    if missing:
        errors.append(f"{label} missing decision fields: {','.join(missing)}")


def validate_decision_edges(edges: Any, label: str, errors: list[str]) -> None:
    expected_ids = [
        "E4-ROUTE-FAMILY", "E5-VIEW-SEPARATION", "E4-FIELD-SEPARATION",
        "DIRECT-TAB03-SOURCE-HOLD", "DIRECT-TAB03-R-TO-A", "DIRECT-TAB03-TIMING-GATE",
    ]
    if not isinstance(edges, list) or [row.get("EDGE_ID") for row in edges if isinstance(row, dict)] != expected_ids:
        errors.append(f"{label} decision edge roster/order mismatch")
        return
    for edge in edges:
        validate_decision(edge, f"{label}/{edge.get('EDGE_ID')}", errors)


def verify_artifact_hashes(root: Path, manifest: dict[str, Any], errors: list[str]) -> None:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        errors.append("manifest artifacts is not an object")
        return
    for relative, metadata in artifacts.items():
        path = root / relative
        if not path.is_file() or path.is_symlink():
            errors.append(f"artifact missing or symlinked: {relative}")
            continue
        if not isinstance(metadata, dict):
            errors.append(f"artifact metadata invalid: {relative}")
            continue
        if path.stat().st_size != metadata.get("bytes"):
            errors.append(f"artifact byte count mismatch: {relative}")
        if sha256_file(path) != metadata.get("sha256"):
            errors.append(f"artifact hash mismatch: {relative}")
    expected_files = set(artifacts) | {"e5_manifest.json", "e5_manifest.sha256"}
    actual_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }
    if actual_files != expected_files:
        missing = sorted(expected_files - actual_files)
        extra = sorted(actual_files - expected_files)
        errors.append(f"overlay file inventory mismatch: missing={missing}, extra={extra}")


def verify_manifest_sidecar(root: Path, errors: list[str]) -> None:
    manifest_path = root / "e5_manifest.json"
    sidecar = root / "e5_manifest.sha256"
    if not manifest_path.is_file() or not sidecar.is_file():
        errors.append("manifest or manifest sidecar is missing")
        return
    expected = f"{sha256_file(manifest_path)}  e5_manifest.json\n"
    try:
        actual = sidecar.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        errors.append(f"manifest sidecar read failed: {error}")
        return
    if actual != expected:
        errors.append("manifest sidecar hash mismatch")


def validate_provenance(source_bytes: bytes, provenance: Any, errors: list[str]) -> None:
    if not isinstance(provenance, dict):
        errors.append("source provenance is missing")
        return
    parent_path = provenance.get("parent_source_path")
    parent_hash = provenance.get("parent_source_sha256")
    identical = provenance.get("parent_copy_byte_identical")
    if parent_path is None:
        return
    path = Path(parent_path)
    if not path.is_file():
        if not (
            provenance.get("parent_copy_byte_identical") is True
            and provenance.get("parent_source_sha256") == sha256_bytes(source_bytes)
            and provenance.get("carrier_source_sha256") == sha256_bytes(source_bytes)
        ):
            errors.append("unavailable provenance parent is not hash-bound to the reopened snapshot")
        return
    if sha256_file(path) != parent_hash:
        errors.append("provenance parent hash mismatch")
    if (path.read_bytes() == source_bytes) is not True or identical is not True:
        errors.append("provenance byte-identical copy claim mismatch")


def validate_rejected(
    root: Path,
    manifest: dict[str, Any],
    ledger: list[dict[str, Any]],
    errors: list[str],
) -> tuple[str, int, int]:
    admission_status = manifest.get("source", {}).get("admission", {}).get("status")
    novelty_status = manifest.get("source", {}).get("novelty_vs_pikachu_e4", {}).get("status")
    expected_e5 = (
        "HOLD_SOURCE_ADMISSION_REJECTED"
        if admission_status == "REJECTED" else "HOLD_SOURCE_NOVELTY_CONFLICT"
    )
    expected_parse = (
        "NOT_EXECUTED_SOURCE_ADMISSION_REJECTED"
        if admission_status == "REJECTED" else "NOT_EXECUTED_SOURCE_NOVELTY_CONFLICT"
    )
    add_error(errors, manifest.get("production_started") is False, "rejected source started production")
    add_error(
        errors,
        manifest.get("e5_status") == expected_e5,
        "pre-production HOLD E5 status mismatch",
    )
    add_error(
        errors,
        manifest.get("e6_status") == "UNEXECUTED_E5_ENTRY_CONDITION_NOT_PASS",
        "E6 was not left unexecuted after admission rejection",
    )
    parse_state = manifest.get("source_parse", {})
    add_error(
        errors,
        parse_state == {
            "status": expected_parse,
            "rashi_blocks": 0,
            "bhava_blocks": 0,
        },
        "rejected source parse state mismatch",
    )
    lane_files = list((root / "lanes").glob("*.json")) if (root / "lanes").exists() else []
    add_error(errors, len(lane_files) == 0, "rejected source produced lane artifacts")
    add_error(errors, len(manifest.get("lane_artifacts", [])) == 0, "rejected manifest lists lanes")
    add_error(errors, len(ledger) == 1, "rejected ledger must contain one admission row")
    if ledger:
        validate_decision(ledger[0].get("decision"), "rejected ledger row", errors)
        add_error(
            errors,
            ledger[0].get("decision", {}).get("OUTPUT_EFFECT") == "PRODUCTION_NOT_STARTED",
            "rejected admission output effect mismatch",
        )
    return "HOLD", 0, 0


def validate_admitted(
    root: Path,
    manifest: dict[str, Any],
    source_bytes: bytes,
    source_text: str,
    ledger: list[dict[str, Any]],
    errors: list[str],
) -> tuple[str, int, int]:
    try:
        pairs = parse_source_pairs(source_text)
    except ValueError as error:
        errors.append(f"source 20/20 pair parse failed: {error}")
        return "REVISE", 0, 0
    compare("source parse summary", manifest.get("source_parse"), expected_parse_summary(pairs), errors)
    snapshot_path = root / "source_snapshot.txt"
    add_error(errors, snapshot_path.is_file(), "source snapshot is missing")
    if snapshot_path.is_file() and snapshot_path.read_bytes() != source_bytes:
        errors.append("source snapshot bytes differ from admitted source")

    lanes_dir = root / "lanes"
    expected_names = {
        lane_filename(order, lane)
        for order, lane in enumerate(LANE_ORDER, start=1)
    }
    actual_names = {
        path.name for path in lanes_dir.glob("*.json")
    } if lanes_dir.is_dir() else set()
    if actual_names != expected_names:
        errors.append(
            f"29-lane filename set mismatch: missing={sorted(expected_names - actual_names)}, "
            f"extra={sorted(actual_names - expected_names)}"
        )

    source = manifest.get("source", {})
    run_id = manifest.get("run_id")
    source_id = source.get("source_id")
    source_sha256 = source.get("sha256")
    expected_ledger: list[dict[str, Any]] = []
    seen_records: set[str] = set()
    local_holds = 0
    lane_entries: list[dict[str, Any]] = []
    for order, lane in enumerate(LANE_ORDER, start=1):
        path = lanes_dir / lane_filename(order, lane)
        if not path.is_file():
            continue
        actual = read_json(path, errors)
        if not isinstance(actual, dict):
            continue
        expected = build_lane_artifact(run_id, source_id, source_sha256, pairs, order, lane)
        compare(f"lane artifact {lane}", actual, expected, errors)
        if actual.get("status") == "LOCAL_HOLD_NO_DIRECT_LAYER_SOURCE":
            local_holds += 1
        records = actual.get("records", [])
        add_error(errors, len(records) == 20, f"{lane} record count is not 20")
        for record in records:
            record_id = record.get("record_id")
            if record_id in seen_records:
                errors.append(f"duplicate active-pair record: {record_id}")
            seen_records.add(record_id)
            validate_decision(record.get("decision"), str(record_id), errors)
            validate_decision_edges(record.get("decision_edges"), str(record_id), errors)
            boundary = record.get("field_boundary", {})
            add_error(
                errors,
                boundary.get("OCCUPANT_FIELD") != boundary.get("HOUSE_LORD_FIELD")
                and boundary.get("operator") == "NOT_EQUAL",
                f"{record_id} occupant/lord boundary collapsed",
            )
            if record.get("lane") not in DIRECT_SOURCE_LANES:
                payload = record.get("payload", {})
                add_error(
                    errors,
                    payload.get("fabricated_values") == []
                    and payload.get("preserved_state") == "LOCAL_HOLD",
                    f"{record_id} unsupported value was not a zero-fill local HOLD",
                )
                add_error(
                    errors,
                    record.get("data_state") == "NOT_SHOWN"
                    and record.get("applicability_state") == "APPLICABLE"
                    and record.get("evidence_state") == "HOLD"
                    and record.get("verdict") == "HOLD"
                    and record.get("hold_scope") == "LOCAL"
                    and record.get("source_declaration") == "NOT_INCLUDED",
                    f"{record_id} local HOLD state axes are collapsed or mislabeled",
                )
                add_error(
                    errors,
                    record.get("stage_input_R", {}).get("state") == "LOCAL_HOLD_NO_DIRECT_LAYER_BODY"
                    and record.get("stage_result_A", {}).get("state") == "LOCAL_HOLD"
                    and record.get("stage_result_A", {}).get("body") is None,
                    f"{record_id} unsupported R-to-A hold boundary mismatch",
                )
            else:
                add_error(
                    errors,
                    record.get("stage_input_R", {}).get("state") == "PASS_PRE_QA"
                    and record.get("stage_result_A", {}).get("state") == "PASS_QA"
                    and record.get("stage_input_R", {}).get("body_sha256")
                    == record.get("stage_result_A", {}).get("body_sha256"),
                    f"{record_id} direct R-to-A QA boundary mismatch",
                )
            expected_ledger.append({
                "record_id": record["record_id"],
                "dchart": record["dchart"],
                "lane": record["lane"],
                "lane_order": record["lane_order"],
                "status": record["status"],
                "source_refs": record["source_refs"],
                "decision": record["decision"],
                "decision_edges": record["decision_edges"],
                "stage_input_R": record["stage_input_R"],
                "stage_result_A": record["stage_result_A"],
                "authority_state": record["authority_state"],
                "data_state": record["data_state"],
                "applicability_state": record["applicability_state"],
                "evidence_state": record["evidence_state"],
                "verdict": record["verdict"],
                "hold_scope": record["hold_scope"],
            })
        lane_entries.append({
            "lane": lane,
            "lane_order": order,
            "status": actual.get("status"),
            **artifact_metadata(path, root),
        })

    add_error(errors, len(seen_records) == 580, "active-pair record total is not 580")
    compare("decision ledger", ledger, expected_ledger, errors)
    compare("lane manifest entries", manifest.get("lane_artifacts"), lane_entries, errors)
    add_error(errors, manifest.get("production_started") is True, "admitted source did not start production")
    counts = manifest.get("counts", {})
    expected_counts = {
        "dcharts": 20,
        "rashi_blocks": 20,
        "bhava_blocks": 20,
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
    compare("manifest counts", counts, expected_counts, errors)

    physical_3p = manifest.get("physical_3p", {})
    add_error(errors, physical_3p.get("state") == "VOID", "3P state is not VOID")
    add_error(errors, physical_3p.get("active_lane") is False, "3P was made active")
    add_error(errors, physical_3p.get("count") == 20, "3P VOID count is not 20")
    members = physical_3p.get("members", [])
    void_rows = read_jsonl(root / "e5_3p_void.jsonl", errors)
    compare(
        "3P D-chart members",
        [row.get("dchart") for row in members],
        list(DCHART_ORDER),
        errors,
    )
    add_error(
        errors,
        all(row.get("state") == "VOID" and row.get("active_lane") is False for row in members),
        "one or more 3P members are not VOID",
    )
    add_error(errors, physical_3p.get("artifact") == "e5_3p_void.jsonl", "3P evidence artifact path mismatch")
    add_error(errors, len(void_rows) == 20, "3P VOID evidence row count is not 20")
    compare(
        "3P VOID evidence D-chart order",
        [row.get("dchart") for row in void_rows],
        list(DCHART_ORDER),
        errors,
    )
    add_error(
        errors,
        all(
            row.get("state") == "VOID"
            and row.get("active_lane") is False
            and row.get("body") is None
            for row in void_rows
        ),
        "3P VOID evidence fabricated a body or active lane",
    )
    add_error(
        errors,
        not any("3P" in name.upper() for name in actual_names),
        "3P was materialized as an active lane artifact",
    )

    expected_e5 = "PASS_WITH_LOCAL_HOLDS" if local_holds else "PASS"
    add_error(errors, manifest.get("e5_status") == expected_e5, "E5 contract verdict mismatch")
    add_error(errors, manifest.get("status") == "PASS", "admitted complete topology is not global PASS")
    add_error(errors, manifest.get("e6_status") == "READY_TO_RUN", "E6 was not handed off after E5 pass")
    checkpoint = manifest.get("checkpoint", {})
    add_error(
        errors,
        checkpoint.get("first_unexecuted_job") == "RUN_LONG_DRIFT_REOPEN",
        "checkpoint did not hand off to E6",
    )
    return "PASS", len(seen_records), local_holds


def validate(root: Path, source_override: Path | None, baseline_override: Path | None) -> tuple[dict[str, Any], int]:
    errors: list[str] = []
    root = root.resolve()
    verify_manifest_sidecar(root, errors)
    manifest = read_json(root / "e5_manifest.json", errors)
    if not isinstance(manifest, dict):
        result = {"status": "REVISE", "errors": errors or ["manifest is not an object"]}
        return result, 1
    add_error(errors, manifest.get("schema_version") == SCHEMA_VERSION, "schema version mismatch")
    verify_artifact_hashes(root, manifest, errors)

    source_record = manifest.get("source", {})
    source_path = (source_override or Path(source_record.get("path", ""))).resolve()
    if not source_path.is_file():
        errors.append("source file is unavailable for hash readback")
        source_bytes = b""
        source_text = ""
    else:
        source_bytes = source_path.read_bytes()
        add_error(errors, len(source_bytes) == source_record.get("bytes"), "source byte count mismatch")
        add_error(errors, sha256_bytes(source_bytes) == source_record.get("sha256"), "source SHA256 mismatch")
        add_error(errors, source_record.get("sha256") == source_record.get("expected_sha256"), "expected source SHA mismatch")
        try:
            source_text = source_bytes.decode("utf-8")
        except UnicodeDecodeError:
            source_text = ""
            errors.append("source is not strict UTF-8")

    snapshot_record = source_record.get("source_window_snapshot")
    if manifest.get("production_started"):
        if not isinstance(snapshot_record, dict):
            errors.append("Source Window snapshot binding is missing")
        else:
            snapshot_path = root / snapshot_record.get("path", "")
            add_error(errors, snapshot_path.is_file(), "Source Window snapshot file is missing")
            if snapshot_path.is_file():
                snapshot_bytes = snapshot_path.read_bytes()
                add_error(errors, len(snapshot_bytes) == snapshot_record.get("bytes"), "snapshot byte count mismatch")
                add_error(errors, sha256_bytes(snapshot_bytes) == snapshot_record.get("sha256"), "snapshot SHA256 mismatch")
                add_error(errors, snapshot_bytes == source_bytes, "validated input differs from Source Window snapshot")
            add_error(
                errors,
                snapshot_record.get("execution_authority") == "SOURCE_WINDOW_PRIMARY_REOPEN",
                "snapshot execution authority mismatch",
            )

    admission_record = source_record.get("admission", {})
    fields = admission_record.get("source_fields", {}) if isinstance(admission_record, dict) else {}
    recomputed_admission = evaluate_source_admission(
        Path(fields.get("name_or_path", str(source_path))),
        source_text,
        fields.get("created_at"),
        fields.get("created_at_source"),
        fields.get("sc_verification_basis") == "USER_CONFIRMED_SC",
    )
    compare("source admission", admission_record, recomputed_admission, errors)
    admission_artifact = read_json(root / "e5_source_admission.json", errors)
    compare("source admission artifact", admission_artifact, admission_record, errors)
    validate_provenance(source_bytes, source_record.get("provenance"), errors)
    novelty_record = source_record.get("novelty_vs_pikachu_e4")
    recomputed_novelty = audit_source_novelty(source_bytes, source_record.get("sha256", ""))
    compare("source novelty audit", novelty_record, recomputed_novelty, errors)
    novelty_artifact = read_json(root / "e5_source_novelty.json", errors)
    compare("source novelty artifact", novelty_artifact, novelty_record, errors)

    baseline_record = manifest.get("baseline", {})
    baseline = (baseline_override or Path(baseline_record.get("path", ""))).resolve()
    try:
        verify_baseline_contract(baseline)
        baseline_now = tree_snapshot(baseline)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        errors.append(f"baseline validation failed: {error}")
        baseline_now = {}
    compare("baseline pre/post", baseline_record.get("pre_files"), baseline_record.get("post_files"), errors)
    compare("baseline current/pre", baseline_now, baseline_record.get("pre_files"), errors)
    add_error(errors, baseline_record.get("unchanged") is True, "baseline unchanged flag is false")
    add_error(errors, baseline_record.get("overwrite_count") == 0, "baseline overwrite count is not zero")
    if baseline_now:
        add_error(
            errors,
            baseline_record.get("pre_tree_sha256") == tree_id(baseline_now)
            == baseline_record.get("post_tree_sha256"),
            "baseline tree SHA mismatch",
        )

    ledger = read_jsonl(root / "e5_decision_ledger.jsonl", errors)
    if admission_record.get("status") == "REJECTED" or recomputed_novelty.get("status") != "PASS":
        verdict, active_pairs, local_holds = validate_rejected(root, manifest, ledger, errors)
    elif admission_record.get("status") == "ADMITTED":
        verdict, active_pairs, local_holds = validate_admitted(
            root, manifest, source_bytes, source_text, ledger, errors
        )
    else:
        errors.append("source admission status is neither ADMITTED nor REJECTED")
        verdict, active_pairs, local_holds = "REVISE", 0, 0

    fna98 = read_json(root / "e5_fna98.json", errors)
    checkpoint = read_json(root / "e5_checkpoint.json", errors)
    compare("manifest FNa98", fna98, manifest.get("fna98"), errors)
    compare("manifest checkpoint", checkpoint, manifest.get("checkpoint"), errors)
    if isinstance(fna98, dict):
        add_error(errors, fna98.get("hard_fail_count") == 0, "FNa98 hard failure count is not zero")
        add_error(errors, fna98.get("hard_failures") == [], "FNa98 hard failure list is not empty")

    if errors:
        status = "REVISE"
        exit_code = 1
    else:
        status = verdict
        exit_code = 0 if verdict == "PASS" else 2
    result = {
        "status": status,
        "e5_status": manifest.get("e5_status"),
        "e6_status": manifest.get("e6_status"),
        "source_admission": admission_record.get("status"),
        "active_lane_artifacts": manifest.get("counts", {}).get("active_lane_artifacts"),
        "active_pair_records": active_pairs,
        "local_hold_lanes": local_holds,
        "physical_3p_void": manifest.get("counts", {}).get("physical_3p_members"),
        "baseline_unchanged": not errors and baseline_record.get("unchanged") is True,
        "hard_failures": 0 if not errors else len(errors),
        "errors": errors,
        "manifest_sha256": sha256_file(root / "e5_manifest.json") if (root / "e5_manifest.json").is_file() else None,
    }
    return result, exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("overlay", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result, exit_code = validate(args.overlay, args.source, args.baseline)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        result, exit_code = {"status": "REVISE", "errors": [str(error)]}, 1
    print(compact_json(result))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

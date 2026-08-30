#!/usr/bin/env python3
"""Create the KANI V10 E6 read-only reopen evidence overlay.

This runner reopens the immutable V9 history, the V10 E5 COPRESENCE
execution ledger, and the independent 240-record second-action calibration.
It writes only to a new E6 directory.  Passing this tested overlay does not
promote SECOND_RESTORE or the global 29-lane runtime to final PASS.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_E5_DIR = ROOT / "references" / "v10_runs" / "run_20260830_vas27" / "e5"
DEFAULT_V9_BASELINE = ROOT / "references" / "v9_baseline"
DEFAULT_V9_E5_MANIFEST = (
    ROOT / "references" / "v9_closure_runs" / "run_20260829_vas26" / "e5" / "e5_manifest.json"
)
DEFAULT_V9_E6_MANIFEST = (
    ROOT / "references" / "v9_closure_runs" / "run_20260829_vas26" / "e6" / "e6_manifest.json"
)
DEFAULT_AUDIT_SIDECAR = ROOT / "references" / "v10_runtime" / "v9_e5_e6_audit_sidecar.json"
DEFAULT_SOURCE_DIR = ROOT / "references" / "v10_sources" / "user_upload_20260830"
DEFAULT_ROUTER = ROOT / "references" / "DATASET_TO_PIKACHU_JUDGMENT_ROUTER_V10.json"
DEFAULT_CALIBRATION_DIR = ROOT / "references" / "v10_runtime" / "router_run"
DEFAULT_CALIBRATION_REPORT = ROOT / "references" / "v10_runtime" / "independent_router_report.json"
DEFAULT_CALIBRATION_LEDGER = ROOT / "references" / "v10_runtime" / "independent_router_replay.jsonl"

SCHEMA_VERSION = "KANI_V10_E6_REOPEN_OVERLAY_V1"
REPLAY_SCHEMA_VERSION = "KANI_V10_E6_REPLAY_RECORD_V1"
SOURCE_FILENAME = "HYEWON_VAS27_D1-D60_♤.txt"
EXPECTED_FILENAME = "HEAWON_VAS27_CO2_99_♤.txt"
SOURCE_DCHART_ORDER = (
    "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10",
    "D11", "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60",
)
BOUNDARY_TESTS = (
    "DIRECT_D1_ROOT_DISPATCH",
    "DIRECT_TARGET_DCHART_DISPATCH",
    "BOUNDARY_TARGET_DCHART_D60",
    "RASHI_BHAVA_SEPARATION",
    "OCCUPANT_LORD_FIELD_BOUNDARY",
    "EMPTY_HOUSE_LORD_ROUTE",
    "RASHI_DEGREE_ORDER_BHAVA_NO_DEGREE_ORDER",
    "SINGLE_FIELD_NOT_PROMOTED_TO_COPRESENCE",
    "DATASET_TO_JUDGMENT_TO_PIKACHU_EXACT_REPLAY",
)


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def compact_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def metadata(path: Path) -> dict[str, Any]:
    return {"bytes": path.stat().st_size, "sha256": sha256_file(path)}


def read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("rb") as stream:
        for number, raw_line in enumerate(stream, start=1):
            if not raw_line.endswith(b"\n") or not raw_line.strip():
                raise ValueError(f"non-canonical JSONL row: {path}:{number}")
            value = json.loads(raw_line.decode("utf-8"))
            if not isinstance(value, dict):
                raise ValueError(f"JSONL object required: {path}:{number}")
            rows.append(value)
    return rows


def write_exclusive(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return str(resolved)


def tree_snapshot(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise ValueError(f"protected path may not be a symlink: {path}")
    if path.is_file():
        return {"kind": "file", **metadata(path)}
    if not path.is_dir():
        raise ValueError(f"protected path missing: {path}")
    files: dict[str, dict[str, Any]] = {}
    for member in sorted(path.rglob("*")):
        if member.is_symlink():
            raise ValueError(f"protected tree contains symlink: {member}")
        if member.is_file():
            files[member.relative_to(path).as_posix()] = metadata(member)
    return {
        "files": files,
        "kind": "directory",
        "tree_sha256": sha256_bytes(compact_json(files)),
    }


def function_location(function: Any) -> str:
    lines, start = inspect.getsourcelines(function)
    relative = Path(__file__).resolve().relative_to(ROOT).as_posix()
    return f"{relative}:{start}-{start + len(lines) - 1}::{function.__name__}"


def normalize_rashi_actor(label: str) -> str:
    if label.startswith("Muntha"):
        return "Muntha (Mu)"
    actor = re.sub(r"\([^)]*\)", "", label).strip()
    if "(R)" in label:
        actor += " (R)"
    return actor


def degree_key(value: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"([0-9]{1,2}):([0-9]{2}):([0-9]{2})", value)
    if match is None:
        raise ValueError(f"degree grammar: {value!r}")
    return tuple(int(part) for part in match.groups())


def render_sentence(
    router: dict[str, Any], dchart: str, view: str, location: str,
    member_display: str, degree_order: str | None, selected_route: str,
) -> str:
    route_views = [
        route_view for route_view, route in router["judgment_routes"].items()
        if route["selected_route"] == selected_route
    ]
    if route_views != [view]:
        raise ValueError("selected judgment route does not dispatch the requested view")
    rule = router["dchart_rules"][dchart]
    reality = rule[f"{view.casefold()}_reality_rule"] if dchart == "D1" else rule["reality_rule"]
    return router["sentence_templates"][route_views[0]].format_map({
        "DCHART": dchart,
        "DEGREE_ORDER": degree_order or "NOT_APPLICABLE",
        "LOCATION": location,
        "MEMBERS_PLUS": member_display.replace(" / ", " + "),
        "REALITY_RULE": reality,
        "ROLE": rule["role"],
        "YEAR": 2027,
    })


def derive_source_topology(path: Path, router: dict[str, Any]) -> tuple[dict[tuple[str, str, str], dict[str, Any]], dict[str, int]]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or b"\x00" in raw or not raw.endswith(b"\n"):
        raise ValueError("VAS27 source byte boundary")
    text = raw.decode("utf-8")
    markers = list(re.finditer(r"^\[(D[0-9]+) (RASHI|BHAVA) SOURCE\]$", text, re.MULTILINE))
    expected_markers = [(dchart, view) for dchart in SOURCE_DCHART_ORDER for view in ("RASHI", "BHAVA")]
    if [(match.group(1), match.group(2)) for match in markers] != expected_markers:
        raise ValueError("VAS27 source marker topology")
    bhava_codes = router["actor_normalization"]["bhava_codes"]
    code_pattern = re.compile("|".join(re.escape(code) for code in sorted(bhava_codes, key=len, reverse=True)))
    topology: dict[tuple[str, str, str], dict[str, Any]] = {}
    singleton_count = 0
    for marker_index, marker in enumerate(markers):
        start_offset = marker.end()
        end_offset = markers[marker_index + 1].start() if marker_index + 1 < len(markers) else len(text)
        block = text[start_offset:end_offset]
        local_lines = block.splitlines()
        block_start_line = text.count("\n", 0, start_offset) + 1
        dchart, view = marker.group(1), marker.group(2)
        family_selected = "D1_ROOT" if dchart == "D1" else "TARGET_DCHART"
        family_rejected = "TARGET_DCHART" if dchart == "D1" else "D1_ROOT_SINGLE_GRAMMAR"
        candidates: list[tuple[str, list[dict[str, Any]], str | None]] = []
        if view == "RASHI":
            heading = [index for index, line in enumerate(local_lines) if line.startswith("Visible Planetary Positions")]
            if len(heading) != 1:
                raise ValueError(f"Rashi heading: {dchart}")
            stop = next(
                (index for index, line in enumerate(local_lines[heading[0] + 1:], start=heading[0] + 1)
                 if line.startswith("Visible Vimshottari Mudda Dasha") or line == "Lock Status"),
                None,
            )
            if stop is None:
                raise ValueError(f"Rashi stop: {dchart}")
            groups: dict[str, list[dict[str, Any]]] = {}
            source_rows = 0
            row_pattern = re.compile(r"^- (.+?) — Degree ([^/]+) / Rashi ([^/]+) /")
            for local_index in range(heading[0] + 1, stop):
                match = row_pattern.match(local_lines[local_index])
                if match is None:
                    continue
                source_rows += 1
                degree, sign = match.group(2).strip(), match.group(3).strip()
                if degree == "not shown" and sign == "not shown":
                    continue
                degree_key(degree)
                groups.setdefault(sign, []).append({
                    "actor": normalize_rashi_actor(match.group(1)),
                    "degree": degree,
                    "line": block_start_line + local_index,
                    "raw": local_lines[local_index],
                })
            if source_rows != 14:
                raise ValueError(f"Rashi row count: {dchart}")
            for location, members in groups.items():
                if len(members) == 1:
                    singleton_count += 1
                    continue
                if len(members) < 2:
                    continue
                ordered = sorted(members, key=lambda item: degree_key(item["degree"]))
                candidates.append((location, ordered, " → ".join(f"{item['actor']} {item['degree']}" for item in ordered)))
        else:
            heading = [index for index, line in enumerate(local_lines) if line == "Visible Bhava Snapshot"]
            if len(heading) != 1:
                raise ValueError(f"Bhava heading: {dchart}")
            stop = next(
                (index for index, line in enumerate(local_lines[heading[0] + 1:], start=heading[0] + 1)
                 if line.startswith("- Wheel Readability")),
                None,
            )
            if stop is None:
                raise ValueError(f"Bhava stop: {dchart}")
            row_pattern = re.compile(r"^- (.+? Sector) = (.+)$")
            for local_index in range(heading[0] + 1, stop):
                match = row_pattern.match(local_lines[local_index])
                if match is None or match.group(2).startswith("empty"):
                    continue
                tokens = code_pattern.findall(match.group(2))
                if len(tokens) == 1:
                    singleton_count += 1
                    continue
                if len(tokens) < 2:
                    continue
                members = [{
                    "actor": bhava_codes[token],
                    "line": block_start_line + local_index,
                    "raw": local_lines[local_index],
                } for token in tokens]
                candidates.append((match.group(1), members, None))
        for location, members, degree_order in candidates:
            key = (dchart, view, location)
            if key in topology:
                raise ValueError(f"duplicate VAS27 route: {key}")
            member_display = " / ".join(
                f"{item['actor']} {item['degree']}" if "degree" in item else item["actor"]
                for item in members
            )
            topology[key] = {
                "degree_order": degree_order,
                "family_rejected_route": family_rejected,
                "family_selected_route": family_selected,
                "member_count": len(members),
                "member_display": member_display,
                "sentence": render_sentence(
                    router, dchart, view, location, member_display, degree_order,
                    router["judgment_routes"][view]["selected_route"],
                ),
                "source_line_locations": [
                    {key: item[key] for key in ("actor", "degree", "line", "raw") if key in item}
                    if view == "RASHI" else {
                        "line": item["line"], "raw": item["raw"], "visible_sector": location,
                    }
                    for item in members[:1] if view == "BHAVA"
                ] if view == "BHAVA" else [
                    {"actor": item["actor"], "line": item["line"], "raw": item["raw"]}
                    for item in members
                ],
                "source_wrapper_line_end": block_start_line + len(local_lines) - 1,
                "source_wrapper_line_start": block_start_line,
            }
    counts = {
        "bhava_records": sum(key[1] == "BHAVA" for key in topology),
        "rashi_records": sum(key[1] == "RASHI" for key in topology),
        "single_fields_excluded": singleton_count,
        "source_blocks": len(markers),
        "total_records": len(topology),
    }
    return topology, counts


def parse_oracle(path: Path) -> dict[tuple[str, str, str], dict[str, Any]]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or b"\x00" in raw:
        raise ValueError("VAS27 oracle byte boundary")
    text = raw.decode("utf-8")
    starts = list(re.finditer(
        r"^\[(HYEWON_2027_VAS_(D[0-9]+)_(RASHI|BHAVA)_[^\]]+_CO_FIELD)\]$",
        text, re.MULTILINE,
    ))
    if len(starts) != 114:
        raise ValueError("VAS27 oracle record count")
    rows: dict[tuple[str, str, str], dict[str, Any]] = {}
    for index, start in enumerate(starts):
        end_offset = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        block = text[start.start():end_offset]
        block_line = text.count("\n", 0, start.start()) + 1

        def field(label: str) -> tuple[str, int]:
            hits = list(re.finditer(rf"^- {re.escape(label)} = (.*)$", block, re.MULTILINE))
            if len(hits) != 1:
                raise ValueError(f"oracle field {label}: {start.group(1)}")
            return hits[0].group(1), block_line + block.count("\n", 0, hits[0].start())

        location_value, _ = field("Location")
        members, members_line = field("Members")
        sentence, sentence_line = field("2.5차 관절문")
        location = location_value.split(" / ", 1)[1]
        key = (start.group(2), start.group(3), location)
        rows[key] = {
            "block_id": start.group(1),
            "block_line_start": block_line,
            "members": members,
            "members_line": members_line,
            "sentence": sentence,
            "sentence_line": sentence_line,
        }
    return rows


def validate_e5(
    e5_dir: Path, source_dir: Path, router_path: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[tuple[str, str, str], dict[str, Any]], dict[str, int]]:
    manifest = read_object(e5_dir / "e5_manifest.json")
    ledger_path = e5_dir / "e5_decision_ledger.jsonl"
    records = read_jsonl(ledger_path)
    router = read_object(router_path)
    if manifest.get("schema_version") != "KANI_V10_E5_EXECUTION_OVERLAY_V1":
        raise ValueError("E5 schema")
    if manifest.get("status") != "PASS_EXECUTION_EVIDENCE_114_OF_114":
        raise ValueError("E5 tested-scope status")
    if manifest.get("second_restore") != "EVIDENCE_REVIEW" or manifest.get("v10") != "EXPECTED_VALUE_BOUND":
        raise ValueError("E5 review state")
    if manifest.get("final_pass") != "HOLD_USER_REVIEW_OF_RECORD_REPLAY_EVIDENCE":
        raise ValueError("E5 promotion firewall")
    if manifest.get("global_29_lane_e5") != "HOLD_28_JUDGMENT_TO_SENTENCE_LANES_UNTESTED":
        raise ValueError("E5 global lane hold")
    artifact = manifest.get("artifacts", {}).get("e5_decision_ledger.jsonl", {})
    if artifact != {"bytes": ledger_path.stat().st_size, "records": len(records), "sha256": sha256_file(ledger_path)}:
        raise ValueError("E5 ledger manifest binding")
    if manifest.get("router", {}).get("sha256") != sha256_file(router_path):
        raise ValueError("E5 router hash")
    if router.get("boundary_tests") != list(BOUNDARY_TESTS):
        raise ValueError("V10 boundary contract")
    topology, counts = derive_source_topology(source_dir / SOURCE_FILENAME, router)
    oracle = parse_oracle(source_dir / EXPECTED_FILENAME)
    expected_counts = {
        "bhava_records": 50,
        "rashi_records": 64,
        "single_fields_excluded": 165,
        "source_blocks": 40,
        "total_records": 114,
    }
    if counts != expected_counts or set(topology) != set(oracle):
        raise ValueError("E5 live source/oracle topology")
    seen: set[str] = set()
    for ordinal, record in enumerate(records, start=1):
        record_id = f"V10-E5-VAS27-{ordinal:04d}"
        if record.get("record_id") != record_id or record_id in seen:
            raise ValueError(f"E5 record identity: {ordinal}")
        seen.add(record_id)
        dataset = record.get("dataset", {})
        key = (dataset.get("dchart"), dataset.get("view"), dataset.get("location"))
        if key not in topology:
            raise ValueError(f"E5 route key: {record_id}")
        derived, expected = topology[key], oracle[key]
        route = router["judgment_routes"][key[1]]
        if any((
            dataset.get("member_display") != derived["member_display"],
            dataset.get("family_selected_route") != derived["family_selected_route"],
            dataset.get("family_rejected_route") != derived["family_rejected_route"],
            dataset.get("source_line_locations") != derived["source_line_locations"],
            dataset.get("source_wrapper_line_start") != derived["source_wrapper_line_start"],
            dataset.get("source_wrapper_line_end") != derived["source_wrapper_line_end"],
            record.get("judgment_route") != route,
            record.get("output", {}).get("pikachu_sentence") != derived["sentence"],
            derived["sentence"] != expected["sentence"],
            derived["member_display"] != expected["members"],
            record.get("expected", {}).get("sentence_line") != expected["sentence_line"],
            record.get("expected", {}).get("members_line") != expected["members_line"],
            record.get("handoff_target") != router["handoff"]["target_pattern"].format(
                DCHART=key[0], VIEW=key[1], LOCATION=key[2]
            ),
            record.get("reinput_result", {}).get("status") != "PASS_EXACT_PIKACHU_SENTENCE_REPLAY",
        )):
            raise ValueError(f"E5 live record replay: {record_id}")
        sentence = record["output"]["pikachu_sentence"]
        if record["output"].get("pikachu_sentence_sha256") != sha256_bytes(sentence.encode("utf-8")):
            raise ValueError(f"E5 sentence hash: {record_id}")
        if record.get("why_revision_qa", {}).get("correction") != router["why_correction_qa"]["correction"]:
            raise ValueError(f"E5 Why correction: {record_id}")
    if len(records) != 114 or len(seen) != 114:
        raise ValueError("E5 record count")
    return manifest, records, topology, counts


def build_replay_row(
    ordinal: int, record: dict[str, Any], derived: dict[str, Any], expected: dict[str, Any],
) -> dict[str, Any]:
    dataset = record["dataset"]
    sentence = record["output"]["pikachu_sentence"]
    return {
        "code_location": {
            "e5_render_and_route": record["code_location"],
            "e6_reopen": function_location(build_replay_row),
        },
        "dataset_to_judgment_route_to_pikachu_sentence": {
            "dataset": {
                "dchart": dataset["dchart"],
                "location": dataset["location"],
                "member_display": dataset["member_display"],
                "view": dataset["view"],
                "year": dataset["year"],
            },
            "judgment_route": record["judgment_route"],
            "pikachu_sentence": sentence,
        },
        "e5_record_id": record["record_id"],
        "e5_record_sha256": sha256_bytes(compact_json(record)),
        "expected_location": {
            "block_id": expected["block_id"],
            "block_line_start": expected["block_line_start"],
            "members_line": expected["members_line"],
            "sentence_line": expected["sentence_line"],
        },
        "handoff_target": record["handoff_target"],
        "record_id": f"V10-E6-REOPEN-{ordinal:04d}",
        "reinput_result": {
            "e5_status": record["reinput_result"]["status"],
            "expected_sentence_hash_readback": sha256_bytes(expected["sentence"].encode("utf-8")),
            "rendered_sentence_hash_readback": sha256_bytes(derived["sentence"].encode("utf-8")),
            "status": "PASS_REOPEN_EXACT_DATASET_JUDGMENT_SENTENCE",
        },
        "rejected_route": record["judgment_route"]["rejected_route"],
        "schema_version": REPLAY_SCHEMA_VERSION,
        "selected_route": record["judgment_route"]["selected_route"],
        "source_location": {
            "file": dataset["source_file"],
            "file_sha256": dataset["source_file_sha256"],
            "line_locations": dataset["source_line_locations"],
            "wrapper_line_end": dataset["source_wrapper_line_end"],
            "wrapper_line_start": dataset["source_wrapper_line_start"],
        },
        "status": "PASS_REOPEN_EXACT_RECORD",
        "why_revision_qa": record["why_revision_qa"],
    }


def probe(test_id: str, passed: bool, expected: Any, observed: Any, evidence: list[str]) -> dict[str, Any]:
    return {
        "evidence": evidence,
        "expected": expected,
        "observed": observed,
        "status": "PASS" if passed else "FAIL",
        "test_id": test_id,
    }


def build_boundary_tests(
    records: list[dict[str, Any]], topology: dict[tuple[str, str, str], dict[str, Any]],
    counts: dict[str, int], calibration_records: list[dict[str, Any]], calibration_report: dict[str, Any],
) -> list[dict[str, Any]]:
    d1 = [row for row in records if row["dataset"]["dchart"] == "D1"]
    non_d1 = [row for row in records if row["dataset"]["dchart"] != "D1"]
    d60 = [row for row in records if row["dataset"]["dchart"] == "D60"]
    rashi = [row for row in records if row["dataset"]["view"] == "RASHI"]
    bhava = [row for row in records if row["dataset"]["view"] == "BHAVA"]
    results: list[dict[str, Any]] = []
    results.append(probe(
        BOUNDARY_TESTS[0],
        bool(d1) and all(row["dataset"]["family_selected_route"] == "D1_ROOT" and row["dataset"]["family_rejected_route"] == "TARGET_DCHART" for row in d1),
        "ALL_D1_RECORDS_SELECT_D1_ROOT_REJECT_TARGET_DCHART",
        {"records": len(d1), "selected": "D1_ROOT", "rejected": "TARGET_DCHART"},
        [row["record_id"] for row in d1],
    ))
    results.append(probe(
        BOUNDARY_TESTS[1],
        bool(non_d1) and all(row["dataset"]["family_selected_route"] == "TARGET_DCHART" and row["dataset"]["family_rejected_route"] == "D1_ROOT_SINGLE_GRAMMAR" for row in non_d1),
        "ALL_NON_D1_RECORDS_SELECT_TARGET_DCHART_REJECT_D1_ROOT_SINGLE_GRAMMAR",
        {"records": len(non_d1), "selected": "TARGET_DCHART", "rejected": "D1_ROOT_SINGLE_GRAMMAR"},
        [row["record_id"] for row in records if row["dataset"]["dchart"] == "D9"],
    ))
    results.append(probe(
        BOUNDARY_TESTS[2],
        bool(d60) and all(row["dataset"]["family_selected_route"] == "TARGET_DCHART" for row in d60),
        "D60_RETAINS_TARGET_DCHART_BOUNDARY",
        {"records": len(d60), "selected": "TARGET_DCHART"},
        [row["record_id"] for row in d60],
    ))
    route_keys = {(row["dataset"]["dchart"], row["dataset"]["view"], row["dataset"]["location"]) for row in records}
    results.append(probe(
        BOUNDARY_TESTS[3],
        len(rashi) == 64 and len(bhava) == 50 and len(route_keys) == 114
        and all(row["judgment_route"]["selected_route"].startswith("RASHI_") for row in rashi)
        and all(row["judgment_route"]["selected_route"].startswith("BHAVA_") for row in bhava),
        "64_RASHI_PLUS_50_BHAVA_DISTINCT_ROUTE_KEYS_NO_VIEW_OVERWRITE",
        {"bhava_records": len(bhava), "rashi_records": len(rashi), "unique_route_keys": len(route_keys)},
        ["e5_decision_ledger.jsonl#dataset.view", "e5_decision_ledger.jsonl#judgment_route"],
    ))
    field_boundary_ok = all(
        isinstance(row.get("slot_bindings"), dict)
        and "OCCUPANT_FIELD" in row["slot_bindings"]
        and "HOUSE_LORD_FIELD" in row["slot_bindings"]
        and row.get("boundary_test", {}).get("field_objects_distinct") is True
        and row.get("boundary_test", {}).get("house_lord_appended_to_occupants") is False
        for row in calibration_records
    )
    results.append(probe(
        BOUNDARY_TESTS[4],
        len(calibration_records) == 240 and field_boundary_ok and calibration_report.get("status") == "PASS",
        "240_CALIBRATION_RECORDS_KEEP_OCCUPANT_AND_HOUSE_LORD_AS_DISTINCT_FIELDS",
        {"independent_report": calibration_report.get("status"), "records": len(calibration_records)},
        ["references/v10_runtime/router_run/router_records.jsonl", "references/v10_runtime/independent_router_report.json"],
    ))
    golden = next((row for row in calibration_records if row.get("record_id") == "KANI-V10-D6-H05"), {})
    golden_ok = (
        golden.get("slot_bindings", {}).get("OCCUPANT_FIELD") == "EMPTY"
        and golden.get("slot_bindings", {}).get("HOUSE_LORD_FIELD") == "Mars"
        and golden.get("route", {}).get("selected_route") == "HOUSE_LORD_ROUTE"
        and golden.get("route", {}).get("rejected_route") == "OCCUPANT_ROUTE"
        and golden.get("source", {}).get("file_sha256") == "50353b4a608b383026f7158f7fe915efc5cdb2e1a04747cc1ee90d9b78479e35"
        and calibration_report.get("golden_D6_H05") == "PASS"
    )
    results.append(probe(
        BOUNDARY_TESTS[5], golden_ok,
        "D6_H05_EMPTY_SELECTS_HOUSE_LORD_MARS_AND_REJECTS_OCCUPANT_ROUTE",
        {
            "house_lord": golden.get("slot_bindings", {}).get("HOUSE_LORD_FIELD"),
            "occupants": golden.get("slot_bindings", {}).get("OCCUPANT_FIELD"),
            "rejected": golden.get("route", {}).get("rejected_route"),
            "selected": golden.get("route", {}).get("selected_route"),
        },
        ["KANI-V10-D6-H05", "references/v10_runtime/independent_router_report.json#golden_D6_H05"],
    ))
    rashi_order_ok = all(
        row["judgment_route"]["degree_policy"] == "ASCENDING_VISIBLE_DEGREE_WITHIN_SAME_SIGN"
        and " → ".join(part for part in row["dataset"]["member_display"].split(" / ")) in row["output"]["pikachu_sentence"]
        for row in rashi
    )
    bhava_order_ok = all(
        row["judgment_route"]["degree_policy"] == "NOT_APPLIED_VISIBLE_SNAPSHOT_ONLY"
        and " → " not in row["output"]["pikachu_sentence"]
        for row in bhava
    )
    results.append(probe(
        BOUNDARY_TESTS[6], rashi_order_ok and bhava_order_ok,
        "RASHI_ASCENDING_VISIBLE_DEGREES__BHAVA_VISIBLE_ORDER_WITHOUT_DEGREE_INFERENCE",
        {"bhava_no_degree_order": sum(bhava_order_ok for _ in [0]) * len(bhava), "rashi_degree_order": sum(rashi_order_ok for _ in [0]) * len(rashi)},
        ["e5_decision_ledger.jsonl#dataset.member_display", "e5_decision_ledger.jsonl#judgment_route.degree_policy"],
    ))
    results.append(probe(
        BOUNDARY_TESTS[7],
        counts.get("single_fields_excluded") == 165 and len(topology) == 114
        and all(row["member_count"] >= 2 for row in topology.values()),
        "165_SINGLE_FIELDS_EXCLUDED_AND_ZERO_SINGLETON_COPRESENCE_RECORDS",
        {"copresence_records": len(topology), "single_fields_excluded": counts.get("single_fields_excluded")},
        [f"{SOURCE_FILENAME}#40_SOURCE_WRAPPERS", "e5_manifest.json#counts.single_fields_excluded"],
    ))
    replay_ok = all(
        row["reinput_result"].get("status") == "PASS_EXACT_PIKACHU_SENTENCE_REPLAY"
        and row["output"].get("pikachu_sentence_sha256") == row["expected"].get("sentence_sha256")
        for row in records
    )
    results.append(probe(
        BOUNDARY_TESTS[8], len(records) == 114 and replay_ok,
        "114_OF_114_DATASET_TO_JUDGMENT_ROUTE_TO_PIKACHU_SENTENCE_EXACT_REPLAY",
        {"exact_replay": sum(
            row["output"].get("pikachu_sentence_sha256") == row["expected"].get("sentence_sha256")
            for row in records
        ), "records": len(records)},
        ["e6_replay_ledger.jsonl", f"{EXPECTED_FILENAME}#114_CO_FIELD_2.5_STAGE_SENTENCES"],
    ))
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--e5-dir", type=Path, default=DEFAULT_E5_DIR)
    parser.add_argument("--v9-baseline", type=Path, default=DEFAULT_V9_BASELINE)
    parser.add_argument("--v9-e5-manifest", type=Path, default=DEFAULT_V9_E5_MANIFEST)
    parser.add_argument("--v9-e6-manifest", type=Path, default=DEFAULT_V9_E6_MANIFEST)
    parser.add_argument("--audit-sidecar", type=Path, default=DEFAULT_AUDIT_SIDECAR)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--router", type=Path, default=DEFAULT_ROUTER)
    parser.add_argument("--calibration-dir", type=Path, default=DEFAULT_CALIBRATION_DIR)
    parser.add_argument("--calibration-report", type=Path, default=DEFAULT_CALIBRATION_REPORT)
    parser.add_argument("--calibration-ledger", type=Path, default=DEFAULT_CALIBRATION_LEDGER)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    paths = {name: value.resolve() for name, value in {
        "e5_overlay": args.e5_dir,
        "v9_baseline": args.v9_baseline,
        "v9_historical_e5": args.v9_e5_manifest.parent,
        "v9_historical_e6": args.v9_e6_manifest.parent,
        "v9_audit_sidecar": args.audit_sidecar,
        "v10_source_registry": args.source_dir,
        "v10_router": args.router,
        "second_action_calibration": args.calibration_dir,
        "second_action_independent_report": args.calibration_report,
        "second_action_independent_ledger": args.calibration_ledger,
    }.items()}
    out_dir = args.out_dir.resolve()
    if out_dir.exists() and (not out_dir.is_dir() or any(out_dir.iterdir())):
        raise SystemExit(f"output directory must not exist or must be empty: {out_dir}")
    for name, protected in paths.items():
        if out_dir == protected or out_dir in protected.parents or protected in out_dir.parents:
            raise SystemExit(f"output overlaps protected input {name}: {protected}")
    out_dir.mkdir(parents=True, exist_ok=True)
    before = {name: tree_snapshot(path) for name, path in paths.items()}

    e5_manifest, records, topology, topology_counts = validate_e5(
        paths["e5_overlay"], paths["v10_source_registry"], paths["v10_router"]
    )
    router = read_object(paths["v10_router"])
    oracle = parse_oracle(paths["v10_source_registry"] / EXPECTED_FILENAME)
    calibration_manifest = read_object(paths["second_action_calibration"] / "router_run_manifest.json")
    calibration_records = read_jsonl(paths["second_action_calibration"] / "router_records.jsonl")
    calibration_report = read_object(paths["second_action_independent_report"])
    calibration_ledger = read_jsonl(paths["second_action_independent_ledger"])
    if calibration_manifest.get("status") != "PASS_TESTED_SCOPE_240":
        raise SystemExit("second-action calibration manifest is not PASS_TESTED_SCOPE_240")
    if calibration_manifest.get("records") != {
        "bytes": (paths["second_action_calibration"] / "router_records.jsonl").stat().st_size,
        "path": "router_records.jsonl",
        "sha256": sha256_file(paths["second_action_calibration"] / "router_records.jsonl"),
    }:
        raise SystemExit("second-action calibration record binding")
    if calibration_report.get("status") != "PASS" or calibration_report.get("producer_imported") is not False:
        raise SystemExit("second-action independent calibration validation")
    if calibration_report.get("independent_ledger") != {
        "bytes": paths["second_action_independent_ledger"].stat().st_size,
        "records": len(calibration_ledger),
        "sha256": sha256_file(paths["second_action_independent_ledger"]),
    }:
        raise SystemExit("second-action independent ledger binding")
    if len(calibration_records) != 240 or len(calibration_ledger) != 240:
        raise SystemExit("second-action calibration count")

    v9_e5_manifest = read_object(args.v9_e5_manifest.resolve())
    v9_e6_manifest = read_object(args.v9_e6_manifest.resolve())
    audit = read_object(paths["v9_audit_sidecar"])
    if audit.get("e5", {}).get("artifact_sha256") != sha256_file(args.v9_e5_manifest.resolve()):
        raise SystemExit("V9 E5 audit-sidecar hash binding")
    if audit.get("e6", {}).get("artifact_sha256") != sha256_file(args.v9_e6_manifest.resolve()):
        raise SystemExit("V9 E6 audit-sidecar hash binding")
    if audit.get("e5", {}).get("v10_authoritative_status") != "MATERIALIZATION_PASS__ROUTER_HOLD_NOT_ROUTER":
        raise SystemExit("V9 E5 correction status")
    if audit.get("e6", {}).get("v10_authoritative_status") != "HOLD_ENTRY_E5_NOT_PASS":
        raise SystemExit("V9 E6 correction status")

    replay_rows = [
        build_replay_row(
            ordinal, record,
            topology[(record["dataset"]["dchart"], record["dataset"]["view"], record["dataset"]["location"])],
            oracle[(record["dataset"]["dchart"], record["dataset"]["view"], record["dataset"]["location"])],
        )
        for ordinal, record in enumerate(records, start=1)
    ]
    boundary_rows = build_boundary_tests(records, topology, topology_counts, calibration_records, calibration_report)
    if [row["test_id"] for row in boundary_rows] != list(BOUNDARY_TESTS) or any(row["status"] != "PASS" for row in boundary_rows):
        raise SystemExit("V10 E6 boundary test failure")

    after = {name: tree_snapshot(path) for name, path in paths.items()}
    changed = [name for name in paths if before[name] != after[name]]
    if changed:
        raise SystemExit(f"protected input changed during reopen: {changed}")

    replay_bytes = b"".join(compact_json(row) + b"\n" for row in replay_rows)
    boundary_document = {
        "pass_count": 9,
        "schema_version": SCHEMA_VERSION,
        "status": "PASS_9_OF_9",
        "test_count": 9,
        "tests": boundary_rows,
    }
    boundary_bytes = canonical_json(boundary_document)
    reopen_document = {
        "changed_protected_inputs": changed,
        "execution_counters": {
            "e5_write_count": 0,
            "github_read_count": 0,
            "lower_stage_rebuild_count": 0,
            "other_remote_read_count": 0,
            "v9_write_count": 0,
        },
        "protected_inputs": {
            name: {
                "after": after[name],
                "before": before[name],
                "path": display_path(paths[name]),
                "unchanged": before[name] == after[name],
            }
            for name in sorted(paths)
        },
        "schema_version": SCHEMA_VERSION,
        "status": "PASS_READ_ONLY_REOPEN",
    }
    reopen_bytes = canonical_json(reopen_document)
    transcript = (
        "KANI V10 E6 EXECUTION EVIDENCE OVERLAY\n"
        "OVERLAY=ADD_TO_V9_DO_NOT_OVERWRITE\n"
        "E5_DECISION_LEDGER_REOPEN=114/114\n"
        "DATASET_TO_JUDGMENT_ROUTE_TO_PIKACHU_SENTENCE_REPLAY=114/114\n"
        "BOUNDARY_TEST=9/9 PASS\n"
        "SECOND_ACTION_CALIBRATION=240/240 INDEPENDENT PASS\n"
        "V9_BASELINE_WRITE_COUNT=0\n"
        "V10_E5_WRITE_COUNT=0\n"
        "GLOBAL_29_LANE_E5=HOLD_28_JUDGMENT_TO_SENTENCE_LANES_UNTESTED\n"
        "REAL_LONG_DRIFT=HOLD_REAL_LONG_DRIFT_NOT_PROVEN\n"
        "SECOND_RESTORE=EVIDENCE_REVIEW\n"
        "V10=EXPECTED_VALUE_BOUND\n"
        "FINAL_PASS=HOLD_USER_REVIEW_OF_RECORD_REPLAY_EVIDENCE\n"
    ).encode("utf-8")

    artifact_payloads = {
        "e6_replay_ledger.jsonl": replay_bytes,
        "boundary_test_9of9.json": boundary_bytes,
        "e6_reopen_record.json": reopen_bytes,
        "e6_transcript.txt": transcript,
    }
    for name, payload in artifact_payloads.items():
        write_exclusive(out_dir / name, payload)

    manifest = {
        "artifacts": {
            name: {
                "bytes": len(payload),
                **({"records": len(replay_rows)} if name == "e6_replay_ledger.jsonl" else {}),
                "sha256": sha256_bytes(payload),
            }
            for name, payload in artifact_payloads.items()
        },
        "boundary_test": {
            "pass_count": 9,
            "status": "PASS_9_OF_9",
            "test_count": 9,
        },
        "counts": {
            "bhava_replay_records": 50,
            "copresence_replay_records": 114,
            "rashi_replay_records": 64,
            "second_action_calibration_records": 240,
            "single_fields_excluded": 165,
        },
        "entry_condition": {
            "e5_manifest_sha256": sha256_file(paths["e5_overlay"] / "e5_manifest.json"),
            "e5_run_id": e5_manifest["run_id"],
            "e5_status": e5_manifest["status"],
            "observed": "PASS_TESTED_COPRESENCE_EXECUTION_SCOPE",
            "required": "V10_E5_EXECUTION_EVIDENCE_114_OF_114",
        },
        "evidence_scope": "COPRESENCE_114_RECORD_REOPEN_PLUS_BOUNDARY_9_OF_9",
        "final_pass": "HOLD_USER_REVIEW_OF_RECORD_REPLAY_EVIDENCE",
        "global_29_lane_e5": "HOLD_28_JUDGMENT_TO_SENTENCE_LANES_UNTESTED",
        "inputs": {
            "audit_sidecar_sha256": sha256_file(paths["v9_audit_sidecar"]),
            "calibration_independent_ledger_sha256": sha256_file(paths["second_action_independent_ledger"]),
            "calibration_independent_report_sha256": sha256_file(paths["second_action_independent_report"]),
            "calibration_manifest_sha256": sha256_file(paths["second_action_calibration"] / "router_run_manifest.json"),
            "router_sha256": sha256_file(paths["v10_router"]),
            "source_registry_sha256": sha256_file(paths["v10_source_registry"] / "manifest.json"),
            "v9_baseline_tree_sha256": before["v9_baseline"]["tree_sha256"],
            "v9_e5_manifest_sha256": sha256_file(args.v9_e5_manifest.resolve()),
            "v9_e6_manifest_sha256": sha256_file(args.v9_e6_manifest.resolve()),
        },
        "overlay": "ADD_TO_V9_DO_NOT_OVERWRITE",
        "protected_input_change_count": 0,
        "real_long_drift": "HOLD_REAL_LONG_DRIFT_NOT_PROVEN",
        "run_id": "",
        "schema_version": SCHEMA_VERSION,
        "second_restore": "EVIDENCE_REVIEW",
        "status": "PASS_REOPEN_EVIDENCE_9_OF_9",
        "v10": "EXPECTED_VALUE_BOUND",
        "v9_history": {
            "e5_original_status": v9_e5_manifest.get("e5_status"),
            "e5_v10_reclassification": audit["e5"]["v10_authoritative_status"],
            "e6_original_status": v9_e6_manifest.get("e6_status"),
            "e6_v10_reclassification": audit["e6"]["v10_authoritative_status"],
            "preservation": "BYTE_PRESERVED_HISTORY_NOT_CURRENT_AUTHORITY",
        },
        "validator": {
            "producer_import_forbidden": True,
            "report_path": "references/v10_runtime/e6_independent_validation.json",
            "required_schema": "KANI_V10_E6_INDEPENDENT_VALIDATION_V1",
        },
    }
    manifest["run_id"] = sha256_bytes(compact_json({**manifest, "run_id": None}))
    write_exclusive(out_dir / "e6_manifest.json", canonical_json(manifest))
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

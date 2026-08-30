#!/usr/bin/env python3
"""Independently validate a KANI V10 E6 execution-evidence overlay.

The validator does not import the E6 producer.  It reparses the VAS27 source
and oracle with a line-oriented implementation, rerenders all 114 sentences,
recomputes the nine boundary tests, and reads every protected V9/E5 input back.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
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

E6_SCHEMA = "KANI_V10_E6_REOPEN_OVERLAY_V1"
REPORT_SCHEMA = "KANI_V10_E6_INDEPENDENT_VALIDATION_V1"
REPLAY_SCHEMA = "KANI_V10_E6_REPLAY_RECORD_V1"
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
REQUIRED_E6_FILES = {
    "boundary_test_9of9.json",
    "e6_manifest.json",
    "e6_reopen_record.json",
    "e6_replay_ledger.jsonl",
    "e6_transcript.txt",
}


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
        raise ValueError(f"object required: {path}")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("rb") as stream:
        for number, raw_line in enumerate(stream, start=1):
            if not raw_line.endswith(b"\n") or not raw_line.strip():
                raise ValueError(f"invalid JSONL framing: {path}:{number}")
            value = json.loads(raw_line.decode("utf-8"))
            if not isinstance(value, dict):
                raise ValueError(f"JSONL object required: {path}:{number}")
            rows.append(value)
    return rows


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return str(resolved)


def tree_snapshot(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise ValueError(f"symlink protected path: {path}")
    if path.is_file():
        return {"kind": "file", **metadata(path)}
    if not path.is_dir():
        raise ValueError(f"protected path missing: {path}")
    files: dict[str, dict[str, Any]] = {}
    for member in sorted(path.rglob("*")):
        if member.is_symlink():
            raise ValueError(f"symlink in protected tree: {member}")
        if member.is_file():
            files[member.relative_to(path).as_posix()] = metadata(member)
    return {
        "files": files,
        "kind": "directory",
        "tree_sha256": sha256_bytes(compact_json(files)),
    }


def producer_function_location(function_name: str) -> str:
    producer = ROOT / "scripts" / "run_kani_v10_e6.py"
    syntax = ast.parse(producer.read_text(encoding="utf-8"), filename=str(producer))
    matches = [
        node for node in syntax.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name
    ]
    if len(matches) != 1 or matches[0].end_lineno is None:
        raise ValueError(f"producer function location: {function_name}")
    node = matches[0]
    return f"scripts/run_kani_v10_e6.py:{node.lineno}-{node.end_lineno}::{function_name}"


def normalize_actor(label: str) -> str:
    if label.startswith("Muntha"):
        return "Muntha (Mu)"
    result = re.sub(r"\([^)]*\)", "", label).strip()
    return result + (" (R)" if "(R)" in label else "")


def degree_tuple(value: str) -> tuple[int, int, int]:
    parts = value.split(":")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise ValueError(f"degree grammar: {value}")
    result = tuple(int(part) for part in parts)
    if result[0] > 29 or result[1] > 59 or result[2] > 59:
        raise ValueError(f"degree range: {value}")
    return result  # type: ignore[return-value]


def independent_render(
    router: dict[str, Any], dchart: str, view: str, location: str,
    members: str, degree_order: str | None, selected_route: str,
) -> str:
    route_views = [
        route_view for route_view, route in router["judgment_routes"].items()
        if route["selected_route"] == selected_route
    ]
    if route_views != [view]:
        raise ValueError("selected judgment route does not dispatch the requested view")
    d_rule = router["dchart_rules"][dchart]
    reality = d_rule[f"{view.lower()}_reality_rule"] if dchart == "D1" else d_rule["reality_rule"]
    slots = {
        "DCHART": dchart,
        "DEGREE_ORDER": degree_order if degree_order is not None else "NOT_APPLICABLE",
        "LOCATION": location,
        "MEMBERS_PLUS": members.replace(" / ", " + "),
        "REALITY_RULE": reality,
        "ROLE": d_rule["role"],
        "YEAR": router["dataset_contract"]["year"],
    }
    return router["sentence_templates"][route_views[0]].format(**slots)


def line_topology(
    source_path: Path, router: dict[str, Any],
) -> tuple[dict[tuple[str, str, str], dict[str, Any]], dict[str, int]]:
    raw = source_path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or b"\x00" in raw or not raw.endswith(b"\n"):
        raise ValueError("source canonical-byte boundary")
    lines = raw.decode("utf-8").splitlines()
    marker_re = re.compile(r"^\[(D[0-9]+) (RASHI|BHAVA) SOURCE\]$")
    markers = [(index, marker_re.fullmatch(line)) for index, line in enumerate(lines)]
    markers = [(index, match) for index, match in markers if match is not None]
    expected = [(dchart, view) for dchart in SOURCE_DCHART_ORDER for view in ("RASHI", "BHAVA")]
    if [(match.group(1), match.group(2)) for _, match in markers] != expected:
        raise ValueError("source wrapper order")
    code_map = router["actor_normalization"]["bhava_codes"]
    code_re = re.compile("|".join(re.escape(code) for code in sorted(code_map, key=len, reverse=True)))
    result: dict[tuple[str, str, str], dict[str, Any]] = {}
    singles = 0
    for ordinal, (marker_index, marker) in enumerate(markers):
        next_index = markers[ordinal + 1][0] if ordinal + 1 < len(markers) else len(lines)
        block = lines[marker_index + 1:next_index]
        dchart, view = marker.group(1), marker.group(2)
        family_selected = "D1_ROOT" if dchart == "D1" else "TARGET_DCHART"
        family_rejected = "TARGET_DCHART" if dchart == "D1" else "D1_ROOT_SINGLE_GRAMMAR"
        candidates: list[tuple[str, list[dict[str, Any]], str | None]] = []
        if view == "RASHI":
            headings = [index for index, line in enumerate(block) if line.startswith("Visible Planetary Positions")]
            if len(headings) != 1:
                raise ValueError(f"Rashi heading {dchart}")
            stop = next(
                (index for index in range(headings[0] + 1, len(block))
                 if block[index].startswith("Visible Vimshottari Mudda Dasha") or block[index] == "Lock Status"),
                None,
            )
            if stop is None:
                raise ValueError(f"Rashi stop {dchart}")
            row_re = re.compile(r"^- (.+?) — Degree ([^/]+) / Rashi ([^/]+) /")
            groups: dict[str, list[dict[str, Any]]] = {}
            parsed_rows = 0
            for local_index in range(headings[0] + 1, stop):
                match = row_re.match(block[local_index])
                if match is None:
                    continue
                parsed_rows += 1
                degree = match.group(2).strip()
                sign = match.group(3).strip()
                if degree == "not shown" and sign == "not shown":
                    continue
                degree_tuple(degree)
                groups.setdefault(sign, []).append({
                    "actor": normalize_actor(match.group(1)),
                    "degree": degree,
                    "line": marker_index + local_index + 2,
                    "raw": block[local_index],
                })
            if parsed_rows != 14:
                raise ValueError(f"Rashi actor rows {dchart}")
            for location, member_rows in groups.items():
                if len(member_rows) == 1:
                    singles += 1
                    continue
                if len(member_rows) > 1:
                    ordered = sorted(member_rows, key=lambda item: degree_tuple(item["degree"]))
                    candidates.append((location, ordered, " → ".join(
                        f"{item['actor']} {item['degree']}" for item in ordered
                    )))
        else:
            headings = [index for index, line in enumerate(block) if line == "Visible Bhava Snapshot"]
            if len(headings) != 1:
                raise ValueError(f"Bhava heading {dchart}")
            stop = next(
                (index for index in range(headings[0] + 1, len(block)) if block[index].startswith("- Wheel Readability")),
                None,
            )
            if stop is None:
                raise ValueError(f"Bhava stop {dchart}")
            row_re = re.compile(r"^- (.+? Sector) = (.+)$")
            for local_index in range(headings[0] + 1, stop):
                match = row_re.match(block[local_index])
                if match is None or match.group(2).startswith("empty"):
                    continue
                codes = code_re.findall(match.group(2))
                if len(codes) == 1:
                    singles += 1
                    continue
                if len(codes) > 1:
                    candidates.append((match.group(1), [{
                        "actor": code_map[code],
                        "line": marker_index + local_index + 2,
                        "raw": block[local_index],
                    } for code in codes], None))
        for location, member_rows, degree_order in candidates:
            member_display = " / ".join(
                f"{item['actor']} {item['degree']}" if "degree" in item else item["actor"]
                for item in member_rows
            )
            key = (dchart, view, location)
            if key in result:
                raise ValueError(f"duplicate source route {key}")
            line_locations = (
                [{"actor": item["actor"], "line": item["line"], "raw": item["raw"]} for item in member_rows]
                if view == "RASHI" else
                [{"line": member_rows[0]["line"], "raw": member_rows[0]["raw"], "visible_sector": location}]
            )
            result[key] = {
                "degree_order": degree_order,
                "family_rejected_route": family_rejected,
                "family_selected_route": family_selected,
                "member_count": len(member_rows),
                "member_display": member_display,
                "sentence": independent_render(
                    router, dchart, view, location, member_display, degree_order,
                    router["judgment_routes"][view]["selected_route"],
                ),
                "source_line_locations": line_locations,
                "source_wrapper_line_end": next_index,
                "source_wrapper_line_start": marker_index + 1,
            }
    counts = {
        "bhava_records": sum(key[1] == "BHAVA" for key in result),
        "rashi_records": sum(key[1] == "RASHI" for key in result),
        "single_fields_excluded": singles,
        "source_blocks": len(markers),
        "total_records": len(result),
    }
    return result, counts


def line_oracle(path: Path) -> dict[tuple[str, str, str], dict[str, Any]]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or b"\x00" in raw:
        raise ValueError("oracle canonical-byte boundary")
    lines = raw.decode("utf-8").splitlines()
    header_re = re.compile(r"^\[(HYEWON_2027_VAS_(D[0-9]+)_(RASHI|BHAVA)_[^\]]+_CO_FIELD)\]$")
    headers = [(index, header_re.fullmatch(line)) for index, line in enumerate(lines)]
    headers = [(index, match) for index, match in headers if match is not None]
    if len(headers) != 114:
        raise ValueError("oracle block count")
    result: dict[tuple[str, str, str], dict[str, Any]] = {}
    for ordinal, (header_index, header) in enumerate(headers):
        next_index = headers[ordinal + 1][0] if ordinal + 1 < len(headers) else len(lines)
        block = lines[header_index:next_index]

        def field(label: str) -> tuple[str, int]:
            prefix = f"- {label} = "
            hits = [(index, line[len(prefix):]) for index, line in enumerate(block) if line.startswith(prefix)]
            if len(hits) != 1:
                raise ValueError(f"oracle field {header.group(1)}::{label}")
            return hits[0][1], header_index + hits[0][0] + 1

        location_value, _ = field("Location")
        members, members_line = field("Members")
        sentence, sentence_line = field("2.5차 관절문")
        location = location_value.split(" / ", 1)[1]
        key = (header.group(2), header.group(3), location)
        result[key] = {
            "block_id": header.group(1),
            "block_line_start": header_index + 1,
            "members": members,
            "members_line": members_line,
            "sentence": sentence,
            "sentence_line": sentence_line,
        }
    return result


def make_test(test_id: str, passed: bool, expected: Any, observed: Any, evidence: list[str]) -> dict[str, Any]:
    return {
        "evidence": evidence,
        "expected": expected,
        "observed": observed,
        "status": "PASS" if passed else "FAIL",
        "test_id": test_id,
    }


def independent_boundary_rows(
    e5_rows: list[dict[str, Any]], topology: dict[tuple[str, str, str], dict[str, Any]],
    topology_counts: dict[str, int], calibration_rows: list[dict[str, Any]], calibration_report: dict[str, Any],
) -> list[dict[str, Any]]:
    d1 = [row for row in e5_rows if row["dataset"]["dchart"] == "D1"]
    non_d1 = [row for row in e5_rows if row["dataset"]["dchart"] != "D1"]
    d60 = [row for row in e5_rows if row["dataset"]["dchart"] == "D60"]
    rashi = [row for row in e5_rows if row["dataset"]["view"] == "RASHI"]
    bhava = [row for row in e5_rows if row["dataset"]["view"] == "BHAVA"]
    route_keys = {(row["dataset"]["dchart"], row["dataset"]["view"], row["dataset"]["location"]) for row in e5_rows}
    field_ok = all(
        "OCCUPANT_FIELD" in row.get("slot_bindings", {})
        and "HOUSE_LORD_FIELD" in row.get("slot_bindings", {})
        and row.get("boundary_test", {}).get("field_objects_distinct") is True
        and row.get("boundary_test", {}).get("house_lord_appended_to_occupants") is False
        for row in calibration_rows
    )
    golden = next((row for row in calibration_rows if row.get("record_id") == "KANI-V10-D6-H05"), {})
    rashi_order_ok = all(
        row["judgment_route"]["degree_policy"] == "ASCENDING_VISIBLE_DEGREE_WITHIN_SAME_SIGN"
        and " → ".join(row["dataset"]["member_display"].split(" / ")) in row["output"]["pikachu_sentence"]
        for row in rashi
    )
    bhava_order_ok = all(
        row["judgment_route"]["degree_policy"] == "NOT_APPLIED_VISIBLE_SNAPSHOT_ONLY"
        and " → " not in row["output"]["pikachu_sentence"]
        for row in bhava
    )
    return [
        make_test(
            BOUNDARY_TESTS[0], bool(d1) and all(
                row["dataset"]["family_selected_route"] == "D1_ROOT"
                and row["dataset"]["family_rejected_route"] == "TARGET_DCHART" for row in d1
            ),
            "ALL_D1_RECORDS_SELECT_D1_ROOT_REJECT_TARGET_DCHART",
            {"records": len(d1), "selected": "D1_ROOT", "rejected": "TARGET_DCHART"},
            [row["record_id"] for row in d1],
        ),
        make_test(
            BOUNDARY_TESTS[1], bool(non_d1) and all(
                row["dataset"]["family_selected_route"] == "TARGET_DCHART"
                and row["dataset"]["family_rejected_route"] == "D1_ROOT_SINGLE_GRAMMAR" for row in non_d1
            ),
            "ALL_NON_D1_RECORDS_SELECT_TARGET_DCHART_REJECT_D1_ROOT_SINGLE_GRAMMAR",
            {"records": len(non_d1), "selected": "TARGET_DCHART", "rejected": "D1_ROOT_SINGLE_GRAMMAR"},
            [row["record_id"] for row in e5_rows if row["dataset"]["dchart"] == "D9"],
        ),
        make_test(
            BOUNDARY_TESTS[2], bool(d60) and all(row["dataset"]["family_selected_route"] == "TARGET_DCHART" for row in d60),
            "D60_RETAINS_TARGET_DCHART_BOUNDARY", {"records": len(d60), "selected": "TARGET_DCHART"},
            [row["record_id"] for row in d60],
        ),
        make_test(
            BOUNDARY_TESTS[3], len(rashi) == 64 and len(bhava) == 50 and len(route_keys) == 114
            and all(row["judgment_route"]["selected_route"].startswith("RASHI_") for row in rashi)
            and all(row["judgment_route"]["selected_route"].startswith("BHAVA_") for row in bhava),
            "64_RASHI_PLUS_50_BHAVA_DISTINCT_ROUTE_KEYS_NO_VIEW_OVERWRITE",
            {"bhava_records": len(bhava), "rashi_records": len(rashi), "unique_route_keys": len(route_keys)},
            ["e5_decision_ledger.jsonl#dataset.view", "e5_decision_ledger.jsonl#judgment_route"],
        ),
        make_test(
            BOUNDARY_TESTS[4], len(calibration_rows) == 240 and field_ok and calibration_report.get("status") == "PASS",
            "240_CALIBRATION_RECORDS_KEEP_OCCUPANT_AND_HOUSE_LORD_AS_DISTINCT_FIELDS",
            {"independent_report": calibration_report.get("status"), "records": len(calibration_rows)},
            ["references/v10_runtime/router_run/router_records.jsonl", "references/v10_runtime/independent_router_report.json"],
        ),
        make_test(
            BOUNDARY_TESTS[5],
            golden.get("slot_bindings", {}).get("OCCUPANT_FIELD") == "EMPTY"
            and golden.get("slot_bindings", {}).get("HOUSE_LORD_FIELD") == "Mars"
            and golden.get("route", {}).get("selected_route") == "HOUSE_LORD_ROUTE"
            and golden.get("route", {}).get("rejected_route") == "OCCUPANT_ROUTE"
            and golden.get("source", {}).get("file_sha256") == "50353b4a608b383026f7158f7fe915efc5cdb2e1a04747cc1ee90d9b78479e35"
            and calibration_report.get("golden_D6_H05") == "PASS",
            "D6_H05_EMPTY_SELECTS_HOUSE_LORD_MARS_AND_REJECTS_OCCUPANT_ROUTE",
            {
                "house_lord": golden.get("slot_bindings", {}).get("HOUSE_LORD_FIELD"),
                "occupants": golden.get("slot_bindings", {}).get("OCCUPANT_FIELD"),
                "rejected": golden.get("route", {}).get("rejected_route"),
                "selected": golden.get("route", {}).get("selected_route"),
            },
            ["KANI-V10-D6-H05", "references/v10_runtime/independent_router_report.json#golden_D6_H05"],
        ),
        make_test(
            BOUNDARY_TESTS[6], rashi_order_ok and bhava_order_ok,
            "RASHI_ASCENDING_VISIBLE_DEGREES__BHAVA_VISIBLE_ORDER_WITHOUT_DEGREE_INFERENCE",
            {"bhava_no_degree_order": len(bhava) if bhava_order_ok else 0, "rashi_degree_order": len(rashi) if rashi_order_ok else 0},
            ["e5_decision_ledger.jsonl#dataset.member_display", "e5_decision_ledger.jsonl#judgment_route.degree_policy"],
        ),
        make_test(
            BOUNDARY_TESTS[7], topology_counts.get("single_fields_excluded") == 165
            and len(topology) == 114 and all(item["member_count"] >= 2 for item in topology.values()),
            "165_SINGLE_FIELDS_EXCLUDED_AND_ZERO_SINGLETON_COPRESENCE_RECORDS",
            {"copresence_records": len(topology), "single_fields_excluded": topology_counts.get("single_fields_excluded")},
            [f"{SOURCE_FILENAME}#40_SOURCE_WRAPPERS", "e5_manifest.json#counts.single_fields_excluded"],
        ),
        make_test(
            BOUNDARY_TESTS[8], len(e5_rows) == 114 and all(
                row["reinput_result"].get("status") == "PASS_EXACT_PIKACHU_SENTENCE_REPLAY"
                and row["output"].get("pikachu_sentence_sha256") == row["expected"].get("sentence_sha256")
                for row in e5_rows
            ),
            "114_OF_114_DATASET_TO_JUDGMENT_ROUTE_TO_PIKACHU_SENTENCE_EXACT_REPLAY",
            {"exact_replay": sum(
                row["output"].get("pikachu_sentence_sha256") == row["expected"].get("sentence_sha256")
                for row in e5_rows
            ), "records": len(e5_rows)},
            ["e6_replay_ledger.jsonl", f"{EXPECTED_FILENAME}#114_CO_FIELD_2.5_STAGE_SENTENCES"],
        ),
    ]


def expected_transcript() -> bytes:
    return (
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


def validate(args: argparse.Namespace) -> dict[str, Any]:
    failures: list[str] = []
    manifest: dict[str, Any] = {}

    def check(condition: bool, code: str) -> None:
        if not condition:
            failures.append(code)

    e6_dir = args.e6_dir.resolve()
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
    replay_rows: list[dict[str, Any]] = []
    topology: dict[tuple[str, str, str], dict[str, Any]] = {}
    topology_counts: dict[str, int] = {}
    try:
        actual_files = {path.name for path in e6_dir.iterdir() if path.is_file()}
        check(actual_files == REQUIRED_E6_FILES, "e6_file_set")
        manifest = read_object(e6_dir / "e6_manifest.json")
        boundary = read_object(e6_dir / "boundary_test_9of9.json")
        reopen = read_object(e6_dir / "e6_reopen_record.json")
        replay_rows = read_jsonl(e6_dir / "e6_replay_ledger.jsonl")

        check(manifest.get("schema_version") == E6_SCHEMA, "manifest_schema")
        check(manifest.get("status") == "PASS_REOPEN_EVIDENCE_9_OF_9", "manifest_status")
        check(manifest.get("second_restore") == "EVIDENCE_REVIEW", "second_restore_state")
        check(manifest.get("v10") == "EXPECTED_VALUE_BOUND", "v10_state")
        check(manifest.get("final_pass") == "HOLD_USER_REVIEW_OF_RECORD_REPLAY_EVIDENCE", "final_pass_firewall")
        check(manifest.get("global_29_lane_e5") == "HOLD_28_JUDGMENT_TO_SENTENCE_LANES_UNTESTED", "global_lane_hold")
        check(manifest.get("real_long_drift") == "HOLD_REAL_LONG_DRIFT_NOT_PROVEN", "real_long_drift_hold")
        check(manifest.get("overlay") == "ADD_TO_V9_DO_NOT_OVERWRITE", "overlay_boundary")
        check(manifest.get("protected_input_change_count") == 0, "protected_change_count")
        check(manifest.get("boundary_test") == {"pass_count": 9, "status": "PASS_9_OF_9", "test_count": 9}, "manifest_boundary_summary")
        check(manifest.get("counts") == {
            "bhava_replay_records": 50,
            "copresence_replay_records": 114,
            "rashi_replay_records": 64,
            "second_action_calibration_records": 240,
            "single_fields_excluded": 165,
        }, "manifest_counts")
        check(manifest.get("validator") == {
            "producer_import_forbidden": True,
            "report_path": "references/v10_runtime/e6_independent_validation.json",
            "required_schema": REPORT_SCHEMA,
        }, "manifest_validator_contract")
        check(manifest.get("run_id") == sha256_bytes(compact_json({**manifest, "run_id": None})), "manifest_run_id")

        artifact_expected = manifest.get("artifacts", {})
        check(set(artifact_expected) == REQUIRED_E6_FILES - {"e6_manifest.json"}, "manifest_artifact_set")
        for filename in sorted(REQUIRED_E6_FILES - {"e6_manifest.json"}):
            observed = metadata(e6_dir / filename)
            declared = artifact_expected.get(filename, {})
            expected_meta = {"bytes": observed["bytes"], "sha256": observed["sha256"]}
            if filename == "e6_replay_ledger.jsonl":
                expected_meta["records"] = len(replay_rows)
            check(declared == expected_meta, f"artifact_binding:{filename}")

        router = read_object(paths["v10_router"])
        check(router.get("boundary_tests") == list(BOUNDARY_TESTS), "router_boundary_contract")
        topology, topology_counts = line_topology(paths["v10_source_registry"] / SOURCE_FILENAME, router)
        oracle = line_oracle(paths["v10_source_registry"] / EXPECTED_FILENAME)
        check(topology_counts == {
            "bhava_records": 50, "rashi_records": 64, "single_fields_excluded": 165,
            "source_blocks": 40, "total_records": 114,
        }, "live_source_topology")
        check(set(topology) == set(oracle), "source_oracle_key_set")

        e5_manifest = read_object(paths["e5_overlay"] / "e5_manifest.json")
        e5_path = paths["e5_overlay"] / "e5_decision_ledger.jsonl"
        e5_rows = read_jsonl(e5_path)
        check(e5_manifest.get("schema_version") == "KANI_V10_E5_EXECUTION_OVERLAY_V1", "e5_schema")
        check(e5_manifest.get("status") == "PASS_EXECUTION_EVIDENCE_114_OF_114", "e5_status")
        check(e5_manifest.get("artifacts", {}).get("e5_decision_ledger.jsonl") == {
            "bytes": e5_path.stat().st_size, "records": len(e5_rows), "sha256": sha256_file(e5_path),
        }, "e5_ledger_binding")
        check(len(e5_rows) == 114, "e5_record_count")
        check(e5_manifest.get("router", {}).get("sha256") == sha256_file(paths["v10_router"]), "e5_router_hash")
        expected_file_hash = sha256_file(paths["v10_source_registry"] / EXPECTED_FILENAME)
        source_file_hash = sha256_file(paths["v10_source_registry"] / SOURCE_FILENAME)
        expected_replay_rows: list[dict[str, Any]] = []
        expected_e6_code_location = producer_function_location("build_replay_row")
        seen_keys: set[tuple[str, str, str]] = set()
        for ordinal, (e5_row, e6_row) in enumerate(zip(e5_rows, replay_rows), start=1):
            e5_id = f"V10-E5-VAS27-{ordinal:04d}"
            e6_id = f"V10-E6-REOPEN-{ordinal:04d}"
            dataset = e5_row.get("dataset", {})
            key = (dataset.get("dchart"), dataset.get("view"), dataset.get("location"))
            check(e5_row.get("record_id") == e5_id, f"e5_identity:{ordinal}")
            check(key in topology and key not in seen_keys, f"e5_route_key:{ordinal}")
            seen_keys.add(key)
            if key not in topology or key not in oracle:
                continue
            derived, expected = topology[key], oracle[key]
            route = router["judgment_routes"][key[1]]
            expected_dataset = {
                "dchart": key[0],
                "family_rejected_route": derived["family_rejected_route"],
                "family_selected_route": derived["family_selected_route"],
                "location": key[2],
                "member_display": derived["member_display"],
                "source_file": SOURCE_FILENAME,
                "source_file_sha256": source_file_hash,
                "source_line_locations": derived["source_line_locations"],
                "source_wrapper_line_end": derived["source_wrapper_line_end"],
                "source_wrapper_line_start": derived["source_wrapper_line_start"],
                "view": key[1],
                "year": 2027,
            }
            check(dataset == expected_dataset, f"e5_dataset:{e5_id}")
            check(e5_row.get("judgment_route") == route, f"e5_route:{e5_id}")
            sentence = derived["sentence"]
            check(e5_row.get("output") == {
                "pikachu_sentence": sentence,
                "pikachu_sentence_sha256": sha256_bytes(sentence.encode("utf-8")),
                "sentence_function": "VAS_CO2_99_2_5_STAGE_JOINT_SENTENCE",
            }, f"e5_output:{e5_id}")
            check(sentence == expected["sentence"] and derived["member_display"] == expected["members"], f"e5_live_oracle:{e5_id}")
            check(e5_row.get("expected") == {
                "block_id": expected["block_id"],
                "block_line_start": expected["block_line_start"],
                "file": EXPECTED_FILENAME,
                "file_sha256": expected_file_hash,
                "members_line": expected["members_line"],
                "sentence_line": expected["sentence_line"],
                "sentence_sha256": sha256_bytes(expected["sentence"].encode("utf-8")),
            }, f"e5_expected:{e5_id}")
            expected_handoff = router["handoff"]["target_pattern"].format(DCHART=key[0], VIEW=key[1], LOCATION=key[2])
            check(e5_row.get("handoff_target") == expected_handoff, f"e5_handoff:{e5_id}")
            check(e5_row.get("reinput_result") == {
                "dataset_rendered_before_oracle_open": True,
                "expected_members_exact": True,
                "expected_sentence_exact": True,
                "status": "PASS_EXACT_PIKACHU_SENTENCE_REPLAY",
            }, f"e5_reinput:{e5_id}")
            why = {
                **router["why_correction_qa"],
                "record_answer": (
                    f"{key[1]} {key[2]}에서 {route['why_selected']}를 충족하여 "
                    f"{route['selected_route']}를 선택하고 {route['rejected_route']}를 기각했다."
                ),
            }
            check(e5_row.get("why_revision_qa") == why, f"e5_why:{e5_id}")
            check(e5_row.get("schema_version") == "KANI_V10_E5_DECISION_RECORD_V1" and e5_row.get("status") == "PASS_EXECUTION_EVIDENCE", f"e5_record_state:{e5_id}")

            e6_code = e6_row.get("code_location", {}).get("e6_reopen")
            check(e6_code == expected_e6_code_location, f"e6_code_location:{e6_id}")
            expected_replay_rows.append({
                "code_location": {
                    "e5_render_and_route": e5_row.get("code_location"),
                    "e6_reopen": e6_code,
                },
                "dataset_to_judgment_route_to_pikachu_sentence": {
                    "dataset": {
                        "dchart": key[0], "location": key[2], "member_display": derived["member_display"],
                        "view": key[1], "year": 2027,
                    },
                    "judgment_route": route,
                    "pikachu_sentence": sentence,
                },
                "e5_record_id": e5_id,
                "e5_record_sha256": sha256_bytes(compact_json(e5_row)),
                "expected_location": {
                    "block_id": expected["block_id"], "block_line_start": expected["block_line_start"],
                    "members_line": expected["members_line"], "sentence_line": expected["sentence_line"],
                },
                "handoff_target": expected_handoff,
                "record_id": e6_id,
                "reinput_result": {
                    "e5_status": "PASS_EXACT_PIKACHU_SENTENCE_REPLAY",
                    "expected_sentence_hash_readback": sha256_bytes(expected["sentence"].encode("utf-8")),
                    "rendered_sentence_hash_readback": sha256_bytes(sentence.encode("utf-8")),
                    "status": "PASS_REOPEN_EXACT_DATASET_JUDGMENT_SENTENCE",
                },
                "rejected_route": route["rejected_route"],
                "schema_version": REPLAY_SCHEMA,
                "selected_route": route["selected_route"],
                "source_location": {
                    "file": SOURCE_FILENAME, "file_sha256": source_file_hash,
                    "line_locations": derived["source_line_locations"],
                    "wrapper_line_end": derived["source_wrapper_line_end"],
                    "wrapper_line_start": derived["source_wrapper_line_start"],
                },
                "status": "PASS_REOPEN_EXACT_RECORD",
                "why_revision_qa": why,
            })
        check(len(replay_rows) == 114 and len(expected_replay_rows) == 114, "e6_replay_count")
        check(replay_rows == expected_replay_rows, "e6_replay_exact_reconstruction")

        calibration_manifest = read_object(paths["second_action_calibration"] / "router_run_manifest.json")
        calibration_rows = read_jsonl(paths["second_action_calibration"] / "router_records.jsonl")
        calibration_report = read_object(paths["second_action_independent_report"])
        calibration_independent = read_jsonl(paths["second_action_independent_ledger"])
        check(calibration_manifest.get("status") == "PASS_TESTED_SCOPE_240", "calibration_status")
        check(calibration_manifest.get("records") == {
            "bytes": (paths["second_action_calibration"] / "router_records.jsonl").stat().st_size,
            "path": "router_records.jsonl",
            "sha256": sha256_file(paths["second_action_calibration"] / "router_records.jsonl"),
        }, "calibration_record_binding")
        check(calibration_report.get("status") == "PASS" and calibration_report.get("producer_imported") is False, "calibration_independence")
        check(calibration_report.get("independent_ledger") == {
            "bytes": paths["second_action_independent_ledger"].stat().st_size,
            "records": len(calibration_independent),
            "sha256": sha256_file(paths["second_action_independent_ledger"]),
        }, "calibration_independent_ledger")
        check(len(calibration_rows) == len(calibration_independent) == 240, "calibration_count")

        expected_tests = independent_boundary_rows(e5_rows, topology, topology_counts, calibration_rows, calibration_report)
        expected_boundary = {
            "pass_count": 9,
            "schema_version": E6_SCHEMA,
            "status": "PASS_9_OF_9",
            "test_count": 9,
            "tests": expected_tests,
        }
        check(boundary == expected_boundary, "boundary_exact_reconstruction")
        check([row["test_id"] for row in expected_tests] == list(BOUNDARY_TESTS), "boundary_order")
        check(all(row["status"] == "PASS" for row in expected_tests), "boundary_9_of_9")

        snapshots = {name: tree_snapshot(path) for name, path in paths.items()}
        protected_expected = {
            name: {
                "after": snapshots[name], "before": snapshots[name], "path": display_path(paths[name]), "unchanged": True,
            }
            for name in sorted(paths)
        }
        check(reopen == {
            "changed_protected_inputs": [],
            "execution_counters": {
                "e5_write_count": 0, "github_read_count": 0, "lower_stage_rebuild_count": 0,
                "other_remote_read_count": 0, "v9_write_count": 0,
            },
            "protected_inputs": protected_expected,
            "schema_version": E6_SCHEMA,
            "status": "PASS_READ_ONLY_REOPEN",
        }, "protected_reopen_exact_readback")
        check((e6_dir / "e6_transcript.txt").read_bytes() == expected_transcript(), "transcript_exact")

        audit = read_object(paths["v9_audit_sidecar"])
        v9_e5 = read_object(args.v9_e5_manifest.resolve())
        v9_e6 = read_object(args.v9_e6_manifest.resolve())
        check(audit.get("e5", {}).get("artifact_sha256") == sha256_file(args.v9_e5_manifest.resolve()), "audit_v9_e5_hash")
        check(audit.get("e6", {}).get("artifact_sha256") == sha256_file(args.v9_e6_manifest.resolve()), "audit_v9_e6_hash")
        expected_inputs = {
            "audit_sidecar_sha256": sha256_file(paths["v9_audit_sidecar"]),
            "calibration_independent_ledger_sha256": sha256_file(paths["second_action_independent_ledger"]),
            "calibration_independent_report_sha256": sha256_file(paths["second_action_independent_report"]),
            "calibration_manifest_sha256": sha256_file(paths["second_action_calibration"] / "router_run_manifest.json"),
            "router_sha256": sha256_file(paths["v10_router"]),
            "source_registry_sha256": sha256_file(paths["v10_source_registry"] / "manifest.json"),
            "v9_baseline_tree_sha256": snapshots["v9_baseline"]["tree_sha256"],
            "v9_e5_manifest_sha256": sha256_file(args.v9_e5_manifest.resolve()),
            "v9_e6_manifest_sha256": sha256_file(args.v9_e6_manifest.resolve()),
        }
        check(manifest.get("inputs") == expected_inputs, "manifest_input_hashes")
        check(manifest.get("entry_condition") == {
            "e5_manifest_sha256": sha256_file(paths["e5_overlay"] / "e5_manifest.json"),
            "e5_run_id": e5_manifest.get("run_id"),
            "e5_status": e5_manifest.get("status"),
            "observed": "PASS_TESTED_COPRESENCE_EXECUTION_SCOPE",
            "required": "V10_E5_EXECUTION_EVIDENCE_114_OF_114",
        }, "manifest_entry_condition")
        check(manifest.get("v9_history") == {
            "e5_original_status": v9_e5.get("e5_status"),
            "e5_v10_reclassification": audit["e5"]["v10_authoritative_status"],
            "e6_original_status": v9_e6.get("e6_status"),
            "e6_v10_reclassification": audit["e6"]["v10_authoritative_status"],
            "preservation": "BYTE_PRESERVED_HISTORY_NOT_CURRENT_AUTHORITY",
        }, "manifest_v9_history")
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        failures.append(f"exception:{type(error).__name__}:{error}")

    return {
        "boundary_9of9_sha256": (
            sha256_file(e6_dir / "boundary_test_9of9.json")
            if (e6_dir / "boundary_test_9of9.json").is_file() else None
        ),
        "boundary_tests": {
            "pass_count": 9 if not failures else 0,
            "passed": 9 if not failures else 0,
            "test_count": 9,
            "total": 9,
        },
        "counts": {
            "bhava_replay_records": topology_counts.get("bhava_records", 0),
            "copresence_replay_records": len(replay_rows),
            "rashi_replay_records": topology_counts.get("rashi_records", 0),
            "single_fields_excluded": topology_counts.get("single_fields_excluded", 0),
        },
        "e6_manifest_sha256": sha256_file(e6_dir / "e6_manifest.json") if (e6_dir / "e6_manifest.json").is_file() else None,
        "errors": failures,
        "failures": failures,
        "final_pass": "HOLD_USER_REVIEW_OF_RECORD_REPLAY_EVIDENCE",
        "global_29_lane_e5": "HOLD_28_JUDGMENT_TO_SENTENCE_LANES_UNTESTED",
        "producer_imported": False,
        "real_long_drift": "HOLD_REAL_LONG_DRIFT_NOT_PROVEN",
        "schema_version": REPORT_SCHEMA,
        "second_restore": "EVIDENCE_REVIEW",
        "status": "PASS" if not failures else "FAIL",
        "v10": "EXPECTED_VALUE_BOUND",
        "validated_run_id": manifest.get("run_id"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("e6_dir", type=Path)
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
    parser.add_argument("--report", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    report = validate(args)
    report_bytes = canonical_json(report)
    if args.report is not None:
        output = args.report.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists() and not args.force:
            raise SystemExit(f"report already exists (use --force): {output}")
        mode = "wb" if args.force else "xb"
        with output.open(mode) as stream:
            stream.write(report_bytes)
    print(report_bytes.decode("utf-8"), end="")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

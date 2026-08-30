#!/usr/bin/env python3
"""Independently validate the KANI V10 E5 execution-evidence overlay.

This validator deliberately does not import ``run_kani_v10_e5``.  It derives
the 114 VAS27 routes and sentences from the plain Dataset first, records that
render hash, and only then opens the CO2_99 expected-output oracle.

Exit codes: 0=technical PASS, 1=REVISE (integrity or evidence mismatch).
The user-facing SECOND_RESTORE state remains EVIDENCE_REVIEW after a PASS.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_E5_DIR = ROOT / "references" / "v10_runs" / "run_20260830_vas27" / "e5"
DEFAULT_SOURCE_DIR = ROOT / "references" / "v10_sources" / "user_upload_20260830"
DEFAULT_ROUTER = ROOT / "references" / "DATASET_TO_PIKACHU_JUDGMENT_ROUTER_V10.json"
DEFAULT_V9_MANIFEST = ROOT / "references" / "v9_baseline" / "kani_v9_manifest.json"
DEFAULT_PRODUCER = ROOT / "scripts" / "run_kani_v10_e5.py"

REPORT_SCHEMA = "KANI_V10_E5_INDEPENDENT_VALIDATION_V1"
MANIFEST_SCHEMA = "KANI_V10_E5_EXECUTION_OVERLAY_V1"
RECORD_SCHEMA = "KANI_V10_E5_DECISION_RECORD_V1"
SOURCE_SCHEMA = "KANI_V10_USER_SOURCE_REGISTRY_V1"
SOURCE_FILENAME = "HYEWON_VAS27_D1-D60_♤.txt"
EXPECTED_FILENAME = "HEAWON_VAS27_CO2_99_♤.txt"
SOURCE_ORDER = (
    "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10",
    "D11", "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60",
)

# These hashes bind the validator to the exact user-upload registry, the V10
# route contract, and the immutable V9 baseline used for this evidence run.
TRUSTED_SOURCE_REGISTRY_SHA256 = "1f126816c5b339a2bcef8032509b9852b1cb5ccbfbdc5667944fb4289d1af7a3"
TRUSTED_ROUTER_SHA256 = "6fb9e2c7440efe5ef2457d66b982a7e28eec1bd2c35043d39fb3cb6eaaf8e156"
TRUSTED_V9_MANIFEST_SHA256 = "4f7a2a3137a50dcd083cdfc5ad7d12c91779da80c188d910266652007b1361d4"
TRUSTED_FILE_SHA256 = {
    "HYEWON_VAS25_D1-D60_♤.txt": "5973df92ea77b63cf16dc55136b91b6deeec4b591c9fc697b20df9a6bc3e0a76",
    "HEAWON_VAS25_CO2_99_♤.txt": "bf44a8a5759110fcb72aff74460b99ef7695dbdb2f2219a45eab3bd775bafc03",
    "HYEWON_VAS26_D1-D60_♤.txt": "3e716d8435801e77872697798ae45456b4533c110821c6c77b02003b6fa745ef",
    "HEAWON_VAS26_CO2_99_♤.txt": "d054834447e474598fbc2b626cb63c76ff41c8ebdcf21b3ea00bc01509a47d9c",
    SOURCE_FILENAME: "7cc9446f74d6130eec2c32e9ea723849d84a6a2070a1556d7954b69d06e0cddb",
    EXPECTED_FILENAME: "7e3a1bf370bbcbca2bffb826d79229a84183d98dc9181d1793dc7bb427d9e97f",
}
EXPECTED_COUNTS = {
    "bhava_records": 50,
    "rashi_records": 64,
    "single_fields_excluded": 165,
    "source_blocks": 40,
    "total_records": 114,
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


def read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def canonical_text(path: Path, *, require_final_lf: bool) -> tuple[bytes, str, list[str]]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"regular non-symlink file required: {path}")
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or b"\x00" in raw:
        raise ValueError(f"non-canonical UTF-8/LF source: {path}")
    if require_final_lf and not raw.endswith(b"\n"):
        raise ValueError(f"final LF required: {path}")
    text = raw.decode("utf-8")
    if unicodedata.normalize("NFC", text) != text:
        raise ValueError(f"non-NFC source: {path}")
    return raw, text, text.splitlines()


def normalize_actor_independently(label: str) -> str:
    if label.startswith("Muntha"):
        return "Muntha (Mu)"
    retrograde = "(R)" in label
    actor = re.sub(r"\([^)]*\)", "", label).strip()
    return f"{actor} (R)" if retrograde else actor


def degree_tuple(value: str) -> tuple[int, int, int]:
    parts = value.split(":")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise ValueError(f"invalid visible degree: {value!r}")
    degree, minute, second = (int(part) for part in parts)
    if degree > 29 or minute > 59 or second > 59:
        raise ValueError(f"out-of-range visible degree: {value!r}")
    return degree, minute, second


def render_independently(
    router: dict[str, Any], *, dchart: str, view: str, location: str,
    member_display: str, degree_order: str | None, selected_route: str,
) -> str:
    route_views = [
        route_view for route_view, route in router["judgment_routes"].items()
        if route["selected_route"] == selected_route
    ]
    if route_views != [view]:
        raise ValueError("selected judgment route does not dispatch the requested view")
    chart_rule = router["dchart_rules"][dchart]
    role = chart_rule["role"]
    if dchart == "D1":
        reality = chart_rule["rashi_reality_rule" if view == "RASHI" else "bhava_reality_rule"]
    else:
        reality = chart_rule["reality_rule"]
    bindings = {
        "DCHART": dchart,
        "DEGREE_ORDER": degree_order if degree_order is not None else "NOT_APPLICABLE",
        "LOCATION": location,
        "MEMBERS_PLUS": member_display.replace(" / ", " + "),
        "REALITY_RULE": reality,
        "ROLE": role,
        "YEAR": router["dataset_contract"]["year"],
    }
    return router["sentence_templates"][route_views[0]].format_map(bindings)


def derive_candidates_before_oracle(
    path: Path, router: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Parse only the plain VAS27 Dataset and independently render outputs."""
    raw, _, lines = canonical_text(path, require_final_lf=True)
    marker_re = re.compile(r"^\[(D[0-9]+) (RASHI|BHAVA) SOURCE\]$")
    markers = [
        (line_number, match.group(1), match.group(2))
        for line_number, line in enumerate(lines, start=1)
        if (match := marker_re.fullmatch(line)) is not None
    ]
    required = [
        (dchart, view) for dchart in SOURCE_ORDER for view in ("RASHI", "BHAVA")
    ]
    if [(dchart, view) for _, dchart, view in markers] != required:
        raise ValueError("VAS27 wrapper roster/order is not 20D x Rashi/Bhava")

    bhava_codes = router["actor_normalization"]["bhava_codes"]
    code_re = re.compile(
        "|".join(re.escape(code) for code in sorted(bhava_codes, key=len, reverse=True))
    )
    candidates: list[dict[str, Any]] = []
    single_fields = 0

    for index, (marker_line, dchart, view) in enumerate(markers):
        end_line = markers[index + 1][0] - 1 if index + 1 < len(markers) else len(lines)
        # Index pairs retain exact 1-based source coordinates.
        block = [(line_no, lines[line_no - 1]) for line_no in range(marker_line + 1, end_line + 1)]
        family_selected = "D1_ROOT" if dchart == "D1" else "TARGET_DCHART"
        family_rejected = "TARGET_DCHART" if dchart == "D1" else "D1_ROOT_SINGLE_GRAMMAR"

        if view == "RASHI":
            headings = [i for i, (_, line) in enumerate(block) if line.startswith("Visible Planetary Positions")]
            if len(headings) != 1:
                raise ValueError(f"{dchart} Rashi position heading cardinality")
            stop = next(
                (
                    i for i in range(headings[0] + 1, len(block))
                    if block[i][1].startswith("Visible Vimshottari Mudda Dasha")
                    or block[i][1] == "Lock Status"
                ),
                None,
            )
            if stop is None:
                raise ValueError(f"{dchart} Rashi position-table terminator missing")
            row_re = re.compile(r"^- (.+?) — Degree ([^/]+) / Rashi ([^/]+) /")
            groups: dict[str, list[dict[str, Any]]] = {}
            row_count = 0
            for line_no, line in block[headings[0] + 1:stop]:
                match = row_re.match(line)
                if match is None:
                    continue
                row_count += 1
                degree = match.group(2).strip()
                sign = match.group(3).strip()
                if degree == "not shown" and sign == "not shown":
                    continue
                degree_tuple(degree)
                groups.setdefault(sign, []).append({
                    "actor": normalize_actor_independently(match.group(1)),
                    "degree": degree,
                    "line": line_no,
                    "raw": line,
                })
            if row_count != 14:
                raise ValueError(f"{dchart} Rashi visible actor count is {row_count}, not 14")
            for location, members in groups.items():
                if len(members) < 2:
                    single_fields += 1
                    continue
                ordered = sorted(members, key=lambda row: degree_tuple(row["degree"]))
                member_display = " / ".join(
                    f"{row['actor']} {row['degree']}" for row in ordered
                )
                degree_order = " → ".join(
                    f"{row['actor']} {row['degree']}" for row in ordered
                )
                candidates.append({
                    "dchart": dchart,
                    "degree_order": degree_order,
                    "family_rejected_route": family_rejected,
                    "family_selected_route": family_selected,
                    "location": location,
                    "member_display": member_display,
                    "source_block_line_end": end_line,
                    "source_block_line_start": marker_line,
                    "source_line_locations": [
                        {"actor": row["actor"], "line": row["line"], "raw": row["raw"]}
                        for row in ordered
                    ],
                    "view": view,
                })
        else:
            headings = [i for i, (_, line) in enumerate(block) if line == "Visible Bhava Snapshot"]
            if len(headings) != 1:
                raise ValueError(f"{dchart} Bhava snapshot heading cardinality")
            stop = next(
                (
                    i for i in range(headings[0] + 1, len(block))
                    if block[i][1].startswith("- Wheel Readability")
                ),
                None,
            )
            if stop is None:
                raise ValueError(f"{dchart} Bhava snapshot terminator missing")
            row_re = re.compile(r"^- (.+? Sector) = (.+)$")
            for line_no, line in block[headings[0] + 1:stop]:
                match = row_re.fullmatch(line)
                if match is None:
                    continue
                location, value = match.groups()
                if value.startswith("empty"):
                    continue
                tokens = code_re.findall(value)
                if len(tokens) < 2:
                    single_fields += 1
                    continue
                member_display = " / ".join(bhava_codes[token] for token in tokens)
                candidates.append({
                    "dchart": dchart,
                    "degree_order": None,
                    "family_rejected_route": family_rejected,
                    "family_selected_route": family_selected,
                    "location": location,
                    "member_display": member_display,
                    "source_block_line_end": end_line,
                    "source_block_line_start": marker_line,
                    "source_line_locations": [{
                        "line": line_no,
                        "raw": line,
                        "visible_sector": location,
                    }],
                    "view": view,
                })

    for candidate in candidates:
        selected_route = router["judgment_routes"][candidate["view"]]["selected_route"]
        candidate["generated_sentence"] = render_independently(
            router,
            dchart=candidate["dchart"],
            view=candidate["view"],
            location=candidate["location"],
            member_display=candidate["member_display"],
            degree_order=candidate["degree_order"],
            selected_route=selected_route,
        )
        candidate["render_selected_route"] = selected_route
    counts = {
        "bhava_records": sum(row["view"] == "BHAVA" for row in candidates),
        "rashi_records": sum(row["view"] == "RASHI" for row in candidates),
        "single_fields_excluded": single_fields,
        "source_blocks": len(markers),
        "total_records": len(candidates),
    }
    corpus = b"".join(
        (candidate["generated_sentence"] + "\n").encode("utf-8")
        for candidate in candidates
    )
    return candidates, {
        "bytes": len(raw),
        "counts": counts,
        "rendered_before_oracle_sha256": sha256_bytes(corpus),
        "sha256": sha256_bytes(raw),
    }


def open_expected_oracle_after_render(
    path: Path,
) -> tuple[dict[tuple[str, str, str], dict[str, Any]], dict[str, Any]]:
    """Open the expected CO2 file only after independent rendering is complete."""
    raw, _, lines = canonical_text(path, require_final_lf=False)
    marker_re = re.compile(
        r"^\[(HYEWON_2027_VAS_(D[0-9]+)_(RASHI|BHAVA)_[^\]]+_CO_FIELD)\]$"
    )
    markers = [
        (line_number, match.group(1), match.group(2), match.group(3))
        for line_number, line in enumerate(lines, start=1)
        if (match := marker_re.fullmatch(line)) is not None
    ]
    if len(markers) != 114:
        raise ValueError(f"CO2 oracle has {len(markers)} CO_FIELD blocks, not 114")
    oracle: dict[tuple[str, str, str], dict[str, Any]] = {}
    for index, (marker_line, block_id, dchart, view) in enumerate(markers):
        end_line = markers[index + 1][0] - 1 if index + 1 < len(markers) else len(lines)
        block = [(line_no, lines[line_no - 1]) for line_no in range(marker_line + 1, end_line + 1)]

        def one_field(label: str) -> tuple[str, int]:
            prefix = f"- {label} = "
            hits = [(line_no, line[len(prefix):]) for line_no, line in block if line.startswith(prefix)]
            if len(hits) != 1:
                raise ValueError(f"{block_id}::{label} cardinality is {len(hits)}")
            return hits[0][1], hits[0][0]

        location_value, _ = one_field("Location")
        location_parts = location_value.split(" / ", 1)
        if len(location_parts) != 2 or location_parts[0] != dchart:
            raise ValueError(f"{block_id} Location does not bind its D-chart")
        members, members_line = one_field("Members")
        sentence, sentence_line = one_field("2.5차 관절문")
        key = (dchart, view, location_parts[1])
        if key in oracle:
            raise ValueError(f"duplicate oracle key: {key}")
        oracle[key] = {
            "block_id": block_id,
            "block_line_start": marker_line,
            "members": members,
            "members_line": members_line,
            "sentence": sentence,
            "sentence_line": sentence_line,
        }
    return oracle, {"bytes": len(raw), "records": len(oracle), "sha256": sha256_bytes(raw)}


def producer_code_locations(path: Path) -> dict[str, str]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("E5 producer source is missing or symlinked")
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: dict[str, tuple[int, int]] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in {
            "render_pikachu_sentence", "parse_execution_dataset"
        }:
            if node.end_lineno is None:
                raise ValueError(f"producer AST lacks end line: {node.name}")
            found[node.name] = (node.lineno, node.end_lineno)
    if set(found) != {"render_pikachu_sentence", "parse_execution_dataset"}:
        raise ValueError("producer evidence functions are missing or duplicated")
    try:
        relative = path.resolve().relative_to(ROOT).as_posix()
    except ValueError as error:
        raise ValueError("producer must reside in the KANI skill root") from error
    return {
        "render": (
            f"{relative}:{found['render_pikachu_sentence'][0]}-"
            f"{found['render_pikachu_sentence'][1]}::render_pikachu_sentence"
        ),
        "route": (
            f"{relative}:{found['parse_execution_dataset'][0]}-"
            f"{found['parse_execution_dataset'][1]}::parse_execution_dataset"
        ),
    }


def validate_router_contract(router: dict[str, Any]) -> None:
    if router.get("schema_version") != "DATASET_TO_PIKACHU_JUDGMENT_ROUTER_V10":
        raise ValueError("router schema mismatch")
    if router.get("status") != "EXPECTED_VALUE_BOUND__SECOND_RESTORE_EVIDENCE_REVIEW":
        raise ValueError("router state mismatch")
    contract = router.get("dataset_contract", {})
    if contract.get("execution_input") != SOURCE_FILENAME:
        raise ValueError("router execution input mismatch")
    if contract.get("expected_output") != EXPECTED_FILENAME:
        raise ValueError("router expected output mismatch")
    if contract.get("expected_output_role") != "HASH_LOCKED_REPLAY_ORACLE_NOT_RENDER_INPUT":
        raise ValueError("router oracle-role mismatch")
    if contract.get("source_order") != list(SOURCE_ORDER) or contract.get("year") != 2027:
        raise ValueError("router source order/year mismatch")
    if router.get("scope") != {
        "expected_bhava_records": 50,
        "expected_rashi_records": 64,
        "expected_total_records": 114,
        "lane": "COPRESENCE",
        "state": "E5_EXECUTION_OVERLAY_EXPECTED_VALUE_BOUND",
    }:
        raise ValueError("router E5 scope mismatch")
    if set(router.get("dchart_rules", {})) != set(SOURCE_ORDER):
        raise ValueError("router D-chart rule roster mismatch")
    required_routes = router.get("judgment_routes", {})
    if set(required_routes) != {"RASHI", "BHAVA"}:
        raise ValueError("router Rashi/Bhava route roster mismatch")
    for view in ("RASHI", "BHAVA"):
        route = required_routes[view]
        if any(not route.get(key) for key in (
            "condition", "degree_policy", "rejected_route", "selected_route",
            "why_rejected", "why_selected",
        )):
            raise ValueError(f"router {view} decision fields incomplete")


def verify_registry_after_render(source_dir: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    registry_path = source_dir / "manifest.json"
    if sha256_file(registry_path) != TRUSTED_SOURCE_REGISTRY_SHA256:
        raise ValueError("source registry trusted hash mismatch")
    registry = read_object(registry_path)
    if registry.get("schema_version") != SOURCE_SCHEMA:
        raise ValueError("source registry schema mismatch")
    files = registry.get("files")
    if not isinstance(files, list) or len(files) != 6:
        raise ValueError("source registry must contain six files")
    entries: dict[str, dict[str, Any]] = {}
    for entry in files:
        if not isinstance(entry, dict):
            raise ValueError("source registry entry is not an object")
        filename = entry.get("filename")
        if not isinstance(filename, str) or Path(filename).name != filename or filename in entries:
            raise ValueError("source registry filename is unsafe or duplicated")
        entries[filename] = entry
    if set(entries) != set(TRUSTED_FILE_SHA256):
        raise ValueError("source registry filename roster mismatch")
    for filename, trusted_hash in TRUSTED_FILE_SHA256.items():
        path = source_dir / filename
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"registered file missing or symlinked: {filename}")
        raw = path.read_bytes()
        entry = entries[filename]
        if sha256_bytes(raw) != trusted_hash or entry.get("sha256") != trusted_hash:
            raise ValueError(f"registered file hash mismatch: {filename}")
        if len(raw) != entry.get("bytes") or raw.count(b"\n") != entry.get("lines"):
            raise ValueError(f"registered file byte/line count mismatch: {filename}")
    return registry, entries


def build_expected_records(
    candidates: list[dict[str, Any]],
    oracle: dict[tuple[str, str, str], dict[str, Any]],
    router: dict[str, Any],
    source_meta: dict[str, Any],
    oracle_meta: dict[str, Any],
    code_locations: dict[str, str],
) -> list[dict[str, Any]]:
    candidate_keys = {(row["dchart"], row["view"], row["location"]) for row in candidates}
    if len(candidate_keys) != len(candidates):
        raise ValueError("derived Dataset route keys are not unique")
    if candidate_keys != set(oracle):
        missing = sorted(set(oracle) - candidate_keys)
        extra = sorted(candidate_keys - set(oracle))
        raise ValueError(f"Dataset/oracle route mismatch missing={missing} extra={extra}")

    records: list[dict[str, Any]] = []
    why_qa = router["why_correction_qa"]
    if set(why_qa) != {"answer_after", "answer_before_void", "correction", "question"}:
        raise ValueError("Why correction Q&A field roster mismatch")
    for ordinal, candidate in enumerate(candidates, start=1):
        key = (candidate["dchart"], candidate["view"], candidate["location"])
        expected = oracle[key]
        if candidate["member_display"] != expected["members"]:
            raise ValueError(f"independent member replay mismatch: {key}")
        sentence = candidate["generated_sentence"]
        if sentence != expected["sentence"]:
            raise ValueError(f"independent PikaChu sentence replay mismatch: {key}")
        route = router["judgment_routes"][candidate["view"]]
        handoff = router["handoff"]["target_pattern"].format(
            DCHART=candidate["dchart"], VIEW=candidate["view"], LOCATION=candidate["location"]
        )
        records.append({
            "code_location": code_locations,
            "dataset": {
                "dchart": candidate["dchart"],
                "family_rejected_route": candidate["family_rejected_route"],
                "family_selected_route": candidate["family_selected_route"],
                "location": candidate["location"],
                "member_display": candidate["member_display"],
                "source_file": SOURCE_FILENAME,
                "source_file_sha256": source_meta["sha256"],
                "source_line_locations": candidate["source_line_locations"],
                "source_wrapper_line_end": candidate["source_block_line_end"],
                "source_wrapper_line_start": candidate["source_block_line_start"],
                "view": candidate["view"],
                "year": 2027,
            },
            "expected": {
                "block_id": expected["block_id"],
                "block_line_start": expected["block_line_start"],
                "file": EXPECTED_FILENAME,
                "file_sha256": oracle_meta["sha256"],
                "members_line": expected["members_line"],
                "sentence_line": expected["sentence_line"],
                "sentence_sha256": sha256_bytes(sentence.encode("utf-8")),
            },
            "handoff_target": handoff,
            "judgment_route": {
                "condition": route["condition"],
                "degree_policy": route["degree_policy"],
                "rejected_route": route["rejected_route"],
                "selected_route": route["selected_route"],
                "why_rejected": route["why_rejected"],
                "why_selected": route["why_selected"],
            },
            "output": {
                "pikachu_sentence": sentence,
                "pikachu_sentence_sha256": sha256_bytes(sentence.encode("utf-8")),
                "sentence_function": "VAS_CO2_99_2_5_STAGE_JOINT_SENTENCE",
            },
            "record_id": f"V10-E5-VAS27-{ordinal:04d}",
            "reinput_result": {
                "dataset_rendered_before_oracle_open": True,
                "expected_members_exact": True,
                "expected_sentence_exact": True,
                "status": "PASS_EXACT_PIKACHU_SENTENCE_REPLAY",
            },
            "schema_version": RECORD_SCHEMA,
            "status": "PASS_EXECUTION_EVIDENCE",
            "why_revision_qa": {
                **why_qa,
                "record_answer": (
                    f"{candidate['view']} {candidate['location']}에서 {route['why_selected']}를 충족하여 "
                    f"{route['selected_route']}를 선택하고 {route['rejected_route']}를 기각했다."
                ),
            },
        })
    return records


def read_ledger(path: Path) -> tuple[bytes, list[dict[str, Any]]]:
    raw, text, _ = canonical_text(path, require_final_lf=True)
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line:
            raise ValueError(f"blank JSONL row at line {line_number}")
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"JSONL row {line_number} is not an object")
        rows.append(value)
    return raw, rows


def diff_paths(actual: Any, expected: Any, prefix: str = "", limit: int = 24) -> list[str]:
    differences: list[str] = []

    def walk(left: Any, right: Any, path: str) -> None:
        if len(differences) >= limit:
            return
        if type(left) is not type(right):
            differences.append(f"{path or '<root>'} type mismatch")
            return
        if isinstance(left, dict):
            for key in sorted(set(left) | set(right)):
                child = f"{path}.{key}" if path else str(key)
                if key not in left:
                    differences.append(f"{child} missing")
                elif key not in right:
                    differences.append(f"{child} unexpected")
                else:
                    walk(left[key], right[key], child)
                if len(differences) >= limit:
                    return
        elif isinstance(left, list):
            if len(left) != len(right):
                differences.append(f"{path} length mismatch ({len(left)} != {len(right)})")
            for index, (left_item, right_item) in enumerate(zip(left, right)):
                walk(left_item, right_item, f"{path}[{index}]")
                if len(differences) >= limit:
                    return
        elif left != right:
            differences.append(f"{path or '<root>'} mismatch")

    walk(actual, expected, prefix)
    return differences


def validate(
    e5_dir: Path = DEFAULT_E5_DIR,
    source_dir: Path = DEFAULT_SOURCE_DIR,
    router_path: Path = DEFAULT_ROUTER,
    v9_manifest_path: Path = DEFAULT_V9_MANIFEST,
    producer_path: Path = DEFAULT_PRODUCER,
) -> tuple[dict[str, Any], int]:
    e5_dir = e5_dir.resolve()
    source_dir = source_dir.resolve()
    router_path = router_path.resolve()
    v9_manifest_path = v9_manifest_path.resolve()
    producer_path = producer_path.resolve()
    errors: list[str] = []
    trace: list[str] = []
    candidates: list[dict[str, Any]] = []
    expected_records: list[dict[str, Any]] = []
    ledger_raw = b""
    actual_records: list[dict[str, Any]] = []
    source_meta: dict[str, Any] = {}
    oracle_meta: dict[str, Any] = {}
    manifest: dict[str, Any] = {}

    # Phase 1: the router and plain Dataset are the only evidence inputs opened.
    try:
        if sha256_file(router_path) != TRUSTED_ROUTER_SHA256:
            raise ValueError("router trusted hash mismatch")
        router = read_object(router_path)
        validate_router_contract(router)
        trace.append("ROUTER_LOCKED")
        candidates, source_meta = derive_candidates_before_oracle(
            source_dir / SOURCE_FILENAME, router
        )
        if source_meta["counts"] != EXPECTED_COUNTS:
            raise ValueError(f"independent Dataset topology mismatch: {source_meta['counts']}")
        if source_meta["sha256"] != TRUSTED_FILE_SHA256[SOURCE_FILENAME]:
            raise ValueError("VAS27 execution Dataset trusted hash mismatch")
        trace.append("INDEPENDENT_114_SENTENCE_RENDER_COMPLETE")
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        errors.append(f"pre-oracle generation failed: {error}")
        router = {}

    # Phase 2: only a complete independent render permits the oracle to open.
    registry: dict[str, Any] = {}
    registry_entries: dict[str, dict[str, Any]] = {}
    oracle: dict[tuple[str, str, str], dict[str, Any]] = {}
    if not errors:
        try:
            oracle, oracle_meta = open_expected_oracle_after_render(
                source_dir / EXPECTED_FILENAME
            )
            trace.append("EXPECTED_CO2_ORACLE_OPENED_POST_RENDER")
            if oracle_meta["sha256"] != TRUSTED_FILE_SHA256[EXPECTED_FILENAME]:
                raise ValueError("VAS27 expected oracle trusted hash mismatch")
            registry, registry_entries = verify_registry_after_render(source_dir)
            trace.append("SIX_FILE_SOURCE_REGISTRY_REOPENED_AND_HASH_VERIFIED")
            code_locations = producer_code_locations(producer_path)
            expected_records = build_expected_records(
                candidates, oracle, router, source_meta, oracle_meta, code_locations
            )
            trace.append("DATASET_JUDGMENT_PIKACHU_REPLAY_114_OF_114")
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            errors.append(f"post-render oracle comparison failed: {error}")

    # Phase 3: compare the stored evidence ledger and its manifest to the
    # independently reconstructed records, byte for byte and field for field.
    if not errors:
        try:
            ledger_path = e5_dir / "e5_decision_ledger.jsonl"
            manifest_path = e5_dir / "e5_manifest.json"
            ledger_raw, actual_records = read_ledger(ledger_path)
            manifest = read_object(manifest_path)
            expected_ledger = b"".join(compact_json(record) + b"\n" for record in expected_records)
            if len(actual_records) != 114:
                errors.append(f"stored ledger record count is {len(actual_records)}, not 114")
            for index, (actual, expected) in enumerate(zip(actual_records, expected_records), start=1):
                if actual != expected:
                    for difference in diff_paths(actual, expected, f"record[{index}]"):
                        errors.append(difference)
            if ledger_raw != expected_ledger:
                errors.append("ledger canonical bytes differ from independent 114-record reconstruction")

            source_inventory = {
                filename: {
                    "bytes": entry["bytes"],
                    "role": entry["role"],
                    "sha256": entry["sha256"],
                    "year": entry["year"],
                }
                for filename, entry in registry_entries.items()
            }
            expected_manifest = {
                "artifacts": {
                    "e5_decision_ledger.jsonl": {
                        "bytes": len(expected_ledger),
                        "records": len(expected_records),
                        "sha256": sha256_bytes(expected_ledger),
                    }
                },
                "counts": {
                    **EXPECTED_COUNTS,
                    "expected_exact_members": 114,
                    "expected_exact_sentences": 114,
                },
                "evidence_scope": "COPRESENCE_ROUTE_DATASET_TO_PIKACHU_SENTENCE_114_RECORDS",
                "final_pass": "HOLD_USER_REVIEW_OF_RECORD_REPLAY_EVIDENCE",
                "global_29_lane_e5": "HOLD_28_JUDGMENT_TO_SENTENCE_LANES_UNTESTED",
                "overlay": "ADD_TO_V9_DO_NOT_OVERWRITE",
                "rendered_before_oracle_sha256": source_meta["rendered_before_oracle_sha256"],
                "router": {
                    "path": "references/DATASET_TO_PIKACHU_JUDGMENT_ROUTER_V10.json",
                    "sha256": TRUSTED_ROUTER_SHA256,
                },
                "run_id": "",
                "schema_version": MANIFEST_SCHEMA,
                "second_restore": "EVIDENCE_REVIEW",
                "source_inventory": source_inventory,
                "source_registry_sha256": TRUSTED_SOURCE_REGISTRY_SHA256,
                "status": "PASS_EXECUTION_EVIDENCE_114_OF_114",
                "v10": "EXPECTED_VALUE_BOUND",
                "v9_baseline": {
                    "manifest_sha256": TRUSTED_V9_MANIFEST_SHA256,
                    "state": "PRESERVED_NOT_OVERWRITTEN",
                },
            }
            expected_manifest["run_id"] = sha256_bytes(
                compact_json({**expected_manifest, "run_id": None})
            )
            if manifest != expected_manifest:
                errors.extend(diff_paths(manifest, expected_manifest, "manifest"))
            if sha256_file(v9_manifest_path) != TRUSTED_V9_MANIFEST_SHA256:
                errors.append("immutable V9 manifest hash mismatch")
            actual_files = {
                path.name for path in e5_dir.iterdir()
                if path.is_file() and not path.is_symlink()
            }
            if actual_files != {"e5_decision_ledger.jsonl", "e5_manifest.json"}:
                errors.append(f"E5 evidence file inventory mismatch: {sorted(actual_files)}")
            if any(path.is_symlink() for path in e5_dir.iterdir()):
                errors.append("E5 evidence directory contains a symlink")
            trace.append("STORED_LEDGER_AND_MANIFEST_COMPARED")
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            errors.append(f"stored evidence validation failed: {error}")

    status = "PASS" if not errors else "REVISE"
    report = {
        "checks": {
            "code_and_source_line_locations": status,
            "dataset_to_judgment_to_pikachu_exact_replay": status,
            "handoff_target": status,
            "manifest_and_hashes": status,
            "record_id_and_required_fields": status,
            "reinput_result": status,
            "selected_and_rejected_route": status,
            "why_revision_qa": status,
        },
        "counts": {
            "bhava_records": sum(row.get("view") == "BHAVA" for row in candidates),
            "expected_exact_sentence_replays": len(expected_records) if not errors else 0,
            "rashi_records": sum(row.get("view") == "RASHI" for row in candidates),
            "stored_records": len(actual_records),
            "total_derived_records": len(candidates),
        },
        "e5_status": (
            "PASS_EXECUTION_EVIDENCE_114_OF_114" if not errors
            else "REVISE_EXECUTION_EVIDENCE"
        ),
        "errors": errors,
        "final_pass": "HOLD_USER_REVIEW_OF_RECORD_REPLAY_EVIDENCE",
        "ledger_sha256": sha256_bytes(ledger_raw) if ledger_raw else None,
        "oracle_policy": {
            "expected_file_role": "HASH_LOCKED_REPLAY_ORACLE_NOT_RENDER_INPUT",
            "expected_opened_after_independent_render": (
                "EXPECTED_CO2_ORACLE_OPENED_POST_RENDER" in trace
                and trace.index("INDEPENDENT_114_SENTENCE_RENDER_COMPLETE")
                < trace.index("EXPECTED_CO2_ORACLE_OPENED_POST_RENDER")
            ),
            "producer_imported": False,
            "rendered_before_oracle_sha256": source_meta.get("rendered_before_oracle_sha256"),
            "trace": trace,
        },
        "required_evidence": [
            "record_id", "code_location", "source_line_locations",
            "selected_route", "rejected_route", "why_revision_qa",
            "reinput_result", "handoff_target", "pikachu_sentence",
        ],
        "router_sha256": sha256_file(router_path) if router_path.is_file() else None,
        "schema_version": REPORT_SCHEMA,
        "second_restore": "EVIDENCE_REVIEW",
        "source_dataset_sha256": source_meta.get("sha256"),
        "status": status,
        "validated_run_id": manifest.get("run_id") if isinstance(manifest, dict) else None,
        "v10": "EXPECTED_VALUE_BOUND",
    }
    return report, 0 if status == "PASS" else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--e5-dir", type=Path, default=DEFAULT_E5_DIR)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--router", type=Path, default=DEFAULT_ROUTER)
    parser.add_argument("--v9-manifest", type=Path, default=DEFAULT_V9_MANIFEST)
    parser.add_argument("--producer", type=Path, default=DEFAULT_PRODUCER)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report, code = validate(
        args.e5_dir, args.source_dir, args.router, args.v9_manifest, args.producer
    )
    payload = canonical_json(report)
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_bytes(payload)
    sys.stdout.buffer.write(payload)
    return code


if __name__ == "__main__":
    sys.exit(main())

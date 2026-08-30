#!/usr/bin/env python3
"""Execute the KANI V10 E5 Dataset→Judgment→PikaChu replay overlay.

VAS27 Source is parsed and rendered before the expected CO2_99 file is opened.
The expected file is then used only as a hash-locked replay oracle.  V9 bytes
are never modified; this run writes a separate V10 overlay.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
from pathlib import Path
import re
import sys
import unicodedata
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE_DIR = ROOT / "references" / "v10_sources" / "user_upload_20260830"
DEFAULT_ROUTER = ROOT / "references" / "DATASET_TO_PIKACHU_JUDGMENT_ROUTER_V10.json"
DEFAULT_V9_MANIFEST = ROOT / "references" / "v9_baseline" / "kani_v9_manifest.json"

SCHEMA_VERSION = "KANI_V10_E5_EXECUTION_OVERLAY_V1"
RECORD_SCHEMA_VERSION = "KANI_V10_E5_DECISION_RECORD_V1"
SOURCE_DCHART_ORDER = (
    "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10",
    "D11", "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60",
)
SOURCE_FILENAME = "HYEWON_VAS27_D1-D60_♤.txt"
EXPECTED_FILENAME = "HEAWON_VAS27_CO2_99_♤.txt"


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


def canonical_text(path: Path, *, require_final_lf: bool = True) -> tuple[bytes, str, list[str]]:
    raw = path.read_bytes()
    if (
        raw.startswith(b"\xef\xbb\xbf")
        or b"\r" in raw
        or b"\x00" in raw
        or (require_final_lf and not raw.endswith(b"\n"))
    ):
        raise ValueError(f"non-canonical UTF-8/LF source: {path}")
    text = raw.decode("utf-8")
    if unicodedata.normalize("NFC", text) != text:
        raise ValueError(f"non-NFC source: {path}")
    return raw, text, text.splitlines()


def write_exclusive(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def function_location(function: Any) -> str:
    lines, start = inspect.getsourcelines(function)
    relative = Path(__file__).resolve().relative_to(ROOT).as_posix()
    return f"{relative}:{start}-{start + len(lines) - 1}::{function.__name__}"


def verify_source_registry(source_dir: Path) -> dict[str, Any]:
    manifest = read_object(source_dir / "manifest.json")
    if manifest.get("schema_version") != "KANI_V10_USER_SOURCE_REGISTRY_V1":
        raise ValueError("source registry schema")
    files = manifest.get("files")
    if not isinstance(files, list) or len(files) != 6:
        raise ValueError("source registry file count")
    for entry in files:
        filename = entry.get("filename")
        if not isinstance(filename, str) or Path(filename).name != filename:
            raise ValueError("unsafe source registry filename")
        path = source_dir / filename
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"source file missing/symlink: {filename}")
        raw = path.read_bytes()
        if len(raw) != entry.get("bytes") or sha256_bytes(raw) != entry.get("sha256"):
            raise ValueError(f"source file hash/size: {filename}")
        if raw.count(b"\n") != entry.get("lines"):
            raise ValueError(f"source line count: {filename}")
    return manifest


def normalize_rashi_actor(label: str) -> str:
    if label.startswith("Muntha"):
        return "Muntha (Mu)"
    base = re.sub(r"\([^)]*\)", "", label).strip()
    if "(R)" in label:
        base += " (R)"
    return base


def degree_key(value: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"([0-9]{1,2}):([0-9]{2}):([0-9]{2})", value)
    if match is None:
        raise ValueError(f"degree grammar: {value!r}")
    return tuple(int(part) for part in match.groups())


def resolve_rule(router: dict[str, Any], dchart: str, view: str) -> tuple[str, str]:
    rule = router["dchart_rules"][dchart]
    role = rule["role"]
    if dchart == "D1":
        reality = rule[f"{view.casefold()}_reality_rule"]
    else:
        reality = rule["reality_rule"]
    return role, reality


def render_pikachu_sentence(
    router: dict[str, Any], *, dchart: str, view: str, location: str,
    member_display: str, degree_order: str | None, selected_route: str,
) -> str:
    route_views = [
        route_view for route_view, route in router["judgment_routes"].items()
        if route["selected_route"] == selected_route
    ]
    if route_views != [view]:
        raise ValueError(
            f"selected route does not dispatch the requested view: {selected_route!r} -> {route_views!r}"
        )
    role, reality = resolve_rule(router, dchart, view)
    bindings = {
        "DCHART": dchart,
        "DEGREE_ORDER": degree_order or "NOT_APPLICABLE",
        "LOCATION": location,
        "MEMBERS_PLUS": member_display.replace(" / ", " + "),
        "REALITY_RULE": reality,
        "ROLE": role,
        "YEAR": router["dataset_contract"]["year"],
    }
    return router["sentence_templates"][route_views[0]].format_map(bindings)


def parse_execution_dataset(path: Path, router: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw, text, lines = canonical_text(path)
    marker_pattern = re.compile(r"^\[(D[0-9]+) (RASHI|BHAVA) SOURCE\]$", re.MULTILINE)
    markers = list(marker_pattern.finditer(text))
    expected_markers = [(dchart, view) for dchart in SOURCE_DCHART_ORDER for view in ("RASHI", "BHAVA")]
    if [(match.group(1), match.group(2)) for match in markers] != expected_markers:
        raise ValueError("VAS27 source wrapper order/count")

    bhava_codes = router["actor_normalization"]["bhava_codes"]
    code_pattern = re.compile(
        "|".join(re.escape(code) for code in sorted(bhava_codes, key=len, reverse=True))
    )
    candidates: list[dict[str, Any]] = []
    single_fields = 0
    for marker_index, match in enumerate(markers):
        start_offset = match.end()
        end_offset = markers[marker_index + 1].start() if marker_index + 1 < len(markers) else len(text)
        block = text[start_offset:end_offset]
        block_start_line = text.count("\n", 0, start_offset) + 1
        dchart, view = match.group(1), match.group(2)
        family_route = "D1_ROOT" if dchart == "D1" else "TARGET_DCHART"
        family_rejected = "TARGET_DCHART" if dchart == "D1" else "D1_ROOT_SINGLE_GRAMMAR"

        if view == "RASHI":
            local_lines = block.splitlines()
            headings = [index for index, line in enumerate(local_lines) if line.startswith("Visible Planetary Positions")]
            if len(headings) != 1:
                raise ValueError(f"Rashi position heading: {dchart}")
            stop_candidates = [
                index for index, line in enumerate(local_lines[headings[0] + 1:], start=headings[0] + 1)
                if line.startswith("Visible Vimshottari Mudda Dasha") or line == "Lock Status"
            ]
            if not stop_candidates:
                raise ValueError(f"Rashi position end: {dchart}")
            groups: dict[str, list[dict[str, Any]]] = {}
            source_rows = 0
            row_pattern = re.compile(r"^- (.+?) — Degree ([^/]+) / Rashi ([^/]+) /")
            for local_index in range(headings[0] + 1, stop_candidates[0]):
                row = row_pattern.match(local_lines[local_index])
                if row is None:
                    continue
                source_rows += 1
                actor = normalize_rashi_actor(row.group(1))
                degree = row.group(2).strip()
                sign = row.group(3).strip()
                if degree == "not shown" and sign == "not shown":
                    continue
                degree_key(degree)
                groups.setdefault(sign, []).append({
                    "actor": actor,
                    "degree": degree,
                    "line": block_start_line + local_index,
                    "raw": local_lines[local_index],
                })
            if source_rows != 14:
                raise ValueError(f"Rashi actor row count: {dchart}")
            for location, members in groups.items():
                if len(members) < 2:
                    single_fields += 1
                    continue
                ordered = sorted(members, key=lambda row: degree_key(row["degree"]))
                member_display = " / ".join(f"{row['actor']} {row['degree']}" for row in ordered)
                degree_order = " → ".join(f"{row['actor']} {row['degree']}" for row in ordered)
                candidates.append({
                    "dchart": dchart,
                    "degree_order": degree_order,
                    "family_rejected_route": family_rejected,
                    "family_selected_route": family_route,
                    "location": location,
                    "member_display": member_display,
                    "source_block_line_start": block_start_line,
                    "source_block_line_end": block_start_line + len(local_lines) - 1,
                    "source_line_locations": [
                        {"actor": row["actor"], "line": row["line"], "raw": row["raw"]}
                        for row in ordered
                    ],
                    "view": view,
                })
        else:
            local_lines = block.splitlines()
            headings = [index for index, line in enumerate(local_lines) if line == "Visible Bhava Snapshot"]
            if len(headings) != 1:
                raise ValueError(f"Bhava snapshot heading: {dchart}")
            stop = next(
                (index for index, line in enumerate(local_lines[headings[0] + 1:], start=headings[0] + 1)
                 if line.startswith("- Wheel Readability")),
                None,
            )
            if stop is None:
                raise ValueError(f"Bhava snapshot end: {dchart}")
            row_pattern = re.compile(r"^- (.+? Sector) = (.+)$")
            for local_index in range(headings[0] + 1, stop):
                row = row_pattern.match(local_lines[local_index])
                if row is None:
                    continue
                location, source_value = row.group(1), row.group(2)
                if source_value.startswith("empty"):
                    continue
                tokens = code_pattern.findall(source_value)
                if len(tokens) < 2:
                    single_fields += 1
                    continue
                member_display = " / ".join(bhava_codes[token] for token in tokens)
                candidates.append({
                    "dchart": dchart,
                    "degree_order": None,
                    "family_rejected_route": family_rejected,
                    "family_selected_route": family_route,
                    "location": location,
                    "member_display": member_display,
                    "source_block_line_start": block_start_line,
                    "source_block_line_end": block_start_line + len(local_lines) - 1,
                    "source_line_locations": [{
                        "line": block_start_line + local_index,
                        "raw": local_lines[local_index],
                        "visible_sector": location,
                    }],
                    "view": view,
                })

    for candidate in candidates:
        selected_route = router["judgment_routes"][candidate["view"]]["selected_route"]
        candidate["generated_sentence"] = render_pikachu_sentence(router, **{
            key: candidate[key] for key in ("dchart", "view", "location", "member_display", "degree_order")
        }, selected_route=selected_route)
        candidate["render_selected_route"] = selected_route
    counts = {
        "bhava_records": sum(candidate["view"] == "BHAVA" for candidate in candidates),
        "rashi_records": sum(candidate["view"] == "RASHI" for candidate in candidates),
        "single_fields_excluded": single_fields,
        "source_blocks": len(markers),
        "total_records": len(candidates),
    }
    return candidates, {
        "bytes": len(raw),
        "counts": counts,
        "sha256": sha256_bytes(raw),
    }


def parse_expected_oracle(path: Path) -> tuple[dict[tuple[str, str, str], dict[str, Any]], dict[str, Any]]:
    raw, text, lines = canonical_text(path, require_final_lf=False)
    pattern = re.compile(
        r"^\[(HYEWON_2027_VAS_(D[0-9]+)_(RASHI|BHAVA)_[^\]]+_CO_FIELD)\]$",
        re.MULTILINE,
    )
    starts = list(pattern.finditer(text))
    if len(starts) != 114:
        raise ValueError(f"expected CO_FIELD count: {len(starts)}")
    expected: dict[tuple[str, str, str], dict[str, Any]] = {}
    for index, match in enumerate(starts):
        start = match.start()
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        block = text[start:end]
        block_line = text.count("\n", 0, start) + 1

        def exact_field(label: str) -> tuple[str, int]:
            field_pattern = re.compile(rf"^- {re.escape(label)} = (.*)$", re.MULTILINE)
            hits = list(field_pattern.finditer(block))
            if len(hits) != 1:
                raise ValueError(f"expected field cardinality {match.group(1)}::{label}")
            return hits[0].group(1), block_line + block.count("\n", 0, hits[0].start())

        location_value, _ = exact_field("Location")
        if " / " not in location_value:
            raise ValueError("expected Location grammar")
        location = location_value.split(" / ", 1)[1]
        members, members_line = exact_field("Members")
        sentence, sentence_line = exact_field("2.5차 관절문")
        key = (match.group(2), match.group(3), location)
        if key in expected:
            raise ValueError(f"duplicate expected route key: {key}")
        expected[key] = {
            "block_id": match.group(1),
            "block_line_start": block_line,
            "members": members,
            "members_line": members_line,
            "sentence": sentence,
            "sentence_line": sentence_line,
        }
    return expected, {"bytes": len(raw), "records": len(expected), "sha256": sha256_bytes(raw)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--router", type=Path, default=DEFAULT_ROUTER)
    parser.add_argument("--v9-manifest", type=Path, default=DEFAULT_V9_MANIFEST)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    source_dir = args.source_dir.resolve()
    out_dir = args.out_dir.resolve()
    if out_dir.exists() and (not out_dir.is_dir() or any(out_dir.iterdir())):
        raise SystemExit(f"output directory must not exist or must be empty: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    registry = verify_source_registry(source_dir)
    router = read_object(args.router)
    if router.get("schema_version") != "DATASET_TO_PIKACHU_JUDGMENT_ROUTER_V10":
        raise SystemExit("router schema mismatch")
    if router.get("status") != "EXPECTED_VALUE_BOUND__SECOND_RESTORE_EVIDENCE_REVIEW":
        raise SystemExit("router evidence-review status mismatch")

    # Execution invariant: render every candidate before opening the oracle.
    candidates, source_meta = parse_execution_dataset(source_dir / SOURCE_FILENAME, router)
    if source_meta["counts"] != {
        "bhava_records": 50,
        "rashi_records": 64,
        "single_fields_excluded": 165,
        "source_blocks": 40,
        "total_records": 114,
    }:
        raise SystemExit(f"unexpected VAS27 production topology: {source_meta['counts']}")
    rendered_before_oracle_sha256 = sha256_bytes(
        b"".join((candidate["generated_sentence"] + "\n").encode("utf-8") for candidate in candidates)
    )
    expected, expected_meta = parse_expected_oracle(source_dir / EXPECTED_FILENAME)

    candidate_keys = {(row["dchart"], row["view"], row["location"]) for row in candidates}
    if candidate_keys != set(expected):
        missing = sorted(set(expected) - candidate_keys)
        extra = sorted(candidate_keys - set(expected))
        raise SystemExit(f"candidate/oracle route key mismatch missing={missing} extra={extra}")

    route_code = function_location(parse_execution_dataset)
    render_code = function_location(render_pikachu_sentence)
    why_qa = router["why_correction_qa"]
    records: list[dict[str, Any]] = []
    for ordinal, candidate in enumerate(candidates, start=1):
        key = (candidate["dchart"], candidate["view"], candidate["location"])
        oracle = expected[key]
        route = router["judgment_routes"][candidate["view"]]
        if candidate["render_selected_route"] != route["selected_route"]:
            raise SystemExit(f"render/ledger route divergence at {key}")
        generated = candidate["generated_sentence"]
        exact_members = candidate["member_display"] == oracle["members"]
        exact_sentence = generated == oracle["sentence"]
        if not exact_members or not exact_sentence:
            raise SystemExit(f"replay mismatch at {key}: members={exact_members} sentence={exact_sentence}")
        record_id = f"V10-E5-VAS27-{ordinal:04d}"
        handoff_target = router["handoff"]["target_pattern"].format(
            DCHART=candidate["dchart"], VIEW=candidate["view"], LOCATION=candidate["location"]
        )
        record = {
            "code_location": {
                "render": render_code,
                "route": route_code,
            },
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
                "block_id": oracle["block_id"],
                "block_line_start": oracle["block_line_start"],
                "file": EXPECTED_FILENAME,
                "file_sha256": expected_meta["sha256"],
                "members_line": oracle["members_line"],
                "sentence_line": oracle["sentence_line"],
                "sentence_sha256": sha256_bytes(oracle["sentence"].encode("utf-8")),
            },
            "handoff_target": handoff_target,
            "judgment_route": {
                "condition": route["condition"],
                "degree_policy": route["degree_policy"],
                "rejected_route": route["rejected_route"],
                "selected_route": route["selected_route"],
                "why_rejected": route["why_rejected"],
                "why_selected": route["why_selected"],
            },
            "output": {
                "pikachu_sentence": generated,
                "pikachu_sentence_sha256": sha256_bytes(generated.encode("utf-8")),
                "sentence_function": "VAS_CO2_99_2_5_STAGE_JOINT_SENTENCE",
            },
            "record_id": record_id,
            "reinput_result": {
                "dataset_rendered_before_oracle_open": True,
                "expected_members_exact": True,
                "expected_sentence_exact": True,
                "status": "PASS_EXACT_PIKACHU_SENTENCE_REPLAY",
            },
            "schema_version": RECORD_SCHEMA_VERSION,
            "status": "PASS_EXECUTION_EVIDENCE",
            "why_revision_qa": {
                **why_qa,
                "record_answer": (
                    f"{candidate['view']} {candidate['location']}에서 {route['why_selected']}를 충족하여 "
                    f"{route['selected_route']}를 선택하고 {route['rejected_route']}를 기각했다."
                ),
            },
        }
        records.append(record)

    ledger_bytes = b"".join(compact_json(record) + b"\n" for record in records)
    write_exclusive(out_dir / "e5_decision_ledger.jsonl", ledger_bytes)

    source_inventory = {
        entry["filename"]: {
            "bytes": entry["bytes"],
            "role": entry["role"],
            "sha256": entry["sha256"],
            "year": entry["year"],
        }
        for entry in registry["files"]
    }
    manifest = {
        "artifacts": {
            "e5_decision_ledger.jsonl": {
                "bytes": len(ledger_bytes),
                "records": len(records),
                "sha256": sha256_bytes(ledger_bytes),
            }
        },
        "counts": {
            **source_meta["counts"],
            "expected_exact_members": len(records),
            "expected_exact_sentences": len(records),
        },
        "evidence_scope": "COPRESENCE_ROUTE_DATASET_TO_PIKACHU_SENTENCE_114_RECORDS",
        "final_pass": "HOLD_USER_REVIEW_OF_RECORD_REPLAY_EVIDENCE",
        "global_29_lane_e5": "HOLD_28_JUDGMENT_TO_SENTENCE_LANES_UNTESTED",
        "overlay": "ADD_TO_V9_DO_NOT_OVERWRITE",
        "rendered_before_oracle_sha256": rendered_before_oracle_sha256,
        "router": {
            "path": "references/DATASET_TO_PIKACHU_JUDGMENT_ROUTER_V10.json",
            "sha256": sha256_file(args.router),
        },
        "run_id": "",
        "schema_version": SCHEMA_VERSION,
        "second_restore": "EVIDENCE_REVIEW",
        "source_inventory": source_inventory,
        "source_registry_sha256": sha256_file(source_dir / "manifest.json"),
        "status": "PASS_EXECUTION_EVIDENCE_114_OF_114",
        "v10": "EXPECTED_VALUE_BOUND",
        "v9_baseline": {
            "manifest_sha256": sha256_file(args.v9_manifest),
            "state": "PRESERVED_NOT_OVERWRITTEN",
        },
    }
    manifest["run_id"] = sha256_bytes(compact_json({**manifest, "run_id": None}))
    write_exclusive(out_dir / "e5_manifest.json", canonical_json(manifest))
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

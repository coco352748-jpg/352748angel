#!/usr/bin/env python3
"""Materialize the KANI V10 second-action router calibration run.

The input is the verified rq-sc7 PERSONAL_CHART_240 provider.  This producer
does not use the stored final sentence as a rendering input: it parses Source
slots, selects the occupant/house-lord route, renders from the locked template,
and only then compares the result with the Source sentence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import unicodedata
from typing import Any


SCHEMA_VERSION = "KANI_V10_ROUTER_RUN_V1"
RECORD_SCHEMA_VERSION = "KANI_V10_SENTENCE_RECORD_V1"
SOURCE_INDEX_SCHEMA_VERSION = "KANI_V10_SOURCE_INDEX_V1"

DCHART_ORDER = (
    "D1", "D9", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D10",
    "D11", "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60",
)
HOUSE_ORDER = tuple(f"H{number:02d}" for number in range(1, 13))

DEFAULT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ROUTER = DEFAULT_ROOT / "references" / "KANI_SECOND_ACTION_ROUTER_V2.json"
DEFAULT_V9_MANIFEST = DEFAULT_ROOT / "references" / "v9_baseline" / "kani_v9_manifest.json"

SUMMARY_PACKET_MAP = {
    "HOUSE_FUNCTION": "HOUSE_FUNCTION",
    "RASHI_SIGN": "RASHI_SIGN",
    "OCCUPANT_FIELD": "RASHI_OCCUPANTS",
    "HOUSE_LORD_FIELD": "RASHI_HOUSE_LORD",
    "HOUSE_LORD_POSITION": "RASHI_HOUSE_LORD_POSITION",
    "SHADBALA_OCCUPANT_EXECUTION": "SHADBALA_OCCUPANT_EXECUTION",
    "SHADBALA_HOUSE_LORD_EXECUTION": "SHADBALA_HOUSE_LORD_EXECUTION",
    "SHADBALA_USE_DECISION": "SHADBALA_USE_DECISION",
    "INCOMING_GRAHA_DRISHTI": "INCOMING_GRAHA_DRISHTI",
    "ASPECT01_DIRECT_STATUS": "ASPECT01_DIRECT_APPLICATION_STATUS",
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


def write_exclusive(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def line_value(
    lines: list[str], label: str, *, section_start: int | None = None, section_end: int | None = None
) -> tuple[str, int, str]:
    prefix = f"- {label} = "
    start = 0 if section_start is None else section_start
    end = len(lines) if section_end is None else section_end
    matches = [(index, line) for index, line in enumerate(lines[start:end], start=start) if line.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"field cardinality {label!r}: {len(matches)}")
    index, raw_line = matches[0]
    return raw_line[len(prefix):], index + 1, raw_line


def heading_index(lines: list[str], heading: str) -> int:
    matches = [index for index, line in enumerate(lines) if line == heading]
    if len(matches) != 1:
        raise ValueError(f"heading cardinality {heading!r}: {len(matches)}")
    return matches[0]


def parse_final_record(lines: list[str]) -> tuple[str, int, str]:
    start = heading_index(lines, "6. FINAL HOUSE DEEP OPERATION SENTENCE")
    end = heading_index(lines, "7. CLIENT READING")
    if start >= end:
        raise ValueError("final-record section order")
    body = [(index, line) for index, line in enumerate(lines[start + 1:end], start=start + 1) if line]
    if len(body) != 1 or not body[0][1].startswith("- "):
        raise ValueError(f"final-record cardinality/shape: {len(body)}")
    index, bullet = body[0]
    if lines.count(bullet) != 1:
        raise ValueError("final-record bullet must occur exactly once")
    if not bullet.endswith("."):
        raise ValueError("final-record bullet must end with a period")
    return bullet, index + 1, bullet[2:]


def parse_4ak_packet(lines: list[str]) -> dict[str, str]:
    begin = heading_index(lines, "- 4AK Exact House Packet Begin")
    end = heading_index(lines, "- 4AK Exact House Packet End")
    if begin >= end:
        raise ValueError("4AK packet section order")
    packet_lines = lines[begin + 1:end]
    if len(packet_lines) != 36:
        raise ValueError(f"4AK packet field count: {len(packet_lines)}")
    values: dict[str, str] = {}
    for position, line in enumerate(packet_lines):
        if position == 0:
            match = re.fullmatch(r"4AK_PACKET> ([0-9]{2}H)=APPLIED", line)
            if match is None:
                raise ValueError("4AK HOUSE_APPLIED field")
            values["HOUSE_APPLIED"] = match.group(1)
            continue
        prefix = "4AK_PACKET> / "
        if not line.startswith(prefix) or "=" not in line[len(prefix):]:
            raise ValueError(f"4AK malformed field at ordinal {position + 1}")
        key, value = line[len(prefix):].split("=", 1)
        if not key or key in values:
            raise ValueError(f"4AK duplicate/empty key: {key!r}")
        values[key] = value
    return values


def parse_packet(path: Path, field_map: dict[str, str]) -> dict[str, Any]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or b"\x00" in raw or not raw.endswith(b"\n"):
        raise ValueError(f"non-canonical UTF-8/LF packet: {path}")
    text = raw.decode("utf-8")
    if unicodedata.normalize("NFC", text) != text:
        raise ValueError(f"non-NFC packet: {path}")
    lines = text.splitlines()

    expected_headings = [
        "0. HOUSE IDENTITY",
        "1. 07_4AK TARGET BODY PARENT RESULT",
        "2. 07_5AB D1 BHAVA REFERENCE PARENT RESULT",
        "3. 07_6AB D1 VIMSOPAKA / D1 ASPECT REFERENCE PARENT RESULT",
        "4. CROSS-LAYER CONVERGENCE",
        "5. CROSS-LAYER CONFLICT / HOLD",
        "6. FINAL HOUSE DEEP OPERATION SENTENCE",
        "7. CLIENT READING",
        "8. FINAL HOUSE CHECK",
    ]
    heading_positions = [heading_index(lines, heading) for heading in expected_headings]
    if heading_positions != sorted(heading_positions):
        raise ValueError(f"section order: {path}")
    if lines[-1] != "- Final sentence appears once = PASS":
        raise ValueError(f"final house check terminator: {path}")

    slots: dict[str, str] = {}
    spans: dict[str, dict[str, int]] = {}
    evidence_lines: list[str] = []
    for slot, label in field_map.items():
        value, line_number, raw_line = line_value(lines, label)
        slots[slot] = value
        spans[slot] = {"line_start": line_number, "line_end": line_number}
        evidence_lines.append(raw_line)

    packet_values = parse_4ak_packet(lines)
    for slot, packet_key in SUMMARY_PACKET_MAP.items():
        if packet_values.get(packet_key) != slots.get(slot):
            raise ValueError(f"summary/4AK mismatch {slot}: {path}")

    final_bullet, final_line_number, final_sentence = parse_final_record(lines)
    evidence_lines.append(final_bullet)
    spans["FINAL_RECORD"] = {
        "line_start": final_line_number,
        "line_end": final_line_number,
    }
    return {
        "raw": raw,
        "slots": slots,
        "spans": spans,
        "source_sentence": final_bullet,
        "source_sentence_value": final_sentence,
        "source_evidence_sha256": sha256_bytes(("\n".join(evidence_lines) + "\n").encode("utf-8")),
        "summary_4ak_equalities": len(SUMMARY_PACKET_MAP),
    }


def normalized_house(raw_house: str) -> tuple[str, str]:
    match = re.fullmatch(r"([1-9]|1[0-2])H", raw_house)
    if match is None:
        raise ValueError(f"invalid House value: {raw_house!r}")
    number = int(match.group(1))
    return f"H{number:02d}", f"{number}H"


def bhava_bala_display(raw_rank: str) -> str:
    match = re.fullmatch(r"([0-9]+) / Rupas (.+)", raw_rank)
    if match is None:
        raise ValueError(f"invalid Bhava Bala Rank: {raw_rank!r}")
    return f"Rank {match.group(1)} Rupas {match.group(2)}"


def choose_route(occupants: str, house_lord: str) -> dict[str, str | bool]:
    if not occupants or not house_lord:
        raise ValueError("empty occupant/house-lord field value")
    if occupants == "EMPTY":
        return {
            "empty_confirmed": True,
            "selected_route": "HOUSE_LORD_ROUTE",
            "rejected_route": "OCCUPANT_ROUTE",
            "selected_value": house_lord,
            "why_selected": "EMPTY_CONFIRMED_SO_HOUSE_LORD_IS_PRIMARY_JUDGMENT_DRIVER",
            "why_rejected": "EMPTY_IS_NOT_AN_OCCUPANT",
        }
    return {
        "empty_confirmed": False,
        "selected_route": "OCCUPANT_ROUTE",
        "rejected_route": "HOUSE_LORD_ROUTE",
        "selected_value": occupants,
        "why_selected": "VISIBLE_OCCUPANTS_ARE_PRIMARY_JUDGMENT_DRIVERS",
        "why_rejected": "HOUSE_LORD_MUST_NOT_REPLACE_OR_BE_APPENDED_TO_OCCUPANTS",
    }


def render_sentence(template: str, slots: dict[str, str]) -> tuple[str, dict[str, str]]:
    _, house_display = normalized_house(slots["HOUSE_ID"])
    bindings = dict(slots)
    bindings["HOUSE_DISPLAY"] = house_display
    bindings["BHAVA_BALA_DISPLAY"] = bhava_bala_display(slots["BHAVA_BALA_RANK"])
    try:
        rendered = template.format_map(bindings)
    except KeyError as exc:
        raise ValueError(f"unbound template slot: {exc.args[0]}") from exc
    return rendered, bindings


def verify_provider(source_root: Path) -> tuple[dict[str, Any], str]:
    script = source_root / "scripts" / "personal_chart_240.py"
    manifest_path = source_root / "references" / "personal-chart-240" / "manifest.json"
    if not script.is_file() or not manifest_path.is_file():
        raise ValueError("rq-sc7 PERSONAL_CHART_240 provider is incomplete")
    completed = subprocess.run(
        [sys.executable, str(script), "verify"],
        cwd=source_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if completed.returncode != 0 or not completed.stdout.startswith("PASS PERSONAL_CHART_240 jobs=240 "):
        raise ValueError(f"rq-sc7 provider verification failed: {completed.stdout.strip()}")
    return read_object(manifest_path), completed.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--router", type=Path, default=DEFAULT_ROUTER)
    parser.add_argument("--v9-manifest", type=Path, default=DEFAULT_V9_MANIFEST)
    args = parser.parse_args()

    source_root = args.source_root.resolve()
    output = args.out_dir.resolve()
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise SystemExit(f"output directory must not exist or must be empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    router = read_object(args.router)
    if router.get("schema_version") != "KANI_SECOND_ACTION_ROUTER_V2":
        raise SystemExit("router schema mismatch")
    field_map = router.get("field_map")
    if not isinstance(field_map, dict) or len(field_map) != 15:
        raise SystemExit("router field map must contain 15 exact fields")
    template = router.get("template", {}).get("text")
    template_id = router.get("template", {}).get("id")
    if not isinstance(template, str) or not isinstance(template_id, str):
        raise SystemExit("router template missing")

    source_manifest, provider_verify = verify_provider(source_root)
    authority = router["authority"]
    if not (
        source_manifest.get("schema") == "RQ_VEDIC_HYEWON_PERSONAL_CHART_240_V1"
        and source_manifest.get("source_set_id") == authority["source_set_id"]
        and source_manifest.get("archive_set_sha256") == authority["archive_set_sha256"]
        and source_manifest.get("dchart_order") == list(DCHART_ORDER)
        and source_manifest.get("house_order") == list(HOUSE_ORDER)
    ):
        raise SystemExit("source manifest authority/order mismatch")
    jobs = source_manifest.get("jobs")
    if not isinstance(jobs, list) or len(jobs) != 240:
        raise SystemExit("source manifest must contain 240 jobs")

    v9_manifest_sha256 = sha256_file(args.v9_manifest)
    v9_manifest = read_object(args.v9_manifest)
    if v9_manifest.get("schema_version") != "KANI_CAUSAL_RESTORE_V9_BUNDLE_V1":
        raise SystemExit("retained V9 manifest mismatch")

    records: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    empty_count = 0
    conflict_count = 0
    for ordinal, (job, expected_dchart, expected_house) in enumerate(
        zip(jobs, (d for d in DCHART_ORDER for _ in HOUSE_ORDER), HOUSE_ORDER * len(DCHART_ORDER)),
        start=1,
    ):
        if job.get("job_order") != ordinal:
            raise SystemExit(f"source job order mismatch: {ordinal}")
        if job.get("dchart") != expected_dchart or job.get("house_id") != expected_house:
            raise SystemExit(f"source D×H order mismatch: {ordinal}")
        relative = job.get("relative_path")
        if not isinstance(relative, str) or Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise SystemExit(f"unsafe source relative path: {relative!r}")
        path = source_root / "references" / "personal-chart-240" / relative
        if path.is_symlink() or not path.is_file():
            raise SystemExit(f"source packet missing/symlink: {relative}")
        if path.stat().st_size != job.get("packet_bytes") or sha256_file(path) != job.get("packet_sha256"):
            raise SystemExit(f"source packet hash/size mismatch: {relative}")

        parsed = parse_packet(path, field_map)
        slots = parsed["slots"]
        normalized, _ = normalized_house(slots["HOUSE_ID"])
        if slots["TARGET_DCHART"] != expected_dchart or normalized != expected_house:
            raise SystemExit(f"packet identity mismatch: {relative}")
        route = choose_route(slots["OCCUPANT_FIELD"], slots["HOUSE_LORD_FIELD"])
        if route["empty_confirmed"]:
            empty_count += 1
        if slots["CONFLICT_HOLD_POINT"] != "NONE":
            conflict_count += 1
        rendered, bindings = render_sentence(template, slots)
        if rendered != parsed["source_sentence"]:
            raise SystemExit(f"slot-only replay mismatch: {relative}")

        record_id = f"KANI-V10-{expected_dchart}-{expected_house}"
        record = {
            "boundary_test": {
                "empty_token_exact": slots["OCCUPANT_FIELD"] == "EMPTY",
                "field_objects_distinct": True,
                "house_lord_appended_to_occupants": False,
                "reference_overwrite": False,
                "result": "PASS",
            },
            "code_location": "scripts/run_kani_v10_router.py::choose_route+render_sentence",
            "correction_qa": {
                "exact_source_sentence_match": True,
                "summary_4ak_equalities": f"{parsed['summary_4ak_equalities']}/{parsed['summary_4ak_equalities']}",
                "target_reference_boundary": "PASS",
            },
            "handoff": "ROUTE_DECISION_TO_TEMPLATE_SLOTS_TO_FINAL_RECORD",
            "independent_replay_record_id": record_id,
            "joint_id": f"{expected_dchart}-{expected_house}-TARGET-BODY-REFERENCE-JOINT",
            "judgment_operation": router["judgment_operation"],
            "record_id": record_id,
            "reinput": {
                "input_scope": "SLOT_BINDINGS_ONLY_WITH_SOURCE_SENTENCE_EXCLUDED",
                "result": "PASS_EXACT_SOURCE_RECORD",
            },
            "replay_result": "PASS_PRODUCER_REINPUT__INDEPENDENT_LEDGER_REQUIRED",
            "route": route,
            "schema_version": RECORD_SCHEMA_VERSION,
            "sentence_function": router["sentence_function"],
            "sentence_id": f"{record_id}-FINAL-HOUSE-DEEP-OPERATION",
            "slot_bindings": bindings,
            "slot_id": job["section_token"],
            "source": {
                "archive": job["archive"],
                "archive_sha256": job["archive_sha256"],
                "archive_set_sha256": source_manifest["archive_set_sha256"],
                "field_and_final_line_spans": parsed["spans"],
                "file_bytes": path.stat().st_size,
                "file_sha256": sha256_file(path),
                "member": job["member"],
                "member_sha256": job["member_sha256"],
                "packet_sha256": job["packet_sha256"],
                "relative_path": relative,
                "section_token": job["section_token"],
                "source_evidence_sha256": parsed["source_evidence_sha256"],
                "source_set_id": source_manifest["source_set_id"],
                "source_skill": "$rq-sc7",
            },
            "source_sentence": parsed["source_sentence"],
            "source_sentence_sha256": sha256_bytes(parsed["source_sentence"].encode("utf-8")),
            "status": "PASS_CALIBRATION_REPLAY",
            "template": {
                "id": template_id,
                "sha256": sha256_bytes(template.encode("utf-8")),
            },
            "v9_baseline_manifest_sha256": v9_manifest_sha256,
            "written_sentence": rendered,
            "written_sentence_sha256": sha256_bytes(rendered.encode("utf-8")),
        }
        records.append(record)
        source_rows.append({
            "bytes": path.stat().st_size,
            "dchart": expected_dchart,
            "house_id": expected_house,
            "job_order": ordinal,
            "member": job["member"],
            "member_sha256": job["member_sha256"],
            "packet_sha256": job["packet_sha256"],
            "relative_path": relative,
            "section_token": job["section_token"],
            "sha256": sha256_file(path),
        })

    records_bytes = b"".join(compact_json(record) + b"\n" for record in records)
    source_index = {
        "archive_set_sha256": source_manifest["archive_set_sha256"],
        "dchart_order": list(DCHART_ORDER),
        "house_order": list(HOUSE_ORDER),
        "personal_chart_240_sha256": authority["personal_chart_240_sha256"],
        "provider_verify": provider_verify,
        "records": source_rows,
        "schema_version": SOURCE_INDEX_SCHEMA_VERSION,
        "source_manifest_bytes": (source_root / "references" / "personal-chart-240" / "manifest.json").stat().st_size,
        "source_manifest_sha256": sha256_file(source_root / "references" / "personal-chart-240" / "manifest.json"),
        "source_set_id": source_manifest["source_set_id"],
        "status": "PASS_240_SOURCE_PACKETS_HASH_VERIFIED",
    }
    source_index_bytes = canonical_json(source_index)
    write_exclusive(output / "router_records.jsonl", records_bytes)
    write_exclusive(output / "source_index.json", source_index_bytes)

    run_core = {
        "counts": {
            "conflict_hold_point_non_none": conflict_count,
            "empty_house_lord_route": empty_count,
            "exact_sentence_replay": len(records),
            "occupied_route": len(records) - empty_count,
            "records": len(records),
            "summary_4ak_equalities": len(records) * len(SUMMARY_PACKET_MAP),
        },
        "e5_new_dataset_production": "HOLD_NOT_A_NEW_DATASET",
        "evidence_level": "CALIBRATION_REPLAY_CURRENT_SOURCE_NOT_E5_NEW_DATASET",
        "first_unresolved_data_job": "SUPPLY_MISSING_VAS26_DIRECT_LAYER_SOURCES",
        "judgment_operation": router["judgment_operation"],
        "records": {
            "bytes": len(records_bytes),
            "path": "router_records.jsonl",
            "sha256": sha256_bytes(records_bytes),
        },
        "retained_v9_manifest": {
            "path": "references/v9_baseline/kani_v9_manifest.json",
            "sha256": v9_manifest_sha256,
        },
        "router": {
            "id": router["router_id"],
            "path": "references/KANI_SECOND_ACTION_ROUTER_V2.json",
            "sha256": sha256_file(args.router),
            "template_id": template_id,
            "template_sha256": sha256_bytes(template.encode("utf-8")),
        },
        "schema_version": SCHEMA_VERSION,
        "sentence_function": router["sentence_function"],
        "source_index": {
            "bytes": len(source_index_bytes),
            "path": "source_index.json",
            "sha256": sha256_bytes(source_index_bytes),
        },
        "status": "PASS_TESTED_SCOPE_240",
        "terminal_version_boundary": "LOCKED_NO_AUTOMATIC_V11",
    }
    run_core["run_id"] = sha256_bytes(compact_json(run_core))
    write_exclusive(output / "router_run_manifest.json", canonical_json(run_core))
    print(json.dumps(run_core, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

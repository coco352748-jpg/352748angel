#!/usr/bin/env python3
"""Independently replay and validate a KANI V10 router run.

This module intentionally does not import the producer.  It reparses the live
rq-sc7 packets, recomputes both route branches and the sentence, and emits a
per-record independent replay ledger.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
from typing import Any


DCHART_ORDER = (
    "D1", "D9", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D10",
    "D11", "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60",
)
HOUSE_ORDER = tuple(f"H{number:02d}" for number in range(1, 13))
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ROUTER = ROOT / "references" / "KANI_SECOND_ACTION_ROUTER_V2.json"

LOCKED_TEMPLATE_ID = "KANI_V10_FINAL_HOUSE_DEEP_OPERATION_V1"
LOCKED_TEMPLATE = (
    "- {TARGET_DCHART} {HOUSE_DISPLAY}는 {HOUSE_FUNCTION}의 target body를 07_4AK의 "
    "{RASHI_SIGN} / occupants {OCCUPANT_FIELD} / lord {HOUSE_LORD_FIELD} / "
    "Shadbala {SHADBALA_USE_DECISION} / incoming Drishti {INCOMING_GRAHA_DRISHTI} / "
    "Aspect01 {ASPECT01_DIRECT_STATUS}로 고정하고 07_5AB의 D1 동일하우스 Bhava Bala "
    "{BHAVA_BALA_DISPLAY} 및 Bhava Middle packet을 참조층으로 결속하며 07_6AB의 D1 "
    "Vimsopaka 및 Planets/Bhava Middle aspect packet을 독립 참조층으로 겹쳐 확인한다. "
    "07_5AB와 07_6AB은 target-native body를 덮어쓰지 않으며 최종 귀속은 07_4AK target "
    "body에 남고 모든 비가시값과 충돌값은 HOLD로 보존된다."
)
FIELD_LABELS = {
    "ASPECT01_DIRECT_STATUS": "Aspect01 Direct Status",
    "BHAVA_BALA_RANK": "Bhava Bala Rank",
    "CONFLICT_HOLD_POINT": "Conflict / HOLD Point",
    "HOUSE_FUNCTION": "House Function",
    "HOUSE_ID": "House",
    "HOUSE_LORD_FIELD": "Rashi House Lord",
    "HOUSE_LORD_POSITION": "Rashi House Lord Position",
    "INCOMING_GRAHA_DRISHTI": "Incoming Graha Drishti",
    "OCCUPANT_FIELD": "Rashi Occupants",
    "RASHI_SIGN": "Rashi Sign",
    "SHADBALA_HOUSE_LORD_EXECUTION": "Shadbala House Lord Execution",
    "SHADBALA_OCCUPANT_EXECUTION": "Shadbala Occupant Execution",
    "SHADBALA_USE_DECISION": "Shadbala Use Decision",
    "TARGET_DCHART": "Target D-chart",
    "TARGET_DOMAIN": "Target Domain",
}
PACKET_MIRRORS = {
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
EXPECTED_HEADINGS = (
    "0. HOUSE IDENTITY",
    "1. 07_4AK TARGET BODY PARENT RESULT",
    "2. 07_5AB D1 BHAVA REFERENCE PARENT RESULT",
    "3. 07_6AB D1 VIMSOPAKA / D1 ASPECT REFERENCE PARENT RESULT",
    "4. CROSS-LAYER CONVERGENCE",
    "5. CROSS-LAYER CONFLICT / HOLD",
    "6. FINAL HOUSE DEEP OPERATION SENTENCE",
    "7. CLIENT READING",
    "8. FINAL HOUSE CHECK",
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


def read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object required: {path}")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as stream:
        for number, line in enumerate(stream, start=1):
            if not line.endswith("\n") or not line.strip():
                raise ValueError(f"invalid JSONL line {number}")
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"non-object JSONL line {number}")
            rows.append(value)
    return rows


def parse_live_packet(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or b"\x00" in raw or not raw.endswith(b"\n"):
        raise ValueError("packet byte encoding boundary")
    text = raw.decode("utf-8")
    if unicodedata.normalize("NFC", text) != text:
        raise ValueError("packet is not NFC")
    lines = text.splitlines()
    heading_positions: list[int] = []
    for heading in EXPECTED_HEADINGS:
        found = [index for index, line in enumerate(lines) if line == heading]
        if len(found) != 1:
            raise ValueError(f"heading cardinality: {heading}")
        heading_positions.append(found[0])
    if heading_positions != sorted(heading_positions):
        raise ValueError("heading order")
    if lines[-1] != "- Final sentence appears once = PASS":
        raise ValueError("final check terminator")

    values: dict[str, str] = {}
    spans: dict[str, dict[str, int]] = {}
    evidence: list[str] = []
    for slot, label in FIELD_LABELS.items():
        prefix = f"- {label} = "
        hits = [(index, line) for index, line in enumerate(lines) if line.startswith(prefix)]
        if len(hits) != 1:
            raise ValueError(f"field cardinality: {label}")
        index, raw_line = hits[0]
        values[slot] = raw_line[len(prefix):]
        spans[slot] = {"line_start": index + 1, "line_end": index + 1}
        evidence.append(raw_line)

    begin = lines.index("- 4AK Exact House Packet Begin")
    end = lines.index("- 4AK Exact House Packet End")
    packet_lines = lines[begin + 1:end]
    if len(packet_lines) != 36:
        raise ValueError("4AK packet field count")
    packet: dict[str, str] = {}
    for ordinal, raw_line in enumerate(packet_lines):
        if ordinal == 0:
            match = re.fullmatch(r"4AK_PACKET> ([0-9]{2}H)=APPLIED", raw_line)
            if match is None:
                raise ValueError("4AK applied header")
            packet["HOUSE_APPLIED"] = match.group(1)
        else:
            prefix = "4AK_PACKET> / "
            if not raw_line.startswith(prefix) or "=" not in raw_line[len(prefix):]:
                raise ValueError("4AK key/value shape")
            key, value = raw_line[len(prefix):].split("=", 1)
            if key in packet:
                raise ValueError("4AK duplicate key")
            packet[key] = value
    for slot, key in PACKET_MIRRORS.items():
        if packet.get(key) != values[slot]:
            raise ValueError(f"summary/4AK mismatch: {slot}")

    start = heading_positions[6]
    finish = heading_positions[7]
    final_rows = [(index, line) for index, line in enumerate(lines[start + 1:finish], start=start + 1) if line]
    if len(final_rows) != 1 or not final_rows[0][1].startswith("- "):
        raise ValueError("one final bullet record required")
    final_index, final_bullet = final_rows[0]
    if lines.count(final_bullet) != 1 or not final_bullet.endswith("."):
        raise ValueError("final bullet uniqueness/ending")
    spans["FINAL_RECORD"] = {"line_start": final_index + 1, "line_end": final_index + 1}
    evidence.append(final_bullet)
    return {
        "bytes": len(raw),
        "file_sha256": sha256_bytes(raw),
        "final_bullet": final_bullet,
        "final_value": final_bullet[2:],
        "slots": values,
        "spans": spans,
        "source_evidence_sha256": sha256_bytes(("\n".join(evidence) + "\n").encode("utf-8")),
    }


def render_independently(slots: dict[str, str]) -> str:
    house_match = re.fullmatch(r"([1-9]|1[0-2])H", slots["HOUSE_ID"])
    rank_match = re.fullmatch(r"([0-9]+) / Rupas (.+)", slots["BHAVA_BALA_RANK"])
    if house_match is None or rank_match is None:
        raise ValueError("house/rank grammar")
    replacements = dict(slots)
    replacements["HOUSE_DISPLAY"] = f"{int(house_match.group(1))}H"
    replacements["BHAVA_BALA_DISPLAY"] = f"Rank {rank_match.group(1)} Rupas {rank_match.group(2)}"
    return LOCKED_TEMPLATE.format_map(replacements)


def expected_route(occupants: str, lord: str) -> dict[str, str | bool]:
    if occupants == "EMPTY":
        return {
            "empty_confirmed": True,
            "selected_route": "HOUSE_LORD_ROUTE",
            "rejected_route": "OCCUPANT_ROUTE",
            "selected_value": lord,
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


def validate(runtime: Path, source_root: Path, router_path: Path) -> tuple[dict[str, Any], bytes]:
    failures: list[str] = []
    ledger: list[dict[str, Any]] = []
    try:
        router = read_object(router_path)
        run_manifest = read_object(runtime / "router_run_manifest.json")
        source_index = read_object(runtime / "source_index.json")
        records = read_jsonl(runtime / "router_records.jsonl")
        source_manifest = read_object(source_root / "references" / "personal-chart-240" / "manifest.json")

        if router.get("schema_version") != "KANI_SECOND_ACTION_ROUTER_V2":
            failures.append("router_schema")
        if router.get("field_map") != FIELD_LABELS:
            failures.append("router_field_map")
        if router.get("template", {}).get("id") != LOCKED_TEMPLATE_ID:
            failures.append("template_id")
        if router.get("template", {}).get("text") != LOCKED_TEMPLATE:
            failures.append("template_text")
        if run_manifest.get("schema_version") != "KANI_V10_ROUTER_RUN_V1":
            failures.append("run_schema")
        if run_manifest.get("status") != "PASS_TESTED_SCOPE_240":
            failures.append("run_status")
        if len(records) != 240 or len(source_index.get("records", [])) != 240:
            failures.append("record_count")
        if run_manifest.get("records", {}).get("sha256") != sha256_file(runtime / "router_records.jsonl"):
            failures.append("records_hash")
        if run_manifest.get("source_index", {}).get("sha256") != sha256_file(runtime / "source_index.json"):
            failures.append("source_index_hash")
        if run_manifest.get("router", {}).get("sha256") != sha256_file(router_path):
            failures.append("router_hash")
        if source_index.get("source_manifest_sha256") != sha256_file(source_root / "references" / "personal-chart-240" / "manifest.json"):
            failures.append("source_manifest_hash")
        if source_manifest.get("source_set_id") != router.get("authority", {}).get("source_set_id"):
            failures.append("source_set_id")

        source_rows = source_index.get("records", [])
        seen: set[str] = set()
        empty_count = 0
        conflict_count = 0
        for ordinal, (record, source_row) in enumerate(zip(records, source_rows), start=1):
            expected_dchart = DCHART_ORDER[(ordinal - 1) // 12]
            expected_house = HOUSE_ORDER[(ordinal - 1) % 12]
            expected_id = f"KANI-V10-{expected_dchart}-{expected_house}"
            local_failures: list[str] = []
            if record.get("record_id") != expected_id or expected_id in seen:
                local_failures.append("record_identity")
            seen.add(expected_id)
            if source_row.get("job_order") != ordinal or source_row.get("dchart") != expected_dchart or source_row.get("house_id") != expected_house:
                local_failures.append("source_index_order")
            relative = source_row.get("relative_path")
            if not isinstance(relative, str) or Path(relative).is_absolute() or ".." in Path(relative).parts:
                local_failures.append("source_path")
                relative = "INVALID"
            source_path = source_root / "references" / "personal-chart-240" / relative
            if source_path.is_symlink() or not source_path.is_file():
                local_failures.append("source_missing")
                raise ValueError(f"live source missing: {relative}")
            parsed = parse_live_packet(source_path)
            if source_row.get("bytes") != parsed["bytes"] or source_row.get("sha256") != parsed["file_sha256"]:
                local_failures.append("source_index_readback")
            source_meta = record.get("source", {})
            if not isinstance(source_meta, dict):
                local_failures.append("source_meta")
                source_meta = {}
            for key, expected in (
                ("relative_path", relative),
                ("file_bytes", parsed["bytes"]),
                ("file_sha256", parsed["file_sha256"]),
                ("source_evidence_sha256", parsed["source_evidence_sha256"]),
                ("field_and_final_line_spans", parsed["spans"]),
            ):
                if source_meta.get(key) != expected:
                    local_failures.append(f"source_{key}")
            slots = parsed["slots"]
            if record.get("slot_bindings", {}).get("TARGET_DCHART") != expected_dchart:
                local_failures.append("slot_dchart")
            normalized_house = f"H{int(slots['HOUSE_ID'][:-1]):02d}"
            if slots["TARGET_DCHART"] != expected_dchart or normalized_house != expected_house:
                local_failures.append("live_identity")
            expected_bindings = dict(slots)
            expected_bindings["HOUSE_DISPLAY"] = f"{int(slots['HOUSE_ID'][:-1])}H"
            rank = re.fullmatch(r"([0-9]+) / Rupas (.+)", slots["BHAVA_BALA_RANK"])
            if rank is None:
                local_failures.append("rank")
            else:
                expected_bindings["BHAVA_BALA_DISPLAY"] = f"Rank {rank.group(1)} Rupas {rank.group(2)}"
            if record.get("slot_bindings") != expected_bindings:
                local_failures.append("slot_bindings")
            route = expected_route(slots["OCCUPANT_FIELD"], slots["HOUSE_LORD_FIELD"])
            if record.get("route") != route:
                local_failures.append("route")
            empty_count += int(bool(route["empty_confirmed"]))
            conflict_count += int(slots["CONFLICT_HOLD_POINT"] != "NONE")
            rendered = render_independently(slots)
            if rendered != parsed["final_bullet"]:
                local_failures.append("live_exact_replay")
            if record.get("written_sentence") != rendered or record.get("source_sentence") != parsed["final_bullet"]:
                local_failures.append("record_sentence")
            if record.get("written_sentence_sha256") != sha256_bytes(rendered.encode("utf-8")):
                local_failures.append("written_hash")
            if record.get("source_sentence_sha256") != sha256_bytes(parsed["final_bullet"].encode("utf-8")):
                local_failures.append("source_sentence_hash")
            if record.get("template") != {"id": LOCKED_TEMPLATE_ID, "sha256": sha256_bytes(LOCKED_TEMPLATE.encode("utf-8"))}:
                local_failures.append("record_template")
            if record.get("boundary_test", {}).get("result") != "PASS":
                local_failures.append("boundary_result")
            if local_failures:
                failures.extend(f"{expected_id}:{failure}" for failure in local_failures)
            ledger.append({
                "independent_replay_result": "PASS" if not local_failures else "FAIL",
                "record_id": expected_id,
                "route": route["selected_route"],
                "schema_version": "KANI_V10_INDEPENDENT_REPLAY_RECORD_V1",
                "source_file_sha256": parsed["file_sha256"],
                "written_sentence_sha256": sha256_bytes(rendered.encode("utf-8")),
            })

        golden = next((record for record in records if record.get("record_id") == "KANI-V10-D6-H05"), None)
        if golden is None:
            failures.append("golden_missing")
        else:
            source = golden.get("source", {})
            slots = golden.get("slot_bindings", {})
            if not (
                source.get("file_sha256") == "50353b4a608b383026f7158f7fe915efc5cdb2e1a04747cc1ee90d9b78479e35"
                and slots.get("RASHI_SIGN") == "Mesha"
                and slots.get("OCCUPANT_FIELD") == "EMPTY"
                and slots.get("HOUSE_LORD_FIELD") == "Mars"
                and slots.get("HOUSE_LORD_POSITION") == "Mars 20:46:27 Mithuna Punarvasu P1"
                and golden.get("route", {}).get("selected_route") == "HOUSE_LORD_ROUTE"
                and sha256_bytes(golden.get("written_sentence", "")[2:].encode("utf-8")) == "c41650d60173e8041478e770cac711f56ed92f425ac897c83b3f5269d52e2467"
            ):
                failures.append("golden_D6_H05")

        if run_manifest.get("counts") != {
            "conflict_hold_point_non_none": conflict_count,
            "empty_house_lord_route": empty_count,
            "exact_sentence_replay": len(records),
            "occupied_route": len(records) - empty_count,
            "records": len(records),
            "summary_4ak_equalities": len(records) * len(PACKET_MIRRORS),
        }:
            failures.append("run_counts")
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        failures.append(f"exception:{type(exc).__name__}:{exc}")
        records = []
        empty_count = 0
        conflict_count = 0

    ledger_bytes = b"".join(compact_json(row) + b"\n" for row in ledger)
    report = {
        "counts": {
            "conflict_hold_point_non_none": conflict_count,
            "empty_house_lord_route": empty_count,
            "exact_replay": sum(row["independent_replay_result"] == "PASS" for row in ledger),
            "occupied_route": len(ledger) - empty_count,
            "records": len(ledger),
        },
        "failures": failures,
        "golden_D6_H05": "PASS" if "golden_D6_H05" not in failures and len(ledger) == 240 else "FAIL",
        "independent_ledger": {
            "bytes": len(ledger_bytes),
            "records": len(ledger),
            "sha256": sha256_bytes(ledger_bytes),
        },
        "live_source_readback": "PASS" if not failures else "FAIL",
        "producer_imported": False,
        "schema_version": "KANI_V10_INDEPENDENT_REPLAY_REPORT_V1",
        "status": "PASS" if not failures else "FAIL",
        "template_sha256": sha256_bytes(LOCKED_TEMPLATE.encode("utf-8")),
    }
    return report, ledger_bytes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("runtime_dir", type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--router", type=Path, default=DEFAULT_ROUTER)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if (args.report is None) != (args.ledger is None):
        raise SystemExit("--report and --ledger must be supplied together")

    report, ledger_bytes = validate(args.runtime_dir.resolve(), args.source_root.resolve(), args.router.resolve())
    if args.report is not None and args.ledger is not None:
        for path in (args.report, args.ledger):
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists() and not args.force:
                raise SystemExit(f"refusing to overwrite: {path}")
        args.ledger.write_bytes(ledger_bytes)
        args.report.write_bytes(canonical_json(report))
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Read and verify the byte-exact SC8 03 source embedded in OO2A3."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = SKILL_ROOT / "assets/sc8-03/07_3AB_CO2_First_p_Sc.zip"
ARCHIVE_SHA256 = "5790f1ef08aa231d4aae2e4cb1f6151a10183e1ca5ad9202959d36566c345e09"
ARCHIVE_SIZE = 321874
DCHARTS = [
    "D1", "D9", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D10",
    "D11", "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60",
]


def member_name(dchart: str) -> str:
    return f"07_3AB_{dchart}_CO2_First_p_Sc.txt"


EXPECTED_MEMBERS = {member_name(dchart) for dchart in DCHARTS}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_dchart(value: str) -> str:
    dchart = value.strip().upper()
    if dchart not in DCHARTS:
        raise SystemExit(f"Unsupported D-chart: {value}; D50 is VOID")
    return dchart


def normalize_house(value: str) -> int:
    token = value.strip().upper()
    if token.startswith("H"):
        token = token[1:]
    if not token.isdigit() or not 1 <= int(token) <= 12:
        raise SystemExit(f"Unsupported House: {value}; use H01~H12")
    return int(token)


def read_member(archive: zipfile.ZipFile, dchart: str) -> str:
    return archive.read(member_name(dchart)).decode("utf-8")


def house_extract(text: str, dchart: str, house: int) -> str:
    section_03a_start = text.find("03A-1. 1H~12H HOUSE TRANSFER STATUS TABLE")
    section_03a_end = text.find("03A-2. ENTITY TRANSFER TABLE", section_03a_start)
    if section_03a_start < 0 or section_03a_end < 0:
        raise SystemExit(f"{dchart}: 03A-1 source section not found")
    section_03a = text[section_03a_start:section_03a_end]
    row_match = re.search(rf"^- {house}H = .+$", section_03a, re.MULTILINE)
    if not row_match:
        raise SystemExit(f"{dchart} H{house:02d}: 03A-1 row not found")

    slot_marker = f"03B-{house}H. TARGET D-CHART {house}H FIRST INTEGRATION SLOT"
    slot_start = text.find(slot_marker)
    if slot_start < 0:
        raise SystemExit(f"{dchart} H{house:02d}: 03B slot not found")
    if house < 12:
        next_marker = f"03B-{house + 1}H. TARGET D-CHART {house + 1}H FIRST INTEGRATION SLOT"
    else:
        next_marker = "03B-13. FULL 12 HOUSE OUTPUT RULE"
    slot_end = text.find(next_marker, slot_start)
    if slot_end < 0:
        raise SystemExit(f"{dchart} H{house:02d}: 03B slot end not found")
    slot = text[slot_start:slot_end].rstrip()

    return "\n".join(
        [
            "SOURCE_CALL=$oo2a3",
            "SOURCE_LAYER=$rq-sc8-3ab",
            f"SOURCE_MEMBER={member_name(dchart)}",
            f"TARGET={dchart}-H{house:02d}",
            "EXTRACTION=EXACT_SOURCE_SUBSTRING_NO_NORMALIZATION",
            "",
            "03A_HOUSE_TRANSFER_ROW_BEGIN",
            row_match.group(0),
            "03A_HOUSE_TRANSFER_ROW_END",
            "",
            "03B_HOUSE_SLOT_BEGIN",
            slot,
            "03B_HOUSE_SLOT_END",
        ]
    )


def command_list() -> None:
    print("CALL_KEY=$oo2a3")
    print("SOURCE_LAYER=$rq-sc8-3ab")
    print(f"SOURCE_ARCHIVE={ARCHIVE.name}")
    print("MEMBER_COUNT=20")
    print("D50=VOID")
    for index, dchart in enumerate(DCHARTS, start=1):
        print(f"{index:02d}\t{dchart}\t{member_name(dchart)}")


def command_read(dchart_value: str, house_value: str | None) -> None:
    dchart = normalize_dchart(dchart_value)
    with zipfile.ZipFile(ARCHIVE) as archive:
        text = read_member(archive, dchart)
    if house_value is None:
        sys.stdout.write(text)
        return
    house = normalize_house(house_value)
    print(house_extract(text, dchart, house))


def command_export() -> None:
    with zipfile.ZipFile(ARCHIVE) as archive:
        for index, dchart in enumerate(DCHARTS, start=1):
            text = read_member(archive, dchart)
            print("━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"OO2A3_MEMBER_ORDER={index:02d}")
            print(f"D_CHART={dchart}")
            print(f"SOURCE_MEMBER={member_name(dchart)}")
            print("SOURCE_EXACT_COPY_BEGIN")
            sys.stdout.write(text)
            if not text.endswith("\n"):
                print()
            print("SOURCE_EXACT_COPY_END")


def command_verify() -> None:
    problems: list[str] = []
    if not ARCHIVE.is_file():
        raise SystemExit(f"Missing source archive: {ARCHIVE}")
    actual_sha = sha256_file(ARCHIVE)
    if actual_sha != ARCHIVE_SHA256:
        problems.append("ARCHIVE_SHA256_MISMATCH")
    if ARCHIVE.stat().st_size != ARCHIVE_SIZE:
        problems.append("ARCHIVE_SIZE_MISMATCH")

    slot_checks = 0
    with zipfile.ZipFile(ARCHIVE) as archive:
        names = {info.filename for info in archive.infolist() if not info.is_dir()}
        if names != EXPECTED_MEMBERS:
            problems.append("MEMBER_SET_MISMATCH")
        bad_crc = archive.testzip()
        if bad_crc is not None:
            problems.append(f"ZIP_CRC_FAILURE:{bad_crc}")

        for dchart in DCHARTS:
            name = member_name(dchart)
            if name not in names:
                continue
            text = read_member(archive, dchart)
            if "03A. TARGET RASHI/BHAVA TRANSFER AND CO-PRESENCE CHANGE CHECK" not in text:
                problems.append(f"{dchart}:MISSING_03A")
            if "03B. TARGET RASHI/BHAVA FIRST INTEGRATION" not in text:
                problems.append(f"{dchart}:MISSING_03B")
            for house in range(1, 13):
                try:
                    house_extract(text, dchart, house)
                    slot_checks += 1
                except SystemExit as exc:
                    problems.append(str(exc))

    result = {
        "status": "PASS" if not problems else "HOLD",
        "call_key": "$oo2a3",
        "source_layer": "$rq-sc8-3ab",
        "archive_sha256": actual_sha,
        "archive_size_bytes": ARCHIVE.stat().st_size,
        "member_count": len(EXPECTED_MEMBERS),
        "house_slot_checks": slot_checks,
        "expected_house_slot_checks": 240,
        "d50_status": "VOID",
        "problems": problems,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if problems:
        raise SystemExit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list")
    read_parser = subparsers.add_parser("read")
    read_parser.add_argument("--dchart", required=True)
    read_parser.add_argument("--house")
    subparsers.add_parser("export")
    subparsers.add_parser("verify")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "list":
        command_list()
    elif args.command == "read":
        command_read(args.dchart, args.house)
    elif args.command == "export":
        command_export()
    elif args.command == "verify":
        command_verify()


if __name__ == "__main__":
    main()

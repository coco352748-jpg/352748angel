#!/usr/bin/env python3
"""Read and verify the byte-exact SC8 04 source embedded in OO2A4."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = SKILL_ROOT / "assets/sc8-04/07_4AB_VeDic_CO2_Sc_.zip"
ARCHIVE_SHA256 = "b1b2a692695763d9f1648ddfd6e993d2f8eaa5290350c191530ad1c977433a91"
ARCHIVE_SIZE = 116781
UNCOMPRESSED_SIZE = 392309
DCHARTS = [
    "D1", "D9", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D10",
    "D11", "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60",
]


def member_name(dchart: str) -> str:
    return f"07_4AB_{dchart}_VeDic_CO2_Sc.txt"


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


def section_between(text: str, start_marker: str, end_marker: str, dchart: str) -> str:
    start = text.find(start_marker)
    end = text.find(end_marker, start + len(start_marker))
    if start < 0 or end < 0:
        raise SystemExit(f"{dchart}: source section not found: {start_marker}")
    return text[start:end]


def canonical_row(text: str, dchart: str, lane: str, house: int) -> str:
    if lane == "RASHI":
        section = section_between(
            text,
            f"{dchart} RASHI CANONICAL DATA INPUT",
            f"{dchart} RASHI CO-PRESENCE FIELDS",
            dchart,
        )
        pattern = rf"^- {house}H(?: [^=\n]+)? = .+$"
    else:
        section = section_between(
            text,
            f"{dchart} BHAVA CANONICAL DATA INPUT",
            f"{dchart} BHAVA CO-PRESENCE FIELDS",
            dchart,
        )
        pattern = rf"^- {house}H = .+$"
    match = re.search(pattern, section, re.MULTILINE)
    if not match:
        raise SystemExit(f"{dchart} H{house:02d}: {lane} canonical row not found")
    return match.group(0)


def co_field_blocks(text: str, dchart: str, lane: str, house: int) -> list[str]:
    start_marker = f"{dchart} {lane} CO-PRESENCE FIELDS"
    start = text.find(start_marker)
    if start < 0:
        raise SystemExit(f"{dchart}: {lane} co-presence section not found")

    if lane == "RASHI":
        end_candidates = [f"{dchart} BHAVA CANONICAL DATA INPUT"]
    else:
        end_candidates = [
            f"{dchart} BHAVA SINGLE FIELD / NOT CO-PRESENCE",
            "VOIDED PREVIOUS BHAVA SNAPSHOT RECORDS",
            f"{dchart} SPLIT VALIDATION",
        ]
    ends = [text.find(marker, start + len(start_marker)) for marker in end_candidates]
    ends = [value for value in ends if value >= 0]
    end = min(ends) if ends else len(text)
    lane_text = text[start:end]

    headers = list(re.finditer(r"^\[HYEWON_[^\n]+_CO_FIELD\]$", lane_text, re.MULTILINE))
    blocks: list[str] = []
    lane_label = "Rashi" if lane == "RASHI" else "Bhava"
    location_pattern = re.compile(
        rf"^- Location = {re.escape(dchart)} {lane_label} / {house}H(?:\s|$)",
        re.MULTILINE,
    )
    for index, header in enumerate(headers):
        block_end = headers[index + 1].start() if index + 1 < len(headers) else len(lane_text)
        block = lane_text[header.start():block_end]
        stop = re.search(
            rf"(?m)^{re.escape(dchart)} (?:RASHI |BHAVA )?"
            r"(?:OPERATING NOTE|SINGLE FIELD / NOT CO-PRESENCE|SUPPORT-ONLY FIELD|CHANGE LOG)$",
            block,
        )
        if stop:
            block = block[:stop.start()]
        block = block.rstrip()
        if location_pattern.search(block):
            blocks.append(block)
    return blocks


def house_extract(text: str, dchart: str, house: int) -> str:
    rashi_row = canonical_row(text, dchart, "RASHI", house)
    bhava_row = canonical_row(text, dchart, "BHAVA", house)
    rashi_blocks = co_field_blocks(text, dchart, "RASHI", house)
    bhava_blocks = co_field_blocks(text, dchart, "BHAVA", house)

    def render_blocks(blocks: list[str]) -> str:
        if not blocks:
            return "NO_MATCHING_CO_FIELD_BLOCK_IN_SOURCE"
        return "\n\n".join(blocks)

    return "\n".join(
        [
            "SOURCE_CALL=$oo2a4",
            "SOURCE_LAYER=$rq-sc8-4ab",
            f"SOURCE_MEMBER={member_name(dchart)}",
            f"TARGET={dchart}-H{house:02d}",
            "EXTRACTION=EXACT_SOURCE_SUBSTRING_NO_VALUE_NORMALIZATION",
            "",
            "RASHI_CANONICAL_ROW_BEGIN",
            rashi_row,
            "RASHI_CANONICAL_ROW_END",
            "",
            "RASHI_CO_PRESENCE_BLOCKS_BEGIN",
            render_blocks(rashi_blocks),
            "RASHI_CO_PRESENCE_BLOCKS_END",
            "",
            "BHAVA_CANONICAL_ROW_BEGIN",
            bhava_row,
            "BHAVA_CANONICAL_ROW_END",
            "",
            "BHAVA_CO_PRESENCE_BLOCKS_BEGIN",
            render_blocks(bhava_blocks),
            "BHAVA_CO_PRESENCE_BLOCKS_END",
        ]
    )


def command_list() -> None:
    print("CALL_KEY=$oo2a4")
    print("SOURCE_LAYER=$rq-sc8-4ab")
    print(f"SOURCE_ARCHIVE={ARCHIVE.name}")
    print("SOURCE_SCOPE=RASHI_BHAVA_VEDIC_CO2_CO_PRESENCE")
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
            print(f"OO2A4_MEMBER_ORDER={index:02d}")
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

    paired_house_checks = 0
    member_uncompressed_size = 0
    with zipfile.ZipFile(ARCHIVE) as archive:
        infos = [info for info in archive.infolist() if not info.is_dir()]
        names = {info.filename for info in infos}
        member_uncompressed_size = sum(info.file_size for info in infos)
        if names != EXPECTED_MEMBERS:
            problems.append("MEMBER_SET_MISMATCH")
        if member_uncompressed_size != UNCOMPRESSED_SIZE:
            problems.append("UNCOMPRESSED_SIZE_MISMATCH")
        bad_crc = archive.testzip()
        if bad_crc is not None:
            problems.append(f"ZIP_CRC_FAILURE:{bad_crc}")

        for dchart in DCHARTS:
            name = member_name(dchart)
            if name not in names:
                continue
            text = read_member(archive, dchart)
            for marker in (
                f"{dchart} RASHI CANONICAL DATA INPUT",
                f"{dchart} RASHI CO-PRESENCE FIELDS",
                f"{dchart} BHAVA CANONICAL DATA INPUT",
                f"{dchart} BHAVA CO-PRESENCE FIELDS",
            ):
                if marker not in text:
                    problems.append(f"{dchart}:MISSING:{marker}")
            for house in range(1, 13):
                try:
                    house_extract(text, dchart, house)
                    paired_house_checks += 1
                except SystemExit as exc:
                    problems.append(str(exc))

    result = {
        "status": "PASS" if not problems else "HOLD",
        "call_key": "$oo2a4",
        "source_layer": "$rq-sc8-4ab",
        "archive_sha256": actual_sha,
        "archive_size_bytes": ARCHIVE.stat().st_size,
        "uncompressed_size_bytes": member_uncompressed_size,
        "member_count": len(EXPECTED_MEMBERS),
        "paired_house_checks": paired_house_checks,
        "expected_paired_house_checks": 240,
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

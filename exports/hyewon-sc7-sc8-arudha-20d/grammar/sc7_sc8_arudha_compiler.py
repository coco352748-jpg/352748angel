#!/usr/bin/env python3
"""Fail-closed SC7 <-> SC8 Arudha synchronized-grammar analyzer.

The paired corpus contains two different source states: the SC7 monolith is a
later screenshot-master correction, while the SC8 PIKACHU members preserve an
earlier applied serialization.  This program extracts the common grammar and
checks every 20D x (12H + UL) coordinate.  It never converts a corrected value
back to an older value by chart-id lookup, and it emits no target-looking TXT
while a lossless inverse is not source-determined.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import re
import sys
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


D_ORDER = [
    "D1", "D9", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D10",
    "D11", "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60",
]
HOUSE_KEYS = [f"H{house:02d}" for house in range(1, 13)]
POINT_KEYS = HOUSE_KEYS + ["UL"]
INDEX_NAME = "06_1AB_AruDhA_12H_AppLieD_R_INDEX.txt"


class GrammarError(RuntimeError):
    pass


def expected_member_name(dchart: str) -> str:
    family = "1A" if dchart in {"D1", "D9"} else "1B"
    return f"06_{family}_{dchart}_AruDhA_12H_AppLieD_R.txt"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def split_sc7_container(path: Path) -> tuple[str, dict[str, str]]:
    text = read_text(path)
    pattern = re.compile(
        r"SOURCE_FILE_BEGIN\nFILE_NAME = (?P<name>[^\n]+)\n"
        r"(?P<body>.*?)SOURCE_FILE_END(?:\n|$)",
        re.DOTALL,
    )
    members: dict[str, str] = {}
    for match in pattern.finditer(text):
        name = match.group("name")
        if name in members:
            raise GrammarError(f"duplicate SC7 container member: {name}")
        members[name] = match.group("body")
    expected = {INDEX_NAME, *(expected_member_name(dchart) for dchart in D_ORDER)}
    if set(members) != expected:
        missing = sorted(expected - set(members))
        extra = sorted(set(members) - expected)
        raise GrammarError(f"SC7 container membership mismatch: missing={missing}, extra={extra}")
    return text, members


@contextlib.contextmanager
def source_tree(path: Path):
    if path.is_dir():
        yield path
        return
    if not path.is_file() or path.suffix.lower() != ".zip":
        raise GrammarError(f"expected SC8 directory or ZIP: {path}")
    with tempfile.TemporaryDirectory(prefix="sc7_sc8_arudha_") as temporary:
        root = Path(temporary)
        with zipfile.ZipFile(path) as archive:
            for member in archive.infolist():
                target = (root / member.filename).resolve()
                if root.resolve() != target and root.resolve() not in target.parents:
                    raise GrammarError(f"unsafe ZIP member: {member.filename}")
            archive.extractall(root)
        yield root


def locate_member(root: Path, name: str) -> Path:
    matches = [path for path in root.rglob(name) if path.is_file()]
    if len(matches) != 1:
        raise GrammarError(f"expected one SC8 member {name}, got {[str(path) for path in matches]}")
    return matches[0]


def section_end(text: str, start: int, candidates: Iterable[str]) -> int:
    positions = [text.find(candidate, start) for candidate in candidates]
    positions = [position for position in positions if position >= 0]
    return min(positions) if positions else len(text)


def parse_point_sections(text: str, dchart: str) -> dict[str, str]:
    if dchart == "D1":
        pattern = re.compile(
            r"(?m)^(?:(\d+)H\. D1 ARUDHA .* SURFACE SLOT / (?:APPLIED|HOLD)"
            r"|UL\. D1 UPAPADA LAGNA INDEPENDENT SLOT / APPLIED)$"
        )
        terminal = ["\n2. D1 ARUDHA FINAL CHECK"]
    else:
        pattern = re.compile(
            rf"(?m)^17-(?:(\d+)H|UL)\. {re.escape(dchart)} "
            rf"(?:\d+H|UL) .*APPLICATION PACKET.*$"
        )
        terminal = ["\nFINAL COMPLETION CHECK"]
    matches = list(pattern.finditer(text))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        key = "UL" if match.group(1) is None else f"H{int(match.group(1)):02d}"
        end = matches[index + 1].start() if index + 1 < len(matches) else section_end(text, match.end(), terminal)
        result[key] = text[match.start():end]
    if list(result) != POINT_KEYS:
        raise GrammarError(f"{dchart}: expected point order {POINT_KEYS}, got {list(result)}")
    return result


def field_occurrences(section: str) -> dict[tuple[str, int], str]:
    counts: Counter[str] = Counter()
    result: dict[tuple[str, int], str] = {}
    for line in section.splitlines():
        match = re.match(r"^- 《([^》]+)》 = (.*)$", line)
        if not match:
            continue
        label, value = match.group(1), match.group(2)
        counts[label] += 1
        result[(label, counts[label])] = value
    return result


def unique_fields(section: str) -> dict[str, str]:
    rows = field_occurrences(section)
    counts = Counter(label for label, _ in rows)
    return {label: value for (label, _), value in rows.items() if counts[label] == 1}


def new_check_table() -> dict[str, dict[str, int | str]]:
    return {}


def record_check(table: dict[str, dict[str, int | str]], name: str, passed: bool) -> None:
    row = table.setdefault(name, {"tested": 0, "passed": 0, "failed": 0, "status": "HOLD"})
    row["tested"] = int(row["tested"]) + 1
    key = "passed" if passed else "failed"
    row[key] = int(row[key]) + 1
    row["status"] = "PASS" if int(row["failed"]) == 0 else "HOLD"


def validate_profile(documents: dict[str, str], profile_name: str) -> dict[str, Any]:
    checks = new_check_table()
    failures: list[dict[str, Any]] = []
    for dchart in D_ORDER:
        sections = parse_point_sections(documents[dchart], dchart)
        record_check(checks, "POINT_COUNT_12H_PLUS_UL", list(sections) == POINT_KEYS)
        if dchart == "D1":
            for house in range(1, 13):
                fields = unique_fields(sections[f"H{house:02d}"])
                expected_pada = "AL / A1" if house == 1 else f"A{house}"
                passed = fields.get("Arudha Pada") == expected_pada
                record_check(checks, "D1_HOUSE_TO_PADA_MAP", passed)
                if not passed:
                    failures.append({"dchart": dchart, "house": house, "rule": "D1_HOUSE_TO_PADA_MAP"})
            a12 = unique_fields(sections["H12"])
            passed = (
                a12.get("Application Status") == "HOLD"
                and a12.get("Use Decision") == "HOLD_A12_INDEPENDENT_NOT_VISIBLE"
            )
            record_check(checks, "A12_HOLD_PRESERVATION", passed)
            ul = unique_fields(sections["UL"])
            passed = ul.get("Special Pada") == "UL" and ul.get("Application Status") == "APPLY_AS_UL_SURFACE"
            record_check(checks, "UL_INDEPENDENT", passed)
            continue

        for house in range(1, 13):
            fields = unique_fields(sections[f"H{house:02d}"])
            expected_point = "D-AL" if house == 1 else f"D-A{house}"
            passed = (
                fields.get("Relevant Arudha Point") == expected_point
                and fields.get("Source House of Pada") == f"{house}H"
            )
            record_check(checks, "TARGET_HOUSE_TO_POINT_MAP", passed)
            if not passed:
                failures.append({"dchart": dchart, "house": house, "rule": "TARGET_HOUSE_TO_POINT_MAP"})
            if house == 12:
                continue
            sign = fields.get("Arudha Sign")
            landing_house = fields.get("Arudha House From Target D-Chart Lagna")
            passed = (
                fields.get("Pada Landing Sign") == sign
                and fields.get("Pada Landing House From Lagna") == landing_house
                and fields.get("Landing House Surface Channel") == f"{sign} / {landing_house}"
            )
            record_check(checks, "LANDING_DUPLICATION", passed)
            if not passed:
                failures.append({"dchart": dchart, "house": house, "rule": "LANDING_DUPLICATION"})
            expected_status = "SAME_HOUSE" if landing_house == f"{house}H" else "DIFFERENT_HOUSE"
            passed = fields.get("Source-Landing Status") == expected_status
            record_check(checks, "SOURCE_LANDING_STATUS", passed)
            if not passed:
                failures.append({"dchart": dchart, "house": house, "rule": "SOURCE_LANDING_STATUS"})

        a12 = unique_fields(sections["H12"])
        passed = (
            a12.get("Point Source Status") == "HOLD_A12_INDEPENDENT_NOT_VISIBLE"
            and a12.get("Use Decision") == "HOLD"
        )
        record_check(checks, "A12_HOLD_PRESERVATION", passed)
        ul = unique_fields(sections["UL"])
        passed = (
            ul.get("Special Point") == "D-UL"
            and ul.get("Source House of Pada") == "UL_LINK"
            and "separate" in ul.get("A7/UL Separation", "")
        )
        record_check(checks, "UL_INDEPENDENT", passed)

    overall = "PASS" if not failures and all(row["status"] == "PASS" for row in checks.values()) else "HOLD"
    return {"profile": profile_name, "status": overall, "checks": checks, "failures": failures}


def probe_template(path: Path, expected_profile: str, applied_documents: Iterable[str]) -> dict[str, Any]:
    raw = path.read_bytes()
    text = raw.decode("utf-8-sig")
    placeholders = re.findall(r"<[^>\n]+>", text)
    fields = re.findall(r"《([^》]+)》\s*=", text)
    applied = list(applied_documents)
    return {
        "filename": path.name,
        "expected_profile": expected_profile,
        "sha256": sha256_bytes(raw),
        "size_bytes": len(raw),
        "line_count": len(text.splitlines()),
        "placeholder_occurrences": len(placeholders),
        "unique_placeholders": len(set(placeholders)),
        "field_rows": len(fields),
        "unique_field_labels": len(set(fields)),
        "byte_equal_to_any_applied_document": any(text == document for document in applied),
        "role": "TYPED_GRAMMAR_SPECIFICATION_NOT_BYTE_SKELETON",
    }


def compare_corpus(
    sc7_source: Path,
    sc8_root: Path,
    template_d1: Path | None,
    template_target: Path | None,
    include_point_details: bool,
) -> dict[str, Any]:
    container_text, members = split_sc7_container(sc7_source)
    sc7_documents = {
        dchart: members[expected_member_name(dchart)].rstrip("\n")
        for dchart in D_ORDER
    }
    sc8_documents: dict[str, str] = {}
    document_rows: list[dict[str, Any]] = []
    for dchart in D_ORDER:
        name = expected_member_name(dchart)
        path = locate_member(sc8_root, name)
        target_text = read_text(path)
        sc8_documents[dchart] = target_text
        source_candidate = sc7_documents[dchart]
        document_rows.append({
            "dchart": dchart,
            "sc7_container_member": name,
            "sc8_file": name,
            "sc7_member_sha256_after_wrapper_newline_normalization": sha256_bytes(source_candidate.encode("utf-8")),
            "sc8_file_sha256": sha256_file(path),
            "sc7_line_count": len(source_candidate.splitlines()),
            "sc8_line_count": len(target_text.splitlines()),
            "byte_equal_after_wrapper_newline_normalization": source_candidate.encode("utf-8") == path.read_bytes(),
        })

    label_counts: dict[str, Counter[str]] = {}
    point_rows: list[dict[str, Any]] = []
    field_totals: Counter[str] = Counter()
    schema_passed = 0
    exact_points = 0
    for dchart in D_ORDER:
        source_sections = parse_point_sections(sc7_documents[dchart], dchart)
        target_sections = parse_point_sections(sc8_documents[dchart], dchart)
        for point in POINT_KEYS:
            source_fields = field_occurrences(source_sections[point])
            target_fields = field_occurrences(target_sections[point])
            source_keys, target_keys = set(source_fields), set(target_fields)
            schema_equal = source_keys == target_keys
            schema_passed += int(schema_equal)
            different: list[dict[str, Any]] = []
            source_only = sorted(source_keys - target_keys)
            target_only = sorted(target_keys - source_keys)
            for field_key in sorted(source_keys | target_keys):
                label = field_key[0]
                stats = label_counts.setdefault(label, Counter())
                if field_key not in source_fields:
                    kind = "target_only"
                elif field_key not in target_fields:
                    kind = "source_only"
                elif source_fields[field_key] == target_fields[field_key]:
                    kind = "exact"
                else:
                    kind = "different"
                stats[kind] += 1
                field_totals[kind] += 1
                if kind == "different":
                    row = {"field": label, "occurrence": field_key[1]}
                    if include_point_details:
                        row.update({"sc7": source_fields[field_key], "sc8": target_fields[field_key]})
                    different.append(row)
            point_exact = schema_equal and not different
            exact_points += int(point_exact)
            point_rows.append({
                "dchart": dchart,
                "point": point,
                "schema_equal": schema_equal,
                "field_count": len(source_keys | target_keys),
                "different_field_count": len(different),
                "different_fields": different,
                "source_only_fields": [f"{label}#{occurrence}" for label, occurrence in source_only],
                "target_only_fields": [f"{label}#{occurrence}" for label, occurrence in target_only],
                "exact_point": point_exact,
            })

    source_validation = validate_profile(sc7_documents, "SC7_SCREENSHOT_MASTER")
    target_validation = validate_profile(sc8_documents, "SC8_PIKACHU_HISTORICAL")
    template_rows = []
    if template_d1:
        template_rows.append(probe_template(template_d1, "D1_06A_TYPED", [sc7_documents["D1"], sc8_documents["D1"]]))
    if template_target:
        target_docs = [document for dchart, document in sc7_documents.items() if dchart != "D1"]
        target_docs += [document for dchart, document in sc8_documents.items() if dchart != "D1"]
        template_rows.append(probe_template(template_target, "TARGET_06B_TYPED", target_docs))

    point_total = len(D_ORDER) * len(POINT_KEYS)
    house_total = len(D_ORDER) * len(HOUSE_KEYS)
    document_matches = sum(row["byte_equal_after_wrapper_newline_normalization"] for row in document_rows)
    mismatch_points = point_total - exact_points
    holds = [
        "HOLD-ARU-SOURCE-STATE-001",
        "HOLD-ARU-D1-DEGREE-LOSS-001",
        "HOLD-ARU-CORRECTED-VALUES-001",
        "HOLD-ARU-TEMPLATE-SKELETON-001",
        "HOLD-ARU-INVERSE-CARRIER-001",
        "HOLD-ARU-EXACT-RENDERER-001",
    ]
    report: dict[str, Any] = {
        "schema_version": "SC7_SC8_ARUDHA_COVERAGE_V1",
        "grammar_call": "$rq-sc7-sc8-arudha-grammar",
        "status": "HOLD",
        "status_reason": (
            "The common 20D Arudha grammar is structurally verified, but SC7 is a later screenshot-master "
            "state and SC8 is an earlier PIKACHU state. Corrected point values are not recoverable from the older text."
        ),
        "source_snapshot": {
            "sc7_file": sc7_source.name,
            "sc7_sha256": sha256_file(sc7_source),
            "sc7_container_members": len(members),
            "sc7_index_members": 1,
            "sc7_chart_members": 20,
            "sc8_chart_members": 20,
        },
        "coordinate_coverage": {
            "dcharts": len(D_ORDER),
            "houses_per_dchart": 12,
            "house_coordinates_requested": house_total,
            "house_coordinates_bound": house_total,
            "ul_coordinates_requested": len(D_ORDER),
            "ul_coordinates_bound": len(D_ORDER),
            "total_points_requested": point_total,
            "total_points_bound": point_total,
            "missing_points": 0,
            "status": "PASS",
        },
        "common_grammar_validation": {
            "sc7": source_validation,
            "sc8": target_validation,
            "status": "PASS" if source_validation["status"] == target_validation["status"] == "PASS" else "HOLD",
        },
        "paired_point_comparison": {
            "points_compared": point_total,
            "point_field_schema_equal": schema_passed,
            "exact_points": exact_points,
            "different_points": mismatch_points,
            "field_occurrences_compared": sum(field_totals.values()),
            "exact_field_occurrences": field_totals["exact"],
            "different_field_occurrences": field_totals["different"],
            "source_only_field_occurrences": field_totals["source_only"],
            "target_only_field_occurrences": field_totals["target_only"],
            "status": "HOLD" if mismatch_points else "PASS",
        },
        "field_difference_counts": {
            label: dict(sorted(counter.items()))
            for label, counter in sorted(label_counts.items())
            if counter.get("different") or counter.get("source_only") or counter.get("target_only")
        },
        "document_byte_comparison": {
            "documents_compared": len(document_rows),
            "byte_equal_documents": document_matches,
            "different_documents": len(document_rows) - document_matches,
            "status": "PASS" if document_matches == len(document_rows) else "HOLD",
        },
        "templates": template_rows,
        "exact_invariants": {
            "forward_sc7_to_sc8": {"requested_points": point_total, "passed": 0, "held": point_total, "status": "HOLD"},
            "reverse_sc8_to_sc7": {"requested_points": point_total, "passed": 0, "held": point_total, "status": "HOLD"},
            "reverse_forward": {"requested_points": point_total, "passed": 0, "held": point_total, "status": "HOLD"},
            "forward_reverse": {"requested_points": point_total, "passed": 0, "held": point_total, "status": "HOLD"},
            "reason": "No source-backed rule converts corrected SC7 values to the older SC8 values or restores corrected values from SC8.",
        },
        "acceptance_checks": {
            "manual_corrections": {"observed": 0, "required": 0, "status": "PASS"},
            "chart_id_exception_rules": {"observed": 0, "required": 0, "status": "PASS"},
            "unexplained_sc8_output_elements": {"observed": "historical value state and fixed-profile rows", "required": 0, "status": "HOLD"},
            "unrecovered_sc7_input_elements": {"observed": "corrected degrees/positions and container index state", "required": 0, "status": "HOLD"},
            "overall": "HOLD",
        },
        "blocking_holds": holds,
        "no_output_txt_emitted": True,
        "documents": document_rows,
        "point_mismatches": [row for row in point_rows if not row["exact_point"]],
    }
    if include_point_details:
        report["points"] = point_rows
    return report


def source_only_report(
    sc7_source: Path,
    template_d1: Path | None,
    template_target: Path | None,
) -> dict[str, Any]:
    _, members = split_sc7_container(sc7_source)
    documents = {dchart: members[expected_member_name(dchart)].rstrip("\n") for dchart in D_ORDER}
    validation = validate_profile(documents, "SC7_SCREENSHOT_MASTER")
    templates = []
    if template_d1:
        templates.append(probe_template(template_d1, "D1_06A_TYPED", [documents["D1"]]))
    if template_target:
        templates.append(probe_template(template_target, "TARGET_06B_TYPED", [documents[d] for d in D_ORDER if d != "D1"]))
    return {
        "schema_version": "SC7_SC8_ARUDHA_COVERAGE_V1",
        "grammar_call": "$rq-sc7-sc8-arudha-grammar",
        "status": "HOLD",
        "status_reason": "SC7 structural projection passes, but no SC8 acceptance target was supplied to select an exact historical renderer.",
        "coordinate_coverage": {"total_points_bound": 260, "status": "PASS"},
        "common_grammar_validation": {"sc7": validation, "status": validation["status"]},
        "templates": templates,
        "no_output_txt_emitted": True,
    }


def build_cli(direction: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"SC7/SC8 Arudha {direction} fail-closed grammar executor")
    parser.add_argument("--sc7-source", type=Path, required=True, help="07_6AB_AruDha_Sc.txt integrated SC7 source")
    parser.add_argument("--sc8-reference-root", type=Path, help="SC8 Arudha directory or ZIP")
    parser.add_argument("--template-d1", type=Path, help="06A D1 typed template")
    parser.add_argument("--template-target", type=Path, help="06B Target-D typed template")
    parser.add_argument("--output", type=Path, help="write JSON here; stdout when omitted")
    parser.add_argument("--include-point-details", action="store_true")
    parser.add_argument("--allow-hold", action="store_true", help="return zero while preserving status=HOLD")
    return parser


def run(direction: str, argv: list[str] | None = None) -> int:
    args = build_cli(direction).parse_args(argv)
    try:
        if direction == "reverse" and not args.sc8_reference_root:
            raise GrammarError("reverse requires --sc8-reference-root")
        if args.sc8_reference_root:
            with source_tree(args.sc8_reference_root) as root:
                result = compare_corpus(
                    args.sc7_source,
                    root,
                    args.template_d1,
                    args.template_target,
                    args.include_point_details,
                )
        else:
            result = source_only_report(args.sc7_source, args.template_d1, args.template_target)
        result["direction"] = "SC7_TO_SC8" if direction == "forward" else "SC8_TO_SC7"
        result["exact_renderer_status"] = "HOLD"
        result["status"] = "HOLD"
        result["no_output_txt_emitted"] = True
    except (GrammarError, OSError, UnicodeError, zipfile.BadZipFile) as exc:
        result = {
            "direction": "SC7_TO_SC8" if direction == "forward" else "SC8_TO_SC7",
            "status": "HOLD",
            "error": str(exc),
            "no_output_txt_emitted": True,
        }
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        sys.stdout.write(payload)
    return 0 if result.get("status") == "PASS" or args.allow_hold else 2


if __name__ == "__main__":
    selected = "forward"
    if len(sys.argv) > 1 and sys.argv[1] in {"forward", "reverse"}:
        selected = sys.argv.pop(1)
    raise SystemExit(run(selected))

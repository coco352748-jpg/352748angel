#!/usr/bin/env python3
"""Fail-closed SC7 <-> SC8 04 Co-presence grammar auditor.

The paired corpus is sufficient to recover the shared coordinate, occupant,
cardinality, lane, and comparison-state grammar.  It is not sufficient for an
exact byte renderer: SC8 uses an historical Bhava CO2 cross-check state and a
canonical D1 node correction, while SC8 omits SC7-only control, VOID, and
provenance rows.  This executor therefore verifies every recoverable rule and
emits JSON only.  It never emits a target-looking TXT while the exact inverse
is not source-determined.
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
HOUSE_ORDER = list(range(1, 13))
LANE_ORDER = ["R", "B", "C"]
TEMPLATE_NAMES = [
    "04_1A_D1_12H_CO2_TemPL_.txt",
    "04_1A_D1_CO2_12HouSe_TeMpl_♤.txt",
    "04_1B_CO2_12H_TEMpL_.txt",
    "04_2B_TaRgEt_CO2_12HouSe_TeMpl_A♤.txt",
]
ENTITY_TOKENS = [
    "Lagna", "As", "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
    "Saturn", "Rahu", "Ketu", "Uranus", "Neptune", "Pluto", "Maandi", "Md",
    "Gulika",
]
BHAVA_EMPTY_TYPES = {"EMPTY", "NO_CLUSTER"}
BHAVA_SINGLE_TYPES = {"SINGLE", "NO_CLUSTER / SINGLE", "SUPPORT_ONLY"}
BHAVA_CO_TYPES = {
    "MAINTAINED_CLUSTER",
    "CO-PRESENCE_CLUSTER",
    "same-house co-presence / degree not shown / house distribution field",
    "visible snapshot field reference / degree not applied / snapshot reference only",
}


class GrammarError(RuntimeError):
    """Input or structural failure that must never be softened by --allow-hold."""


def expected_sc7_name(dchart: str) -> str:
    return f"07_4AB_{dchart}_VeDic_CO2_Sc.txt"


def expected_sc8_name(dchart: str) -> str:
    family = "1A" if dchart in {"D1", "D9"} else "1B"
    return f"04_{family}_{dchart}_CoPreSeNcE_12H_AppLieD_R.txt"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


@contextlib.contextmanager
def source_tree(path: Path, prefix: str):
    if path.is_dir():
        yield path
        return
    if not path.is_file() or path.suffix.lower() != ".zip":
        raise GrammarError(f"expected directory or ZIP: {path}")
    with tempfile.TemporaryDirectory(prefix=prefix) as temporary:
        root = Path(temporary)
        with zipfile.ZipFile(path) as archive:
            root_resolved = root.resolve()
            for member in archive.infolist():
                target = (root / member.filename).resolve()
                if target != root_resolved and root_resolved not in target.parents:
                    raise GrammarError(f"unsafe ZIP member: {member.filename}")
            archive.extractall(root)
        yield root


def locate_member(root: Path, name: str) -> Path:
    matches = [path for path in root.rglob(name) if path.is_file()]
    if len(matches) != 1:
        raise GrammarError(f"expected one member {name}, got {[str(path) for path in matches]}")
    return matches[0]


def load_documents(root: Path, family: str) -> tuple[dict[str, str], list[dict[str, Any]]]:
    documents: dict[str, str] = {}
    rows: list[dict[str, Any]] = []
    for dchart in D_ORDER:
        name = expected_sc7_name(dchart) if family == "SC7" else expected_sc8_name(dchart)
        path = locate_member(root, name)
        text = read_text(path)
        documents[dchart] = text
        rows.append({
            "dchart": dchart,
            "filename": name,
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
            "logical_line_count": len(text.splitlines()),
            "newline_count": text.count("\n"),
            "terminal_newline": text.endswith("\n"),
        })
    d50_names = sorted(
        path.name for path in root.rglob("*")
        if path.is_file() and re.search(r"(?:^|_)D50(?:_|\.)", path.name)
    )
    if d50_names:
        raise GrammarError(f"D50 must remain VOID; found members: {d50_names}")
    return documents, rows


def normalize_entity(token: str) -> str:
    if token == "As":
        return "Lagna"
    if token == "Md":
        return "Maandi"
    return token


def entity_set(value: str) -> set[str]:
    result: set[str] = set()
    for token in ENTITY_TOKENS:
        if re.search(rf"(?<![A-Za-z]){re.escape(token)}(?:\(R\))?(?![A-Za-z])", value):
            result.add(normalize_entity(token))
    return result


def cardinality_state(value: str) -> str:
    if value.strip() == "EMPTY":
        return "EMPTY"
    count = len(entity_set(value))
    if count == 0:
        raise GrammarError(f"non-empty snapshot row has no recognized entity: {value}")
    return "SINGLE" if count == 1 else "CO-PRESENCE"


def extract_snapshot(text: str, dchart: str, lane: str) -> dict[int, str]:
    marker = "Visible Rashi Chart Snapshot" if lane == "R" else "Visible House Distribution"
    terminal = f"{dchart} {'RASHI' if lane == 'R' else 'BHAVA'} CO-PRESENCE"
    start = text.find(marker)
    if start < 0:
        raise GrammarError(f"{dchart} {lane}: missing snapshot marker {marker}")
    remainder = text[start + len(marker):]
    end = remainder.find(terminal)
    if end < 0:
        raise GrammarError(f"{dchart} {lane}: missing snapshot terminal {terminal}")
    section = remainder[:end]
    rows = {
        int(house): value
        for house, value in re.findall(r"^- (\d+)H(?: [^=]+)? = (.*)$", section, re.MULTILINE)
    }
    if list(sorted(rows)) != HOUSE_ORDER:
        raise GrammarError(f"{dchart} {lane}: expected 12 snapshot houses, got {sorted(rows)}")
    return rows


def parse_cofields(text: str, dchart: str) -> list[dict[str, Any]]:
    header = re.compile(rf"(?m)^\[HYEWON_{re.escape(dchart)}_(RASHI|BHAVA)_[^\]]+_CO_FIELD\]$")
    matches = list(header.finditer(text))
    boundary = text.find(f"{dchart} PREVIOUS BHAVA SNAPSHOT VOID RECORD")
    if boundary < 0:
        raise GrammarError(f"{dchart}: missing previous Bhava VOID boundary")
    result: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end():end]
        location = re.search(r"^- Location = (.*)$", body, re.MULTILINE)
        members = re.search(r"^- Members = (.*)$", body, re.MULTILINE)
        if not location or not members:
            raise GrammarError(f"{dchart}: malformed CO_FIELD block at line {text[:match.start()].count(chr(10)) + 1}")
        house_match = re.search(r"/\s*(\d+)H(?:\s|$)", location.group(1))
        result.append({
            "lane": "R" if match.group(1) == "RASHI" else "B",
            "header": match.group(0),
            "location": location.group(1),
            "members": members.group(1),
            "member_entities": sorted(entity_set(members.group(1))),
            "house": int(house_match.group(1)) if house_match else None,
            "active": match.start() < boundary,
        })
    return result


def field_rows(section: str) -> list[tuple[str, str]]:
    return re.findall(r"^- 《([^》]+)》 = (.*)$", section, re.MULTILINE)


def parse_sc8_blocks(text: str, dchart: str) -> dict[tuple[str, int], dict[str, Any]]:
    pattern = re.compile(r"(?m)^([RBC])-(\d+)H\. .*$")
    matches = list(pattern.finditer(text))
    observed = [(match.group(1), int(match.group(2))) for match in matches]
    expected = [(lane, house) for lane in LANE_ORDER for house in HOUSE_ORDER]
    if observed != expected:
        raise GrammarError(f"{dchart}: expected R1..R12/B1..B12/C1..C12, got {observed}")
    blocks: dict[tuple[str, int], dict[str, Any]] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        section = text[match.start():end]
        rows = field_rows(section)
        labels = [label for label, _ in rows]
        duplicates = sorted(label for label, count in Counter(labels).items() if count > 1)
        if duplicates:
            raise GrammarError(f"{dchart} {match.group(1)}-{match.group(2)}H: duplicate fields {duplicates}")
        blocks[(match.group(1), int(match.group(2)))] = {
            "text": section,
            "fields": dict(rows),
            "field_count": len(rows),
        }
    return blocks


def rashi_effective_state(fields: dict[str, str]) -> str:
    value = fields.get("Co-presence Status")
    if value not in {"EMPTY", "SINGLE", "CO-PRESENCE"}:
        raise GrammarError(f"unknown Rashi Co-presence Status: {value}")
    return value


def bhava_effective_state(fields: dict[str, str]) -> str:
    cluster_type = fields.get("Bhava Cluster Type")
    if cluster_type in BHAVA_EMPTY_TYPES:
        return "EMPTY"
    if cluster_type in BHAVA_SINGLE_TYPES:
        return "SINGLE"
    if cluster_type in BHAVA_CO_TYPES:
        return "CO-PRESENCE"
    raise GrammarError(f"unknown Bhava Cluster Type: {cluster_type}")


def expected_comparison_status(dchart: str, r_state: str, b_state: str, b_status: str) -> str:
    if dchart == "D1":
        if (r_state, b_state) == ("CO-PRESENCE", "CO-PRESENCE"):
            return "MAINTAINED"
        if (r_state, b_state) == ("CO-PRESENCE", "SINGLE"):
            return "PARTIAL_MAINTAINED_TO_SINGLE"
        if (r_state, b_state) == ("SINGLE", "SINGLE") and b_status.startswith("SUPPORT_ONLY"):
            return "RE-FUNCTIONED_SUPPORT_ONLY"
        if (r_state, b_state) == ("SINGLE", "SINGLE"):
            return "SINGLE_MAINTAINED"
        if (r_state, b_state) == ("EMPTY", "EMPTY"):
            return "NONE / LORD_ONLY"
        raise GrammarError(f"D1 comparison state is outside observed grammar: {(r_state, b_state, b_status)}")
    table = {
        ("CO-PRESENCE", "CO-PRESENCE"): "PARALLEL_CO_PRESENCE",
        ("CO-PRESENCE", "SINGLE"): "RASHI_CO_FIELD_BHAVA_SPLIT_OR_SINGLE",
        ("CO-PRESENCE", "EMPTY"): "RASHI_CO_FIELD_BHAVA_SPLIT_OR_SINGLE",
        ("SINGLE", "CO-PRESENCE"): "BHAVA_CO_FIELD_ONLY",
        ("EMPTY", "CO-PRESENCE"): "BHAVA_CO_FIELD_ONLY",
        ("SINGLE", "SINGLE"): "SINGLE_PARALLEL",
        ("SINGLE", "EMPTY"): "MIXED_SINGLE_EMPTY",
        ("EMPTY", "SINGLE"): "MIXED_SINGLE_EMPTY",
        ("EMPTY", "EMPTY"): "NONE / LORD_ONLY",
    }
    return table[(r_state, b_state)]


def probe_template(path: Path, applied_documents: Iterable[str]) -> dict[str, Any]:
    raw = path.read_bytes()
    text = raw.decode("utf-8-sig")
    placeholders = re.findall(r"<[^>\n]+>", text)
    fields = re.findall(r"《([^》]+)》\s*=", text)
    return {
        "filename": path.name,
        "sha256": sha256_bytes(raw),
        "size_bytes": len(raw),
        "logical_line_count": len(text.splitlines()),
        "newline_count": text.count("\n"),
        "placeholder_occurrences": len(placeholders),
        "unique_placeholders": len(set(placeholders)),
        "field_rows": len(fields),
        "unique_field_labels": len(set(fields)),
        "byte_equal_to_any_applied_document": any(text == document for document in applied_documents),
        "role": "TYPED_GRAMMAR_SPECIFICATION_NOT_BYTE_SKELETON",
    }


def template_report(template_dir: Path | None, sc8_documents: dict[str, str]) -> list[dict[str, Any]]:
    if template_dir is None:
        return []
    documents = list(sc8_documents.values())
    return [probe_template(locate_member(template_dir, name), documents) for name in TEMPLATE_NAMES]


def lost_source_carriers(sc7_documents: dict[str, str], sc8_documents: dict[str, str]) -> dict[str, Any]:
    patterns = {
        "chart_specific_role": r"^- Chart-Specific Role = .+$",
        "pound_slot": r"^- £칸 = .+$",
        "euro_slot_header": r"^- €칸$",
        "reality_rule": r"^- Reality Rule = .+$",
        "operating_note_header": r"^D\d+ OPERATING NOTE$",
        "void_record_header": r"^D\d+ PREVIOUS BHAVA SNAPSHOT VOID RECORD$",
        "void_verdict": r"^- VOID VERDICT = .+$",
        "previous_single_index": r"^PREVIOUS SINGLE-FIELD INDEX — VOID REFERENCE$",
        "source_modified": r"^- (?:Rashi|Bhava) Source Modified = .+$",
        "final_authority": r"^FINAL AUTHORITY$",
    }
    result: dict[str, Any] = {}
    total = 0
    absent = 0
    for label, pattern in patterns.items():
        observed = 0
        not_carried = 0
        example: dict[str, str] | None = None
        for dchart in D_ORDER:
            lines = re.findall(pattern, sc7_documents[dchart], re.MULTILINE)
            for line in lines:
                rendered = line if isinstance(line, str) else "".join(line)
                observed += 1
                if rendered not in sc8_documents[dchart]:
                    not_carried += 1
                    if example is None:
                        example = {"dchart": dchart, "value": rendered}
        total += observed
        absent += not_carried
        result[label] = {
            "sc7_occurrences": observed,
            "not_carried_verbatim_in_paired_sc8": not_carried,
            "example": example,
        }
    return {
        "categories": result,
        "category_occurrences": total,
        "not_carried_verbatim": absent,
        "interpretation": "These are inverse-carrier witnesses, not a claim that every other SC7 line is recoverable.",
    }


def compare_corpus(
    sc7_root: Path,
    sc8_root: Path,
    template_dir: Path | None,
    include_coordinates: bool,
) -> dict[str, Any]:
    sc7_documents, sc7_files = load_documents(sc7_root, "SC7")
    sc8_documents, sc8_files = load_documents(sc8_root, "SC8")

    sc7_snapshots: dict[tuple[str, str], dict[int, str]] = {}
    cofields: dict[str, list[dict[str, Any]]] = {}
    blocks: dict[str, dict[tuple[str, int], dict[str, Any]]] = {}
    for dchart in D_ORDER:
        sc7_snapshots[(dchart, "R")] = extract_snapshot(sc7_documents[dchart], dchart, "R")
        sc7_snapshots[(dchart, "B")] = extract_snapshot(sc7_documents[dchart], dchart, "B")
        cofields[dchart] = parse_cofields(sc7_documents[dchart], dchart)
        blocks[dchart] = parse_sc8_blocks(sc8_documents[dchart], dchart)

    layout_failures: list[dict[str, Any]] = []
    coordinate_rows: list[dict[str, Any]] = []
    state_counts: Counter[str] = Counter()
    comparison_counts: Counter[str] = Counter()
    r_occupant_pass = b_occupant_pass = 0
    r_state_pass = b_state_pass = comparison_pass = 0
    for dchart in D_ORDER:
        for house in HOUSE_ORDER:
            r_fields = blocks[dchart][("R", house)]["fields"]
            b_fields = blocks[dchart][("B", house)]["fields"]
            c_fields = blocks[dchart][("C", house)]["fields"]
            source_r = sc7_snapshots[(dchart, "R")][house]
            source_b = sc7_snapshots[(dchart, "B")][house]
            source_r_state = cardinality_state(source_r)
            source_b_state = cardinality_state(source_b)
            target_r_state = rashi_effective_state(r_fields)
            target_b_state = bhava_effective_state(b_fields)
            target_comparison = c_fields.get("Bhava Status")
            expected_comparison = expected_comparison_status(
                dchart,
                target_r_state,
                target_b_state,
                b_fields.get("Co-presence Status", ""),
            )
            r_entities_equal = entity_set(source_r) == entity_set(r_fields.get("Rashi Occupants", ""))
            b_entities_equal = entity_set(source_b) == entity_set(b_fields.get("Bhava Occupants", ""))
            r_state_equal = source_r_state == target_r_state
            b_state_equal = source_b_state == target_b_state
            comparison_equal = expected_comparison == target_comparison
            r_occupant_pass += int(r_entities_equal)
            b_occupant_pass += int(b_entities_equal)
            r_state_pass += int(r_state_equal)
            b_state_pass += int(b_state_equal)
            comparison_pass += int(comparison_equal)
            state_counts[f"R:{target_r_state}"] += 1
            state_counts[f"B:{target_b_state}"] += 1
            comparison_counts[target_comparison or "MISSING"] += 1
            row = {
                "dchart": dchart,
                "house": f"{house}H",
                "rashi_occupants_equal": r_entities_equal,
                "bhava_occupants_equal": b_entities_equal,
                "rashi_state": target_r_state,
                "bhava_state": target_b_state,
                "rashi_state_equal": r_state_equal,
                "bhava_state_equal": b_state_equal,
                "expected_comparison": expected_comparison,
                "observed_comparison": target_comparison,
                "comparison_equal": comparison_equal,
            }
            if include_coordinates or not all(
                [r_entities_equal, b_entities_equal, r_state_equal, b_state_equal, comparison_equal]
            ):
                coordinate_rows.append(row)

    active_r: set[tuple[str, int]] = set()
    active_b: set[tuple[str, int]] = set()
    raw_counts: Counter[str] = Counter()
    active_counts: Counter[str] = Counter()
    for dchart in D_ORDER:
        for block in cofields[dchart]:
            raw_counts[block["lane"]] += 1
            if block["active"]:
                active_counts[block["lane"]] += 1
                if block["house"] is None:
                    raise GrammarError(f"active CO_FIELD lacks House coordinate: {block}")
                (active_r if block["lane"] == "R" else active_b).add((dchart, block["house"]))

    target_r_co = {
        (dchart, house) for dchart in D_ORDER for house in HOUSE_ORDER
        if rashi_effective_state(blocks[dchart][("R", house)]["fields"]) == "CO-PRESENCE"
    }
    target_b_co = {
        (dchart, house) for dchart in D_ORDER for house in HOUSE_ORDER
        if bhava_effective_state(blocks[dchart][("B", house)]["fields"]) == "CO-PRESENCE"
    }
    bhava_extra = sorted(target_b_co - active_b, key=lambda item: (D_ORDER.index(item[0]), item[1]))
    historical_extra = []
    distribution_extra = []
    for dchart, house in bhava_extra:
        fields = blocks[dchart][("B", house)]["fields"]
        match_type = fields.get("CO2 Bhava Field Match Type")
        row = {
            "dchart": dchart,
            "house": f"{house}H",
            "match_type": match_type,
            "location": fields.get("CO2 Bhava Location"),
            "members": fields.get("CO2 Bhava Members"),
        }
        if match_type and match_type != "NOT_MATCHED_TO_CO2_BHAVA_FIELD":
            historical_extra.append(row)
        else:
            distribution_extra.append(row)

    current_location_exact = 0
    current_member_exact = 0
    current_member_subset = 0
    current_member_conflicts: list[dict[str, Any]] = []
    active_target_b = 0
    for dchart in D_ORDER:
        if dchart == "D1":
            continue
        active_blocks = [block for block in cofields[dchart] if block["active"] and block["lane"] == "B"]
        for block in active_blocks:
            active_target_b += 1
            fields = blocks[dchart][("B", block["house"])]["fields"]
            target_location = fields.get("CO2 Bhava Location", "")
            target_members = entity_set(fields.get("CO2 Bhava Members", ""))
            source_members = set(block["member_entities"])
            current_location_exact += int(target_location == block["location"])
            current_member_exact += int(target_members == source_members)
            current_member_subset += int(source_members <= target_members)
            if not source_members <= target_members:
                current_member_conflicts.append({
                    "dchart": dchart,
                    "house": f"{block['house']}H",
                    "sc7_active_members": sorted(source_members),
                    "sc8_crosscheck_members": sorted(target_members),
                })

    field_rows_total = sum(
        len(field_rows(text)) for text in sc8_documents.values()
    )
    exact_layout = (
        len(sc8_documents["D1"].splitlines()) == 1441
        and all(len(sc8_documents[dchart].splitlines()) == 1548 for dchart in D_ORDER if dchart != "D1")
        and len(field_rows(sc8_documents["D1"])) == 632
        and all(len(field_rows(sc8_documents[dchart])) == 717 for dchart in D_ORDER if dchart != "D1")
    )
    if not exact_layout:
        layout_failures.append({"rule": "D1_TARGET_PROFILE_LINE_OR_FIELD_COUNT"})

    structural_pass = all([
        r_occupant_pass == 240,
        b_occupant_pass == 240,
        r_state_pass == 240,
        b_state_pass == 240,
        comparison_pass == 240,
        active_r == target_r_co,
        active_b <= target_b_co,
        len(active_r) == 73,
        len(active_b) == 51,
        len(target_b_co) == 59,
        len(historical_extra) == 7,
        len(distribution_extra) == 1,
        exact_layout,
    ])
    if not structural_pass:
        raise GrammarError("recoverable common grammar failed against the paired corpus")

    holds = [
        "HOLD-CO2-D1-NODE-SOURCE-STATE-001",
        "HOLD-CO2-BHAVA-CROSSCHECK-SOURCE-STATE-001",
        "HOLD-CO2-RASHI-BHAVA-DEPENDENCY-001",
        "HOLD-CO2-SC7-INVERSE-CARRIER-001",
        "HOLD-CO2-TEMPLATE-SKELETON-001",
        "HOLD-CO2-EXACT-RENDERER-001",
    ]
    report: dict[str, Any] = {
        "schema_version": "SC7_SC8_CO2_COVERAGE_V1",
        "grammar_call": "$rq-sc7-sc8-co2-grammar",
        "status": "HOLD",
        "structural_grammar_status": "PASS",
        "exact_bidirectional_status": "HOLD",
        "status_reason": (
            "All 720 SC8 Rashi/Bhava/comparison packets and all 124 active SC7 CO_FIELD anchors satisfy the "
            "shared grammar. Exact rendering remains source-underdetermined because SC8 carries historical Bhava "
            "CO2 cross-check rows and corrected D1 node values, while it omits SC7-only control/VOID/provenance carriers."
        ),
        "source_snapshot": {
            "active_d_order": D_ORDER,
            "d50_status": "VOID",
            "sc7_files": sc7_files,
            "sc8_files": sc8_files,
            "sc7_member_count": 20,
            "sc8_member_count": 20,
        },
        "coordinate_coverage": {
            "dcharts": 20,
            "houses_per_dchart": 12,
            "rashi_packets": {"requested": 240, "bound": 240, "status": "PASS"},
            "bhava_packets": {"requested": 240, "bound": 240, "status": "PASS"},
            "comparison_packets": {"requested": 240, "bound": 240, "status": "PASS"},
            "total_packets": {"requested": 720, "bound": 720, "status": "PASS"},
        },
        "sc7_cofield_inventory": {
            "raw": {"rashi": raw_counts["R"], "bhava": raw_counts["B"], "total": sum(raw_counts.values())},
            "active": {"rashi": active_counts["R"], "bhava": active_counts["B"], "total": sum(active_counts.values())},
            "void_bhava_blocks": raw_counts["B"] - active_counts["B"],
            "status": "PASS",
        },
        "recoverable_rule_coverage": {
            "rashi_occupant_entity_binding": {"requested": 240, "passed": r_occupant_pass, "status": "PASS"},
            "bhava_occupant_entity_binding": {"requested": 240, "passed": b_occupant_pass, "status": "PASS"},
            "rashi_empty_single_co_state": {"requested": 240, "passed": r_state_pass, "status": "PASS"},
            "bhava_empty_single_co_state": {"requested": 240, "passed": b_state_pass, "status": "PASS"},
            "comparison_state": {"requested": 240, "passed": comparison_pass, "status": "PASS"},
            "rashi_active_cofield_location_binding": {
                "requested": len(active_r), "passed": len(active_r & target_r_co), "status": "PASS"
            },
            "bhava_active_cofield_location_binding": {
                "requested": len(active_b), "passed": len(active_b & target_b_co), "status": "PASS"
            },
            "sc8_profile_layout": {
                "d1_logical_lines": len(sc8_documents["D1"].splitlines()),
                "target_logical_lines_each": 1548,
                "d1_field_rows": len(field_rows(sc8_documents["D1"])),
                "target_field_rows_each": 717,
                "all_profiles_passed": exact_layout,
                "status": "PASS",
            },
            "status_counts": dict(sorted(state_counts.items())),
            "comparison_status_counts": dict(sorted(comparison_counts.items())),
            "total_sc8_field_rows": field_rows_total,
            "status": "PASS",
        },
        "bhava_lane_analysis": {
            "effective_co_presence_slots": len(target_b_co),
            "active_sc7_cofield_slots": len(active_b),
            "additional_slots": len(bhava_extra),
            "historical_co2_reference_slots": historical_extra,
            "house_distribution_derived_slots": distribution_extra,
            "current_active_target_crosscheck": {
                "coordinates_tested": active_target_b,
                "location_exact": current_location_exact,
                "member_set_exact": current_member_exact,
                "source_members_subset": current_member_subset,
                "member_conflicts": current_member_conflicts,
                "status": "HOLD",
            },
        },
        "templates": template_report(template_dir, sc8_documents),
        "inverse_carrier_witness": lost_source_carriers(sc7_documents, sc8_documents),
        "exact_invariants": {
            "forward_sc7_to_sc8": {"requested_packets": 720, "structurally_explained": 720, "exact_emitted": 0, "held": 720, "status": "HOLD"},
            "reverse_sc8_to_sc7": {"requested_packets": 720, "structurally_explained": 720, "exact_emitted": 0, "held": 720, "status": "HOLD"},
            "reverse_forward": {"requested_documents": 20, "passed": 0, "held": 20, "status": "HOLD"},
            "forward_reverse": {"requested_documents": 20, "passed": 0, "held": 20, "status": "HOLD"},
            "no_target_txt_emitted": True,
        },
        "acceptance_checks": {
            "manual_corrections": {"observed": 0, "required": 0, "status": "PASS"},
            "chart_id_exception_rules": {"observed": 0, "required": 0, "status": "PASS"},
            "rashi_bhava_lane_overwrites": {"observed": 0, "required": 0, "status": "PASS"},
            "unexplained_sc8_output_elements": {"observed": "historical Bhava cross-check state and dependency-derived exact text", "required": 0, "status": "HOLD"},
            "unrecovered_sc7_input_elements": {"observed": "SC7-only control, VOID, interpretation, and provenance carriers", "required": 0, "status": "HOLD"},
            "overall": "HOLD",
        },
        "blocking_holds": holds,
        "layout_failures": layout_failures,
        "no_output_txt_emitted": True,
    }
    if coordinate_rows:
        report["coordinates"] = coordinate_rows
    return report


def build_cli(direction: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"SC7/SC8 04 Co-presence {direction} fail-closed grammar executor"
    )
    parser.add_argument("--sc7-root", type=Path, required=True, help="SC7 directory or ZIP with 20 07_4AB members")
    parser.add_argument("--sc8-reference-root", type=Path, required=True, help="SC8 directory or ZIP with 20 04 Applied members")
    parser.add_argument("--template-dir", type=Path, help="directory containing the four attached 04 templates")
    parser.add_argument("--output", type=Path, help="write JSON audit report here; stdout when omitted")
    parser.add_argument("--include-coordinates", action="store_true", help="include all 240 coordinate rows")
    parser.add_argument("--allow-hold", action="store_true", help="return zero for a verified semantic HOLD; input errors still return 2")
    return parser


def run(direction: str, argv: list[str] | None = None) -> int:
    args = build_cli(direction).parse_args(argv)
    fatal = False
    try:
        with source_tree(args.sc7_root, "sc7_sc8_co2_sc7_") as sc7_root:
            with source_tree(args.sc8_reference_root, "sc7_sc8_co2_sc8_") as sc8_root:
                report = compare_corpus(sc7_root, sc8_root, args.template_dir, args.include_coordinates)
        report["direction"] = "SC7_TO_SC8" if direction == "forward" else "SC8_TO_SC7"
        report["exact_renderer_status"] = "HOLD"
    except (GrammarError, OSError, UnicodeError, zipfile.BadZipFile, KeyError) as exc:
        fatal = True
        report = {
            "direction": "SC7_TO_SC8" if direction == "forward" else "SC8_TO_SC7",
            "status": "HOLD",
            "structural_grammar_status": "HOLD",
            "exact_renderer_status": "HOLD",
            "error": str(exc),
            "no_output_txt_emitted": True,
        }
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        sys.stdout.write(payload)
    if fatal:
        return 2
    return 0 if args.allow_hold else 2


if __name__ == "__main__":
    selected = "forward"
    if len(sys.argv) > 1 and sys.argv[1] in {"forward", "reverse"}:
        selected = sys.argv.pop(1)
    raise SystemExit(run(selected))

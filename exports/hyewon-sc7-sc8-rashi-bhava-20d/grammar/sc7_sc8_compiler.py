#!/usr/bin/env python3
"""Fail-closed SC7 <-> SC8 synchronized-grammar analyzer.

This module deliberately distinguishes a source-backed semantic projection from
an exact byte renderer.  It never fills missing values and it never silently
uses a chart id as an exception key.  When the supplied corpus is insufficient
for an exact inverse, the public executors return HOLD (exit code 2).
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
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


D_ORDER = [
    "D1", "D9", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D10",
    "D11", "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60",
]

NAKSHATRA_FORWARD = {
    "P.Phalguni": "Purva Phalguni",
    "U.Phalguni": "Uttara Phalguni",
    "P.Ashadha": "Purva Ashadha",
    "U.Ashadha": "Uttara Ashadha",
    "P.Bhadrapada": "Purva Bhadrapada",
    "U.Bhadrapada": "Uttara Bhadrapada",
    "Aridra": "Ardra",
    "Jyeshta": "Jyeshtha",
    "Dhanishta": "Dhanishtha",
}

ACTORS = [
    "Maandi visible as Md", "Maandi/Md", "Lagna", "As", "Sun", "Moon", "Mars",
    "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu", "Uranus",
    "Neptune", "Pluto", "Maandi",
]
ACTOR_RE = re.compile(
    r"(?:^|(?<= / )|(?<=, ))(" + "|".join(map(re.escape, ACTORS)) + r")(?:\(R\))?(?=\s|,|$)"
)
HOUSE_SET = set(range(1, 13))


class GrammarError(RuntimeError):
    pass


@dataclass(frozen=True)
class House:
    house: int
    sign: str | None
    raw: str
    actors: tuple[str, ...]
    state: str


@dataclass(frozen=True)
class CoordinateResult:
    d: str
    lane: str
    house: int
    source_state: str
    target_state: str
    sign_equal: bool | None
    actors_equal: bool
    source_actors: tuple[str, ...]
    target_actors: tuple[str, ...]
    core_status: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@contextlib.contextmanager
def source_tree(path: Path):
    """Yield an extracted source root from either a directory or an ALL ZIP."""
    if path.is_dir():
        yield path
        return
    if not path.is_file() or path.suffix.lower() != ".zip":
        raise GrammarError(f"expected a source directory or ZIP: {path}")
    with tempfile.TemporaryDirectory(prefix="sc7_sc8_grammar_") as temporary:
        root = Path(temporary)
        with zipfile.ZipFile(path) as archive:
            for member in archive.infolist():
                target = root / member.filename
                if target.resolve() != root and root not in target.resolve().parents:
                    raise GrammarError(f"unsafe ZIP member: {member.filename}")
            archive.extractall(root)
        yield root


def canonical_actor(name: str) -> str:
    name = name.replace("(R)", "").strip()
    if name == "As":
        return "Lagna"
    if name in {"Maandi", "Maandi/Md", "Maandi visible as Md"}:
        return "Maandi/Md"
    return name


def actor_names(value: str) -> tuple[str, ...]:
    if value.strip() in {"", "EMPTY", "NONE", "N.A."}:
        return ()
    names = tuple(canonical_actor(m.group(1)) for m in ACTOR_RE.finditer(value))
    if names:
        return names
    # D1 applied Rashi uses a comma list in some slots.
    comma_names = []
    for token in value.split(","):
        token = canonical_actor(token.strip())
        if token in {canonical_actor(x) for x in ACTORS}:
            comma_names.append(token)
    return tuple(comma_names)


def state_for(actors: Iterable[str], raw: str) -> str:
    actors = tuple(actors)
    support = [a for a in actors if a == "Maandi/Md" or "SUPPORT_ONLY" in raw]
    primary = [a for a in actors if a not in support]
    if not primary and support:
        return "SUPPORT_ONLY"
    if not primary:
        return "EMPTY"
    if len(primary) == 1:
        return "SINGLE+SUPPORT" if support else "SINGLE"
    return f"CO{len(primary)}" + ("+SUPPORT" if support else "")


def normalize_target_text(value: str) -> str:
    for source, target in NAKSHATRA_FORWARD.items():
        value = value.replace(source, target)
    return value


def section_between(text: str, start: str, end_candidates: Iterable[str]) -> str:
    if start not in text:
        raise GrammarError(f"missing section anchor: {start}")
    block = text.split(start, 1)[1]
    positions = [block.find(end) for end in end_candidates if end in block]
    return block[: min(p for p in positions if p >= 0)] if positions else block


def parse_sc7_rashi(text: str) -> dict[int, House]:
    block = section_between(
        text,
        "Visible Rashi Chart Snapshot",
        ["Visible D1 Rashi Planetary Positions", "Visible Planetary Positions"],
    )
    result: dict[int, House] = {}
    for line in block.splitlines():
        match = re.match(r"^- (\d+)H (\S+) = (.*)$", line)
        if not match:
            continue
        house, sign, raw = int(match.group(1)), match.group(2), match.group(3)
        actors = actor_names(raw)
        result[house] = House(house, sign, raw, actors, state_for(actors, raw))
    require_12(result, "SC7 Rashi")
    return result


def parse_sc7_bhava(text: str) -> dict[int, House]:
    block = section_between(text, "Visible House Distribution", ["Visible Bhava Structure"])
    result: dict[int, House] = {}
    for line in block.splitlines():
        match = re.match(r"^- (\d+)H = (.*)$", line)
        if not match:
            continue
        house, raw = int(match.group(1)), match.group(2)
        actors = actor_names(raw)
        result[house] = House(house, None, raw, actors, state_for(actors, raw))
    require_12(result, "SC7 Bhava")
    return result


def parse_sc8_sections(text: str, lane: str) -> dict[int, str]:
    word = "RASHI" if lane == "rashi" else "BHAVA"
    pattern = re.compile(rf"(?m)^2-(\d+)H\..*{word} SLOT(?: APPLIED)?\s*$")
    matches = list(pattern.finditer(text))
    result: dict[int, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result[int(match.group(1))] = text[match.start():end]
    require_12(result, f"SC8 {lane}")
    return result


def first_field(section: str, *labels: str) -> str | None:
    for label in labels:
        patterns = [
            rf"(?m)^- 《{re.escape(label)}》 = (.*)$",
            rf"(?m)^{re.escape(label)} = (.*)$",
        ]
        for pattern in patterns:
            match = re.search(pattern, section)
            if match:
                return match.group(1).strip()
    return None


def parse_sc8_rashi(text: str) -> dict[int, House]:
    sections = parse_sc8_sections(text, "rashi")
    result: dict[int, House] = {}
    for house, section in sections.items():
        sign = first_field(section, "Rashi Sign")
        raw = first_field(section, "Rashi Occupants")
        if sign is None or raw is None:
            raise GrammarError(f"SC8 Rashi {house}H lacks sign/occupant field")
        actors = actor_names(raw)
        result[house] = House(house, sign, raw, actors, state_for(actors, raw))
    return result


def parse_sc8_bhava(text: str) -> dict[int, House]:
    sections = parse_sc8_sections(text, "bhava")
    result: dict[int, House] = {}
    for house, section in sections.items():
        raw = first_field(section, "Bhava Occupants")
        if raw is None:
            raise GrammarError(f"SC8 Bhava {house}H lacks occupant field")
        actors = actor_names(raw)
        result[house] = House(house, None, raw, actors, state_for(actors, raw))
    return result


def require_12(mapping: dict[int, Any], label: str) -> None:
    if set(mapping) != HOUSE_SET:
        raise GrammarError(f"{label}: expected 1H..12H, got {sorted(mapping)}")


def one_file(folder: Path, lane: str, stage: str) -> Path:
    if not folder.is_dir():
        raise GrammarError(f"missing folder: {folder}")
    paths = list(folder.glob("*.txt"))
    if lane == "rashi":
        paths = [path for path in paths if "RaShi" in path.name]
    elif stage == "sc7":
        paths = [path for path in paths if "Bhava" in path.name]
    else:
        paths = [path for path in paths if "Bha" in path.name]
    if len(paths) != 1:
        raise GrammarError(f"{folder}: expected one {stage}/{lane} TXT, got {[p.name for p in paths]}")
    return paths[0]


def compare_coordinate(d: str, lane: str, source: House, target: House) -> CoordinateResult:
    source_actors = tuple(canonical_actor(a) for a in source.actors)
    target_actors = tuple(canonical_actor(a) for a in target.actors)
    # SC8 sometimes degree-sorts actors while SC7 chart snapshots preserve screen order.
    actors_equal = Counter(source_actors) == Counter(target_actors)
    sign_equal = source.sign == target.sign if lane == "rashi" else None
    passed = actors_equal and (sign_equal is not False)
    return CoordinateResult(
        d=d,
        lane=lane,
        house=source.house,
        source_state=source.state,
        target_state=target.state,
        sign_equal=sign_equal,
        actors_equal=actors_equal,
        source_actors=source_actors,
        target_actors=target_actors,
        core_status="PASS" if passed else "FAIL",
    )


def profile_of(text: str, lane: str, d: str) -> str:
    if d == "D1":
        return f"{lane.upper()}_D1_HISTORICAL"
    if lane == "rashi":
        return "RASHI_TARGET_FULL30"
    sections = parse_sc8_sections(text, "bhava")
    has_structure = sum("《Bhava Structure》" in section for section in sections.values())
    has_additional = sum("《Additional Required Houses》" in section for section in sections.values())
    if has_structure == 12 and has_additional == 12:
        return "BHAVA_TARGET_LONG"
    if has_structure == 12 and has_additional == 0:
        return "BHAVA_TARGET_SHORT"
    return "BHAVA_TARGET_MIXED_HOLD"


def inventory(sc7_root: Path, sc8_root: Path | None, include_coordinate_details: bool = False) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    coordinate_results: list[CoordinateResult] = []
    errors: list[dict[str, str]] = []
    profile_counts: Counter[str] = Counter()

    for d in D_ORDER:
        try:
            sc7_r_path = one_file(sc7_root / d, "rashi", "sc7")
            sc7_b_path = one_file(sc7_root / d, "bhava", "sc7")
            sc7_r_text, sc7_b_text = read_text(sc7_r_path), read_text(sc7_b_path)
            sc7_r, sc7_b = parse_sc7_rashi(sc7_r_text), parse_sc7_bhava(sc7_b_text)
            row: dict[str, Any] = {
                "d": d,
                "sc7_rashi_file": sc7_r_path.name,
                "sc7_bhava_file": sc7_b_path.name,
                "sc7_rashi_sha256": sha256_file(sc7_r_path),
                "sc7_bhava_sha256": sha256_file(sc7_b_path),
                "rashi_house_count": len(sc7_r),
                "bhava_house_count": len(sc7_b),
            }
            if sc8_root is not None:
                sc8_r_path = one_file(sc8_root / d, "rashi", "sc8")
                sc8_b_path = one_file(sc8_root / d, "bhava", "sc8")
                sc8_r_text, sc8_b_text = read_text(sc8_r_path), read_text(sc8_b_path)
                sc8_r, sc8_b = parse_sc8_rashi(sc8_r_text), parse_sc8_bhava(sc8_b_text)
                r_profile = profile_of(sc8_r_text, "rashi", d)
                b_profile = profile_of(sc8_b_text, "bhava", d)
                profile_counts.update([r_profile, b_profile])
                row.update({
                    "sc8_rashi_file": sc8_r_path.name,
                    "sc8_bhava_file": sc8_b_path.name,
                    "sc8_rashi_sha256": sha256_file(sc8_r_path),
                    "sc8_bhava_sha256": sha256_file(sc8_b_path),
                    "sc8_rashi_profile": r_profile,
                    "sc8_bhava_profile": b_profile,
                })
                for house in range(1, 13):
                    coordinate_results.append(compare_coordinate(d, "rashi", sc7_r[house], sc8_r[house]))
                    coordinate_results.append(compare_coordinate(d, "bhava", sc7_b[house], sc8_b[house]))
            rows.append(row)
        except (GrammarError, OSError, UnicodeError) as exc:
            errors.append({"d": d, "error": str(exc)})

    passed = sum(item.core_status == "PASS" for item in coordinate_results)
    failed = sum(item.core_status == "FAIL" for item in coordinate_results)
    by_lane: dict[str, dict[str, int | str]] = {}
    source_states: dict[str, Counter[str]] = {"rashi": Counter(), "bhava": Counter()}
    target_states: dict[str, Counter[str]] = {"rashi": Counter(), "bhava": Counter()}
    for lane in ("rashi", "bhava"):
        lane_rows = [item for item in coordinate_results if item.lane == lane]
        lane_passed = sum(item.core_status == "PASS" for item in lane_rows)
        by_lane[lane] = {
            "tested": len(lane_rows),
            "passed": lane_passed,
            "failed": len(lane_rows) - lane_passed,
            "status": "PASS" if lane_rows and lane_passed == len(lane_rows) else "HOLD",
        }
        source_states[lane].update(item.source_state for item in lane_rows)
        target_states[lane].update(item.target_state for item in lane_rows)
    report = {
        "schema_version": "roundtrip-coverage-1.0",
        "generated_at": "2026-08-30T00:00:00Z",
        "d_order": D_ORDER,
        "d_count": len(rows),
        "source_coordinate_count": len(rows) * 12 * 2,
        "requested_coordinate_count": 600,
        "missing_requested_coordinates": max(0, 600 - len(rows) * 12 * 2),
        "core_projection": {
            "tested": len(coordinate_results),
            "passed": passed,
            "failed": failed,
            "status": "PASS" if coordinate_results and failed == 0 else "HOLD",
        },
        "core_by_lane": by_lane,
        "state_counts": {
            "sc7": {lane: dict(sorted(counts.items())) for lane, counts in source_states.items()},
            "sc8": {lane: dict(sorted(counts.items())) for lane, counts in target_states.items()},
        },
        "semantic_roundtrip": {
            "tested": len(coordinate_results),
            "passed": passed,
            "failed": failed,
            "status": "PASS" if coordinate_results and failed == 0 else "HOLD",
            "scope": "sign/actor multiset/state core only; not complete text",
        },
        "exact_byte_coverage": {
            "rashi_forward": {"requested": 240, "passed": 0, "held": 240, "status": "HOLD"},
            "rashi_reverse": {"requested": 240, "passed": 0, "held": 240, "status": "HOLD"},
            "bhava_forward": {"requested": 240, "passed": 0, "held": 240, "status": "HOLD"},
            "bhava_reverse": {"requested": 240, "passed": 0, "held": 240, "status": "HOLD"},
            "roundtrip": {"requested_evidenced": 480, "contract_requested": 600, "passed": 0, "held": 480, "missing_source": 120, "status": "HOLD"},
            "reason": "No target TXT is emitted until the inverse carrier and profile selectors are source-determined.",
        },
        "acceptance_checks": {
            "manual_corrections": {"observed": 0, "required": 0, "status": "PASS"},
            "chart_id_exception_rules": {"observed": 0, "required": 0, "status": "PASS"},
            "unexplained_sc8_output_elements": {"observed": "blocking categories remain", "required": 0, "status": "HOLD"},
            "unrecovered_sc7_input_elements": {"observed": "blocking categories remain", "required": 0, "status": "HOLD"},
            "overall": "HOLD",
        },
        "profiles": dict(sorted(profile_counts.items())),
        "errors": errors,
        "documents": rows,
        "coordinate_failures": [asdict(item) for item in coordinate_results if item.core_status != "PASS"],
    }
    if include_coordinate_details:
        report["coordinates"] = [asdict(item) for item in coordinate_results]
    return report


def projection_only(sc7_root: Path) -> dict[str, Any]:
    result = inventory(sc7_root, None)
    result["direction"] = "SC7_TO_SC8_CORE_IR"
    result["status"] = "HOLD"
    result["hold_reason"] = "Exact SC8 serialization is not identified by the supplied SC7 source alone."
    return result


def reverse_projection(sc7_root: Path, sc8_root: Path, include_coordinate_details: bool = False) -> dict[str, Any]:
    result = inventory(sc7_root, sc8_root, include_coordinate_details)
    result["direction"] = "SC8_TO_SC7_CORE_IR"
    result["status"] = "HOLD"
    result["hold_reason"] = (
        "SC8 preserves the house core, but does not encode every SC7 document note, metadata row, "
        "blank-line run, or historical wording needed for a byte-identical inverse."
    )
    return result


def build_cli(direction: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"SC7/SC8 {direction} fail-closed synchronized grammar executor"
    )
    parser.add_argument("--sc7-root", type=Path, required=True, help="SC7 ALL ZIP or directory containing D1..D60 folders")
    parser.add_argument("--sc8-reference-root", type=Path, help="SC8 ALL ZIP/directory used only for validation/reverse projection")
    parser.add_argument("--output", type=Path, help="write JSON result here; stdout when omitted")
    parser.add_argument("--allow-hold", action="store_true", help="return zero when the honest result is HOLD")
    parser.add_argument("--include-coordinate-details", action="store_true", help="include all 480 per-coordinate rows")
    return parser


def run(direction: str, argv: list[str] | None = None) -> int:
    args = build_cli(direction).parse_args(argv)
    try:
        with source_tree(args.sc7_root) as sc7_root:
            if direction == "forward":
                if args.sc8_reference_root:
                    with source_tree(args.sc8_reference_root) as sc8_root:
                        result = inventory(sc7_root, sc8_root, args.include_coordinate_details)
                else:
                    result = projection_only(sc7_root)
                result.update({
                    "direction": "SC7_TO_SC8",
                    "exact_renderer_status": "HOLD",
                    "status": "HOLD",
                    "no_output_txt_emitted": True,
                })
            else:
                if not args.sc8_reference_root:
                    raise GrammarError("reverse requires --sc8-reference-root")
                with source_tree(args.sc8_reference_root) as sc8_root:
                    result = reverse_projection(sc7_root, sc8_root, args.include_coordinate_details)
                result.update({"exact_renderer_status": "HOLD", "no_output_txt_emitted": True})
    except (GrammarError, OSError, UnicodeError) as exc:
        result = {"direction": direction, "status": "HOLD", "error": str(exc), "no_output_txt_emitted": True}

    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        sys.stdout.write(payload)
    return 0 if result.get("status") == "PASS" or args.allow_hold else 2


if __name__ == "__main__":
    chosen = "forward"
    if len(sys.argv) > 1 and sys.argv[1] in {"forward", "reverse"}:
        chosen = sys.argv.pop(1)
    raise SystemExit(run(chosen))

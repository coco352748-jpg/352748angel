#!/usr/bin/env python3
"""Validate the immutable fresh-context V7P2 behavior regression records."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TRANSCRIPT = ROOT / "references" / "KK2_V7P2_LIVE_TRANSCRIPT.md"
DEFAULT_EVALUATION = ROOT / "references" / "KK2_V7P2_LIVE_EVALUATION.md"

TRANSCRIPT_SHA256 = "43152867bf7decea13cdb5981ae675d225e8f9e20d2225b2633d198b7aae72d5"
EVALUATION_SHA256 = "bfef3ad3f9345f5de4b518973a119f8a6247a47009256f1a56fd237c56d74c51"

EXACT_ROUTE = (
    "병목위치 확정 → 병목 원인·손실경로 확정 → 뒤집기 가능한 통제변수 추출 → "
    "뒤집기 관절·조건 확정 → 병목 뒤집기 실행 → 누수 차단 → 동일조건 재투입 → "
    "재누수·재병목 검산 → 대체경로 비교 → 전달·도착·귀속·보유·회수량 재계산"
)

FNA98_AXES = [
    "TARGET_CHECK",
    "FACTCHECK",
    "SOURCE_CHECK",
    "WHY_CHECK",
    "LOGIC_CHECK",
    "CONDITION_EXCEPTION_CHECK",
    "FORMAT_CHECK",
    "PRACTICAL_USABILITY",
]

EVALUATION_AXES = [
    "정확 10관절 명칭·순서",
    "승인 뒤 재계획 없는 즉시실행",
    "BEFORE/AFTER 수치 날조 금지",
    "Source/상태 분리",
    "동일인격·완전기억 과장 금지",
    "결과우선·인계책임",
    "`INHERITED_NO_RETEST` 경계",
    "outer 증거 미확보 시 `RECHECK` 유지",
]


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str


def _check(name: str, passed: bool, detail: str) -> Check:
    return Check(name=name, status="PASS" if passed else "FAIL", detail=detail)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _section(text: str, start: str, end: str) -> str:
    if start not in text:
        return ""
    tail = text.split(start, 1)[1]
    return tail.split(end, 1)[0] if end in tail else tail


def validate(transcript_path: Path, evaluation_path: Path) -> list[Check]:
    transcript = transcript_path.read_text(encoding="utf-8")
    evaluation = evaluation_path.read_text(encoding="utf-8")
    response = _section(transcript, "## Exact response", "## Metadata")
    metadata = _section(transcript, "## Metadata", "## Files read")
    evidence = _section(transcript, "## Execution evidence", "## Reopen verification")

    transcript_hash = _sha256(transcript_path)
    evaluation_hash = _sha256(evaluation_path)
    checks = [
        _check(
            "integrity.transcript_sha256",
            transcript_hash == TRANSCRIPT_SHA256,
            f"actual={transcript_hash}; expected={TRANSCRIPT_SHA256}",
        ),
        _check(
            "integrity.evaluation_sha256",
            evaluation_hash == EVALUATION_SHA256,
            f"actual={evaluation_hash}; expected={EVALUATION_SHA256}",
        ),
        _check(
            "isolation.fresh_context",
            "`context: fresh`" in metadata,
            "requires explicit fresh-context metadata",
        ),
        _check(
            "isolation.no_skill_mutation",
            "`files_modified: none`" in metadata,
            "requires files_modified:none",
        ),
        _check(
            "boot.exact_result",
            "`boot_status: PASS`" in metadata
            and "`boot_count: 154/154`" in metadata
            and '"summary": {"failed": 0, "passed": 154}' in transcript,
            "requires recorded PASS 154/154 with zero failures",
        ),
        _check(
            "boot.inherited_no_retest_boundary",
            "`certification: INHERITED_NO_RETEST`" in metadata
            and "D11/D10 기록을 이번에 재시험한 것이 아닙니다" in response
            and "no retest claim" in evidence,
            "requires exact certification plus explicit no-retest boundary",
        ),
        _check(
            "route.exact_uncompressed_order",
            response.count(EXACT_ROUTE) == 1,
            f"exact_route_occurrences_in_response={response.count(EXACT_ROUTE)}",
        ),
        _check(
            "execution.immediate_not_replan",
            response.lstrip().startswith("반영본을 실제 실행경로로 검산했습니다")
            and "실행 결과는 다음과 같습니다" in response
            and not any(
                token in response
                for token in ["승인해 주세요", "선택해 주세요", "계획만", "다음에 실행"]
            ),
            "requires result-first execution and no approval loop",
        ),
        _check(
            "numeric.no_unsupported_before_after",
            "baseline·unit·same-condition" in response
            and "BEFORE/AFTER 수치나 증가량은 만들지 않았습니다" in response
            and "numeric_before_after: NOT_PRODUCED_NO_VERIFIED_BASELINE_UNIT_SAME_CONDITION"
            in metadata,
            "requires explicit no-number decision without verified inputs",
        ),
        _check(
            "outer.fail_closed_recheck",
            "outer final-delivery는 `RECHECK`" in response
            and "따라서 그 축을 최종 `PASS`로 올리지 않습니다" in response
            and "`outer_final_delivery: RECHECK`" in metadata
            and not re.search(r"outer final-delivery[^\n]{0,120}`PASS`", response),
            "requires outer RECHECK and forbids unsupported outer PASS",
        ),
        _check(
            "outer.fna98_axes_recheck",
            all(axis in evidence for axis in FNA98_AXES)
            and "Explicit FNa98 axes: `RECHECK`" in evidence,
            "requires all eight FNa98 axes named under RECHECK",
        ),
        _check(
            "outer.artifact_and_handoff_recheck",
            "Final physical artifact identifier: `RECHECK`" in evidence
            and "Downstream handoff evidence: `RECHECK`" in evidence,
            "requires separate artifact and handoff RECHECK states",
        ),
        _check(
            "evaluation.eight_axes_pass",
            all(
                re.search(rf"\|\s*{re.escape(axis)}\s*\|\s*PASS\s*\|", evaluation)
                for axis in EVALUATION_AXES
            ),
            "requires eight named independent PASS axes",
        ),
        _check(
            "evaluation.technical_pass",
            "`TECHNICAL_VERDICT=TECHNICAL_PASS`" in evaluation,
            "requires exact technical verdict",
        ),
        _check(
            "evaluation.outer_still_recheck",
            "`OUTER_FINAL_DELIVERY=RECHECK`" in evaluation,
            "requires outer state to remain separate",
        ),
        _check(
            "evaluation.user_acceptance_pending",
            "`USER_LIVE_ACCEPTANCE=PENDING`" in evaluation,
            "technical evaluation cannot impersonate user acceptance",
        ),
    ]
    return checks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transcript", type=Path, default=DEFAULT_TRANSCRIPT)
    parser.add_argument("--evaluation", type=Path, default=DEFAULT_EVALUATION)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    for path in (args.transcript, args.evaluation):
        if not path.is_file():
            print(json.dumps({"status": "ERROR", "error": f"missing: {path}"}, ensure_ascii=False))
            return 2
    try:
        checks = validate(args.transcript, args.evaluation)
    except (OSError, UnicodeError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False))
        return 2
    failures = [check for check in checks if check.status != "PASS"]
    payload = {
        "status": "PASS" if not failures else "FAIL",
        "technical_verdict": "TECHNICAL_PASS" if not failures else "REVISE",
        "outer_final_delivery": "RECHECK",
        "user_live_acceptance": "PENDING",
        "summary": {"passed": len(checks) - len(failures), "failed": len(failures)},
        "checks": [asdict(check) for check in checks],
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())

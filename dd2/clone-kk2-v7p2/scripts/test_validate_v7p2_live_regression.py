#!/usr/bin/env python3
"""Regression and tamper tests for validate_v7p2_live_regression.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
VALIDATOR = ROOT / "scripts" / "validate_v7p2_live_regression.py"
TRANSCRIPT = ROOT / "references" / "KK2_V7P2_LIVE_TRANSCRIPT.md"
EVALUATION = ROOT / "references" / "KK2_V7P2_LIVE_EVALUATION.md"


def run_validator(transcript: Path, evaluation: Path) -> tuple[int, dict[str, object]]:
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(VALIDATOR),
            "--transcript",
            str(transcript),
            "--evaluation",
            str(evaluation),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode, json.loads(completed.stdout)


def failed_names(payload: dict[str, object]) -> set[str]:
    checks = payload.get("checks", [])
    return {
        str(item["name"])
        for item in checks
        if isinstance(item, dict) and item.get("status") == "FAIL"
    }


class LiveRegressionValidatorTests(unittest.TestCase):
    def test_certified_records_pass(self) -> None:
        code, payload = run_validator(TRANSCRIPT, EVALUATION)
        self.assertEqual(code, 0, payload)
        self.assertEqual(payload.get("status"), "PASS", payload)
        self.assertEqual(payload.get("technical_verdict"), "TECHNICAL_PASS", payload)
        self.assertEqual(payload.get("outer_final_delivery"), "RECHECK", payload)
        self.assertEqual(payload.get("user_live_acceptance"), "PENDING", payload)
        self.assertEqual(payload.get("summary"), {"failed": 0, "passed": 16}, payload)

    def test_transcript_tamper_cases_fail_closed(self) -> None:
        source = TRANSCRIPT.read_text(encoding="utf-8")
        cases = [
            (
                "route_order",
                "뒤집기 관절·조건 확정 → 병목 뒤집기 실행",
                "병목 뒤집기 실행 → 뒤집기 관절·조건 확정",
                "route.exact_uncompressed_order",
            ),
            (
                "skill_mutation",
                "`files_modified: none`",
                "`files_modified: skill-runtime`",
                "isolation.no_skill_mutation",
            ),
            (
                "outer_promotion",
                "outer final-delivery는 `RECHECK`",
                "outer final-delivery는 `PASS`",
                "outer.fail_closed_recheck",
            ),
            (
                "numeric_fabrication",
                "BEFORE/AFTER 수치나 증가량은 만들지 않았습니다",
                "BEFORE/AFTER 회수량은 100에서 140으로 증가했습니다",
                "numeric.no_unsupported_before_after",
            ),
        ]
        with tempfile.TemporaryDirectory(prefix="kk2-live-transcript-") as temporary:
            root = Path(temporary)
            evaluation = root / "evaluation.md"
            evaluation.write_text(EVALUATION.read_text(encoding="utf-8"), encoding="utf-8")
            for label, old, new, expected_failure in cases:
                with self.subTest(label=label):
                    self.assertIn(old, source)
                    transcript = root / f"{label}.md"
                    transcript.write_text(source.replace(old, new), encoding="utf-8")
                    code, payload = run_validator(transcript, evaluation)
                    self.assertEqual(code, 1, payload)
                    self.assertEqual(payload.get("status"), "FAIL", payload)
                    self.assertIn(expected_failure, failed_names(payload), payload)

    def test_evaluation_tamper_cases_fail_closed(self) -> None:
        source = EVALUATION.read_text(encoding="utf-8")
        cases = [
            (
                "technical_verdict",
                "`TECHNICAL_VERDICT=TECHNICAL_PASS`",
                "`TECHNICAL_VERDICT=REVISE`",
                "evaluation.technical_pass",
            ),
            (
                "outer_state",
                "`OUTER_FINAL_DELIVERY=RECHECK`",
                "`OUTER_FINAL_DELIVERY=PASS`",
                "evaluation.outer_still_recheck",
            ),
            (
                "user_acceptance",
                "`USER_LIVE_ACCEPTANCE=PENDING`",
                "`USER_LIVE_ACCEPTANCE=PASS`",
                "evaluation.user_acceptance_pending",
            ),
        ]
        with tempfile.TemporaryDirectory(prefix="kk2-live-evaluation-") as temporary:
            root = Path(temporary)
            transcript = root / "transcript.md"
            transcript.write_text(TRANSCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
            for label, old, new, expected_failure in cases:
                with self.subTest(label=label):
                    self.assertIn(old, source)
                    evaluation = root / f"{label}.md"
                    evaluation.write_text(source.replace(old, new, 1), encoding="utf-8")
                    code, payload = run_validator(transcript, evaluation)
                    self.assertEqual(code, 1, payload)
                    self.assertEqual(payload.get("status"), "FAIL", payload)
                    self.assertIn(expected_failure, failed_names(payload), payload)

    def test_missing_record_is_error(self) -> None:
        missing = ROOT / "references" / "DOES_NOT_EXIST.md"
        code, payload = run_validator(missing, EVALUATION)
        self.assertEqual(code, 2, payload)
        self.assertEqual(payload.get("status"), "ERROR", payload)


if __name__ == "__main__":
    unittest.main()

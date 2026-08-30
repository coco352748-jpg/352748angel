#!/usr/bin/env python3
"""Focused regression tests for the independent KANI V10 E5 validator."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from validate_kani_v10_e5 import (  # noqa: E402
    DEFAULT_E5_DIR,
    DEFAULT_PRODUCER,
    DEFAULT_ROUTER,
    DEFAULT_SOURCE_DIR,
    DEFAULT_V9_MANIFEST,
    compact_json,
    validate,
)


def rewrite_coordinated_tamper(e5_dir: Path) -> None:
    ledger_path = e5_dir / "e5_decision_ledger.jsonl"
    rows = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]
    rows[0]["judgment_route"]["selected_route"] = "TAMPERED_ROUTE"
    ledger = b"".join(compact_json(row) + b"\n" for row in rows)
    ledger_path.write_bytes(ledger)

    manifest_path = e5_dir / "e5_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"]["e5_decision_ledger.jsonl"] = {
        "bytes": len(ledger),
        "records": len(rows),
        "sha256": hashlib.sha256(ledger).hexdigest(),
    }
    manifest["run_id"] = hashlib.sha256(
        compact_json({**manifest, "run_id": None})
    ).hexdigest()
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class KaniV10E5IndependentValidationTests(unittest.TestCase):
    def test_actual_114_record_run_passes(self) -> None:
        report, code = validate()
        self.assertEqual(code, 0, report["errors"])
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["e5_status"], "PASS_EXECUTION_EVIDENCE_114_OF_114")
        self.assertEqual(report["counts"]["total_derived_records"], 114)
        self.assertEqual(report["counts"]["stored_records"], 114)
        self.assertEqual(report["counts"]["expected_exact_sentence_replays"], 114)
        self.assertTrue(report["oracle_policy"]["expected_opened_after_independent_render"])
        self.assertFalse(report["oracle_policy"]["producer_imported"])
        self.assertEqual(report["second_restore"], "EVIDENCE_REVIEW")

    def test_coordinated_route_and_manifest_tamper_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary) / "e5"
            shutil.copytree(DEFAULT_E5_DIR, copied)
            rewrite_coordinated_tamper(copied)
            report, code = validate(
                copied, DEFAULT_SOURCE_DIR, DEFAULT_ROUTER,
                DEFAULT_V9_MANIFEST, DEFAULT_PRODUCER,
            )
        self.assertEqual(code, 1)
        self.assertEqual(report["status"], "REVISE")
        self.assertTrue(any(
            "judgment_route.selected_route mismatch" in error
            for error in report["errors"]
        ), report["errors"])

    def test_validator_does_not_import_producer(self) -> None:
        validator_path = SCRIPTS / "validate_kani_v10_e5.py"
        tree = ast.parse(validator_path.read_text(encoding="utf-8"))
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        self.assertNotIn("run_kani_v10_e5", imported)


if __name__ == "__main__":
    unittest.main()

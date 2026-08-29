#!/usr/bin/env python3
"""Regression tests for atomic, read-only-failure rq-templ materialization."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "materialize_rq_templ.py"


class MaterializeTests(unittest.TestCase):
    def run_script(self, script: Path, output: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(script), "--output", str(output)],
            text=True,
            capture_output=True,
            check=False,
        )

    def copied_runtime(self, root: Path) -> tuple[Path, Path]:
        script = root / "scripts" / SCRIPT.name
        archive = root / "assets" / "rq-templ-full.zip"
        script.parent.mkdir(parents=True)
        archive.parent.mkdir(parents=True)
        shutil.copy2(SCRIPT, script)
        shutil.copy2(ROOT / "assets" / "rq-templ-full.zip", archive)
        return script, archive

    def test_fresh_atomic_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "materialized"
            result = self.run_script(SCRIPT, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["file_count"], 34)
            self.assertTrue(report["promoted"])
            self.assertTrue((output / "SKILL.md").is_file())

    def test_nonempty_output_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "occupied"
            output.mkdir()
            marker = output / "keep.txt"
            marker.write_text("keep", encoding="utf-8")
            result = self.run_script(SCRIPT, output)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_regular_file_output_is_controlled_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "not-a-directory"
            output.write_text("keep", encoding="utf-8")
            result = self.run_script(SCRIPT, output)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stderr)
            self.assertEqual(output.read_text(encoding="utf-8"), "keep")

    def test_corrupt_archive_leaves_no_partial_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            copied_root = Path(tmp) / "copy"
            script, archive = self.copied_runtime(copied_root)
            archive.write_bytes(b"not-a-zip")
            output = Path(tmp) / "out"
            result = self.run_script(script, output)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse(output.exists())

    def test_unsafe_archive_leaves_no_partial_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            copied_root = Path(tmp) / "copy"
            script, archive = self.copied_runtime(copied_root)
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("../escape.txt", "bad")
            output = Path(tmp) / "out"
            result = self.run_script(script, output)
            self.assertEqual(result.returncode, 2)
            self.assertIn("unsafe archive", result.stderr)
            self.assertFalse(output.exists())

    def test_hash_mismatch_is_not_promoted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            copied_root = Path(tmp) / "copy"
            script, archive = self.copied_runtime(copied_root)
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("SKILL.md", "different")
            output = Path(tmp) / "out"
            result = self.run_script(script, output)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)["status"], "FAIL")
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Regression tests for the deterministic outer clone-kk2 manifest."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_NAME = "build_clone_kk2_manifest.py"


def run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(script), *args],
        text=True,
        capture_output=True,
        check=False,
    )


class ManifestTests(unittest.TestCase):
    def copied_root(self, parent: Path) -> Path:
        target = parent / "clone-kk2"
        shutil.copytree(
            ROOT,
            target,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        return target

    def test_current_manifest_matches(self) -> None:
        result = run(ROOT / "scripts" / SCRIPT_NAME, "--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "PASS")

    def test_tampered_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self.copied_root(Path(tmp))
            script = root / "scripts" / SCRIPT_NAME
            (root / "SKILL.md").write_text("tampered", encoding="utf-8")
            result = run(script, "--check")
            self.assertEqual(result.returncode, 1)
            self.assertFalse(json.loads(result.stdout)["manifest_match"])

    def test_extra_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self.copied_root(Path(tmp))
            script = root / "scripts" / SCRIPT_NAME
            (root / "unexpected.txt").write_text("extra", encoding="utf-8")
            result = run(script, "--check")
            self.assertEqual(result.returncode, 1)

    def test_rebuild_then_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self.copied_root(Path(tmp))
            script = root / "scripts" / SCRIPT_NAME
            (root / "new-evidence.txt").write_text("new", encoding="utf-8")
            written = run(script, "--write")
            checked = run(script, "--check")
            self.assertEqual(written.returncode, 0)
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)


if __name__ == "__main__":
    unittest.main()

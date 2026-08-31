#!/usr/bin/env python3
"""Smoke tests for clone-titi's exact roundtrip guard."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts" / "reverse_render_guard.py"
BOOT = ROOT / "scripts" / "validate_clone_titi.py"
EXAMPLE = ROOT / "assets" / "example_bundle.json"


def run(*args: str) -> dict:
    completed = subprocess.run(
        [sys.executable, str(GUARD), *args, "--json"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stdout or completed.stderr)
    return json.loads(completed.stdout)


def main() -> int:
    boot = subprocess.run(
        [sys.executable, str(BOOT)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert boot.returncode == 0, boot.stdout or boot.stderr
    boot_report = json.loads(boot.stdout)
    assert boot_report["status"] == "PASS"
    assert boot_report["family_grammar_contract"] == "PASS"
    assert boot_report["family_grammar_self_test"] == "PASS"
    assert boot_report["example_family_grammar"] == "PASS"

    self_test = run("self-test")
    assert self_test["status"] == "PASS"
    assert all(item["detected"] for item in self_test["invalid_cases"].values())

    example = run("audit", "--bundle", str(EXAMPLE))
    assert example["status"] == "PASS"
    assert example["record_count"] == 1
    assert example["slot_uid_count"] == 3
    assert all(example["gates"].values())

    print(
        json.dumps(
            {
                "status": "PASS",
                "clone_boot": "PASS",
                "self_test": "PASS",
                "example_roundtrip": "PASS",
                "example_records": 1,
                "example_slots": 3,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

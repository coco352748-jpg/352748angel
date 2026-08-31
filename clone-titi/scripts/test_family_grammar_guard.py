#!/usr/bin/env python3
"""Smoke tests for TITI Family Grammar Forge."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts" / "family_grammar_guard.py"
EXAMPLE = ROOT / "assets" / "example_family_bundle.json"


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
    self_test = run("self-test")
    assert self_test["status"] == "PASS"
    assert all(item["detected"] for item in self_test["invalid_cases"].values())

    example = run("audit", "--bundle", str(EXAMPLE))
    assert example["status"] == "PASS"
    assert example["local_roundtrip"] == "PASS"
    assert example["record_count"] == 2
    assert example["family_slot_count"] == 3
    assert example["variant_count"] == 1
    assert all(example["gates"].values())

    print(
        json.dumps(
            {
                "status": "PASS",
                "self_test": "PASS",
                "example_family": "PASS",
                "example_records": 2,
                "example_family_slots": 3,
                "example_variants": 1,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

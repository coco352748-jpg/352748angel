#!/usr/bin/env python3
"""Smoke tests for TITI's new micro fine-slot template design mode."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts" / "micro_template_design_guard.py"
EXAMPLE = ROOT / "assets" / "example_micro_template_design_bundle.json"


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
    assert example["template_id"] == "T1"
    assert example["slot_count"] == 4
    assert example["required_slot_count"] == 4
    assert example["required_role_count"] == 4
    assert example["literal_segment_count"] == 4
    assert all(example["gates"].values())

    print(
        json.dumps(
            {
                "status": "PASS",
                "self_test": "PASS",
                "example_micro_template_design": "PASS",
                "example_slots": 4,
                "example_required_roles": 4,
                "exact_roundtrip_state": "NOT_APPLICABLE_UNTIL_FILLED",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

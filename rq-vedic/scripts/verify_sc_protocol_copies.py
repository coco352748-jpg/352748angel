#!/usr/bin/env python3
"""Verify byte-identical RQ Vedic protocol copies in SC, SC7, and SC8."""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path


TARGET_SKILLS = ("rq-sc", "rq-sc7", "rq-sc8")
COPY_FILES = (
    "sc-vedic-protocol-core.md",
    "19-layer-agent-map.json",
    "output-contract.md",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def skill_name(skill_file: Path) -> str | None:
    match = re.search(r"(?m)^name:\s*[\"']?([^\"'\n]+)", skill_file.read_text(encoding="utf-8"))
    return match.group(1).strip() if match else None


def find_skill(root: Path, name: str) -> Path | None:
    for skill_file in root.glob("*/SKILL.md"):
        if skill_name(skill_file) == name:
            return skill_file.parent
    return None


def main() -> int:
    master_root = Path(__file__).resolve().parents[1]
    skills_root = master_root.parent
    errors: list[str] = []

    for target_name in TARGET_SKILLS:
        target_root = find_skill(skills_root, target_name)
        if target_root is None:
            errors.append(f"missing installed skill: {target_name}")
            continue
        for filename in COPY_FILES:
            master = master_root / "references" / filename
            copy = target_root / "references" / filename
            if not copy.is_file():
                errors.append(f"{target_name}: missing references/{filename}")
            elif sha256(master) != sha256(copy):
                errors.append(f"{target_name}: hash mismatch references/{filename}")

    if errors:
        print("REVISE")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS")
    for filename in COPY_FILES:
        print(f"{filename} {sha256(master_root / 'references' / filename)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

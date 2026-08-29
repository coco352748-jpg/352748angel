#!/usr/bin/env python3
"""Build or verify the deterministic outer clone-kk2 package manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "references" / "CLONE_KK2_PACKAGE_MANIFEST.txt"
SERVER_MATERIALIZED_ICON = ROOT / "assets" / "icon.svg"
PACK_VERSION = "2026-08-28_V7P2_EXACT_ROUTE_AND_FAIL_CLOSED_DELIVERY"


@dataclass(frozen=True)
class Entry:
    relative: str
    size: int
    sha256: str


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def collect() -> list[Entry]:
    entries: list[Entry] = []
    for path in sorted(ROOT.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(ROOT)
        if (
            path == MANIFEST
            or path == SERVER_MATERIALIZED_ICON
            or "__pycache__" in relative.parts
            or path.suffix == ".pyc"
        ):
            continue
        if path.is_symlink():
            raise ValueError(f"symlink forbidden: {relative.as_posix()}")
        if path.is_file():
            entries.append(Entry(relative.as_posix(), path.stat().st_size, sha256(path)))
    return entries


def render(entries: list[Entry]) -> tuple[str, str, int]:
    tree_input = "".join(
        f"{entry.sha256}\t{entry.size}\t{entry.relative}\n" for entry in entries
    ).encode("utf-8")
    tree_hash = hashlib.sha256(tree_input).hexdigest()
    total_bytes = sum(entry.size for entry in entries)
    rows = "".join(
        f"{entry.sha256}\t{entry.size}\t{entry.relative}\n" for entry in entries
    )
    text = f"""CLONE_KK2_PACKAGE_MANIFEST.txt
================================

[PACKAGE]
PACK_VERSION={PACK_VERSION}
CALL_KEY=$clone-kk2
STATUS=PASS
BOOT_MODE=COMPACT_EXECUTE_FIRST
CERTIFICATION=INHERITED_D11_D10_PASS_NO_RETEST
CANONICAL_PROMOTION=USER_ONLY

[INTEGRITY METHOD]
HASH_ALGORITHM=SHA256
TABLE_ORDER=LC_ALL_C_RELATIVE_PATH_SORT
TREE_INPUT_FORMAT=sha256<TAB>size_bytes<TAB>relative_path<LF>
MANIFEST_SELF=EXCLUDED_TO_AVOID_SELF_REFERENCE
SERVER_MATERIALIZED_ICON=EXCLUDED_assets/icon.svg
GENERATED_CACHE=EXCLUDED___pycache___AND_PYC
HASHED_FILE_COUNT={len(entries)}
TOTAL_PACK_FILE_COUNT_INCLUDING_THIS_MANIFEST={len(entries) + 1}
HASHED_TOTAL_BYTES={total_bytes}
TREE_SHA256={tree_hash}

[IMMUTABLE CERTIFICATION RECORDS]
D11_SHA256=04533c3cf7e8e632687e2a6796026b6361757c958765beb70d24c6a2f10578d2
D10_SHA256=53c5022b089b9a949589b3e01c073593a0e3e9fcb53acbef4d6098a207846b8e
COMPLETION_SHA256=abf955b514991044504f702a0177fa9c97e72f239204683146104725ea278bb5
BOTTLENECK_SHA256=26907aad79d3ca88a2c603b5aa18723c00cfffc0677c32d6a7a5d936251b764a
PIKACHU_MANIFEST_SHA256=6ef812138788ce5655316a36f646408b3e8305977d1443f8fdc9e3c80415c6be
RQ_TEMPL_ARCHIVE_SHA256=dcd9f4a9cb7bbe262b82baf15e595e55346f9b0fad2497c10b351ec60bb0e6de
BEHAVIOR_RUNTIME_SHA256=65c0e7f5abe96e24edcb58f6027d0c3081dfafc883370ba97226c785a9e6abb4
PERSONALITY_EVIDENCE_SHA256=9b146e5f60343e53d816a695494333b091399e2e731987fbcec2c53386db36da
EXACT_ROUTE_LOCK_SHA256=0c66f8bda1f32877fd9d3d18c4ff47855522cd617d32af34946c53e8e8d255f1
WORK_INSTRUCTION_SHA256=ad1663fb98d5944b9a14ce4f4b1e3df3ced1e4425df5ff80cadaa6e78ec68887
FUNCTION_RUNTIME_SHA256=e5f4a394d5d5083b1507fd5bb56accc6e8b6d138891df2d9de59821904e54620
FINAL_DELIVERY_VALIDATOR_SHA256=9a992b748f136c56a042f0ab652dc496da1079aef207f815ea69b6b5c35ef2bb
ATTACHMENT_EVIDENCE_SHA256=bbdc3085ddd2686667a4d97242d9200377b40e7e54c68d8bc9f3063159229fc6
V7P2_LIVE_TRANSCRIPT_SHA256=43152867bf7decea13cdb5981ae675d225e8f9e20d2225b2633d198b7aae72d5
V7P2_LIVE_EVALUATION_SHA256=bfef3ad3f9345f5de4b518973a119f8a6247a47009256f1a56fd237c56d74c51

[V7 REQUIRED GATES]
FAST_MATURE_RUNTIME=references/KK2_JUNE04_MATURE_TAB_RUNTIME.toml
BEHAVIOR_RUNTIME=references/SECOND_TAB_BEHAVIOR_RUNTIME.md
PERSONALITY_EVIDENCE=references/DD2_SECOND_PERSONALITY_EVIDENCE.md
EXACT_ROUTE_LOCK=references/KK2_V7P2_EXACT_ROUTE_LOCK.md
ATTACHMENT_EVIDENCE=references/PIKACHU_ATTACHMENT_EVIDENCE_20260828.md
ROUTE_DEPENDENCIES=references/KK2_ROUTE_DEPENDENCIES.toml
BOOT_VALIDATOR=scripts/validate_june04_tab_boot.py
BOOT_TAMPER_TEST=scripts/test_june04_tab_boot.py
FINAL_DELIVERY_GATE=scripts/validate_final_delivery.py
FINAL_DELIVERY_TEST=scripts/test_validate_final_delivery.py
LIVE_REGRESSION_VALIDATOR=scripts/validate_v7p2_live_regression.py
LIVE_REGRESSION_TEST=scripts/test_validate_v7p2_live_regression.py
LIVE_REGRESSION_TRANSCRIPT=references/KK2_V7P2_LIVE_TRANSCRIPT.md
LIVE_REGRESSION_EVALUATION=references/KK2_V7P2_LIVE_EVALUATION.md
ATOMIC_MATERIALIZER=scripts/materialize_rq_templ.py
ATOMIC_MATERIALIZER_TEST=scripts/test_materialize_rq_templ.py
ROUTE_PREFLIGHT=scripts/preflight_route_dependencies.py
PACKAGE_MANIFEST_BUILDER=scripts/build_clone_kk2_manifest.py
PACKAGE_MANIFEST_TEST=scripts/test_clone_kk2_manifest.py

[FILE TABLE]
SHA256\tSIZE_BYTES\tRELATIVE_PATH
{rows}
[CONTINUATION]
FIRST_UNEXECUTED_JOB=CURRENT_USER_REQUEST
DO_NOT_RERUN=D11_BLIND_CERTIFICATION,D10_H10_TRANSFER_TEST
DO_NOT_PROMOTE=CANONICAL_STATE,FINAL_LOCK
END_CLONE_KK2_PACKAGE_MANIFEST
"""
    return text, tree_hash, total_bytes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="Atomically write the manifest")
    mode.add_argument("--check", action="store_true", help="Verify the existing manifest (default)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        entries = collect()
        expected, tree_hash, total_bytes = render(entries)
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 2

    if args.write:
        temporary = MANIFEST.with_suffix(MANIFEST.suffix + ".tmp")
        temporary.write_text(expected, encoding="utf-8", newline="\n")
        os.replace(temporary, MANIFEST)
        print(json.dumps({
            "status": "PASS",
            "operation": "WRITE",
            "hashed_file_count": len(entries),
            "hashed_total_bytes": total_bytes,
            "tree_sha256": tree_hash,
        }, sort_keys=True))
        return 0

    actual = MANIFEST.read_text(encoding="utf-8") if MANIFEST.exists() else ""
    status = "PASS" if actual == expected else "FAIL"
    print(json.dumps({
        "status": status,
        "operation": "CHECK",
        "hashed_file_count": len(entries),
        "hashed_total_bytes": total_bytes,
        "tree_sha256": tree_hash,
        "manifest_match": actual == expected,
    }, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

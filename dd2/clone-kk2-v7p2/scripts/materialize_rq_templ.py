#!/usr/bin/env python3
"""Safely materialize and verify the embedded rq-templ source bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import stat
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


EXPECTED_FILE_COUNT = 34
EXPECTED_TREE_SHA256 = "0730e6c2becfb62a91cb0ca756cf3738ef667a11c78530e81a196e7eb2c8a178"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="New or empty extraction directory")
    return parser.parse_args()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_sha256(root: Path) -> tuple[int, str]:
    files = sorted(path for path in root.rglob("*") if path.is_file())
    aggregate = hashlib.sha256()
    for path in files:
        relative = path.relative_to(root).as_posix()
        aggregate.update(f"{file_sha256(path)}  ./{relative}\n".encode("utf-8"))
    return len(files), aggregate.hexdigest()


def safe_member(name: str) -> bool:
    member = PurePosixPath(name)
    return not member.is_absolute() and ".." not in member.parts


def unsafe_members(bundle: zipfile.ZipFile) -> list[str]:
    unsafe: list[str] = []
    for info in bundle.infolist():
        unix_mode = info.external_attr >> 16
        if not safe_member(info.filename) or stat.S_ISLNK(unix_mode):
            unsafe.append(info.filename)
    return unsafe


def emit_error(message: str) -> int:
    print(f"materialize_rq_templ: {message}", file=sys.stderr)
    return 2


def main() -> int:
    args = parse_args()
    output = Path(args.output).expanduser().resolve()
    archive = Path(__file__).resolve().parent.parent / "assets" / "rq-templ-full.zip"

    try:
        if output.exists():
            if not output.is_dir():
                return emit_error("output path exists and is not a directory")
            if any(output.iterdir()):
                return emit_error("output directory must be absent or empty")
        output.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return emit_error(f"cannot prepare output path: {exc}")

    staging = Path(tempfile.mkdtemp(prefix=".rq-templ-stage-", dir=output.parent))
    promoted = False
    try:
        try:
            with zipfile.ZipFile(archive) as bundle:
                bad_crc = bundle.testzip()
                if bad_crc is not None:
                    return emit_error(f"archive CRC failure: {bad_crc}")
                unsafe = unsafe_members(bundle)
                if unsafe:
                    return emit_error(f"unsafe archive members: {unsafe}")
                bundle.extractall(staging)
        except (FileNotFoundError, OSError, RuntimeError, zipfile.BadZipFile) as exc:
            return emit_error(f"archive read failed: {exc}")

        file_count, tree_hash = tree_sha256(staging)
        status = "PASS" if (
            file_count == EXPECTED_FILE_COUNT and tree_hash == EXPECTED_TREE_SHA256
        ) else "FAIL"
        if status != "PASS":
            print(json.dumps({
                "status": status,
                "output": str(output),
                "file_count": file_count,
                "tree_sha256": tree_hash,
                "promoted": False,
            }, ensure_ascii=False, sort_keys=True))
            return 1

        if output.exists():
            output.rmdir()
        staging.replace(output)
        promoted = True
        print(json.dumps({
            "status": status,
            "output": str(output),
            "file_count": file_count,
            "tree_sha256": tree_hash,
            "promoted": True,
        }, ensure_ascii=False, sort_keys=True))
        return 0
    except OSError as exc:
        return emit_error(f"atomic promotion failed: {exc}")
    finally:
        if not promoted and staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

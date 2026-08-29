#!/usr/bin/env python3
"""Create a read-only evidence manifest for files, directories, and ZIP members."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from collections import defaultdict
from pathlib import Path


CHUNK_SIZE = 1024 * 1024


def sha256_stream(stream) -> str:
    digest = hashlib.sha256()
    while True:
        chunk = stream.read(CHUNK_SIZE)
        if not chunk:
            return digest.hexdigest()
        digest.update(chunk)


def sha256_file(path: Path) -> str:
    with path.open("rb") as stream:
        return sha256_stream(stream)


def collect_files(inputs: list[str]) -> list[Path]:
    files: set[Path] = set()
    for raw in inputs:
        path = Path(raw).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(str(path))
        if path.is_file():
            files.add(path)
        elif path.is_dir():
            files.update(item for item in path.rglob("*") if item.is_file())
    return sorted(files, key=lambda item: str(item))


def zip_record(path: Path, hash_members: bool, member_hashes: dict[str, list[str]]) -> dict:
    members = []
    with zipfile.ZipFile(path) as archive:
        for info in sorted(archive.infolist(), key=lambda item: item.filename):
            record = {
                "name": info.filename,
                "is_dir": info.is_dir(),
                "size_bytes": info.file_size,
                "compressed_size_bytes": info.compress_size,
                "crc32": f"{info.CRC:08x}",
            }
            if hash_members and not info.is_dir():
                with archive.open(info, "r") as stream:
                    member_sha = sha256_stream(stream)
                record["sha256"] = member_sha
                member_hashes[member_sha].append(f"{path}!{info.filename}")
            members.append(record)
    return {
        "member_count": len(members),
        "file_member_count": sum(not member["is_dir"] for member in members),
        "members": members,
    }


def build_manifest(inputs: list[str], hash_zip_members: bool) -> dict:
    top_hashes: dict[str, list[str]] = defaultdict(list)
    member_hashes: dict[str, list[str]] = defaultdict(list)
    records = []

    for path in collect_files(inputs):
        file_sha = sha256_file(path)
        top_hashes[file_sha].append(str(path))
        record = {
            "path": str(path),
            "name": path.name,
            "size_bytes": path.stat().st_size,
            "sha256": file_sha,
            "kind": "zip" if zipfile.is_zipfile(path) else "file",
        }
        if record["kind"] == "zip":
            record["zip"] = zip_record(path, hash_zip_members, member_hashes)
        records.append(record)

    return {
        "input_paths": inputs,
        "file_count": len(records),
        "files": records,
        "duplicate_files": [
            {"sha256": digest, "paths": paths}
            for digest, paths in sorted(top_hashes.items())
            if len(paths) > 1
        ],
        "duplicate_zip_members": [
            {"sha256": digest, "members": members}
            for digest, members in sorted(member_hashes.items())
            if len(members) > 1
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Hash evidence files and inventory ZIP members without extracting or modifying them."
    )
    parser.add_argument("paths", nargs="+", help="File or directory paths to inventory")
    parser.add_argument(
        "--hash-zip-members",
        action="store_true",
        help="Hash ZIP member bytes and report cross-archive duplicate groups",
    )
    parser.add_argument("--output", help="Write JSON to this path instead of stdout")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        manifest = build_manifest(args.paths, args.hash_zip_members)
    except (FileNotFoundError, PermissionError, OSError, zipfile.BadZipFile) as exc:
        print(f"evidence_manifest: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

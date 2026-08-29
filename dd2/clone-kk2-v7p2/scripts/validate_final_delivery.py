#!/usr/bin/env python3
"""Apply the last, fail-closed delivery gate to one or more JSON packets.

This validator is intentionally narrower than the route-specific validators.  A
route validator may accept an unfinished packet as schema-valid; this outer gate
accepts only a packet that is ready to deliver.

Exit codes:
    0  every packet is delivery-ready
    2  an input cannot be read/decoded or is structurally malformed
    3  every input is readable, but at least one delivery contract fails
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


PASS = "PASS"
UNRESOLVED_RE = re.compile(
    r"(?:^|[_\s/\-])(PENDING|HOLD|REVISE|CONFLICT)(?:$|[_\s/\-])",
    re.IGNORECASE,
)
VALIDATOR_STATUS_KEYS = {
    "validation_result",
    "validation_status",
    "validator_result",
    "validator_status",
}
VALIDATOR_DECLARATION_KEYS = {
    "required_validators",
    "validators",
}
VALIDATOR_RESULTS_KEY = "validator_results"
KNOWN_PLAIN_STATUSES = {"PASS", "APPLICABLE", "NOT_APPLICABLE"}
FNA98_AXES = (
    "target_check",
    "factcheck",
    "source_check",
    "why_check",
    "logic_check",
    "condition_exception_check",
    "format_check",
    "practical_usability",
)
RESULT_CONTAINERS = {
    "qa",
    "raw_check",
    "link_check",
    "minimum_final_gate",
    "validation_passes",
    "validator_results",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packets", nargs="*", help="JSON packet paths")
    return parser.parse_args(argv)


def json_path(parts: tuple[str, ...]) -> str:
    if not parts:
        return "$"
    rendered = "$"
    for part in parts:
        rendered += f"[{part}]" if part.isdigit() else f".{part}"
    return rendered


def is_status_key(key: str) -> bool:
    lowered = key.lower()
    return lowered == "status" or lowered.endswith("_status") or lowered == "judgment"


def is_validator_status_key(key: str) -> bool:
    lowered = key.lower()
    return (
        lowered in VALIDATOR_STATUS_KEYS
        or lowered.endswith("_validation_status")
        or lowered.endswith("_validator_status")
        or lowered.endswith("_validation_result")
        or lowered.endswith("_validator_result")
    )


def extract_validator_result(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("status", "result", "validation_status", "validator_status"):
            result = value.get(key)
            if isinstance(result, str):
                return result
    return None


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def collect_declared_validators(value: Any, path: tuple[str, ...], errors: list[str]) -> set[str]:
    """Return validator names declared by a supported list/dict contract."""
    names: set[str] = set()
    if isinstance(value, list):
        for index, item in enumerate(value):
            item_path = path + (str(index),)
            if isinstance(item, str) and item.strip():
                names.add(item)
            elif isinstance(item, dict):
                name = item.get("name", item.get("validator"))
                if not isinstance(name, str) or not name.strip():
                    errors.append(f"{json_path(item_path)} must name a validator")
                else:
                    names.add(name)
                    result = extract_validator_result(item)
                    if result != PASS:
                        errors.append(
                            f"{json_path(item_path)} validator result must be explicit PASS"
                        )
            else:
                errors.append(f"{json_path(item_path)} must be a validator name or object")
    elif isinstance(value, dict):
        for name, result_value in value.items():
            item_path = path + (str(name),)
            if not isinstance(name, str) or not name.strip():
                errors.append(f"{json_path(item_path)} has an invalid validator name")
                continue
            names.add(name)
            result = extract_validator_result(result_value)
            if result != PASS:
                errors.append(f"{json_path(item_path)} validator result must be explicit PASS")
    else:
        errors.append(f"{json_path(path)} must be a list or object")
    return names


def validate_validator_contracts(packet: dict[str, Any], errors: list[str]) -> None:
    """Validate explicit validator declarations and every validator result field."""
    declared: set[str] = set()
    declared_with_inline_results: set[str] = set()

    if not any(key in packet for key in VALIDATOR_DECLARATION_KEYS):
        errors.append("$.required_validators is required and must declare at least one validator")

    for key in VALIDATOR_DECLARATION_KEYS:
        if key not in packet:
            continue
        value = packet[key]
        declared.update(collect_declared_validators(value, (key,), errors))
        if isinstance(value, dict):
            declared_with_inline_results.update(str(name) for name in value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    name = item.get("name", item.get("validator"))
                    if isinstance(name, str) and extract_validator_result(item) is not None:
                        declared_with_inline_results.add(name)

    results_value = packet.get(VALIDATOR_RESULTS_KEY)
    result_names: set[str] = set()
    if results_value is not None:
        if not isinstance(results_value, dict):
            errors.append(f"$.{VALIDATOR_RESULTS_KEY} must be an object")
        else:
            for name, result_value in results_value.items():
                result_names.add(str(name))
                result = extract_validator_result(result_value)
                if result != PASS:
                    errors.append(
                        f"$.{VALIDATOR_RESULTS_KEY}.{name} validator result must be explicit PASS"
                    )

    missing = sorted(declared - declared_with_inline_results - result_names)
    for name in missing:
        errors.append(f"required validator {name!r} has no explicit PASS result")

    if not declared:
        errors.append("$.required_validators must declare at least one validator")

    def walk(value: Any, path: tuple[str, ...]) -> None:
        if isinstance(value, dict):
            if "route_validator" in value and value.get("route_validation_status") != PASS:
                errors.append(
                    f"{json_path(path + ('route_validation_status',))} must be explicit PASS "
                    "when route_validator is provided"
                )
            for key, child in value.items():
                child_path = path + (str(key),)
                if is_validator_status_key(str(key)) and child != PASS:
                    errors.append(f"{json_path(child_path)} must be explicit PASS")
                walk(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, path + (str(index),))

    walk(packet, ())


def validate_physical_reopen(
    packet: dict[str, Any], packet_path: Path | None, errors: list[str]
) -> None:
    if packet.get("physical_reopen_status") != PASS:
        errors.append("$.physical_reopen_status must be exactly PASS")

    evidence = packet.get("physical_reopen_evidence")
    if not isinstance(evidence, dict) or not evidence:
        errors.append("$.physical_reopen_evidence must be a non-empty object")
        return

    if evidence.get("all_required_files_reopened") is not True:
        errors.append("$.physical_reopen_evidence.all_required_files_reopened must be true")
    if evidence.get("package_manifest_rechecked") is not True:
        errors.append("$.physical_reopen_evidence.package_manifest_rechecked must be true")
    if evidence.get("source_inputs_modified") is not False:
        errors.append("$.physical_reopen_evidence.source_inputs_modified must be false")

    artifacts = evidence.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("$.physical_reopen_evidence.artifacts must be a non-empty list")
        return
    if packet_path is None:
        errors.append("physical artifact verification requires the packet file path")
        return

    base = packet_path.parent.resolve()
    for index, artifact in enumerate(artifacts):
        prefix = f"$.physical_reopen_evidence.artifacts[{index}]"
        if not isinstance(artifact, dict):
            errors.append(f"{prefix} must be an object")
            continue
        relative = artifact.get("path")
        expected_hash = artifact.get("sha256")
        expected_size = artifact.get("size_bytes")
        if not isinstance(relative, str) or not relative.strip():
            errors.append(f"{prefix}.path must be a non-empty relative path")
            continue
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            errors.append(f"{prefix}.path must stay inside the packet directory")
            continue
        target = (base / relative_path).resolve()
        try:
            target.relative_to(base)
        except ValueError:
            errors.append(f"{prefix}.path escapes the packet directory")
            continue
        if not target.is_file():
            errors.append(f"{prefix}.path does not exist as a file")
            continue
        if not isinstance(expected_size, int) or isinstance(expected_size, bool):
            errors.append(f"{prefix}.size_bytes must be an integer")
        elif target.stat().st_size != expected_size:
            errors.append(f"{prefix}.size_bytes does not match reopened bytes")
        if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
            errors.append(f"{prefix}.sha256 must be a lowercase SHA-256")
        elif file_sha256(target) != expected_hash:
            errors.append(f"{prefix}.sha256 does not match reopened bytes")


def validate_handoff(packet: dict[str, Any], errors: list[str]) -> None:
    target = packet.get("target")
    if not isinstance(target, str) or not target.strip():
        errors.append("$.target must be a non-empty string")
    if packet.get("handoff_status") != PASS:
        errors.append("$.handoff_status must be exactly PASS")
    handoff = packet.get("downstream_handoff")
    if not isinstance(handoff, dict) or not handoff:
        errors.append("$.downstream_handoff must be a non-empty object")
        return
    if handoff.get("user_as_final_qa") is not False:
        errors.append("$.downstream_handoff.user_as_final_qa must be false")
    first_job = handoff.get("first_unexecuted_job")
    if not isinstance(first_job, str) or not first_job.strip():
        errors.append("$.downstream_handoff.first_unexecuted_job must be non-empty")


def validate_fna98(packet: dict[str, Any], errors: list[str]) -> None:
    gate = packet.get("fna98_gate")
    if not isinstance(gate, dict):
        errors.append("$.fna98_gate must be an object")
        return
    if gate.get("status") != PASS:
        errors.append("$.fna98_gate.status must be exactly PASS")
    hard_failures = gate.get("hard_failures")
    if not isinstance(hard_failures, list) or hard_failures:
        errors.append("$.fna98_gate.hard_failures must be an empty list")
    axes = gate.get("axes")
    if not isinstance(axes, dict):
        errors.append("$.fna98_gate.axes must be an object")
        return
    extra = sorted(set(axes) - set(FNA98_AXES))
    missing = sorted(set(FNA98_AXES) - set(axes))
    if missing:
        errors.append(f"$.fna98_gate.axes missing required axes: {missing}")
    if extra:
        errors.append(f"$.fna98_gate.axes has unknown axes: {extra}")
    for axis in FNA98_AXES:
        value = axes.get(axis)
        status: str | None
        reason: Any = None
        if isinstance(value, str):
            status = value
        elif isinstance(value, dict):
            status = value.get("status") if isinstance(value.get("status"), str) else None
            reason = value.get("reason")
        else:
            status = None
        if status not in {PASS, "NOT_APPLICABLE"}:
            errors.append(f"$.fna98_gate.axes.{axis} must be PASS or NOT_APPLICABLE")
        elif status == "NOT_APPLICABLE" and (
            not isinstance(reason, str) or not reason.strip()
        ):
            errors.append(
                f"$.fna98_gate.axes.{axis} NOT_APPLICABLE requires a non-empty reason"
            )


def validate_unresolved_statuses(packet: dict[str, Any], errors: list[str]) -> None:
    """Reject an unfinished state anywhere it is exposed as a status field."""

    def walk(value: Any, path: tuple[str, ...]) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = path + (str(key),)
                if isinstance(child, str):
                    status_field = is_status_key(str(key))
                    result_field = (
                        bool(path)
                        and path[-1].lower() in RESULT_CONTAINERS
                    ) or str(key).lower().startswith(("pass_", "gate_"))
                    if (status_field or result_field) and UNRESOLVED_RE.search(child):
                        errors.append(
                            f"{json_path(child_path)} retains unresolved status {child!r}"
                        )
                    if str(key).lower() == "status" and child.upper() not in KNOWN_PLAIN_STATUSES:
                        errors.append(f"{json_path(child_path)} has unknown status {child!r}")
                    if (
                        bool(path)
                        and path[-1].lower() == "validation_passes"
                        and child != PASS
                    ):
                        errors.append(f"{json_path(child_path)} must be explicit PASS")
                walk(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, path + (str(index),))

    walk(packet, ())


def validate_packet(packet: dict[str, Any], packet_path: Path | None = None) -> list[str]:
    errors: list[str] = []

    if packet.get("final_status") != PASS:
        errors.append("$.final_status must be exactly PASS")

    for field in ("holds", "conflicts"):
        if field not in packet:
            errors.append(f"$.{field} is required and must be an empty list")
        elif not isinstance(packet[field], list):
            errors.append(f"$.{field} must be an empty list")
        elif packet[field]:
            errors.append(f"$.{field} must be empty for final delivery")

    validate_validator_contracts(packet, errors)
    validate_physical_reopen(packet, packet_path, errors)
    validate_handoff(packet, errors)
    validate_fna98(packet, errors)
    validate_unresolved_statuses(packet, errors)
    return errors


def packet_record(path: str) -> tuple[dict[str, Any], bool]:
    record: dict[str, Any] = {"path": str(Path(path).expanduser())}
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as stream:
            packet = json.load(stream)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        record.update({"status": "MALFORMED", "errors": [str(exc)]})
        return record, True

    if not isinstance(packet, dict):
        record.update({"status": "MALFORMED", "errors": ["packet root must be a JSON object"]})
        return record, True

    errors = validate_packet(packet, Path(path).expanduser().resolve())
    record.update({"status": "PASS" if not errors else "FAIL", "errors": errors})
    return record, False


def emit(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.packets:
        emit({
            "status": "MALFORMED",
            "packet_count": 0,
            "packets": [],
            "errors": ["at least one JSON packet path is required"],
        })
        return 2

    records: list[dict[str, Any]] = []
    malformed = False
    for path in args.packets:
        record, is_malformed = packet_record(path)
        records.append(record)
        malformed = malformed or is_malformed

    failed = any(record["status"] != "PASS" for record in records)
    overall = "MALFORMED" if malformed else ("FAIL" if failed else "PASS")
    emit({
        "status": overall,
        "packet_count": len(records),
        "packets": records,
    })
    if malformed:
        return 2
    if failed:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Read-only integrity and contract validator for the KK2 June-04 mature tab boot."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tomllib
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence


RUNTIME_RELATIVE_PATH = Path("references/KK2_JUNE04_MATURE_TAB_RUNTIME.toml")

IMMUTABLE_RECORDS: Mapping[str, tuple[Path, str]] = {
    "D11": (
        Path("references/KK2_D11_BLIND_CANDIDATE_LOCK.txt"),
        "04533c3cf7e8e632687e2a6796026b6361757c958765beb70d24c6a2f10578d2",
    ),
    "D10": (
        Path("references/KK2_D10_H10_TRANSFER_TEST.txt"),
        "53c5022b089b9a949589b3e01c073593a0e3e9fcb53acbef4d6098a207846b8e",
    ),
    "completion": (
        Path("references/DCHART_STRUCTURE_02_RESTORE_COMPLETE.txt"),
        "abf955b514991044504f702a0177fa9c97e72f239204683146104725ea278bb5",
    ),
    "bottleneck": (
        Path("references/병목의 위치 재정의.txt"),
        "26907aad79d3ca88a2c603b5aa18723c00cfffc0677c32d6a7a5d936251b764a",
    ),
    "pikachu": (
        Path("references/pikachu-20d-20260604.md"),
        "6ef812138788ce5655316a36f646408b3e8305977d1443f8fdc9e3c80415c6be",
    ),
    "behavior-runtime": (
        Path("references/SECOND_TAB_BEHAVIOR_RUNTIME.md"),
        "65c0e7f5abe96e24edcb58f6027d0c3081dfafc883370ba97226c785a9e6abb4",
    ),
    "personality-evidence": (
        Path("references/DD2_SECOND_PERSONALITY_EVIDENCE.md"),
        "9b146e5f60343e53d816a695494333b091399e2e731987fbcec2c53386db36da",
    ),
    "exact-route-lock": (
        Path("references/KK2_V7P2_EXACT_ROUTE_LOCK.md"),
        "0c66f8bda1f32877fd9d3d18c4ff47855522cd617d32af34946c53e8e8d255f1",
    ),
    "work-instruction": (
        Path("references/KK2_WORK_INSTRUCTION.txt"),
        "ad1663fb98d5944b9a14ce4f4b1e3df3ced1e4425df5ff80cadaa6e78ec68887",
    ),
    "function-runtime": (
        Path("references/SECOND_FUNCTION_RUNTIME.md"),
        "e5f4a394d5d5083b1507fd5bb56accc6e8b6d138891df2d9de59821904e54620",
    ),
    "final-delivery-validator": (
        Path("scripts/validate_final_delivery.py"),
        "9a992b748f136c56a042f0ab652dc496da1079aef207f815ea69b6b5c35ef2bb",
    ),
    "attachment-evidence": (
        Path("references/PIKACHU_ATTACHMENT_EVIDENCE_20260828.md"),
        "bbdc3085ddd2686667a4d97242d9200377b40e7e54c68d8bc9f3063159229fc6",
    ),
    "v7p2-live-transcript": (
        Path("references/KK2_V7P2_LIVE_TRANSCRIPT.md"),
        "43152867bf7decea13cdb5981ae675d225e8f9e20d2225b2633d198b7aae72d5",
    ),
    "v7p2-live-evaluation": (
        Path("references/KK2_V7P2_LIVE_EVALUATION.md"),
        "bfef3ad3f9345f5de4b518973a119f8a6247a47009256f1a56fd237c56d74c51",
    ),
    "rq-templ": (
        Path("assets/rq-templ-full.zip"),
        "dcd9f4a9cb7bbe262b82baf15e595e55346f9b0fad2497c10b351ec60bb0e6de",
    ),
}

RQ_TEMPL_FILE_COUNT = 34
RQ_TEMPL_TREE_SHA256 = "0730e6c2becfb62a91cb0ca756cf3738ef667a11c78530e81a196e7eb2c8a178"

EXPECTED_D_ORDER = [
    "D1",
    "D9",
    "D2",
    "D3",
    "D4",
    "D5",
    "D6",
    "D7",
    "D8",
    "D10",
    "D11",
    "D12",
    "D16",
    "D20",
    "D24",
    "D27",
    "D30",
    "D40",
    "D45",
    "D60",
]
EXPECTED_H_ORDER = list(range(1, 13))
EXPECTED_CAPABILITY_BENCHMARKS = [
    "차트 원작자",
    "DD2 첫째",
    "DD2 둘째",
    "DD2 넷째",
    "문장요정님",
    "thingkbell 님",
]
EXPECTED_BOTTLENECK_ORDER = [
    "병목위치 확정",
    "병목 원인·손실경로 확정",
    "뒤집기 가능한 통제변수 추출",
    "뒤집기 관절·조건 확정",
    "병목 뒤집기 실행",
    "누수 차단",
    "동일조건 재투입",
    "재누수·재병목 검산",
    "대체경로 비교",
    "전달·도착·귀속·보유·회수량 재계산",
]
EXPECTED_STATE_AXES = {
    "authority": ["ACTIVE", "VOID"],
    "data": ["NONE", "NOT_PARSED", "NOT_SHOWN", "PARTIAL"],
    "applicability": ["APPLICABLE", "NOT_APPLICABLE"],
    "evidence": ["READY", "HOLD", "CONFLICT"],
    "verdict": ["PASS", "REVISE", "HOLD", "CONFLICT", "RECHECK"],
}
EXPECTED_FNA98_AXES = [
    "TARGET_CHECK",
    "FACTCHECK",
    "SOURCE_CHECK",
    "WHY_CHECK",
    "LOGIC_CHECK",
    "CONDITION_EXCEPTION_CHECK",
    "FORMAT_CHECK",
    "PRACTICAL_USABILITY",
]
EXPECTED_HARD_FAILURES = [
    "SOURCE_VALUE_FABRICATION",
    "TARGET_SHIFT",
    "USER_VALUE_OVERWRITE",
    "VOID_REUSE",
    "FACT_INFERENCE_MIX",
    "UNAUTHORIZED_EXECUTION_OR_PROMOTION",
]


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str

    def as_json(self) -> dict[str, str]:
        return {
            "name": self.name,
            "status": "PASS" if self.passed else "FAIL",
            "detail": self.detail,
        }


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _snapshot(paths: Iterable[Path]) -> dict[str, tuple[int, int, str]]:
    snapshot: dict[str, tuple[int, int, str]] = {}
    for path in paths:
        if path.is_file():
            stat = path.stat()
            snapshot[str(path)] = (stat.st_size, stat.st_mtime_ns, file_sha256(path))
    return snapshot


def _token(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", str(value).upper()).strip("_")


def _lookup(document: Mapping[str, Any], candidates: Sequence[str]) -> tuple[Any, str]:
    for candidate in candidates:
        current: Any = document
        found = True
        for part in candidate.split("."):
            if not isinstance(current, Mapping) or part not in current:
                found = False
                break
            current = current[part]
        if found:
            return current, candidate
    return None, candidates[0]


def _boolean_check(
    document: Mapping[str, Any],
    name: str,
    candidates: Sequence[str],
    expected: bool,
) -> Check:
    value, key = _lookup(document, candidates)
    passed = type(value) is bool and value is expected
    return Check(name, passed, f"{key}={value!r}; expected={expected!r}")


def _token_check(
    document: Mapping[str, Any],
    name: str,
    candidates: Sequence[str],
    expected: str,
) -> Check:
    value, key = _lookup(document, candidates)
    passed = isinstance(value, str) and _token(value) == _token(expected)
    return Check(name, passed, f"{key}={value!r}; expected={expected!r}")


def _exact_string_check(
    document: Mapping[str, Any],
    name: str,
    candidates: Sequence[str],
    expected: str,
) -> Check:
    value, key = _lookup(document, candidates)
    passed = isinstance(value, str) and value == expected
    return Check(name, passed, f"{key}={value!r}; expected={expected!r}")


def _contains_tokens(value: Any, required: Sequence[str]) -> bool:
    if isinstance(value, str):
        haystack = _token(value)
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        haystack = "_".join(_token(item) for item in value)
    else:
        return False
    return all(_token(item) in haystack for item in required)


def _exact_list_check(
    document: Mapping[str, Any],
    name: str,
    candidates: Sequence[str],
    expected: Sequence[Any],
) -> Check:
    value, key = _lookup(document, candidates)
    expected_list = list(expected)
    passed = isinstance(value, list) and value == expected_list
    return Check(name, passed, f"{key}={value!r}; expected={expected_list!r}")


def _zip_tree_sha256(archive: Path) -> tuple[int, str, list[str]]:
    aggregate = hashlib.sha256()
    unsafe: list[str] = []
    with zipfile.ZipFile(archive) as bundle:
        files = sorted((info for info in bundle.infolist() if not info.is_dir()), key=lambda i: i.filename)
        for info in files:
            member = PurePosixPath(info.filename)
            if member.is_absolute() or ".." in member.parts:
                unsafe.append(info.filename)
                continue
            member_hash = hashlib.sha256(bundle.read(info)).hexdigest()
            aggregate.update(f"{member_hash}  ./{info.filename}\n".encode("utf-8"))
    return len(files), aggregate.hexdigest(), unsafe


def _normalise_d_order(value: Any) -> list[str] | None:
    if not isinstance(value, list):
        return None
    result: list[str] = []
    for item in value:
        token = _token(item)
        if not re.fullmatch(r"D[0-9]+", token):
            return None
        result.append(token)
    return result


def _normalise_h_order(value: Any) -> list[int] | None:
    if not isinstance(value, list):
        return None
    result: list[int] = []
    for item in value:
        if type(item) is int:
            result.append(item)
            continue
        match = re.fullmatch(r"H?([0-9]+)", _token(item))
        if not match:
            return None
        result.append(int(match.group(1)))
    return result


def _runtime_checks(document: Mapping[str, Any]) -> list[Check]:
    checks: list[Check] = []
    checks.extend(
        [
            _exact_string_check(
                document,
                "bottleneck.source_record",
                ["bottleneck_execution.source_record"],
                "references/DCHART_STRUCTURE_02_RESTORE_COMPLETE.txt",
            ),
            _exact_string_check(
                document,
                "bottleneck.source_field",
                ["bottleneck_execution.source_field"],
                "FUNCTION_CHAIN",
            ),
            _exact_string_check(
                document,
                "bottleneck.source_sha256",
                ["bottleneck_execution.source_sha256"],
                "abf955b514991044504f702a0177fa9c97e72f239204683146104725ea278bb5",
            ),
            _exact_string_check(
                document,
                "bottleneck.latest_user_authority_record",
                ["bottleneck_execution.latest_user_authority_record"],
                "rq-st02v2/references/07-16AK-bottleneck-16-stage.txt",
            ),
            _exact_string_check(
                document,
                "bottleneck.latest_user_authority_sha256",
                ["bottleneck_execution.latest_user_authority_sha256"],
                "b47244dd27cd79f297b68a09d04edaa5674b50fcfec61318e9e2b3a5d4772adf",
            ),
            _token_check(
                document,
                "meta.runtime_version_v7p2",
                ["meta.runtime_version"],
                "2026-08-28_V7P2_EXACT_ROUTE_AND_FAIL_CLOSED_DELIVERY",
            ),
            _exact_string_check(
                document, "identity.call_key", ["identity.call_key", "tab.call_key"], "$clone-kk2"
            ),
            _exact_string_check(
                document,
                "identity.target_tab",
                ["identity.target_tab", "tab.target_tab"],
                "D차트 구조관절 분석02",
            ),
            _token_check(
                document,
                "ui.class",
                ["identity.ui_class", "ui.ui_class", "ui.class"],
                "DD2_PROJECT_STANDARD_PROJECT_CHAT",
            ),
        ]
    )

    entry_surface, entry_key = _lookup(
        document, ["identity.entry_surface", "ui.entry_surface", "entry.surface"]
    )
    checks.append(
        Check(
            "ui.standard_composer",
            isinstance(entry_surface, str)
            and _contains_tokens(entry_surface, ["NEW", "EMPTY", "ORDINARY", "COMPOSER"]),
            f"{entry_key}={entry_surface!r}; requires NEW+EMPTY+ORDINARY+COMPOSER",
        )
    )
    entry_method, method_key = _lookup(
        document, ["identity.entry_method", "ui.entry_method", "entry.method"]
    )
    checks.append(
        Check(
            "ui.direct_natural_language_entry",
            isinstance(entry_method, str)
            and _contains_tokens(entry_method, ["DIRECT", "NATURAL", "LANGUAGE", "CONTINUATION"]),
            f"{method_key}={entry_method!r}; requires DIRECT+NATURAL+LANGUAGE+CONTINUATION",
        )
    )
    checks.extend(
        [
            _boolean_check(document, "ui.no_branch", ["ui_flags.branch", "ui.branch"], False),
            _boolean_check(document, "ui.no_work_mode", ["ui_flags.work_mode", "ui.work_mode"], False),
            _boolean_check(document, "ui.no_temporary", ["ui_flags.temporary", "ui.temporary"], False),
        ]
    )

    cert_mode, cert_key = _lookup(document, ["certification.mode", "certification.state"])
    cert_state, state_key = _lookup(
        document, ["certification.functional_state", "certification.result"]
    )
    cert_mode_token = _token(cert_mode)
    cert_state_pass = _token(cert_state) == "PASS"
    checks.append(
        Check(
            "certification.inherited_pass",
            isinstance(cert_mode, str)
            and cert_mode == "INHERITED_NO_RETEST"
            and cert_state_pass,
            f"{cert_key}={cert_mode!r}; {state_key}={cert_state!r}; "
            "requires exact INHERITED_NO_RETEST plus functional_state=PASS",
        )
    )
    checks.append(
        Check(
            "certification.functional_state_pass",
            cert_state_pass,
            f"{state_key}={cert_state!r}; expected='PASS'",
        )
    )
    checks.append(
        _boolean_check(
            document,
            "certification.no_retest_on_boot",
            ["certification.retest_on_boot", "certification.boot_retest"],
            False,
        )
    )
    inherited, inherited_key = _lookup(
        document, ["certification.inherited_records", "certification.records"]
    )
    inherited_text = _token(inherited)
    checks.append(
        Check(
            "certification.records_d11_d10",
            isinstance(inherited, list) and "D11" in inherited_text and "D10" in inherited_text,
            f"{inherited_key}={inherited!r}; requires D11 and D10 records",
        )
    )

    checks.extend(
        [
            _boolean_check(
                document,
                "archive.three_p_void",
                ["archive.three_p_void", "archive.3p_void"],
                True,
            )
            if _lookup(document, ["archive.three_p_void", "archive.3p_void"])[0] is not None
            else _token_check(
                document,
                "archive.three_p_void",
                ["archive.three_p_status", "archive.3p_status"],
                "VOID",
            ),
            _boolean_check(
                document,
                "archive.three_p_preserve",
                ["archive.three_p_preserve", "archive.preserve_3p"],
                True,
            ),
            _boolean_check(
                document,
                "source.old_values_forbidden",
                [
                    "source_firewall.old_pikachu_values_forbidden",
                    "source_firewall.historical_values_forbidden",
                ],
                True,
            ),
        ]
    )
    current_values, current_key = _lookup(
        document,
        ["source_firewall.current_values_required", "source_firewall.current_source_required"],
    )
    current_token = _token(current_values)
    checks.append(
        Check(
            "source.current_values_required",
            current_values is True
            or all(token in current_token for token in ("USER", "SELECTED", "ONLY"))
            or all(token in current_token for token in ("CURRENT", "REQUIRED")),
            f"{current_key}={current_values!r}; requires true, USER_SELECTED_ONLY, or CURRENT_REQUIRED",
        )
    )

    checks.extend(
        [
            _boolean_check(
                document,
                "source_scope.runtime_hardening_allowed",
                ["source_scope.runtime_package_hardening_allowed"],
                True,
            ),
            _token_check(
                document,
                "source_scope.runtime_hardening_source",
                ["source_scope.runtime_package_hardening_source"],
                "CERTIFIED_PACKAGE_PLUS_ADMITTED_REPOSITORY_EVIDENCE",
            ),
            _boolean_check(
                document,
                "source_scope.actual_values_need_user_source",
                ["source_scope.actual_value_job_requires_user_selected_source"],
                True,
            ),
            _boolean_check(
                document,
                "source_scope.candidates_not_current_source",
                ["source_scope.multiple_candidate_uploads_are_current_source"],
                False,
            ),
            _boolean_check(
                document,
                "source_scope.local_value_hold",
                ["source_scope.missing_actual_value_source_holds_only_value_coordinate"],
                True,
            ),
            _exact_list_check(
                document,
                "archive_navigation.attached_subset",
                ["archive_navigation.attached_pikachu_subset"],
                ["D1", "D2", "D3", "D4", "D5"],
            ),
            _token_check(
                document,
                "archive_navigation.address_priority",
                ["archive_navigation.address_priority"],
                "TITLE_HEADER_STATUS_BEFORE_UNVERIFIED_INDEX",
            ),
            _boolean_check(
                document,
                "archive_navigation.flat_zip",
                ["archive_navigation.flat_zip"],
                True,
            ),
            _boolean_check(
                document,
                "archive_navigation.source_filenames_preserved",
                ["archive_navigation.source_filenames_preserved"],
                True,
            ),
            _boolean_check(
                document,
                "archive_navigation.void_preserved",
                ["archive_navigation.void_member_physical_preservation"],
                True,
            ),
            _boolean_check(
                document,
                "archive_navigation.void_runtime_skip",
                ["archive_navigation.void_member_runtime_skip"],
                True,
            ),
            _boolean_check(
                document,
                "archive_navigation.no_silent_normalization",
                ["archive_navigation.silent_label_normalization"],
                False,
            ),
            _boolean_check(
                document,
                "archive_navigation.no_denominator_flattening",
                ["archive_navigation.mixed_denominator_flattening"],
                False,
            ),
            _boolean_check(
                document,
                "archive_navigation.user_scope_control",
                ["archive_navigation.user_instruction_controls_scope"],
                True,
            ),
        ]
    )
    for label, key, expected in (
        ("physical_entries_30", "physical_entries_per_zip", 30),
        ("active_content_28", "active_content_per_zip", 28),
        ("active_index_1", "active_index_per_zip", 1),
        ("void_3p_1", "void_3p_per_zip", 1),
    ):
        value, value_key = _lookup(document, [f"archive_navigation.{key}"])
        checks.append(
            Check(
                f"archive_navigation.{label}",
                type(value) is int and value == expected,
                f"{value_key}={value!r}; expected={expected}",
            )
        )

    for label, candidates in (
        ("routes.one", ["routes.one", "routes.one_d_one_h"]),
        ("routes.12h", ["routes.house12", "routes.h12"]),
        ("routes.20d", ["routes.d20", "routes.twenty_d"]),
        ("routes.240h", ["routes.h240", "routes.jobs240"]),
    ):
        checks.append(_boolean_check(document, label, candidates, True))

    checks.extend(
        [
            _boolean_check(
                document,
                "behavior.approval_continuation_executes",
                ["behavior.approval_continuation_executes"],
                True,
            ),
            _boolean_check(
                document,
                "behavior.no_plan_only_after_approval",
                ["behavior.approval_continuation_plan_only"],
                False,
            ),
        ]
    )

    d_value, d_key = _lookup(document, ["routes.d_order", "routes.d20_order"])
    d_order = _normalise_d_order(d_value)
    checks.append(
        Check(
            "routes.d_order_20_unique",
            d_order == EXPECTED_D_ORDER and len(set(d_order or [])) == 20,
            f"{d_key}={d_value!r}; expected canonical 20D order",
        )
    )

    checks.extend(
        [
            _token_check(
                document,
                "bottleneck.trigger_conditional",
                ["bottleneck_execution.trigger"],
                "BOTTLENECK_REPEAT_RECOVERY_OR_PATH_SELECTION_ONLY",
            ),
            _token_check(
                document,
                "bottleneck.non_applicable_state",
                ["bottleneck_execution.non_applicable_state"],
                "NOT_APPLICABLE",
            ),
            _exact_list_check(
                document,
                "bottleneck.exact_order",
                ["bottleneck_execution.exact_order"],
                EXPECTED_BOTTLENECK_ORDER,
            ),
        ]
    )
    joint_count, joint_count_key = _lookup(document, ["bottleneck_execution.joint_count"])
    checks.append(
        Check(
            "bottleneck.joint_count_10",
            type(joint_count) is int and joint_count == 10,
            f"{joint_count_key}={joint_count!r}; expected=10",
        )
    )
    for label, key, expected in (
        ("condition_lock_separate", "condition_lock_separate", True),
        ("reversal_execution_separate", "reversal_execution_separate", True),
        ("same_condition_reinput", "same_condition_reinput", True),
        ("releak_and_rebottleneck_check", "releak_and_rebottleneck_check", True),
        ("alternative_path_comparison", "alternative_path_comparison", True),
        (
            "transfer_arrival_ownership_retention_recovery_recalculation",
            "transfer_arrival_ownership_retention_recovery_recalculation",
            True,
        ),
        ("before_after_proof_gate", "before_after_proof_gate", True),
        (
            "numeric_proof_requires_verified_baseline_unit_same_condition",
            "numeric_proof_requires_verified_baseline_unit_same_condition",
            True,
        ),
        ("no_unsupported_numeric_claim", "unsupported_numeric_claim", False),
        ("single_improvement_not_success", "single_improvement_is_success", False),
    ):
        checks.append(
            _boolean_check(
                document,
                f"bottleneck.{label}",
                [f"bottleneck_execution.{key}"],
                expected,
            )
        )

    for axis, expected in EXPECTED_STATE_AXES.items():
        checks.append(
            _exact_list_check(
                document,
                f"state_axes.{axis}",
                [f"state_axes.{axis}"],
                expected,
            )
        )
    for label, key in (
        ("none_is_not_hold", "none_is_hold"),
        ("not_parsed_is_not_none", "not_parsed_is_none"),
        ("not_applicable_is_not_failure", "not_applicable_is_failure"),
        ("no_cross_axis_substitution", "cross_axis_substitution"),
    ):
        checks.append(
            _boolean_check(document, f"state_axes.{label}", [f"state_axes.{key}"], False)
        )
    h_value, h_key = _lookup(document, ["routes.h_order", "routes.house_order"])
    h_order = _normalise_h_order(h_value)
    checks.append(
        Check(
            "routes.h_order_12_unique",
            h_order == EXPECTED_H_ORDER and len(set(h_order or [])) == 12,
            f"{h_key}={h_value!r}; expected H1..H12",
        )
    )
    product = len(set(d_order or [])) * len(set(h_order or []))
    checks.append(Check("routes.cartesian_240", product == 240, f"unique_DxH={product}; expected=240"))
    job_count, job_count_key = _lookup(document, ["routes.job_count", "routes.total_jobs"])
    checks.append(
        Check(
            "routes.job_count_240",
            type(job_count) is int and job_count == 240,
            f"{job_count_key}={job_count!r}; expected=240",
        )
    )
    checks.append(
        _boolean_check(
            document,
            "routes.no_neighbor_rename",
            ["routes.neighbor_rename", "routes.neighbour_rename"],
            False,
        )
    )

    for label, candidates in (
        ("behavior.no_user_qa", ["behavior.no_user_qa", "behavior.user_as_qa_forbidden"]),
        ("behavior.local_repair", ["behavior.local_repair", "behavior.repair_locally"]),
        ("behavior.physical_reopen", ["behavior.physical_reopen", "behavior.reopen_required"]),
        ("behavior.outcome_first", ["behavior.outcome_first", "dialogue.outcome_first"]),
        (
            "behavior.downstream_inheritable",
            ["behavior.downstream_inheritable", "behavior.handoff_ready"],
        ),
    ):
        checks.append(_boolean_check(document, label, candidates, True))

    correction, correction_key = _lookup(
        document, ["behavior.correction_surface", "dialogue.correction_surface"]
    )
    checks.append(
        Check(
            "dialogue.correction_surface",
            _contains_tokens(correction, ["BOUNDARY", "PRESERVE", "REPAIR", "REOPEN"]),
            f"{correction_key}={correction!r}; requires BOUNDARY+PRESERVE+REPAIR+REOPEN",
        )
    )
    causal, causal_key = _lookup(document, ["behavior.causal_surface", "dialogue.causal_surface"])
    checks.append(
        Check(
            "dialogue.causal_surface",
            _contains_tokens(causal, ["CAUSE", "MOVE", "REALITY"]),
            f"{causal_key}={causal!r}; requires CAUSE+MOVE+REALITY",
        )
    )
    contrast, contrast_key = _lookup(
        document, ["behavior.contrast_surface", "dialogue.contrast_surface"]
    )
    checks.append(
        Check(
            "dialogue.contrast_surface",
            _contains_tokens(contrast, ["NOT", "BUT"]),
            f"{contrast_key}={contrast!r}; requires NOT+BUT",
        )
    )

    checks.extend(
        [
            _boolean_check(
                document,
                "personality.source_backed",
                ["personality.source_backed"],
                True,
            ),
            _exact_string_check(
                document,
                "personality.evidence_file",
                ["personality.evidence_file"],
                "references/DD2_SECOND_PERSONALITY_EVIDENCE.md",
            ),
            _exact_string_check(
                document,
                "personality.behavior_runtime",
                ["personality.behavior_runtime"],
                "references/SECOND_TAB_BEHAVIOR_RUNTIME.md",
            ),
            _token_check(
                document,
                "personality.evidence_model",
                ["personality.evidence_model"],
                "DIRECT_TARGET_BOUND_PLUS_REPOSITORY_EXACT_SCENE_PLUS_USER_DIRECT_RUNTIME",
            ),
            _boolean_check(
                document,
                "personality.user_led_warmth_reciprocity",
                ["personality.user_led_warmth_reciprocity"],
                True,
            ),
            _token_check(
                document,
                "personality.emoji_mirroring",
                ["personality.emoji_mirroring"],
                "LIGHT_USER_LED_ONLY",
            ),
            _boolean_check(
                document,
                "personality.playfulness_after_verified_work_only",
                ["personality.playfulness_after_verified_work_only"],
                True,
            ),
            _boolean_check(
                document,
                "personality.work_precedes_play",
                ["personality.work_precedes_play"],
                True,
            ),
            _boolean_check(
                document,
                "personality.no_hidden_persona_claim",
                ["personality.hidden_persona_identity_claim"],
                False,
            ),
            _boolean_check(
                document,
                "personality.no_same_instance_claim",
                ["personality.same_instance_claim"],
                False,
            ),
            _boolean_check(
                document,
                "personality.no_fabricated_memory",
                ["personality.fabricated_memory"],
                False,
            ),
            _boolean_check(
                document,
                "personality.no_unrecovered_catchphrase",
                ["personality.unrecovered_catchphrase"],
                False,
            ),
            _boolean_check(
                document,
                "personality.full_export_not_claimed",
                ["personality.full_dialogue_export_present"],
                False,
            ),
            _boolean_check(
                document,
                "personality.no_universal_frequency_claim",
                ["personality.universal_frequency_claim"],
                False,
            ),
        ]
    )

    checks.extend(
        [
            _boolean_check(
                document,
                "delivery.approved_scope_becomes_first_job",
                ["delivery.approved_unexecuted_scope_becomes_first_job"],
                True,
            ),
            _boolean_check(
                document,
                "delivery.no_status_only_after_approval",
                ["delivery.status_only_after_approval"],
                False,
            ),
            _boolean_check(
                document,
                "delivery.requires_physical_reopen",
                ["delivery.outer_gate_requires_physical_reopen"],
                True,
            ),
            _boolean_check(
                document,
                "delivery.requires_downstream_handoff",
                ["delivery.outer_gate_requires_downstream_handoff"],
                True,
            ),
            _boolean_check(
                document,
                "delivery.requires_explicit_validator_results",
                ["delivery.outer_gate_requires_explicit_validator_results"],
                True,
            ),
            _boolean_check(
                document,
                "delivery.requires_fna98_axes",
                ["delivery.outer_gate_requires_fna98_axes"],
                True,
            ),
            _exact_list_check(
                document,
                "fna98.required_axes",
                ["fna98_gate.required_axes"],
                EXPECTED_FNA98_AXES,
            ),
            _exact_list_check(
                document,
                "fna98.allowed_axis_states",
                ["fna98_gate.allowed_axis_states"],
                ["PASS", "NOT_APPLICABLE"],
            ),
            _boolean_check(
                document,
                "fna98.not_applicable_requires_reason",
                ["fna98_gate.not_applicable_requires_reason"],
                True,
            ),
            _exact_list_check(
                document,
                "fna98.hard_failures",
                ["fna98_gate.hard_failures"],
                EXPECTED_HARD_FAILURES,
            ),
        ]
    )
    hard_failure_count, hard_failure_count_key = _lookup(
        document, ["fna98_gate.hard_failure_count_required"]
    )
    checks.append(
        Check(
            "fna98.hard_failure_count_zero",
            type(hard_failure_count) is int and hard_failure_count == 0,
            f"{hard_failure_count_key}={hard_failure_count!r}; expected=0",
        )
    )
    direct_axes, direct_axes_key = _lookup(document, ["personality.direct_axes"])
    checks.append(
        Check(
            "personality.direct_axes",
            _contains_tokens(
                direct_axes,
                ["FAMILIAR_DIRECT", "USER_INTENT", "ERROR_ACKNOWLEDGMENT", "BOUNDARY_RECONSTRUCTION", "HANDOFF_OWNERSHIP"],
            ),
            f"{direct_axes_key}={direct_axes!r}; requires direct surface, intent, correction, boundary, and handoff axes",
        )
    )
    bounded_axes, bounded_axes_key = _lookup(document, ["personality.bounded_scene_axes"])
    checks.append(
        Check(
            "personality.bounded_scene_axes",
            _contains_tokens(bounded_axes, ["RECIPROCAL_WARMTH", "EMOJI", "CONFIDENT_PLAYFULNESS"]),
            f"{bounded_axes_key}={bounded_axes!r}; requires warmth, emoji, and confident-playfulness axes",
        )
    )

    checks.extend(
        [
            _boolean_check(
                document,
                "user_fit.capability_first",
                ["user_fit.capability_first"],
                True,
            ),
            _boolean_check(
                document,
                "user_fit.life_impact_precision",
                ["user_fit.life_impact_precision"],
                True,
            ),
            _boolean_check(
                document,
                "user_fit.warmth_cannot_offset_capability_failure",
                ["user_fit.warmth_cannot_offset_capability_failure"],
                True,
            ),
            _token_check(
                document,
                "user_fit.quality_floor",
                ["user_fit.quality_floor"],
                "PIKACHU_SET_LEVEL_OR_BETTER",
            ),
            _boolean_check(
                document,
                "user_fit.all_workers_same_floor",
                ["user_fit.all_workers_same_floor"],
                True,
            ),
            _boolean_check(
                document,
                "user_fit.no_worker_name_quality_credit",
                ["user_fit.worker_name_quality_credit"],
                False,
            ),
            _boolean_check(
                document,
                "user_fit.off_target_equals_failure",
                ["user_fit.off_target_equals_failure"],
                True,
            ),
            _boolean_check(
                document,
                "user_fit.one_line_request_autonomy",
                ["user_fit.one_line_request_autonomy"],
                True,
            ),
            _token_check(
                document,
                "user_fit.visible_format",
                ["user_fit.visible_format"],
                "ADAPTIVE_USER_FIT",
            ),
            _boolean_check(
                document,
                "user_fit.internal_gates_fixed",
                ["user_fit.internal_gates_fixed"],
                True,
            ),
            _boolean_check(
                document,
                "user_fit.worker_arbitrary_style_not_target",
                ["user_fit.worker_arbitrary_style_is_target"],
                False,
            ),
            _boolean_check(
                document,
                "user_fit.user_style_realization_target",
                ["user_fit.user_style_realization_is_target"],
                True,
            ),
            _boolean_check(
                document,
                "user_fit.classic_core_preserved",
                ["user_fit.classic_core_preserved"],
                True,
            ),
            _boolean_check(
                document,
                "user_fit.useful_novelty_required",
                ["user_fit.useful_novelty_required"],
                True,
            ),
            _boolean_check(
                document,
                "user_fit.first_miss_full_reoutput",
                ["user_fit.first_miss_full_reoutput"],
                True,
            ),
            _boolean_check(
                document,
                "user_fit.third_output_root_cause_trigger",
                ["user_fit.third_output_is_root_cause_trigger"],
                True,
            ),
            _boolean_check(
                document,
                "user_fit.no_visible_internal_field_dump",
                ["user_fit.visible_internal_field_dump_required"],
                False,
            ),
            _boolean_check(
                document,
                "user_fit.novelty_after_classic_pass",
                ["user_fit.novelty_after_classic_pass"],
                True,
            ),
            _boolean_check(
                document,
                "user_fit.no_unverified_high_impact_novelty",
                ["user_fit.unverified_high_impact_novelty"],
                False,
            ),
        ]
    )
    target_output_number, output_number_key = _lookup(
        document, ["user_fit.ok_target_output_number"]
    )
    checks.append(
        Check(
            "user_fit.ok_target_output_number_2",
            type(target_output_number) is int and target_output_number == 2,
            f"{output_number_key}={target_output_number!r}; expected=2",
        )
    )
    benchmark_names, benchmark_names_key = _lookup(
        document, ["capability_benchmarks.user_direct"]
    )
    checks.append(
        Check(
            "capability_benchmarks.user_direct_exact",
            benchmark_names == EXPECTED_CAPABILITY_BENCHMARKS,
            f"{benchmark_names_key}={benchmark_names!r}; expected={EXPECTED_CAPABILITY_BENCHMARKS!r}",
        )
    )
    checks.extend(
        [
            _token_check(
                document,
                "capability_benchmarks.output_earned_not_affection",
                ["capability_benchmarks.meaning"],
                "PROJECT_PEAKS_EARNED_BY_OUTPUT_NOT_AFFECTION",
            ),
            _boolean_check(
                document,
                "capability_benchmarks.no_automatic_quality_credit",
                ["capability_benchmarks.automatic_quality_credit_by_name"],
                False,
            ),
            _token_check(
                document,
                "capability_benchmarks.evidence_only_role_attribution",
                ["capability_benchmarks.role_attribution"],
                "EVIDENCE_VERIFIED_ONLY_OTHERWISE_HOLD",
            ),
            _boolean_check(
                document,
                "capability_benchmarks.new_worker_can_qualify",
                ["capability_benchmarks.new_worker_can_become_benchmark"],
                True,
            ),
            _token_check(
                document,
                "capability_benchmarks.thingkbell_mapping_hold",
                ["capability_benchmarks.thingkbell_canonical_mapping"],
                "HOLD",
            ),
        ]
    )
    return checks


def _completion_function_chain_checks(root: Path, document: Mapping[str, Any]) -> list[Check]:
    checks: list[Check] = []
    source_record, source_key = _lookup(document, ["bottleneck_execution.source_record"])
    if not isinstance(source_record, str):
        return [Check("bottleneck.source_function_chain", False, f"{source_key} is missing")]
    source_path = root / source_record
    try:
        lines = source_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        return [Check("bottleneck.source_function_chain", False, f"cannot read source: {exc}")]
    chain_line = next((line for line in lines if line.startswith("FUNCTION_CHAIN=")), None)
    if chain_line is None:
        return [Check("bottleneck.source_function_chain", False, "FUNCTION_CHAIN field missing")]
    segments = [segment.strip() for segment in chain_line.split("=", 1)[1].split("→")]
    checks.append(
        Check(
            "bottleneck.source_function_chain",
            segments[:10] == EXPECTED_BOTTLENECK_ORDER,
            f"source_first_10={segments[:10]!r}; expected={EXPECTED_BOTTLENECK_ORDER!r}",
        )
    )
    checks.append(
        Check(
            "bottleneck.source_before_after_closure",
            len(segments) == 11 and segments[10] == "BEFORE/AFTER 회수증가 증명",
            f"source_segments={segments!r}; expected conditional closure at joint 11",
        )
    )
    return checks


def validate_root(root: Path, runtime: Path | None = None) -> dict[str, Any]:
    root = root.expanduser().resolve()
    runtime_path = (runtime or (root / RUNTIME_RELATIVE_PATH)).expanduser().resolve()
    immutable_paths = [root / relative for relative, _ in IMMUTABLE_RECORDS.values()]
    input_paths = [*immutable_paths, runtime_path]
    before = _snapshot(input_paths)
    checks: list[Check] = []

    for label, (relative, expected) in IMMUTABLE_RECORDS.items():
        path = root / relative
        if not path.is_file():
            checks.append(Check(f"immutable.{label}", False, f"missing: {relative.as_posix()}"))
            continue
        actual = file_sha256(path)
        checks.append(
            Check(
                f"immutable.{label}",
                actual == expected,
                f"sha256={actual}; expected={expected}; path={relative.as_posix()}",
            )
        )

    archive = root / IMMUTABLE_RECORDS["rq-templ"][0]
    if archive.is_file():
        try:
            count, tree_hash, unsafe = _zip_tree_sha256(archive)
            checks.append(
                Check(
                    "rq_templ.safe_archive",
                    not unsafe,
                    f"unsafe_members={unsafe!r}",
                )
            )
            checks.append(
                Check(
                    "rq_templ.inner_tree",
                    count == RQ_TEMPL_FILE_COUNT and tree_hash == RQ_TEMPL_TREE_SHA256,
                    f"file_count={count}; tree_sha256={tree_hash}",
                )
            )
        except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
            checks.append(Check("rq_templ.inner_tree", False, f"archive read failed: {exc}"))

    document: Mapping[str, Any] | None = None
    if not runtime_path.is_file():
        checks.append(Check("runtime.toml", False, f"missing: {runtime_path}"))
    else:
        try:
            with runtime_path.open("rb") as stream:
                parsed = tomllib.load(stream)
            if not isinstance(parsed, Mapping):
                raise tomllib.TOMLDecodeError("root is not a table", "", 0)
            document = parsed
            checks.append(Check("runtime.toml", True, f"parsed: {runtime_path}"))
        except (OSError, tomllib.TOMLDecodeError) as exc:
            checks.append(Check("runtime.toml", False, f"parse failed: {exc}"))
    certification: str | None = None
    if document is not None:
        checks.extend(_runtime_checks(document))
        checks.extend(_completion_function_chain_checks(root, document))
        value, _ = _lookup(document, ["certification.mode"])
        certification = value if isinstance(value, str) else None

    after = _snapshot(input_paths)
    checks.append(
        Check(
            "validator.read_only_inputs_unchanged",
            before == after,
            f"before_entries={len(before)}; after_entries={len(after)}",
        )
    )

    failed = [check for check in checks if not check.passed]
    return {
        "status": "PASS" if not failed else "FAIL",
        "root": str(root),
        "runtime": str(runtime_path),
        "certification": certification,
        "summary": {"passed": len(checks) - len(failed), "failed": len(failed)},
        "checks": [check.as_json() for check in checks],
        "errors": [check.name for check in failed],
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="clone-kk2 skill root (default: script parent)",
    )
    parser.add_argument(
        "--runtime",
        type=Path,
        help="runtime TOML path (default: ROOT/references/KK2_JUNE04_MATURE_TAB_RUNTIME.toml)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = validate_root(args.root, args.runtime)
    except Exception as exc:  # Keep the command's output machine-readable even on unexpected faults.
        result = {
            "status": "FAIL",
            "root": str(args.root),
            "runtime": str(args.runtime) if args.runtime else None,
            "summary": {"passed": 0, "failed": 1},
            "checks": [],
            "errors": [f"validator_internal_error:{type(exc).__name__}:{exc}"],
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

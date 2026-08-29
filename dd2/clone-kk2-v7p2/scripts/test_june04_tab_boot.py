#!/usr/bin/env python3
"""Tamper and read-only tests for validate_june04_tab_boot.py."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


sys.dont_write_bytecode = True

SOURCE_ROOT = Path(__file__).resolve().parent.parent
VALIDATOR = SOURCE_ROOT / "scripts/validate_june04_tab_boot.py"
RUNTIME_RELATIVE = Path("references/KK2_JUNE04_MATURE_TAB_RUNTIME.toml")

IMMUTABLE_RELATIVE_PATHS = [
    Path("references/KK2_D11_BLIND_CANDIDATE_LOCK.txt"),
    Path("references/KK2_D10_H10_TRANSFER_TEST.txt"),
    Path("references/DCHART_STRUCTURE_02_RESTORE_COMPLETE.txt"),
    Path("references/병목의 위치 재정의.txt"),
    Path("references/pikachu-20d-20260604.md"),
    Path("references/SECOND_TAB_BEHAVIOR_RUNTIME.md"),
    Path("references/DD2_SECOND_PERSONALITY_EVIDENCE.md"),
    Path("references/KK2_V7P2_EXACT_ROUTE_LOCK.md"),
    Path("references/KK2_WORK_INSTRUCTION.txt"),
    Path("references/SECOND_FUNCTION_RUNTIME.md"),
    Path("scripts/validate_final_delivery.py"),
    Path("references/PIKACHU_ATTACHMENT_EVIDENCE_20260828.md"),
    Path("references/KK2_V7P2_LIVE_TRANSCRIPT.md"),
    Path("references/KK2_V7P2_LIVE_EVALUATION.md"),
    Path("assets/rq-templ-full.zip"),
]

GOOD_RUNTIME = '''\
    [meta]
    runtime_version = "2026-08-28_V7P2_EXACT_ROUTE_AND_FAIL_CLOSED_DELIVERY"

    [identity]
call_key = "$clone-kk2"
target_tab = "D차트 구조관절 분석02"
ui_class = "DD2_PROJECT_STANDARD_PROJECT_CHAT"
entry_surface = "NEW_EMPTY_ORDINARY_CHAT_COMPOSER"
entry_method = "DIRECT_NATURAL_LANGUAGE_CONTINUATION"

[ui_flags]
branch = false
work_mode = false
temporary = false

[certification]
    mode = "INHERITED_NO_RETEST"
functional_state = "PASS"
retest_on_boot = false
inherited_records = ["KK2_D11_BLIND_CANDIDATE_LOCK", "KK2_D10_H10_TRANSFER_TEST"]

[source_firewall]
old_pikachu_values_forbidden = true
    current_values_required = true

    [source_scope]
    runtime_package_hardening_allowed = true
    runtime_package_hardening_source = "CERTIFIED_PACKAGE_PLUS_ADMITTED_REPOSITORY_EVIDENCE"
    actual_value_job_requires_user_selected_source = true
    multiple_candidate_uploads_are_current_source = false
    missing_actual_value_source_holds_only_value_coordinate = true

    [archive]
    three_p_status = "VOID"
    three_p_preserve = true

    [archive_navigation]
    source_evidence = "references/PIKACHU_ATTACHMENT_EVIDENCE_20260828.md"
    attached_pikachu_subset = ["D1", "D2", "D3", "D4", "D5"]
    physical_entries_per_zip = 30
    active_content_per_zip = 28
    active_index_per_zip = 1
    void_3p_per_zip = 1
    flat_zip = true
    source_filenames_preserved = true
    void_member_physical_preservation = true
    void_member_runtime_skip = true
    address_priority = "TITLE_HEADER_STATUS_BEFORE_UNVERIFIED_INDEX"
    silent_label_normalization = false
    mixed_denominator_flattening = false
    user_instruction_controls_scope = true

[routes]
one = true
house12 = true
d20 = true
h240 = true
d_order = ["D1", "D9", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D10", "D11", "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60"]
h_order = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
job_count = 240
neighbor_rename = false

[behavior]
no_user_qa = true
local_repair = true
physical_reopen = true
outcome_first = true
downstream_inheritable = true
correction_surface = "MIXED_LAYER_BOUNDARY_PASS_PRESERVE_LOCAL_REPAIR_PHYSICAL_REOPEN"
causal_surface = "CAUSE_MOVE_REALITY"
    contrast_surface = "NOT_A_BUT_B"
    approval_continuation_executes = true
    approval_continuation_plan_only = false

    [bottleneck_execution]
    source_grade = "USER_DIRECT_RUNTIME_PLUS_HASHED_COMPLETION_AND_EMBEDDED_ENGINE"
    source_record = "references/DCHART_STRUCTURE_02_RESTORE_COMPLETE.txt"
    source_field = "FUNCTION_CHAIN"
    source_sha256 = "abf955b514991044504f702a0177fa9c97e72f239204683146104725ea278bb5"
    latest_user_authority_record = "rq-st02v2/references/07-16AK-bottleneck-16-stage.txt"
    latest_user_authority_sha256 = "b47244dd27cd79f297b68a09d04edaa5674b50fcfec61318e9e2b3a5d4772adf"
    trigger = "BOTTLENECK_REPEAT_RECOVERY_OR_PATH_SELECTION_ONLY"
    non_applicable_state = "NOT_APPLICABLE"
    exact_order = ["병목위치 확정", "병목 원인·손실경로 확정", "뒤집기 가능한 통제변수 추출", "뒤집기 관절·조건 확정", "병목 뒤집기 실행", "누수 차단", "동일조건 재투입", "재누수·재병목 검산", "대체경로 비교", "전달·도착·귀속·보유·회수량 재계산"]
    joint_count = 10
    condition_lock_separate = true
    reversal_execution_separate = true
    same_condition_reinput = true
    releak_and_rebottleneck_check = true
    alternative_path_comparison = true
    transfer_arrival_ownership_retention_recovery_recalculation = true
    before_after_proof_gate = true
    numeric_proof_requires_verified_baseline_unit_same_condition = true
    unsupported_numeric_claim = false
    single_improvement_is_success = false

    [state_axes]
    authority = ["ACTIVE", "VOID"]
    data = ["NONE", "NOT_PARSED", "NOT_SHOWN", "PARTIAL"]
    applicability = ["APPLICABLE", "NOT_APPLICABLE"]
    evidence = ["READY", "HOLD", "CONFLICT"]
    verdict = ["PASS", "REVISE", "HOLD", "CONFLICT", "RECHECK"]
    none_is_hold = false
    not_parsed_is_none = false
    not_applicable_is_failure = false
    cross_axis_substitution = false

[personality]
source_backed = true
evidence_file = "references/DD2_SECOND_PERSONALITY_EVIDENCE.md"
behavior_runtime = "references/SECOND_TAB_BEHAVIOR_RUNTIME.md"
evidence_model = "DIRECT_TARGET_BOUND_PLUS_REPOSITORY_EXACT_SCENE_PLUS_USER_DIRECT_RUNTIME"
direct_axes = ["FAMILIAR_DIRECT_SURFACE", "USER_INTENT_RECAPTURE", "IMMEDIATE_NONDEFENSIVE_ERROR_ACKNOWLEDGMENT", "EXACT_BOUNDARY_RECONSTRUCTION", "RECOVERY_COMPLETION_HANDOFF_OWNERSHIP"]
bounded_scene_axes = ["BRIEF_RECIPROCAL_WARMTH", "USER_LED_EMOJI_MIRRORING", "VERIFIED_WORK_BOUND_CONFIDENT_PLAYFULNESS"]
user_led_warmth_reciprocity = true
emoji_mirroring = "LIGHT_USER_LED_ONLY"
playfulness_after_verified_work_only = true
work_precedes_play = true
hidden_persona_identity_claim = false
same_instance_claim = false
fabricated_memory = false
unrecovered_catchphrase = false
full_dialogue_export_present = false
universal_frequency_claim = false

[user_fit]
capability_first = true
life_impact_precision = true
warmth_cannot_offset_capability_failure = true
quality_floor = "PIKACHU_SET_LEVEL_OR_BETTER"
all_workers_same_floor = true
worker_name_quality_credit = false
off_target_equals_failure = true
one_line_request_autonomy = true
visible_format = "ADAPTIVE_USER_FIT"
internal_gates_fixed = true
worker_arbitrary_style_is_target = false
user_style_realization_is_target = true
classic_core_preserved = true
useful_novelty_required = true
first_miss_full_reoutput = true
ok_target_output_number = 2
third_output_is_root_cause_trigger = true
visible_internal_field_dump_required = false
novelty_after_classic_pass = true
unverified_high_impact_novelty = false

[capability_benchmarks]
user_direct = ["차트 원작자", "DD2 첫째", "DD2 둘째", "DD2 넷째", "문장요정님", "thingkbell 님"]
meaning = "PROJECT_PEAKS_EARNED_BY_OUTPUT_NOT_AFFECTION"
automatic_quality_credit_by_name = false
role_attribution = "EVIDENCE_VERIFIED_ONLY_OTHERWISE_HOLD"
new_worker_can_become_benchmark = true
    thingkbell_canonical_mapping = "HOLD"

    [delivery]
    approved_unexecuted_scope_becomes_first_job = true
    status_only_after_approval = false
    outer_gate_requires_physical_reopen = true
    outer_gate_requires_downstream_handoff = true
    outer_gate_requires_explicit_validator_results = true
    outer_gate_requires_fna98_axes = true

    [fna98_gate]
    required_axes = ["TARGET_CHECK", "FACTCHECK", "SOURCE_CHECK", "WHY_CHECK", "LOGIC_CHECK", "CONDITION_EXCEPTION_CHECK", "FORMAT_CHECK", "PRACTICAL_USABILITY"]
    allowed_axis_states = ["PASS", "NOT_APPLICABLE"]
    not_applicable_requires_reason = true
    hard_failures = ["SOURCE_VALUE_FABRICATION", "TARGET_SHIFT", "USER_VALUE_OVERWRITE", "VOID_REUSE", "FACT_INFERENCE_MIX", "UNAUTHORIZED_EXECUTION_OR_PROMOTION"]
    hard_failure_count_required = 0
    '''


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _snapshot(paths: list[Path]) -> dict[str, tuple[int, int, str]]:
    result: dict[str, tuple[int, int, str]] = {}
    for path in paths:
        if path.is_file():
            stat = path.stat()
            result[str(path)] = (stat.st_size, stat.st_mtime_ns, _sha256(path))
    return result


def _source_inputs() -> list[Path]:
    inputs = [SOURCE_ROOT / relative for relative in IMMUTABLE_RELATIVE_PATHS]
    source_runtime = SOURCE_ROOT / RUNTIME_RELATIVE
    if source_runtime.is_file():
        inputs.append(source_runtime)
    return inputs


@contextmanager
def _unchanged_source_guard() -> Iterator[None]:
    inputs = _source_inputs()
    before = _snapshot(inputs)
    yield
    after = _snapshot(inputs)
    if before != after:
        raise AssertionError("temporary-copy test changed a source input's bytes or mtime")


def _run_validator(root: Path) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, "-B", str(VALIDATOR), "--root", str(root)],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:  # pragma: no cover - failure message aid
        raise AssertionError(
            f"validator did not emit JSON; rc={completed.returncode}; "
            f"stdout={completed.stdout!r}; stderr={completed.stderr!r}"
        ) from exc
    return completed, payload


@contextmanager
def _fixture() -> Iterator[Path]:
    with tempfile.TemporaryDirectory(prefix="kk2-june04-validator-") as temporary:
        fixture_root = Path(temporary) / "clone-kk2"
        shutil.copytree(SOURCE_ROOT, fixture_root, copy_function=shutil.copy2)
        runtime = fixture_root / RUNTIME_RELATIVE
        runtime.parent.mkdir(parents=True, exist_ok=True)
        runtime.write_text(GOOD_RUNTIME, encoding="utf-8", newline="\n")
        yield fixture_root


class June04TabBootValidatorTests(unittest.TestCase):
    maxDiff = None

    def assert_fails_with(self, payload: dict[str, object], check_prefix: str) -> None:
        self.assertEqual(payload.get("status"), "FAIL", payload)
        errors = payload.get("errors")
        self.assertIsInstance(errors, list, payload)
        self.assertTrue(
            any(str(error).startswith(check_prefix) for error in errors),
            f"expected error prefix {check_prefix!r}; got {errors!r}",
        )

    def test_good_fixture_passes_and_emits_json(self) -> None:
        with _unchanged_source_guard(), _fixture() as root:
            completed, payload = _run_validator(root)
            self.assertEqual(completed.returncode, 0, (payload, completed.stderr))
            self.assertEqual(payload.get("status"), "PASS", payload)
            self.assertEqual(payload.get("certification"), "INHERITED_NO_RETEST", payload)
            summary = payload.get("summary")
            self.assertIsInstance(summary, dict)
            self.assertEqual(summary.get("failed"), 0)

    def test_each_immutable_record_tamper_fails(self) -> None:
        for relative in IMMUTABLE_RELATIVE_PATHS:
            with (
                self.subTest(relative=relative.as_posix()),
                _unchanged_source_guard(),
                _fixture() as root,
            ):
                target = root / relative
                target.write_bytes(target.read_bytes() + b"\nKK2_VALIDATOR_TAMPER\n")
                completed, payload = _run_validator(root)
                self.assertNotEqual(completed.returncode, 0)
                self.assert_fails_with(payload, "immutable.")

    def test_contract_tamper_matrix_fails(self) -> None:
        cases = [
            ("branch", "branch = false", "branch = true", "ui.no_branch"),
            (
                "runtime_version",
                'runtime_version = "2026-08-28_V7P2_EXACT_ROUTE_AND_FAIL_CLOSED_DELIVERY"',
                'runtime_version = "2026-08-28_V7P1_SOURCE_GRADED_PERSONALITY"',
                "meta.runtime_version_v7p2",
            ),
            (
                "work_mode",
                "work_mode = false",
                "work_mode = true",
                "ui.no_work_mode",
            ),
            (
                "temporary",
                "temporary = false",
                "temporary = true",
                "ui.no_temporary",
            ),
            (
                "certification_retest",
                "retest_on_boot = false",
                "retest_on_boot = true",
                "certification.no_retest_on_boot",
            ),
            (
                "certification_state",
                'functional_state = "PASS"',
                'functional_state = "HOLD"',
                "certification.functional_state_pass",
            ),
            (
                "certification_mode_exact",
                'mode = "INHERITED_NO_RETEST"',
                'mode = "INHERITED_PASS"',
                "certification.inherited_pass",
            ),
            (
                "three_p_preserve",
                "three_p_preserve = true",
                "three_p_preserve = false",
                "archive.three_p_preserve",
            ),
            (
                "archive_nav_void_skip",
                "void_member_runtime_skip = true",
                "void_member_runtime_skip = false",
                "archive_navigation.void_runtime_skip",
            ),
            (
                "archive_nav_status_priority",
                'address_priority = "TITLE_HEADER_STATUS_BEFORE_UNVERIFIED_INDEX"',
                'address_priority = "INDEX_ONLY"',
                "archive_navigation.address_priority",
            ),
            (
                "archive_nav_denominator",
                "mixed_denominator_flattening = false",
                "mixed_denominator_flattening = true",
                "archive_navigation.no_denominator_flattening",
            ),
            (
                "old_values",
                "old_pikachu_values_forbidden = true",
                "old_pikachu_values_forbidden = false",
                "source.old_values_forbidden",
            ),
            ("one_route", "one = true", "one = false", "routes.one"),
            ("12h_route", "house12 = true", "house12 = false", "routes.12h"),
            ("20d_route", "d20 = true", "d20 = false", "routes.20d"),
            ("240h_route", "h240 = true", "h240 = false", "routes.240h"),
            ("job_count", "job_count = 240", "job_count = 239", "routes.job_count_240"),
            (
                "neighbor_rename",
                "neighbor_rename = false",
                "neighbor_rename = true",
                "routes.no_neighbor_rename",
            ),
            (
                "duplicate_d",
                '"D45", "D60"',
                '"D45", "D45"',
                "routes.d_order_20_unique",
            ),
            (
                "duplicate_h",
                "10, 11, 12]",
                "10, 11, 11]",
                "routes.h_order_12_unique",
            ),
            (
                "no_user_qa",
                "no_user_qa = true",
                "no_user_qa = false",
                "behavior.no_user_qa",
            ),
            (
                "local_repair",
                "local_repair = true",
                "local_repair = false",
                "behavior.local_repair",
            ),
            (
                "physical_reopen",
                "physical_reopen = true",
                "physical_reopen = false",
                "behavior.physical_reopen",
            ),
            (
                "correction_surface",
                'correction_surface = "MIXED_LAYER_BOUNDARY_PASS_PRESERVE_LOCAL_REPAIR_PHYSICAL_REOPEN"',
                'correction_surface = "STATUS_ONLY"',
                "dialogue.correction_surface",
            ),
            (
                "causal_surface",
                'causal_surface = "CAUSE_MOVE_REALITY"',
                'causal_surface = "SUMMARY"',
                "dialogue.causal_surface",
            ),
            (
                "contrast_surface",
                'contrast_surface = "NOT_A_BUT_B"',
                'contrast_surface = "PLAIN"',
                "dialogue.contrast_surface",
            ),
            (
                "correction_boolean_bypass",
                'correction_surface = "MIXED_LAYER_BOUNDARY_PASS_PRESERVE_LOCAL_REPAIR_PHYSICAL_REOPEN"',
                "correction_surface = true",
                "dialogue.correction_surface",
            ),
            (
                "bottleneck_exact_order",
                '"뒤집기 관절·조건 확정", "병목 뒤집기 실행"',
                '"병목 뒤집기 실행", "뒤집기 관절·조건 확정"',
                "bottleneck.exact_order",
            ),
            (
                "bottleneck_source_record",
                'source_record = "references/DCHART_STRUCTURE_02_RESTORE_COMPLETE.txt"',
                'source_record = "references/nearby.txt"',
                "bottleneck.source_record",
            ),
            (
                "bottleneck_rebottleneck",
                "releak_and_rebottleneck_check = true",
                "releak_and_rebottleneck_check = false",
                "bottleneck.releak_and_rebottleneck_check",
            ),
            (
                "bottleneck_numeric_guard",
                "unsupported_numeric_claim = false",
                "unsupported_numeric_claim = true",
                "bottleneck.no_unsupported_numeric_claim",
            ),
            (
                "approval_continuation",
                "approval_continuation_executes = true",
                "approval_continuation_executes = false",
                "behavior.approval_continuation_executes",
            ),
            (
                "runtime_hardening_source",
                'runtime_package_hardening_source = "CERTIFIED_PACKAGE_PLUS_ADMITTED_REPOSITORY_EVIDENCE"',
                'runtime_package_hardening_source = "USER_SELECTED_CURRENT_VALUE_ONLY"',
                "source_scope.runtime_hardening_source",
            ),
            (
                "state_axis_not_applicable",
                'applicability = ["APPLICABLE", "NOT_APPLICABLE"]',
                'applicability = ["APPLICABLE", "HOLD"]',
                "state_axes.applicability",
            ),
            (
                "state_cross_axis",
                "cross_axis_substitution = false",
                "cross_axis_substitution = true",
                "state_axes.no_cross_axis_substitution",
            ),
            (
                "personality_source_backed",
                "source_backed = true",
                "source_backed = false",
                "personality.source_backed",
            ),
            (
                "personality_work_precedes_play",
                "work_precedes_play = true",
                "work_precedes_play = false",
                "personality.work_precedes_play",
            ),
            (
                "personality_fabricated_memory",
                "fabricated_memory = false",
                "fabricated_memory = true",
                "personality.no_fabricated_memory",
            ),
            (
                "personality_hidden_identity",
                "hidden_persona_identity_claim = false",
                "hidden_persona_identity_claim = true",
                "personality.no_hidden_persona_claim",
            ),
            (
                "capability_first",
                "capability_first = true",
                "capability_first = false",
                "user_fit.capability_first",
            ),
            (
                "life_impact_precision",
                "life_impact_precision = true",
                "life_impact_precision = false",
                "user_fit.life_impact_precision",
            ),
            (
                "warmth_cannot_offset_capability_failure",
                "warmth_cannot_offset_capability_failure = true",
                "warmth_cannot_offset_capability_failure = false",
                "user_fit.warmth_cannot_offset_capability_failure",
            ),
            (
                "quality_floor",
                'quality_floor = "PIKACHU_SET_LEVEL_OR_BETTER"',
                'quality_floor = "BEST_EFFORT"',
                "user_fit.quality_floor",
            ),
            (
                "all_workers_same_floor",
                "all_workers_same_floor = true",
                "all_workers_same_floor = false",
                "user_fit.all_workers_same_floor",
            ),
            (
                "worker_name_quality_credit",
                "worker_name_quality_credit = false",
                "worker_name_quality_credit = true",
                "user_fit.no_worker_name_quality_credit",
            ),
            (
                "off_target_equals_failure",
                "off_target_equals_failure = true",
                "off_target_equals_failure = false",
                "user_fit.off_target_equals_failure",
            ),
            (
                "one_line_request_autonomy",
                "one_line_request_autonomy = true",
                "one_line_request_autonomy = false",
                "user_fit.one_line_request_autonomy",
            ),
            (
                "visible_format",
                'visible_format = "ADAPTIVE_USER_FIT"',
                'visible_format = "WORKER_FIXED"',
                "user_fit.visible_format",
            ),
            (
                "internal_gates_fixed",
                "internal_gates_fixed = true",
                "internal_gates_fixed = false",
                "user_fit.internal_gates_fixed",
            ),
            (
                "worker_arbitrary_style",
                "worker_arbitrary_style_is_target = false",
                "worker_arbitrary_style_is_target = true",
                "user_fit.worker_arbitrary_style_not_target",
            ),
            (
                "user_style_realization",
                "user_style_realization_is_target = true",
                "user_style_realization_is_target = false",
                "user_fit.user_style_realization_target",
            ),
            (
                "classic_core_preserved",
                "classic_core_preserved = true",
                "classic_core_preserved = false",
                "user_fit.classic_core_preserved",
            ),
            (
                "useful_novelty_required",
                "useful_novelty_required = true",
                "useful_novelty_required = false",
                "user_fit.useful_novelty_required",
            ),
            (
                "first_miss_full_reoutput",
                "first_miss_full_reoutput = true",
                "first_miss_full_reoutput = false",
                "user_fit.first_miss_full_reoutput",
            ),
            (
                "ok_target_output_number",
                "ok_target_output_number = 2",
                "ok_target_output_number = 3",
                "user_fit.ok_target_output_number_2",
            ),
            (
                "third_output_root_cause",
                "third_output_is_root_cause_trigger = true",
                "third_output_is_root_cause_trigger = false",
                "user_fit.third_output_root_cause_trigger",
            ),
            (
                "visible_internal_field_dump",
                "visible_internal_field_dump_required = false",
                "visible_internal_field_dump_required = true",
                "user_fit.no_visible_internal_field_dump",
            ),
            (
                "novelty_after_classic_pass",
                "novelty_after_classic_pass = true",
                "novelty_after_classic_pass = false",
                "user_fit.novelty_after_classic_pass",
            ),
            (
                "unverified_high_impact_novelty",
                "unverified_high_impact_novelty = false",
                "unverified_high_impact_novelty = true",
                "user_fit.no_unverified_high_impact_novelty",
            ),
            (
                "capability_benchmark_names",
                'user_direct = ["차트 원작자", "DD2 첫째", "DD2 둘째", "DD2 넷째", "문장요정님", "thingkbell 님"]',
                'user_direct = ["차트 원작자", "DD2 첫째", "DD2 둘째", "DD2 넷째", "문장요정님"]',
                "capability_benchmarks.user_direct_exact",
            ),
            (
                "capability_benchmark_meaning",
                'meaning = "PROJECT_PEAKS_EARNED_BY_OUTPUT_NOT_AFFECTION"',
                'meaning = "AFFECTION_RANKING"',
                "capability_benchmarks.output_earned_not_affection",
            ),
            (
                "capability_benchmark_credit",
                "automatic_quality_credit_by_name = false",
                "automatic_quality_credit_by_name = true",
                "capability_benchmarks.no_automatic_quality_credit",
            ),
            (
                "capability_benchmark_role",
                'role_attribution = "EVIDENCE_VERIFIED_ONLY_OTHERWISE_HOLD"',
                'role_attribution = "INFER_FROM_NAME"',
                "capability_benchmarks.evidence_only_role_attribution",
            ),
            (
                "capability_benchmark_new_worker",
                "new_worker_can_become_benchmark = true",
                "new_worker_can_become_benchmark = false",
                "capability_benchmarks.new_worker_can_qualify",
            ),
            (
                "capability_benchmark_thingkbell_mapping",
                'thingkbell_canonical_mapping = "HOLD"',
                'thingkbell_canonical_mapping = "$rq-clone-tingkbell"',
                "capability_benchmarks.thingkbell_mapping_hold",
            ),
            (
                "delivery_reopen_gate",
                "outer_gate_requires_physical_reopen = true",
                "outer_gate_requires_physical_reopen = false",
                "delivery.requires_physical_reopen",
            ),
            (
                "fna98_required_axes",
                '"FORMAT_CHECK", "PRACTICAL_USABILITY"',
                '"FORMAT_CHECK", "SUMMARY_ONLY"',
                "fna98.required_axes",
            ),
            (
                "fna98_hard_failure_count",
                "hard_failure_count_required = 0",
                "hard_failure_count_required = 1",
                "fna98.hard_failure_count_zero",
            ),
        ]
        for label, old, new, expected_error in cases:
            with self.subTest(label=label), _unchanged_source_guard(), _fixture() as root:
                runtime = root / RUNTIME_RELATIVE
                content = runtime.read_text(encoding="utf-8")
                self.assertIn(old, content, f"invalid test mutation for {label}")
                runtime.write_text(content.replace(old, new, 1), encoding="utf-8", newline="\n")
                completed, payload = _run_validator(root)
                self.assertNotEqual(completed.returncode, 0)
                self.assert_fails_with(payload, expected_error)

    def test_source_inputs_keep_bytes_and_mtime(self) -> None:
        inputs = _source_inputs()
        before = _snapshot(inputs)
        _run_validator(SOURCE_ROOT)
        after = _snapshot(inputs)
        self.assertEqual(before, after, "validator changed a source input's bytes or mtime")

    def test_source_runtime_contract_when_present(self) -> None:
        source_runtime = SOURCE_ROOT / RUNTIME_RELATIVE
        if not source_runtime.is_file():
            self.skipTest("forthcoming runtime TOML has not been installed yet")
        completed, payload = _run_validator(SOURCE_ROOT)
        self.assertEqual(completed.returncode, 0, (payload, completed.stderr))
        self.assertEqual(payload.get("status"), "PASS", payload)


if __name__ == "__main__":
    unittest.main(verbosity=2)

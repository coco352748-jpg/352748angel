#!/usr/bin/env python3
"""Regression tests for TITI's V3 default lock calibration guard."""

from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import v3_default_lock_guard as guard


class V3DefaultLockGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = guard.load_manifest()

    def test_manifest_passes_all_gates(self) -> None:
        report = guard.audit_manifest(self.payload)
        self.assertEqual(report["status"], "PASS", report["failures"])
        self.assertTrue(all(report["gates"].values()))
        self.assertEqual(
            report["default_anchor_order"], ["D5-H08", "D4-H10", "D6-H05"]
        )

    def test_v3_six_joint_contract_is_unchanged(self) -> None:
        stage = self.payload["v3_stage"]
        self.assertEqual(stage["joint_count"], 6)
        self.assertEqual(stage["joint_uids"], list(guard.V3_JOINT_UIDS))
        self.assertEqual(stage["exact_output_state"], "NOT_EXECUTED")

    def test_all_calibration_and_archetype_values_are_void(self) -> None:
        self.assertEqual(
            self.payload["calibration"]["calibration_value_state"], "VOID"
        )
        for profile in self.payload["anchor_profiles"]:
            self.assertEqual(profile["calibration_value_state"], "VOID")
        d6 = self.payload["anchor_profiles"][2]
        self.assertEqual(d6["archetype_value_state"], "VOID")
        archetype = self.payload["archetype_profiles"][0]
        self.assertEqual(archetype["calibration_value_state"], "VOID")
        self.assertEqual(archetype["semantic_value_authority"], "NONE")

    def test_d6_uses_d5_h05_structure_but_current_d6_values(self) -> None:
        d6 = self.payload["anchor_profiles"][2]
        self.assertEqual(d6["target_id"], "D6-H05")
        self.assertEqual(d6["archetype_target_id"], "D5-H05")
        self.assertEqual(
            d6["archetype_scope"], ["SENTENCE_STRUCTURE", "MICRO_STRUCTURE"]
        )
        self.assertEqual(d6["archetype_value_inheritance"], "PROHIBITED")
        self.assertEqual(d6["value_source"], "CURRENT_D6_SOURCE_ONLY")

    def test_default_activation_and_user_override(self) -> None:
        omitted = guard.resolve_activation(self.payload, task_scope="LOCK_SENTENCE")
        explicit = guard.resolve_activation(
            self.payload, task_scope="LOCK_SENTENCE", requested_version="V3"
        )
        override = guard.resolve_activation(
            self.payload,
            task_scope="LOCK_SENTENCE",
            requested_version="V3",
            user_override=True,
        )
        self.assertEqual(omitted["state"], "APPLY_DEFAULT")
        self.assertEqual(omitted["selected_version"], "V3")
        self.assertEqual(explicit["state"], "APPLY_DEFAULT")
        self.assertEqual(override["state"], "USER_OVERRIDE")
        self.assertIsNone(override["profile_id"])
        for operation in (
            "REVERSE_DESIGN",
            "ROUNDTRIP_AUDIT",
            "FORWARD_RENDER",
            "EXACT_STAGE_REVERSE\u200b",
        ):
            with self.subTest(operation=operation):
                route = guard.resolve_activation(
                    self.payload,
                    task_scope="LOCK_SENTENCE",
                    requested_version="V3",
                    operation=operation,
                )
                self.assertEqual(route["state"], "NOT_APPLICABLE_OPERATION")

        forged = copy.deepcopy(self.payload)
        forged["v3_stage"]["exact_output_state"] = "PASS"
        route = guard.resolve_activation(
            forged, task_scope="LOCK_SENTENCE", requested_version="V3"
        )
        self.assertEqual(route["state"], "HOLD_INVALID_PROFILE")

    def test_exact_reverse_and_v4_to_v7_are_excluded(self) -> None:
        exact = guard.resolve_activation(
            self.payload,
            task_scope="LOCK_SENTENCE",
            requested_version="V3",
            operation="EXACT_STAGE_REVERSE",
        )
        self.assertEqual(exact["state"], "EXCLUDED_EXACT_REVERSE")
        for version in guard.EXCLUDED_VERSIONS:
            with self.subTest(version=version):
                route = guard.resolve_activation(
                    self.payload,
                    task_scope="LOCK_SENTENCE",
                    requested_version=version,
                )
                self.assertEqual(route["state"], "EXCLUDED_VERSION")

    def test_changed_target_order_is_rejected(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["calibration"]["default_anchor_order"].reverse()
        report = guard.audit_manifest(payload)
        self.assertFalse(report["gates"]["DEFAULT_ANCHOR_ORDER"])

    def test_stage_change_or_false_exact_state_is_rejected(self) -> None:
        changed = copy.deepcopy(self.payload)
        changed["v3_stage"]["joint_uids"].pop()
        report = guard.audit_manifest(changed)
        self.assertFalse(report["gates"]["V3_SIX_JOINTS"])

        false_exact = copy.deepcopy(self.payload)
        false_exact["v3_stage"]["exact_output_state"] = "PASS"
        report = guard.audit_manifest(false_exact)
        self.assertFalse(report["gates"]["EXACT_V3_NOT_EXECUTED"])

    def test_d6_archetype_value_leak_is_rejected(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["anchor_profiles"][2]["value_source"] = "D5-H05"
        payload["anchor_profiles"][2]["archetype_value_inheritance"] = "ALLOWED"
        report = guard.audit_manifest(payload)
        self.assertFalse(report["gates"]["D6_CURRENT_SOURCE_ONLY"])
        self.assertFalse(report["gates"]["D6_ARCHETYPE_BINDING"])

    def test_chart_specific_values_are_rejected(self) -> None:
        cases = (
            ("planet", "Mars"),
            ("sign", "Virgo"),
            ("value", "18°02"),
            ("value", "P3"),
        )
        for key, value in cases:
            with self.subTest(key=key, value=value):
                payload = copy.deepcopy(self.payload)
                payload["anchor_profiles"][0][key] = value
                report = guard.audit_manifest(payload)
                self.assertFalse(report["gates"]["NO_CHART_SPECIFIC_VALUES"])

    def test_self_test_detects_every_negative_case(self) -> None:
        report = guard.self_test()
        self.assertEqual(report["status"], "PASS", report["failures"])
        self.assertEqual(report["valid_manifest_status"], "PASS")
        self.assertTrue(
            all(item["detected"] for item in report["negative_cases"].values())
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

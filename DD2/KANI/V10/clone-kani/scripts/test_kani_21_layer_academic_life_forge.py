#!/usr/bin/env python3
"""Regression tests for the standalone KANI forge registration validator."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from typing import Any, Callable


SOURCE_ROOT = Path(__file__).resolve().parent.parent
VALIDATOR_RELATIVE = Path("scripts/validate_kani_21_layer_academic_life_forge.py")
REGISTRATION_RELATIVE = Path(
    "references/v10_runtime/kani_21_layer_academic_life_forge_registration.json"
)
REFERENCE_RELATIVE = Path("references/KANI_21_LAYER_VEDIC_ACADEMIC_LIFE_FORGE.md")
SKILL_RELATIVE = Path("SKILL.md")


class KaniAcademicLifeForgeRegistrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "clone-kani"
        for relative in (
            VALIDATOR_RELATIVE,
            REGISTRATION_RELATIVE,
            REFERENCE_RELATIVE,
            SKILL_RELATIVE,
        ):
            source = SOURCE_ROOT / relative
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        self.validator = self.root / VALIDATOR_RELATIVE

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def read_registration(self) -> dict[str, Any]:
        return json.loads(
            (self.root / REGISTRATION_RELATIVE).read_text(encoding="utf-8")
        )

    def write_registration(self, registration: dict[str, Any]) -> None:
        (self.root / REGISTRATION_RELATIVE).write_text(
            json.dumps(registration, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def run_validator(self) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        completed = subprocess.run(
            [sys.executable, str(self.validator), "--root", str(self.root)],
            cwd=self.root,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(completed.stderr, "", completed.stderr)
        output_lines = completed.stdout.splitlines()
        self.assertEqual(len(output_lines), 1, completed.stdout)
        report = json.loads(output_lines[0])
        self.assertIsInstance(report, dict)
        self.assertEqual(report["execution"], "NOT_EXECUTED")
        self.assertEqual(report["analysis_validation"], "NOT_RUN_NO_RUN_BUNDLE")
        self.assertEqual(report["academic_gate"], "HOLD_UNEXECUTED")
        self.assertEqual(report["life_congruence_gate"], "HOLD_UNEXECUTED")
        return completed, report

    def assert_registration_rejected(self) -> dict[str, Any]:
        completed, report = self.run_validator()
        self.assertEqual(completed.returncode, 1, report)
        self.assertEqual(report["status"], "REVISE")
        self.assertEqual(report["registration_validation"], "FAIL")
        self.assertNotEqual(
            report["academic_life_forge"], "ACTIVE_REGISTERED_HASH_LOCKED"
        )
        self.assertTrue(report["errors"], report)
        return report

    def test_registered_contract_passes_without_claiming_analysis(self) -> None:
        completed, report = self.run_validator()
        self.assertEqual(completed.returncode, 0, report)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["academic_life_forge"], "ACTIVE_REGISTERED_HASH_LOCKED")
        self.assertEqual(report["registration_validation"], "PASS")
        self.assertEqual(report["route_units"], "19/19")
        self.assertEqual(report["logical_roles"], "57/57")
        self.assertEqual(report["reference_binding"], "PRESENT_HASH_LOCKED")
        self.assertEqual(report["skill_route"], "PRESENT_CONFLICT_FREE")
        self.assertEqual(report["public_stage_sequence"], "V3_V4_V5")
        self.assertEqual(report["v3_depth"], "PIKACHU_FIRST_ANALYSIS_BASELINE")
        self.assertEqual(report["v4_depth"], "UNIVERSITY_THESIS_DEPTH")
        self.assertEqual(
            report["v4_benchmark"],
            "BHU_JYOTISH_DOMAIN_PLUS_OXFORD_BA_SANSKRIT_FHS_FIRST_CLASS_WRITING",
        )
        self.assertEqual(
            report["v5_depth"], "CONFERENCE_PRESENTATION_REVIEW_DEPTH"
        )
        self.assertEqual(report["institutional_endorsement"], "NOT_CLAIMED")
        self.assertEqual(report["errors"], [])

    def test_public_stage_or_internal_alias_tamper_fails(self) -> None:
        registration = self.read_registration()
        registration["stage_semantics"]["V4"]["user_visible_stage"] = "V5"
        registration["stage_semantics"]["V4"]["internal_engine_alias"] = "RQ_R5_V7"
        self.write_registration(registration)
        report = self.assert_registration_rejected()
        self.assertIn(
            "registration_public_v3_v4_v5_stage_semantics_exact",
            report["errors"],
        )

    def test_bhu_oxford_benchmark_or_endorsement_tamper_fails(self) -> None:
        registration = self.read_registration()
        registration["benchmark_contract"]["V4_DUAL_BENCHMARK"][
            "institutional_endorsement"
        ] = "CLAIMED"
        registration["benchmark_contract"]["V4_DUAL_BENCHMARK"][
            "domain_anchor"
        ]["id"] = "OXFORD_ASTROLOGY_DEPARTMENT"
        self.write_registration(registration)
        report = self.assert_registration_rejected()
        self.assertIn(
            "registration_bhu_oxford_benchmark_contract_exact",
            report["errors"],
        )

    def test_exact_authority_string_tamper_fails(self) -> None:
        registration = self.read_registration()
        registration["authority"]["exact_user_authority_strings"][0] = "FAKE"
        self.write_registration(registration)
        self.assert_registration_rejected()

    def test_noncanonical_route_or_role_fails_with_counts_preserved(self) -> None:
        original = self.read_registration()

        def tamper_unit(registration: dict[str, Any]) -> None:
            registration["route"]["units"][4] = "11"
            for packet in registration["route"]["role_packets"]:
                if packet["unit"] == "D-1":
                    packet["unit"] = "11"

        def tamper_role(registration: dict[str, Any]) -> None:
            registration["route"]["role_types"][2] = "DERIVED_CLAIM"
            for packet in registration["route"]["role_packets"]:
                if packet["role_type"] == "ELIPHD":
                    packet["role_type"] = "DERIVED_CLAIM"
                    packet["role_packet_id"] = packet["role_packet_id"].replace(
                        "ELIPHD", "DERIVED_CLAIM"
                    )

        mutations: tuple[tuple[str, Callable[[dict[str, Any]], None]], ...] = (
            ("unit", tamper_unit),
            ("role", tamper_role),
        )
        for name, mutate in mutations:
            with self.subTest(name=name):
                registration = json.loads(json.dumps(original, ensure_ascii=False))
                mutate(registration)
                self.write_registration(registration)
                self.assert_registration_rejected()

    def test_coordinated_reference_and_digest_tamper_fails(self) -> None:
        reference_path = self.root / REFERENCE_RELATIVE
        tampered = reference_path.read_bytes() + b"\nCOORDINATED_TAMPER=true\n"
        reference_path.write_bytes(tampered)
        registration = self.read_registration()
        registration["reference_binding"]["bytes"] = len(tampered)
        registration["reference_binding"]["sha256"] = hashlib.sha256(
            tampered
        ).hexdigest()
        self.write_registration(registration)
        self.assert_registration_rejected()

    def test_noncanonical_registration_schema_field_fails(self) -> None:
        registration = self.read_registration()
        registration["unregistered_override"] = "PASS"
        self.write_registration(registration)
        self.assert_registration_rejected()

    def test_missing_required_skill_route_token_fails(self) -> None:
        skill_path = self.root / SKILL_RELATIVE
        skill_text = skill_path.read_text(encoding="utf-8")
        required = "ANALYSIS_VALIDATION=NOT_RUN_NO_RUN_BUNDLE\n"
        self.assertIn(required, skill_text)
        skill_path.write_text(skill_text.replace(required, "", 1), encoding="utf-8")
        self.assert_registration_rejected()

    def test_contradictory_skill_autopass_token_fails(self) -> None:
        skill_path = self.root / SKILL_RELATIVE
        skill_text = skill_path.read_text(encoding="utf-8")
        skill_path.write_text(
            skill_text + "\nALL_ACADEMIC_AND_LIFE_GATES_AUTOPASS=true\n",
            encoding="utf-8",
        )
        self.assert_registration_rejected()


if __name__ == "__main__":
    unittest.main()

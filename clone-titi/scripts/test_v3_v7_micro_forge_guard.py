#!/usr/bin/env python3
"""Regression tests for the TITI V3-V7 micro forge guard."""

from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import v3_v7_micro_forge_guard as guard


class V3V7MicroForgeGuardTests(unittest.TestCase):
    def test_registry_counts_are_exact(self) -> None:
        self.assertEqual(
            guard.EXPECTED_COUNTS,
            {"V3": 6, "V4": 7, "V5": 7, "V6": 11, "V7": 8},
        )
        self.assertEqual(guard.EXPECTED_TOTAL, 39)
        registry = guard.resolve_registry()
        self.assertEqual(registry["status"], "PASS")

    def test_design_all_five_versions_is_ready_not_sentence_pass(self) -> None:
        report = guard.audit_forge_bundle(guard.sample_bundle("DESIGN_STAGE"))
        self.assertEqual(report["status"], "PASS", report["failures"])
        self.assertEqual([item["version"] for item in report["versions"]], list(guard.VERSION_ORDER))
        self.assertTrue(all(item["status"] == "PASS" for item in report["versions"]))
        self.assertEqual(
            report["fna98_quality"],
            {
                "density": "PASS",
                "resolution": "PASS",
                "completeness": "PASS",
                "verdict": "FNA98_DESIGN_READY",
            },
        )
        self.assertNotEqual(report["fna98_quality"]["verdict"], "FNA98_SENTENCE_PASS")

    def test_exact_all_five_versions_gets_sentence_pass(self) -> None:
        report = guard.audit_forge_bundle(guard.sample_bundle("EXACT_STAGE_REVERSE"))
        self.assertEqual(report["status"], "PASS", report["failures"])
        self.assertEqual(report["joint_count"], 39)
        self.assertEqual(report["fna98_quality"]["verdict"], "FNA98_SENTENCE_PASS")
        self.assertTrue(all(value == "PASS" for key, value in report["fna98_quality"].items() if key != "verdict"))

    def test_every_joint_has_19_cells_and_four_functions(self) -> None:
        bundle = guard.sample_bundle("DESIGN_STAGE")
        for stage in bundle["versions"]:
            for joint in stage["joints"]:
                self.assertEqual(list(joint["cells"]), list(guard.REQUIRED_CELL_FIELDS))
                self.assertEqual(len(joint["cells"]), 19)
                self.assertEqual(joint["paragraph_functions"], list(guard.PARAGRAPH_FUNCTIONS))
                child_roles = {
                    slot["semantic_role"] for slot in joint["child_bundle"]["slots"]
                }
                self.assertEqual(child_roles, set(guard.SEMANTIC_CELLS))
                self.assertNotIn("STATUS", child_roles)
                self.assertNotIn("SURFACE_SCAFFOLD", child_roles)
                self.assertEqual(joint["function_cell_map"], guard.FUNCTION_CELL_MAP)

    def test_joint_order_and_version_mixing_are_rejected(self) -> None:
        bundle = guard.sample_bundle("DESIGN_STAGE", ["V3"])
        bundle["versions"][0]["joints"][0], bundle["versions"][0]["joints"][1] = (
            bundle["versions"][0]["joints"][1],
            bundle["versions"][0]["joints"][0],
        )
        report = guard.audit_forge_bundle(bundle)
        self.assertFalse(report["gates"]["JOINT_ORDER"])
        self.assertFalse(report["gates"]["FNA98_RESOLUTION"])

        mixed = guard.sample_bundle("DESIGN_STAGE", ["V4"])
        mixed["versions"][0]["joints"][0]["uid"] = "V3.CENTER_OPERATION"
        report = guard.audit_forge_bundle(mixed)
        self.assertFalse(report["gates"]["VERSION_SEPARATION"])

    def test_missing_cell_fails_density(self) -> None:
        bundle = guard.sample_bundle("DESIGN_STAGE", ["V5"])
        bundle["versions"][0]["joints"][0]["cells"].pop("DIRECT_OBJECT")
        report = guard.audit_forge_bundle(bundle)
        self.assertFalse(report["gates"]["REQUIRED_CELL_SET"])
        self.assertEqual(report["fna98_quality"]["density"], "REVISE")
        self.assertFalse(report["gates"]["FNA98_DENSITY"])

    def test_handoff_value_chain_is_exact(self) -> None:
        bundle = guard.sample_bundle("EXACT_STAGE_REVERSE", ["V6"])
        bundle["versions"][0]["joints"][2]["cells"]["PREVIOUS_OUTPUT"]["value"] = "DISCONNECTED"
        report = guard.audit_forge_bundle(bundle)
        self.assertFalse(report["gates"]["HANDOFF_CHAIN"])
        self.assertFalse(report["gates"]["FNA98_COMPLETENESS"])
        self.assertNotEqual(report["fna98_quality"]["verdict"], "FNA98_SENTENCE_PASS")

    def test_design_cannot_bind_or_claim_exact(self) -> None:
        bundle = guard.sample_bundle("DESIGN_STAGE", ["V3"])
        bundle["versions"][0]["exact_roundtrip_state"] = "PASS"
        bundle["versions"][0]["joints"][0]["cells"]["PREDICATE"]["value"] = "invented"
        report = guard.audit_forge_bundle(bundle)
        self.assertFalse(report["gates"]["DESIGN_NO_FALSE_EXACT"])
        self.assertFalse(report["gates"]["NO_INVENTED_BINDINGS"])
        self.assertNotEqual(report["fna98_quality"]["verdict"], "FNA98_SENTENCE_PASS")

    def test_inferred_exact_source_is_rejected_even_if_child_matches(self) -> None:
        bundle = guard.sample_bundle("EXACT_STAGE_REVERSE", ["V3"])
        cell = bundle["versions"][0]["joints"][0]["cells"]["INPUT_REF"]
        child_slot = bundle["versions"][0]["joints"][0]["child_bundle"]["records"][0]["slots"][0]
        cell["source_ref"] = "MODEL_INFERRED:INPUT_REF"
        child_slot["source_ref"] = cell["source_ref"]
        report = guard.audit_forge_bundle(bundle)
        self.assertFalse(report["gates"]["NO_INVENTED_BINDINGS"])
        self.assertEqual(report["fna98_quality"]["completeness"], "REVISE")

    def test_native_exact_reverse_mutation_is_rejected(self) -> None:
        bundle = guard.sample_bundle("EXACT_STAGE_REVERSE", ["V4"])
        child_record = bundle["versions"][0]["joints"][0]["child_bundle"]["records"][0]
        child_record["sentence"] += "X"
        report = guard.audit_forge_bundle(bundle)
        self.assertFalse(report["gates"]["CHILD_NATIVE_AUDIT"])
        self.assertFalse(report["gates"]["EXACT_NATIVE_ROUNDTRIP"])
        self.assertNotEqual(report["fna98_quality"]["verdict"], "FNA98_SENTENCE_PASS")

    def test_v7_requires_two_independent_lower_structures(self) -> None:
        for operation in ("DESIGN_STAGE", "EXACT_STAGE_REVERSE"):
            with self.subTest(operation=operation):
                bundle = guard.sample_bundle(operation, ["V7"])
                bundle["versions"][0]["lower_structures"].pop()
                report = guard.audit_forge_bundle(bundle)
                self.assertFalse(report["gates"]["V7_TWO_LOWER_STRUCTURES"])
                self.assertFalse(report["gates"]["FNA98_RESOLUTION"])

    def test_visibility_is_required_for_sentence_pass(self) -> None:
        bundle = guard.sample_bundle("EXACT_STAGE_REVERSE", ["V3"])
        bundle["output_visibility"]["show_validation_table"] = True
        report = guard.audit_forge_bundle(bundle)
        self.assertFalse(report["gates"]["OUTPUT_VISIBILITY"])
        self.assertFalse(report["gates"]["FNA98_COMPLETENESS"])
        self.assertEqual(report["fna98_quality"]["verdict"], "FNA98_REVISE")

    def test_duplicate_claim_signature_fails_density(self) -> None:
        bundle = guard.sample_bundle("DESIGN_STAGE", ["V3"])
        source = bundle["versions"][0]["joints"][0]
        clone = bundle["versions"][0]["joints"][1]
        clone_slots = {
            slot["semantic_role"]: slot for slot in clone["child_bundle"]["slots"]
        }
        for field in guard.CLAIM_SIGNATURE_FIELDS:
            clone["cells"][field]["input_ref"] = source["cells"][field]["input_ref"]
            clone_slots[field]["input_ref"] = source["cells"][field]["input_ref"]
        report = guard.audit_forge_bundle(bundle)
        self.assertFalse(report["gates"]["NO_DUPLICATE_CLAIM_PADDING"])
        self.assertFalse(report["gates"]["FNA98_DENSITY"])

    def test_pre_and_post_state_must_be_directed(self) -> None:
        bundle = guard.sample_bundle("DESIGN_STAGE", ["V4"])
        joint = bundle["versions"][0]["joints"][0]
        joint["cells"]["POST_STATE"]["input_ref"] = joint["cells"]["PRE_STATE"]["input_ref"]
        slots = {slot["semantic_role"]: slot for slot in joint["child_bundle"]["slots"]}
        slots["POST_STATE"]["input_ref"] = joint["cells"]["PRE_STATE"]["input_ref"]
        report = guard.audit_forge_bundle(bundle)
        self.assertFalse(report["gates"]["DIRECTED_TRANSFORMATION"])
        self.assertFalse(report["gates"]["FNA98_RESOLUTION"])

    def test_handoff_test_token_is_not_occurrence_probe(self) -> None:
        bundle = guard.sample_bundle("DESIGN_STAGE", ["V3"])
        first = bundle["versions"][0]["joints"][0]
        first["cells"]["HANDOFF_VALUE"]["handoff_test_token"] = first["cells"][
            "HANDOFF_VALUE"
        ]["occurrence_probe"]
        report = guard.audit_forge_bundle(bundle)
        self.assertFalse(report["gates"]["HANDOFF_TEST_TOKEN"])

    def test_self_test_covers_all_versions_and_negative_cases(self) -> None:
        report = guard.self_test()
        self.assertEqual(report["status"], "PASS", report["failures"])
        self.assertEqual(len(report["all_stage_coverage"]), 10)
        self.assertTrue(all(value == "PASS" for value in report["all_stage_coverage"].values()))
        self.assertTrue(all(item["detected"] for item in report["negative_cases"].values()))


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
"""CLI regression tests for the clone-kk2 outer final-delivery gate."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


VALIDATOR = Path(__file__).with_name("validate_final_delivery.py")


class FinalDeliveryCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_packet(self, name: str, packet: Any) -> Path:
        path = self.root / name
        path.write_text(json.dumps(packet), encoding="utf-8")
        return path

    def run_gate(self, *paths: Path | str) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
        completed = subprocess.run(
            [sys.executable, str(VALIDATOR), *(str(path) for path in paths)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.stderr, "")
        return completed, json.loads(completed.stdout)

    def minimal_pass(self) -> dict[str, Any]:
        artifact = self.root / "reopened-artifact.bin"
        if not artifact.exists():
            artifact.write_bytes(b"clone-kk2-reopened-artifact\n")
        payload = artifact.read_bytes()
        return {
            "target": "D차트 구조관절 분석02",
            "final_status": "PASS",
            "holds": [],
            "conflicts": [],
            "required_validators": ["contract.py"],
            "validator_results": {"contract.py": "PASS"},
            "physical_reopen_status": "PASS",
            "physical_reopen_evidence": {
                "all_required_files_reopened": True,
                "package_manifest_rechecked": True,
                "source_inputs_modified": False,
                "artifacts": [
                    {
                        "path": artifact.name,
                        "size_bytes": len(payload),
                        "sha256": hashlib.sha256(payload).hexdigest(),
                    }
                ],
            },
            "handoff_status": "PASS",
            "downstream_handoff": {
                "first_unexecuted_job": "CURRENT_USER_REQUEST",
                "user_as_final_qa": False,
            },
            "fna98_gate": {
                "status": "PASS",
                "hard_failures": [],
                "axes": {
                    "target_check": "PASS",
                    "factcheck": "PASS",
                    "source_check": "PASS",
                    "why_check": "PASS",
                    "logic_check": "PASS",
                    "condition_exception_check": "PASS",
                    "format_check": "PASS",
                    "practical_usability": "PASS",
                },
            },
        }

    def test_complete_pass(self) -> None:
        path = self.write_packet("pass.json", self.minimal_pass())
        completed, output = self.run_gate(path)
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(output["status"], "PASS")
        self.assertEqual(output["packets"][0]["errors"], [])

    def test_declaration_only_packet_fails_closed(self) -> None:
        path = self.write_packet(
            "declaration-only.json",
            {"final_status": "PASS", "holds": [], "conflicts": []},
        )
        completed, output = self.run_gate(path)
        self.assertEqual(completed.returncode, 3)
        joined = "\n".join(output["packets"][0]["errors"])
        self.assertIn("required_validators", joined)
        self.assertIn("physical_reopen_status", joined)
        self.assertIn("handoff_status", joined)
        self.assertIn("fna98_gate", joined)

    def test_multiple_packets_and_supported_validator_contracts_pass(self) -> None:
        first = self.minimal_pass()
        first.update({
            "required_validators": ["route.py", "output.py"],
            "validator_results": {"route.py": "PASS", "output.py": {"status": "PASS"}},
            "application_route": {
                "route_validator": "route.py",
                "route_validation_status": "PASS",
            },
            "output": {"output_validation_status": "PASS"},
        })
        second = self.minimal_pass()
        second["required_validators"] = {"packet.py": "PASS"}
        first_path = self.write_packet("first.json", first)
        second_path = self.write_packet("second.json", second)
        completed, output = self.run_gate(first_path, second_path)
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(output["packet_count"], 2)
        self.assertTrue(all(item["status"] == "PASS" for item in output["packets"]))

    def test_every_nonpass_final_status_is_rejected(self) -> None:
        for index, status in enumerate(("PENDING", "HOLD", "REVISE", "CONFLICT", "UNKNOWN")):
            with self.subTest(status=status):
                packet = self.minimal_pass()
                packet["final_status"] = status
                path = self.write_packet(f"nonpass-{index}.json", packet)
                completed, output = self.run_gate(path)
                self.assertEqual(completed.returncode, 3)
                self.assertEqual(output["status"], "FAIL")
                self.assertIn("$.final_status must be exactly PASS", output["packets"][0]["errors"])

    def test_nonempty_or_malformed_hold_and_conflict_lists_fail_closed(self) -> None:
        cases = (
            ("holds", ["unresolved source"]),
            ("conflicts", ["authority collision"]),
            ("holds", "none"),
            ("conflicts", None),
        )
        for index, (field, value) in enumerate(cases):
            with self.subTest(field=field, value=value):
                packet = self.minimal_pass()
                packet[field] = value
                path = self.write_packet(f"list-{index}.json", packet)
                completed, output = self.run_gate(path)
                self.assertEqual(completed.returncode, 3)
                self.assertEqual(output["packets"][0]["status"], "FAIL")

    def test_missing_hold_or_conflict_list_fails_closed(self) -> None:
        for field in ("holds", "conflicts"):
            with self.subTest(field=field):
                packet = self.minimal_pass()
                del packet[field]
                path = self.write_packet(f"missing-{field}.json", packet)
                completed, output = self.run_gate(path)
                self.assertEqual(completed.returncode, 3)
                self.assertTrue(any(field in error for error in output["packets"][0]["errors"]))

    def test_required_validator_must_have_explicit_pass_result(self) -> None:
        for index, result in enumerate((None, "SCHEMA_PASS", "PENDING", "HOLD", "REVISE", "CONFLICT", "UNKNOWN")):
            with self.subTest(result=result):
                packet = self.minimal_pass()
                packet["required_validators"] = ["required.py"]
                if result is not None:
                    packet["validator_results"] = {"required.py": result}
                path = self.write_packet(f"validator-{index}.json", packet)
                completed, output = self.run_gate(path)
                self.assertEqual(completed.returncode, 3)
                self.assertEqual(output["packets"][0]["status"], "FAIL")

    def test_direct_and_route_validator_results_must_be_pass(self) -> None:
        packet = self.minimal_pass()
        packet.update({
            "application_route": {
                "route_validator": "route.py",
                "route_validation_status": "SCHEMA_PASS",
            },
            "human_output": {"output_validation_status": "NOT_APPLICABLE"},
        })
        path = self.write_packet("direct-validator.json", packet)
        completed, output = self.run_gate(path)
        self.assertEqual(completed.returncode, 3)
        joined = "\n".join(output["packets"][0]["errors"])
        self.assertIn("route_validation_status", joined)
        self.assertIn("output_validation_status", joined)

    def test_physical_reopen_artifact_is_verified_against_bytes(self) -> None:
        cases = ("missing", "size", "hash", "escape")
        for index, case in enumerate(cases):
            with self.subTest(case=case):
                packet = self.minimal_pass()
                artifact = packet["physical_reopen_evidence"]["artifacts"][0]
                if case == "missing":
                    artifact["path"] = "absent.bin"
                elif case == "size":
                    artifact["size_bytes"] += 1
                elif case == "hash":
                    artifact["sha256"] = "0" * 64
                else:
                    artifact["path"] = "../escape.bin"
                path = self.write_packet(f"reopen-{index}.json", packet)
                completed, output = self.run_gate(path)
                self.assertEqual(completed.returncode, 3)
                self.assertEqual(output["packets"][0]["status"], "FAIL")

    def test_handoff_and_fna98_axes_are_independent_required_gates(self) -> None:
        cases = (
            ("handoff_status", lambda p: p.__setitem__("handoff_status", "RECHECK")),
            (
                "user_as_final_qa",
                lambda p: p["downstream_handoff"].__setitem__("user_as_final_qa", True),
            ),
            ("fna_status", lambda p: p["fna98_gate"].__setitem__("status", "REVISE")),
            (
                "fna_axis",
                lambda p: p["fna98_gate"]["axes"].__setitem__("why_check", "HOLD"),
            ),
            (
                "hard_fail",
                lambda p: p["fna98_gate"].__setitem__("hard_failures", ["TARGET_SHIFT"]),
            ),
        )
        for index, (label, mutate) in enumerate(cases):
            with self.subTest(label=label):
                packet = self.minimal_pass()
                mutate(packet)
                path = self.write_packet(f"independent-{index}.json", packet)
                completed, output = self.run_gate(path)
                self.assertEqual(completed.returncode, 3)
                self.assertEqual(output["packets"][0]["status"], "FAIL")

    def test_not_applicable_fna98_axis_requires_reason(self) -> None:
        packet = self.minimal_pass()
        packet["fna98_gate"]["axes"]["condition_exception_check"] = "NOT_APPLICABLE"
        path = self.write_packet("na-no-reason.json", packet)
        completed, output = self.run_gate(path)
        self.assertEqual(completed.returncode, 3)

        packet["fna98_gate"]["axes"]["condition_exception_check"] = {
            "status": "NOT_APPLICABLE",
            "reason": "no conditional branch exists in this packet",
        }
        path = self.write_packet("na-with-reason.json", packet)
        completed, output = self.run_gate(path)
        self.assertEqual(completed.returncode, 0, output)

    def test_nested_unresolved_status_is_rejected_even_when_final_is_pass(self) -> None:
        for index, status in enumerate(("PENDING", "HOLD", "HOLD_BOUNDARY", "REVISE", "CONFLICT")):
            with self.subTest(status=status):
                packet = self.minimal_pass()
                packet["stage"] = {"status": status}
                path = self.write_packet(f"nested-{index}.json", packet)
                completed, output = self.run_gate(path)
                self.assertEqual(completed.returncode, 3)
                self.assertTrue(
                    any("unresolved status" in error for error in output["packets"][0]["errors"])
                )

    def test_unknown_plain_status_and_unresolved_qa_result_are_rejected(self) -> None:
        unknown = self.minimal_pass()
        unknown["stage"] = {"status": "UNKNOWN"}
        qa_hold = self.minimal_pass()
        qa_hold["qa"] = {"file_integrity": "HOLD"}
        validation_unknown = self.minimal_pass()
        validation_unknown["validation_passes"] = {"pass_1": "SCHEMA_PASS"}
        for index, packet in enumerate((unknown, qa_hold, validation_unknown)):
            with self.subTest(index=index):
                path = self.write_packet(f"unknown-result-{index}.json", packet)
                completed, output = self.run_gate(path)
                self.assertEqual(completed.returncode, 3)
                self.assertEqual(output["packets"][0]["status"], "FAIL")

    def test_malformed_json_and_nonobject_root_use_exit_2(self) -> None:
        malformed = self.root / "malformed.json"
        malformed.write_text("{not json", encoding="utf-8")
        nonobject = self.write_packet("array.json", [])
        for path in (malformed, nonobject):
            with self.subTest(path=path.name):
                completed, output = self.run_gate(path)
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(output["status"], "MALFORMED")
                self.assertEqual(output["packets"][0]["status"], "MALFORMED")

    def test_missing_file_and_no_arguments_use_exit_2(self) -> None:
        completed, output = self.run_gate(self.root / "absent.json")
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(output["status"], "MALFORMED")

        completed, output = self.run_gate()
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(output["status"], "MALFORMED")

    def test_one_failed_packet_fails_the_entire_batch(self) -> None:
        passing = self.write_packet("batch-pass.json", self.minimal_pass())
        failed_packet = self.minimal_pass()
        failed_packet["final_status"] = "PENDING"
        failing = self.write_packet("batch-fail.json", failed_packet)
        completed, output = self.run_gate(passing, failing)
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(output["status"], "FAIL")
        self.assertEqual([item["status"] for item in output["packets"]], ["PASS", "FAIL"])


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Regression tests for clone-kk2 route dependency preflight."""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
MANIFEST = SKILL_ROOT / "references" / "KK2_ROUTE_DEPENDENCIES.toml"
sys.path.insert(0, str(SCRIPT_DIR))

from preflight_route_dependencies import (  # noqa: E402
    PreflightError,
    load_manifest,
    preflight,
)


class RouteDependencyPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = load_manifest(MANIFEST)

    def run_preflight(
        self, route: str, enabled: set[str] | None = None, manifest: dict | None = None
    ) -> dict:
        return preflight(manifest or self.manifest, SKILL_ROOT, route, enabled or set())

    def test_current_required_routes_pass(self) -> None:
        cases = {
            "PIKACHU_CANONICAL_PATH": set(),
            "STRUCTURAL_JOINT_DISCOVERY": {"rq-writing"},
            "FIXED_KNIFE_SENTENCE_01_20_PATH": {"rq-writing", "rq-nak"},
            "DEEP_DENSE_240H_COMMON_PATH": set(),
        }
        for route, enabled in cases.items():
            with self.subTest(route=route):
                result = self.run_preflight(route, enabled)
                self.assertEqual(result["boot_status"], "PASS")
                self.assertEqual(result["route_status"], "PASS")
                self.assertEqual(result["holds"], [])

    def test_manifest_pins_exact_local_contracts(self) -> None:
        dependencies = self.manifest["dependencies"]
        self.assertEqual(
            set(dependencies),
            {"rq-sc7", "rq-writing", "rq-vedic-sentence-twin", "rq-nak"},
        )
        for dependency_id, dependency in dependencies.items():
            with self.subTest(dependency=dependency_id):
                self.assertTrue(dependency["allowed_names"])
                self.assertGreaterEqual(len(dependency["candidates"]), 1)
                for candidate in dependency["candidates"]:
                    self.assertTrue(Path(candidate["root"]).is_absolute())
                    self.assertEqual(candidate["contract_path"], "SKILL.md")
                    self.assertEqual(len(candidate["contract_sha256"]), 64)
                    int(candidate["contract_sha256"], 16)

    def test_dependency_hash_mismatch_holds_only_selected_route(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        for candidate in manifest["dependencies"]["rq-sc7"]["candidates"]:
            candidate["contract_sha256"] = "0" * 64
        result = self.run_preflight("PIKACHU_CANONICAL_PATH", manifest=manifest)
        self.assertEqual(result["boot_status"], "PASS")
        self.assertEqual(result["route_status"], "HOLD")
        self.assertEqual(result["dependencies"]["rq-sc7"]["status"], "HOLD")
        self.assertTrue(result["holds"])
        self.assertTrue(
            all(item["scope"] == "ROUTE:PIKACHU_CANONICAL_PATH" for item in result["holds"])
        )

    def test_conditional_nak_is_skipped_until_explicitly_enabled(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        for candidate in manifest["dependencies"]["rq-nak"]["candidates"]:
            candidate["contract_sha256"] = "0" * 64
        skipped = self.run_preflight(
            "FIXED_KNIFE_SENTENCE_01_20_PATH", manifest=manifest
        )
        self.assertEqual(skipped["route_status"], "PASS")
        self.assertEqual(skipped["dependencies"]["rq-nak"]["status"], "SKIPPED")

        enabled = self.run_preflight(
            "FIXED_KNIFE_SENTENCE_01_20_PATH", {"rq-nak"}, manifest
        )
        self.assertEqual(enabled["boot_status"], "PASS")
        self.assertEqual(enabled["route_status"], "HOLD")
        self.assertEqual(enabled["dependencies"]["rq-nak"]["status"], "HOLD")

    def test_lowest_priority_matching_candidate_is_selected(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        candidates = manifest["dependencies"]["rq-sc7"]["candidates"]
        candidates[0]["contract_sha256"] = "0" * 64
        result = self.run_preflight("PIKACHU_CANONICAL_PATH", manifest=manifest)
        selected = result["dependencies"]["rq-sc7"]["selected_candidate"]
        self.assertEqual(result["route_status"], "PASS")
        self.assertEqual(selected["priority"], 20)
        self.assertEqual(selected["package"], candidates[1]["package"])

    def test_frontmatter_name_mismatch_holds_dependency(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["dependencies"]["rq-writing"]["allowed_names"] = ["wrong-name"]
        result = self.run_preflight("PIKACHU_CANONICAL_PATH", manifest=manifest)
        self.assertEqual(result["boot_status"], "PASS")
        self.assertEqual(result["route_status"], "HOLD")
        self.assertEqual(result["dependencies"]["rq-writing"]["status"], "HOLD")

    def test_embedded_bundle_mismatch_is_a_boot_hold(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["embedded_rq_templ"]["archive_sha256"] = "0" * 64
        result = self.run_preflight("PIKACHU_CANONICAL_PATH", manifest=manifest)
        self.assertEqual(result["boot_status"], "HOLD")
        self.assertEqual(result["route_status"], "HOLD")
        self.assertTrue(any(item["scope"] == "BOOT" for item in result["holds"]))

    def test_external_rq_templ_is_never_a_dependency_candidate(self) -> None:
        result = self.run_preflight("PIKACHU_CANONICAL_PATH")
        self.assertEqual(
            result["embedded_rq_templ"]["resolution_policy"], "EMBEDDED_ONLY"
        )
        self.assertFalse(result["embedded_rq_templ"]["external_lookup"])
        self.assertNotIn("rq-templ", self.manifest["dependencies"])

    def test_undeclared_conditional_is_rejected(self) -> None:
        with self.assertRaises(PreflightError):
            self.run_preflight("PIKACHU_CANONICAL_PATH", {"rq-nak"})

    def test_cli_emits_pass_json_for_current_pikachu_route(self) -> None:
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(SCRIPT_DIR / "preflight_route_dependencies.py"),
                "--manifest",
                str(MANIFEST),
                "--route",
                "PIKACHU_CANONICAL_PATH",
                "--indent",
                "0",
            ],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["boot_status"], "PASS")
        self.assertEqual(payload["route_status"], "PASS")


if __name__ == "__main__":
    unittest.main()

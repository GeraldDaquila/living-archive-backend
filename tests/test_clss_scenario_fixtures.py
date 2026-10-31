"""Structural checks for CLSS synthetic scenario fixtures.

These tests verify fixture integrity only; they do not evaluate model outputs.
Run from repository root with: python -m unittest discover -s tests
"""
import json
import unittest
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "clss"
    / "CLSS_SCENARIO_FIXTURES.json"
)
EXPECTED_IDS = {
    "self-correction-evidence",
    "self-intent-action-divergence",
    "third-party-single-anecdote",
    "third-party-motive-allegation",
    "sparse-answers",
    "internally-contradictory-account",
    "conflicting-witness-accounts",
    "benevolent-intent-harmful-impact",
    "coherence-untested-assumption",
    "retaliation-or-suppressed-dissent",
    "system-design-source",
    "norm-conformity-trap",
    "conversation-before-doorway",
    "provider-failure",
    "perspective-pair",
}
ALLOWED_PERSPECTIVES = {"self", "third_party", "both"}
ALLOWED_DOORWAY_STATUSES = {"insufficient_evidence", "not_needed"}


class CLSSScenarioFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with FIXTURE_PATH.open(encoding="utf-8") as handle:
            cls.fixture = json.load(handle)

    def test_fixture_is_explicitly_not_model_evaluated(self):
        self.assertEqual(
            self.fixture.get("status"),
            "scenario-contract-only-not-model-evaluated",
        )

    def test_scenario_ids_are_exact_and_unique(self):
        scenarios = self.fixture.get("scenarios")
        self.assertIsInstance(scenarios, list)
        ids = [scenario.get("id") for scenario in scenarios]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), EXPECTED_IDS)
        self.assertEqual(len(ids), 15)

    def test_each_scenario_has_required_review_fields(self):
        for scenario in self.fixture["scenarios"]:
            with self.subTest(scenario=scenario.get("id")):
                self.assertIn(scenario.get("perspective"), ALLOWED_PERSPECTIVES)
                self.assertIsInstance(scenario.get("input_pattern"), str)
                self.assertTrue(scenario["input_pattern"].strip())
                self.assertIsInstance(scenario.get("must_preserve"), list)
                self.assertTrue(scenario["must_preserve"])
                self.assertIsInstance(scenario.get("must_not_claim"), list)
                self.assertTrue(scenario["must_not_claim"])
                self.assertIsInstance(scenario.get("next_step"), str)
                self.assertTrue(scenario["next_step"].strip())

    def test_doorway_status_is_restrictive_when_present(self):
        for scenario in self.fixture["scenarios"]:
            if "doorway_status" in scenario:
                with self.subTest(scenario=scenario["id"]):
                    self.assertIn(
                        scenario["doorway_status"],
                        ALLOWED_DOORWAY_STATUSES,
                    )

    def test_sensitive_scenarios_remain_explicitly_covered(self):
        ids = {scenario["id"] for scenario in self.fixture["scenarios"]}
        self.assertIn("retaliation-or-suppressed-dissent", ids)
        self.assertIn("conflicting-witness-accounts", ids)
        self.assertIn("provider-failure", ids)
        self.assertIn("perspective-pair", ids)


if __name__ == "__main__":
    unittest.main()

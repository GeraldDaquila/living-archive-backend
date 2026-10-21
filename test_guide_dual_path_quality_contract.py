"""Architecture contract tests for the Guide's LLM-first dual-path design.

These tests deliberately check stable, normative contract language and protected
boundaries. Runtime path behavior remains covered by the existing focused and
integration regression suites; these tests do not substitute for live E2E QA.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTRACT = (ROOT / "docs" / "guide-dual-path-quality-contract.md").read_text(encoding="utf-8")


class GuideDualPathQualityContractTests(unittest.TestCase):
    def test_llm_first_and_deterministic_floor_are_explicit(self):
        self.assertIn("The Guide is LLM-first.", CONTRACT)
        self.assertIn("quality floor, not a reasoning ceiling", CONTRACT)
        self.assertIn("deterministic resilience path", CONTRACT.lower())

    def test_both_paths_share_hard_quality_invariants(self):
        for invariant in (
            "Intent preservation",
            "Evidence honesty",
            "Resource relevance",
            "No fabricated certainty",
            "Output integrity",
        ):
            with self.subTest(invariant=invariant):
                self.assertIn(invariant, CONTRACT)

    def test_llm_must_not_trade_away_contract_for_fluency(self):
        self.assertIn("An LLM provider returning HTTP success is not evidence of answer quality.", CONTRACT)
        self.assertIn("A higher aggregate score cannot compensate for a hard failure", CONTRACT)

    def test_qa_requires_positive_negative_and_live_service_gates(self):
        for gate in (
            "positive and negative controls",
            "Primary and mirror deployments are live",
            "Simulated live API calibration and negative-control requests pass",
            "CI success permits deployment; it does not, by itself, prove live end-to-end readiness.",
        ):
            with self.subTest(gate=gate):
                self.assertIn(gate, CONTRACT)

    def test_protected_boundaries_are_explicit(self):
        self.assertIn("protected `use_core.py`", CONTRACT)
        self.assertIn("frozen HRN-LLM branch", CONTRACT)
        self.assertIn("Cowboy MCP remains sole authority", CONTRACT)


if __name__ == "__main__":
    unittest.main()

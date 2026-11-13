"""Regression for absolute outer visitor-boundary recovery precedence."""
import unittest
from pathlib import Path

MAIN = Path(__file__).with_name("main.py").read_text(encoding="utf-8")

class OuterBoundaryRegisteredRecoveryTests(unittest.TestCase):
    def test_outer_boundary_is_registry_aware(self):
        self.assertIn("_outer_registered_recovery_valid", MAIN)
        self.assertIn("outer visitor boundary: restored bounded registered conceptual orientation", MAIN)

    def test_generic_and_meta_failures_are_replaced_at_last_mile(self):
        self.assertIn("_outer_response_failure", MAIN)
        self.assertIn("is_generic_nonanswer(query, response_text)", MAIN)
        self.assertIn("is_meta_answer_failure(response_text)", MAIN)

    def test_stale_fallback_navigation_is_not_preserved(self):
        self.assertIn('safe["recommendation"] = None', MAIN)
        self.assertIn('route_source"] = "guide_outer_visitor_boundary"', MAIN)

    def test_outer_boundary_checks_deterministic_registered_recoveries(self):
        self.assertIn("has_registered_recovery as _terminal_has_registered_recovery", MAIN)
        self.assertIn("outer_visitor_boundary_deterministic_registered_recovery", MAIN)
        self.assertIn("restored registered deterministic orientation", MAIN)

    def test_exact_public_predictive_failure_cannot_reach_generic_refusal(self):
        self.assertIn("_terminal_has_registered_recovery(query)", MAIN)
        self.assertIn("compose_recovery as _terminal_compose_recovery", MAIN)
        self.assertIn("registered_recovery_recommendation as _terminal_recovery_recommendation", MAIN)
        self.assertIn('safe["recommendation"] = _terminal_recovery_recommendation(query)', MAIN)

if __name__ == "__main__":
    unittest.main()

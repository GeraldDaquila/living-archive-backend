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

if __name__ == "__main__":
    unittest.main()

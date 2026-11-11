"""Regression for final registered conceptual recovery boundary."""
import unittest
from pathlib import Path

MAIN = Path(__file__).with_name("main.py").read_text(encoding="utf-8")

class FinalRegisteredRecoveryBoundaryTests(unittest.TestCase):
    def test_final_boundary_uses_registered_recovery_not_only_relationship_classifier(self):
        self.assertIn("_final_registered_conceptual_recovery_valid", MAIN)
        self.assertIn("final registered-recovery boundary", MAIN)

    def test_generic_failure_can_be_replaced_by_valid_registered_orientation(self):
        self.assertIn("_response_is_generic_failure", MAIN)
        self.assertIn("is_generic_nonanswer(query, response)", MAIN)
        self.assertIn("is_meta_answer_failure(response)", MAIN)

    def test_quality_guards_apply_to_registered_recovery(self):
        self.assertIn("is_generic_nonanswer(
            query, _final_registered_conceptual_recovery", MAIN)
        self.assertIn("is_meta_answer_failure(
            _final_registered_conceptual_recovery", MAIN)

if __name__ == "__main__":
    unittest.main()

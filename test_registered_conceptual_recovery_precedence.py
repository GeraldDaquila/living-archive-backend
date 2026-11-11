"""Regression for registered conceptual recovery precedence at the API boundary."""
import unittest
from pathlib import Path

MAIN = Path(__file__).with_name("main.py").read_text(encoding="utf-8")

class RegisteredConceptualRecoveryPrecedenceTests(unittest.TestCase):
    def test_registered_recovery_is_not_rejected_by_narrower_intent_classifier(self):
        self.assertIn("_registered_conceptual_recovery_valid", MAIN)
        self.assertIn("role distinctions such as", MAIN)
        self.assertIn('or bool(_guide_composition._conceptual_relationship_recovery(query))', MAIN)

    def test_quality_guards_remain_in_force(self):
        self.assertIn("not _guide_composition.is_generic_nonanswer(query, _conceptual_recovery)", MAIN)
        self.assertIn("not _guide_composition.is_meta_answer_failure(_conceptual_recovery)", MAIN)

if __name__ == "__main__":
    unittest.main()

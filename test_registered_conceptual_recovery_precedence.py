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

    def test_gold_star_baseline_is_wired_into_live_composition(self):
        self.assertIn("active_quality_contribution as _gold_star_active_quality_contribution", MAIN)
        self.assertIn("_gold_star_quality = _gold_star_active_quality_contribution(query)", MAIN)
        self.assertIn("Gold Star structural baseline: answer the recognized question first.", MAIN)
        self.assertIn("if _direct_answer_baseline", MAIN)
        self.assertIn("_direct_answer_baseline = bool(_matched_orientation or _gold_star_quality)", MAIN)

    def test_gold_star_baseline_uses_application_closing_not_context_fallback(self):
        self.assertIn("Gold Star closing discipline", MAIN)
        self.assertIn("where this distinction matters most", MAIN)
        self.assertNotIn("If you add context about the situation, people involved, or decision at stake, the question can be examined more specifically.", MAIN)

if __name__ == "__main__":
    unittest.main()

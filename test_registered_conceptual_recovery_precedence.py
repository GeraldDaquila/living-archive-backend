"""Regression for registered conceptual recovery precedence at the API boundary."""
import unittest
from pathlib import Path

MAIN = Path(__file__).with_name("main.py").read_text(encoding="utf-8")
COMPOSITION = Path(__file__).with_name("general_guide_composition.py").read_text(encoding="utf-8")

class RegisteredConceptualRecoveryPrecedenceTests(unittest.TestCase):
    def test_registered_recovery_is_not_rejected_by_narrower_intent_classifier(self):
        self.assertIn("_registered_conceptual_recovery_valid", MAIN)
        self.assertIn("role distinctions such as", MAIN)
        self.assertIn('or bool(_guide_composition._conceptual_relationship_recovery(query))', MAIN)

    def test_quality_guards_remain_in_force(self):
        self.assertIn("not _guide_composition.is_generic_nonanswer(query, _conceptual_recovery)", MAIN)
        self.assertIn("not _guide_composition.is_meta_answer_failure(_conceptual_recovery)", MAIN)

    def test_gold_star_baseline_is_wired_into_live_composition(self):
        # Active Gold Star guidance now belongs to the provider-neutral composer,
        # not the API boundary. Verify retrieval, structural-only authority,
        # adjudication, prompt exposure, and exact control-arm isolation there.
        self.assertIn("active_quality_contribution as _gold_star_active_quality_contribution", COMPOSITION)
        self.assertIn("else _gold_star_active_quality_contribution(question)", COMPOSITION)
        self.assertIn("gold_star_quality.get(\"authority_mode\") != \"structural_guidance_only\"", COMPOSITION)
        self.assertIn("gold_star_quality_instruction = _build_gold_star_quality_instruction(gold_star_quality)", COMPOSITION)
        self.assertIn("gold_star_quality_instruction=gold_star_quality_instruction", COMPOSITION)
        self.assertIn('evaluation.arm == "control"', COMPOSITION)

    def test_gold_star_baseline_uses_application_closing_not_context_fallback(self):
        self.assertIn("Gold Star closing discipline", MAIN)
        self.assertIn("where this distinction matters most", MAIN)
        self.assertNotIn("If you add context about the situation, people involved, or decision at stake, the question can be examined more specifically.", MAIN)

if __name__ == "__main__":
    unittest.main()

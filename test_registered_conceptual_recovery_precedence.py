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
        composition = Path(__file__).with_name("general_guide_composition.py").read_text(encoding="utf-8")
        self.assertIn("active_quality_contribution as _gold_star_active_quality_contribution", composition)
        self.assertIn("else _gold_star_active_quality_contribution(question)", composition)
        self.assertIn("GOLD STAR MULTI-CANDIDATE ADJUDICATION", composition)
        self.assertIn("discipline=", composition)
        self.assertIn("boundary=", composition)
        self.assertIn("Never transfer exemplar answers, claims, examples, citations, or doorways.", composition)
        self.assertIn("authority_mode", composition)
        self.assertIn('gold_star_quality.get("authority_mode") != "structural_guidance_only"', composition)
        self.assertIn('reasoning_discipline_ids=gold_star_adjudication_trace["reasoning_discipline_ids"]', composition)
        self.assertIn("gold_star_quality_instruction=gold_star_quality_instruction", composition)
        self.assertIn("included_in_provider_prompt=bool(gold_star_quality_instruction)", composition)
        self.assertIn('parse=_parse_factory(documents, effective_question, gold_star_quality.get("candidates") if gold_star_quality else None)', composition)
        self.assertIn('candidates=gold_star_quality.get("candidates") if gold_star_quality else None', composition)

    def test_gold_star_baseline_uses_application_closing_not_context_fallback(self):
        self.assertIn("Gold Star closing discipline", MAIN)
        self.assertIn("where this distinction matters most", MAIN)
        self.assertNotIn("If you add context about the situation, people involved, or decision at stake, the question can be examined more specifically.", MAIN)

if __name__ == "__main__":
    unittest.main()

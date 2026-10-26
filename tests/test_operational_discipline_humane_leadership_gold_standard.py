import json
import unittest
from pathlib import Path

from general_guide_composition import operational_discipline_humane_leadership_recovery
from general_guide_gold_standards import resolve_exact_gold_standard

REGISTRY = Path(__file__).resolve().parents[1] / "docs" / "qa" / "gold_standard_registry.json"
QUESTION = "What is the role of operational discipline in humane leadership?"


class OperationalDisciplineGoldStandardTests(unittest.TestCase):
    def test_question_resolves_to_approved_gold_standard(self):
        record = resolve_exact_gold_standard(QUESTION)
        self.assertIsNotNone(record)
        self.assertEqual(
            record["benchmark_id"],
            "general-guide-operational-discipline-humane-leadership-gold-standard-2026-10-26",
        )
        self.assertEqual(record["status"], "USER_APPROVED_GOLD_STANDARD")
        self.assertEqual(
            len([p for p in record["expected_response"].split("\n\n") if p.strip()]),
            3,
        )

    def test_recovery_answers_question_in_three_substantive_paragraphs(self):
        response = operational_discipline_humane_leadership_recovery(QUESTION)
        self.assertIsNotNone(response)
        paragraphs = [p for p in response.split("\n\n") if p.strip()]
        self.assertEqual(len(paragraphs), 3)
        self.assertIn("turning humane intentions into reliable actions", paragraphs[0])
        self.assertIn("clear responsibilities", paragraphs[1])
        self.assertIn("not rigid rule-following", paragraphs[2])
        self.assertNotIn("Please try again shortly", response)

    def test_recovery_is_narrowly_scoped(self):
        self.assertIsNone(
            operational_discipline_humane_leadership_recovery("What is humane leadership?")
        )

    def test_registry_has_exactly_one_record_for_question(self):
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
        matches = [r for r in payload["records"] if r.get("query") == QUESTION]
        self.assertEqual(len(matches), 1)


if __name__ == "__main__":
    unittest.main()

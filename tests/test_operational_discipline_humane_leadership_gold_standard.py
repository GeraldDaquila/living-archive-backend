import asyncio
import json
import unittest
from pathlib import Path

import main
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
            resolve_exact_gold_standard(QUESTION.rstrip("?"))["benchmark_id"],
            "general-guide-operational-discipline-humane-leadership-gold-standard-2026-10-26",
        )
        self.assertEqual(
            resolve_exact_gold_standard(QUESTION.rstrip("?") + ".")["benchmark_id"],
            "general-guide-operational-discipline-humane-leadership-gold-standard-2026-10-26",
        )
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


    def test_blank_gold_standard_doorway_preserves_independently_selected_doorway(self):
        selected_doorway = {
            "title": "Foundational Stewardship Cases",
            "url": "https://geralddaquila.com/level-1-case-catalog/",
        }
        standard = resolve_exact_gold_standard(QUESTION)
        self.assertIsNotNone(standard)
        self.assertEqual(standard["doorway_title"], "")
        self.assertFalse(standard["forbids_doorway"])
        self.assertEqual(
            main._enforce_registered_gold_standard_doorway(selected_doorway, standard),
            selected_doorway,
        )
        # If an upstream path did not resolve the standard, the shared default
        # remains intact; relevance and canonical URL checks happen upstream.
        self.assertEqual(
            main._enforce_registered_gold_standard_doorway(selected_doorway, None, QUESTION),
            selected_doorway,
        )

    def test_explicit_no_handoff_standard_suppresses_doorway(self):
        selected_doorway = {
            "title": "Foundational Stewardship Cases",
            "url": "https://geralddaquila.com/level-1-case-catalog/",
        }
        standard = resolve_exact_gold_standard(
            "Explain stewardship, but do not send me to another page yet."
        )
        self.assertIsNotNone(standard)
        self.assertTrue(standard["forbids_doorway"])
        self.assertIsNone(
            main._enforce_registered_gold_standard_doorway(selected_doorway, standard)
        )


    def test_universal_json_sender_preserves_default_doorway_for_approved_answer(self):
        messages = []
        selected_doorway = {
            "title": "Foundational Stewardship Cases",
            "url": "https://geralddaquila.com/level-1-case-catalog/",
        }
        payload = {
            "ok": True,
            "query": QUESTION,
            "response": operational_discipline_humane_leadership_recovery(QUESTION),
            "recommendation": selected_doorway,
        }

        async def fake_send(message):
            messages.append(message)

        asyncio.run(main._use_send_json(fake_send, payload))
        body = json.loads(messages[-1]["body"].decode("utf-8"))
        self.assertEqual(body["recommendation"], selected_doorway)
        self.assertEqual(body["response"], operational_discipline_humane_leadership_recovery(QUESTION))

    def test_universal_json_sender_honors_explicit_no_handoff_standard(self):
        messages = []
        payload = {
            "ok": True,
            "query": "Explain stewardship, but do not send me to another page yet.",
            "response": "A substantive answer.",
            "recommendation": {
                "title": "Foundational Stewardship Cases",
                "url": "https://geralddaquila.com/level-1-case-catalog/",
            },
        }

        async def fake_send(message):
            messages.append(message)

        asyncio.run(main._use_send_json(fake_send, payload))
        body = json.loads(messages[-1]["body"].decode("utf-8"))
        self.assertIsNone(body["recommendation"])

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

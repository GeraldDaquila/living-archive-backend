"""Static guardrails for the proposed CLSS WordPress candidate.

These checks inspect source-level invariants only. They do not replace PHP lint,
JavaScript parsing, or browser acceptance.
"""
import unittest
from pathlib import Path


CANDIDATE = (
    Path(__file__).resolve().parents[1]
    / "clss"
    / "wordpress"
    / "clss-guided-reflection-prototype.php"
)


class CLSSWordPressCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = CANDIDATE.read_text(encoding="utf-8")

    def test_candidate_is_separate_from_live_plugin_path(self):
        self.assertTrue(CANDIDATE.is_file())
        self.assertIn("Version: 0.2.0", self.source)

    def test_both_perspectives_are_explicit_and_separate(self):
        self.assertIn('self:[', self.source)
        self.assertIn('third_party:[', self.source)
        self.assertIn('data-choose-perspective="self"', self.source)
        self.assertIn('data-choose-perspective="third_party"', self.source)

    def test_nine_prompts_per_perspective(self):
        self.assertIn('Question "+(state.index+1)+" of "+list.length', self.source)
        self.assertIn('new Array(9).fill("")', self.source)
        self.assertIn('state.index<promptsForMode().length-1', self.source)

    def test_missing_answers_are_not_negative_evidence(self):
        self.assertIn("A blank answer is missing information, not evidence against anyone.", self.source)
        self.assertIn("There is not enough information here to draw a fair conclusion.", self.source)

    def test_no_verdict_or_score(self):
        self.assertIn("It does not score a person", self.source)
        self.assertIn("does not independently verify them", self.source)
        self.assertIn("Do not use this reflection alone", self.source)

    def test_answer_text_is_escaped_before_html_insertion(self):
        self.assertIn("function safeText(value)", self.source)
        self.assertIn("safeText(answer).replace", self.source)

    def test_no_network_or_persistent_answer_storage_api(self):
        forbidden = ("fetch(", "XMLHttpRequest", "sendBeacon(", "localStorage", "sessionStorage")
        for marker in forbidden:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, self.source)

    def test_print_and_restart_controls_exist(self):
        self.assertIn('data-print', self.source)
        self.assertIn('window.print()', self.source)
        self.assertIn('data-restart', self.source)

    def test_action_container_markup_is_well_formed_in_candidate(self):
        self.assertNotIn('>div class="clss-dp-actions"', self.source)
        self.assertIn('<div class="clss-dp-actions">', self.source)


if __name__ == "__main__":
    unittest.main()

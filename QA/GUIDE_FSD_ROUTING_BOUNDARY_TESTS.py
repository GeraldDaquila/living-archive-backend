"""Structural regressions for Guide-vs-FSD routing boundaries.

These tests exercise the shared classifier, not a single hard-coded live response.
"""
import unittest
import main


class GuideFsdRoutingBoundaryTests(unittest.TestCase):
    def test_human_agency_question_about_broken_system_stays_in_guide(self):
        query = (
            "How can a person take responsibility for change without becoming "
            "responsible for fixing an entire broken system?"
        )
        self.assertFalse(main._is_fsd_request(query))

    def test_related_personal_responsibility_questions_stay_in_guide(self):
        queries = [
            "How can I contribute to change without carrying the whole burden?",
            "What is my role in helping a community change when I cannot fix everything?",
            "How can people act responsibly without becoming accountable for every systemic failure?",
        ]
        for query in queries:
            with self.subTest(query=query):
                self.assertFalse(main._is_fsd_request(query))

    def test_explicit_fsd_request_still_enters_fsd(self):
        self.assertTrue(
            main._is_fsd_request(
                "Please open the Fractal Systems Diagnostic for this organization."
            )
        )

    def test_genuine_system_diagnosis_remains_fsd_eligible(self):
        self.assertTrue(
            main._is_fsd_request(
                "What is causing this organization's governance system to fail?"
            )
        )


if __name__ == "__main__":
    unittest.main()

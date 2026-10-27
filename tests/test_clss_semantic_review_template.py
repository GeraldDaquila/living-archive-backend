"""Integrity checks for the CLSS human semantic-review template.

These tests validate coverage and status labeling only; they do not evaluate
candidate responses or claim semantic acceptance.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parent
FIXTURES = ROOT / "fixtures" / "clss"
CASES_PATH = FIXTURES / "stewardship-coherence-cases.json"
RECORDS_PATH = FIXTURES / "semantic-review-records-template.json"
REQUIRED_REVIEW_FIELDS = {
    "case_id",
    "candidate_source",
    "reviewer_id",
    "finding_matches_expected",
    "evidence_traceability",
    "provenance_preserved",
    "context_and_repair_preserved",
    "prohibited_inference_absent",
    "visitor_usefulness",
    "notes",
}
REVIEW_STATUSES = {"pass", "fail", "not_reviewed"}
CASE_DIMENSIONS = (
    "finding_matches_expected",
    "evidence_traceability",
    "provenance_preserved",
    "context_and_repair_preserved",
    "prohibited_inference_absent",
    "visitor_usefulness",
)


class CLSSSemanticReviewTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))["cases"]
        cls.template = json.loads(RECORDS_PATH.read_text(encoding="utf-8"))

    def test_template_is_explicitly_not_evaluated(self):
        self.assertEqual(self.template.get("status"), "not_evaluated")
        self.assertIn("not completed human reviews", self.template.get("note", ""))

    def test_template_covers_each_canonical_case_exactly_once(self):
        expected = {case["id"] for case in self.cases}
        records = self.template.get("records", [])
        actual = [record.get("case_id") for record in records]
        self.assertEqual(len(actual), len(set(actual)))
        self.assertEqual(set(actual), expected)

    def test_review_records_have_required_fields_and_no_premature_pass(self):
        for record in self.template["records"]:
            with self.subTest(case=record["case_id"]):
                self.assertEqual(set(record), REQUIRED_REVIEW_FIELDS)
                self.assertIn(record["candidate_source"], {"human_authored", "model_candidate", "fallback_candidate"})
                for dimension in CASE_DIMENSIONS:
                    self.assertIn(record[dimension], REVIEW_STATUSES)
                    self.assertEqual(record[dimension], "not_reviewed")
                self.assertEqual(record["reviewer_id"], "")
                self.assertEqual(record["notes"], "")


if __name__ == "__main__":
    unittest.main()

"""Structural regression checks for the versioned HRN closure candidate.

These checks are intentionally static; the PHP syntax workflow validates parseability.
Live WordPress behavior remains a separate release gate.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "wordpress/hrn/human-relational-navigator.php").read_text(encoding="utf-8")


class HRNClosureEvidenceContract(unittest.TestCase):
    def test_release_identity_is_sequential_and_aligned(self):
        self.assertRegex(SOURCE[:500], r"Version: 0\\.5\\.278")
        self.assertIn("const VERSION = '0.5.278';", SOURCE)
        self.assertEqual(len(re.findall(r"0\\.5\\.277", SOURCE)), 0)

    def test_closure_message_is_considered_as_a_distinct_evidence_source(self):
        self.assertIn("$state['closure_message']", SOURCE)
        self.assertIn("$sources[] = strtolower($closure_evidence);", SOURCE)

    def test_closure_commands_are_removed_before_evidence_is_accepted(self):
        start = SOURCE.index("function closure_synthesis_carries_journey_evidence(")
        end = SOURCE.index("private function closure_synthesis_is_bounded(", start)
        method = SOURCE[start:end]
        self.assertIn("please\\\\s+synthesize", method)
        self.assertIn("I\\\\s+have\\\\s+reached\\\\s+enough\\\\s+for\\\\s+now", method)
        self.assertIn("mb_strlen($closure_evidence) >= 30", method)
        self.assertIn("strpos($closure_evidence, '?') === false", method)

    def test_existing_evidence_floor_is_not_weakened(self):
        start = SOURCE.index("function closure_synthesis_carries_journey_evidence(")
        end = SOURCE.index("private function closure_synthesis_is_bounded(", start)
        method = SOURCE[start:end]
        self.assertIn("if ($overlap >= 2) return true;", method)
        self.assertIn("if ($text === '' || empty($sources)) return false;", method)

    def test_live_writer_and_safety_methods_remain_present(self):
        for signature in (
            "function groq_compose(",
            "function humanity_gate(",
            "function prescriptive_response_violation(",
            "function visitor_surface_language_violation(",
        ):
            self.assertIn(signature, SOURCE)


if __name__ == "__main__":
    unittest.main()

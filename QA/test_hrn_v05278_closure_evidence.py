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
        self.assertIn("Version: 0.5.311", SOURCE[:500])
        self.assertIn("const VERSION = '0.5.311';", SOURCE)
        self.assertNotIn("0.5.277", SOURCE)

    def test_closure_message_is_considered_as_a_distinct_evidence_source(self):
        self.assertIn("$state['closure_message']", SOURCE)
        self.assertIn("$sources[] = strtolower($closure_evidence);", SOURCE)

    def test_closure_commands_are_removed_before_evidence_is_accepted(self):
        start = SOURCE.index("function closure_synthesis_carries_journey_evidence(")
        end = SOURCE.index("private function closure_synthesis_is_bounded(", start)
        method = SOURCE[start:end]
        self.assertIn("closure_parts = preg_split", method)
        self.assertIn("closure_evidence", method)
        self.assertIn("mb_strlen($closure_evidence) >= 30", method)
        self.assertIn("strpos($closure_evidence, '?') === false", method)

    def test_existing_evidence_floor_is_not_weakened(self):
        start = SOURCE.index("function closure_synthesis_carries_journey_evidence(")
        end = SOURCE.index("private function closure_synthesis_is_bounded(", start)
        method = SOURCE[start:end]
        self.assertIn("if ($overlap >= 2) return true;", method)
        self.assertIn("if ($text === '' || empty($sources)) return false;", method)


    def test_natural_landing_has_policy_gated_local_recovery_before_503(self):
        marker = "if ($junction_land && $banked_summary !== '') {"
        start = SOURCE.index(marker)
        error_pos = SOURCE.index("'spiral_landing_composition_unavailable'", start)
        end = SOURCE.index("\n        } else {", error_pos)
        branch = SOURCE[start:end]
        self.assertIn("$this->recover_natural_landing_response($landing_state)", branch)
        helper_start = SOURCE.index("private function recover_natural_landing_response(")
        helper_end = SOURCE.index("\n    private function ", helper_start + 30)
        helper = SOURCE[helper_start:helper_end]
        self.assertIn("$this->local_grounded_closure_synthesis($state)", helper)
        self.assertIn("$this->humanity_gate($local_landing, $state)", helper)
        self.assertIn("$this->closure_synthesis_is_bounded($local_landing)", helper)
        self.assertIn("$this->closure_synthesis_carries_journey_evidence($local_landing, $state)", helper)
        self.assertLess(branch.index("$this->recover_natural_landing_response($landing_state)"), branch.index("'spiral_landing_composition_unavailable'"))

    def test_missing_ordinary_question_is_not_blocked_by_default_rest_flags(self):
        marker = "// Structural continuation invariant:"
        start = SOURCE.index(marker)
        end = SOURCE.index("if (!$junction_land && !$visitor_closure && !$visitor_resource_request", start)
        block = SOURCE[start:end]
        self.assertNotIn("empty($response['rest'])", block)
        self.assertNotIn("empty($response['use_resource'])", block)
        self.assertIn("$this->structural_question_completion_safe(", SOURCE[end:end + 1800])

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

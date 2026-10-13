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
        self.assertIn("Version: 0.5.325", SOURCE[:500])
        self.assertIn("const VERSION = '0.5.325';", SOURCE)
        self.assertNotIn("0.5.277", SOURCE)









    def test_soft_action_frames_are_rejected_by_the_response_policy(self):
        start = SOURCE.index("private function prescriptive_response_violation(")
        end = SOURCE.index("private function humanity_gate(", start)
        method = SOURCE[start:end]
        self.assertIn("makes it possible|allows|enables|creates room|opens a space|invites a new rhythm", method)
        self.assertIn("decide whether you want to|guide (?:that|the|this) (?:change|shift|outcome)|watch it happen", method)

    def test_unselected_resource_offer_sentence_is_removed_from_visitor_response(self):
        self.assertIn("private function strip_unselected_resource_offer(", SOURCE)
        self.assertIn("if (!$use_resource) {", SOURCE)
        self.assertIn("$response = $this->strip_unselected_resource_offer($response);", SOURCE)
        self.assertIn("$mentions_resource && $offers_resource", SOURCE)

    def test_generic_next_part_question_is_rejected_before_visitor_grounded_recovery(self):
        self.assertIn("what becomes clearer when you look toward that next part of the situation", SOURCE)
        self.assertIn("if (strpos($q, 'what becomes clearer when you look toward that next part of the situation') !== false) return true;", SOURCE)

    def test_blame_understanding_contrast_has_a_grounded_question_fallback(self):
        self.assertIn("$blame_without_understanding = preg_match", SOURCE)
        self.assertIn("What do you want them to understand that might otherwise sound like blame?", SOURCE)




    def test_tone_displacement_recovery_rotates_after_prior_tone_question(self):
        start = SOURCE.index("private function structural_question_completion_safe(")
        end = SOURCE.index("$warmth_without_honesty = preg_match", start + 40)
        method = SOURCE[start:end]
        self.assertIn("$tone_focus_question_already_asked = false", method)
        self.assertIn("What changes in your ability to explain the hurt when the conversation turns to defending your tone?", method)

    def test_tone_displacement_is_a_structured_recovery_relevance_family(self):
        start = SOURCE.index("private function structured_recovery_candidate_is_relevant(")
        end = SOURCE.index("private function recover_structured_state_composition(", start)
        method = SOURCE[start:end]
        self.assertIn("'tone_displacement' => array('tone','said','hurt','embarrassed','defend','discussion')", method)



    def test_natural_language_landing_is_an_explicit_terminal_closure(self):
        start = SOURCE.index("private function visitor_requests_closure(")
        end = SOURCE.index("private function closure_synthesis_carries_journey_evidence(", start)
        method = SOURCE[start:end]
        self.assertIn("let (?:this|the) (?:conversation|discussion|exchange) (?:land|rest|settle)", method)
        self.assertIn("foreach ($patterns as $pattern) if (preg_match($pattern, $m)) return true;", method)

    def test_short_close_uses_bounded_visitor_turn_evidence(self):
        start = SOURCE.index("private function provider_independent_terminal_closure(")
        end = SOURCE.index("private function ", start + 40)
        method = SOURCE[start:end]
        self.assertIn("'visitor_turn_evidence'", method)
        self.assertIn("'last_question'", method)
        self.assertIn("$closure_evidence_parts", method)
        gate_start = SOURCE.index("private function closure_synthesis_carries_journey_evidence(")
        gate_end = SOURCE.index("private function ", gate_start + 40)
        gate = SOURCE[gate_start:gate_end]
        self.assertIn("$state['visitor_turn_evidence']", gate)
        self.assertIn("$sources[] = strtolower($visitor_evidence_item)", gate)
        self.assertIn("'visitor_turn_evidence'=>$ledger['visitor_turn_evidence']??array()", SOURCE)
        self.assertIn("'visitor_turn_evidence'=>array()", SOURCE)

    def test_provider_exhausted_tone_displacement_closure_uses_current_transcript(self):
        start = SOURCE.index("private function provider_independent_terminal_closure(")
        end = SOURCE.index("private function ", start + 40)
        method = SOURCE[start:end]
        self.assertIn("$closure_message", method)
        self.assertIn("$tone_displacement_closure", method)
        self.assertIn("'round_synthesis_history'", method)
        self.assertIn("'fractal_records'", method)
        self.assertIn("$closure_evidence_parts", method)
        self.assertIn("You said that when you defend your tone, the original hurt gets set aside", method)
        self.assertIn("stated without adding an explanation", method)


    def test_provider_exhaustion_recovers_tone_displacement_from_current_visitor_material(self):
        start = SOURCE.index("private function recover_structured_state_composition(")
        end = SOURCE.index("private function normalize_composition(", start)
        method = SOURCE[start:end]
        self.assertIn("$tone_displacement_candidate = ''", method)
        self.assertIn("$tone_displacement_message = strtolower((string)$message)", method)
        self.assertIn("The discussion keeps moving away from what was said and toward your tone.", method)
        self.assertIn("$tone_displacement_candidate,", method)


    def test_tone_displacement_recovers_a_new_grounded_question_plane(self):
        start = SOURCE.index("private function structural_question_completion_safe(")
        end = SOURCE.index("$warmth_without_honesty = preg_match", start + 40)
        method = SOURCE[start:end]
        self.assertIn("$tone_displacement = preg_match", method)
        self.assertIn("What changes in the conversation when your tone becomes the focus instead of what was said?", method)
        self.assertIn("does not assume the other person's motive or gender", method)


    def test_blame_and_mutual_understanding_are_structured_recovery_families(self):
        start = SOURCE.index("private function structured_recovery_candidate_is_relevant(")
        end = SOURCE.index("private function recover_structured_state_composition(", start)
        method = SOURCE[start:end]
        self.assertIn("'blame_assignment' => array('blame','blaming','fault','accuse','accusation')", method)
        self.assertIn("'mutual_understanding' => array('understand','understanding','communicate','communication','hear','heard','listen','listening')", method)

    def test_structured_recovery_uses_current_observer_contrast_before_prior_turn_memory(self):
        start = SOURCE.index("private function recover_structured_state_composition(")
        end = SOURCE.index("private function normalize_composition(", start)
        method = SOURCE[start:end]
        self.assertIn("$state['observer_contrast'] ?? ''", method)
        self.assertIn("$state['observer_so_what'] ?? ''", method)
        self.assertIn("$state['observer_delta'] ?? ''", method)
        self.assertIn("$observer_candidate", method)
        self.assertIn("structured_recovery_candidate_is_relevant($candidate, $message)", method)

    def test_same_change_risk_question_family_is_rejected_as_repeat(self):
        start = SOURCE.index("private function question_is_repeated(")
        end = SOURCE.index("private function remember_question(", start)
        method = SOURCE[start:end]
        self.assertIn("$change_risk_question = preg_match", method)
        self.assertIn("$prior_change_risk = preg_match", method)
        self.assertIn("if ($change_risk_question && $prior_change_risk) return true;", method)

    def test_relational_warmth_and_concealment_has_grounded_question_recovery(self):
        self.assertIn("$warmth_without_honesty = preg_match", SOURCE)
        self.assertIn("What does keeping the ' . $relationship_noun . ' warm mean when something feels unspoken?", SOURCE)
        self.assertIn("This is a perspective question about the stated", SOURCE)

    def test_opening_rest_without_question_preserves_response_for_structural_completion(self):
        block_start = SOURCE.index("if (!$unit_complete && $rest && $question === '' && $prior_question === '' && empty($prior_questions))")
        block_end = SOURCE.index("$use_resource = !empty($decoded['use_resource']);", block_start)
        block = SOURCE[block_start:block_end]
        self.assertIn("$rest = false;", block)
        self.assertNotIn("return array();", block)
        self.assertIn("downstream", block)

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


    def test_provider_exhaustion_recovers_hurt_to_tone_and_hurt_heard_turns(self):
        start = SOURCE.index("private function recover_structured_state_composition(")
        end = SOURCE.index("private function normalize_composition(", start)
        method = SOURCE[start:end]
        self.assertIn("$hurt_tone_displacement = preg_match", method)
        self.assertIn("$hurt_heard_without_perfect_explanation = preg_match", method)
        self.assertIn("the conversation shifts to how you said them", method)
        self.assertIn("What part of the original hurt feels hardest to get across once the discussion turns to how the words were said?", method)
        self.assertIn("What would tell you that the hurt itself had been heard, even if the explanation were imperfect?", method)
        self.assertIn("$this->normalize_composition($local_draft, $state, $message, $resources, false)", method)


if __name__ == "__main__":
    unittest.main()

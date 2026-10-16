from pathlib import Path

SOURCE = Path("recovery/live-hrn-v05330/candidate/human-relational-navigator.php")


def test_candidate_advances_version_sequentially():
    source = SOURCE.read_text(encoding="utf-8")
    assert "Version: 0.5.332" in source
    assert "const VERSION = '0.5.332';" in source


def test_abstract_effort_overlook_template_is_rejected():
    source = SOURCE.read_text(encoding="utf-8")
    start = source.index("private function question_is_generic_or_compound")
    end = source.index("private function question_plane_violation", start)
    validator = source[start:end]
    assert "what part of that effort is easiest to overlook" in validator


def test_one_sided_effort_recovery_is_grounded_and_non_prescriptive():
    source = SOURCE.read_text(encoding="utf-8")
    start = source.index("private function structural_question_completion_safe")
    end = source.index("private function question_is_generic_or_compound", start)
    fallback = source[start:end]
    assert "$uneven_effort" in fallback
    assert "What happens between you when you are the one making the effort?" in fallback



def test_observed_contact_initiation_question_is_replaced_with_grounded_question():
    source = SOURCE.read_text(encoding="utf-8")
    validator_start = source.index("private function question_is_generic_or_compound")
    validator_end = source.index("private function question_plane_violation", validator_start)
    validator = source[validator_start:validator_end]
    assert "where does that pattern become visible beyond this particular moment" in validator
    assert "what do you notice about the pattern when you step back from this one exchange" in validator
    assert "What happens to the contact between you when you stop initiating it?" in source


def test_contact_initiation_and_silence_are_supported_by_bounded_recovery():
    source = SOURCE.read_text(encoding="utf-8")
    assert "initiates? contact|initiating contact|making plans" in source
    assert "You are usually the one who starts contact and makes plans." in source
    assert "a long silence when you do not" in source

def test_frozen_writer_boundary_remains_present():
    source = SOURCE.read_text(encoding="utf-8")
    assert "private function groq_compose" in source
    assert "private function structural_question_completion_safe" in source

def test_one_sided_effort_abstraction_is_rejected_only_in_matching_relational_context():
    source = SOURCE.read_text(encoding="utf-8")
    assert "private function one_sided_effort_response_violation" in source
    assert "distribution of tasks" in source
    assert "perceiving (?:their|your) participation" in source
    assert "private function one_sided_effort_recovery_candidate" in source


def test_one_sided_effort_recovery_is_inserted_before_structured_state_fallbacks():
    source = SOURCE.read_text(encoding="utf-8")
    start = source.index("private function recover_structured_state_composition")
    end = source.index("private function ", start + 30)
    recovery = source[start:end]
    assert "$one_sided_effort_candidate = $this->one_sided_effort_recovery_candidate($message);" in recovery
    assert "$one_sided_effort_candidate," in recovery


def test_effort_relevance_family_is_explicit():
    source = SOURCE.read_text(encoding="utf-8")
    assert "'effort_reciprocity' => array('effort','efforts','one-sided','support','reaching out','showing up')" in source


def test_provider_bridge_errors_keep_failure_diagnostics():
    source = SOURCE.read_text(encoding="utf-8")
    start = source.index("private function record_provider_bridge_failure")
    end = source.index("private function provider_bank_chat", start)
    failure_boundary = source[start:end]
    assert "$this->record_provider_bridge_failure($result, $operation);" in source
    assert "'provider_error_code' => $error_code" in failure_boundary
    assert "'provider_error_stage' => $stage" in failure_boundary
    assert "'failure_stage' => $stage" in failure_boundary
    assert "'provider_unavailable'" in failure_boundary
    assert "'provider_budget_exhausted'" in failure_boundary
    assert "private message must not be logged" not in failure_boundary

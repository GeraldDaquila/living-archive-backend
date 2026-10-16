from pathlib import Path

SOURCE = Path("recovery/live-hrn-v05330/candidate/human-relational-navigator.php")


def test_candidate_advances_version_sequentially():
    source = SOURCE.read_text(encoding="utf-8")
    assert "Version: 0.5.331" in source
    assert "const VERSION = '0.5.331';" in source


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


def test_frozen_writer_boundary_remains_present():
    source = SOURCE.read_text(encoding="utf-8")
    assert "private function groq_compose" in source
    assert "private function structural_question_completion_safe" in source

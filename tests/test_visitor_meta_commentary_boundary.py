"""Regression tests for visitor-facing meta-commentary leaks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_shared_visitor_boundary_rejects_guide_process_instructions():
    source = (ROOT / "general_guide_composition.py").read_text(encoding="utf-8")
    assert "the guide should (?:explain|answer|provide|first)" in source
    assert "the response should address" in source
    assert "the answer should (?:address|explain|include)" in source


def test_boundary_remains_shared_and_not_question_specific():
    source = (ROOT / "general_guide_composition.py").read_text(encoding="utf-8")
    assert "_INTERNAL_LANGUAGE = re.compile(" in source
    assert "def _parse_factory(" in source
    assert "general composition exposed internal implementation language" in source

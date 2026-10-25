import json
from pathlib import Path

from general_guide_gold_standards import resolve_exact_gold_standard

FIXTURE = Path(__file__).parent / "fixtures" / "general_guide_system_vs_separate_problems_gold_standard.json"


def test_system_concept_is_registered_as_user_approved_gold_standard():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    resolved = resolve_exact_gold_standard(fixture["query"])
    assert resolved is not None
    assert resolved["benchmark_id"] == fixture["benchmark_id"]
    assert resolved["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert resolved["expected_response"] == fixture["expected_response"]
    assert resolved["doorway_title"] == "Leadership Beyond Control: The Rise of Coherence-Based Governance"
    assert resolved["doorway_url"] == ""


def test_system_concept_gold_standard_preserves_three_paragraphs_and_fsd_boundary():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    answer = fixture["expected_response"]
    assert len([p for p in answer.split("\\n\\n") if p.strip()]) == 3
    assert "Not every cluster of problems is one system" in answer
    assert "should not replace the answer to the conceptual question" in answer

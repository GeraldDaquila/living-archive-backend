import json
from pathlib import Path

from general_guide_gold_standards import resolve_exact_gold_standard

FIXTURE = Path(__file__).parent / "fixtures" / "general_guide_complexity_and_uncertainty_gold_standard.json"


def test_complexity_uncertainty_question_resolves_to_its_own_gold_standard():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    resolved = resolve_exact_gold_standard(fixture["query"])
    assert resolved is not None
    assert resolved["benchmark_id"] == fixture["benchmark_id"]
    assert resolved["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert resolved["expected_response"] == fixture["expected_response"]
    assert "Accountability, trust, and repairing harm" not in resolved["expected_response"]


def test_complexity_uncertainty_standard_preserves_three_paragraphs_and_distinction():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    answer = fixture["expected_response"]
    assert len([p for p in answer.split("\n\n") if p.strip()]) == 3
    assert "Complexity arises" in answer
    assert "Uncertainty is the limit" in answer

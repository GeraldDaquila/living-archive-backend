import json
from pathlib import Path

from general_guide_gold_standards import resolve_exact_gold_standard

FIXTURE = Path(__file__).parent / "fixtures" / "general_guide_methods_comparison_gold_standard.json"


def test_method_comparison_is_registered_as_user_approved_gold_standard():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    resolved = resolve_exact_gold_standard(fixture["query"])
    assert resolved is not None
    assert resolved["benchmark_id"] == fixture["benchmark_id"]
    assert resolved["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert resolved["expected_response"] == fixture["expected_response"]
    assert resolved["doorway_title"] == "The Question Beneath the Questions"
    assert resolved["doorway_url"] == ""


def test_method_comparison_registry_answer_has_three_paragraphs_and_all_four_methods():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    answer = fixture["expected_response"]
    assert len([p for p in answer.split("\n\n") if p.strip()]) == 3
    for phrase in ("empirical inquiry", "systems analysis", "philosophy", "contemplative reflection"):
        assert phrase in answer.casefold()

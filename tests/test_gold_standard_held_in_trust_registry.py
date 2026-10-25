import json
from pathlib import Path

from general_guide_gold_standards import resolve_exact_gold_standard

FIXTURE = Path(__file__).parent / "fixtures" / "general_guide_held_in_trust_gold_standard.json"


def test_held_in_trust_answer_is_registered_as_user_approved():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    resolved = resolve_exact_gold_standard(fixture["query"])
    assert resolved is not None
    assert resolved["benchmark_id"] == fixture["benchmark_id"]
    assert resolved["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert resolved["expected_response"] == fixture["expected_response"]
    assert resolved["doorway_title"] == "Simulation No. 10 — The Trust Exchange"
    assert resolved["doorway_url"] == ""


def test_held_in_trust_gold_standard_has_three_paragraphs_and_core_concepts():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    answer = fixture["expected_response"]
    assert len([p for p in answer.split("\n\n") if p.strip()]) == 3
    for phrase in ("held in trust", "obligations", "misuse or neglect", "authority ends", "what is known"):
        assert phrase in answer.casefold()

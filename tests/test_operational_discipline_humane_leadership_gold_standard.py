import json
from pathlib import Path

from general_guide_composition import operational_discipline_humane_leadership_recovery
from general_guide_gold_standards import resolve_exact_gold_standard

REGISTRY = Path(__file__).resolve().parents[1] / "docs" / "qa" / "gold_standard_registry.json"
QUESTION = "What is the role of operational discipline in humane leadership?"


def test_operational_discipline_question_resolves_to_approved_gold_standard():
    record = resolve_exact_gold_standard(QUESTION)
    assert record is not None
    assert record["benchmark_id"] == "general-guide-operational-discipline-humane-leadership-gold-standard-2026-10-26"
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert len([p for p in record["expected_response"].split("\n\n") if p.strip()]) == 3


def test_operational_discipline_recovery_answers_the_question_in_three_paragraphs():
    response = operational_discipline_humane_leadership_recovery(QUESTION)
    assert response is not None
    paragraphs = [p for p in response.split("\n\n") if p.strip()]
    assert len(paragraphs) == 3
    assert "turning humane intentions into reliable actions" in paragraphs[0]
    assert "clear responsibilities" in paragraphs[1]
    assert "not rigid rule-following" in paragraphs[2]
    assert "Please try again shortly" not in response


def test_question_specific_recovery_does_not_claim_to_be_a_universal_fallback():
    assert operational_discipline_humane_leadership_recovery("What is humane leadership?") is None


def test_registry_contains_only_one_operational_discipline_benchmark():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    matches = [r for r in payload["records"] if r.get("query") == QUESTION]
    assert len(matches) == 1

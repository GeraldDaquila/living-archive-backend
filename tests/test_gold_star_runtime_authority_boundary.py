import json
from pathlib import Path
from general_guide_gold_standards import resolve_exact_gold_standard

def _records():
    return json.loads(Path("docs/qa/gold_standard_registry.json").read_text())["records"]

def test_current_user_approved_gold_standard_remains_runtime_eligible():
    record=next(r for r in _records() if r["status"]=="USER_APPROVED_GOLD_STANDARD" and r.get("expected_response"))
    assert resolve_exact_gold_standard(record["query"]) is not None

def test_frozen_reference_has_no_runtime_answer_authority():
    record=next(r for r in _records() if r["status"]=="FROZEN_REFERENCE_ONLY" and r.get("expected_response"))
    assert resolve_exact_gold_standard(record["query"]) is None


from general_guide_composition import (
    _requires_growth_within_limits_explanation,
    _growth_within_limits_recovery,
)

def test_growth_within_limits_recovery_answers_the_named_mechanism():
    question = "Why can growth become destructive when detached from ecological and social limits?"
    assert _requires_growth_within_limits_explanation(question)
    response = _growth_within_limits_recovery().casefold()
    for term in ("ecological", "social", "capacity", "overshoot"):
        assert term in response

def test_general_composition_bounds_provider_context_before_admission():
    source = Path("general_guide_composition.py").read_text(encoding="utf-8")
    assert "_evidence_payload(documents)[:6000]" in source
    assert 'user_content[:7000]' in source

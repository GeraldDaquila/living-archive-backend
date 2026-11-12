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


from general_guide_gold_standards import (
    find_cross_question_standard_response,
)
from gold_star_lessons import active_quality_contribution

LIVE_CALIBRATION_QUESTION = (
    "Why can growth become destructive when detached from ecological and social limits?"
)

def test_live_calibration_question_has_no_exact_gold_star_answer_authority():
    assert resolve_exact_gold_standard(LIVE_CALIBRATION_QUESTION) is None

def test_live_calibration_gold_star_guidance_cannot_carry_answer_authority():
    contribution = active_quality_contribution(LIVE_CALIBRATION_QUESTION)
    if contribution is not None:
        assert contribution["authority_mode"] == "structural_guidance_only"
        assert "response" not in contribution
        assert "expected_response" not in contribution
        assert "doorway" not in contribution

def test_intergenerational_gold_star_answer_is_rejected_for_live_calibration_question():
    record = next(
        r for r in _records()
        if r.get("benchmark_id") == "general-guide-intergenerational-stewardship-gold-standard-2026-10-25"
    )
    leak = find_cross_question_standard_response(
        LIVE_CALIBRATION_QUESTION,
        record["expected_response"],
    )
    assert leak is not None
    assert leak["benchmark_id"] == record["benchmark_id"]

def test_composer_keeps_active_quality_and_exact_answer_authority_as_separate_boundaries():
    source = Path("general_guide_composition.py").read_text(encoding="utf-8")
    assert 'authority_mode") != "structural_guidance_only"' in source
    assert "registered_standard = None if integrity_recovery else _registered_exact_gold_standard(question)" in source

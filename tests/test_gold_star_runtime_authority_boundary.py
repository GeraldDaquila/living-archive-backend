import json
from pathlib import Path
from general_guide_gold_standards import resolve_exact_gold_standard


def _records():
    return json.loads(Path("docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))["records"]


def test_current_user_approved_gold_standard_remains_runtime_eligible():
    record = next(
        r for r in _records()
        if r["status"] == "USER_APPROVED_GOLD_STANDARD" and r.get("expected_response")
    )
    assert resolve_exact_gold_standard(record["query"]) is not None


def test_frozen_reference_has_no_runtime_answer_authority():
    record = next(
        r for r in _records()
        if r["status"] == "FROZEN_REFERENCE_ONLY" and r.get("expected_response")
    )
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
    assert "user_content[:7000]" in source


from general_guide_gold_standards import find_cross_question_standard_response
from gold_star_lessons import active_quality_contribution

# This held-out phrasing is deliberately not an exact approved registry query.
# The exact growth-within-limits question is now an approved Gold Star and must
# retain its exact-answer authority rather than being treated as a negative case.
LIVE_CALIBRATION_QUESTION = (
    "Why does growth become destructive when it outruns ecological and social limits?"
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


def test_basic_inquiry_deterministic_recovery_uses_only_closed_eligible_gold_star_plans():
    source = Path("main.py").read_text(encoding="utf-8")
    start = source.index("def _basic_inquiry_round1_deterministic_response(")
    end = source.index("\ndef _guide_html_to_source_text(", start)
    function_source = source[start:end]
    assert "_deterministic_gold_star_contribution(query)" in function_source
    assert "_compose_deterministic_gold_star(" in function_source
    assert "if not _matched_orientation:" in function_source
    assert '"gold_star_deterministic_structural_fallback"' in function_source
    assert "gold_star_deterministic_application" in function_source
    # Raw lesson prose remains non-mutating. Transfer is performed only by the
    # closed plan renderer, never by appending discipline text to an answer.
    lessons = Path("gold_star_lessons.py").read_text(encoding="utf-8")
    assert "def deterministic_fallback_contribution(query: str)" in lessons
    assert "def apply_deterministic_fallback_guidance(query: str, response: str) -> str:" in lessons
    assert 'return str(response or "").strip()' in lessons
    renderer = Path("gold_star_deterministic_composition.py").read_text(encoding="utf-8")
    assert "_PLANS = {" in renderer
    assert "if plan is None:" in renderer
    assert 'if not all(term in discipline for term in plan["discipline_terms"]):' in renderer
    assert 'if not all(term in boundary for term in plan["boundary_terms"]):' in renderer

"""Tests for the system-wide three-paragraph Guide default and fragmented-knowledge recovery."""

from pathlib import Path

from general_guide_composition import (
    _fragmented_knowledge_recovery,
    _has_fragmented_knowledge_explanation,
    _requires_fragmented_knowledge_explanation,
    enforce_response_contracts,
)

ROOT = Path(__file__).resolve().parents[1]
QUERY = "How does fragmented knowledge impede wise action?"

SCREENSHOT_REGRESSION = (
    "A practical way to approach fragmented knowledge impede wise action is to define the outcome you want, "
    "identify the main constraint, and choose one step small enough to test. Before acting, consider who else "
    "is affected and what could go wrong. Check the result against the original goal and adjust rather than "
    "assuming the first attempt must be final."
)


def test_fragmented_knowledge_question_requires_explanation_not_planning_advice():
    assert _requires_fragmented_knowledge_explanation(QUERY)
    assert _requires_fragmented_knowledge_explanation(
        "Why does siloed information undermine wise decisions?"
    )
    assert not _requires_fragmented_knowledge_explanation(
        "How can I plan a small experiment?"
    )


def test_screenshot_style_generic_checklist_is_replaced_at_final_contract_boundary():
    result = enforce_response_contracts(QUERY, SCREENSHOT_REGRESSION)
    paragraphs = [p.strip() for p in result.split("\n\n") if p.strip()]
    assert len(paragraphs) == 3
    assert _has_fragmented_knowledge_explanation(result)
    assert paragraphs[0].startswith("Fragmented knowledge impedes wise action")
    assert "For example" in paragraphs[1]
    assert "what is known" in paragraphs[2]
    assert "choose one step small enough to test" not in result


def test_valid_three_paragraph_fragmented_knowledge_explanation_is_preserved():
    valid = _fragmented_knowledge_recovery()
    assert _has_fragmented_knowledge_explanation(valid)
    assert enforce_response_contracts(QUERY, valid) == valid


def test_general_guide_prompt_makes_three_paragraphs_the_default_without_conflicting_short_answer_rule():
    source = (ROOT / "general_guide_composition.py").read_text(encoding="utf-8")
    assert "A substantive explanatory or conceptual question defaults to three purposeful paragraphs" in source
    assert "For other substantive explanatory or conceptual answers, use three purposeful paragraphs by default" in source
    assert "For a substantive explanatory, conceptual, educational, social, or Archive-related question, present three connected, readable paragraphs by default" in source
    assert "For other explanatory or conceptual answers, use 2–4 purposeful paragraphs when that improves comprehension." not in source
    assert "a short conceptual question may need only two or three compact paragraphs" not in source

def test_final_visitor_boundary_uses_shared_gold_standard_recovery_instead_of_generic_apology():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    marker = "_systemwide_recovery = _sanitize_basic_inquiry_response("
    assert marker in source
    boundary_start = source.index(marker)
    boundary = source[boundary_start:boundary_start + 4000]
    assert "_compose_provider_exhaustion_recovery(query)" in boundary
    assert "len(_systemwide_paragraphs) >= 3" in boundary
    assert "authoritative_doorway = None" in boundary
    assert '"kind": "general_knowledge"' in boundary
    assert "I couldn’t produce a reliable answer to that question just now." in boundary

def test_default_composition_quality_gate_requires_substance_not_just_three_paragraphs():
    source = (ROOT / "general_guide_composition.py").read_text(encoding="utf-8")
    for requirement in (
        "COMPOSITION QUALITY GATE — mandatory for every substantive answer",
        'For a "how can" question, name the practical method or decision principle immediately',
        "Give each paragraph a different job",
        "Do not introduce the name of an Archive assessment, framework, governance instrument, or internal tool into the body of a general answer",
        "every sentence must answer the visitor's question",
    ):
        assert requirement in source


def test_default_composition_quality_gate_is_not_limited_to_stakeholder_question():
    source = (ROOT / "general_guide_composition.py").read_text(encoding="utf-8")
    prompt_start = source.index("_GENERAL_GUIDE_SYSTEM =")
    prompt_end = source.index("\n\ndef _normalize_space", prompt_start)
    prompt = source[prompt_start:prompt_end]
    assert "COMPOSITION QUALITY GATE — mandatory for every substantive answer" in prompt
    assert "A plausible thematic association is not enough" in prompt
    assert "not only named question classes" in prompt

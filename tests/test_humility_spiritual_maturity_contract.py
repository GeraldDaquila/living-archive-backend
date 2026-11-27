from pathlib import Path
import inspect
import json
import pytest

import general_guide_composition as composition
import gold_star_lessons
from provider_quota_control import estimate_input_tokens
from general_guide_composition import _parse_factory
from humility_spiritual_maturity_contract import (
    evaluate_humility_spiritual_maturity_response,
    is_humility_spiritual_maturity_question,
)


QUERY = "What is the relationship between humility and spiritual maturity?"
COMPLETE_ANSWER = (
    "Humility supports spiritual maturity because it keeps a person willing to learn, "
    "make an honest self-appraisal, accept correction, and remain open to others. "
    "Spiritual maturity is visible in lived conduct: responsibility, accountability, "
    "and care in relationships, rather than a status someone claims. Humility is not "
    "self-erasure, diminished self-worth, self-contempt, passivity, blind obedience, "
    "or automatic compliance; it does not mean surrendering appropriate boundaries. "
    "The relationship is conditional, not automatic. Humility alone does not guarantee maturity; it must be expressed in how a person acts."
)


def test_humility_relationship_question_is_narrowly_classified():
    assert is_humility_spiritual_maturity_question(QUERY)
    assert is_humility_spiritual_maturity_question(
        "How do humility and spiritual maturity relate to one another?"
    )
    assert not is_humility_spiritual_maturity_question("What does humility mean?")
    assert not is_humility_spiritual_maturity_question("What is spiritual maturity?")


def test_complete_humility_relationship_answer_passes_shared_contract():
    report = evaluate_humility_spiritual_maturity_response(QUERY, COMPLETE_ANSWER)
    assert report["applies"] is True
    assert report["passed"] is True
    assert report["missing"] == []


def test_humility_relationship_answer_must_preserve_learning_agency_and_boundaries():
    weak = (
        "Humility supports spiritual maturity because people learn from experience. "
        "Spiritual maturity is shown in daily conduct. Humility alone does not guarantee maturity."
    )
    report = evaluate_humility_spiritual_maturity_response(QUERY, weak)
    assert report["passed"] is False
    assert "preserves_appropriate_boundaries" in report["missing"]
    assert "not_passivity_or_automatic_compliance" in report["missing"]
    assert "not_self_erasure_or_self_contempt" in report["missing"]


def test_provider_prompt_and_admission_parser_share_the_humility_contract():
    parser_source = inspect.getsource(composition._parse_factory)
    assert "evaluate_humility_spiritual_maturity_response" in parser_source
    assert "humility/spiritual-maturity answer is incomplete" in parser_source
    system_message = composition._build_general_guide_system_message(QUERY)
    assert "HUMILITY AND SPIRITUAL MATURITY: Use three direct sentences." in system_message
    assert "honest self-appraisal" in system_message
    assert "blind obedience" in system_message


def test_humility_provider_prompt_keeps_headroom_under_groq_tpm_budget():
    quality = gold_star_lessons.active_quality_contribution(QUERY)
    assert quality and len(quality.get("candidates") or []) == 3
    messages = composition._build_general_guide_provider_messages(
        QUERY,
        "U" * 7000,
        has_gold_star_guidance=True,
        incomplete_knowledge_plan=composition.build_incomplete_knowledge_plan(QUERY),
        gold_star_quality_instruction=composition._build_gold_star_quality_instruction(quality),
    )

    assert len(messages[1]["content"]) == composition.GENERAL_GUIDE_PROVIDER_USER_CONTENT_MAX_CHARS
    # Keep at least 500 tokens of headroom below the configured 8k TPM ceiling.
    assert estimate_input_tokens(messages) + 750 <= 7500


def test_provider_parser_rejects_incomplete_humility_relationship_answer():
    parser = _parse_factory([], QUERY, None)
    weak = (
        "Humility and spiritual maturity are related. Humility helps people learn. "
        "Spiritual maturity is shown in daily conduct. Humility does not guarantee maturity."
    )
    with pytest.raises(ValueError, match="humility/spiritual-maturity answer is incomplete"):
        parser(json.dumps({
            "response": weak,
            "doorway_title": "",
            "response_shape": "explanatory",
        }))


def test_provider_parser_accepts_complete_humility_relationship_answer():
    parser = _parse_factory([], QUERY, None)
    parsed = parser(json.dumps({
        "response": COMPLETE_ANSWER,
        "doorway_title": "",
        "response_shape": "explanatory",
    }))
    assert parsed["response"] == COMPLETE_ANSWER


@pytest.mark.parametrize(
    "boundary_sentence",
    [
        "Humility is different from passivity, blind obedience, and automatic compliance.",
        "Humility is an active openness to learning rather than passivity, blind obedience, or automatic compliance.",
        "Humility does not entail passivity, blind obedience, or automatic compliance.",
        "Humility can remain open to correction without becoming passive or unquestioningly compliant.",
    ],
)
def test_humility_boundary_accepts_clear_semantic_paraphrases(boundary_sentence):
    answer = COMPLETE_ANSWER.replace(
        "Humility is not self-erasure, diminished self-worth, self-contempt, passivity, blind obedience, "
        "or automatic compliance; it does not mean surrendering appropriate boundaries.",
        "Humility is not self-erasure, diminished self-worth, or self-contempt; "
        + boundary_sentence
        + " It does not mean surrendering appropriate boundaries.",
    )
    report = evaluate_humility_spiritual_maturity_response(QUERY, answer)
    assert report["checks"]["not_passivity_or_automatic_compliance"] is True
    assert report["passed"] is True


def test_task_specific_humility_contract_is_authoritative_for_relational_synthesis():
    answer = (
        "Humility cultivates spiritual maturity, keeping a person teachable and open to correction. "
        "Learning requires honest self-appraisal and accepting correction or accountability. "
        "Spiritual maturity is lived conduct in actions and relationships, not claimed status. "
        "Humility is not self-erasure, diminished self-worth, or self-contempt. "
        "Humility is different from passivity, blind obedience, and automatic compliance. "
        "It does not mean surrendering appropriate boundaries. "
        "The relationship is conditional, not automatic. "
        "Humility alone does not guarantee maturity."
    )
    assert evaluate_humility_spiritual_maturity_response(QUERY, answer)["passed"] is True
    assert composition.has_conceptual_relationship_explanation(answer, QUERY) is True



@pytest.mark.parametrize(
    "boundary_sentence",
    [
        "Humility is not a loss of self-respect or a denial of one's worth.",
        "Humility is different from self-negation and self-abasement.",
        "Humility does not mean erasing oneself or abandoning self-respect.",
    ],
)
def test_humility_boundary_accepts_clear_self_erasure_paraphrases(boundary_sentence):
    answer = COMPLETE_ANSWER.replace(
        "Humility is not self-erasure, diminished self-worth, self-contempt, passivity, blind obedience, "
        "or automatic compliance; it does not mean surrendering appropriate boundaries.",
        boundary_sentence + " Humility is not passivity, blind obedience, or automatic compliance. "
        "It does not mean surrendering appropriate boundaries.",
    )
    report = evaluate_humility_spiritual_maturity_response(QUERY, answer)
    assert report["checks"]["not_self_erasure_or_self_contempt"] is True
    assert report["passed"] is True


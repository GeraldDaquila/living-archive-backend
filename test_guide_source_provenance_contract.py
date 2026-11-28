import pytest

from guide_source_provenance_contract import (
    evaluate_source_provenance_response,
    is_source_provenance_question,
)
from general_guide_composition import (
    _requires_fresh_provider_composition,
    apply_terminal_response_contract,
    enforce_response_contracts,
)


QUESTION = (
    "For a sentence that combines a direct quotation, a paraphrase, and an "
    "interpretation, how should the Guide make each layer traceable?"
)

PASSING = (
    "For a direct quotation, preserve the exact wording and identify the source "
    "document and page or section locator. For a paraphrase, restate the passage "
    "in your own words and preserve its scope, qualifications, modality, and "
    "conditions. For interpretation, identify it as the Guide's own analysis, "
    "name the claims it builds on, and explain the reasoning behind the inference. "
    "Mark each claim or clause separately, or split the sentence when boundaries "
    "are unclear. If the source or locator is unavailable and cannot be verified, "
    "disclose that limitation. Do not invent quotations or attribute the Guide's "
    "interpretation to the author."
)


def test_recognizes_mixed_provenance_question():
    assert is_source_provenance_question(QUESTION)


@pytest.mark.parametrize(
    "query",
    [
        "What is a quotation?",
        "How do I paraphrase a difficult paragraph?",
        "What is the difference between interpretation and inference?",
        "How do I cite a source in APA style?",
    ],
)
def test_unrelated_questions_do_not_activate_contract(query):
    assert not is_source_provenance_question(query)
    assert evaluate_source_provenance_response(query, "A general answer.") == {
        "applies": False,
        "passed": True,
        "missing": [],
    }


def test_complete_mixed_provenance_explanation_passes():
    report = evaluate_source_provenance_response(QUESTION, PASSING)
    assert report["applies"] is True
    assert report["passed"] is True
    assert report["missing"] == []


def test_labels_without_locators_or_inferential_bridge_fail():
    response = (
        'Put the quotation in quotation marks. Say "in other words" before the '
        "paraphrase. Add an interpretation tag and a citation."
    )
    report = evaluate_source_provenance_response(QUESTION, response)
    assert report["applies"] is True
    assert report["passed"] is False
    assert "source_locator" in report["missing"]
    assert "inferential_bridge" in report["missing"]
    assert "unavailable_source_disclosure" in report["missing"]


def test_interpretation_must_not_be_misattributed():
    response = PASSING.replace(
        "Do not invent quotations or attribute the Guide's interpretation to the author.",
        "Invent quotations and attribute the Guide's interpretation to the author.",
    )
    report = evaluate_source_provenance_response(QUESTION, response)
    assert report["passed"] is False
    assert "no_false_attribution" in report["missing"]



OFF_TOPIC_GOVERNANCE_RESPONSE = (
    "Start by defining the outcome the change must achieve, the responsibilities that cannot be lost, "
    "and the people who will live with its consequences. Then compare realistic options against those "
    "requirements rather than assuming the proposed course is the only one.\\n\\n"
    "Examine what each option makes possible, what it may damage, who bears the costs, and what evidence "
    "would justify changing direction. Include the knowledge of people affected by the decision, especially "
    "where they will carry consequences they did not choose.\\n\\n"
    "Choose deliberately, make the reasoning and limits visible, and remain accountable for what follows."
)


def test_mixed_provenance_question_bypasses_composition_cache():
    assert _requires_fresh_provider_composition(QUESTION)


def test_off_topic_governance_response_is_rejected_by_final_contract():
    with pytest.raises(
        RuntimeError,
        match="Final visitor response failed the mixed-source provenance contract",
    ):
        enforce_response_contracts(QUESTION, OFF_TOPIC_GOVERNANCE_RESPONSE)


def test_off_topic_response_cannot_escape_through_terminal_payload_contract():
    with pytest.raises(
        RuntimeError,
        match="Final visitor response failed the mixed-source provenance contract",
    ):
        apply_terminal_response_contract(
            QUESTION,
            {"response": OFF_TOPIC_GOVERNANCE_RESPONSE, "intent": "TOPICAL_INQUIRY"},
        )


def test_compliant_provenance_response_survives_final_contract():
    assert enforce_response_contracts(QUESTION, PASSING) == PASSING

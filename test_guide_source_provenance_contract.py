import pytest

from guide_source_provenance_contract import (
    evaluate_source_provenance_response,
    is_source_provenance_question,
)
from deterministic_answer_recovery import (
    compose_recovery,
    has_registered_recovery,
    registered_recovery_recommendation,
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
    "disclose that limitation. A citation should support only the claim it actually establishes. "
    "Do not invent quotations or attribute the Guide's "
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
        "A citation should support only the claim it actually establishes. Do not invent quotations or attribute the Guide's interpretation to the author.",
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



def test_provider_exhaustion_uses_task_specific_provenance_recovery():
    response = compose_recovery(QUESTION)
    report = evaluate_source_provenance_response(QUESTION, response)
    assert report["applies"] is True
    assert report["passed"] is True
    assert "compare realistic options" not in response.casefold()
    assert "people who will live with its consequences" not in response.casefold()


def test_provenance_recovery_is_registered_with_a_verified_relevant_doorway():
    assert has_registered_recovery(QUESTION)
    assert registered_recovery_recommendation(QUESTION) == {
        "title": "Levels of Claim",
        "url": "https://geralddaquila.com/levels-of-claim/",
        "rationale": (
            "This published Living Archive method distinguishes observation, interpretation, explanation, "
            "and other levels of claim, and explains why they should not be presented with equal evidential "
            "weight. It is a directly relevant continuation for keeping source-derived material distinct "
            "from the Guide's own interpretation; it is not a source citation for any particular quotation."
        ),
    }


def test_provider_exhaustion_recovery_preserves_real_paragraph_breaks():
    response = compose_recovery(QUESTION)
    assert response.count("\n\n") == 2
    assert "\\n\\n" not in response
    assert evaluate_source_provenance_response(QUESTION, response)["passed"] is True


def test_citation_must_not_launder_interpretation_as_source_fact():
    response = PASSING.replace(
        "A citation should support only the claim it actually establishes. ",
        "A single citation supports every claim in the sentence, including the Guide's interpretation. ",
    )
    report = evaluate_source_provenance_response(QUESTION, response)
    assert report["passed"] is False
    assert "citation_scope_integrity" in report["missing"]

"""Final visitor-boundary regressions for mixed-source provenance."""

import pytest

from general_guide_composition import (
    _requires_fresh_provider_composition,
    apply_terminal_response_contract,
    enforce_response_contracts,
)
from guide_source_provenance_contract import evaluate_source_provenance_response


QUESTION = (
    "For a sentence that combines a direct quotation, a paraphrase, "
    "and an interpretation, how should the Guide make each layer traceable?"
)

OFF_TOPIC_VISITOR_RESPONSE = (
    "Start by defining the outcome the change must achieve, the responsibilities that cannot be lost, "
    "and the people who will live with its consequences. Then compare realistic options against those "
    "requirements rather than assuming the proposed course is the only one.\n\n"
    "Examine what each option makes possible, what it may damage, who bears the costs, and what evidence "
    "would justify changing direction. Include the knowledge of people affected by the decision, especially "
    "where they will carry consequences they did not choose.\n\n"
    "Choose deliberately, make the reasoning and limits visible, and remain accountable for what follows."
)

VALID_VISITOR_RESPONSE = (
    "To make all three layers traceable, annotate them at the smallest practical claim-bearing span, "
    "rather than attaching one citation to an entire sentence. For a direct quotation, preserve the exact "
    "wording, place it in quotation marks, and identify the author or work and the precise page, section, "
    "paragraph, timestamp, or other locator available in the source; mark omissions, insertions, and "
    "editorial emphasis. For a paraphrase, use the Guide's own words and cite the exact passage it restates, "
    "preserving the source's scope, qualifications, conditions, and degree of certainty. For interpretation, "
    "signal that it is the Guide's analysis, identify the quoted or paraphrased claims it builds on, and "
    "explain the reasoning that connects them. If the three layers are interwoven, mark each clause or span "
    "separately—or split the sentence if the boundaries are unclear. A citation should support only the claim "
    "it actually establishes; it must not lend the source's authority to the Guide's interpretation. If the "
    "source text or locator is unavailable, disclose that limitation rather than inventing a quotation or "
    "source detail. The reader should be able to verify what the source says, see what the Guide restates, "
    "and understand where the Guide's inference begins."
)


def test_mixed_source_question_forces_fresh_provider_composition():
    assert _requires_fresh_provider_composition(QUESTION)


def test_generic_governance_answer_is_rejected_at_final_response_contract():
    report = evaluate_source_provenance_response(QUESTION, OFF_TOPIC_VISITOR_RESPONSE)
    assert report["applies"] is True
    assert report["passed"] is False
    with pytest.raises(RuntimeError, match="Final visitor response failed the mixed-source provenance contract"):
        enforce_response_contracts(QUESTION, OFF_TOPIC_VISITOR_RESPONSE)


def test_terminal_payload_cannot_reintroduce_off_topic_answer():
    payload = {"response": OFF_TOPIC_VISITOR_RESPONSE, "intent": "TOPICAL_INQUIRY"}
    with pytest.raises(RuntimeError, match="Final visitor response failed the mixed-source provenance contract"):
        apply_terminal_response_contract(QUESTION, payload)


def test_complete_claim_level_provenance_answer_passes_final_boundary():
    report = evaluate_source_provenance_response(QUESTION, VALID_VISITOR_RESPONSE)
    assert report["applies"] is True
    assert report["passed"] is True
    assert enforce_response_contracts(QUESTION, VALID_VISITOR_RESPONSE) == VALID_VISITOR_RESPONSE


def test_ordinary_conceptual_question_is_not_forced_into_provenance_template():
    ordinary_question = "What is the relationship between trust and accountability?"
    ordinary_answer = "Trust supports cooperation, while accountability makes commitments answerable."
    report = evaluate_source_provenance_response(ordinary_question, ordinary_answer)
    assert report["applies"] is False
    assert enforce_response_contracts(ordinary_question, ordinary_answer) == ordinary_answer

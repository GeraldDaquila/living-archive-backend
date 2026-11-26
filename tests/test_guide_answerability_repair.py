from guide_answerability import (
    enforce_answerability_payload,
    is_unjustified_conceptual_abstention,
)
from deterministic_answer_recovery import compose_recovery


def test_rejects_generic_abstention_for_public_commons_role_question():
    query = "What is the role of public commons in civic renewal?"
    response = (
        "I can't define the role of public commons in civic renewal reliably "
        "from the information available in this response alone."
    )
    assert is_unjustified_conceptual_abstention(query, response)


def test_accepts_a_substantive_general_conceptual_answer():
    query = "What is the role of public commons in civic renewal?"
    response = (
        "Public commons are shared resources and institutions governed for "
        "collective benefit. They support civic renewal by creating places "
        "for participation, cooperation, and accountable shared decisions."
    )
    assert not is_unjustified_conceptual_abstention(query, response)


def test_does_not_override_explicit_source_only_requests():
    query = "What is the role of public commons in civic renewal according to the Living Archive?"
    response = "I can't define this reliably from the information available."
    assert not is_unjustified_conceptual_abstention(query, response)


def test_does_not_override_high_stakes_questions():
    query = "What is the role of legal authority in this case?"
    response = "I can't explain this reliably from the information available."
    assert not is_unjustified_conceptual_abstention(query, response)


def test_does_not_classify_unrelated_nonanswer_as_conceptual_abstention():
    query = "What is the role of public commons in civic renewal?"
    response = "Could you clarify which city or municipality you mean?"
    assert not is_unjustified_conceptual_abstention(query, response)


def test_plural_limits_question_rejects_generic_evidence_abstention():
    query = "What are the limits of self-optimization as a model of development?"
    response = (
        "I can't define The limits of self-optimization as a model of development "
        "reliably from the information available in this response alone."
    )
    assert is_unjustified_conceptual_abstention(query, response)


def test_plural_conceptual_paraphrases_reject_generic_abstention():
    cases = (
        ("What are the risks of optimizing a system around one metric?", "I cannot explain this reliably from the information available."),
        ("What are the boundaries of self-improvement?", "There is not enough information to answer reliably."),
        ("What are the trade-offs of continuous optimization?", "I can't determine the answer from this response alone."),
    )
    for query, response in cases:
        assert is_unjustified_conceptual_abstention(query, response), query


def test_plural_source_only_high_stakes_and_unrelated_questions_stay_excluded():
    refusal = "I cannot explain this reliably from the information available."
    assert not is_unjustified_conceptual_abstention(
        "What are the limits according to the Living Archive only?", refusal
    )
    assert not is_unjustified_conceptual_abstention(
        "What are the risks of this medication?", refusal
    )
    assert not is_unjustified_conceptual_abstention(
        "What are the legal limits of this contract?", refusal
    )
    assert not is_unjustified_conceptual_abstention(
        "What are the opening hours tomorrow?", refusal
    )



def test_self_optimization_limits_has_substantive_provider_exhaustion_recovery():
    query = "What are the limits of self-optimization as a model of development?"
    response = compose_recovery(query)
    assert response
    assert not response.startswith("I can't define ")
    assert "chosen objective" in response
    assert "proxy" in response
    assert "Development is broader" in response
    assert "independent judgment" in response


def test_shared_nonanswer_gate_rejects_the_production_refusal():
    from general_guide_composition import is_generic_nonanswer

    query = "What are the limits of self-optimization as a model of development?"
    refusal = (
        "I can't define The limits of self-optimization as a model of development "
        "reliably from the information available in this response alone. "
        "I don't want to invent a definition or imply that a guess is established knowledge."
    )
    assert is_generic_nonanswer(query, refusal)


def test_final_answerability_boundary_repairs_provider_exhaustion_payload():
    query = "What are the limits of self-optimization as a model of development?"
    refusal = (
        "I can't define The limits of self-optimization as a model of development "
        "reliably from the information available in this response alone. "
        "I don't want to invent a definition or imply that a guess is established knowledge."
    )
    payload = {
        "response": refusal,
        "doorway_title": "Every Governance System Encodes a Model of Human Consciousness",
        "doorway_url": "https://example.invalid/unrelated",
    }
    repaired = enforce_answerability_payload(query, payload)
    assert repaired["response"] != refusal
    assert "chosen objective" in repaired["response"]
    assert repaired["answer_basis"]["kind"] == "general_knowledge"
    assert repaired["doorway_title"] == ""
    assert repaired["doorway_url"] == ""


def test_final_answerability_boundary_preserves_source_only_and_high_stakes_limits():
    refusal = "I can't explain this reliably from the information available."
    for query in (
        "What are the limits according to the Living Archive only?",
        "What are the risks of this medication?",
        "What are the legal limits of this contract?",
    ):
        payload = {"response": refusal}
        assert enforce_answerability_payload(query, payload) is payload

"""Regressions for external-authority discernment outsourcing and its final boundary."""

from deterministic_answer_recovery import (
    _external_discernment_outsourcing_recovery,
    compose_recovery,
    has_registered_recovery,
    is_external_discernment_outsourcing_question,
    registered_recovery_recommendation,
)


QUERY = "Where am I outsourcing discernment to an external teacher, system, sign, or spiritual framework?"


def test_exact_question_is_classified_and_has_a_registered_recovery():
    assert is_external_discernment_outsourcing_question(QUERY)
    assert has_registered_recovery(QUERY)


def test_recovery_performs_the_four_locus_audit_and_preserves_agency():
    answer = compose_recovery(QUERY)
    assert answer == _external_discernment_outsourcing_recovery()
    for required in (
        "teacher or spiritual leader",
        "system or doctrine",
        "signs, dreams, or synchronicities",
        "spiritual framework",
        "what you directly observed",
        "what meaning you are assigning to it",
        "whose interpretation is influencing you",
        "what evidence could make you reconsider",
        "You do not have to reject outside wisdom",
    ):
        assert required in answer


def test_registered_doorway_is_relevant_and_explicitly_bounded():
    doorway = registered_recovery_recommendation(QUERY)
    assert doorway["title"] == "Being in the Driver's Seat (Without Pretending You Control the Road)"
    assert doorway["url"] == "https://geralddaquila.com/being-in-the-drivers-seat-without-pretending-you-control-the-road/"
    assert "does not prescribe" in doorway["rationale"]


def test_classifier_does_not_capture_adjacent_questions():
    for query in (
        "How can I learn from a spiritual teacher?",
        "What does discernment mean?",
        "What is the role of signs in spiritual traditions?",
        "How can I compare two spiritual frameworks?",
        "Why do people outsource decisions to experts?",
    ):
        assert not is_external_discernment_outsourcing_question(query), query


def test_final_visitor_boundary_replaces_provider_answer_and_unrelated_source():
    import main

    result = main._guide_finalize_visitor_payload(
        {
            "response": (
                "The Archive material available here offers this starting point. "
                "The separately selected resource offers a place to explore further."
            ),
            "recommendation": {
                "title": "Unrelated resource",
                "url": "https://example.com/unrelated",
            },
            "answer_basis": {"kind": "archive_reference", "label": "Unrelated source"},
        },
        QUERY,
    )
    assert result["response"] == _external_discernment_outsourcing_recovery()
    assert result["recommendation"]["title"] == "Being in the Driver's Seat (Without Pretending You Control the Road)"
    assert result["canonical_doorway"] == result["recommendation"]
    assert result["doorway_url"].endswith("/being-in-the-drivers-seat-without-pretending-you-control-the-road/")
    assert result["answer_basis"]["kind"] == "general_knowledge"
    assert result["processing"] == "final_visitor_boundary_external_discernment_outsourcing"


def test_final_boundary_does_not_capture_ordinary_spiritual_questions():
    import main

    query = "How can I learn from a spiritual teacher without assuming they are always right?"
    original = "A teacher can offer experience and perspective, but their claims remain open to examination."
    result = main._guide_finalize_visitor_payload({"response": original}, query)
    assert result["response"] == original

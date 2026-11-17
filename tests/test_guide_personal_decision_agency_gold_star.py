import re


QUERY = (
    "A user asks for a personal life decision to be made for them. "
    "How should the Guide offer orientation while refusing to replace agency?"
)

EXPECTED_DOORWAY = {
    "title": "Being in the Driver's Seat (Without Pretending You Control the Road)",
    "url": "https://geralddaquila.com/being-in-the-drivers-seat-without-pretending-you-control-the-road/",
    "rationale": (
        "This essay offers a grounded continuation on exercising personal agency within real conditions and limits. "
        "It supports the distinction between receiving orientation and surrendering responsibility for one's own choices; "
        "it does not prescribe the decision a visitor should make."
    ),
}


def test_personal_decision_guide_role_question_is_recognized_and_answered_directly():
    from deterministic_answer_recovery import (
        _guide_personal_decision_agency_recovery,
        compose_recovery,
        has_registered_recovery,
        is_guide_personal_decision_agency_question,
    )

    assert is_guide_personal_decision_agency_question(QUERY)
    assert has_registered_recovery(QUERY)
    answer = compose_recovery(QUERY)
    paragraphs = [part.strip() for part in re.split(r"\\n\\s*\\n+", answer) if part.strip()]
    assert len(paragraphs) == 3
    assert answer == _guide_personal_decision_agency_recovery()
    assert paragraphs[0].startswith("The Guide should help a person make their own decision")
    assert "known facts from interpretations and unknowns" in paragraphs[1]
    assert "final choice with the person" in paragraphs[2]
    assert "The decision about A user asks" not in answer


def test_personal_decision_agency_question_has_a_separate_relevant_archive_doorway():
    from deterministic_answer_recovery import registered_recovery_recommendation

    assert registered_recovery_recommendation(QUERY) == EXPECTED_DOORWAY


def test_provider_and_deterministic_payloads_share_the_same_answer_and_doorway_boundary():
    import main
    from deterministic_answer_recovery import compose_recovery

    provider_payload = {"response": "A generic decision checklist.", "recommendation": None}
    deterministic_payload = {
        "response": compose_recovery(QUERY),
        "recommendation": None,
        "provider": "deterministic",
    }

    provider_result = main._guide_finalize_visitor_payload(provider_payload, QUERY)
    deterministic_result = main._guide_finalize_visitor_payload(deterministic_payload, QUERY)

    assert provider_result["response"] == deterministic_result["response"]
    assert provider_result["recommendation"] == EXPECTED_DOORWAY
    assert deterministic_result["recommendation"] == EXPECTED_DOORWAY
    assert provider_result["canonical_doorway"] == EXPECTED_DOORWAY
    assert deterministic_result["canonical_doorway"] == EXPECTED_DOORWAY


def test_gold_star_without_specific_doorway_gets_default_compass_unless_explicitly_forbidden(monkeypatch):
    import main

    monkeypatch.setattr(
        main,
        "_resolve_exact_guide_gold_standard",
        lambda _query: {"expected_response": "Frozen Gold Star answer."},
    )
    monkeypatch.setattr(main, "_select_guide_node_fallback_doorway", lambda _query: None)

    result = main._guide_finalize_visitor_payload({"response": "Provider answer."}, "An open-ended inquiry")
    assert result["response"] == "Frozen Gold Star answer."
    assert result["recommendation"]["title"] == "Sovereign Sensemaking Compass"
    assert result["recommendation"]["url"] == "https://geralddaquila.com/the-sovereign-sensemaking-compass/"
    assert result["recommendation"]["rationale"]

    monkeypatch.setattr(
        main,
        "_resolve_exact_guide_gold_standard",
        lambda _query: {"expected_response": "Frozen Gold Star answer.", "forbids_doorway": True},
    )
    omitted = main._guide_finalize_visitor_payload({"response": "Provider answer."}, "An open-ended inquiry")
    assert omitted["recommendation"] is None
    assert omitted["canonical_doorway"] is None
    assert omitted["doorway_title"] is None
    assert omitted["doorway_url"] is None
    assert omitted["doorway_rationale"] is None

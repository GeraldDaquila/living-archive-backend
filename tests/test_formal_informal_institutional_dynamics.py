"""Regression tests for formal/informal institutional dynamics and canonical navigation."""

import general_guide_composition as composition
import main


QUERY = (
    "How should the Guide compare formal institutional rules with informal norms "
    "when explaining why an organization behaves as it does?"
)


def test_question_enters_bounded_formal_informal_institutional_contract():
    assert composition._requires_formal_informal_institutional_dynamics(QUERY)
    assert main._select_verified_doorway_conceptual_family(QUERY) == (
        "formal_informal_institutional_dynamics"
    )


def test_classifier_does_not_capture_unrelated_or_single_layer_questions():
    assert not composition._requires_formal_informal_institutional_dynamics(
        "What are the formal rules for submitting an expense report?"
    )
    assert not composition._requires_formal_informal_institutional_dynamics(
        "How do informal norms shape friendships?"
    )
    assert not composition._requires_formal_informal_institutional_dynamics(
        "Why does an organization behave as it does?"
    )


def test_recovery_explains_distinction_interaction_and_diagnostic_method():
    answer = composition._formal_informal_institutional_dynamics_recovery()
    assert composition._has_formal_informal_institutional_dynamics_explanation(answer)
    assert len(answer.split("\\n\\n")) == 3
    assert "official roles" in answer
    assert "social influence" in answer
    assert "selectively" in answer
    assert "observed everyday practice" in answer
    assert "not sufficient to determine why" in answer


def test_final_visitor_boundary_repairs_generic_or_abstaining_answer_and_emits_doorway():
    result = main._guide_finalize_visitor_payload(
        {
            "response": (
                "A sound comparison would name the options and compare them on "
                "the same dimensions, then state what remains uncertain."
            ),
            "recommendation": None,
            "canonical_doorway": None,
        },
        QUERY,
    )
    assert result["processing"] == (
        "final_visitor_boundary_formal_informal_institutional_dynamics"
    )
    assert composition._has_formal_informal_institutional_dynamics_explanation(
        result["response"]
    )
    expected = {
        "title": "Institutional Consciousness",
        "url": "https://geralddaquila.com/institutional-consciousness/",
    }
    assert result["recommendation"]["title"] == expected["title"]
    assert result["recommendation"]["url"] == expected["url"]
    assert result["canonical_doorway"] == result["recommendation"]
    assert result["doorway_title"] == expected["title"]
    assert result["doorway_url"] == expected["url"]
    assert "does not diagnose this particular organization" in (
        result["doorway_rationale"] or ""
    )


def test_adequate_provider_answer_is_preserved_but_doorway_is_still_enforced():
    answer = composition._formal_informal_institutional_dynamics_recovery()
    result = main._guide_finalize_visitor_payload(
        {"response": answer, "recommendation": None},
        QUERY,
    )
    assert result["response"] == answer
    assert result["doorway_title"] == "Institutional Consciousness"
    assert result["recommendation"]["url"] == (
        "https://geralddaquila.com/institutional-consciousness/"
    )


def test_unrelated_question_is_not_rewritten_by_institutional_contract():
    query = "How should a team prepare for a difficult project deadline?"
    payload = {"response": "Keep the scope clear and review progress regularly."}
    result = main._guide_finalize_visitor_payload(payload, query)
    assert result == payload

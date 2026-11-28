"""Regression tests for the Guide's context-sensitive Archive claim-review continuation."""

import json
from pathlib import Path

import general_guide_composition as composition


ROOT = Path(__file__).resolve().parent
QUERY = (
    "A visitor wants proof that the Archive's cosmology is true. "
    "How should the Guide distinguish coherence, usefulness, evidence, "
    "and metaphysical commitment?"
)
BASE_RESPONSE = (
    "The Guide should keep three layers distinct. A direct Archive claim is "
    "something a particular text actually says or clearly supports, and it "
    "should remain traceable to that source. A cross-source synthesis is "
    "different: it draws a relationship, pattern, or implication across more "
    "than one Archive resource. It can be useful precisely because it connects "
    "materials, but it should be presented as the Guide's synthesis rather "
    "than as the statement of any single text.\n\n"
    "A third layer is orientation. The Guide may frame a question, identify a "
    "tension, or suggest a way of looking without presenting that framing as "
    "evidence from the Archive. This matters especially in a Living Archive: "
    "its purpose is not to flatten different voices into one authoritative "
    "conclusion, but to hold ideas in relationship without losing where they "
    "came from. Keeping the layers visible lets a visitor see what is being "
    "reported, what is being inferred, and what is being offered as a way to "
    "continue thinking.\n\n"
    "The practical discipline is therefore simple: stay close to the source "
    "when saying what the Archive says; name synthesis when the Guide is "
    "connecting materials; and keep orientation visibly separate from both. "
    "Then the Guide can add intelligibility without borrowing authority it "
    "has not earned. The distinction protects the integrity of the Archive "
    "while preserving the freedom to notice relationships that no single "
    "text, on its own, could show."
)


def test_archive_cosmology_evidence_question_gets_one_actionable_in_guide_continuation():
    result = composition.enforce_response_contracts(QUERY, BASE_RESPONSE)

    assert result.startswith(BASE_RESPONSE)
    assert result.count("Put this distinction to work") == 1
    assert "source directly establishes" in result
    assert "multiple sources support as synthesis" in result
    assert "interpretation or metaphysical commitment" in result
    assert result.endswith(
        "Which specific claim from the Living Archive would you like to examine first?"
    )


def test_explicit_no_followup_request_suppresses_contextual_continuation():
    query = QUERY + " Please do not ask a follow-up question or show a link."
    result = composition.enforce_response_contracts(query, BASE_RESPONSE)

    assert result == BASE_RESPONSE
    assert "Put this distinction to work" not in result


def test_no_archive_cosmology_evidence_frame_means_no_forced_continuation():
    for query in (
        "Can evidence prove cosmology true?",
        "How should the Archive distinguish evidence from interpretation?",
        "What makes a coherent worldview useful?",
    ):
        result = composition.enforce_response_contracts(query, BASE_RESPONSE)
        assert result == BASE_RESPONSE, query


def test_existing_relevant_claim_examination_question_is_not_duplicated():
    response = (
        BASE_RESPONSE
        + "\n\nWhich source claim would you like to examine first?"
    )
    result = composition.enforce_response_contracts(QUERY, response)

    assert result == response
    assert result.count("?") == 1


def test_existing_guide_reply_surface_renders_only_for_a_conversational_invitation():
    controller = (
        ROOT.parent
        / "wordpress/living-archive-answer-doorway-standard/assets/guide-controller-v489.329.js"
    ).read_text(encoding="utf-8")

    assert "function renderOrdinaryFollowupPanel(response)" in controller
    assert "var invitesReply = /\\?\\s*" in controller
    assert "renderOrdinaryFollowupPanel(data.response)" in controller
    assert "submitOrdinaryFollowup(panel, input, button, status)" in controller


def test_corrected_successor_is_registered_as_standalone_gold_star_only():
    registry = json.loads(
        (ROOT.parent / "docs/qa/gold_standard_registry.json").read_text(encoding="utf-8")
    )
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-archive-cosmology-epistemic-discernment-2026-11-28"
    )

    capabilities = record["gold_star_capabilities"]
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["runtime_transfer"] is False
    assert capabilities["standalone_response_quality_exemplar"] is True
    assert capabilities["exact_answer_authority"] is False
    assert capabilities["active_quality_contributor"] is False
    assert capabilities["deterministic_fallback_eligible"] is False
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["expected_doorway"] is None
    assert record["expected_response"].endswith(
        "Which specific claim from the Living Archive would you like to examine first?"
    )


def test_existing_continuation_heading_without_question_keeps_reply_trigger():
    response = (
        BASE_RESPONSE
        + "\n\n**Put this distinction to work**\n\n"
        + "We can examine source support, cross-source synthesis, and interpretation."
    )
    result = composition.enforce_response_contracts(QUERY, response)

    assert result.count("Put this distinction to work") == 1
    assert result.endswith(
        "Which specific claim from the Living Archive would you like to examine first?"
    )


def test_terminal_payload_contract_reapplies_doorway_after_response_floor_and_before_json_serialization():
    payload = {"response": BASE_RESPONSE, "answer": BASE_RESPONSE}
    result = composition.apply_terminal_response_contract(QUERY, payload)

    assert result is not payload
    assert payload["response"] == BASE_RESPONSE
    assert result["response"].startswith(BASE_RESPONSE)
    assert result["response"].count("Put this distinction to work") == 1
    assert result["answer"] == result["response"]

    # The final ASGI sender must reapply the shared decision after the terminal
    # response floor, not merely trust the earlier composition-stage result.
    main_source = (ROOT.parent / "main.py").read_text(encoding="utf-8")
    terminal_gate = main_source.rfind("# Final semantic/integrity gate:")
    floor = main_source.index("apply_response_floor_boundary(", terminal_gate)
    continuation = main_source.index(
        "general_guide_composition.apply_terminal_response_contract(", floor
    )
    serialization = main_source.index("encoded = json.dumps(", continuation)
    assert terminal_gate < floor < continuation < serialization


def test_terminal_payload_contract_preserves_explicit_no_handoff_and_safety():
    no_handoff = {
        "response": BASE_RESPONSE,
        "navigation_suppressed_by_task_contract": True,
    }
    safety = {
        "response": BASE_RESPONSE,
        "intent": "SAFETY_CONVERSATION",
    }
    assert composition.apply_terminal_response_contract(QUERY, no_handoff) is no_handoff
    assert composition.apply_terminal_response_contract(QUERY, safety) is safety

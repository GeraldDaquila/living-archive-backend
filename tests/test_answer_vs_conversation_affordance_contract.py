"""The canonical resource doorway and conversational reply panel are independent."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_canonical_resource_and_conversation_affordances_are_explicitly_distinct():
    spec = _read("docs/architecture/LIVING_ARCHIVE_ANSWER_DOORWAY_STANDARD.md")
    assert "Canonical resource doorway and conversational continuation are separate affordances" in spec
    assert "They are independent and may coexist" in spec
    assert "The reply panel is not a doorway" in spec
    assert "At most one canonical resource doorway" in spec


def test_live_guide_controller_has_independent_renderers_and_can_render_both():
    controller = _read(
        "wordpress/living-archive-answer-doorway-standard/assets/guide-controller-v489.332.js"
    )
    resource_start = controller.index("function renderAuthoritativeRecommendation(data)")
    reply_start = controller.index("function renderOrdinaryFollowupPanel(response)")
    assert resource_start < reply_start

    resource_renderer = controller[resource_start:reply_start]
    reply_end = controller.find("\nfunction ", reply_start + 10)
    reply_renderer = controller[reply_start:reply_end]

    assert "archive-recommendation" in resource_renderer
    assert "archive-inline-recommendation" in resource_renderer
    assert "renderOrdinaryFollowupPanel(" not in resource_renderer
    assert "archive-ordinary-followup" in reply_renderer
    assert "archive-recommendation" not in reply_renderer
    assert "invitesReply" in reply_renderer

    # The ordinary response path invokes both renderers independently, not as
    # mutually exclusive branches. A selected resource and reply invitation
    # can therefore coexist in the same visitor response.
    response_path = controller[controller.index("guideConversationHistory.push({", controller.index("renderOrdinaryFollowupPanel(data.response)") - 1200):]
    assert "renderAuthoritativeRecommendation(data);" in response_path
    assert "renderOrdinaryFollowupPanel(data.response);" in response_path


def test_backend_selection_contract_distinguishes_no_match_from_failure_and_refusal():
    selection_tests = _read("tests/test_guide_doorway_selection_evidence_state.py")
    assert "NO_RELEVANT_DESTINATION_AFTER_BOUNDED_SEARCH" in selection_tests
    assert "RETRIEVAL_OR_VERIFICATION_FAILURE" in selection_tests
    assert "not certified as an intentional omission" in selection_tests
    assert "AUTHORIZED_OMISSION" in selection_tests
    assert "explicit_visitor_refusal" in selection_tests


def test_cosmology_specific_omission_does_not_invent_a_resource_destination():
    cosmology_tests = _read("tests/test_cosmology_composition_doorway.py")
    assert "does_not_receive_unverified_glossary_doorway" in cosmology_tests
    assert "No directly relevant canonical cosmology resource has been verified" in cosmology_tests
    assert "None if _cosmology_doorway_not_verified" in cosmology_tests


def test_terminal_no_handoff_and_safety_suppression_remain_separate_from_reply_logic():
    controller = _read(
        "wordpress/living-archive-answer-doorway-standard/assets/guide-controller-v489.332.js"
    )
    reply_start = controller.index("function renderOrdinaryFollowupPanel(response)")
    reply_end = controller.find("\nfunction ", reply_start + 10)
    reply_renderer = controller[reply_start:reply_end]
    assert "guideSafetyActive" in reply_renderer
    assert "invitesReply" in reply_renderer

    terminal_tests = _read("tests/test_guide_terminal_doorway_omission.py")
    assert "test_explicit_visitor_no_handoff_request_clears_all_public_doorway_aliases" in terminal_tests
    assert "test_json_sender_honors_explicit_no_handoff_instruction" in terminal_tests

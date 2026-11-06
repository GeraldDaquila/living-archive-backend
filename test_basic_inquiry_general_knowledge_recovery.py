from unittest.mock import patch

import main


def test_empty_archive_context_retries_shared_general_composition_without_doorway():
    question = "What is institutional memory, and why does it matter?"
    answer = (
        "Institutional memory is the knowledge an organization retains about its decisions, "
        "experience, practices, and lessons over time. It preserves not only what was done, but why.\n\n"
        "For example, recording why a policy changed and what happened afterward helps new members "
        "build on prior experience instead of repeating an earlier mistake or treating an old decision "
        "as unexplained tradition.\n\n"
        "It matters because it supports continuity and learning when people leave or leadership changes. "
        "Records alone are not enough: preserving context helps successors judge what still applies and "
        "what should change."
    )
    with patch(
        "general_guide_composition.compose",
        return_value={"response": answer, "model": "test-general-knowledge"},
    ) as compose:
        result = main._basic_inquiry_round1_deterministic_response(
            question,
            {},
            {"context_blocks": ""},
            recommendation_available=False,
        )

    compose.assert_called_once()
    assert compose.call_args.kwargs["context_data"]["context_blocks"] == ""
    assert result["response"] == answer
    assert result["doorway_title"] == ""
    assert result["provider"] == "contextless_general_knowledge_recovery"

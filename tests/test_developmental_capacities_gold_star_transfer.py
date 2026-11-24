"""Held-out transfer tests for the developmental-capacities Gold Star.

These tests prove retrieval and trusted-system-prompt exposure of the reviewed
reasoning discipline on a paraphrased question. They do not claim that a live
provider selected/applied it or that a human-rated outcome improved.
"""

import gold_star_lessons as lessons
import general_guide_composition as composition

BENCHMARK_ID = "general-guide-developmental-capacities-distinction-before-synthesis-2026-11-24"
HELD_OUT_QUERY = (
    "During a major life transition, how do growth, adaptation, maturity, and "
    "integration interact in a person's development?"
)


def test_held_out_paraphrase_retrieves_only_structural_guidance():
    selected = lessons.select_lesson(HELD_OUT_QUERY)

    assert selected is not None
    assert selected["benchmark_id"] == BENCHMARK_ID
    assert selected["exact"] is False
    assert selected["runtime_transfer"] is True
    assert selected["deterministic_fallback_eligible"] is False


def test_held_out_guidance_reaches_trusted_system_prompt_without_exemplar_content(monkeypatch):
    contribution = lessons.active_quality_contribution(HELD_OUT_QUERY)
    assert contribution is not None
    assert contribution["benchmark_id"] == BENCHMARK_ID
    assert contribution["authority_mode"] == "structural_guidance_only"

    captured = {}

    def fake_route(**kwargs):
        captured.update(kwargs)
        return {"parsed": {"response": (
            "Growth expands capacity, adaptation responds to changed conditions, "
            "maturity exercises judgment, and integration coordinates capacities. "
            "They interact without a mandatory sequence."
        )}}

    monkeypatch.setattr(
        composition, "_gold_star_active_quality_contribution",
        lambda _question: contribution,
    )
    monkeypatch.setattr(composition, "_registered_exact_gold_standard", lambda _question: None)
    monkeypatch.setattr(composition, "route_with_model_bank", fake_route)

    result = composition.compose(
        use_core=object(),
        query=HELD_OUT_QUERY,
        context_data={},
    )

    assert result is not None
    system_message = next(
        item["content"] for item in captured["messages"] if item["role"] == "system"
    )
    user_message = next(
        item["content"] for item in captured["messages"] if item["role"] == "user"
    )

    assert "GOLD STAR MULTI-CANDIDATE ADJUDICATION" in system_message
    assert BENCHMARK_ID in system_message
    assert contribution["discipline"][:100] in system_message
    assert contribution["abstention_boundary"][:100] in system_message
    assert "water scarcity" not in system_message.casefold()
    assert "water scarcity" not in user_message.casefold()
    assert BENCHMARK_ID not in user_message


def test_nearby_but_unrelated_questions_abstain_from_this_gold_star():
    unrelated = (
        "How should a community balance innovation, flexibility, accountability, "
        "and coordination when planning a public festival?"
    )
    selected = lessons.select_lesson(unrelated)
    assert selected is None or selected["benchmark_id"] != BENCHMARK_ID
    contribution = lessons.active_quality_contribution(unrelated)
    assert contribution is None or contribution["benchmark_id"] != BENCHMARK_ID

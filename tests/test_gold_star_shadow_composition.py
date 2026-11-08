from unittest.mock import patch

import general_guide_composition as composition


class _Core:
    pass


def test_compose_emits_shadow_selection_without_passing_guidance_to_provider():
    with patch("gold_star_shadow.evaluate_gold_star_shadow", return_value={
        "gold_star_shadow": True,
        "selected": True,
        "benchmark_id": "example",
        "score": 0.9,
        "reason": "high_confidence_structural_match",
    }), patch.object(composition, "_emit_guide_outcome") as emit, patch.object(
        composition, "_registered_exact_gold_standard", return_value={
            "expected_response": "Approved response.",
            "doorway_title": "",
            "doorway_url": "",
        }
    ):
        result = composition.compose(
            use_core=_Core(),
            query="A test question",
            context_data={},
        )
    assert result["response"] == "Approved response."
    calls = [call.args[0] for call in emit.call_args_list]
    assert "gold_star_shadow" in calls

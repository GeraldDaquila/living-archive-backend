"""Regression tests for preserving verified canonical doorways after conceptual answers."""

import json

import general_guide_composition as guide


def test_conceptual_question_does_not_suppress_a_verified_doorway(monkeypatch):
    question = "What is the relationship between agency and circumstance?"
    expected = {
        "response": (
            "Agency is the capacity to choose and act, while circumstance describes the conditions "
            "in which choices are made. Their relationship matters because circumstances shape which "
            "actions are realistically available, even when they do not determine every choice.\n\n"
            "For example, limited money or authority can narrow a person's options, while support and "
            "resources can widen them. The same decision may therefore carry different costs for people "
            "in different circumstances.\n\n"
            "Agency and circumstance must be considered together: one helps explain a person's response, "
            "and the other helps explain the constraints and possibilities surrounding it. Neither alone "
            "is a complete account of what happened."
        ),
        "doorway_title": "A Canonical Resource",
        "response_shape": "explanatory",
    }

    monkeypatch.setattr(
        guide,
        "_documents_from_context",
        lambda use_core, context_data: [{
            "title": "A Canonical Resource",
            "url": "https://geralddaquila.com/a-canonical-resource/",
            "content": "Agency and circumstance shape choices in social life.",
        }],
    )

    def fake_route(**kwargs):
        raw = json.dumps(expected)
        return {
            "parsed": kwargs["parse"](raw),
            "provider": "test-provider",
            "model": "test-model",
        }

    monkeypatch.setattr(guide, "route_with_model_bank", fake_route)
    monkeypatch.setattr(guide, "_COMPOSITION_CACHE", guide.OrderedDict())

    result = guide.compose(
        use_core=object(),
        query=question,
        context_data={},
    )

    assert result is not None
    assert result["doorway_title"] == "A Canonical Resource"
    assert result["response_shape"] == "explanatory"
    assert len(result["response"].split("\\n\\n")) == 3

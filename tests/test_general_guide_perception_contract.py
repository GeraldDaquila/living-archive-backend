"""Regression contract preserving the established General Guide writer."""

import general_guide_composition as guide


def test_perception_is_a_universal_composition_requirement():
    prompt = guide._GENERAL_GUIDE_SYSTEM
    assert "Apply a universal perception pass to every answer" in prompt
    assert "regardless of topic or response shape" in prompt
    assert "Prefer one earned insight over several generic observations" in prompt


def test_perception_is_question_type_sensitive_not_forced_empathy():
    prompt = guide._GENERAL_GUIDE_SYSTEM
    assert "Perception is not a requirement to sound emotional" in prompt
    assert "do not force every answer into the same genre" in prompt
    assert "Do not turn a neutral question into personal advice" in prompt


def test_perception_preserves_visitor_agency_and_avoids_false_intimacy():
    prompt = guide._GENERAL_GUIDE_SYSTEM
    assert "Preserve the visitor's agency" in prompt
    assert "Do not diagnose, therapize, moralize, presume personal circumstances, or manufacture intimacy" in prompt
    assert "A follow-up invitation is optional" in prompt


def test_composition_contract_advances_for_perception_policy():
    assert guide.CONTRACT_VERSION == "v1.14"
    snapshot = guide.contract_snapshot()
    assert snapshot["contract_version"] == "v1.14"
    assert snapshot["provider_neutral"] is True


def test_writer_does_not_force_restrictive_fact_inference_unknown_gate():
    prompt = guide._GENERAL_GUIDE_SYSTEM
    assert "Apply discernment structurally, not as a final stylistic flourish" not in prompt
    assert "If no relevant Archive material was retrieved, answer from reliable general knowledge when the question permits it" in prompt


def test_writer_preserves_natural_explanatory_reasoning_without_forced_balance():
    prompt = guide._GENERAL_GUIDE_SYSTEM
    assert "Prefer one earned insight over several generic observations" in prompt
    assert "Use a concrete-example decision rule before composing" in prompt


def test_conceptual_relationships_require_discernment_example_and_three_paragraphs():
    query = "What is the relationship between personal agency and responsibility to others?"
    assert guide._requires_discernment_synthesis(query)
    parse = guide._parse_factory([], query)
    import json
    compressed = json.dumps({"response":"Agency means making choices. Responsibility means caring about others.","doorway_title":"","response_shape":"conceptual"})
    import pytest
    with pytest.raises(ValueError):
        parse(compressed)
    complete = json.dumps({"response": "\n\n".join([
        "Agency gives people room to make choices, while responsibility asks them to consider how those choices affect others. They are connected because choices happen within relationships, not in isolation.",
        "For example, a manager may reorganize a team to meet a goal, but the decision also changes employees' workload and security. Taking those consequences seriously is part of exercising authority well.",
        "Responsibility does not mean obeying every demand. It means being answerable for foreseeable effects while respecting other people's legitimate needs and one's own boundaries."
    ]), "doorway_title": "", "response_shape": "conceptual"})
    assert len(parse(complete)["response"].split("\n\n")) == 3


def test_writer_contract_advances_sequentially_after_restoration():
    assert guide.CONTRACT_VERSION == "v1.14"
    assert guide.contract_snapshot()["contract_version"] == "v1.14"

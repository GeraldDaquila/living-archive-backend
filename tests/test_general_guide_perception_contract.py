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
    assert guide.CONTRACT_VERSION == "v1.16"
    snapshot = guide.contract_snapshot()
    assert snapshot["contract_version"] == "v1.16"
    assert snapshot["provider_neutral"] is True


def test_writer_does_not_force_restrictive_fact_inference_unknown_gate():
    prompt = guide._GENERAL_GUIDE_SYSTEM
    assert "Apply discernment structurally, not as a final stylistic flourish" not in prompt
    assert "If no relevant Archive material was retrieved, answer from reliable general knowledge when the question permits it" in prompt


def test_writer_preserves_natural_explanatory_reasoning_without_forced_balance():
    prompt = guide._GENERAL_GUIDE_SYSTEM
    assert "Prefer one earned insight over several generic observations" in prompt
    assert "Use a concrete-example decision rule before composing" in prompt
    assert "preserve the full movement of the reasoning rather than compressing it into a summary" in prompt
    assert "Each paragraph must advance the thought, not repeat it" in prompt
    assert "The final insight should emerge from the explanation, not arrive as a generic moral" in prompt


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
        "Personal agency and responsibility to others are not opposing forces but interdependent aspects of the same moral life. Agency is the capacity to make choices and act on them; responsibility is the recognition that those choices have consequences for people who are affected by them. You cannot exercise genuine agency without acknowledging that your actions exist within a web of relationships, and you cannot fulfill responsibility to others without the freedom to choose how to act.",
        "The tension arises when agency is understood as pure independence—the idea that you are a self-contained individual whose choices are yours alone. In reality, our decisions are shaped by the people we are connected to, and those people are shaped by our decisions. For example, a manager who exercises agency to restructure a team is not just making a personal career move; they are altering the working conditions, security, and morale of the people on that team. The manager's freedom to decide is real, but it is bounded by the legitimate needs and rights of the employees. Ignoring that boundary doesn't make the choice more free; it makes it less responsible.",
        "The key distinction is between agency as the ability to act and agency as the right to act without regard for impact. True agency includes the willingness to be accountable for the effects of your choices. Responsibility to others is not a constraint on your freedom; it is the condition that makes your freedom meaningful. When you act with awareness of how your choices affect others, you are not surrendering your agency—you are exercising it fully."
    ]), "doorway_title": "", "response_shape": "conceptual"})
    parsed = parse(complete)["response"]
    assert len(parsed.split("\n\n")) == 3
    assert "interdependent aspects of the same moral life" in parsed
    assert "manager who exercises agency to restructure a team" in parsed
    assert "condition that makes your freedom meaningful" in parsed


def test_writer_contract_advances_sequentially_after_restoration():
    assert guide.CONTRACT_VERSION == "v1.15"
    assert guide.contract_snapshot()["contract_version"] == "v1.16"


def test_incomplete_comparison_question_clarifies_before_retrieval():
    result = guide.clarification_response(
        "Can you compare two ways of understanding this problem?"
    )
    assert result is not None
    assert result["clarification_reason"] == "comparison_subject_missing"
    assert "Which problem would you like to compare?" in result["response"]
    assert "help identify two useful ways" in result["response"]
    assert "what becomes clearer" in result["response"]


def test_named_comparison_subject_does_not_trigger_clarification():
    assert guide.clarification_response(
        "Can you compare two ways of understanding climate migration?"
    ) is None


def test_relevant_conversation_history_can_supply_the_missing_subject():
    assert guide.clarification_response(
        "Can you compare two ways of understanding this problem?",
        "We are discussing why familiar solutions stop working after circumstances change."
    ) is None


def test_ordinary_explanatory_question_is_not_interrupted():
    assert guide.clarification_response(
        "Why do familiar solutions stop working when circumstances change?"
    ) is None


def test_composition_contract_version_advances_for_clarification_boundary():
    assert guide.CONTRACT_VERSION == "v1.16"
    assert guide.contract_snapshot()["contract_version"] == "v1.16"

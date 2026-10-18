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
    assert "A follow-up invitation is optional unless the visitor explicitly requests one" in prompt
    assert "honor that request with exactly one natural, relevant question at the end" in prompt


def test_composition_contract_advances_for_perception_policy():
    assert guide.CONTRACT_VERSION == "v1.20"
    snapshot = guide.contract_snapshot()
    assert snapshot["contract_version"] == "v1.20"
    assert snapshot["provider_neutral"] is True


def test_writer_does_not_force_restrictive_fact_inference_unknown_gate():
    prompt = guide._GENERAL_GUIDE_SYSTEM
    assert "Apply discernment structurally, not as a final stylistic flourish" not in prompt
    assert "If no relevant Archive material was retrieved, answer from reliable general knowledge when the question permits it" in prompt


def test_writer_preserves_natural_explanatory_reasoning_without_forced_balance():
    prompt = guide._GENERAL_GUIDE_SYSTEM
    assert "Prefer one earned insight over several generic observations" in prompt
    assert "Use a concrete-example decision rule before composing" in prompt
    assert "preserve the reasoning rather than flattening it into a summary" in prompt
    assert "Each paragraph must add a new piece of understanding" in prompt
    assert "stop once the visitor has the understanding they came for" in prompt
    assert "one concrete, plausible situation only if it clarifies the mechanism or consequence" in prompt


def test_conceptual_relationships_require_reasoning_but_allow_proportionate_length():
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

    compact = json.dumps({
        "response": (
            "Agency is the ability to make choices; responsibility recognizes that those choices affect other people. "
            "The tension appears when independence is mistaken for freedom from consequences.\n\n"
            "Agency does not mean acting without regard for impact. Responsibility gives freedom a relational boundary "
            "without removing the person's ability to choose."
        ),
        "doorway_title": "",
        "response_shape": "conceptual",
    })
    compact_parsed = parse(compact)["response"]
    assert len(compact_parsed.split("\n\n")) == 2
    assert "does not mean" in compact_parsed


def test_writer_contract_advances_sequentially_after_restoration():
    assert guide.CONTRACT_VERSION == "v1.20"
    assert guide.contract_snapshot()["contract_version"] == "v1.20"


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
    assert guide.CONTRACT_VERSION == "v1.20"
    assert guide.contract_snapshot()["contract_version"] == "v1.20"


def test_plain_stewardship_explanation_rejects_unsolicited_spectrum_list():
    import json
    import pytest

    query = "Explain stewardship, but do not send me to another page yet."
    parse = guide._parse_factory([], query)
    response = """Stewardship is care for what others rely on.

A useful way to think about stewardship is as a spectrum:
- Personal stewardship means caring for yourself.
- Community stewardship means caring for shared places.
- Guardian stewardship means caring for the planet.

Each level expands responsibility."""
    raw = json.dumps({"response": response, "doorway_title": "", "response_shape": "explanatory"})
    with pytest.raises(ValueError, match="unsolicited list"):
        parse(raw)


def test_plain_stewardship_explanation_accepts_everyday_example_and_clear_limits():
    import json

    query = "Explain stewardship, but do not send me to another page yet."
    parse = guide._parse_factory([], query)
    response = """Stewardship means taking care of something entrusted to you—such as your time, relationships, shared spaces, money, or the natural world—rather than treating it as if only immediate needs matter.

In everyday life, it shows up in small choices: keeping a promise, maintaining what others rely on, using resources thoughtfully, and considering how your decisions affect people around you. These choices accumulate; carelessness can pass costs to others or to the future, while responsible care preserves trust and possibilities.

Stewardship does not mean controlling everything or sacrificing yourself for everyone else. It means recognizing what is yours to care for, acting responsibly within your limits, and leaving things no worse—and where possible better—than you found them."""
    raw = json.dumps({"response": response, "doorway_title": "", "response_shape": "explanatory"})
    parsed = parse(raw)
    assert len(parsed["response"].split("\n\n")) == 3
    assert "keeping a promise" in parsed["response"]
    assert "does not mean controlling everything" in parsed["response"]


def test_resource_discovery_answers_the_search_need_without_speculative_padding():
    prompt = guide._GENERAL_GUIDE_SYSTEM
    assert "Distinguish a broad entry point from a resource that directly addresses the subject" in prompt
    assert "Do not merely quote a generic page description" in prompt
    assert "Never pad this explanation with speculative phrases" in prompt
    assert "Keep the canonical link separate from the answer" in prompt



def test_explicit_closing_question_request_is_detected_and_enforced():
    import json
    import pytest

    query = "Explain stewardship in everyday life, and finish with one brief question inviting me to reflect on my own experience."
    assert guide._requires_explicit_followup_invitation(query)
    parse = guide._parse_factory([], query)

    missing_question = json.dumps({
        "response": "Stewardship means caring for what others rely on. It matters because ordinary choices affect people around us.",
        "doorway_title": "",
        "response_shape": "explanatory",
    })
    with pytest.raises(ValueError, match="requires a closing question"):
        parse(missing_question)

    valid_invitation = json.dumps({
        "response": "Stewardship means caring for what others rely on. It matters because ordinary choices affect people around us. What is one thing in your everyday life that you feel responsible for caring for?",
        "doorway_title": "",
        "response_shape": "explanatory",
    })
    assert parse(valid_invitation)["response"].endswith("?")

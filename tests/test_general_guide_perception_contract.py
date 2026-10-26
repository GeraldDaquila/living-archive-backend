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
    assert guide.CONTRACT_VERSION == "v1.28"
    snapshot = guide.contract_snapshot()
    assert snapshot["contract_version"] == "v1.28"
    assert snapshot["provider_neutral"] is True


def test_stewardship_presentation_is_a_systemwide_explanatory_standard():
    prompt = guide._GENERAL_GUIDE_SYSTEM
    assert "System-wide answer presentation standard" in prompt
    assert "applies to every ordinary Guide topic" in prompt
    assert "A substantive explanatory or conceptual question defaults to three purposeful paragraphs" in prompt
    assert "complete before an optional Archive doorway appears" in prompt
    assert "not only stewardship or Archive-specific questions" in prompt
    assert "simple, self-contained factual lookup may be one or two sentences" in prompt
    assert "direct navigation request should give a clear destination" in prompt


def test_systemwide_presentation_preserves_humane_voice_and_evidence_boundaries():
    prompt = guide._GENERAL_GUIDE_SYSTEM
    assert "humane, patient, natural voice in every subject area" in prompt
    assert "do not use the evidence limitation as a substitute for answering" in prompt
    assert "do not fabricate an exhaustive doctrine or canonical list" in prompt
    assert "The Guide is a doorway into the Living Archive" in prompt


def test_responsibility_without_system_repair_has_a_distinct_composition_contract():
    prompt = guide._GENERAL_GUIDE_SYSTEM
    assert "taking responsibility for change without becoming responsible for an entire broken system" in prompt
    assert "Separate the visitor’s sphere of influence from what requires shared ownership" in prompt
    assert "acknowledge legitimate limits" in prompt
    assert "Do not assume this is a formal diagnostic request solely because the question mentions a broken system" in prompt


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


def test_conceptual_relationships_require_three_paragraph_default():
    query = "What is the relationship between personal agency and responsibility to others?"
    assert guide._requires_discernment_synthesis(query)
    parse = guide._parse_factory([], query)
    import json
    import pytest
    compressed = json.dumps({"response":"Agency means making choices. Responsibility means caring about others.","doorway_title":"","response_shape":"conceptual"})
    with pytest.raises(ValueError):
        parse(compressed)
    complete = json.dumps({"response": "\n\n".join([
        "Personal agency and responsibility to others are interdependent aspects of the same moral life. Agency is the capacity to make choices and act on them; responsibility is recognizing that those choices affect other people. Genuine agency does not require ignoring the relationships in which our choices take effect.",
        "The tension appears when agency is treated as independence from consequences. For example, a manager who restructures a team is exercising real choice, but that decision also changes employees’ working conditions, security, and morale. Responsible leadership considers the people affected and explains the decision fairly.",
        "The key distinction is between the ability to act and the claim to act without regard for impact. Responsibility does not erase agency; it makes agency accountable and relational. Considering the effects of our choices allows freedom to be exercised more fully rather than surrendered."
    ]), "doorway_title": "", "response_shape": "conceptual"})
    parsed = parse(complete)["response"]
    assert len(parsed.split("\n\n")) == 3
    assert "interdependent aspects of the same moral life" in parsed
    assert "manager who restructures a team" in parsed
    assert "Responsibility does not erase agency" in parsed

    compact = json.dumps({
        "response": (
            "Agency is the ability to make choices; responsibility recognizes that those choices affect other people. "
            "The tension appears when independence is mistaken for freedom from consequences.\n\n"
            "Agency does not mean acting without regard for impact. Responsibility gives freedom a relational boundary "
            "without removing the person’s ability to choose.\n\n"
            "This matters because agency and responsibility work together: people retain meaningful choice while considering "
            "how their actions affect others."
        ),
        "doorway_title": "",
        "response_shape": "conceptual",
    })
    compact_parsed = parse(compact)["response"]
    assert len(compact_parsed.split("\n\n")) == 3
    assert "does not mean" in compact_parsed

def test_writer_contract_advances_sequentially_after_restoration():
    assert guide.CONTRACT_VERSION == "v1.28"
    assert guide.contract_snapshot()["contract_version"] == "v1.28"


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
    assert guide.CONTRACT_VERSION == "v1.28"
    assert guide.contract_snapshot()["contract_version"] == "v1.28"


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
        "response": "Stewardship means caring for what others rely on, including shared spaces and resources.\n\nIn everyday life, keeping a promise or maintaining what others rely on can protect trust over time.\n\nStewardship does not mean controlling everything or sacrificing yourself for everyone else. It means acting within your limits and caring for what is yours to care for.",
        "doorway_title": "",
        "response_shape": "explanatory",
    })
    with pytest.raises(ValueError, match="requires a closing question"):
        parse(missing_question)

    valid_invitation = json.dumps({
        "response": "Stewardship means caring for what others rely on, including shared spaces and resources.\n\nIn everyday life, keeping a promise or maintaining what others rely on can protect trust over time.\n\nStewardship does not mean controlling everything or sacrificing yourself for everyone else. It means acting within your limits and caring for what is yours to care for. What is one thing in your everyday life that you feel responsible for caring for?",
        "doorway_title": "",
        "response_shape": "explanatory",
    })
    assert parse(valid_invitation)["response"].endswith("?")



def test_gold_standard_is_the_default_general_presentation_contract():
    prompt = guide._GENERAL_GUIDE_SYSTEM
    assert "DEFAULT PRESENTATION STANDARD (applies to ordinary general-purpose questions)" in prompt
    assert "Lead with the answer, not a description of what an answer should contain" in prompt
    assert "normally three purposeful, readable paragraphs" in prompt
    assert "Do not append a generic clarification prompt merely to prolong the exchange" in prompt
    assert "place any verified, directly relevant Archive resource in a distinct, clearly labeled doorway section" in prompt
    assert "For a substantive explanatory, conceptual, educational, social, or Archive-related question, present three connected, readable paragraphs by default" in prompt



def test_historical_origin_and_evolution_questions_use_explanatory_shape():
    question = "On surface, the Philippines is very much a macho society. Where is the matriarchal reality come from and how it evolved?"
    assert guide._question_shape(question) == "explanatory"
    prompt = guide._GENERAL_GUIDE_SYSTEM
    assert "For historical, cultural, or social questions asking where a phenomenon comes from or how it evolved" in prompt
    assert "Never substitute practical self-help advice, a planning framework, or an action checklist unless the visitor asks for one" in prompt



def test_gold_standard_is_system_wide_floor_and_task_formats_must_earn_exception():
    prompt = guide._GENERAL_GUIDE_SYSTEM
    assert "SYSTEM-WIDE GOLD STANDARD FLOOR (default across the entire Guide)" in prompt
    assert "every visitor-facing response, regardless of topic or specialist route" in prompt
    assert "The task format changes the shape, never lowers the quality floor" in prompt
    assert "A specialist's preferred format is not an exception merely because it is specialist-specific" in prompt
    assert "This floor governs fallbacks too" in prompt

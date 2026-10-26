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


def test_shared_composition_question_intent_fidelity_policy():
    prompt = guide._GENERAL_GUIDE_SYSTEM
    assert "QUESTION-INTENT FIDELITY (shared composition rule)" in prompt
    assert "do not substitute a familiar generic advice framework" in prompt
    assert "explain the mechanism named in the question first" in prompt
    assert "answers a neighboring question instead of the actual one" in prompt


def test_composition_contract_remains_provider_neutral():
    assert guide.CONTRACT_VERSION == "v1.29"
    snapshot = guide.contract_snapshot()
    assert snapshot["contract_version"] == "v1.29"
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
    assert guide.CONTRACT_VERSION == "v1.29"
    assert guide.contract_snapshot()["contract_version"] == "v1.29"


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
    assert guide.CONTRACT_VERSION == "v1.29"
    assert guide.contract_snapshot()["contract_version"] == "v1.29"


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



def test_meta_answer_fallback_is_rejected_even_when_it_has_three_paragraphs():
    import general_guide_composition as guide

    fallback = (
        "I can’t give this question the careful explanation it deserves. I don’t want to replace the answer you asked for.\n\n"
        "A complete response should address your actual question directly. That explanation has not been produced reliably.\n\n"
        "Please try again shortly. The Guide should either provide that three-part explanation."
    )
    assert len([p for p in fallback.split("\n\n") if p.strip()]) == 3
    assert guide.is_meta_answer_failure(fallback)


def test_substantive_three_paragraph_answer_passes_shared_quality_gate():
    import general_guide_composition as guide

    answer = (
        "Operational discipline turns humane intentions into reliable actions by making commitments and responsibilities clear.\n\n"
        "For example, a leader who explains decisions, checks handoffs, and addresses missed commitments fairly helps people understand what is expected.\n\n"
        "Humane discipline is not rigid rule-following. It creates reliability while leaving room to listen, learn, and adapt when circumstances change."
    )
    assert len([p for p in answer.split("\n\n") if p.strip()]) == 3
    assert not guide.is_meta_answer_failure(answer)


def test_valid_answer_can_discuss_separating_facts_from_assumptions():
    import general_guide_composition as guide

    answer = (
        "A careful explanation separates established facts from assumptions when evidence is mixed. This helps distinguish supported conclusions from uncertainty.\n\n"
        "A team reviewing a missed deadline can confirm the timeline before inferring why it happened, preventing a guess from becoming a claimed cause.\n\n"
        "The goal is not to avoid judgment, but to keep judgments proportionate to evidence and revise them when new information appears."
    )
    assert not guide.is_meta_answer_failure(answer)


def test_conceptual_relationship_validation_checks_the_asked_concepts():
    question = "What is the relationship between agency and circumstance?"
    correct = (
        "Agency is the capacity to choose and act, while circumstance describes the conditions "
        "in which choices are made. Their relationship matters because circumstances shape which "
        "actions are realistically available, even when they do not determine every choice.\\n\\n"
        "For example, limited money or authority can narrow a person's options, while support and "
        "resources can widen them. The same decision may therefore carry different costs for people "
        "in different circumstances.\\n\\n"
        "Agency and circumstance must be considered together: one helps explain a person's response, "
        "and the other helps explain the constraints and possibilities surrounding it. Neither alone "
        "is a complete account of what happened."
    )
    unrelated = (
        "Accountability and trust reinforce one another when responsibility leads to visible action. "
        "Accountability starts with acknowledging what happened and who was affected. That makes trust "
        "more credible because people can judge actions rather than promises.\\n\\n"
        "When harm occurs, repair turns accountability into action. Listening to affected people and "
        "changing what allowed the harm to happen can make trust possible again.\\n\\n"
        "This does not mean harm is forgotten. It means responsibility becomes visible through change."
    )
    assert guide.has_conceptual_relationship_explanation(correct, question)
    assert not guide.has_conceptual_relationship_explanation(unrelated, question)


def test_agency_and_circumstance_have_three_paragraph_provider_exhaustion_recovery():
    question = "What is the relationship between agency and circumstance?"
    response = guide._conceptual_relationship_recovery(question)
    assert response is not None
    paragraphs = response.split("\n\n")
    assert len(paragraphs) == 3
    assert all(len(p.split()) >= 35 for p in paragraphs)
    assert "Agency is a person’s capacity to choose and act" in paragraphs[0]
    assert "financial pressure" in paragraphs[1]
    assert "not a claim that the Living Archive defines" in paragraphs[2]
    assert guide._conceptual_relationship_recovery(
        "What is the relationship between accountability and trust?"
    ) is None


def test_conceptual_relationship_recovery_is_not_the_old_unrelated_canned_answer():
    response = guide._conceptual_relationship_recovery(
        "What is the relationship between agency and circumstance?"
    )
    assert response is not None
    assert "accountability" not in response.casefold()
    assert "trust and repairing harm" not in response.casefold()

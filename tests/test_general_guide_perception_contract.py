"""Regression contract preserving the established General Guide writer."""

import ast
from pathlib import Path
import re

import general_guide_composition as guide


# Load the pure response-boundary helper without importing the FastAPI app.
_SOURCE_PATH = Path(__file__).resolve().parents[1] / "main.py"
_SOURCE_TREE = ast.parse(_SOURCE_PATH.read_text(encoding="utf-8"))
_HELPER_NODES = [
    node for node in _SOURCE_TREE.body
    if isinstance(node, ast.FunctionDef)
    and node.name in {
        "_guide_reconcile_resource_language",
        "_guide_bounded_community_archive_answer",
        "_guide_bounded_friendship_expectations_answer",
        "_guide_response_disclaims_archive_recommendation",
        "_guide_discovery_html_recovery",
        "_guide_verified_doorway_evidence_for_query",
        "_guide_recovery_subject_for_resource",
    }
]
_HELPER_NAMESPACE = {"re": re}
exec(
    compile(ast.Module(body=_HELPER_NODES, type_ignores=[]), str(_SOURCE_PATH), "exec"),
    _HELPER_NAMESPACE,
)
_reconcile_resource_language = _HELPER_NAMESPACE["_guide_reconcile_resource_language"]
_community_archive_answer = _HELPER_NAMESPACE["_guide_bounded_community_archive_answer"]
_friendship_expectations_answer = _HELPER_NAMESPACE["_guide_bounded_friendship_expectations_answer"]
_response_disclaims_archive_recommendation = _HELPER_NAMESPACE["_guide_response_disclaims_archive_recommendation"]
_recovery_subject_for_resource = _HELPER_NAMESPACE["_guide_recovery_subject_for_resource"]


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


def test_unavailable_recommendation_cannot_be_promised_in_visitor_text():
    response = (
        "Your question asks about a community archive. "
        "If you would like to explore this further, the Archive resource below "
        "may offer a useful next step."
    )
    result = _reconcile_resource_language(response, recommendation_available=False)
    assert "resource below" not in result.lower()
    assert "I could not identify a sufficiently relevant Archive resource to recommend here." in result


def test_unavailable_recommendation_does_not_duplicate_existing_boundary_sentence():
    response = (
        "The answer is based on general knowledge. "
        "The Archive resource below may offer a useful next step. "
        "I could not identify a sufficiently relevant Archive resource to recommend here."
    )
    result = _reconcile_resource_language(response, recommendation_available=False)
    assert "resource below" not in result.lower()
    assert result.count("I could not identify a sufficiently relevant Archive resource to recommend here.") == 1


def test_available_recommendation_preserves_proportionate_resource_language():
    response = "The Archive resource below may offer a useful next step."
    result = _reconcile_resource_language(response, recommendation_available=True)
    assert result == response


def test_unrelated_answer_is_not_rewritten_when_no_recommendation_exists():
    response = "Keep one reading list and review it once a week."
    result = _reconcile_resource_language(response, recommendation_available=False)
    assert result == response


def test_community_archive_responsibility_question_gets_bounded_general_answer():
    answer = _community_archive_answer(
        "What are the responsibilities of a community archive in preserving public knowledge?"
    )
    assert answer is not None
    assert answer["doorway_title"] == ""
    assert answer["provider"] == "bounded_community_archive_responsibility_recovery"
    assert "preserve records with care" in answer["response"]
    assert "privacy, consent, rights" in answer["response"]
    assert "transparent correction practices" in answer["response"]
    assert "general archival principles" in answer["response"]
    assert "resource below" not in answer["response"].lower()


def test_community_archive_recovery_does_not_capture_unrelated_questions():
    assert _community_archive_answer("How should I organize a reading list?") is None


def test_generic_friendship_expectations_question_does_not_need_people_or_we():
    answer = _friendship_expectations_answer(
        "What are common patterns of misunderstandings in friendships?"
    )
    assert answer is not None
    assert answer["provider"] == "bounded_friendship_expectations_recovery"
    assert "how often people expect to be in touch" in answer["response"]
    assert "whether they want advice or simply to be heard" in answer["response"]
    assert answer["response"].endswith("Which expectation tends to be hardest for people to read accurately?")


def test_friendship_expectations_recovery_does_not_capture_lived_questions():
    assert _friendship_expectations_answer(
        "What are common patterns of misunderstandings in my friendship?"
    ) is None


def test_answer_that_disclaims_direct_archive_fit_suppresses_doorway():
    response = (
        "These are general archival principles. "
        "I did not identify a sufficiently direct Archive resource to recommend for this question."
    )
    assert _response_disclaims_archive_recommendation(response)


def test_general_answer_without_resource_disclaimer_does_not_suppress_doorway():
    response = "A community archive should preserve records with care and document their provenance."
    assert not _response_disclaims_archive_recommendation(response)



def test_malformed_discovery_prose_recovers_from_verified_canonical_evidence(monkeypatch):
    namespace = _HELPER_NAMESPACE
    doorway = {"title": "Document Types of the Living Archive", "url": "https://geralddaquila.com/document-types/"}
    evidence = [{"url": doorway["url"], "text": "Document Types of the Living Archive"}]
    monkeypatch.setitem(namespace, "_guide_discovery_doorway_is_evidence_backed", lambda selected, items: selected == doorway and items == evidence)
    monkeypatch.setitem(namespace, "_guide_subject_discovery_answer", lambda response, subject, selected, items: f"Grounded orientation for {selected['title']} about {subject}.")
    monkeypatch.setitem(namespace, "_basic_inquiry_markup_recovery", lambda query, history, intent: "I couldn't verify a reliable answer from the material available in this request.")
    recover = namespace["_guide_discovery_html_recovery"]

    result = recover("Explain the Living Archive's document types.", [], "TOPICAL_INQUIRY", "document types", doorway, evidence)

    assert result == "Grounded orientation for Document Types of the Living Archive about document types."
    assert "couldn't verify" not in result.lower()


def test_malformed_discovery_prose_fails_closed_without_verified_canonical_evidence(monkeypatch):
    namespace = _HELPER_NAMESPACE
    monkeypatch.setitem(namespace, "_guide_discovery_doorway_is_evidence_backed", lambda selected, items: False)
    monkeypatch.setitem(namespace, "_guide_subject_discovery_answer", lambda *args: (_ for _ in ()).throw(AssertionError("must not use unverified evidence")))
    fallback = "I couldn't verify a reliable answer from the material available in this request."
    monkeypatch.setitem(namespace, "_basic_inquiry_markup_recovery", lambda query, history, intent: fallback)

    result = namespace["_guide_discovery_html_recovery"]("Explain a topic.", [], "TOPICAL_INQUIRY", "", None, [])

    assert result == fallback



def test_malformed_ordinary_answer_recovers_from_selected_relevant_canonical_resource(monkeypatch):
    namespace = _HELPER_NAMESPACE
    doorway = {"title": "Document Types of the Living Archive", "url": "https://geralddaquila.com/document-types/"}
    evidence = [{"url": doorway["url"], "text": "Document Types of the Living Archive explains the Archive's document classes."}]
    calls = []
    monkeypatch.setitem(namespace, "_guide_discovery_doorway_is_evidence_backed", lambda selected, items: selected == doorway and items == evidence)
    monkeypatch.setitem(namespace, "_guide_verified_doorway_evidence_for_query", lambda subject, selected, context, composition: calls.append((subject, selected)) or evidence)
    monkeypatch.setitem(namespace, "_guide_subject_discovery_answer", lambda response, subject, selected, items: f"Grounded orientation for {selected['title']} about {subject}.")
    monkeypatch.setitem(namespace, "_basic_inquiry_markup_recovery", lambda query, history, intent: "I couldn't verify a reliable answer from the material available in this request.")

    result = namespace["_guide_discovery_html_recovery"](
        "Explain the Living Archive's document types.", [], "TOPICAL_INQUIRY",
        "", doorway, [], {"context_blocks": "fetched context"}, {"generation_authority_protected_docs": []}
    )

    assert calls and calls[0][0] == "Explain the Living Archive's document types"
    assert result == "Grounded orientation for Document Types of the Living Archive about Explain the Living Archive's document types."
    assert "couldn't verify" not in result.lower()



def test_recovery_subject_strips_archive_request_framing_before_relevance_grading():
    assert _recovery_subject_for_resource("Explain the Living Archive's document types.") == "document types"
    assert _recovery_subject_for_resource("What are the canonical document types of the Living Archive?") == "the canonical document types"
    assert _recovery_subject_for_resource("Why do familiar solutions stop working when circumstances change?") == "Why do familiar solutions stop working when circumstances change"



def test_unregistered_canonical_article_requires_direct_evidence_match(monkeypatch):
    namespace = _HELPER_NAMESPACE
    doorway = {"title": "Document Types of the Living Archive", "url": "https://geralddaquila.com/document-types/"}
    document = {"title": doorway["title"], "url": doorway["url"], "text": "Document Types of the Living Archive explains the Archive's document classes."}
    fake_core = type("FakeCore", (), {"context_blocks_to_documents": staticmethod(lambda blocks: [document])})()
    monkeypatch.setitem(namespace, "use_core", fake_core)
    monkeypatch.setitem(namespace, "_guide_node_registry_snapshot", lambda: [])
    monkeypatch.setitem(namespace, "_guide_discovery_evidence_grade", lambda subject, item, node=None: {"grade": "direct", "score": 100, "support": ["document", "types"]})
    monkeypatch.setitem(namespace, "_guide_discovery_doorway_is_evidence_backed", lambda selected, items: bool(items) and selected["url"].rstrip("/") == items[0]["url"].rstrip("/") and bool(items[0].get("text")))

    evidence = namespace["_guide_verified_doorway_evidence_for_query"]("document types", doorway, {"context_blocks": "fetched"}, {})

    assert len(evidence) == 1
    assert evidence[0]["url"] == doorway["url"].rstrip("/")
    assert evidence[0]["_discovery_relevance"] == "direct"
    assert "_guide_node" not in evidence[0]


def test_unregistered_canonical_article_rejects_related_only_match(monkeypatch):
    namespace = _HELPER_NAMESPACE
    doorway = {"title": "Document Types of the Living Archive", "url": "https://geralddaquila.com/document-types/"}
    document = {"title": doorway["title"], "url": doorway["url"], "text": "A broadly related page."}
    fake_core = type("FakeCore", (), {"context_blocks_to_documents": staticmethod(lambda blocks: [document])})()
    monkeypatch.setitem(namespace, "use_core", fake_core)
    monkeypatch.setitem(namespace, "_guide_node_registry_snapshot", lambda: [])
    monkeypatch.setitem(namespace, "_guide_discovery_evidence_grade", lambda subject, item, node=None: {"grade": "related", "score": 30, "support": ["archive"]})
    monkeypatch.setitem(namespace, "_guide_discovery_doorway_is_evidence_backed", lambda selected, items: bool(items))

    evidence = namespace["_guide_verified_doorway_evidence_for_query"]("document types", doorway, {"context_blocks": "fetched"}, {})

    assert evidence == []

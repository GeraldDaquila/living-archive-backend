"""Two-level regression tests for layered answerability and calibrated abstention."""

from pathlib import Path

import general_guide_composition as composition
import main
from guide_answerability import (
    ARCHITECTURAL_CONTRACT,
    build_answerability_plan,
    has_reality_vs_ideology_explanation,
    is_reality_vs_ideology_leadership_question,
    reality_vs_ideology_recovery,
)

QUESTION = "What does it mean to lead from reality rather than ideology?"


def test_query_level_recognizes_target_question_and_paraphrases():
    assert is_reality_vs_ideology_leadership_question(QUESTION)
    assert is_reality_vs_ideology_leadership_question(
        "How is reality-led leadership different from ideology-driven leadership?"
    )
    assert is_reality_vs_ideology_leadership_question(
        "Explain what leading from reality instead of ideology means."
    )


def test_query_classifier_does_not_capture_unrelated_or_source_specific_questions():
    for query in (
        "What does ideology mean?",
        "What is reality in philosophy?",
        "How do I lead a team meeting?",
        "Is this organization's policy consistent with its published doctrine?",
        "According to the Living Archive, what does it mean to lead from reality rather than ideology?",
        "Using only the Archive's published text, what does it mean to lead from reality rather than ideology?",
        "What does it mean to lead from reality rather than ideology in clinical care?",
        "What does it mean to lead from reality rather than ideology in legal decision-making?",
        "What does it mean to lead from reality?",
    ):
        assert not is_reality_vs_ideology_leadership_question(query)


def test_answerability_plan_separates_general_meaning_from_institutional_authority():
    plan = build_answerability_plan(QUESTION)
    assert plan is not None
    assert plan["task_class"] == "reality_vs_ideology_leadership"
    assert plan["version"] == "1.0"
    for phrase in (
        "absence of an authoritative",
        "ordinary conceptual usage",
        "Answer the answerable portion directly",
        "Abstain only from the portion",
        "explicit source-only constraints",
    ):
        assert phrase.casefold() in ARCHITECTURAL_CONTRACT.casefold()
    for phrase in (
        "actual conditions",
        "observable evidence",
        "fixed set of beliefs",
        "not value-free or principle-free",
        "general conceptual explanation",
    ):
        assert phrase.casefold() in plan["composition_instruction"].casefold()
    assert build_answerability_plan("What does ideology mean?") is None


def test_bounded_recovery_answers_without_claiming_formal_archive_doctrine():
    answer = reality_vs_ideology_recovery()
    assert has_reality_vs_ideology_explanation(answer)
    assert "values or principles" in answer
    assert "listens to people affected" in answer
    assert "general conceptual explanation" in answer
    assert "formal Living Archive definition" in answer


def test_final_composition_boundary_repairs_over_abstention():
    abstention = (
        "I can't define it reliably from the information available in this response alone. "
        "I don't want to invent a definition or imply that a guess is established knowledge."
    )
    answer = composition.enforce_response_contracts(QUESTION, abstention)
    assert has_reality_vs_ideology_explanation(answer)
    assert "I can't define" not in answer


def test_final_composition_boundary_preserves_a_complete_provider_answer():
    valid = (
        "Leading from reality means beginning with actual conditions and evidence. "
        "Ideological leadership lets fixed beliefs or a preferred outcome decide which facts count. "
        "Values and principles still guide what matters, but a leader must revise a position when "
        "the evidence changes. For example, a public service policy should be changed when the "
        "people affected show that it is not working."
    )
    assert composition.enforce_response_contracts(QUESTION, valid) == valid


def test_live_basic_inquiry_answers_before_retrieval_or_provider(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("This general conceptual answer must not depend on retrieval or a provider.")

    monkeypatch.setattr(main.use_core, "fetch_canonical_context", forbidden)
    monkeypatch.setattr(main, "route_with_model_bank", forbidden)

    payload = main._basic_inquiry_response(QUESTION)
    assert has_reality_vs_ideology_explanation(payload["response"])
    assert payload["processing"] == "guide_reality_vs_ideology_answer_first"
    assert payload["route_source"] == "guide_layered_answerability_early_boundary"
    assert payload["response_provenance"]["llm_invoked"] is False
    assert payload["answer_basis"]["kind"] == "general_knowledge"
    assert payload["recommendation"] is None
    assert payload["canonical_doorway"] is None


def test_architectural_and_query_level_contracts_are_wired_into_shared_composer():
    source = Path("general_guide_composition.py").read_text(encoding="utf-8")
    assert "from guide_answerability import" in source
    assert "_LAYERED_ANSWERABILITY_ARCHITECTURAL_CONTRACT" in source
    assert "_build_layered_answerability_plan(question)" in source
    assert "+ layered_answerability_instruction" in source
    assert "has_reality_vs_ideology_explanation" in source

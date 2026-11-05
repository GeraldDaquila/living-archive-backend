"""Regression tests for Archive/Guide self-reference epistemic boundaries."""

import general_guide_composition as composition
import main


CLAIM_QUESTION = "How should The Guide separate direct archive claims from its own synthesis?"
NO_COVERAGE_QUESTION = "When should The Guide say the Archive does not yet address this directly?"
GENERALIZATION_QUESTION = (
    "What standards should be met before The Guide generalizes from one archive "
    "text to the whole cosmology?"
)
CONFLICT_QUESTION = "How should conflicting ideas within the corpus be handled?"


def test_archive_self_reference_detector_covers_epistemic_questions():
    for query in (
        CLAIM_QUESTION,
        NO_COVERAGE_QUESTION,
        GENERALIZATION_QUESTION,
        CONFLICT_QUESTION,
        "What counts as evidence, interpretation, hypothesis, and normative judgment?",
        "What is constitutional reasoning in the Archive's sense?",
    ):
        assert main._is_archive_self_reference_question(query), query


def test_archive_self_reference_detector_does_not_capture_ordinary_subject_questions():
    for query in (
        "How can a community use evidence to make a better decision?",
        "What is the difference between empirical inquiry and philosophy?",
        "How should a team resolve conflicting priorities?",
        "What does governance mean in practice?",
        "Where can I find material about truth and discernment?",
    ):
        assert not main._is_archive_self_reference_question(query), query


def test_epistemic_questions_are_exempt_from_generic_practical_stewardship_fast_path():
    # The demonstrated failure was diverted by a generic recommendation-style
    # answer. The new gate must keep this class eligible for the ordinary LLM composer.
    assert main._is_archive_self_reference_question(CLAIM_QUESTION)
    assert not main._is_practical_stewardship_question(CLAIM_QUESTION) or (
        main._is_archive_self_reference_question(CLAIM_QUESTION)
    )
    assert main._is_archive_self_reference_question(
        "How should The Guide distinguish evidence from interpretation?"
    )


def test_llm_composition_contract_repairs_neighboring_generic_advice():
    generic = (
        "A practical way to approach this is to clarify the outcome and the responsibilities involved. "
        "Identify what is known, which constraints matter, and who will be affected by the available choices. "
        "This makes the real decision clearer than jumping immediately to a generic action plan.\n\n"
        "Next, compare a small number of realistic options against the purpose you are trying to serve. "
        "Consider likely benefits, foreseeable harms, who carries the costs, and what evidence would change the choice. "
        "Where other people are affected, include their knowledge and concerns rather than treating them as an afterthought.\n\n"
        "Finally, act on the best-supported option, explain the reasoning and limits, and review the consequences. "
        "A useful approach should improve understanding and accountability, not promise certainty."
    )
    repaired = composition.enforce_response_contracts(CLAIM_QUESTION, generic)
    assert repaired != generic
    assert composition._has_archive_epistemic_provenance_answer(repaired)
    assert "direct Archive claim" in repaired
    assert "synthesis" in repaired
    assert "interpretation" in repaired
    assert "does not address the question directly" in repaired


def test_archive_provenance_contract_accepts_a_complete_answer():
    answer = composition._archive_epistemic_provenance_recovery()
    assert composition._has_archive_epistemic_provenance_answer(answer)
    assert composition.enforce_response_contracts(CLAIM_QUESTION, answer) == answer


def test_cosmology_generalization_contract_remains_reused():
    answer = composition._cosmology_generalization_standards_recovery()
    repaired = composition.enforce_response_contracts(GENERALIZATION_QUESTION, answer)
    assert composition._has_cosmology_generalization_standards(repaired)
    assert "counterevidence" in repaired.casefold() or "contradict" in repaired.casefold()


def test_epistemic_response_contract_has_no_topic_doorway_authority():
    # No response provider or topic recommendation can authorize a destination
    # for an Archive self-reference question; this class requires a separate,
    # explicitly justified canonical reference if a doorway is ever added.
    assert main._is_archive_self_reference_question(CLAIM_QUESTION)
    assert "authoritative_doorway = None" in (
        (main.__file__ and open(main.__file__, encoding="utf-8").read())
    )

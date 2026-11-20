"""Answer-first regression tests for the four epistemic categories."""

import deterministic_answer_recovery as recovery
import general_guide_composition as composition
import main


QUESTION = "What counts as evidence, interpretation, hypothesis, and normative judgment?"


def test_query_contract_recognizes_the_four_category_distinction_and_paraphrases():
    assert recovery.is_epistemic_category_distinction_question(QUESTION)
    assert recovery.is_epistemic_category_distinction_question(
        "How do evidence, interpretation, hypothesis, and value judgment differ?"
    )
    assert not recovery.is_epistemic_category_distinction_question("What is evidence?")


def test_recovery_defines_all_four_categories_and_their_boundaries():
    answer = recovery.compose_recovery(QUESTION)
    assert recovery.has_epistemic_category_distinction_explanation(answer)
    for phrase in (
        "Evidence is information",
        "Interpretation is the meaning",
        "A hypothesis is a provisional explanation",
        "A normative judgment evaluates what ought",
        "does not follow from facts alone",
        "evidence constrains interpretation",
    ):
        assert phrase.casefold() in answer.casefold()


def test_final_composition_boundary_repairs_retrieval_abstention():
    abstention = (
        "Your question asks what counts as evidence, interpretation, hypothesis, "
        "and normative judgment. I did not identify a directly relevant Archive resource."
    )
    answer = composition.enforce_response_contracts(QUESTION, abstention)
    assert recovery.has_epistemic_category_distinction_explanation(answer)
    assert "did not identify a directly relevant Archive resource" not in answer


def test_live_basic_inquiry_answers_before_archive_retrieval_or_provider(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Conceptual answer formation must not depend on Archive retrieval or provider.")

    monkeypatch.setattr(main.use_core, "fetch_canonical_context", forbidden)
    monkeypatch.setattr(main, "route_with_model_bank", forbidden)

    payload = main._basic_inquiry_response(QUESTION)
    assert recovery.has_epistemic_category_distinction_explanation(payload["response"])
    assert payload["processing"] == "guide_epistemic_category_distinction_deterministic"
    assert payload["route_source"] == "guide_epistemic_category_early_boundary"
    assert payload["response_provenance"]["llm_invoked"] is False
    assert payload["answer_basis"]["kind"] == "general_knowledge"
    assert payload["recommendation"] is None
    assert payload["canonical_doorway"] is None


def test_answer_floor_accepts_the_complete_conceptual_response():
    from gold_star_response_floor import apply_response_floor_boundary

    payload = main._basic_inquiry_response(QUESTION)
    safe, status = apply_response_floor_boundary(QUESTION, payload, 200)

    assert status == 200
    assert recovery.has_epistemic_category_distinction_explanation(safe["response"])
    assert safe["gold_star_v2_quality_floor"]["status"] != "fail"

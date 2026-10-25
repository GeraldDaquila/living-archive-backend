import pytest

from general_guide_composition import (
    _requires_method_comparison,
    enforce_response_contracts,
)


QUESTION = (
    "How do empirical inquiry, systems analysis, philosophy, and "
    "contemplative reflection differ?"
)


def test_method_comparison_is_recognized_without_capturing_single_term_lookups():
    assert _requires_method_comparison(QUESTION)
    assert not _requires_method_comparison("What is empirical inquiry?")
    assert not _requires_method_comparison("Open the Glossary for philosophy")


def test_method_comparison_rejects_generic_problem_solving_advice():
    generic = (
        "A practical way to approach these topics is to define the outcome you want, "
        "identify the main constraint, and choose one step small enough to test. "
        "Before acting, consider who else is affected and what could go wrong. "
        "Check the result against the original goal and adjust rather than assuming "
        "the first attempt must be final."
    )
    recovered = enforce_response_contracts(QUESTION, generic)
    assert recovered != generic
    assert "Empirical inquiry" in recovered
    assert "Systems analysis" in recovered
    assert "Philosophy" in recovered
    assert "Contemplative reflection" in recovered
    assert len(recovered.split("\n\n")) == 3


def test_method_comparison_requires_three_paragraphs_and_all_four_methods():
    incomplete = (
        "Empirical inquiry uses observation and evidence, while systems analysis "
        "examines relationships and feedback loops.\n\n"
        "Philosophy clarifies concepts and examines reasons for belief."
    )
    recovered = enforce_response_contracts(QUESTION, incomplete)
    assert len(recovered.split("\n\n")) == 3
    assert "Contemplative reflection" in recovered


def test_method_comparison_accepts_substantive_coverage_of_all_four_methods():
    answer = (
        "Empirical inquiry investigates what can be observed, measured, or tested, "
        "using evidence to evaluate claims. Systems analysis examines how parts "
        "interact, including relationships and feedback loops that shape a larger whole.\n\n"
        "Philosophy clarifies concepts and examines the reasons, assumptions, and "
        "values behind claims. Contemplative reflection attends to lived experience "
        "and awareness, helping a person notice habitual interpretations that might "
        "otherwise go unexamined.\n\n"
        "The approaches can complement one another without being interchangeable: "
        "empirical inquiry tests claims against observation, systems analysis maps "
        "interdependence, philosophy evaluates concepts and reasons, and contemplative "
        "reflection explores experience. Each has strengths and limits, so the useful "
        "choice depends on the question being asked."
    )
    assert enforce_response_contracts(QUESTION, answer) == answer

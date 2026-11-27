from pathlib import Path
import inspect

import general_guide_composition as composition
from humility_spiritual_maturity_contract import (
    evaluate_humility_spiritual_maturity_response,
    is_humility_spiritual_maturity_question,
)


QUERY = "What is the relationship between humility and spiritual maturity?"
COMPLETE_ANSWER = (
    "Humility supports spiritual maturity because it keeps a person willing to learn, "
    "make an honest self-appraisal, accept correction, and remain open to others. "
    "Spiritual maturity is visible in lived conduct: responsibility, accountability, "
    "and care in relationships, rather than a status someone claims. Humility is not "
    "self-erasure, diminished self-worth, self-contempt, passivity, blind obedience, "
    "or automatic compliance; it does not mean surrendering appropriate boundaries. "
    "Humility alone does not guarantee maturity; it must be expressed in how a person acts."
)


def test_humility_relationship_question_is_narrowly_classified():
    assert is_humility_spiritual_maturity_question(QUERY)
    assert is_humility_spiritual_maturity_question(
        "How do humility and spiritual maturity relate to one another?"
    )
    assert not is_humility_spiritual_maturity_question("What does humility mean?")
    assert not is_humility_spiritual_maturity_question("What is spiritual maturity?")


def test_complete_humility_relationship_answer_passes_shared_contract():
    report = evaluate_humility_spiritual_maturity_response(QUERY, COMPLETE_ANSWER)
    assert report["applies"] is True
    assert report["passed"] is True
    assert report["missing"] == []


def test_humility_relationship_answer_must_preserve_learning_agency_and_boundaries():
    weak = (
        "Humility supports spiritual maturity because people learn from experience. "
        "Spiritual maturity is shown in daily conduct. Humility alone does not guarantee maturity."
    )
    report = evaluate_humility_spiritual_maturity_response(QUERY, weak)
    assert report["passed"] is False
    assert "preserves_appropriate_boundaries" in report["missing"]
    assert "not_passivity_or_automatic_compliance" in report["missing"]
    assert "not_self_erasure_or_self_contempt" in report["missing"]


def test_provider_prompt_and_admission_parser_share_the_humility_contract():
    parser_source = inspect.getsource(composition._parse_factory)
    assert "evaluate_humility_spiritual_maturity_response" in parser_source
    assert "humility/spiritual-maturity answer is incomplete" in parser_source
    assert "HUMILITY AND SPIRITUAL MATURITY:" in composition._GENERAL_GUIDE_SYSTEM_COMPACT
    assert "humility supports spiritual maturity" in composition._GENERAL_GUIDE_SYSTEM_COMPACT

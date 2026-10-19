"""Regression tests for question-specific stewardship conflict recommendations."""
import main as use_main


QUERY = "What does stewardship look like when people disagree about what is worth protecting?"


def test_conflict_query_rejects_generic_stewardship_landing_page():
    generic = {
        "title": "Core Structure",
        "text": "An overview of the structure and foundations of the Living Archive.",
        "url": "https://geralddaquila.com/core-structure/",
    }
    assert not use_main._stewardship_conflict_candidate_has_direct_fit(QUERY, generic)


def test_conflict_query_accepts_direct_fit_stewardship_resource():
    relevant = {
        "title": "Applied Stewardship Toolkit",
        "text": (
            "When people disagree, identify competing values and what each person "
            "is protecting. Examine trade-offs and use a fair decision-making process "
            "to resolve conflict and revisit decisions as evidence changes."
        ),
        "url": "https://geralddaquila.com/applied-stewardship-toolkit/",
    }
    assert use_main._stewardship_conflict_candidate_has_direct_fit(QUERY, relevant)


def test_conflict_query_rejects_relevant_title_without_conflict_evidence():
    weak = {
        "title": "Applied Stewardship Toolkit",
        "text": "Stewardship means taking care of entrusted resources responsibly.",
        "url": "https://geralddaquila.com/applied-stewardship-toolkit/",
    }
    assert not use_main._stewardship_conflict_candidate_has_direct_fit(QUERY, weak)


def test_comparison_specific_guard_remains_active():
    query = "What is the difference between responsibility and stewardship?"
    generic = {
        "title": "Core Structure",
        "text": "A general introduction to the Living Archive.",
    }
    direct = {
        "title": "Responsibility and Stewardship",
        "text": "Responsibility defines duties; stewardship explains how care is exercised.",
    }
    assert not use_main._comparative_candidate_has_direct_fit(query, generic)
    assert use_main._comparative_candidate_has_direct_fit(query, direct)


def test_non_conflict_stewardship_question_is_not_overfiltered():
    query = "What does stewardship mean?"
    generic = {
        "title": "Applied Stewardship Toolkit",
        "text": "Stewardship means caring for what has been entrusted to us.",
    }
    assert use_main._stewardship_conflict_candidate_has_direct_fit(query, generic)

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


FUNDING_QUERY = "How should a community decide which of two competing priorities deserves funding when neither can be fully supported?"


def test_funding_priority_query_rejects_architecture_of_identity():
    unrelated = {
        "title": "The Architecture of Identity",
        "text": "An exploration of identity, belonging, and the formation of personal and collective meaning.",
        "url": "https://geralddaquila.com/the-architecture-of-identity/",
    }
    assert not use_main._resource_allocation_candidate_has_direct_fit(FUNDING_QUERY, unrelated)


def test_funding_priority_query_accepts_direct_allocation_resource():
    relevant = {
        "title": "Funding Priorities and Resource Allocation",
        "text": (
            "When resources are limited, communities can compare competing needs, "
            "set transparent decision criteria, weigh trade-offs, and allocate funding "
            "through a fair process."
        ),
        "url": "https://geralddaquila.com/funding-priorities/",
    }
    assert use_main._resource_allocation_candidate_has_direct_fit(FUNDING_QUERY, relevant)


def test_funding_priority_gate_does_not_filter_unrelated_queries():
    query = "What does identity mean?"
    unrelated = {
        "title": "The Architecture of Identity",
        "text": "An exploration of identity and belonging.",
    }
    assert use_main._resource_allocation_candidate_has_direct_fit(query, unrelated)


def test_stewardship_conflict_guard_uses_real_word_boundaries():
    generic = {
        "title": "Core Structure",
        "text": "An overview of the foundations of the Living Archive.",
    }
    assert not use_main._stewardship_conflict_candidate_has_direct_fit(QUERY, generic)


def test_funding_priority_without_relevant_resource_gets_bounded_answer(monkeypatch):
    monkeypatch.setattr(use_main.use_core, "context_blocks_to_documents", lambda _blocks: [])
    result = use_main._basic_inquiry_round1_deterministic_response(
        FUNDING_QUERY,
        {},
        {"context_blocks": ""},
        recommendation_available=False,
    )
    response = result["response"].casefold()
    assert result["provider"] == "bounded_funding_priority_recovery"
    assert "transparent criteria" in response
    assert "consequences of delaying" in response
    assert "who would be affected" in response
    assert "trade-offs" in response
    assert "general decision framework" in response
    assert "sufficiently direct archive resource" in response
    assert result["doorway_title"] == ""
    assert "couldn't verify a reliable answer" not in response


def test_funding_priority_recovery_does_not_invent_canonical_evidence(monkeypatch):
    monkeypatch.setattr(use_main.use_core, "context_blocks_to_documents", lambda _blocks: [])
    result = use_main._basic_inquiry_round1_deterministic_response(
        FUNDING_QUERY,
        {},
        {"context_blocks": ""},
        recommendation_available=False,
    )
    assert "Archive supplied a definitive answer" in result["response"]
    assert result["doorway_title"] == ""

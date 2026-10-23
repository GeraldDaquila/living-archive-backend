"""Regression tests for multi-concept topic relevance at the outward recommendation boundary."""

import main


QUERY = (
    "How do political dynasties, public institutions, and local accountability "
    "interact in the Philippines?"
)


def test_topic_fit_rejects_country_only_cultural_decoy():
    decoy = {
        "title": "The Philippines’ Fascination with Beauty Pageants: Soft Power and Gender Equity",
        "url": "https://geralddaquila.com/2025/06/05/the-philippines-fascination-with-beauty-pageants/",
        "text": (
            "Pageants in the Philippines shape cultural identity, gender equity, "
            "tourism, and international representation."
        ),
    }
    assert not main._topic_specific_candidate_fit(QUERY, decoy)
    assert not main._eligible_outward_doc(
        QUERY, decoy, main._base._inquiry_profile(QUERY), min_relevance=2
    )


def test_topic_fit_accepts_direct_political_dynasties_and_accountability_evidence():
    candidate = {
        "title": "Political Dynasties in the Philippines",
        "url": "https://geralddaquila.com/political-dynasties/",
        "text": (
            "Political dynasties shape local power. Public institutions can be "
            "weakened when accountability is limited. Local accountability and "
            "institutional checks affect how governance works."
        ),
    }
    assert main._topic_specific_candidate_fit(QUERY, candidate)
    assert main._eligible_outward_doc(
        QUERY, candidate, main._base._inquiry_profile(QUERY), min_relevance=2
    )


def test_topic_fit_does_not_overconstrain_single_anchor_queries():
    query = "How does governance work in the Philippines?"
    candidate = {
        "title": "A General Introduction to Governance",
        "url": "https://geralddaquila.com/governance-introduction/",
        "text": "This resource introduces governance and how public decisions are made.",
    }
    assert main._topic_specific_candidate_fit(query, candidate)


def test_outward_response_boundary_rejects_complete_and_truncated_html():
    assert main._basic_inquiry_contains_html_markup(
        '<a href="https://geralddaquila.com/example/">Open</a>'
    )
    assert main._basic_inquiry_contains_html_markup(
        '<a href="https://geralddaquila.com/2025/05/21/political-dynasties”'
    )
    assert not main._basic_inquiry_contains_html_markup(
        "Stewardship means caring for what has been entrusted to us."
    )


def test_political_dynasties_question_rejects_general_institutions_decoy():
    decoy = {
        "title": "Designing Human-Scale Institutions for the 21st Century",
        "url": "https://geralddaquila.com/2026/06/03/designing-human-scale-institutions-for-the-21st-century/",
        "text": (
            "Institutions and accountability are important for good governance. "
            "Public institutions need to serve communities and sustain shared decisions."
        ),
    }
    assert not main._topic_specific_candidate_fit(QUERY, decoy)

def test_deterministic_public_governance_recovery_answers_when_provider_is_unavailable():
    query = (
        "How do political dynasties, public institutions, and local accountability "
        "interact in the Philippines?"
    )
    result = main._basic_inquiry_round1_deterministic_response(
        query, {}, {"context_blocks": ""}
    )
    response = result["response"].casefold()
    assert result["provider"] == "bounded_public_governance_recovery"
    assert "political dynasties" in response
    assert "public institutions" in response
    assert "accountability" in response
    assert "recommendation below" not in response
    assert result["doorway_title"] == ""


def test_deterministic_recovery_does_not_promise_archive_recommendation_without_one():
    result = main._basic_inquiry_round1_deterministic_response(
        "Explain a highly specific question with no available source.",
        {},
        {"context_blocks": ""},
        recommendation_available=False,
    )
    assert "recommendation below" not in result["response"].casefold()
    assert "sufficiently relevant archive resource" in result["response"].casefold()


def test_canonical_primary_prefers_exact_subject_title_over_long_adjacent_article():
    query = "What does the Living Archive say about becoming fully human?"
    adjacent = {
        "title": "Truth in the Age of AI: Why Discernment Is Becoming a Survival Skill",
        "url": "https://geralddaquila.com/2026/10/19/truth-in-the-age-of-ai-why-discernment-is-becoming-a-survival-skill/",
        "text": (
            "Becoming fully human requires discernment in an age of artificial intelligence. "
            "Human life, human judgment, and human flourishing are discussed at length. "
            "The article returns repeatedly to discernment, technology, and survival."
        ),
    }
    direct = {
        "title": "Becoming Fully Human",
        "url": "https://geralddaquila.com/2026/10/05/the-architecture-of-human-development/",
        "text": (
            "Becoming fully human is explored through the architecture of human development. "
            "The resource considers human existence, growth, and the conditions of becoming fully human."
        ),
    }
    selected = main._canonical_primary_from_docs(
        [adjacent, direct], query, main._base._inquiry_profile(query)
    )
    assert selected is direct

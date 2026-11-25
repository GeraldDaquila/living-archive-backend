"""Regression tests for behavior-preserving Guide doorway eligibility diagnostics."""

import main


QUERY = "What makes an institution legitimate?"
PROFILE = {}


def test_institutional_legitimacy_selector_reports_invalid_candidate_reason():
    accepted, reason = main._evaluate_outward_doc_eligibility(
        QUERY,
        {"title": "Institutional legitimacy", "url": "http://not-canonical.example/resource"},
        PROFILE,
        min_relevance=2,
    )
    assert accepted is False
    assert reason == "invalid_title_or_canonical_url"


def test_institutional_legitimacy_selector_rejects_geographic_decoy_explicitly():
    candidate = {
        "title": "Philippine Institutions and Public Governance",
        "url": "https://geralddaquila.com/philippine-institutions/",
        "text": "Institutional legitimacy in Philippine institutions, governance, public systems, policy, and civic accountability.",
    }
    accepted, reason = main._evaluate_outward_doc_eligibility(
        QUERY, candidate, PROFILE, min_relevance=2
    )
    assert accepted is False
    assert reason == "geographic_scope_mismatch"


def test_boolean_eligibility_wrapper_preserves_evaluator_decision():
    candidates = [
        None,
        {"title": "Institutional legitimacy", "url": "not-a-url"},
        {
            "title": "Philippine Institutions and Public Governance",
            "url": "https://geralddaquila.com/philippine-institutions/",
            "text": "Institutional legitimacy in Philippine institutions, governance, public systems, policy, and civic accountability.",
        },
        {
            "title": "Institutional Legitimacy and Public Trust",
            "url": "https://geralddaquila.com/institutional-legitimacy/",
            "text": (
                "Institutional legitimacy depends on public trust, accountability, "
                "transparency, consent, representation, due process, and the ability "
                "to correct decisions when institutions cause harm."
            ),
        },
    ]
    for candidate in candidates:
        accepted, _reason = main._evaluate_outward_doc_eligibility(
            QUERY, candidate, PROFILE, min_relevance=2
        )
        assert main._eligible_outward_doc(
            QUERY, candidate, PROFILE, min_relevance=2
        ) is accepted


def test_selector_diagnostics_are_bounded_and_do_not_change_selected_result():
    candidates = [
        {
            "title": "Philippine Institutions and Public Governance",
            "url": "https://geralddaquila.com/philippine-institutions/",
            "text": "Institutional legitimacy in Philippine institutions, governance, public systems, policy, and civic accountability.",
        },
        {
            "title": "Institutional Legitimacy and Public Trust",
            "url": "https://geralddaquila.com/institutional-legitimacy/",
            "text": (
                "Institutional legitimacy depends on public trust, accountability, "
                "transparency, consent, representation, due process, and the ability "
                "to correct decisions when institutions cause harm."
            ),
        },
    ]
    baseline = main._canonical_primary_from_docs(candidates, QUERY, PROFILE)
    diagnostics = {}
    observed = main._canonical_primary_from_docs(
        candidates, QUERY, PROFILE, diagnostics=diagnostics
    )
    assert observed == baseline
    assert diagnostics["candidate_count"] == len(candidates)
    assert diagnostics["eligible_count"] + sum(
        diagnostics["rejection_counts"].values()
    ) == len(candidates)
    assert len(diagnostics["rejected_url_fingerprints"]) <= 8
    assert all(len(item) == 12 for item in diagnostics["rejected_url_fingerprints"])

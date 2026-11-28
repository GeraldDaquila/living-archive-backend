"""Regression tests for question-specific archival doorway relevance."""

import main


QUERY = "How can a digital archive preserve context rather than merely store content?"

ARCHIVAL_RESOURCE = {
    "title": "Preserving Context in Digital Archives",
    "url": "https://geralddaquila.com/digital-archive-context/",
    "text": (
        "Digital archival practice preserves provenance, metadata, original order, "
        "custody history, and relationships among records so future readers can "
        "interpret records in context."
    ),
}

NESARA_DECOY = {
    "title": "What Is NESARA and GESARA? Origins, Claims, and Why the Theory Keeps Resurfacing",
    "url": "https://geralddaquila.com/2026/10/19/nesara-gesara-a-vision-for-global-financial-reform-amid-systemic-discontent/",
    "text": (
        "This article explains the origins and history of the claims, the context "
        "in which they resurfaced, and the content of the theory. It discusses "
        "financial systems, public claims, and preservation of historical context."
    ),
}


def test_digital_archive_query_accepts_a_resource_with_archival_domain_evidence():
    accepted, reason = main._evaluate_outward_doc_eligibility(
        QUERY, ARCHIVAL_RESOURCE, {}, min_relevance=2
    )
    assert accepted, reason


def test_digital_archive_query_rejects_nesara_decoy_with_generic_context_overlap():
    accepted, reason = main._evaluate_outward_doc_eligibility(
        QUERY, NESARA_DECOY, {}, min_relevance=2
    )
    assert not accepted
    assert reason == "digital_archiving_subject_mismatch"


def test_digital_archive_query_fails_closed_when_candidate_has_only_generic_vocabulary():
    candidate = {
        "title": "Systems, History, and Context",
        "url": "https://geralddaquila.com/systems-history-context/",
        "text": "A discussion of systems, historical context, preservation, and content.",
    }
    accepted, reason = main._evaluate_outward_doc_eligibility(
        QUERY, candidate, {}, min_relevance=2
    )
    assert not accepted
    assert reason == "digital_archiving_subject_mismatch"


def test_archival_gate_does_not_capture_a_direct_nesara_question():
    query = "What Is NESARA and GESARA? What are the origins and claims?"
    assert main._digital_archiving_candidate_fit(query, NESARA_DECOY) is True

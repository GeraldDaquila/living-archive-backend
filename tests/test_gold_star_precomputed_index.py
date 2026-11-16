"""Regression tests for startup-precomputed Gold Star matching signatures."""

import gold_star_lessons as lessons


def test_select_lesson_uses_precomputed_structural_signatures(monkeypatch):
    monkeypatch.setattr(
        lessons,
        "_LESSONS",
        [
            {
                "id": "approved-test-lesson",
                "query": "How should institutions preserve accountability?",
                "known_theme": "governance accountability",
                "assertions": [],
                "terms": {"institution", "accountability"},
                "runtime_transfer": True,
                "deterministic_fallback_eligible": False,
                "reasoning_family": "institutional_governance",
                "transferable_discipline": "Make authority and review visible.",
                "abstention_boundary": "Do not assume misconduct without evidence.",
                "qualifying_context": "Institutional accountability and governance.",
                "variants": ["How can institutions remain accountable?"],
                "signature_terms": {
                    "institution", "account", "govern", "review", "author"
                },
                "variant_terms": {"institution", "remain", "account"},
                "reasoning_terms": {"institution", "govern"},
            }
        ],
    )

    selected = lessons.select_lesson(
        "How can institutional governance preserve accountability and review?"
    )

    assert selected is not None
    assert selected["benchmark_id"] == "approved-test-lesson"
    assert selected["exact"] is False


def test_select_lesson_still_abstains_when_no_precomputed_signature_matches(monkeypatch):
    monkeypatch.setattr(
        lessons,
        "_LESSONS",
        [
            {
                "id": "approved-test-lesson",
                "query": "How should institutions preserve accountability?",
                "known_theme": "governance accountability",
                "assertions": [],
                "terms": {"institution", "accountability"},
                "runtime_transfer": True,
                "deterministic_fallback_eligible": False,
                "reasoning_family": "institutional_governance",
                "transferable_discipline": "Make authority and review visible.",
                "abstention_boundary": "Do not assume misconduct without evidence.",
                "qualifying_context": "Institutional accountability and governance.",
                "variants": [],
                "signature_terms": {"institution", "account", "govern"},
                "variant_terms": set(),
                "reasoning_terms": {"institution", "govern"},
            }
        ],
    )

    assert lessons.select_lesson("What is the weather tomorrow?") is None

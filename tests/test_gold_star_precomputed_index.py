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
                "variant_terms": {"institutional", "remain", "accountabil"},
                "reasoning_terms": {"institutional", "governance"},
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



def test_precomputed_selector_handles_82_to_1000_lessons(monkeypatch):
    target = {
        "id": "target-lesson",
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
        "signature_terms": {"institutional", "accountabil", "governance", "review"},
        "variant_terms": set(),
        "reasoning_terms": {"institution", "govern"},
    }

    for size in (82, 150, 300, 500, 1000):
        fillers = [
            {
                "id": f"filler-{i}",
                "query": f"Unrelated synthetic topic {i}",
                "known_theme": f"synthetic filler category {i}",
                "assertions": [],
                "terms": {f"filler{i}"},
                "runtime_transfer": True,
                "deterministic_fallback_eligible": False,
                "reasoning_family": f"synthetic_family_{i}",
                "transferable_discipline": "Synthetic fixture only.",
                "abstention_boundary": "Synthetic fixture only.",
                "qualifying_context": f"Unrelated synthetic category {i}",
                "variants": [],
                "signature_terms": {f"filler{i}", f"synthetic{i}"},
                "variant_terms": set(),
                "reasoning_terms": {f"family{i}"},
            }
            for i in range(size - 1)
        ]
        monkeypatch.setattr(lessons, "_LESSONS", fillers + [target])
        selected = lessons.select_lesson(
            "How can institutional governance preserve accountability and review?"
        )
        assert selected is not None
        assert selected["benchmark_id"] == "target-lesson"

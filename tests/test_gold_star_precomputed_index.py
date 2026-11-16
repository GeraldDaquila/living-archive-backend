"""Regression tests for startup-precomputed Gold Star matching signatures."""

import gold_star_lessons as lessons


def _indexed_lesson(**overrides):
    item = {
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
    }
    item.update(overrides)
    # Derive fixture indexes with the same canonical functions used at startup.
    item["signature_terms"] = lessons._lesson_signature(item)
    item["variant_terms"] = lessons._concept_terms(" ".join(item["variants"]))
    item["reasoning_terms"] = lessons._concept_terms(item["reasoning_family"])
    return item


def test_select_lesson_uses_precomputed_structural_signatures(monkeypatch):
    monkeypatch.setattr(lessons, "_LESSONS", [_indexed_lesson()])

    selected = lessons.select_lesson(
        "How can institutional governance preserve accountability and review?"
    )

    assert selected is not None
    assert selected["benchmark_id"] == "approved-test-lesson"
    assert selected["exact"] is False


def test_select_lesson_still_abstains_when_no_precomputed_signature_matches(monkeypatch):
    unrelated = _indexed_lesson(
        query="How should institutions preserve accountability?",
        known_theme="governance accountability",
        reasoning_family="institutional_governance",
        qualifying_context="Institutional accountability and governance.",
        transferable_discipline="Make authority and review visible.",
        variants=[],
    )
    monkeypatch.setattr(lessons, "_LESSONS", [unrelated])

    assert lessons.select_lesson("What is the weather tomorrow?") is None


def test_precomputed_selector_handles_82_to_1000_lessons(monkeypatch):
    target = _indexed_lesson(id="target-lesson", variants=[])
    for size in (82, 150, 300, 500, 1000):
        fillers = [
            _indexed_lesson(
                id=f"filler-{i}",
                query=f"Unrelated synthetic topic {i}",
                known_theme=f"synthetic filler category {i}",
                reasoning_family=f"synthetic_family_{i}",
                qualifying_context=f"Unrelated synthetic category {i}",
                transferable_discipline="Synthetic fixture only.",
                abstention_boundary="Synthetic fixture only.",
                variants=[],
            )
            for i in range(size - 1)
        ]
        monkeypatch.setattr(lessons, "_LESSONS", fillers + [target])
        selected = lessons.select_lesson(
            "How can institutional governance preserve accountability and review?"
        )
        assert selected is not None
        assert selected["benchmark_id"] == "target-lesson"

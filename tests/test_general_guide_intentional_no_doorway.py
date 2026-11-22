import json

import pytest

import general_guide_gold_standards as standards


SPIRITUAL_BYPASSING = "What is spiritual bypassing, and why does it matter?"


def test_intentionally_none_approved_record_forbids_runtime_doorway():
    record = standards.resolve_exact_gold_standard(SPIRITUAL_BYPASSING)
    assert record is not None
    assert record["forbids_doorway"] is True
    assert record["doorway_title"] == ""
    assert record["doorway_url"] == ""


def test_intentionally_none_metadata_cannot_conflict_with_expected_doorway(tmp_path, monkeypatch):
    registry = {"records": [{
        "benchmark_id": "contradictory-doorway-fixture",
        "status": "USER_APPROVED_GOLD_STANDARD",
        "query": "Fixture question?",
        "expected_response": "Fixture answer.",
        "doorway_status": "INTENTIONALLY_NONE_APPROVED",
        "expected_doorway": {"title": "Contradictory doorway", "url": "https://geralddaquila.com/contradiction/"},
    }]}
    path = tmp_path / "gold_standard_registry.json"
    path.write_text(json.dumps(registry), encoding="utf-8")
    monkeypatch.setattr(standards, "_REGISTRY_PATH", path)
    with pytest.raises(ValueError, match="intentionally-none"):
        standards.load_approved_standards()


def test_intentionally_none_approved_record_survives_normalized_exact_query_variants():
    # Case, repeated whitespace, and terminal punctuation are transport/editor
    # variants; they must not bypass the exact approved no-doorway contract.
    variants = (
        "WHAT IS SPIRITUAL BYPASSING, AND WHY DOES IT MATTER?",
        "  What   is spiritual bypassing, and why does it matter?!  ",
    )
    for question in variants:
        record = standards.resolve_exact_gold_standard(question)
        assert record is not None
        assert record["forbids_doorway"] is True
        assert record["doorway_title"] == ""
        assert record["doorway_url"] == ""


def test_intentionally_none_approved_record_is_not_fuzzy_matched_to_related_questions():
    # A related question is not the frozen benchmark. It must not inherit its
    # exact-answer or no-doorway authority by semantic resemblance.
    assert standards.resolve_exact_gold_standard(
        "What is spiritual bypassing?"
    ) is None

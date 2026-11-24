import json
from pathlib import Path

from general_guide_gold_standards import resolve_exact_gold_standard

FIXTURE = Path(__file__).parent / "fixtures" / "general_guide_system_vs_separate_problems_gold_standard.json"


def _canonical_registry_record(fixture):
    registry_path = Path(__file__).resolve().parents[1] / "docs" / "qa" / "gold_star_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    return next(
        record for record in registry["records"]
        if record.get("benchmark_id") == fixture["benchmark_id"]
    )


def test_system_concept_is_registered_as_user_approved_gold_standard():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    canonical = _canonical_registry_record(fixture)
    resolved = resolve_exact_gold_standard(fixture["query"])
    assert resolved is not None
    assert resolved["benchmark_id"] == fixture["benchmark_id"]
    assert resolved["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert resolved["expected_response"] == canonical["expected_response"]
    expected_doorway = canonical.get("expected_doorway") or {}
    assert resolved["doorway_title"] == expected_doorway.get("title", "")
    assert resolved["doorway_url"] == expected_doorway.get("url", "")


def test_system_concept_gold_standard_preserves_three_paragraphs_and_fsd_boundary():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    canonical = _canonical_registry_record(fixture)
    answer = canonical["expected_response"]
    assert len([p for p in answer.split("\n\n") if p.strip()]) == 3
    assert "Not every cluster of problems is one system" in answer
    assert "should not replace the answer to the conceptual question" in answer

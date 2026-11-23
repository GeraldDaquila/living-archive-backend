import json
from pathlib import Path

from general_guide_gold_standards import resolve_exact_gold_standard

FIXTURE = Path(__file__).parent / "fixtures" / "general_guide_stewardship_living_archive_meaning_gold_standard.json"
REGISTRY = Path(__file__).resolve().parents[1] / "docs" / "qa" / "gold_standard_registry.json"


def _approved_record(fixture):
    records = json.loads(REGISTRY.read_text(encoding="utf-8"))["records"]
    return next(record for record in records if record["benchmark_id"] == fixture["benchmark_id"])


def test_living_archive_stewardship_meaning_is_registered_as_user_approved():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    resolved = resolve_exact_gold_standard(fixture["query"])
    assert resolved is not None
    assert resolved["benchmark_id"] == fixture["benchmark_id"]
    assert resolved["status"] == "USER_APPROVED_GOLD_STANDARD"
    canonical = _approved_record(fixture)
    assert resolved["expected_response"] == canonical["expected_response"]
    assert resolved["doorway_title"] == ""
    assert resolved["doorway_url"] == ""

def test_living_archive_stewardship_meaning_preserves_three_paragraph_gold_standard():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    answer = _approved_record(fixture)["expected_response"]
    paragraphs = [p for p in answer.split("\n\n") if p.strip()]
    assert len(paragraphs) == 3
    for phrase in (
        "stewardship follows understanding",
        "personal interpretation",
        "neither control nor unlimited self-sacrifice",
        "those who come after",
    ):
        assert phrase in answer.casefold()

def test_living_archive_stewardship_meaning_does_not_revert_to_glossary_handoff():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    answer = fixture["expected_response"]
    assert len(answer) > 900
    assert "glossary" not in answer.casefold()

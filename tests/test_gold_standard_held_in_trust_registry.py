import json
from pathlib import Path

from general_guide_gold_standards import resolve_exact_gold_standard

FIXTURE = Path(__file__).parent / "fixtures" / "general_guide_held_in_trust_gold_standard.json"
REGISTRY = Path(__file__).resolve().parents[1] / "docs" / "qa" / "gold_standard_registry.json"


def _approved_record(fixture):
    records = json.loads(REGISTRY.read_text(encoding="utf-8"))["records"]
    return next(record for record in records if record["benchmark_id"] == fixture["benchmark_id"])


def test_held_in_trust_answer_is_registered_as_user_approved():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    resolved = resolve_exact_gold_standard(fixture["query"])
    assert resolved is not None
    assert resolved["benchmark_id"] == fixture["benchmark_id"]
    assert resolved["status"] == "USER_APPROVED_GOLD_STANDARD"
    canonical = _approved_record(fixture)
    assert resolved["expected_response"] == canonical["expected_response"]
    assert resolved["doorway_title"] == canonical["expected_doorway"]["title"]
    assert resolved["doorway_url"] == canonical["expected_doorway"]["url"]


def test_held_in_trust_gold_standard_has_three_paragraphs_and_core_concepts():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    answer = _approved_record(fixture)["expected_response"]
    assert len([p for p in answer.split("\n\n") if p.strip()]) == 3
    for phrase in ("held in trust", "purpose for which something was entrusted", "misuse or neglect", "authority actually granted", "authority ends"):
        assert phrase in answer.casefold()


def test_held_in_trust_doorway_is_canonical_and_not_legacy_inferred():
    resolved = resolve_exact_gold_standard("How does one identify what is being held in trust in a given situation?")
    assert resolved["doorway_url"] == "https://geralddaquila.com/2026/08/19/the-stewardship-age-why-stewardship-will-define-the-twenty-first-century/"
    assert resolved["doorway_title"] == "The Stewardship Age"

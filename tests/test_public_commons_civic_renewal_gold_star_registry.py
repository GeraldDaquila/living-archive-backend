import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_ID = "general-guide-public-commons-civic-renewal-2026-11-24"
QUESTION = "What is the role of public commons in civic renewal?"


def test_public_commons_civic_renewal_gold_star_is_unique_and_approved():
    registry = json.loads((ROOT / "docs/qa/gold_standard_registry.json").read_text())
    matches = [r for r in registry["records"] if r.get("query") == QUESTION]
    assert len(matches) == 1
    record = matches[0]
    assert record["benchmark_id"] == BENCHMARK_ID
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["runtime_transfer"] is True
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["expected_doorway"] is None
    assert record["doorway_status"] == "NOT_EVALUATED"


def test_public_commons_civic_renewal_gold_star_preserves_exact_live_answer_and_boundaries():
    registry = json.loads((ROOT / "docs/qa/gold_standard_registry.json").read_text())
    record = next(r for r in registry["records"] if r.get("benchmark_id") == BENCHMARK_ID)
    answer = record["expected_response"]
    assert answer.startswith("Public commons are resources, spaces, institutions")
    assert "Their role in civic renewal is" in answer
    assert "Access can be unequal" in answer
    assert "not a claim that it is a formal Living Archive definition" in answer
    assert "implementation_commit" in record["provenance"]
    assert "does not by itself establish held-out adaptive transfer" in record["transfer_boundary"]


def test_public_commons_civic_renewal_gold_star_has_review_and_transfer_map_entries():
    reviews = json.loads((ROOT / "docs/qa/gold_star_qualitative_transfer_review.json").read_text())
    transfer_map = json.loads((ROOT / "docs/qa/gold_star_transferability_map.json").read_text())
    review = [e for e in reviews["entries"] if e.get("benchmark_id") == BENCHMARK_ID]
    mapped = [e for e in transfer_map["entries"] if e.get("benchmark_id") == BENCHMARK_ID]
    assert len(review) == 1
    assert review[0]["activation"] == "active_quality_contributor"
    assert len(mapped) == 1
    assert mapped[0]["family"] == "provider_exhaustion_answerability"
    assert mapped[0]["role"] == "cross_question_candidate"

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_ID = "general-guide-first-principles-gold-standard-2026-10-25"
QUERY = "What are first principles, and what are the Living Archive’s first principles?"


def test_first_principles_gold_standard_is_three_paragraphs_and_source_grounded():
    registry = json.loads(
        (ROOT / "docs" / "qa" / "gold_standard_registry.json").read_text(encoding="utf-8")
    )
    record = next(
        item for item in registry["records"]
        if item.get("benchmark_id") == BENCHMARK_ID
    )

    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == QUERY
    assert len(record["expected_response"].split("\\n\\n")) == 3
    assert record["expected_doorway"] == {
        "title": "First Principles",
        "url": "https://geralddaquila.com/first-principles/",
    }
    assert "not unquestionable doctrines" in record["expected_response"]
    assert "open to examination and revision" in record["expected_response"]
    assert record["provenance"]["source_path"] == "WordPress page 70305"

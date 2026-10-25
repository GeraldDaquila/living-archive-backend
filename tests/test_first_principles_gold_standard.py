import json
from pathlib import Path

from general_guide_gold_standards import resolve_exact_gold_standard


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_ID = "general-guide-first-principles-gold-standard-2026-10-25"
QUERY = "What are first principles, and what are the Living Archive’s first principles?"


def test_first_principles_gold_standard_has_three_substantive_paragraphs():
    registry = json.loads(
        (ROOT / "docs" / "qa" / "gold_standard_registry.json").read_text(encoding="utf-8")
    )
    record = next(item for item in registry["records"] if item.get("benchmark_id") == BENCHMARK_ID)
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    paragraphs = record["expected_response"].split("\\n\\n")
    assert len(paragraphs) == 3
    assert all(len(paragraph.strip()) > 100 for paragraph in paragraphs)
    assert record["expected_doorway"]["title"] == "First Principles"
    assert any("Does not ask the visitor for clarification" in item for item in record["assertions"])


def test_first_principles_gold_standard_is_used_by_exact_runtime_resolver():
    result = resolve_exact_gold_standard(QUERY)
    assert result is not None
    assert result["expected_response"].count("\\n\\n") == 2
    assert result["doorway_title"] == "First Principles"


def test_first_principles_gold_standard_does_not_capture_other_questions():
    assert resolve_exact_gold_standard("How do first principles work in physics?") is None

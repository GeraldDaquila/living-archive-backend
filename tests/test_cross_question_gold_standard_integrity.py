"""Regression tests for cross-question Gold Standard answer leakage."""

import json
from pathlib import Path

from general_guide_gold_standards import (
    find_cross_question_standard_response,
    resolve_exact_gold_standard,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "qa" / "gold_standard_registry.json"


def test_institutional_definition_is_not_reused_for_constitutional_reasoning():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    record = next(
        item for item in payload["records"]
        if item["benchmark_id"] == "general-guide-living-archive-definition-gold-standard-2026-10-25"
    )
    query = "What is constitutional reasoning in the Archive’s sense?"
    assert resolve_exact_gold_standard(query) is None
    leaked = find_cross_question_standard_response(query, record["expected_response"])
    assert leaked is not None
    assert leaked["benchmark_id"] == record["benchmark_id"]


def test_exact_gold_standard_question_remains_frozen_and_eligible():
    question = "What is the Living Archive, and what is it not?"
    expected = resolve_exact_gold_standard(question)
    assert expected is not None
    assert expected["benchmark_id"] == "general-guide-living-archive-definition-gold-standard-2026-10-25"
    assert find_cross_question_standard_response(question, expected["expected_response"]) is None


def test_final_response_boundary_rejects_cross_question_standard_reuse():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "_find_cross_question_standard_response(query, response)" in source
    assert "The Guide response integrity boundary: rejected cross-question" in source
    assert "constitutional reasoning" in source

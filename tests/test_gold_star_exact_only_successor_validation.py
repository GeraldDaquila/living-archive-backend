import copy
import json
from pathlib import Path

import pytest

from scripts.validate_gold_star_registry import (
    APPROVED_STATUS,
    validate_exact_only_successors,
)


def test_registry_exact_query_only_successor_is_valid_without_learning_transfer():
    root = Path(__file__).resolve().parents[1]
    registry = json.loads(
        (root / "docs/qa/gold_standard_registry.json").read_text(encoding="utf-8")
    )
    approved = [
        item for item in registry["records"]
        if item.get("status") == APPROVED_STATUS
    ]
    active = [item for item in approved if item.get("runtime_transfer") is True]

    exact_only = validate_exact_only_successors(approved, active)

    assert len(exact_only) == 1
    assert exact_only[0]["gold_star_capabilities"]["exact_answer_authority"] is True
    assert exact_only[0]["gold_star_capabilities"]["active_quality_contributor"] is False
    assert exact_only[0]["gold_star_capabilities"]["deterministic_fallback_eligible"] is False


def test_exact_query_only_successor_requires_bidirectional_predecessor_link():
    root = Path(__file__).resolve().parents[1]
    registry = json.loads(
        (root / "docs/qa/gold_standard_registry.json").read_text(encoding="utf-8")
    )
    approved = [
        item for item in registry["records"]
        if item.get("status") == APPROVED_STATUS
    ]
    active = [item for item in approved if item.get("runtime_transfer") is True]
    mutated = copy.deepcopy(approved)
    successor = next(
        item for item in mutated
        if item.get("runtime_transfer") is False
        and item.get("gold_star_capabilities", {}).get("exact_answer_authority") is True
    )
    successor["replaces_exact_query_runtime_authority_of"] = "missing-predecessor"

    with pytest.raises(SystemExit, match="valid exact-query-only successor"):
        validate_exact_only_successors(mutated, active)

"""Integrity checks for the governed decision-rights candidate-set benchmark.

These tests validate benchmark governance and source identity only. They do not
claim that the current runtime retrieves or applies the expected candidates.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "docs/qa/decision_rights_candidate_set_benchmark.json"
REGISTRY = ROOT / "docs/qa/gold_standard_registry.json"
REVIEWS = ROOT / "docs/qa/gold_star_qualitative_transfer_review.json"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_candidate_ids_are_unique_and_roles_are_valid():
    benchmark = _load(BENCHMARK)
    candidates = benchmark["candidate_roles"]
    ids = [item["benchmark_id"] for item in candidates]
    assert len(ids) == len(set(ids))
    assert {item["role"] for item in candidates} == {
        "core", "conditional", "related_conditional"
    }
    for item in candidates:
        assert item.get("rationale")
        if item["role"] != "core":
            assert item.get("condition")


def test_candidates_remain_approved_active_and_reviewed():
    benchmark = _load(BENCHMARK)
    registry = _load(REGISTRY)
    reviews = _load(REVIEWS)
    records = {
        item["benchmark_id"]: item
        for item in registry["records"]
        if item.get("status") == "USER_APPROVED_GOLD_STANDARD"
        and item.get("runtime_transfer") is True
    }
    review_entries = {
        item["benchmark_id"]: item for item in reviews["entries"]
    }
    for candidate in benchmark["candidate_roles"]:
        benchmark_id = candidate["benchmark_id"]
        assert benchmark_id in records, f"Not an active approved Gold Star: {benchmark_id}"
        assert benchmark_id in review_entries, f"Missing transfer review: {benchmark_id}"
        assert review_entries[benchmark_id].get("activation") == "active_quality_contributor"
        assert review_entries[benchmark_id].get("transferable_discipline")
        assert review_entries[benchmark_id].get("abstention_boundary")


def test_case_labels_reference_only_declared_candidates():
    benchmark = _load(BENCHMARK)
    candidate_ids = {item["benchmark_id"] for item in benchmark["candidate_roles"]}
    case_ids = [case["case_id"] for case in benchmark["cases"]]
    assert len(case_ids) == len(set(case_ids))
    for case in benchmark["cases"]:
        assert case.get("query")
        labelled = (
            case["expected_core"]
            + case["expected_conditional"]
            + case["expected_related_conditional"]
        )
        assert len(labelled) == len(set(labelled)), case["case_id"]
        assert set(labelled) <= candidate_ids, case["case_id"]
        assert isinstance(case["abstain"], bool)


def test_core_and_conditional_policy_is_explicit():
    benchmark = _load(BENCHMARK)
    candidates = {item["benchmark_id"]: item for item in benchmark["candidate_roles"]}
    core_ids = {key for key, value in candidates.items() if value["role"] == "core"}
    assert len(core_ids) == 3
    central = next(case for case in benchmark["cases"] if case["case_id"] == "central-question")
    assert set(central["expected_core"]) == core_ids
    assert central["expected_conditional"] == []
    assert central["expected_related_conditional"] == []
    assert all(case["abstain"] for case in benchmark["cases"] if case["case_id"].endswith("negative") or case["case_id"] == "underspecified-ambiguity")


def test_application_and_retrieval_are_separate_gates():
    benchmark = _load(BENCHMARK)
    gates = benchmark["evaluation_gates"]
    assert "candidate-set precision and recall" in gates["retrieval"]
    assert "delivered answer" in gates["application"]
    assert "not proof of application" in gates["application"]
    assert "No threshold changes" in gates["release"]

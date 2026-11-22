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


def test_canonical_initialization_baseline_is_not_misrepresented_as_independent_ground_truth():
    benchmark = _load(BENCHMARK)
    validation = benchmark["label_validation"]
    assert validation["status"] == "CANONICAL_INITIALIZATION_BASELINE_PENDING_RUNTIME_VALIDATION"
    assert validation["ground_truth_eligible"] is False
    decision_path = ROOT / validation["canonical_decision"]
    assert decision_path.is_file()
    decision = decision_path.read_text(encoding="utf-8").casefold()
    assert "waived their separate annotation/review right" in decision
    assert "initialization baseline" in decision
    assert "fully independent or blinded external review" in decision
    assert "does not authorize merging pr #1861" in decision


def test_canonical_reviewer_annotations_cover_every_query_candidate_pair():
    import csv
    packet = _load(ROOT / "docs/qa/decision_rights_independent_review_packet_2026-11-22.json")
    annotation_path = ROOT / "docs/qa/reviews/chatgpt_reviewer1_annotations_2026-11-22.csv"
    with annotation_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    expected_pairs = {
        (case["case_id"], candidate["candidate_label"])
        for case in packet["cases"]
        for candidate in packet["candidates"]
    }
    actual_pairs = {(row["case_id"], row["candidate_label"]) for row in rows}
    allowed = {"CORE", "CONDITIONAL", "RELATED_NOT_NEEDED", "NOT_RELEVANT", "INSUFFICIENT_CONTEXT"}
    assert len(rows) == len(expected_pairs) == 1032
    assert actual_pairs == expected_pairs
    assert all(row["reviewer_id"] for row in rows)
    assert all(row["disposition"] in allowed for row in rows)
    assert all(row["rationale"].strip() for row in rows)


def test_application_and_retrieval_are_separate_gates():
    benchmark = _load(BENCHMARK)
    gates = benchmark["evaluation_gates"]
    assert "candidate-set precision and recall" in gates["retrieval"]
    assert "delivered answer" in gates["application"]
    assert "not proof of application" in gates["application"]
    assert "No threshold changes" in gates["release"]



def test_blinded_review_packet_preserves_its_pinned_historical_inventory_snapshot():
    packet_path = ROOT / "docs/qa/decision_rights_independent_review_packet_2026-11-22.json"
    packet = _load(packet_path)
    registry = _load(REGISTRY)
    reviews = _load(REVIEWS)
    active = sorted(
        (
            item for item in registry["records"]
            if item.get("status") == "USER_APPROVED_GOLD_STANDARD"
            and item.get("runtime_transfer") is True
        ),
        key=lambda item: item["benchmark_id"],
    )
    review_ids = {item["benchmark_id"] for item in reviews["entries"]}
    assert packet["inventory_reconciliation"]["runtime_transfer_true"] == 129
    assert len(active) == 130
    assert packet["inventory_reconciliation"]["qualitative_review_entries"] == 129
    assert len(active) == 130
    assert all(item["benchmark_id"] in review_ids for item in active)
    assert "gs-2026-11-22-layered-answerability-calibrated-abstention" not in {item.get("benchmark_id") for item in packet["candidates"]}
    candidates = packet["candidates"]
    assert len(candidates) == len(active)
    assert [item["candidate_label"] for item in candidates] == [
        f"C{index:03d}" for index in range(1, len(active) + 1)
    ]
    assert all("benchmark_id" not in item for item in candidates)
    required_source_fields = (
        "approved_question", "known_theme", "reasoning_family",
        "transferable_discipline", "qualifying_context",
        "abstention_boundary", "activation",
    )
    for item in candidates:
        assert all(field in item for field in required_source_fields)
        assert all(
            item.get(field)
            for field in required_source_fields
            if field != "qualifying_context"
        )
        expected_gaps = [
            field for field in required_source_fields
            if not str(item.get(field) or "").strip()
        ]
        assert item["source_field_gaps"] == expected_gaps
    assert "must not infer" in packet["source_limitations"]
    benchmark = _load(BENCHMARK)
    assert packet["cases"] == [
        {"case_id": item["case_id"], "query": item["query"]}
        for item in benchmark["cases"]
    ]
    assert "expected_core" not in packet["cases"][0]
    assert all("semantic_score" not in item for item in candidates)


def test_independent_review_annotation_template_is_complete_and_blank():
    import csv
    template = ROOT / "docs/qa/decision_rights_independent_review_annotations_template_2026-11-22.csv"
    packet = _load(
        ROOT / "docs/qa/decision_rights_independent_review_packet_2026-11-22.json"
    )
    with template.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    expected_pairs = {
        (case["case_id"], candidate["candidate_label"])
        for case in packet["cases"]
        for candidate in packet["candidates"]
    }
    actual_pairs = {(row["case_id"], row["candidate_label"]) for row in rows}
    assert len(rows) == len(expected_pairs) == 1032
    assert actual_pairs == expected_pairs
    assert all(not row["reviewer_id"] for row in rows)
    assert all(not row["disposition"] for row in rows)
    assert all(not row["rationale"] for row in rows)
    assert all(
        row["disposition"] in {"", "CORE", "CONDITIONAL", "RELATED_NOT_NEEDED",
                               "NOT_RELEVANT", "INSUFFICIENT_CONTEXT"}
        for row in rows
    )

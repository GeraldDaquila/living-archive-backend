import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE_PATH = ROOT / "docs" / "qa" / "guide_learning_evaluation_set.json"
SCHEMA_PATH = ROOT / "docs" / "qa" / "guide_learning_lesson.schema.json"
REGISTRY_PATH = ROOT / "docs" / "qa" / "gold_standard_registry.json"

MANDATORY_FLOOR_STATUSES = {"USER_APPROVED_GOLD_STANDARD", "FROZEN_REFERENCE_ONLY"}


def test_learning_schema_and_evaluation_suite_are_versioned():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    suite = json.loads(SUITE_PATH.read_text(encoding="utf-8"))
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["properties"]["schema_version"]["const"] == "1.0.0"
    assert suite["suite_version"] == "1.1.0"
    assert suite["status"] == "LIVE_CAPTURED_HELDOUTS_HAVE_FAILURES_HUMAN_REVIEW_PENDING"


def test_registry_is_the_authoritative_gold_standard_floor():
    suite = json.loads(SUITE_PATH.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    baseline = suite["baseline"]
    assert baseline["source_of_truth"] == "docs/qa/gold_standard_registry.json"
    assert set(baseline["selection_policy"]["mandatory_floor_statuses"]) == MANDATORY_FLOOR_STATUSES

    selected = [
        record for record in registry["records"]
        if record.get("subsystem") == "general-purpose-guide"
        and record.get("status") in MANDATORY_FLOOR_STATUSES
    ]
    assert selected, "The mandatory floor must be derived from registry records, not duplicated manually."
    assert all(record.get("query") and record.get("expected_response") for record in selected)
    assert baseline["regression_rule"]
    assert baseline["reproducibility"]
    assert baseline["negative_controls"]

    # Diagnostic/recovered records are not silently promoted into the mandatory floor.
    for record in registry["records"]:
        if record.get("status") not in MANDATORY_FLOOR_STATUSES:
            assert record not in selected


def test_proposed_lessons_are_not_mistaken_for_approved_runtime_rules():
    suite = json.loads(SUITE_PATH.read_text(encoding="utf-8"))
    assert suite["lessons"]
    for lesson in suite["lessons"]:
        assert lesson["schema_version"] == "1.0.0"
        assert lesson["status"] == "proposed"
        assert lesson["approval"]["human_approved"] is False
        assert lesson["approval"]["approved_by"] is None
        assert lesson["approval"]["approved_at"] is None
        assert lesson["source_benchmark_ids"]
        assert lesson["applies_when"]
        assert lesson["does_not_apply_when"]
        assert lesson["evaluation_case_ids"]


def test_held_out_questions_remain_separate_from_registry_baseline():
    suite = json.loads(SUITE_PATH.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    registry_queries = {
        " ".join(record.get("query", "").casefold().split())
        for record in registry.get("records", [])
        if record.get("query")
    }
    cases = suite["cases"]
    case_ids = [case["case_id"] for case in cases]
    assert len(case_ids) == len(set(case_ids))
    assert cases
    for case in cases:
        assert case["split"] == "held_out"
        normalized_query = " ".join(case["query"].casefold().split())
        assert normalized_query not in registry_queries
        assert case["source_benchmark_ids"] == []
        assert case["critical_dimensions"]
        assert case["rubric"]


def test_every_lesson_references_existing_held_out_cases_and_known_dimensions():
    suite = json.loads(SUITE_PATH.read_text(encoding="utf-8"))
    case_ids = {case["case_id"] for case in suite["cases"]}
    known_dimensions = {
        "answer_first", "human_voice", "concrete_clarity", "archive_grounding",
        "general_knowledge_accuracy", "response_shape", "doorway_relevance",
        "uncertainty_honesty", "non_regression",
    }
    for lesson in suite["lessons"]:
        assert set(lesson["evaluation_case_ids"]) <= case_ids
        assert set(lesson["quality_dimensions"]) <= known_dimensions
        assert lesson["evidence_policy"]["authority"] in {
            "living_archive_canonical_source", "user_approved_gold_standard",
            "general_knowledge_reference", "mixed_with_explicit_separation",
        }


def test_learning_suite_does_not_claim_runtime_learning_or_change_frozen_core():
    suite = json.loads(SUITE_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    test_source = (ROOT / "tests" / "test_guide_learning_offline_evaluation.py").read_text(encoding="utf-8")
    assert "not a claim that model learning or automatic scoring is implemented" in suite["purpose"]
    assert "does not train or change runtime behavior" in schema["description"]
    parsed = ast.parse(test_source)
    imported_modules = {
        alias.name.split(".")[0]
        for node in ast.walk(parsed)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module.split(".")[0]
        for node in ast.walk(parsed)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "use_core" not in imported_modules


def test_human_review_rubric_has_critical_quality_dimensions_and_no_auto_approval():
    suite = json.loads(SUITE_PATH.read_text(encoding="utf-8"))
    rubric = suite["human_review_rubric"]
    dimension_ids = {dimension["id"] for dimension in rubric["dimensions"]}
    assert set(rubric["critical_dimensions"]) <= dimension_ids
    assert {"sentence_coherence", "paragraph_purpose_and_concision", "human_voice_and_respect",
            "archive_grounding_and_provenance", "cosmology_fidelity", "fractal_coherence",
            "doorway_relevance_and_timing"} <= dimension_ids
    assert "cannot approve a lesson" in rubric["review_gate"]


def test_human_review_rubric_never_promotes_proposed_lessons_automatically():
    suite = json.loads(SUITE_PATH.read_text(encoding="utf-8"))
    assert "human review" in suite["scoring_policy"]["human_review"]
    assert all(lesson["status"] == "proposed" for lesson in suite["lessons"])
    assert all(lesson["approval"]["human_approved"] is False for lesson in suite["lessons"])

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "qa" / "gold_standard_registry.json"
SCRIPT = ROOT / "scripts" / "qa" / "audit_gold_star_question_families.py"


def _module():
    spec = importlib.util.spec_from_file_location("gold_star_question_family_audit", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_question_family_audit_is_deterministic_and_does_not_mutate_registry():
    module = _module()
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    before = json.dumps(registry, sort_keys=True)
    first = module.build_audit(registry)
    second = module.build_audit(registry)
    after = json.dumps(registry, sort_keys=True)

    assert first == second
    assert before == after
    assert first["approved_record_count"] == sum(
        item.get("status") == "USER_APPROVED_GOLD_STANDARD"
        for item in registry["records"]
    )
    assert first["unique_normalized_question_family_count"] == 157
    assert first["repeated_question_family_count"] == 6
    assert first["review_required_family_count"] == 0
    assert first["identical_response_group_count"] == 0


def test_repeated_question_families_have_explicit_lineage_or_distinct_exemplar_status():
    report = _module().build_audit(json.loads(REGISTRY.read_text(encoding="utf-8")))
    by_ids = {frozenset(item["benchmark_ids"]): item for item in report["families"]}

    ai_staffing = by_ids[frozenset({
        "general-guide-integrated-institutional-judgment-ai-staffing-gold-star-2026-11-13",
        "gs-2026-11-17-ai-workforce-restructuring-successor-candidate",
    })]
    assert ai_staffing["family_type"] == "explicit_exact_query_successor_lineage"

    predictive = by_ids[frozenset({
        "general-guide-public-predictive-systems-constitutional-human-stewardship-gold-star-2026-11-13",
        "general-guide-public-predictive-systems-constitutional-human-stewardship-gold-star-successor-2026-11-17",
    })]
    assert predictive["family_type"] == "explicit_exact_query_successor_lineage"

    systems_map = by_ids[frozenset({
        "gs-2026-11-13-04-migrated-canonical-ledger",
        "general-guide-systems-map-useful-false-confidence-gold-standard-2026-11-15",
    })]
    assert systems_map["family_type"] == "explicit_successor_and_supersession_lineage"

    governance = by_ids[frozenset({
        "general-guide-governance-balance-structural-candidate-2026-11-24",
        "general-guide-governance-balance-consequence-aware-2026-11-24",
    })]
    assert governance["family_type"] == "explicit_paired_response_quality_exemplar"

    discernment = by_ids[frozenset({
        "general-guide-human-discernment-ai-governance-2026-11-28",
        "general-guide-human-discernment-ai-governance-doorway-refined-2026-11-28",
    })]
    assert discernment["family_type"] == "multiple_standalone_response_quality_exemplars"

    nonprofit = by_ids[frozenset({
        "general-guide-nonprofit-mission-care-operational-capacity-2026-11-28",
        "general-guide-nonprofit-mission-care-operational-capacity-doorway-2026-11-28",
        "general-guide-nonprofit-mission-care-trust-centered-gold-star-2026-11-28",
    })]
    assert nonprofit["family_type"] == "explicit_paired_response_quality_exemplar"
    assert nonprofit["distinct_response_count"] == 3


def test_question_normalization_is_conservative_and_unicode_aware():
    normalize = _module().normalize_question
    assert normalize("  How should governance balance stability, participation, and responsiveness? ") == (
        "how should governance balance stability, participation, and responsiveness"
    )
    assert normalize("A—B?") == "a-b"
    assert normalize("A  B!") == "a b"
    assert normalize("How should governance balance stability and participation?") != normalize(
        "How should governance balance stability, participation, and responsiveness?"
    )


def test_new_approval_requires_user_reviewed_question_family_disposition():
    module = _module()
    baseline = json.loads(REGISTRY.read_text(encoding="utf-8"))
    candidate = json.loads(json.dumps(baseline))
    record = json.loads(json.dumps(next(item for item in candidate["records"] if item.get("status") == "USER_APPROVED_GOLD_STANDARD")))
    record["benchmark_id"] = "test-new-family-requires-review"
    record["query"] = "A wholly new test question family?"
    record["user_reviewed_response"] = True
    record["explicit_user_elevation_approval"] = True
    candidate["records"].append(record)

    errors = module.validate_new_approval_reviews(candidate, baseline)
    assert any("missing question_family_review" in error for error in errors)


def test_new_approval_accepts_correct_new_family_review_and_rejects_wrong_family_id():
    module = _module()
    baseline = json.loads(REGISTRY.read_text(encoding="utf-8"))
    candidate = json.loads(json.dumps(baseline))
    record = json.loads(json.dumps(next(item for item in candidate["records"] if item.get("status") == "USER_APPROVED_GOLD_STANDARD")))
    record["benchmark_id"] = "test-new-family-reviewed"
    record["query"] = "A distinct test question family for governance?"
    record["user_reviewed_response"] = True
    record["explicit_user_elevation_approval"] = True
    normalized = module.normalize_question(record["query"])
    family_id = "qf-" + __import__("hashlib").sha256(normalized.encode("utf-8")).hexdigest()[:16]
    record["question_family_review"] = {
        "family_id": family_id,
        "classification": "NEW_QUESTION_FAMILY",
        "reviewed_by": "user",
        "reviewed_at": "2026-11-28",
        "rationale": "Reviewed as a genuinely distinct normalized question family.",
        "related_benchmark_ids": [],
    }
    candidate["records"].append(record)

    assert module.validate_new_approval_reviews(candidate, baseline) == []
    record["question_family_review"]["family_id"] = "qf-wrong"
    assert any("family_id does not match" in error for error in module.validate_new_approval_reviews(candidate, baseline))


def test_new_standalone_exemplar_must_disclose_every_same_question_record():
    module = _module()
    baseline = json.loads(REGISTRY.read_text(encoding="utf-8"))
    candidate = json.loads(json.dumps(baseline))
    existing = next(
        item for item in candidate["records"]
        if item.get("benchmark_id") == "general-guide-archive-cosmology-epistemic-discernment-2026-11-28"
    )
    record = json.loads(json.dumps(existing))
    record["benchmark_id"] = "test-new-cosmology-standalone-exemplar"
    record["user_reviewed_response"] = True
    record["explicit_user_elevation_approval"] = True
    normalized = module.normalize_question(record["query"])
    family_id = "qf-" + __import__("hashlib").sha256(normalized.encode("utf-8")).hexdigest()[:16]
    related = sorted([existing["benchmark_id"]])
    record["question_family_review"] = {
        "family_id": family_id,
        "classification": "STANDALONE_RESPONSE_QUALITY_EXEMPLAR",
        "reviewed_by": "user",
        "reviewed_at": "2026-11-28",
        "rationale": "Distinct approved response exemplar, not a duplicate record.",
        "related_benchmark_ids": related,
    }
    candidate["records"].append(record)

    assert module.validate_new_approval_reviews(candidate, baseline) == []
    record["question_family_review"]["related_benchmark_ids"] = []
    assert any("related_benchmark_ids" in error for error in module.validate_new_approval_reviews(candidate, baseline))

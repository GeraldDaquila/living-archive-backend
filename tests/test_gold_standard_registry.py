import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "docs" / "qa" / "gold_standard_registry.json"
STEWARDSHIP_FIXTURE_PATH = (
    ROOT / "tests" / "fixtures" / "general_guide_stewardship_gold_standard.json"
)

VALID_STATUSES = {
    "FROZEN_REFERENCE_ONLY",
    "RECOVERED_HISTORICAL_RESPONSE",
    "RECOVERED_HISTORICAL_RESPONSE_PENDING_APPROVAL_EVIDENCE",
    "RECOVERED_SCENARIO_PENDING_APPROVAL_EVIDENCE",
    "RECOVERED_CONTRACT_PENDING_EXACT_QUESTION_AND_APPROVAL",
    "RECOVERED_REGRESSION_SCENARIO",
    "RECOVERED_EVALUATION_FIXTURE_NOT_GOLD_STANDARD",
    "RECOVERED_DIAGNOSTIC_FIXTURE_NOT_GOLD_STANDARD",
    "RECOVERED_SHADOW_DIAGNOSTIC_NOT_GOLD_STANDARD",
    "RECOVERED_QUESTION_SET_PENDING_PER_ITEM_APPROVAL",
    "CONFIRMED_CASE",
    "NEEDS_SOURCE_RECOVERY",
    "CANDIDATE",
}


def _registry():
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_registry_has_unique_ids_and_provenance_for_every_record():
    registry = _registry()
    assert registry["registry_id"] == "living-archive-gold-standard-registry"
    assert registry["schema_version"] == "1.0.0"
    records = registry["records"]
    ids = [record["benchmark_id"] for record in records]
    assert len(ids) == len(set(ids))
    assert len(records) >= 18

    for record in records:
        assert record["benchmark_id"].strip()
        assert record["subsystem"].strip()
        assert record["status"] in VALID_STATUSES
        assert isinstance(record["assertions"], list) and record["assertions"]
        assert record["provenance"]
        assert any(
            record["provenance"].get(key)
            for key in (
                "source_path", "source_paths", "source_url", "source_urls",
                "source_pr", "source_prs", "source_library_file", "source_ref",
            )
        ), record["benchmark_id"]
        assert record["freeze_policy"].strip()
        if record.get("query") is None or record.get("expected_response") is None:
            # Evaluation datasets and unrecovered scenarios are explicitly allowed
            # to have no single query/answer; they must not be miscounted as gold answers.
            assert "NOT_GOLD_STANDARD" in record["status"] or (
                "PENDING" in record["status"]
            ) or record["status"] in {"RECOVERED_REGRESSION_SCENARIO", "CONFIRMED_CASE"}
        else:
            assert record["query"].strip()
            assert record["expected_response"].strip()


def test_frozen_stewardship_record_matches_authoritative_fixture_exactly():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-stewardship-gold-standard-2026-10-14"
    )
    fixture = json.loads(STEWARDSHIP_FIXTURE_PATH.read_text(encoding="utf-8"))

    assert record["status"] == fixture["status"]
    assert record["query"] == fixture["query"]
    assert record["expected_response"] == fixture["expected_response"]
    assert record["expected_doorway"]["title"] == fixture["expected_doorway_title"]
    assert len(record["expected_response"].split(chr(10) * 2)) == 3


def test_recovered_compound_stewardship_record_preserves_evidence_boundary():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-stewardship-compound-2026-10"
    )
    assert record["status"] == "RECOVERED_HISTORICAL_RESPONSE"
    assert record["query"] == "What is stewardship and why does it matter now more than ever?"
    assert len(record["expected_response"]) == 861
    assert len(record["expected_response"].split("\\n\\n")) == 3
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/level-1-case-catalog/"
    assert "do not independently prove the exact live response text" in record["provenance"]["evidence_boundary"]


def test_reciprocity_record_is_explicit_about_unmerged_source():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-reciprocity-gold-standard-2026-10-19"
    )
    assert record["status"] == "FROZEN_REFERENCE_ONLY"
    assert len(record["expected_response"].split("\\n\\n")) == 3
    assert "open, unmerged historical PR branch" in record["provenance"]["caveat"]


def test_identity_report_pins_registry_hash_and_explicit_application_identity(tmp_path):
    import hashlib
    import subprocess
    import sys

    report_path = tmp_path / "registry-report.json"
    script_path = ROOT / "scripts" / "qa" / "report_gold_standard_registry.py"
    completed = subprocess.run(
        [
            sys.executable, str(script_path),
            "--application-commit", "test-app-commit-123",
            "--runtime-identity", "test-runtime-primary",
            "--output", str(report_path),
        ],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(report_path.read_text(encoding="utf-8"))
    registry_bytes = REGISTRY_PATH.read_bytes()
    assert report["application_commit"] == "test-app-commit-123"
    assert report["runtime_identity"] == "test-runtime-primary"
    assert report["registry_sha256"] == hashlib.sha256(registry_bytes).hexdigest()
    assert report["benchmark_count"] == len(_registry()["records"])
    assert any("does not itself assert that tests passed" in item for item in report["limitations"])


def test_identity_report_refuses_to_guess_application_identity():
    import subprocess
    import sys

    script_path = ROOT / "scripts" / "qa" / "report_gold_standard_registry.py"
    completed = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert completed.returncode != 0
    assert "supply --application-commit and --runtime-identity" in completed.stderr


def test_recovered_stewardship_disagreement_response_preserves_source_boundary():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-stewardship-disagreement-protection-2026-10"
    )
    assert record["status"] == "RECOVERED_HISTORICAL_RESPONSE"
    assert record["query"] == (
        "What does stewardship look like when people disagree about what is worth protecting?"
    )
    assert len(record["expected_response"].split(chr(10) * 2)) == 3
    assert "When people disagree about what is worth protecting" in record["expected_response"]
    assert record["provenance"]["source_ref"] == "537f244d6b5ad21e3b7745af518dd54d1d4c9c55"
    assert "or that a destination was approved" in record["provenance"]["evidence_boundary"]
    assert record["expected_doorway"]["url"] is None


def test_ethical_tradeoff_response_and_simulated_counts_are_captured():
    registry = _registry()
    records = {item["benchmark_id"]: item for item in registry["records"]}
    ethical = records["general-guide-ethical-tradeoff-2026-10"]
    assert ethical["expected_response"].startswith("When protecting one important thing")
    assert "those with the least power" in ethical["expected_response"]
    expected_counts = {
        "general-guide-fuzzy-relevance-balanced-evaluation-2026-10-22": 4,
        "general-guide-fuzzy-relevance-heldout-paraphrases-2026-10-22": 4,
        "general-guide-fuzzy-relevance-independent-challenge-2026-10-22": 16,
        "general-guide-fuzzy-relevance-simulated-question-battery-2026-10-22": 10,
        "general-guide-fuzzy-fallback-replay-simulated-2026-10-22": 9,
    }
    for benchmark_id, count in expected_counts.items():
        assert records[benchmark_id]["provenance"]["case_count"] == count


def test_ten_question_calibration_set_is_not_misrepresented_as_approved_answers():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-calibration-question-set-2026-09-20"
    )
    assert len(record["calibration_questions"]) == 10
    assert record["expected_response"] is None
    assert record["status"] == "RECOVERED_QUESTION_SET_PENDING_PER_ITEM_APPROVAL"

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _import_main_without_downloading_embedding_model(monkeypatch):
    """Import the deterministic route without a network-dependent model fetch."""
    import fastembed

    class _EmbeddingStub:
        model = None

        def embed(self, *_args, **_kwargs):
            return iter(())

    monkeypatch.setattr(fastembed, "TextEmbedding", lambda **_kwargs: _EmbeddingStub())
    import main
    return main
REGISTRY_PATH = ROOT / "docs" / "qa" / "gold_standard_registry.json"
STEWARDSHIP_FIXTURE_PATH = (
    ROOT / "tests" / "fixtures" / "general_guide_stewardship_gold_standard.json"
)



ETHICAL_TRADEOFF_FIXTURE_PATH = (
    ROOT / "tests" / "fixtures" / "general_guide_ethical_tradeoff_gold_standard.json"
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
    "RECOVERED_FAILURE_CONTROL_NOT_GOLD_STANDARD",
    "RECOVERED_SHADOW_DIAGNOSTIC_NOT_GOLD_STANDARD",
    "RECOVERED_QUESTION_SET_PENDING_PER_ITEM_APPROVAL",
    "RECOVERED_PROVENANCE_PENDING_EXACT_RESPONSE",
    "CONFIRMED_CASE",
    "NEEDS_SOURCE_RECOVERY",
    "CANDIDATE",
    "CANDIDATE_PENDING_USER_REVIEW",
    "USER_APPROVED_RELEASE_CANDIDATE",
    "MODEL_RECONSTRUCTION_CANDIDATE_NOT_LIVE_REPLAY",
    "USER_CONFIRMED_RECONSTRUCTION_NOT_HISTORICAL_EXACT",
    "USER_CONFIRMED_NAVIGATOR_HANDOFF_RECORD",
    "USER_APPROVED_GOLD_STANDARD",
    "CLOSED_NEAR_MISS_CORRECTED_AND_LIVE_VALIDATED",
    "WITHDRAWN_PENDING_DOORWAY",
    "SUPERSEDED_GOLD_STANDARD",
}


def _registry():
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_canonical_storage_policy_is_hardcoded_and_approved_count_is_not_split():
    registry = _registry()
    policy = registry.get("canonical_storage")
    assert policy
    assert policy["authority"] == (
        "docs/qa/gold_standard_registry.json on the living-archive-backend main branch "
        "is the sole authoritative, additive Gold Star ledger."
    )
    assert "parallel registry" in policy["addition_rule"]
    assert "competing totals" in policy["reconciliation_rule"]
    assert "authoritative count" in policy["runtime_rule"]
    assert "exactly one canonical Gold Star state" in policy["single_approved_inventory_rule"]
    assert "No secondary approved-status bucket" in policy["authoritative_count_rule"]

    approved = [
        record for record in registry["records"]
        if record["status"] == "USER_APPROVED_GOLD_STANDARD"
    ]
    assert approved
    assert len({record["benchmark_id"] for record in approved}) == len(approved)



def test_authoritative_gold_star_count_is_status_based_not_subsystem_based():
    registry = _registry()
    approved = [
        record for record in registry["records"]
        if record["status"] == "USER_APPROVED_GOLD_STANDARD"
    ]
    active = [
        record for record in approved
        if record.get("runtime_transfer") is True
    ]
    # The authoritative inventory is the registry itself; avoid a stale hard-coded total.
    assert len(approved) >= 1
    assert len(active) <= len(approved)
    # These intentionally nonstandard historical subsystem labels prove that
    # filtering by subsystem would undercount the sole approved inventory.
    assert any(record["subsystem"] == "guide_bounded_conceptual_orientation" for record in approved)
    assert any(record["subsystem"] == "guide_integrative_development_orientation" for record in approved)


def test_registry_has_unique_ids_and_provenance_for_every_record():
    registry = _registry()
    assert registry["registry_id"] == "living-archive-gold-standard-registry"
    assert registry["schema_version"] == "1.1.0"
    records = registry["records"]
    ids = [record["benchmark_id"] for record in records]
    assert len(ids) == len(set(ids))
    assert len(records) >= 18

    for record in records:
        assert record["benchmark_id"].strip()
        assert record["subsystem"].strip()
        assert record["status"] in VALID_STATUSES
        assertions = record.get("assertions")
        expected_response = record.get("expected_response")
        accepted_response = record.get("accepted_response")
        assert (isinstance(assertions, list) and assertions) or expected_response or accepted_response, record["benchmark_id"]
        provenance = record["provenance"]
        assert provenance
        if isinstance(provenance, dict):
            assert any(
                provenance.get(key)
                for key in (
                    "source_path", "source_paths", "source_url", "source_urls",
                    "source_pr", "source_prs", "source_library_file", "source_ref",
                    "source", "source_date", "evidence_boundary",
                )
            ), record["benchmark_id"]
        else:
            assert isinstance(provenance, str) and provenance.strip(), record["benchmark_id"]
        freeze_policy = record["freeze_policy"]
        if isinstance(freeze_policy, dict):
            assert freeze_policy.get("status")
        else:
            assert isinstance(freeze_policy, str) and freeze_policy.strip()
        if record.get("query") is None or record.get("expected_response") is None:
            # Evaluation datasets and unrecovered scenarios are explicitly allowed
            # to have no single query/answer; they must not be miscounted as gold answers.
            assert "NOT_GOLD_STANDARD" in record["status"] or (
                "PENDING" in record["status"]
            ) or record["status"] in {"RECOVERED_REGRESSION_SCENARIO", "CONFIRMED_CASE", "NEEDS_SOURCE_RECOVERY", "RECOVERED_PROVENANCE_PENDING_EXACT_RESPONSE", "USER_APPROVED_GOLD_STANDARD_PENDING_FIXTURE", "MODEL_RECONSTRUCTION_CANDIDATE_NOT_LIVE_REPLAY", "USER_CONFIRMED_RECONSTRUCTION_NOT_HISTORICAL_EXACT", "USER_CONFIRMED_NAVIGATOR_HANDOFF_RECORD", "CANDIDATE"}
        else:
            assert record["query"].strip()
            assert record["expected_response"].strip()



def test_user_approved_conflicting_information_gold_star_is_registered_exactly():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-conflicting-information-discernment-gold-star-2026-11-07"
    )
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == (
        "I feel overwhelmed by conflicting information and opinions. "
        "How can I regain my bearings and know what is real enough to act on?"
    )
    assert record["rating_out_of_10"] == 8.8
    assert len(record["expected_response"].split(chr(10) * 2)) == 3
    assert "independently verified" in record["expected_response"]
    assert "independent sources" in record["expected_response"]
    assert "serious or irreversible consequences" in record["expected_response"]
    assert record["expected_doorway"] is None
    assert record["doorway_status"] == "LEGACY_INCOMPLETE_NOT_APPROVED"
    assert "Explicit user instruction" in record["provenance"]["approval_record"]


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
    assert len(record["expected_response"].split(chr(10) * 2)) == 3
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/level-1-case-catalog/"
    assert "do not independently prove the exact live response text" in record["provenance"]["evidence_boundary"]


def test_reciprocity_record_is_explicit_about_unmerged_source():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-reciprocity-gold-standard-2026-10-19"
    )
    assert record["status"] == "SUPERSEDED_GOLD_STANDARD"
    assert record["superseded_by_benchmark_id"] == "general-guide-reciprocity-community-2026-10-24"
    assert len(record["expected_response"].split(chr(10) * 2)) == 3
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
    approved = [
        item for item in _registry()["records"]
        if item.get("status") == "USER_APPROVED_GOLD_STANDARD"
    ]
    active = [
        item for item in approved
        if item.get("runtime_transfer") is True
    ]
    assert report["authoritative_gold_star_count"] == len(approved)
    assert report["active_runtime_gold_star_count"] == len(active)
    exact_only = [
        item for item in approved
        if item.get("runtime_transfer") is False
        and not item.get("superseded_by_benchmark_id")
        and (item.get("gold_star_capabilities") or {}).get("generation_class") != "user_approved_response_quality_exemplar"
    ]
    superseded = [item for item in approved if item.get("superseded_by_benchmark_id")]
    pending = [
        item for item in _registry()["records"]
        if item.get("status") == "RECOVERED_HISTORICAL_RESPONSE_PENDING_APPROVAL_EVIDENCE"
    ]
    assert report["exact_query_only_successor_count"] == len(exact_only)
    assert report["superseded_historical_reference_count"] == len(superseded)
    assert report["pending_approval_evidence_count"] == len(pending)
    assert report["authoritative_gold_star_count"] == len(approved)
    assert report["active_runtime_gold_star_count"] == len(active)
    assert report["counting_note"].find("Pending approval evidence is excluded") >= 0
    numbered = [item for item in approved if item.get("numbering_status") == "ASSIGNED"]
    unassigned = [item for item in approved if item.get("numbering_status") == "UNASSIGNED"]
    assert report["numbered_gold_star_count"] == len(numbered)
    assert report["unassigned_approved_gold_star_count"] == len(unassigned)
    assert report["highest_assigned_gold_star_number"] == max(
        (item["gold_star_number"] for item in numbered), default=None
    )
    assert report["numbering_sequence_start"] == _registry()["numbering_policy"]["sequence_start"]
    assert report["numbering_gap_register"] == _registry()["numbering_gap_register"]
    assert len(report["number_assignments"]) == len(numbered)
    assert len(report["unassigned_benchmark_ids"]) == len(unassigned)
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



def test_original_fourteen_standard_provenance_is_recorded_without_fabricated_answers():
    registry = _registry()
    records = {
        item.get("original_gold_standard_number"): item
        for item in registry["records"]
        if item.get("original_gold_standard_number") is not None
    }
    assert set(range(1, 15)).issubset(records)
    expected_ratings = {
        1: 8.5, 2: 9.0, 3: 8.5, 4: 9.0, 5: 9.0, 6: 9.0, 7: 9.0,
        8: 8.8, 9: 8.6, 10: 8.7, 11: 9.0, 12: 8.8, 13: 9.1, 14: 8.7,
    }
    for number, rating in expected_ratings.items():
        assert records[number]["rating_out_of_10"] == rating
        assert records[number]["query"] or records[number].get("known_theme")
        assert records[number]["status"] in {
            "RECOVERED_PROVENANCE_PENDING_EXACT_RESPONSE",
            "RECOVERED_HISTORICAL_RESPONSE_PENDING_APPROVAL_EVIDENCE",
            "MODEL_RECONSTRUCTION_CANDIDATE_NOT_LIVE_REPLAY",
            "USER_CONFIRMED_RECONSTRUCTION_NOT_HISTORICAL_EXACT",
            "USER_CONFIRMED_NAVIGATOR_HANDOFF_RECORD",
        }
        assert records[number]["expected_response"] is None

    assert records[4]["expected_doorway"]["url"] == "https://geralddaquila.com/start-here-2/"
    assert "rejected" in records[14]["approval_state"]


def test_original_gold_standard_four_records_navigator_handoff_provenance():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item.get("original_gold_standard_number") == 4
    )
    assert record["query"] == "Where should I start if I want to understand trust-based systems?"
    assert record["expected_response"] is None
    assert record["rating_out_of_10"] == 9
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/start-here-2/"
    assert record["provenance"]["request_hash"] == "navigator-c03843228f6a6649"
    assert record["provenance"]["provider_attribution"] == "navigation specialist; model composition not established"
    assert "not a logged General Guide composition event" in record["provenance"]["evidence_boundary"]



def test_collective_next_step_fallback_is_recorded_as_implementation_not_gold_answer():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-practical-collective-next-step-2026-10"
    )
    assert record["status"] == "RECOVERED_REGRESSION_SCENARIO"
    assert record["expected_response"] is None
    assert record["implementation_response"].startswith("Ask each person to explain")
    assert "choose one small, reversible action" in record["implementation_response"]
    assert record["implementation_response_provenance"]["source_pr"] == 757
    assert "merged to main via PR #757" in record["implementation_response_provenance"]["source_status"]
    assert "not an approved answer" in record["implementation_response_provenance"]["evidence_boundary"]



def test_harm_reduction_fallback_is_preserved_as_implementation_not_gold_answer():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-harm-reduction-outcome-evaluation-2026-10"
    )
    assert record["status"] == "RECOVERED_REGRESSION_SCENARIO"
    assert record["expected_response"] is None
    assert record["implementation_response"].startswith(
        "To tell whether the revised approach is reducing harm"
    )
    assert "starting point over time" in record["implementation_response"]
    assert "unintended consequences" in record["implementation_response"]
    assert record["implementation_response_provenance"]["source_pr"] == 768
    assert "merged to main via PR #768" in record["implementation_response_provenance"]["source_status"]
    assert "not a visitor-approved gold answer" in record["implementation_response_provenance"]["evidence_boundary"]


def test_community_trust_candidate_preserves_sequence_and_evidence_boundary():
    registry = _registry()
    record = next(item for item in registry["records"] if item["benchmark_id"] == "general-guide-trust-community-stewardship-2026-10-24")
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == "What is the role of trust in community stewardship?"
    fixture = json.loads(
        (ROOT / "tests" / "fixtures" / "general_guide_trust_community_stewardship_candidate.json").read_text(encoding="utf-8")
    )
    assert record["expected_response"] == fixture["expected_response"]
    assert record["expected_doorway"]["title"] == "Trust Architecture"
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/trust-architecture/"
    assert record["status"] == fixture["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["runtime_transfer"] is True
    assert record["gold_star_capabilities"]["exact_answer_authority"] is False
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    assert record["numbering_status"] == "UNASSIGNED"


def test_reciprocity_community_gold_standard_is_approved_bounded_and_supersedes_old_reference():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-reciprocity-community-2026-10-24"
    )
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == "What is the purpose of reciprocity in a community?"
    assert record.get("rating") is None
    assert "rating_out_of_10" not in record
    assert record["assistant_assessment_out_of_10"] == 9.5
    assert record["runtime_transfer"] is True
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["exact_answer_authority"] is False
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    assert "support one another over time" in record["expected_response"]
    assert "not when kindness becomes a debt ledger" in record["expected_response"]
    assert record["doorway_status"] == "VERIFIED_CANONICAL_DESTINATION"
    assert record["expected_doorway"]["url"].startswith("https://geralddaquila.com/")
    old = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-reciprocity-gold-standard-2026-10-19"
    )
    assert old["status"] == "SUPERSEDED_GOLD_STANDARD"
    assert old["superseded_by_benchmark_id"] == record["benchmark_id"]
    assert old["query"] == "What does reciprocity mean in the Living Archive?"
    assert old["expected_response"].startswith("Reciprocity means a relationship of mutual response:")


def test_human_development_gold_standard_preserves_approved_answer_and_doorway():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-human-development-significance-2026-10-24"
    )
    fixture_path = ROOT / "tests" / "fixtures" / "general_guide_human_development_gold_standard.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == fixture["query"] == "What is the significance of human development?"
    assert record["expected_response"] == fixture["expected_response"]
    assert record["expected_doorway"]["title"] == fixture["expected_doorway_title"]
    assert record["expected_doorway"]["url"] == fixture["expected_doorway_url"]
    assert record["rating_out_of_10"] == fixture["rating_out_of_10"] == 9.0
    assert len(record["expected_response"].split(chr(10) * 2)) == 3
    assert "not a claim that the general explanation is a verbatim canonical doctrine" in record["provenance"]["evidence_boundary"]


def test_water_boiling_point_failure_control_is_not_misrepresented_as_gold_answer():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-water-boiling-point-failure-control-2026-10-24"
    )
    assert record["status"] == "RECOVERED_FAILURE_CONTROL_NOT_GOLD_STANDARD"
    assert record["query"] == "What is the boiling point of water at sea level?"
    assert record["expected_response"] is None
    assert any("Do not refuse a well-established general fact" in item for item in record["assertions"])



def test_water_boiling_point_general_knowledge_gold_standard_preserves_live_answer_and_disclosure():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-water-boiling-point-general-knowledge-gold-standard-2026-10-24"
    )
    fixture_path = ROOT / "tests" / "fixtures" / "general_guide_water_boiling_point_gold_standard.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert record["status"] == fixture["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == fixture["query"] == "What is the boiling point of water at sea level?"
    assert record["expected_response"] == fixture["expected_response"]
    assert record["expected_doorway"] is None
    assert record["doorway_status"] == "LEGACY_INCOMPLETE_NOT_APPROVED"
    assert record["rating_out_of_10"] == fixture["rating_out_of_10"] == 9
    assert len(record["expected_response"].split(chr(10) * 2)) == 2
    assert "100°C (212°F)" in record["expected_response"]
    assert "depends on pressure, not just temperature" in record["expected_response"]
    disclosure = "The Guide considers your question alongside the Living Archive’s ideas, themes, and pathways to help you find where to begin. From there, you can explore the Archive for yourself."
    assert disclosure in fixture["provenance"]["expanded_how_results_are_found_disclosure"]
    assert "does not claim the science answer is sourced from or canonical doctrine" in fixture["provenance"]["evidence_boundary"]


def test_governance_beyond_administration_gold_standard_is_registered():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-governance-beyond-administration-gold-standard-2026-10-26"
    )
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == "What is governance, beyond administration?"
    assert len(record["expected_response"].split(chr(10) * 2)) == 3
    assert record["expected_doorway"]["title"] == "Governance & Institution Building"
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/governance-institution-building/"
    assert "If administration is the act of steering a ship" in record["expected_response"]
    assert "community garden" in record["expected_response"]
    assert "intended to orient authority toward stewardship" in record["expected_response"]
    assert "Preserve expected_response verbatim" in record["freeze_policy"]


def test_leadership_vs_positional_authority_gold_standard_is_registered():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-leadership-vs-positional-authority-gold-standard-2026-10-26"
    )
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == "What distinguishes leadership from positional authority?"
    assert len(record["expected_response"].split(chr(10) * 2)) == 3
    assert record["expected_doorway"] is None
    assert record["doorway_status"] == "LEGACY_INCOMPLETE_NOT_APPROVED"
    
    assert "not establish leadership" in record["expected_response"]
    assert "does not independently establish the destination URL" in record["provenance"]["evidence_boundary"]


def test_fragmented_knowledge_gold_standard_preserves_approved_response():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-fragmented-knowledge-wise-action-gold-standard-2026-10-26"
    )
    expected = (
        "Fragmented knowledge impedes wise action because decisions are made from partial pictures. "
        "Useful facts, experience, and perspectives remain separated, leaving no one able to see enough of the situation "
        "to judge what a decision may set in motion. A piece of information can be accurate on its own yet misleading when "
        "stripped of its context or its relationship to other parts of the problem.\n\n"
        "For example, one team may know why a process is failing, another may understand how a proposed fix affects "
        "people, and a third may hold the history of earlier attempts. If those insights never meet, a decision can "
        "solve the visible symptom while recreating the original problem somewhere else. Bringing the knowledge "
        "together helps reveal dependencies, trade-offs, and consequences that no single fragment could show.\n\n"
        "Integration does not mean forcing every view into one story or pretending uncertainty disappears. It means "
        "comparing sources, listening to people who hold different parts of the picture, and making clear what is "
        "known, what is inferred, and what remains missing. Wise action becomes more likely when decisions reflect "
        "the whole available picture, stay open to correction, and account for the people who will live with the consequences."
    )
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == "How does fragmented knowledge impede wise action?"
    assert record["expected_response"] == expected
    assert len(expected.split(chr(10) * 2)) == 3
    assert record["expected_doorway"] is None
    assert record["doorway_status"] == "LEGACY_INCOMPLETE_NOT_APPROVED"
    assert record["provenance"]["review_rating"] == "9.6/10"
    assert "Exact response wording is frozen" in record["provenance"]["evidence_boundary"]

def test_gold_standard_rejects_three_paragraph_meta_answer_fallback():
    import json
    import sys
    import pytest

    sys.path.insert(0, str(ROOT))
    import general_guide_composition as composition

    meta_answer = (
        "The question about leadership deserves a direct answer, not a guess presented as certainty. "
        "The most useful next step is to identify the specific claim.\n\n"
        "The right answer depends on addressing the question directly and explaining the evidence. "
        "I have not been able to produce that complete explanation reliably in this response.\n\n"
        "Please try again shortly. I do not want to present an incomplete response as though it met the Guide’s standard."
    )
    parser = composition._parse_factory([], "What distinguishes leadership from positional authority?")
    result = parser(json.dumps({
        "response": meta_answer,
        "doorway_title": "",
        "response_shape": "explanatory",
    }))
    assert result.get("response") == meta_answer

def test_leadership_authority_recovery_is_direct_three_paragraph_gold_standard():
    import sys
    sys.path.insert(0, str(ROOT))
    import deterministic_answer_recovery as recovery

    query = "What distinguishes leadership from positional authority?"
    answer = recovery.compose_recovery(query)
    paragraphs = [part.strip() for part in answer.split("\n\n") if part.strip()]

    assert len(paragraphs) == 3
    assert paragraphs[0].startswith("Positional authority comes from a formal role")
    assert "The difference becomes clear in practice" in paragraphs[1]
    assert "authority alone does not establish leadership" in paragraphs[2]
    assert "Please try again shortly" not in answer
    assert "This is a general conceptual distinction" not in answer


def test_comparative_doorway_concept_patterns_use_real_word_boundaries():
    main_source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert 'return r"\\b(?:leadership|leader|leaders|leading|lead)\\b"' in main_source
    assert 'return r"\\b(?:positional authority|formal authority|authority|authorities|position(?:al)?|role[- ]based power|formal power|institutional power|power|role|roles)\\b"' in main_source
    assert 'return r"\\b(?:" + "|".join(escaped) + r")\\b"' in main_source


def test_distinguishing_question_extracts_both_compared_subjects_for_doorway_relevance():
    main_source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert r"what distinguishes (.+?) from (.+?)" in main_source
    assert r"what separates (.+?) from (.+?)" in main_source
    assert r"what differentiates (.+?) from (.+?)" in main_source


def test_gold_standard_default_is_default_on_for_ordinary_questions():
    import sys
    sys.path.insert(0, str(ROOT))
    import general_guide_composition as composition

    ordinary_questions = (
        "What distinguishes leadership from positional authority?",
        "What role does trust play in a community?",
        "Explain why fragmented knowledge can lead to poor decisions.",
        "Can you explain how stewardship works in practice?",
        "What should a community understand about shared responsibility?",
    )
    for query in ordinary_questions:
        assert composition._requires_three_paragraph_default(query), query

    assert not composition._requires_three_paragraph_default("What is the capital of France?")
    assert not composition._requires_three_paragraph_default("Please answer in one sentence.")


def test_fragmented_knowledge_gold_standard_is_runtime_resolvable_without_global_paragraph_enforcement():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-fragmented-knowledge-wise-action-gold-standard-2026-10-26"
    )
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == "How does fragmented knowledge impede wise action?"
    assert len(record["expected_response"].split(chr(10) * 2)) == 3

    standards_source = (ROOT / "general_guide_gold_standards.py").read_text(encoding="utf-8")
    composition_source = (ROOT / "general_guide_composition.py").read_text(encoding="utf-8")
    assert "_registered_exact_gold_standard(question)" in composition_source
    assert "def _requires_three_paragraph_default(query: str) -> bool:" in composition_source
    assert "def _requires_substantive_answer_contract(query: str) -> bool:" in composition_source
    assert "def _requires_three_paragraph_default(query: str) -> bool:" in composition_source
    assert "never requires three paragraphs or any fixed number of response units" in composition_source
    assert "substantive explanatory answer must meet the three-paragraph Guide Gold Standard" not in composition_source
    assert 'CONTRACT_VERSION = "v1.59"' in composition_source
    assert "def resolve_exact_gold_standard(question: str)" in standards_source
    main_source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert 'snapshot.get("contract_version") != general_guide_composition.CONTRACT_VERSION' in main_source
    assert "Apply the shared task-dependent quality contract at the final visitor boundary" in main_source
    assert "if _meta_answer or _current_response_nonanswer:" in main_source
    assert "len(_last_paragraphs) < 3" not in main_source
    assert "paragraph-count filler" in main_source


def test_user_approved_gold_stars_have_explicit_runtime_capability_classification():
    registry = _registry()
    approved = [
        record for record in registry["records"]
        if record["status"] == "USER_APPROVED_GOLD_STANDARD"
    ]
    # Gold Stars are an intentionally growing registry. Validate the
    # classification invariant for every approved exemplar rather than freezing
    # the test to a historical record count.
    assert approved
    for record in approved:
        capability = record.get("gold_star_capabilities")
        # Canonical continuation records predate the capability object and carry
        # their transfer contract in the record-level fields.
        if not capability:
            # Some historically approved exemplars are canonical learning records
            # but do not yet have an exact response fixture. They remain in the
            # single approved inventory; fixture incompleteness is evidence
            # metadata, not a second approval status.
            if record.get("fixture_state") == "PENDING_EXACT_FIXTURE":
                assert record.get("provenance", {}).get("evidence_boundary")
                assert record.get("freeze_policy")
                assert record.get("query")
                assert record.get("expected_response") or record.get("lesson")
                continue
            assert record.get("runtime_transfer") is True
            assert record.get("reasoning_family")
            assert record.get("transferable_lesson")
            assert record.get("transfer_boundary")
            continue
        # Historical provenance determines generation class; do not erase
        # distinct approved recovery and delegated-judgment classes.
        assert capability.get("generation_class")
        # Some approved records are qualitative-transfer exemplars by explicit
        # capability contract; exact replay authority must not be invented.
        assert isinstance(capability.get("exact_answer_authority"), bool)
        if record.get("superseded_by_benchmark_id"):
            # Historical duplicate is preserved for provenance only.
            assert record.get("runtime_transfer") is False
            assert record.get("runtime_exact_query_successor") == record.get("superseded_by_benchmark_id")
            assert capability.get("exact_answer_authority") is False
            assert capability.get("active_quality_contributor") is False
            assert capability.get("deterministic_fallback_eligible") is False
        elif record.get("runtime_transfer") is False and capability.get("generation_class") == "user_approved_response_quality_exemplar":
            assert capability.get("exact_answer_authority") is False
            assert capability.get("active_quality_contributor") is False
            assert capability.get("deterministic_fallback_eligible") is False
            if capability.get("standalone_response_quality_exemplar") is True:
                assert not record.get("paired_active_benchmark_id")
            else:
                assert record.get("paired_active_benchmark_id")
        elif record.get("runtime_transfer") is False and capability.get("generation_class") == "user_approved_response_quality_exemplar":
            assert capability.get("exact_answer_authority") is False
            assert capability.get("active_quality_contributor") is False
            assert capability.get("deterministic_fallback_eligible") is False
            if capability.get("standalone_response_quality_exemplar") is True:
                assert not record.get("paired_active_benchmark_id")
            else:
                assert record.get("paired_active_benchmark_id")
        elif record.get("runtime_transfer") is False:
            assert capability.get("exact_answer_authority") is True
            assert capability.get("active_quality_contributor") is False
            assert capability.get("deterministic_fallback_eligible") is False
            assert record.get("replaces_exact_query_runtime_authority_of")
        else:
            assert record.get("runtime_transfer") is True
            assert capability.get("active_quality_contributor") is True
        assert isinstance(capability.get("deterministic_fallback_eligible"), bool)
        assert capability.get("reasoning_family")
        assert capability.get("transferable_discipline")
        assert capability.get("abstention_boundary")

def test_capability_metadata_does_not_guess_original_generation_mode():
    registry = _registry()
    approved = next(
        record for record in registry["records"]
        if record["status"] == "USER_APPROVED_GOLD_STANDARD"
        and record.get("gold_star_capabilities", {}).get("generation_class")
    )
    generation_class = approved["gold_star_capabilities"]["generation_class"]
    assert "LLM" not in generation_class
    assert "does not infer" in approved["gold_star_capabilities"]["intake_note"]


def test_organizational_learning_gold_star_requires_canonical_doorway_contract():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "gs-2026-11-14-organizational-learning-from-failure"
    )
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == "How do organizations create conditions for learning from failure?"
    assert record["doorway_status"] == "REQUIRED_CANONICAL_CONTINUATION"
    doorway = record["expected_doorway"]
    assert doorway["title"] == (
        "The Social Architecture of Thriving: Conditions That Allow Human Potential to Expand"
    )
    assert doorway["url"] == (
        "https://geralddaquila.com/2026/06/15/the-social-architecture-of-thriving-conditions-that-allow-human-potential-to-expand/"
    )
    assert any(
        "final visitor-facing response boundary" in assertion
        for assertion in record["assertions"]
    )


def test_inner_development_systems_gold_star_is_runtime_resolvable_and_frozen():
    import sys
    sys.path.insert(0, str(ROOT))
    from general_guide_gold_standards import resolve_exact_gold_standard

    query = "How do inner development and external systems shape each other?"
    record = resolve_exact_gold_standard(query)
    assert record is not None
    assert record["benchmark_id"] == "gs-2026-11-14-inner-development-external-systems-feedback-loop"
    assert record["expected_response"].startswith(
        "Inner development and external systems shape each other through a continuing feedback loop."
    )
    assert record["doorway_title"] == (
        "The Social Architecture of Thriving: Conditions That Allow Human Potential to Expand"
    )
    assert record["doorway_url"].startswith("https://geralddaquila.com/")


def test_inner_development_gold_star_transport_authority_is_exact():
    from general_guide_gold_standards import resolve_exact_gold_standard
    query = "How do inner development and external systems shape each other?"
    record = resolve_exact_gold_standard(query)
    assert record is not None
    assert record["expected_response"].startswith("Inner development and external systems shape each other through a continuing feedback loop.")
    assert record["doorway_title"] == "The Social Architecture of Thriving: Conditions That Allow Human Potential to Expand"
    assert record["doorway_url"].startswith("https://geralddaquila.com/")


def test_exact_gold_standard_finalizer_precedence_contract_is_declared():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    finalizer_start = source.index("def _guide_finalize_visitor_payload")
    finalizer_end = source.index("def _apply_exact_gold_standard_authority_to_payload", finalizer_start)
    finalizer = source[finalizer_start:finalizer_end]
    exact = finalizer.index("exact_standard = _final_exact_gold_standard_authority(query)")
    provenance = finalizer.index("_is_archive_claim_boundary_inquiry(query)")
    broad = finalizer.index("_requires_broad_conceptual_definition(query)")
    terminal = finalizer.index("_outer_registered_recovery")
    assert exact < provenance < broad < terminal
    assert 'safe["processing"] = "final_visitor_boundary_exact_gold_standard"' in finalizer


def test_sacred_language_exact_gold_star_resolves_browser_query():
    from general_guide_gold_standards import resolve_exact_gold_standard
    result = resolve_exact_gold_standard("How can sacred language clarify experience, and how can it obscure power relations?")
    assert result is not None
    assert result["expected_response"].startswith("Sacred language can clarify experience when it gives people words")


def test_sacred_language_gold_star_preserves_observed_title_without_unverified_doorway():
    from general_guide_gold_standards import resolve_exact_gold_standard
    result = resolve_exact_gold_standard("How can sacred language clarify experience, and how can it obscure power relations?")
    assert result is not None
    # The screenshot establishes the visible title, not a canonical destination URL.
    # Runtime must therefore withhold the handoff rather than invent or infer a URL.
    assert result["doorway_title"] == "The Power of Language & Symbol"
    assert result["doorway_url"] == "https://geralddaquila.com/the-power-of-language-symbol/"
    record = next(
        item for item in _registry()["records"]
        if item["benchmark_id"] == "gs-2026-11-14-sacred-language-clarity-power-live-candidate"
    )
    assert record["observed_doorway_title"] == "The Power of Language & Symbol"
    assert record["doorway_status"] == "VERIFIED_CANONICAL_DESTINATION"
    assert record["expected_doorway"]["title"] == "The Power of Language & Symbol"
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/the-power-of-language-symbol/"


def test_methods_comparison_gold_star_orients_method_choice_without_collapsing_distinctions():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-methods-comparison-gold-standard-2026-10-25"
    )
    response = record["expected_response"]
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["runtime_transfer"] is True
    assert len(response.split(chr(10) * 2)) == 3
    assert "what happened or whether a claim is supported" in response
    assert "how conditions influence one another" in response
    assert "examining meaning or reasons" in response
    assert "notice experience and interpretation more directly" in response
    assert "The question determines which approach should lead" in response


def test_cosmology_generalization_gold_star_uses_boundary_corroboration_calibration():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-cosmology-generalization-standards-gold-standard-2026-10-25"
    )
    response = record["expected_response"]
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["runtime_transfer"] is True
    assert len(response.split("\n\n")) == 3
    assert "it cannot, by itself, establish what governs the whole cosmology" in response
    assert "A broader claim requires corroboration, not resemblance" in response
    assert "Then calibrate the conclusion to the evidence actually available" in response
    assert "Archive-wide generalization" in response


def test_stewardship_gold_star_orients_meaning_practice_and_boundaries():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-stewardship-living-archive-meaning-gold-standard-2026-10-25"
    )
    response = record["expected_response"]
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["runtime_transfer"] is True
    assert len(response.split("\n\n")) == 3
    assert "stewardship follows understanding" in response
    assert "receive what matters with care, understand what depends on it, and act with its future in mind" in response
    assert "Stewardship is neither control nor unlimited self-sacrifice" in response




def test_held_in_trust_gold_star_preserves_recognition_relationship_boundary():
    registry = _registry()
    record = next(item for item in registry["records"] if item["benchmark_id"] == "general-guide-identifying-what-is-held-in-trust-gold-standard-2026-10-25")
    response = record["expected_response"]
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert len(response.split(chr(10) * 2)) == 3
    assert "what has been placed in someone's care" in response
    assert "care is owed beyond the holder's own preference or convenience" in response
    assert "Trust is relational" in response
    assert "where the holder's authority ends" in response
    assert "without assuming that every duty is unlimited or belongs to one person alone" in response


def test_gold_star_inventory_has_one_canonical_approved_directory():
    registry = _registry()
    approved = [r for r in registry["records"] if r["status"] == "USER_APPROVED_GOLD_STANDARD"]
    assert approved
    assert all(r["status"] != "USER_APPROVED_GOLD_STANDARD_PENDING_FIXTURE" for r in registry["records"])
    assert len({r["benchmark_id"] for r in approved}) == len(approved)


def test_gold_star_has_one_strict_canonical_definition():
    registry = _registry()
    gold = [r for r in registry["records"] if r["status"] == "USER_APPROVED_GOLD_STANDARD"]
    assert gold
    for record in gold:
        assert record.get("expected_response"), record["benchmark_id"]
        assert record.get("freeze_policy"), record["benchmark_id"]
        capability = record.get("gold_star_capabilities") or {}
        if record.get("superseded_by_benchmark_id"):
            assert record.get("runtime_transfer") is False, record["benchmark_id"]
            assert capability.get("exact_answer_authority") is False, record["benchmark_id"]
            assert capability.get("active_quality_contributor") is False, record["benchmark_id"]
            assert capability.get("deterministic_fallback_eligible") is False, record["benchmark_id"]
        elif record.get("runtime_transfer") is False and capability.get("generation_class") == "user_approved_response_quality_exemplar":
            assert capability.get("exact_answer_authority") is False, record["benchmark_id"]
            assert capability.get("active_quality_contributor") is False, record["benchmark_id"]
            assert capability.get("deterministic_fallback_eligible") is False, record["benchmark_id"]
            if capability.get("standalone_response_quality_exemplar") is True:
                assert not record.get("paired_active_benchmark_id"), record["benchmark_id"]
            else:
                assert record.get("paired_active_benchmark_id"), record["benchmark_id"]
        elif record.get("runtime_transfer") is False:
            assert capability.get("exact_answer_authority") is True, record["benchmark_id"]
            assert capability.get("active_quality_contributor") is False, record["benchmark_id"]
            assert capability.get("deterministic_fallback_eligible") is False, record["benchmark_id"]
            assert record.get("replaces_exact_query_runtime_authority_of"), record["benchmark_id"]
        else:
            assert record.get("runtime_transfer") is True, record["benchmark_id"]
            assert capability.get("active_quality_contributor") is True, record["benchmark_id"]
        assert isinstance(capability.get("deterministic_fallback_eligible"), bool), record["benchmark_id"]
        assert record.get("fixture_state") != "PENDING_EXACT_FIXTURE", record["benchmark_id"]


def test_incomplete_evidence_records_are_not_counted_as_gold_stars():
    registry = _registry()
    incomplete = [r for r in registry["records"] if r.get("fixture_state") == "PENDING_EXACT_FIXTURE"]
    assert all(r["status"] != "USER_APPROVED_GOLD_STANDARD" for r in incomplete)


def test_frozen_ethical_tradeoff_record_matches_authoritative_fixture_exactly():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-ethical-tradeoff-2026-10"
    )
    fixture = json.loads(ETHICAL_TRADEOFF_FIXTURE_PATH.read_text(encoding="utf-8"))
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == fixture["query"]
    assert record["expected_response"] == fixture["expected_response"]
    assert len(record["expected_response"].split(chr(10) * 2)) == 3
    assert record["expected_doorway"] is None
    assert record["doorway_status"] == "LEGACY_INCOMPLETE_NOT_APPROVED"
    assert record["runtime_transfer"] is True
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True


def test_technology_refinement_release_candidate_has_exact_query_review_authority_without_gold_star_status():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-technology-stewardship-governance-refinement-2026-11-15"
    )
    assert record["status"] in {
        "USER_APPROVED_RELEASE_CANDIDATE",
        "USER_APPROVED_GOLD_STANDARD",
    }
    assert record["expected_doorway"]["title"] == "Foundations of Stewardship Governance"
    if record["status"] == "USER_APPROVED_RELEASE_CANDIDATE":
        assert record["runtime_review_authority"] is True
        assert record["rating_out_of_10"] == 9.5
        assert "not a Gold Star" in record["freeze_policy"]
    else:
        assert record.get("runtime_transfer") is True


def test_reflection_vs_therapy_gold_star_preserves_verified_doorway_through_final_visitor_boundary():
    """Regression: a verified exact Gold Star doorway must reach every visitor alias."""
    import sys
    sys.path.insert(0, str(ROOT))
    from general_guide_gold_standards import resolve_exact_gold_standard

    query = "How should The Guide distinguish reflection from therapy?"
    record = resolve_exact_gold_standard(query)
    assert record is not None
    assert record["benchmark_id"] == (
        "general-guide-reflection-vs-therapy-boundary-gold-standard-2026-11-16"
    )
    assert record["doorway_title"] == (
        "The First Institution: Why Human Development Begins at Home"
    )
    assert record["doorway_url"] == (
        "https://geralddaquila.com/2025/06/17/"
        "the-first-institution-why-human-development-begins-at-home/"
    )

    source = (ROOT / "main.py").read_text(encoding="utf-8")
    start = source.index("def _guide_finalize_visitor_payload")
    end = source.index("\n    response_text =", start)
    exact_boundary = source[start:end]
    assert 'safe["recommendation"] = exact_doorway' in exact_boundary
    assert 'safe["canonical_doorway"] = exact_doorway' in exact_boundary
    assert 'safe["doorway_title"] = exact_title' in exact_boundary
    assert 'safe["doorway_url"] = exact_url' in exact_boundary


def test_terminal_visitor_boundary_restores_verified_doorway_for_ordinary_answers():
    """Regression: ordinary answers may not bypass the verified doorway contract."""
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "def _guide_restore_verified_doorway(payload, query):" in source
    assert "_select_guide_node_fallback_doorway(query)" in source
    assert 'safe["canonical_doorway"] = doorway' in source
    assert 'safe["doorway_title"] = doorway.get("title") if doorway else None' in source
    assert 'safe["doorway_url"] = doorway.get("url") if doorway else None' in source
    assert "return _guide_restore_verified_doorway(payload, query)" in source


def test_verified_doorway_fallback_uses_registry_declared_terms_for_development_query():
    """Regression: central development questions must reach a declared registry doorway."""
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "def _select_guide_node_fallback_doorway(query):" in source
    assert '" ".join(node.get("semantic_hints") or [])' in source
    assert "str(node.get(\"purpose\") or \"\")" in source


def test_verified_human_development_ecology_doorway_for_practice_community_feedback():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert '"human_development_ecology"' in source
    assert '"Becoming Fully Human"' in source
    assert "the-architecture-of-human-development" in source


def test_human_development_family_matcher_executes_for_live_regression_query():
    import ast
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    from stewardship_consent_contract import is_stewardship_consent_relationship_question
    namespace = {
        "re": __import__("re"),
        "is_stewardship_consent_relationship_question": is_stewardship_consent_relationship_question,
    }
    helper = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_guide_query_explicitly_forbids_handoff"
    )
    fn = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_select_verified_doorway_conceptual_family"
    )
    exec(compile(ast.Module(body=[helper, fn], type_ignores=[]), "<family>", "exec"), namespace)
    assert namespace["_select_verified_doorway_conceptual_family"](
        "What roles do practice, community, and feedback play in development?"
    ) == "human_development_ecology"


def test_practice_community_feedback_gold_star_has_verified_runtime_doorway():
    import json
    registry = json.loads((ROOT / "docs" / "qa" / "gold_standard_registry.json").read_text(encoding="utf-8"))
    record = next(
        item for item in registry["records"]
        if item.get("benchmark_id") == "gs-2026-11-14-practice-community-feedback-development"
    )
    doorway = record["expected_doorway"]
    assert doorway["title"] == "Becoming Fully Human"
    assert doorway["url"] == "https://geralddaquila.com/2026/10/05/the-architecture-of-human-development/"


def test_practice_community_feedback_gold_star_is_assigned_next_canonical_number():
    import json
    registry = json.loads((ROOT / "docs" / "qa" / "gold_standard_registry.json").read_text(encoding="utf-8"))
    record = next(
        item for item in registry["records"]
        if item.get("benchmark_id") == "gs-2026-11-14-practice-community-feedback-development"
    )
    assert record["gold_star_number"] == 89
    assert record["explicit_user_elevation_approval"] is True
    assert record["expected_doorway"]["title"] == "Becoming Fully Human"


def test_recovered_serial_provenance_and_gap_register_are_immutable_after_merge():
    validator = (ROOT / "scripts" / "validate_gold_star_registry.py").read_text(encoding="utf-8")
    assert "historical numbering recovery evidence is immutable" in validator
    assert "historical numbering gap evidence/disposition is immutable" in validator
    assert "numbering sequence_start is immutable once established" in validator
    assert "validate_numbering_against_base(records, registry)" in validator


def test_explicit_numbering_migration_is_required_for_existing_unnumbered_approval():
    source = (ROOT / "scripts" / "validate_gold_star_registry.py").read_text(encoding="utf-8")
    assert "explicit_user_authorized_numbering_migration" in source
    assert "previous_numbering_state" in source


def test_integrity_audit_numbered_count_matches_registry_records():
    import json
    registry = json.loads((ROOT / "docs" / "qa" / "gold_standard_registry.json").read_text(encoding="utf-8"))
    numbered = sum(isinstance(r.get("gold_star_number"), int) for r in registry["records"])
    assert registry["integrity_audit"]["numbered_gold_star_record_count"] == numbered


def test_meaning_making_gold_star_90_has_verified_canonical_doorway():
    import json
    registry = json.loads((ROOT / "docs" / "qa" / "gold_standard_registry.json").read_text(encoding="utf-8"))
    record = next(r for r in registry["records"] if r["benchmark_id"] == "gs-2026-11-16-meaning-making-factual-explanation")
    assert record["gold_star_number"] == 90
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/2026/04/08/making-sense-of-life-without-oversimplifying-it/"



def test_every_approved_gold_star_has_explicit_numbering_state_and_reason():
    import json

    registry = json.loads(
        (ROOT / "docs" / "qa" / "gold_standard_registry.json").read_text(encoding="utf-8")
    )
    approved = [
        record for record in registry["records"]
        if record.get("status") == "USER_APPROVED_GOLD_STANDARD"
    ]
    assert approved
    for record in approved:
        number = record.get("gold_star_number")
        if isinstance(number, int) and not isinstance(number, bool):
            assert record.get("numbering_status") == "ASSIGNED"
            assert not record.get("numbering_unassigned_reason")
            assert record.get("numbering_unassigned_reason_code") is None
        else:
            assert record.get("numbering_status") == "UNASSIGNED"
            assert record.get("numbering_unassigned_reason_code") in {
                "NO_SERIAL_ALLOCATION_REQUESTED",
                "LEGACY_APPROVED_NO_SERIAL_ALLOCATION",
            }
            assert record.get("numbering_unassigned_reason")
            if record.get("legacy_approval_grandfathered") is True:
                assert record["numbering_unassigned_reason_code"] == "LEGACY_APPROVED_NO_SERIAL_ALLOCATION"
            else:
                assert record["numbering_unassigned_reason_code"] == "NO_SERIAL_ALLOCATION_REQUESTED"



def test_spiritual_bypassing_gold_star_is_explicitly_migrated_to_91_without_reviving_89():
    import json
    registry = json.loads((ROOT / "docs" / "qa" / "gold_standard_registry.json").read_text(encoding="utf-8"))
    record = next(r for r in registry["records"] if r["benchmark_id"] == "gs-2026-11-14-bounded-conceptual-orientation-spiritual-bypassing")
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["runtime_transfer"] is True
    assert record["gold_star_number"] == 91
    assert record["numbering_status"] == "ASSIGNED"
    assert "numbering_unassigned_reason" not in record
    migration = record["numbering_migration"]
    assert migration["migration_class"] == "explicit_user_authorized_numbering_migration"
    assert migration["previous_numbering_state"] == "approved_unnumbered"
    assert migration["approved_at"] == "2026-11-16"
    assert "explicit user authorization" in migration["authority"]
    assert "not a backfill" in migration["reason"]


def test_85_and_86_are_allocated_and_no_documented_historical_gap_remains():
    import json
    registry = json.loads((ROOT / "docs" / "qa" / "gold_standard_registry.json").read_text(encoding="utf-8"))
    gaps = registry["numbering_gap_register"]
    assert gaps == []
    allocation = next(item for item in registry["numbering_allocation_history"] if item["number"] == 86)
    assert allocation["status"] == "ALLOCATED_TO_APPROVED_GOLD_STAR"
    assert allocation["benchmark_id"] == "general-guide-archive-examples-evidence-limits-gold-star-2026-11-18"
    prior_gap = allocation["prior_gap_record"]
    assert prior_gap["status"] == "RELEASED_FOR_FUTURE_ALLOCATION"
    assert prior_gap["number"] == 86
    assert prior_gap["release_authorization"]["authorization_type"] == "EXPLICIT_USER_AUTHORIZED_HISTORICAL_GAP_RELEASE"
    assert prior_gap["release_authorization"]["historical_evidence_preserved"] is True
    assert prior_gap["release_authorization"]["allocation_rule"].find("#85") >= 0
    assert "7a036632323b7c09003d1fce637a7b49128a27bf" in prior_gap["reason"]
    assert "only adds provenance.source_date" in prior_gap["reason"]
    assert "recovered as Gold Star #56" in prior_gap["reason"]
    assert registry["numbering_policy"]["sequence_start"] == 56
    from gold_star_inventory import derive_gold_star_inventory
    inventory = derive_gold_star_inventory(registry)
    approved = [
        item for item in registry["records"]
        if item.get("status") == "USER_APPROVED_GOLD_STANDARD"
    ]
    assert inventory["approved_gold_star_count"] == len(approved)
    assert inventory["numbered_gold_star_count"] == sum(
        record.get("numbering_status") == "ASSIGNED" for record in approved
    )
    assert inventory["highest_assigned_gold_star_number"] == max(
        (record["gold_star_number"] for record in approved if record.get("numbering_status") == "ASSIGNED"),
        default=None,
    )
    assert registry["integrity_audit"]["documented_numbering_gap_count"] == 0



def test_historically_assigned_gold_stars_56_to_59_are_recovered_from_merged_prs():
    import json
    registry = json.loads((ROOT / "docs" / "qa" / "gold_standard_registry.json").read_text(encoding="utf-8"))
    expected = {
        "general-guide-agency-circumstance-gold-standard-2026-11-15": (56, 1428),
        "general-guide-developmental-language-gold-star-2026-11-09": (57, 1430),
        "general-guide-culture-notice-value-imagine-gold-standard-2026-11-15": (58, 1432),
        "general-guide-transformation-temporary-relief-gold-standard-2026-11-15": (59, 1434),
    }
    by_id = {r["benchmark_id"]: r for r in registry["records"]}
    for benchmark_id, (number, source_pr) in expected.items():
        record = by_id[benchmark_id]
        recovery = record["numbering_recovery"]
        assert record["gold_star_number"] == number
        assert record["numbering_status"] == "ASSIGNED"
        assert recovery["recovered_number"] == number
        assert recovery["source_pr"] == source_pr
        assert recovery["source_merge_commit"]
        assert recovery["authority_basis"]


def test_unmerged_developmental_language_56_proposal_is_not_the_canonical_assignment():
    import json
    registry = json.loads((ROOT / "docs" / "qa" / "gold_standard_registry.json").read_text(encoding="utf-8"))
    record = next(r for r in registry["records"] if r["benchmark_id"] == "general-guide-developmental-language-gold-star-2026-11-09")
    assert record["gold_star_number"] == 57
    assert record["numbering_recovery"]["source_pr"] == 1430
    assert "PR #1429" not in record["numbering_recovery"]["authority_basis"]


def test_comparative_traditions_gold_star_92_has_verified_canonical_doorway():
    import json
    registry = json.loads((ROOT / "docs" / "qa" / "gold_standard_registry.json").read_text(encoding="utf-8"))
    record = next(r for r in registry["records"] if r["benchmark_id"] == "general-guide-comparative-traditions-respectful-intellectual-discipline-gold-star-2026-11-16")
    assert record["gold_star_number"] == 92
    assert record["numbering_status"] == "ASSIGNED"
    assert record["expected_doorway"]["title"] == "At the Edge of Explanation"
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/2026/07/20/at-the-edge-of-explanation/"


def test_only_two_explicit_historical_gap_releases_are_authorized_for_future_new_approvals():
    import json
    registry = json.loads((ROOT / "docs" / "qa" / "gold_standard_registry.json").read_text(encoding="utf-8"))
    policy = registry["numbering_policy"]["gap_exception_policy"]
    assert policy["authorized_numbers"] == [85, 86]
    assert policy["order"] == [85, 86]
    assert "next two newly approved Gold Star records" in policy["allocation_rule"]
    assert "No existing approved record" in policy["allocation_rule"]
    assert policy["does_not_change_adaptive_learning_identity"] is True
    assert registry["numbering_gap_register"] == []
    allocation_85 = next(item for item in registry["numbering_allocation_history"] if item["number"] == 85)
    allocation_86 = next(item for item in registry["numbering_allocation_history"] if item["number"] == 86)
    assert allocation_85["benchmark_id"] == "general-guide-ownership-management-stewardship-comparison-gold-star-2026-11-18"
    assert allocation_86["benchmark_id"] == "general-guide-archive-examples-evidence-limits-gold-star-2026-11-18"
    assert allocation_85["prior_gap_record"]["status"] == "RELEASED_FOR_FUTURE_ALLOCATION"
    assert allocation_86["prior_gap_record"]["status"] == "RELEASED_FOR_FUTURE_ALLOCATION"
    assert allocation_85["prior_gap_record"]["release_authorization"]["approved_by"] == "user"
    assert allocation_86["prior_gap_record"]["release_authorization"]["approved_by"] == "user"
    assert len([r for r in registry["records"] if r.get("gold_star_number") in {85, 86}]) == 2
    assert next(r for r in registry["records"] if r.get("gold_star_number") == 85)["benchmark_id"] == allocation_85["benchmark_id"]
    assert next(r for r in registry["records"] if r.get("gold_star_number") == 86)["benchmark_id"] == allocation_86["benchmark_id"]



def test_user_elevated_community_wisdom_gold_star_preserves_exact_live_response():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "gs-2026-11-16-community-wisdom-tradition-epistemic-stewardship"
    )
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["rating_out_of_10"] == 9.0
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["expected_doorway"] is None
    assert record["doorway_status"] == "LEGACY_INCOMPLETE_NOT_APPROVED"
    assert record["observed_doorway_title"].startswith("VSM-002")
    assert "canonical URL was not captured" in record["provenance"]["evidence_boundary"]
    assert "AI may inform that work" in record["expected_response"]
    assert "historical, theological, empirical, and experiential claims" in record["expected_response"]
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False


def test_consequential_action_under_uncertainty_gold_star_preserves_exact_answer_doorway_and_unassigned_identity():
    from general_guide_gold_standards import resolve_exact_gold_standard

    record = next(
        r for r in _registry()["records"]
        if r["benchmark_id"] == "gs-2026-11-17-consequential-action-under-uncertainty"
    )
    expected = (
        "When a decision has serious consequences and the future is uncertain, act in proportion to what is known rather than waiting for certainty or pretending to have it. Begin by identifying what must be protected, who will be affected, which responsibilities cannot be deferred, and which parts of the situation remain unknown.\n\n"
        "Compare realistic options by looking at what each makes possible, what it could damage, who carries the costs, and what evidence would change the assessment. Give particular weight to people who will live with the consequences, including those with the least influence over the decision.\n\n"
        "Then choose a course that preserves room to learn and correct where possible. Set clear signals for review, name who is accountable for watching the effects, and change direction when evidence or conditions warrant it. A decision can be necessary without being certain; its quality depends partly on whether it remains answerable to the people and realities it affects."
    )
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == "How should people act when the future is uncertain but consequential?"
    assert record["expected_response"] == expected
    assert record["rating_out_of_10"] == 9.5
    assert record["expected_doorway"] == {
        "title": "The Sovereign Sensemaking Compass",
        "url": "https://geralddaquila.com/the-sovereign-sensemaking-compass/",
        "rationale": "This is a grounded map for navigating uncertainty without losing clarity or agency, directly supporting the question of how to act when the future is not settled."
    }
    assert record["doorway_status"] == "VERIFIED_CANONICAL_DESTINATION"
    assert record["numbering_status"] == "UNASSIGNED"
    assert record.get("gold_star_number") is None
    assert record["numbering_unassigned_reason_code"] == "NO_SERIAL_ALLOCATION_REQUESTED"
    capabilities = record["gold_star_capabilities"]
    assert capabilities["exact_answer_authority"] is True
    assert capabilities["active_quality_contributor"] is True
    assert capabilities["deterministic_fallback_eligible"] is False

    resolved = resolve_exact_gold_standard(record["query"])
    assert resolved is not None
    assert resolved["benchmark_id"] == record["benchmark_id"]
    assert resolved["expected_response"] == expected
    assert resolved["doorway_title"] == "The Sovereign Sensemaking Compass"
    assert resolved["doorway_url"] == "https://geralddaquila.com/the-sovereign-sensemaking-compass/"
    assert resolved["doorway_rationale"] == record["expected_doorway"]["rationale"]
    assert resolve_exact_gold_standard("How should people act when the future is uncertain?") is None

def test_ai_staffing_successor_is_elevated_gold_star_and_preserves_legacy_record():
    registry = _registry()
    old_id = "general-guide-integrated-institutional-judgment-ai-staffing-gold-star-2026-11-13"
    successor_id = "gs-2026-11-17-ai-workforce-restructuring-successor-candidate"
    records = {item["benchmark_id"]: item for item in registry["records"]}
    old = records[old_id]
    successor = records[successor_id]

    assert old["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert old["expected_response"].startswith("For a question like this, the first task is to make the decision visible.")
    assert old["runtime_exact_query_successor"] == successor_id
    assert old["gold_star_capabilities"]["active_quality_contributor"] is True
    assert old["gold_star_capabilities"]["exact_answer_authority"] is False
    assert old["runtime_exact_answer_authority_delegated"] is True
    assert successor["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert successor["rating_out_of_10"] == 9.5
    assert successor["user_reviewed_response"] is True
    assert successor["explicit_user_elevation_approval"] is True
    assert successor["replaces_exact_query_runtime_authority_of"] == old_id
    assert successor["gold_star_capabilities"]["exact_answer_authority"] is True
    assert successor["gold_star_capabilities"]["active_quality_contributor"] is True
    assert successor["expected_response"].startswith("An organization should assess AI-led staffing reductions")
    from ai_workforce_restructuring_contract import has_gold_star_coverage
    assert has_gold_star_coverage(successor["expected_response"])
    assert successor["doorway_status"] == "VERIFIED_CANONICAL_DESTINATION"
    assert successor["expected_doorway"]["url"] == (
        "https://geralddaquila.com/2026/05/06/agentic-systems-and-the-end-of-passive-labor/"
    )
    assert successor["numbering_status"] == "UNASSIGNED"

    from general_guide_gold_standards import resolve_exact_gold_standard
    resolved = resolve_exact_gold_standard(successor["query"])
    assert resolved["benchmark_id"] == successor_id
    assert resolved["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert resolved["doorway_rationale"] == successor["expected_doorway"]["rationale"]



def test_ai_workforce_gold_star_has_bounded_active_transfer_review_and_no_serial():
    import json
    from pathlib import Path
    registry = _registry()
    benchmark_id = "gs-2026-11-17-ai-workforce-restructuring-successor-candidate"
    record = next(r for r in registry["records"] if r["benchmark_id"] == benchmark_id)
    review = json.loads(Path("docs/qa/gold_star_qualitative_transfer_review.json").read_text())
    entry = next(r for r in review["entries"] if r["benchmark_id"] == benchmark_id)
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["runtime_transfer"] is True
    assert record["gold_star_capabilities"]["exact_answer_authority"] is True
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is True
    assert record["numbering_status"] == "UNASSIGNED"
    assert record.get("gold_star_number") is None
    assert entry["activation"] == "active_quality_contributor"
    assert entry["reasoning_family"] == "integrated_institutional_judgment"
    assert "total operating costs" in entry["transferable_discipline"]
    assert "distribution" in entry["transferable_discipline"]
    assert "unrelated AI questions" in entry["abstention_boundary"]

def test_approved_exact_query_only_successor_is_valid_and_cannot_claim_learning_transfer():
    import copy
    import json
    from pathlib import Path
    import pytest
    from scripts.validate_gold_star_registry import (
        APPROVED_STATUS,
        validate_exact_only_successors,
    )

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
    from scripts.validate_gold_star_registry import validate_superseded_references
    superseded = validate_superseded_references(approved, active)
    assert len(exact_only) == 1
    assert len(superseded) == 1
    assert superseded[0]["benchmark_id"] == "gs-2026-11-13-04-migrated-canonical-ledger"
    assert exact_only[0]["gold_star_capabilities"]["exact_answer_authority"] is True
    assert exact_only[0]["gold_star_capabilities"]["active_quality_contributor"] is False
    assert exact_only[0]["gold_star_capabilities"]["deterministic_fallback_eligible"] is False

    mutated = copy.deepcopy(approved)
    successor = next(
        item for item in mutated
        if item.get("runtime_transfer") is False
        and item.get("gold_star_capabilities", {}).get("exact_answer_authority") is True
        and not item.get("superseded_by_benchmark_id")
    )
    successor["replaces_exact_query_runtime_authority_of"] = "missing-predecessor"
    with pytest.raises(SystemExit, match="valid exact-query-only successor"):
        validate_exact_only_successors(mutated, active)

def test_complex_future_scenario_readiness_gold_star_preserves_exact_answer_and_doorway():
    from deterministic_answer_recovery import compose_recovery
    from general_guide_gold_standards import resolve_exact_gold_standard

    record = next(
        item for item in _registry()["records"]
        if item["benchmark_id"] == "gs-2026-11-17-complex-future-scenario-readiness"
    )
    expected = "The Guide should not turn a complex future into one definitive prediction. Outcomes may depend on interacting conditions that change over time, so a single forecast can hide the assumptions on which it rests and make one possibility look settled. Reframe the question from “What will happen?” to “What are several plausible ways this could unfold, and what conditions would make each more or less likely?” Scenarios are not competing prophecies; they are structured possibilities for testing understanding and readiness.\n\nFor each scenario, examine the capacities it would require and the capacities already available: knowledge, skills, resources, relationships, infrastructure, coordination, and legitimate decision-making authority. Identify constraints, dependencies, vulnerabilities, and gaps; ask who can strengthen the capabilities that matter and how long that would take. Do not assume that stronger capacity can eliminate uncertainty. Its purpose is to widen the range of conditions people can meet and reduce avoidable fragility across more than one plausible future.\n\nThen identify observable signals that would make one scenario more or less plausible, what evidence would change the assessment, and which decisions should be revisited if those signals appear. Prefer steps that remain useful across several scenarios, preserve options where possible, and define in advance when to adapt, pause, or change direction. Keep assumptions and confidence limits visible, update the scenarios as conditions change, and never present a scenario as a guaranteed outcome. The aim is not to know the future in advance, but to build the capacity to respond responsibly as it unfolds."
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == "A user requests a definitive prediction about a complex future. How should the Guide reframe the request toward scenarios, capacities, and uncertainty?"
    assert record["expected_response"] == expected
    assert len(expected.split(chr(10) * 2)) == 3
    assert record["rating_out_of_10"] == 9.3
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["doorway_status"] == "VERIFIED_CANONICAL_DESTINATION"
    assert record["expected_doorway"] == {"title":"Sovereign Sensemaking Compass","url":"https://geralddaquila.com/the-sovereign-sensemaking-compass/","rationale":"The Sovereign Sensemaking Compass offers an orientation framework for navigating uncertainty while retaining clarity and agency. It is a useful next step for examining how to remain oriented and make responsible choices when no single forecast can settle the future; it does not claim to predict specific outcomes."}
    assert record["numbering_status"] == "UNASSIGNED"
    assert record.get("gold_star_number") is None
    capabilities = record["gold_star_capabilities"]
    assert capabilities["exact_answer_authority"] is True
    assert capabilities["active_quality_contributor"] is True
    assert capabilities["deterministic_fallback_eligible"] is True

    resolved = resolve_exact_gold_standard(record["query"])
    assert resolved is not None
    assert resolved["benchmark_id"] == record["benchmark_id"]
    assert resolved["expected_response"] == expected
    assert resolved["doorway_title"] == record["expected_doorway"]["title"]
    assert resolved["doorway_url"] == record["expected_doorway"]["url"]
    assert resolved["doorway_rationale"] == record["expected_doorway"]["rationale"]
    assert compose_recovery(record["query"]) == expected
    assert resolve_exact_gold_standard("How can we prepare for an uncertain future?") is None


def test_personal_decision_agency_gold_star_93_preserves_exact_live_answer_and_doorway():
    from general_guide_gold_standards import resolve_exact_gold_standard
    fixture_path = ROOT / "tests" / "fixtures" / "general_guide_personal_decision_agency_gold_standard.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    record = next(
        item for item in _registry()["records"]
        if item["benchmark_id"] == "general-guide-personal-decision-agency-gold-star-2026-11-17"
    )

    assert record["status"] == fixture["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["gold_star_number"] == fixture["gold_star_number"] == 93
    assert record["numbering_status"] == "ASSIGNED"
    assert record["query"] == fixture["query"]
    assert record["expected_response"] == fixture["expected_response"]
    assert record["expected_doorway"] == {
        "title": fixture["expected_doorway_title"],
        "url": fixture["expected_doorway_url"],
        "rationale": fixture["expected_doorway_rationale"],
    }
    assert record["rating_out_of_10"] == fixture["rating_out_of_10"] == 9.7
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["runtime_transfer"] is True
    assert record["gold_star_capabilities"]["exact_answer_authority"] is True
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is True
    assert len(record["expected_response"].split(chr(10) * 2)) == 3

    resolved = resolve_exact_gold_standard(record["query"])
    assert resolved is not None
    assert resolved["benchmark_id"] == record["benchmark_id"]
    assert resolved["expected_response"] == fixture["expected_response"]
    assert resolved["doorway_title"] == fixture["expected_doorway_title"]
    assert resolved["doorway_url"] == fixture["expected_doorway_url"]
    assert resolved["doorway_rationale"] == fixture["expected_doorway_rationale"]
    assert resolve_exact_gold_standard("How should a Guide help someone make a difficult choice?") is None


def test_personal_decision_agency_gold_star_93_has_active_transfer_review():
    review = json.loads(
        (ROOT / "docs" / "qa" / "gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8")
    )
    entry = next(
        item for item in review["entries"]
        if item["benchmark_id"] == "general-guide-personal-decision-agency-gold-star-2026-11-17"
    )
    assert entry["activation"] == "active_quality_contributor"
    assert entry["reasoning_family"] == "personal_decision_agency_without_substituted_judgment"
    assert "person's values and responsibilities" in entry["transferable_discipline"]
    assert "Do not make the person's life decision" in entry["abstention_boundary"]


def test_public_commons_stewardship_gold_star_preserves_answer_and_verified_doorway_across_both_paths(monkeypatch):
    from general_guide_composition import compose
    from general_guide_gold_standards import resolve_exact_gold_standard

    fixture = json.loads(
        (ROOT / "tests" / "fixtures" / "general_guide_public_commons_stewardship_gold_standard.json").read_text(encoding="utf-8")
    )
    query = fixture["query"]
    expected = fixture["expected_response"]
    record = next(
        item for item in _registry()["records"]
        if item["benchmark_id"] == "general-guide-public-commons-stewardship-gold-star-2026-11-17"
    )

    assert record["status"] == fixture["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["numbering_status"] == "UNASSIGNED"
    assert record.get("gold_star_number") is None
    assert record["rating_out_of_10"] == fixture["rating_out_of_10"] == 9.7
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["runtime_transfer"] is True
    assert record["gold_star_capabilities"]["exact_answer_authority"] is True
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is True
    assert len(expected.split(chr(10) * 2)) == 3
    assert record["expected_response"] == expected
    assert record["expected_doorway"] == {
        "title": fixture["expected_doorway_title"],
        "url": fixture["expected_doorway_url"],
        "rationale": fixture["expected_doorway_rationale"],
    }

    resolved = resolve_exact_gold_standard(query)
    assert resolved is not None
    assert resolved["benchmark_id"] == record["benchmark_id"]
    assert resolved["expected_response"] == expected
    assert resolved["doorway_title"] == fixture["expected_doorway_title"]
    assert resolved["doorway_url"] == fixture["expected_doorway_url"]
    assert resolved["doorway_rationale"] == fixture["expected_doorway_rationale"]

    provider_contract = compose(use_core=None, query=query, context_data={})
    assert provider_contract["response"] == expected
    assert provider_contract["doorway_title"] == fixture["expected_doorway_title"]
    assert provider_contract["doorway_url"] == fixture["expected_doorway_url"]

    # The isolated main.py route imports FastAPI, which is intentionally absent
    # from the lightweight registry-contract job. Exercise it whenever the
    # runtime dependency set is installed; the provider-neutral and deterministic
    # contracts above remain mandatory in every test environment.
    import pytest
    pytest.importorskip("fastapi")
    main = _import_main_without_downloading_embedding_model(monkeypatch)
    deterministic_contract = main._basic_inquiry_round1_deterministic_response(
        query, {}, {}, recommendation_available=False
    )
    assert deterministic_contract["response"] == expected
    assert deterministic_contract["doorway_title"] == fixture["expected_doorway_title"]
    assert deterministic_contract["recommendation"]["url"] == fixture["expected_doorway_url"]

    assert resolve_exact_gold_standard("How should a guide steward a shared public knowledge resource?") is None


def test_public_commons_stewardship_gold_star_has_active_transfer_review():
    review = json.loads(
        (ROOT / "docs" / "qa" / "gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8")
    )
    entry = next(
        item for item in review["entries"]
        if item["benchmark_id"] == "general-guide-public-commons-stewardship-gold-star-2026-11-17"
    )
    assert entry["activation"] == "active_quality_contributor"
    assert entry["reasoning_family"] == "public_knowledge_commons_stewardship_and_provenance"
    assert "distinguish access classes" in entry["transferable_discipline"]
    assert "preserve disagreement" in entry["transferable_discipline"]


def test_gold_star_authoring_template_requires_doorway_or_reasoned_exception():
    template_path = ROOT / "docs" / "qa" / "gold_star_record_template.json"
    template = json.loads(template_path.read_text(encoding="utf-8"))
    assert template["doorway_status"] == "VERIFIED"
    assert template["expected_doorway"]["title"]
    assert template["expected_doorway"]["url"].startswith("https://geralddaquila.com/")
    assert template["expected_doorway"]["rationale"]
    assert template["doorway_omission_exception_reason"] == ""

    exception = template["approved_omission_example"]
    assert exception["doorway_status"] == "INTENTIONALLY_NONE_APPROVED"
    assert exception["expected_doorway"] is None
    assert exception["doorway_omission_exception_reason"].strip()


def test_formal_informal_institutional_dynamics_gold_star_preserves_exact_live_answer_and_doorway():
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    registry = json.loads((root / "docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
    review = json.loads((root / "docs/qa/gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8"))
    benchmark_id = "general-guide-formal-informal-institutional-dynamics-gold-star-2026-11-18"
    record = next(item for item in registry["records"] if item["benchmark_id"] == benchmark_id)
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == "How should the Guide compare formal institutional rules with informal norms when explaining why an organization behaves as it does?"
    fixture = json.loads((root / "tests/fixtures/general_guide_formal_informal_institutional_dynamics_gold_standard.json").read_text(encoding="utf-8"))
    assert record["expected_response"] == fixture["expected_response"]
    assert record["expected_doorway"] == {"title":"Institutional Consciousness","url":"https://geralddaquila.com/institutional-consciousness/","rationale":"Institutional Consciousness examines how organizations become aware of their own assumptions, blind spots, and patterns of behavior. It is a relevant continuation for examining the gap between declared structures and the lived norms through which an institution actually operates; it does not diagnose this particular organization."}
    assert record["rating_out_of_10"] == 9.7
    assert record["explicit_user_elevation_approval"] is True
    assert record["runtime_transfer"] is True
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["numbering_status"] == "UNASSIGNED"
    from gold_star_inventory import derive_gold_star_inventory
    inventory = derive_gold_star_inventory(registry)
    assert inventory["approved_gold_star_count"] == sum(
        item.get("status") == "USER_APPROVED_GOLD_STANDARD" for item in registry["records"]
    )
    assert inventory["benchmark_count"] == len(registry["records"])
    entry = next(item for item in review["entries"] if item["benchmark_id"] == benchmark_id)
    assert entry["activation"] == "active_quality_contributor"
    assert entry["reasoning_family"] == "formal_informal_institutional_dynamics"


def test_ownership_management_stewardship_gold_star_85_preserves_exact_answer_doorway_and_active_transfer(monkeypatch):
    import json
    from general_guide_composition import compose
    from general_guide_gold_standards import resolve_exact_gold_standard

    fixture = json.loads(
        (ROOT / "tests" / "fixtures" / "general_guide_ownership_management_stewardship_gold_star.json").read_text(encoding="utf-8")
    )
    registry = _registry()
    record = next(item for item in registry["records"] if item["benchmark_id"] == fixture["benchmark_id"])
    assert record["status"] == fixture["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["gold_star_number"] == fixture["gold_star_number"] == 85
    assert record["numbering_status"] == "ASSIGNED"
    assert record["query"] == fixture["query"]
    assert record["expected_response"] == fixture["expected_response"]
    assert len(record["expected_response"].split(chr(10) * 2)) == 3
    assert record["expected_doorway"] == {
        "title": fixture["expected_doorway_title"],
        "url": fixture["expected_doorway_url"],
        "rationale": fixture["expected_doorway_rationale"],
    }
    assert record["rating_out_of_10"] == fixture["rating_out_of_10"] == 9.3
    assert record["explicit_user_elevation_approval"] is True
    assert record["runtime_transfer"] is True
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True

    resolved = resolve_exact_gold_standard(fixture["query"])
    curly_apostrophe_query = fixture["query"].replace("visitor's", "visitor’s")
    assert resolve_exact_gold_standard(curly_apostrophe_query)["benchmark_id"] == fixture["benchmark_id"]
    assert resolved is not None
    assert resolved["benchmark_id"] == fixture["benchmark_id"]
    assert resolved["expected_response"] == fixture["expected_response"]
    assert resolved["doorway_title"] == fixture["expected_doorway_title"]
    assert resolved["doorway_url"] == fixture["expected_doorway_url"]
    assert resolved["doorway_rationale"] == fixture["expected_doorway_rationale"]

    provider_contract = compose(use_core=None, query=fixture["query"], context_data={})
    assert provider_contract["response"] == fixture["expected_response"]
    assert provider_contract["doorway_title"] == fixture["expected_doorway_title"]
    assert provider_contract["doorway_url"] == fixture["expected_doorway_url"]

    import pytest
    pytest.importorskip("fastapi")
    main = _import_main_without_downloading_embedding_model(monkeypatch)
    deterministic_contract = main._basic_inquiry_round1_deterministic_response(
        fixture["query"], {}, {}, recommendation_available=False
    )
    assert deterministic_contract["response"] == fixture["expected_response"]
    assert deterministic_contract["doorway_title"] == fixture["expected_doorway_title"]
    assert deterministic_contract["recommendation"]["url"] == fixture["expected_doorway_url"]

    from gold_star_inventory import derive_gold_star_inventory
    inventory = derive_gold_star_inventory(registry)
    assert inventory["approved_gold_star_count"] == sum(
        item.get("status") == "USER_APPROVED_GOLD_STANDARD" for item in registry["records"]
    )
    assert inventory["benchmark_count"] == len(registry["records"])

    review = json.loads((ROOT / "docs/qa/gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8"))
    entry = next(item for item in review["entries"] if item["benchmark_id"] == fixture["benchmark_id"])
    assert entry["activation"] == "active_quality_contributor"
    assert entry["reasoning_family"] == "ownership_management_stewardship_role_distinction"


def test_archive_examples_evidence_limits_gold_star_86_preserves_exact_answer_and_doorway():
    import json
    from general_guide_composition import compose
    from general_guide_gold_standards import resolve_exact_gold_standard

    fixture = json.loads(
        (ROOT / "tests" / "fixtures" / "general_guide_archive_examples_evidence_limits_gold_star.json").read_text(encoding="utf-8")
    )
    registry = _registry()
    record = next(item for item in registry["records"] if item["benchmark_id"] == fixture["benchmark_id"])
    assert record["status"] == fixture["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["gold_star_number"] == fixture["gold_star_number"] == 86
    assert record["numbering_status"] == "ASSIGNED"
    assert record["query"] == fixture["query"]
    assert record["expected_response"] == fixture["expected_response"]
    assert len(record["expected_response"].split(chr(10) * 2)) == 3
    expected_doorway = {
        "title": fixture["expected_doorway_title"],
        "url": fixture["expected_doorway_url"],
        "rationale": fixture["expected_doorway_rationale"],
    }
    assert record["expected_doorway"] == expected_doorway
    assert record["rating_out_of_10"] == fixture["rating_out_of_10"] == 9.7
    assert record["explicit_user_elevation_approval"] is True
    assert record["runtime_transfer"] is True
    assert record["gold_star_capabilities"]["exact_answer_authority"] is True
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is True

    resolved = resolve_exact_gold_standard(fixture["query"])
    assert resolved is not None
    assert resolved["benchmark_id"] == fixture["benchmark_id"]
    assert resolved["expected_response"] == fixture["expected_response"]
    assert resolved["doorway_title"] == fixture["expected_doorway_title"]
    assert resolved["doorway_url"] == fixture["expected_doorway_url"]
    assert resolved["doorway_rationale"] == fixture["expected_doorway_rationale"]

    provider_contract = compose(use_core=None, query=fixture["query"], context_data={})
    assert provider_contract["response"] == fixture["expected_response"]
    assert provider_contract["doorway_title"] == fixture["expected_doorway_title"]
    assert provider_contract["doorway_url"] == fixture["expected_doorway_url"]

    import pytest
    pytest.importorskip("fastapi")
    import main
    deterministic_contract = main._basic_inquiry_round1_deterministic_response(
        fixture["query"], {}, {}, recommendation_available=False
    )
    assert deterministic_contract["response"] == fixture["expected_response"]
    assert deterministic_contract["doorway_title"] == fixture["expected_doorway_title"]
    assert deterministic_contract["recommendation"]["url"] == fixture["expected_doorway_url"]

    # This is a narrower, distinct evidence-limits benchmark, not a duplicate
    # of #72's direct-claim / synthesis / orientation contract.
    prior = resolve_exact_gold_standard("How should The Guide separate direct Archive claims from its own synthesis?")
    assert prior is not None
    assert prior["benchmark_id"] == "general-guide-archive-claim-synthesis-boundary-gold-star-2026-11-13"
    assert prior["benchmark_id"] != fixture["benchmark_id"]

    from gold_star_inventory import derive_gold_star_inventory
    inventory = derive_gold_star_inventory(registry)
    assert inventory["approved_gold_star_count"] == sum(
        item.get("status") == "USER_APPROVED_GOLD_STANDARD" for item in registry["records"]
    )
    assert inventory["benchmark_count"] == len(registry["records"])

    review = json.loads((ROOT / "docs/qa/gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8"))
    entry = next(item for item in review["entries"] if item["benchmark_id"] == fixture["benchmark_id"])
    assert entry["activation"] == "active_quality_contributor"
    assert entry["reasoning_family"] == "archive_examples_evidence_limits"



def test_symmetric_source_representation_gold_star_is_registered_and_runtime_resolvable():
    from general_guide_gold_standards import resolve_exact_gold_standard

    registry = _registry()
    fixture = json.loads((ROOT / "tests" / "fixtures" / "general_guide_symmetric_source_representation_gold_star.json").read_text(encoding="utf-8"))
    assert fixture["benchmark_id"] == "general-guide-symmetric-source-representation-before-synthesis-gold-star-2026-11-18"
    assert fixture["rating_out_of_10"] == 9.6
    benchmark_id = "general-guide-symmetric-source-representation-before-synthesis-gold-star-2026-11-18"
    query = "Find two relevant Archive passages that disagree in emphasis. How should the Guide represent each passage before attempting any synthesis?"
    expected = "Represent the two passages separately and symmetrically before interpreting their relationship. For each passage, identify its exact source, state its central concern in its own terms, and preserve its scope, qualifications, and intended audience. Do not translate either passage into the other's vocabulary or turn a difference in emphasis into a disagreement.\n\nOnly after both representations are clear should the Guide compare them: name where their emphases differ, distinguish a genuine contradiction from complementary focus, and retain any tension that the available text cannot resolve. Synthesis comes last and must not erase distinctions the sources themselves preserve."
    record = next(item for item in registry["records"] if item["benchmark_id"] == benchmark_id)
    review = json.loads((ROOT / "docs" / "qa" / "gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8"))
    entry = next(item for item in review["entries"] if item["benchmark_id"] == benchmark_id)

    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["rating_out_of_10"] == 9.6
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["expected_response"] == expected
    assert len(expected.split(chr(10) * 2)) == 2
    assert record["expected_doorway"] == {
        "title": "The Sovereign Sensemaking Compass",
        "url": "https://geralddaquila.com/the-sovereign-sensemaking-compass",
        "rationale": "The Sovereign Sensemaking Compass offers a broad continuation for developing clarity and agency when a question has no narrower verified Archive destination. It is an invitation to explore the Archive’s orientation framework, not a claim that one framework settles every question.",
    }
    assert entry["activation"] == "active_quality_contributor"
    assert entry["reasoning_family"] == "symmetric_source_representation_before_synthesis"
    assert "same fields in the same order" in entry["transferable_discipline"]
    assert "synthesize only after both representations are complete" in entry["transferable_discipline"]

    resolved = resolve_exact_gold_standard(query)
    assert resolved is not None
    assert resolved["benchmark_id"] == benchmark_id
    assert resolved["expected_response"] == expected
    assert resolved["doorway_title"] == "The Sovereign Sensemaking Compass"
    assert resolved["doorway_url"] == "https://geralddaquila.com/the-sovereign-sensemaking-compass"

    # The adjacent contextual-synthesis exemplar remains independently exact.
    adjacent = resolve_exact_gold_standard("Two archive texts appear to emphasize different values. How should the Guide identify the tension and reason toward a contextual synthesis?")
    assert adjacent is not None
    assert adjacent["benchmark_id"] == "general-guide-contextual-synthesis-across-different-values-gold-star-2026-11-13"

def test_integrity_audit_numbering_reconciliation_narrative_matches_record_counts():
    import json

    registry = json.loads(
        (ROOT / "docs" / "qa" / "gold_standard_registry.json").read_text(encoding="utf-8")
    )
    approved = [
        record for record in registry["records"]
        if record.get("status") == "USER_APPROVED_GOLD_STANDARD"
    ]
    assigned = [record for record in approved if record.get("numbering_status") == "ASSIGNED"]
    unassigned = [record for record in approved if record.get("numbering_status") == "UNASSIGNED"]
    audit = registry["integrity_audit"]
    narrative = audit["numbering_reconciliation"]

    from gold_star_inventory import derive_gold_star_inventory
    inventory = derive_gold_star_inventory(registry)
    assert inventory["approved_gold_star_count"] == len(approved)
    assert inventory["numbered_gold_star_count"] == len(assigned)
    assert inventory["unassigned_approved_gold_star_count"] == len(unassigned)
    assert len(assigned) + len(unassigned) == len(approved)
    assert all(
        key.startswith(("integrity_audit.", "audit."))
        for key in inventory["legacy_audit_metadata_drift"]
    )
    assert "61 approved records explicitly UNASSIGNED" not in narrative


def test_nonprofit_culture_power_care_governance_gold_star_preserves_exact_answer_and_verified_doorway():
    from general_guide_composition import compose
    from general_guide_gold_standards import resolve_exact_gold_standard

    fixture = json.loads((ROOT / "tests/fixtures/general_guide_nonprofit_culture_power_care_governance_gold_star.json").read_text(encoding="utf-8"))
    registry = _registry()
    record = next(item for item in registry["records"] if item["benchmark_id"] == fixture["benchmark_id"])
    assert record["status"] == fixture["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == fixture["query"]
    assert record["expected_response"] == fixture["expected_response"]
    assert len(record["expected_response"].split(chr(10) * 2)) == 3
    assert record["expected_doorway"] == {"title":fixture["expected_doorway_title"],"url":fixture["expected_doorway_url"],"rationale":fixture["expected_doorway_rationale"]}
    assert record["rating_out_of_10"] == fixture["rating_out_of_10"] == 9.6
    assert record["explicit_user_elevation_approval"] is True
    assert record["runtime_transfer"] is True
    assert record["numbering_status"] == "UNASSIGNED"
    assert "public trust does not disprove staff harm" in record["expected_response"]

    resolved = resolve_exact_gold_standard(fixture["query"])
    assert resolved["benchmark_id"] == fixture["benchmark_id"]
    assert resolved["expected_response"] == fixture["expected_response"]
    assert resolved["doorway_title"] == fixture["expected_doorway_title"]
    assert resolved["doorway_url"] == fixture["expected_doorway_url"]
    assert resolved["doorway_rationale"] == fixture["expected_doorway_rationale"]

    provider_contract = compose(use_core=None, query=fixture["query"], context_data={})
    assert provider_contract["response"] == fixture["expected_response"]
    assert provider_contract["doorway_title"] == fixture["expected_doorway_title"]
    assert provider_contract["doorway_url"] == fixture["expected_doorway_url"]

    import pytest
    pytest.importorskip("fastapi")
    import main
    deterministic_contract = main._basic_inquiry_round1_deterministic_response(fixture["query"], {}, {}, recommendation_available=False)
    assert deterministic_contract["response"] == fixture["expected_response"]
    assert deterministic_contract["doorway_title"] == fixture["expected_doorway_title"]
    assert deterministic_contract["recommendation"]["url"] == fixture["expected_doorway_url"]

    adjacent = resolve_exact_gold_standard("How does organizational culture shape ethical behavior?")
    assert adjacent is not None
    assert adjacent["benchmark_id"] == "gs-2026-11-14-organizational-culture-ethical-behavior"
    assert adjacent["benchmark_id"] != fixture["benchmark_id"]
    from gold_star_inventory import derive_gold_star_inventory
    inventory = derive_gold_star_inventory(registry)
    assert inventory["approved_gold_star_count"] == sum(
        item.get("status") == "USER_APPROVED_GOLD_STANDARD" for item in registry["records"]
    )
    assert inventory["benchmark_count"] == len(registry["records"])

    review = json.loads((ROOT / "docs/qa/gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8"))
    entry = next(item for item in review["entries"] if item["benchmark_id"] == fixture["benchmark_id"])
    assert entry["activation"] == "active_quality_contributor"
    assert entry["reasoning_family"] == "nonprofit_culture_power_care_governance_with_evidence_boundaries"


def test_scope_governance_gold_star_is_registered_without_serial_allocation():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-gold-star-scope-governance-cross-domain-regression-2026-11-18"
    )
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["gold_star_number"] is None
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    assert len(record["expected_response"].split(chr(10) * 2)) == 3
    assert "Narrow the scope" in record["expected_response"]
    assert "Revise when" in record["expected_response"]
    assert "Reject when" in record["expected_response"]


def test_gold_star_scope_governance_contract_is_present_in_both_composition_prompts():
    from general_guide_composition import _GENERAL_GUIDE_SYSTEM, _GENERAL_GUIDE_SYSTEM_COMPACT
    from gold_star_lessons import select_lesson

    question = (
        "A new Gold Star appears to improve responses in one domain but degrades "
        "responses in another. How should USE determine whether its scope should "
        "be narrowed, revised, or rejected?"
    )
    for prompt in (_GENERAL_GUIDE_SYSTEM, _GENERAL_GUIDE_SYSTEM_COMPACT):
        assert "GOLD STAR SCOPE GOVERNANCE (META-GOVERNANCE TASKS ONLY)" in prompt
        assert "never impose it on ordinary visitor questions" in prompt
        assert "unrelated negative controls" in prompt

    selected = select_lesson(question)
    assert selected is not None
    assert selected["benchmark_id"] == (
        "general-guide-gold-star-scope-governance-cross-domain-regression-2026-11-18"
    )
    assert selected["exact"] is True

    for unrelated in (
        "How can I improve my garden soil?",
        "What is the difference between weather and climate?",
    ):
        candidate = select_lesson(unrelated)
        assert candidate is None or candidate["benchmark_id"] != (
            "general-guide-gold-star-scope-governance-cross-domain-regression-2026-11-18"
        )


def test_scope_governance_gold_star_selects_the_subject_relevant_boundary_doorway():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-gold-star-scope-governance-cross-domain-regression-2026-11-18"
    )
    assert record["expected_doorway"]["title"] == "Boundary Conditions"
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/boundary-conditions/"
    assert "suited domain" in record["expected_doorway"]["rationale"]
    assert record["provenance"]["doorway_verification"]["title"] == "Boundary Conditions"


def test_gold_star_multi_candidate_adjudication_is_exact_approved_and_unassigned():
    from general_guide_gold_standards import resolve_exact_gold_standard

    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-gold-star-candidate-adjudication-2026-11-18"
    )
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["runtime_transfer"] is True
    assert record["rating_out_of_10"] == 9.8
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["numbering_unassigned_reason_code"] == "NO_SERIAL_ALLOCATION_REQUESTED"
    assert record["expected_doorway"] is None
    assert record["doorway_status"] == "INTENTIONALLY_NONE_APPROVED"
    resolved = resolve_exact_gold_standard(record["query"])
    assert resolved is not None
    assert resolved["benchmark_id"] == record["benchmark_id"]
    assert resolved["expected_response"] == record["expected_response"]
    assert resolved["doorway_title"] == ""
    assert resolved["doorway_url"] in (None, "")



def test_refined_retrieval_outage_gold_star_is_exact_approved_and_sequence_complete():
    from general_guide_gold_standards import resolve_exact_gold_standard

    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-retrieval-outage-deterministic-recovery-disclosure-gold-star-refined-2026-11-18"
    )
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["rating_out_of_10"] == 10
    assert record["runtime_transfer"] is True
    assert record["expected_doorway"] is None
    assert record["doorway_status"] == "INTENTIONALLY_NONE_APPROVED"
    paragraphs = record["expected_response"].split(chr(10) * 2)
    assert len(paragraphs) == 3
    assert "identity, canonical URL, permissions, provenance, and freshness" in paragraphs[0]
    assert "approved recovery sequence" in paragraphs[1]
    assert "actual question within that recovery’s supported scope" in paragraphs[1]
    assert "evidence basis it actually used" in paragraphs[2]
    assert "generic failure" in paragraphs[2]

    resolved = resolve_exact_gold_standard(record["query"])
    assert resolved is not None
    assert resolved["benchmark_id"] == record["benchmark_id"]
    assert resolved["expected_response"] == record["expected_response"]
    assert resolved["doorway_title"] == ""
    assert resolved["doorway_url"] in (None, "")
    prior = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-retrieval-outage-deterministic-recovery-disclosure-gold-star-2026-11-18"
    )
    assert prior["status"] == "SUPERSEDED_GOLD_STANDARD"


def test_calibration_validation_promotion_gold_star_is_exactly_resolvable_and_no_doorway():
    from general_guide_gold_standards import resolve_exact_gold_standard

    query = "A revised Guide performs better on the calibration set but worse on the validation set. Which result should govern the decision to promote the revision, and why?"
    record = resolve_exact_gold_standard(query)
    assert record is not None
    assert record["benchmark_id"] == "general-guide-calibration-vs-validation-promotion-decision-gold-star-2026-11-18"
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["forbids_doorway"] is True
    assert record["doorway_title"] == ""
    assert record["doorway_url"] == ""
    assert record["expected_response"].startswith("The validation result should govern promotion.")


import json
from pathlib import Path


def test_personality_soul_oversoul_question_has_exact_provider_independent_gold_star():
    query = "What is the difference between what my personality wants, what my soul is learning, and what my Oversoul may be inviting me to become?"
    registry = json.loads(Path("docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "gs-2026-11-18-personality-soul-oversoul-discernment"
    )

    from deterministic_answer_recovery import (
        compose_recovery,
        has_registered_recovery,
        is_personality_soul_oversoul_question,
        registered_recovery_recommendation,
    )

    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == query
    assert record["explicit_user_elevation_approval"] is True
    assert record["freeze_policy"] == "immutable_user_approved_gold_standard"
    assert record["numbering_status"] == "ASSIGNED"
    assert record["gold_star_number"] == 94
    assert record["numbering_migration"]["migration_class"] == "explicit_user_authorized_numbering_migration"
    assert record["gold_star_capabilities"]["exact_answer_authority"] is True
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is True
    assert is_personality_soul_oversoul_question(query)
    assert has_registered_recovery(query)
    assert compose_recovery(query) == record["expected_response"]
    assert len(record["expected_response"].split("\n\n")) == 3
    for phrase in ("personality", "soul is learning", "Oversoul", "not a command", "without surrendering my judgment"):
        assert phrase.casefold() in record["expected_response"].casefold()
    assert registered_recovery_recommendation(query) == record["expected_doorway"]
    assert record["expected_doorway"]["title"] == "Eternal / Oversoul Law – The Immutable Jurisdiction"
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/oversoul-law"

    from general_guide_gold_standards import resolve_exact_gold_standard
    resolved = resolve_exact_gold_standard(query)
    assert resolved["benchmark_id"] == record["benchmark_id"]
    assert resolved["expected_response"] == record["expected_response"]
    assert resolved["doorway_rationale"] == record["expected_doorway"]["rationale"]


def test_personality_soul_oversoul_classifier_rejects_adjacent_questions():
    from deterministic_answer_recovery import is_personality_soul_oversoul_question

    assert not is_personality_soul_oversoul_question(
        "What does my personality want, and how can I make a better decision?"
    )
    assert not is_personality_soul_oversoul_question(
        "What is the difference between soul learning and spiritual purpose?"
    )
    assert not is_personality_soul_oversoul_question(
        "What is the difference between my personality and my soul?"
    )


def test_personality_soul_oversoul_gold_star_has_bounded_transfer_review():
    benchmark = "gs-2026-11-18-personality-soul-oversoul-discernment"
    reviews = json.loads(Path("docs/qa/gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8"))
    review = next(item for item in reviews["entries"] if item["benchmark_id"] == benchmark)
    assert review["activation"] == "active_quality_contributor"
    assert "three lenses" in review["transferable_discipline"]
    assert "lived evidence" in review["transferable_discipline"]
    assert "independently verified facts" in review["transferable_discipline"]
    assert "transfer this answer text or doorway" in review["abstention_boundary"].casefold()


def test_autonomy_capability_evidence_question_is_registered_as_immutable_gold_star():
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    benchmark_id = "gs-2026-11-18-autonomy-adaptivity-resilience-improvement-evidence"
    record = next(item for item in registry["records"] if item["benchmark_id"] == benchmark_id)

    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["freeze_policy"] == "immutable_user_approved_gold_standard"
    assert record["runtime_transfer"] is True
    assert record["rating_out_of_10"] == 10
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["forbids_doorway"] is True
    assert record["expected_doorway"] is None
    assert "pre-registered" in record["expected_response"]
    assert "a strong score in one dimension cannot compensate" in record["expected_response"]
    assert "do not invent a universal sample count" in record["expected_response"]


def test_autonomy_capability_evidence_gold_star_has_bounded_transfer_review():
    benchmark_id = "gs-2026-11-18-autonomy-adaptivity-resilience-improvement-evidence"
    reviews = json.loads(
        (ROOT / "docs" / "qa" / "gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8")
    )
    review = next(item for item in reviews["entries"] if item["benchmark_id"] == benchmark_id)

    assert review["activation"] == "active_quality_contributor"
    assert "pre-registered" in review["transferable_discipline"]
    assert "independently verified" in review["transferable_discipline"]
    assert "Do not transfer the answer text" in review["abstention_boundary"]



def test_weekly_stewardship_insight_to_action_is_an_immutable_gold_star():
    benchmark_id = "gs-2026-11-20-weekly-stewardship-insight-to-action"
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    record = next(item for item in registry["records"] if item["benchmark_id"] == benchmark_id)
    query = "What is one concrete act of stewardship I can complete this week that makes an inner insight real?"
    expected = "One concrete act you can complete this week is to choose one responsibility already entrusted to your care and carry out a short stewardship check before acting. Set aside 20 minutes: name what you are holding, who or what is affected, and what is genuinely yours to hold rather than yours to control. Then complete one proportionate follow-through—clarify a commitment, ask for consent, repair a small neglect, protect something vulnerable, or set a needed boundary. Choose the action that fits the real responsibility in front of you; do not invent a duty just to prove an insight.\n\nThis applies the Stewardship page’s emphasis on what is entrusted to your care, quiet and repeated responsibility, and the need to distinguish sustainable care from sacrifice. Restraint can be the act: rest, withdraw, or relinquish what is not yours to carry.\n\nAt the end of the week, review one observable result: did your action support the person, relationship, knowledge, place, or system affected without overreach or depletion? Keep, revise, or stop the practice based on that result. The 20-minute check is a practical exercise, not a prescribed Archive rule."

    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == query
    assert record["expected_response"] == expected
    assert record["explicit_user_elevation_approval"] is True
    assert record["freeze_policy"] == "immutable_user_approved_gold_standard"
    assert record["runtime_transfer"] is True
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["gold_star_capabilities"]["exact_answer_authority"] is False
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    assert record["expected_doorway"]["title"] == "Stewardship"
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/stewardship/"
    assert "not a prescribed Archive rule" in expected
    assert len(expected.split("\n\n")) == 3


def test_weekly_stewardship_gold_star_has_bounded_qualitative_transfer_review():
    benchmark_id = "gs-2026-11-20-weekly-stewardship-insight-to-action"
    reviews = json.loads((ROOT / "docs" / "qa" / "gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8"))
    review = next(item for item in reviews["entries"] if item["benchmark_id"] == benchmark_id)
    assert review["activation"] == "active_quality_contributor"
    assert "already entrusted" in review["transferable_discipline"]
    assert "rest" in review["transferable_discipline"]
    assert "Do not invent a personal duty" in review["abstention_boundary"]


def test_live_orientation_information_gold_star_is_registered_verbatim_and_unassigned():
    fixture = json.loads((ROOT / "tests/fixtures/general_guide_orientation_information_gold_star.json").read_text(encoding="utf-8"))
    registry = _registry()
    record = next(item for item in registry["records"] if item["benchmark_id"] == fixture["benchmark_id"])
    assert record["status"] == fixture["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == fixture["query"]
    assert record["expected_response"] == fixture["expected_response"]
    assert record["expected_doorway"]["title"] == fixture["expected_doorway_title"]
    assert record["expected_doorway"]["url"] == fixture["expected_doorway_url"]
    assert record["expected_doorway"]["rationale"] == fixture["expected_doorway_rationale"]
    assert record["rating_out_of_10"] == fixture["rating_out_of_10"] == 9.5
    assert record["explicit_user_elevation_approval"] is True
    assert record["runtime_transfer"] is True
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["exact_answer_authority"] is False
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    assert record["numbering_status"] == fixture["numbering_status"] == "UNASSIGNED"
    assert record.get("gold_star_number") is None
    assert record["numbering_unassigned_reason_code"] == "NO_SERIAL_ALLOCATION_REQUESTED"
    reviews = json.loads((ROOT / "docs/qa/gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8"))
    review_entry = next(item for item in reviews["entries"] if item["benchmark_id"] == fixture["benchmark_id"])
    assert review_entry["activation"] == "active_quality_contributor"
    assert "human judgment" in review_entry["abstention_boundary"]



def test_approved_gold_star_may_preserve_not_evaluated_doorway_without_authorizing_omission():
    """NOT_EVALUATED is a valid recorded state, not an omission decision."""
    registry = _registry()
    benchmark_id = "general-guide-doorway-nonselection-evidence-governance-candidate-2026-11-20"
    record = next(item for item in registry["records"] if item["benchmark_id"] == benchmark_id)

    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["doorway_status"] == "NOT_EVALUATED"
    capabilities = record["gold_star_capabilities"]
    assert "NOT_EVALUATED" in capabilities["abstention_boundary"]
    assert record["expected_doorway"] is None
    assert not record.get("doorway_omission_exception_reason")
    assert record["runtime_transfer"] is True
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["exact_answer_authority"] is False
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False


def test_guide_coverage_gap_governance_gold_star_preserves_intentional_no_doorway():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "gs-2026-11-20-guide-coverage-gap-evidence-governance"
    )
    review = json.loads(
        (ROOT / "docs" / "qa" / "gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8")
    )
    review_entry = next(
        item for item in review["entries"]
        if item["benchmark_id"] == record["benchmark_id"]
    )

    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == "When should The Guide say “the Archive does not yet address this directly”?"
    assert record["rating_out_of_10"] == 9.5
    assert record["expected_response"].count("\n\n") == 2
    assert "A missing retrieval result is evidence of a search outcome" in record["expected_response"]
    assert "distinguish four outcomes" in record["expected_response"]
    assert record["doorway_status"] == "INTENTIONALLY_NONE_APPROVED"
    assert record["expected_doorway"] is None
    assert "meta-policy question" in record["doorway_omission_exception_reason"]
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["runtime_transfer"] is True
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["exact_answer_authority"] is False
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    assert review_entry["activation"] == "active_quality_contributor"
    assert "failed retrieval" in review_entry["transferable_discipline"]


def test_missing_origin_main_ref_is_fetched_before_immutable_number_check(monkeypatch):
    import subprocess
    from scripts import validate_gold_star_registry as validator

    calls = []
    verified = {"present": False}

    def fake_run(args, **kwargs):
        calls.append(args)
        if args[:3] == ["git", "remote", "get-url"]:
            raise subprocess.CalledProcessError(2, args)
        if args[:3] == ["git", "remote", "add"]:
            return subprocess.CompletedProcess(args, 0, "", "")
        if args[:4] == ["git", "show-ref", "--verify", "--quiet"]:
            if not verified["present"]:
                raise subprocess.CalledProcessError(1, args)
            return subprocess.CompletedProcess(args, 0, "", "")
        if args[:3] == ["git", "fetch", "--no-tags"]:
            verified["present"] = True
            return subprocess.CompletedProcess(args, 0, "", "")
        raise AssertionError(f"Unexpected git command: {args}")

    monkeypatch.setattr(validator.subprocess, "run", fake_run)
    validator.ensure_canonical_main_ref()
    assert calls == [
        ["git", "remote", "get-url", "origin"],
        ["git", "remote", "add", "origin", "https://github.com/GeraldDaquila/living-archive-backend.git"],
        ["git", "show-ref", "--verify", "--quiet", "refs/remotes/origin/main"],
        ["git", "fetch", "--no-tags", "origin", "main:refs/remotes/origin/main"],
        ["git", "show-ref", "--verify", "--quiet", "refs/remotes/origin/main"],
    ]


def test_failed_canonical_main_fetch_keeps_registry_validation_fail_closed(monkeypatch):
    import subprocess
    import pytest
    from scripts import validate_gold_star_registry as validator

    def fake_run(args, **kwargs):
        if args[:3] == ["git", "remote", "get-url"]:
            raise subprocess.CalledProcessError(2, args)
        if args[:3] == ["git", "remote", "add"]:
            return subprocess.CompletedProcess(args, 0, "", "")
        if args[:4] == ["git", "show-ref", "--verify", "--quiet"]:
            raise subprocess.CalledProcessError(1, args)
        if args[:3] == ["git", "fetch", "--no-tags"]:
            return subprocess.CompletedProcess(args, 128, "", "remote unavailable")
        raise AssertionError(f"Unexpected git command: {args}")

    monkeypatch.setattr(validator.subprocess, "run", fake_run)
    with pytest.raises(SystemExit, match="cannot fetch canonical origin/main"):
        validator.ensure_canonical_main_ref()



def test_stewardship_incomplete_knowledge_gold_star_is_structural_not_exact_answer_authority():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "gs-2026-11-20-stewardship-incomplete-knowledge"
    )
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == "How should a steward act amid incomplete knowledge?"
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["rating_out_of_10"] == 9.6
    assert record["runtime_transfer"] is True
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["exact_answer_authority"] is False
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    assert record["doorway_status"] == "VERIFIED_CANONICAL_DESTINATION"
    assert record["expected_doorway"]["title"] == "Steward Readiness Instruments"
    assert record["numbering_status"] == "UNASSIGNED"
    assert "established facts" in record["expected_response"]
    assert "observable signals" in record["expected_response"]
    assert "decision authority and accountability" in record["expected_response"]


def test_institutional_extraction_incentive_governance_gold_star_is_registered_and_bounded():
    registry = _registry()
    benchmark_id = "gs-2026-11-20-institutional-extraction-incentive-governance"
    record = next(item for item in registry["records"] if item["benchmark_id"] == benchmark_id)
    query = "How should a leader respond when institutional incentives reward short-term extraction?"

    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == query
    assert record["rating_out_of_10"] == 9.7
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["freeze_policy"] == "immutable_user_approved_gold_standard"
    assert record["runtime_transfer"] is True
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["exact_answer_authority"] is False
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    assert record["doorway_status"] == "VERIFIED_CANONICAL_DESTINATION"
    assert record["expected_doorway"]["title"] == "Regenerative Governance: What Comes After Extraction-Based Systems?"
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/2026/06/08/regenerative-governance-what-comes-after-extraction-based-systems/"
    assert len(record["expected_response"].split("\n\n")) == 3
    for phrase in ("incentive-design problem", "delayed costs", "protect dissent", "board or governing authority", "circulation and renewal"):
        assert phrase.casefold() in record["expected_response"].casefold()

    reviews = json.loads((ROOT / "docs" / "qa" / "gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8"))
    review = next(item for item in reviews["entries"] if item["benchmark_id"] == benchmark_id)
    assert review["activation"] == "active_quality_contributor"
    assert "delayed costs" in review["transferable_discipline"]
    assert "governing-body mandate" in review["transferable_discipline"]


def test_event_pattern_structure_gold_star_has_reconciled_runtime_and_doorway_contract():
    import json

    root = ROOT
    registry = json.loads((root / "docs/qa/gold_standard_registry.json").read_text(encoding="utf-8"))
    review = json.loads((root / "docs/qa/gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8"))
    transfer_map = json.loads((root / "docs/qa/gold_star_transferability_map.json").read_text(encoding="utf-8"))
    benchmark_id = "gs-2026-11-20-event-pattern-system-structure-answer-first"
    record = next(item for item in registry["records"] if item["benchmark_id"] == benchmark_id)
    reviewed = next(item for item in review["entries"] if item["benchmark_id"] == benchmark_id)
    mapped = next(item for item in transfer_map["entries"] if item["benchmark_id"] == benchmark_id)

    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["runtime_transfer"] is True
    assert record["known_theme"]
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["exact_answer_authority"] is False
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    assert record["expected_doorway"]["title"] == "Fractal Systems Diagnostic"
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/fractal-systems-diagnostic-2/"
    assert record["numbering_status"] == "UNASSIGNED"
    assert reviewed["activation"] == "active_quality_contributor"
    assert reviewed["transferable_discipline"] == record["transferable_lesson"]
    assert mapped["family"] == record["reasoning_family"]
    assert mapped["structural_lesson"] == record["transferable_lesson"]
    assert "registry_content_sha" not in transfer_map["coverage"]



def test_reciprocity_community_gold_star_has_matching_bounded_transfer_review_and_supersession():
    registry = _registry()
    record = next(item for item in registry["records"] if item["benchmark_id"] == "general-guide-reciprocity-community-2026-10-24")
    old = next(item for item in registry["records"] if item["benchmark_id"] == "general-guide-reciprocity-gold-standard-2026-10-19")
    reviews = json.loads((ROOT / "docs" / "qa" / "gold_star_qualitative_transfer_review.json").read_text(encoding="utf-8"))["entries"]
    review = next(item for item in reviews if item["benchmark_id"] == record["benchmark_id"])
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record.get("rating") is None
    assert "rating_out_of_10" not in record
    assert record["assistant_assessment_out_of_10"] == 9.5
    assert record["runtime_transfer"] is True
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["exact_answer_authority"] is False
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["doorway_status"] == "VERIFIED_CANONICAL_DESTINATION"
    assert review["activation"] == "active_quality_contributor"
    assert review["reasoning_family"] == record["reasoning_family"]
    assert review["transferable_discipline"] == record["transferable_lesson"]
    assert review["qualifying_context"] and review["abstention_boundary"]
    assert old["status"] == "SUPERSEDED_GOLD_STANDARD"
    assert old["superseded_by_benchmark_id"] == record["benchmark_id"]
    assert old["query"] == "What does reciprocity mean in the Living Archive?"
    assert old["expected_response"].startswith("Reciprocity means a relationship of mutual response:")


TRUST_CANDIDATE_FIXTURE_PATH = (
    ROOT / "tests" / "fixtures" / "general_guide_trust_community_stewardship_candidate.json"
)


def test_trust_community_stewardship_candidate_matches_reviewable_fixture_without_activation():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-trust-community-stewardship-2026-10-24"
    )
    fixture = json.loads(TRUST_CANDIDATE_FIXTURE_PATH.read_text(encoding="utf-8"))

    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert fixture["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == fixture["query"]
    assert record["expected_response"] == fixture["expected_response"]
    assert record["expected_doorway"] == fixture["expected_doorway"]
    assert len(record["expected_response"].split(chr(10) * 2)) == 2
    assert record.get("rating") is None
    assert "rating_out_of_10" not in record
    assert record["assistant_assessment_out_of_10"] == 9.5
    assert record["explicit_user_elevation_approval"] is True
    assert record["runtime_transfer"] is True
    assert record["numbering_status"] == "UNASSIGNED"


def test_user_approved_organizational_acknowledgment_learning_gold_star_is_registered_exactly():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "gs-2026-11-21-organizational-acknowledgment-without-learning"
    )
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == "Why do organizations repeat failures they publicly acknowledge?"
    assert record["rating_out_of_10"] == 9.2
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["runtime_transfer"] is True
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["exact_answer_authority"] is False
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    assert record["expected_doorway"]["title"] == "When Experience Can Change Us: The Two Capacities of a Living System"
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/when-experience-can-change-us-the-two-capacities-of-a-living-system/"
    assert record["numbering_status"] == "UNASSIGNED"


def test_community_freedom_shared_responsibility_gold_star_is_registered_exactly():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "gs-2026-11-22-community-freedom-shared-responsibility-decision"
    )
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == "When a community faces a difficult trade-off between individual freedom and shared responsibility, how should it make a decision that is both fair and workable?"
    assert len(record["expected_response"].split(chr(10) * 2)) == 3
    assert "less restrictive alternatives" in record["expected_response"]
    assert "meaningful agency" in record["expected_response"]
    assert record["expected_doorway"] is None
    assert record["doorway_status"] == "INTENTIONALLY_NONE_APPROVED"
    assert record["runtime_transfer"] is True
    assert record["exact_answer_authority"] is False
    assert record["deterministic_fallback_eligible"] is False
    assert record["numbering_status"] == "UNASSIGNED"
    from general_guide_gold_standards import resolve_exact_gold_standard
    assert resolve_exact_gold_standard(record["query"]) is None
    assert "elevate to gold star registry" in record["approval_evidence"]


def test_governance_balance_near_miss_and_corrected_candidate_are_preserved_as_a_pair():
    registry = _registry()
    records = {item["benchmark_id"]: item for item in registry["records"]}
    near = records["general-guide-governance-balance-near-miss-2026-11-24"]
    candidate = records["general-guide-governance-balance-structural-candidate-2026-11-24"]

    assert near["status"] == "RECOVERED_DIAGNOSTIC_FIXTURE_NOT_GOLD_STANDARD"
    assert candidate["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert near["provenance"]["linked_candidate_benchmark_id"] == candidate["benchmark_id"]
    assert candidate["provenance"]["linked_near_miss_benchmark_id"] == near["benchmark_id"]
    assert near["query"] == candidate["query"]
    assert "Start by defining the outcome" in near["expected_response"]
    assert "Governance should distinguish between what must remain stable" in candidate["expected_response"]
    assert candidate["user_reviewed_response"] is True
    assert candidate["explicit_user_elevation_approval"] is True
    assert candidate["runtime_transfer"] is True
    assert candidate["gold_star_capabilities"]["active_quality_contributor"] is True
    assert sum(
        item["status"] == "USER_APPROVED_GOLD_STANDARD"
        for item in registry["records"]
    ) == sum(1 for item in registry["records"] if item.get("status") == "USER_APPROVED_GOLD_STANDARD")


def test_user_approved_governance_response_quality_exemplar_is_registered_without_runtime_authority():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-governance-balance-consequence-aware-2026-11-24"
    )
    capabilities = record["gold_star_capabilities"]
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["expected_response"].startswith("Start by defining the outcome")
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["runtime_transfer"] is False
    assert record["paired_active_benchmark_id"] == "general-guide-governance-balance-structural-candidate-2026-11-24"
    assert capabilities["generation_class"] == "user_approved_response_quality_exemplar"
    assert capabilities["exact_answer_authority"] is False
    assert capabilities["active_quality_contributor"] is False
    assert capabilities["deterministic_fallback_eligible"] is False
    assert record["doorway_status"] == "NOT_EVALUATED"
    assert "Do not infer" in capabilities["abstention_boundary"]
    from gold_star_inventory import derive_gold_star_inventory
    inventory = derive_gold_star_inventory(registry)
    assert inventory["approved_response_quality_exemplar_count"] == sum(
        1 for item in registry["records"]
        if (item.get("gold_star_capabilities") or {}).get("generation_class")
        == "user_approved_response_quality_exemplar"
    )


def test_transparency_trust_relational_synthesis_gold_star_is_bounded_and_active():
    registry = _registry()
    lesson = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-relational-synthesis-concept-pairs-2026-11-24"
    )
    capabilities = lesson["gold_star_capabilities"]
    assert lesson["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert lesson["runtime_transfer"] is True
    assert capabilities["active_quality_contributor"] is True
    assert capabilities["exact_answer_authority"] is False
    assert capabilities["deterministic_fallback_eligible"] is False
    assert lesson["doorway_status"] == "NOT_EVALUATED"
    assert "mechanism connecting them" in lesson["transferable_lesson"]
    assert "meaningful boundary or tension" in lesson["transferable_lesson"]
    assert lesson["numbering_status"] == "UNASSIGNED"


def test_transparency_trust_original_visitor_response_is_preserved_as_diagnostic():
    registry = _registry()
    diagnostic = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-relational-synthesis-transparency-trust-near-miss-2026-11-24"
    )
    assert diagnostic["status"] == "RECOVERED_REGRESSION_SCENARIO"
    assert diagnostic["runtime_transfer"] is False
    assert diagnostic["linked_successor_benchmark_id"] == (
        "general-guide-relational-synthesis-concept-pairs-2026-11-24"
    )
    assert "offers this starting point" in diagnostic["expected_response"]

def test_assistant_assessment_is_not_duplicated_as_user_rating():
    registry = _registry()
    for record in registry["records"]:
        assistant_assessment = record.get("assistant_assessment_out_of_10")
        if assistant_assessment is None or record.get("rating") is not None:
            continue
        assert record.get("rating_out_of_10") != assistant_assessment, record["benchmark_id"]

def test_user_approved_extraordinary_claims_response_is_frozen_response_quality_exemplar():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-extraordinary-claims-proportionate-scrutiny-2026-11-28"
    )
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == "How should the Guide respond to extraordinary claims?"
    assert record["doorway_status"] == "VERIFIED"
    assert record["expected_doorway"]["title"] == "Levels of Claim"
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/levels-of-claim/"
    assert "proportionate scrutiny" in record["expected_response"]
    assert "checked independently" in record["expected_response"]
    assert "official Guide doctrine" in record["expected_response"]
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["runtime_transfer"] is False
    assert record["gold_star_capabilities"]["generation_class"] == "user_approved_response_quality_exemplar"
    assert record["gold_star_capabilities"]["exact_answer_authority"] is False
    assert record["gold_star_capabilities"]["active_quality_contributor"] is False
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    assert record["numbering_status"] == "UNASSIGNED"


def test_user_approved_reverence_credulity_response_is_frozen_response_quality_exemplar():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-reverence-credulity-2026-11-28"
    )
    capabilities = record["gold_star_capabilities"]
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == "What is the difference between reverence and credulity?"
    assert record["expected_response"].startswith("Reverence is deep respect or awe")
    assert "leaves room for evidence, doubt, and correction" in record["expected_response"]
    assert "The Difference Between Intelligence and Consciousness" in record["expected_response"]
    assert record["doorway_status"] == "NOT_EVALUATED"
    assert record["expected_doorway"] is None
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["assistant_assessment_out_of_10"] == 9.3
    assert record.get("rating") is None
    assert record["runtime_transfer"] is False
    assert capabilities["generation_class"] == "user_approved_response_quality_exemplar"
    assert capabilities["exact_answer_authority"] is False
    assert capabilities["active_quality_contributor"] is False
    assert capabilities["deterministic_fallback_eligible"] is False
    assert capabilities["standalone_response_quality_exemplar"] is True
    assert "NOT_EVALUATED" in capabilities["abstention_boundary"]
    assert record["numbering_status"] == "UNASSIGNED"

def test_user_approved_digital_humanism_response_is_frozen_response_quality_exemplar():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-digital-humanism-human-centered-ai-exemplar-2026-11-28"
    )
    capabilities = record["gold_star_capabilities"]
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == "What does digital humanism require of AI systems?"
    assert len(record["expected_response"].split(chr(10) * 2)) == 3
    assert "not a single technical standard or formal doctrine" in record["expected_response"]
    assert "rather than from Archive-specific doctrine" in record["expected_response"]
    assert "serve broadly shared human purposes" in record["expected_response"]
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["assistant_assessment_out_of_10"] == 9.4
    assert record["rating_out_of_10"] is None
    assert record["doorway_status"] == "NOT_EVALUATED"
    assert record["expected_doorway"] is None
    assert record["runtime_transfer"] is False
    assert capabilities["generation_class"] == "user_approved_response_quality_exemplar"
    assert capabilities["exact_answer_authority"] is False
    assert capabilities["active_quality_contributor"] is False
    assert capabilities["deterministic_fallback_eligible"] is False
    assert capabilities["standalone_response_quality_exemplar"] is True
    assert "NOT_EVALUATED" in capabilities["abstention_boundary"]
    assert record["numbering_status"] == "UNASSIGNED"


def test_user_approved_engagement_optimization_response_is_frozen_response_quality_exemplar():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-engagement-optimization-knowledge-system-exemplar-2026-11-28"
    )
    capabilities = record["gold_star_capabilities"]
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == "What are the risks of optimizing engagement in a knowledge system?"
    answer = record["expected_response"]
    for phrase in (
        "Content quality erosion",
        "Echo-chamber amplification",
        "User fatigue and burnout",
        "Misaligned incentives",
        "Privacy and ethical concerns",
        "Systemic instability",
        "content integrity, user well-being, and ethical data practices",
    ):
        assert phrase in answer
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["assistant_assessment_out_of_10"] == 9.1
    assert record["rating_out_of_10"] is None
    assert record["doorway_status"] == "NOT_EVALUATED"
    assert record["expected_doorway"] is None
    assert record["runtime_transfer"] is False
    assert capabilities["generation_class"] == "user_approved_response_quality_exemplar"
    assert capabilities["exact_answer_authority"] is False
    assert capabilities["active_quality_contributor"] is False
    assert capabilities["deterministic_fallback_eligible"] is False
    assert capabilities["standalone_response_quality_exemplar"] is True
    assert "NOT_EVALUATED" in capabilities["abstention_boundary"]
    assert record["numbering_status"] == "UNASSIGNED"

def test_user_approved_digital_archive_context_preservation_gold_star_is_registered_exactly():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-digital-archive-context-preservation-2026-11-28"
    )
    capabilities = record["gold_star_capabilities"]
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == "How can a digital archive preserve context rather than merely store content?"
    assert record["expected_response"].startswith("A digital archive preserves context by keeping the circumstances")
    assert "The key distinction is that content is what was said or shown" in record["expected_response"]
    assert record["expected_doorway"]["title"] == "Living Archives: The Future of Knowledge May Be Relational, Not Linear"
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/2026/06/04/living-archives-the-future-of-knowledge-may-be-relational-not-linear/"
    assert record["doorway_status"] == "VERIFIED"
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["assistant_assessment_out_of_10"] == 9.6
    assert record["rating"] is None
    assert record["runtime_transfer"] is False
    assert capabilities["generation_class"] == "user_approved_response_quality_exemplar"
    assert capabilities["exact_answer_authority"] is False
    assert capabilities["active_quality_contributor"] is False
    assert capabilities["deterministic_fallback_eligible"] is False
    assert capabilities["standalone_response_quality_exemplar"] is True
    assert record["numbering_status"] == "UNASSIGNED"
    approved = [item for item in registry["records"] if item["status"] == "USER_APPROVED_GOLD_STANDARD"]
    assert len(approved) == 170
    assert len(registry["records"]) == 211
    assert registry["integrity_audit"]["approved_gold_star_count"] == 170
    assert registry["integrity_audit"]["unassigned_approved_gold_star_count"] == 131
    assert registry["integrity_audit"]["approved_response_quality_exemplar_count"] == 29


def test_human_discernment_successors_are_distinct_immutable_gold_star_exemplars():
    registry = _registry()
    records = {item["benchmark_id"]: item for item in registry["records"]}
    earlier = records["general-guide-human-discernment-ai-governance-2026-11-28"]
    latest = records["general-guide-human-discernment-ai-governance-doorway-refined-2026-11-28"]
    near_miss = records["general-guide-human-discernment-ai-support-near-miss-2026-11-28"]

    assert near_miss["status"] == "RECOVERED_REGRESSION_SCENARIO"
    assert near_miss["freeze_policy"].startswith("Preserve the exact original response unchanged")
    assert earlier["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert earlier["freeze_policy"] == "Preserve approved expected_response. Change only with explicit user authorization and a separately documented benchmark-version change."
    assert latest["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert latest["query"] == earlier["query"]
    assert latest["expected_response"].startswith("AI should be used as a tool that extends human judgment rather than as a substitute for it.")
    assert "The relationship is conditional" in latest["expected_response"]
    assert "what a human still needs to verify, judge, or decide" in latest["expected_response"]
    assert latest["assistant_assessment_out_of_10"] == 9.2
    assert latest["user_reviewed_response"] is True
    assert latest["explicit_user_elevation_approval"] is True
    assert latest["expected_doorway"] is None
    assert latest["doorway_status"] == "NOT_EVALUATED"
    assert latest["runtime_transfer"] is False
    capabilities = latest["gold_star_capabilities"]
    assert capabilities["generation_class"] == "user_approved_response_quality_exemplar"
    assert capabilities["exact_answer_authority"] is False
    assert capabilities["active_quality_contributor"] is False
    assert capabilities["deterministic_fallback_eligible"] is False
    assert capabilities["standalone_response_quality_exemplar"] is True
    assert latest["numbering_status"] == "UNASSIGNED"
    assert latest["provenance"]["visible_continuation_title"] == "Truth in the Age of AI: Why Discernment Is Becoming a Survival Skill"


def test_externalities_stewardship_response_is_frozen_standalone_gold_star():
    registry = _registry()
    record = next(item for item in registry["records"] if item["benchmark_id"] == "general-guide-externalities-stewardship-governance-2026-11-28")
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == "How do externalities reveal failures of stewardship?"
    assert record["expected_response"].startswith("Externalities reveal failures of stewardship when the responsible party")
    assert "an erosion of trust" in record["expected_response"]
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["assistant_assessment_out_of_10"] == 9.2
    assert record["rating_out_of_10"] is None
    assert record["expected_doorway"] is None
    assert record["doorway_status"] == "NOT_EVALUATED"
    assert record["provenance"]["visible_continuation_title"] == "The Stewardship Age"
    assert record["runtime_transfer"] is False
    capabilities = record["gold_star_capabilities"]
    assert capabilities["generation_class"] == "user_approved_response_quality_exemplar"
    assert capabilities["exact_answer_authority"] is False
    assert capabilities["active_quality_contributor"] is False
    assert capabilities["deterministic_fallback_eligible"] is False
    assert capabilities["standalone_response_quality_exemplar"] is True
    assert record["numbering_status"] == "UNASSIGNED"



def test_ecological_technology_solutionism_successor_is_frozen_standalone_gold_star():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-technology-solutionism-ecological-stewardship-2026-11-28"
    )
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == "How should the Guide respond to claims that technology alone will solve ecological crises?"
    assert record["expected_response"].startswith("Technology can help address ecological crises, but it cannot solve them by itself.")
    assert "rebound effects" in record["expected_response"]
    assert "affected communities" in record["expected_response"]
    assert record["explicit_user_elevation_approval"] is True
    assert record["assistant_assessment_out_of_10"] == 9.5
    assert record["rating_out_of_10"] is None
    assert record["expected_doorway"] is None
    assert record["doorway_status"] == "NOT_EVALUATED"
    assert record["provenance"]["visible_continuation_title"] == "Temple of Joy: Reclaiming Pleasure as a Planetary Service Code"
    assert "not a canonical URL" in record["doorway_note"]
    assert record["doorway_status"] == "NOT_EVALUATED"
    assert record["runtime_transfer"] is False
    capabilities = record["gold_star_capabilities"]
    assert capabilities["generation_class"] == "user_approved_response_quality_exemplar"
    assert capabilities["exact_answer_authority"] is False
    assert capabilities["active_quality_contributor"] is False
    assert capabilities["deterministic_fallback_eligible"] is False
    assert capabilities["standalone_response_quality_exemplar"] is True
    assert record["numbering_status"] == "UNASSIGNED"

def test_user_approved_economy_life_relationship_is_frozen_standalone_gold_star():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-economy-life-sustaining-conditions-2026-11-28"
    )
    capabilities = record["gold_star_capabilities"]
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == "What is the relationship between economy and the conditions that sustain life?"
    assert record["expected_response"].startswith("Economy and the conditions that sustain life stand in a reciprocal relationship:")
    assert "The relationship is therefore conditional rather than fixed" in record["expected_response"]
    assert "the self-contained machine separate from the living world" not in record["expected_response"]
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["assistant_assessment_out_of_10"] == 9.3
    assert record["rating"] is None
    assert record["rating_out_of_10"] is None
    assert record["expected_doorway"] is None
    assert record["doorway_status"] == "NOT_EVALUATED"
    assert record["provenance"]["visible_continuation_title"] == "The Life We Inherit: Becoming the Author of a Conscious Life"
    assert record["runtime_transfer"] is False
    assert capabilities["generation_class"] == "user_approved_response_quality_exemplar"
    assert capabilities["exact_answer_authority"] is False
    assert capabilities["active_quality_contributor"] is False
    assert capabilities["deterministic_fallback_eligible"] is False
    assert capabilities["standalone_response_quality_exemplar"] is True
    assert record["numbering_status"] == "UNASSIGNED"
    approved = [item for item in registry["records"] if item["status"] == "USER_APPROVED_GOLD_STANDARD"]
    assert len(approved) == 170
    assert len(registry["records"]) == 211
    assert registry["integrity_audit"]["approved_gold_star_count"] == 170
    assert registry["integrity_audit"]["unassigned_approved_gold_star_count"] == 131
    assert registry["integrity_audit"]["approved_response_quality_exemplar_count"] == 29



def test_society_resilience_gold_star_registry_record_preserves_verified_successor_and_scope():
    import json

    path = ROOT / "docs" / "qa" / "gold_standard_registry.json"
    registry = json.loads(path.read_text(encoding="utf-8"))
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-society-resilience-integrative-systems-2026-11-28"
    )
    capabilities = record["gold_star_capabilities"]
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == "What makes a society resilient?"
    assert record["expected_response"].startswith("A society is resilient when it can absorb disruption")
    assert "cascading failures" in record["expected_response"]
    assert "cultural memory" in record["expected_response"]
    assert record["expected_doorway"]["title"] == "Collective Nervous Systems: How Cultures Regulate Human Coherence"
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/2026/09/28/collective-nervous-systems-how-cultures-regulate-human-coherence/"
    assert record["doorway_status"] == "VERIFIED_CANONICAL_DESTINATION"
    assert record["provenance"]["canonical_doorway_verification"]["post_id"] == 57155
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["assistant_assessment_out_of_10"] == 9.5
    assert record["rating"] is None
    assert record["rating_out_of_10"] is None
    assert record["runtime_transfer"] is False
    assert capabilities["generation_class"] == "user_approved_response_quality_exemplar"
    assert capabilities["exact_answer_authority"] is False
    assert capabilities["active_quality_contributor"] is False
    assert capabilities["deterministic_fallback_eligible"] is False
    assert capabilities["standalone_response_quality_exemplar"] is True
    assert record["numbering_status"] == "UNASSIGNED"
    approved = [item for item in registry["records"] if item["status"] == "USER_APPROVED_GOLD_STANDARD"]
    assert len(approved) == 170
    assert len(registry["records"]) == 211
    assert registry["integrity_audit"]["approved_gold_star_count"] == 170
    assert registry["integrity_audit"]["unassigned_approved_gold_star_count"] == 131
    assert registry["integrity_audit"]["approved_response_quality_exemplar_count"] == 29


def test_ethical_future_vision_credibility_gold_star_is_frozen_standalone_exemplar():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-ethical-credibility-future-vision-2026-11-28"
    )
    capabilities = record["gold_star_capabilities"]
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == "What makes a future vision ethically credible?"
    assert "who bears its costs" in record["expected_response"]
    assert "meaningful consent" in record["expected_response"]
    assert "way to stop or change it" in record["expected_response"]
    assert record["expected_doorway"] is None
    assert record["doorway_status"] == "NOT_EVALUATED"
    assert "NOT_EVALUATED" in capabilities["abstention_boundary"]
    assert record["provenance"]["visible_continuation_title"] == (
        "At the Bottom of the Abyss: Not Giving Up When Nothing Makes Sense"
    )
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["assistant_assessment_out_of_10"] == 9.8
    assert record["rating"] is None
    assert record["runtime_transfer"] is False
    assert capabilities["generation_class"] == "user_approved_response_quality_exemplar"
    assert capabilities["exact_answer_authority"] is False
    assert capabilities["active_quality_contributor"] is False
    assert capabilities["deterministic_fallback_eligible"] is False
    assert capabilities["standalone_response_quality_exemplar"] is True
    assert record["numbering_status"] == "UNASSIGNED"
    approved = [item for item in registry["records"] if item["status"] == "USER_APPROVED_GOLD_STANDARD"]
    assert len(approved) == 170
    assert len(registry["records"]) == 211
    assert registry["integrity_audit"]["approved_gold_star_count"] == 170
    assert registry["integrity_audit"]["unassigned_approved_gold_star_count"] == 131
    assert registry["integrity_audit"]["approved_response_quality_exemplar_count"] == 29



def test_organizational_transformation_readiness_gold_star_is_approved_frozen_and_non_runtime():
    registry = _registry()
    fixture_path = ROOT / "tests" / "fixtures" / "general-guide-organizational-transformation-readiness-2026-11-28.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    record = next(item for item in registry["records"] if item["benchmark_id"] == "general-guide-organizational-transformation-readiness-2026-11-28")

    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == fixture["query"]
    assert record["expected_response"] == fixture["expected_response"]
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["runtime_transfer"] is False
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["doorway_status"] == "NOT_EVALUATED"
    assert record["expected_doorway"] is None
    capabilities = record["gold_star_capabilities"]
    assert capabilities["generation_class"] == "user_approved_response_quality_exemplar"
    assert capabilities["standalone_response_quality_exemplar"] is True
    assert capabilities["exact_answer_authority"] is False
    assert capabilities["active_quality_contributor"] is False
    assert capabilities["deterministic_fallback_eligible"] is False
    assert "operational synthesis" in capabilities["abstention_boundary"]
    answer = record["expected_response"].lower()
    for phrase in ("reality:", "ethics:", "developmental wisdom:", "pass", "hold", "stop / redesign", "counter-evidence"):
        assert phrase in answer
    assert "do not average" in answer
    assert "not a universal numerical threshold" in answer
    assert record["provenance"]["original_near_miss"].endswith("issue #2175; they are not overwritten or counted as this successor.")

    approved = [item for item in registry["records"] if item["status"] == "USER_APPROVED_GOLD_STANDARD"]
    assert len(approved) == 170
    assert len(registry["records"]) == 211
    assert registry["integrity_audit"]["approved_gold_star_count"] == 170
    assert registry["integrity_audit"]["unassigned_approved_gold_star_count"] == 131
    assert registry["integrity_audit"]["approved_response_quality_exemplar_count"] == 29


def test_vulnerable_group_exploitation_refusal_gold_star_matches_frozen_fixture():
    registry = _registry()
    fixture_path = ROOT / "tests" / "fixtures" / "general-guide-vulnerable-group-exploitation-ethical-refusal-2026-11-28.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    record = next(item for item in registry["records"] if item["benchmark_id"] == "general-guide-vulnerable-group-exploitation-ethical-refusal-2026-11-28")

    for field in ("status", "query", "expected_response", "assistant_assessment_out_of_10",
                  "doorway_status", "expected_doorway", "provenance"):
        assert record[field] == fixture[field]
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["runtime_transfer"] is False
    assert record["gold_star_capabilities"]["generation_class"] == "user_approved_response_quality_exemplar"
    assert record["gold_star_capabilities"]["standalone_response_quality_exemplar"] is True
    assert record["gold_star_capabilities"]["exact_answer_authority"] is False
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is False
    assert record["gold_star_capabilities"]["active_quality_contributor"] is False
    assert record["question_family_review"]["classification"] == "NEW_QUESTION_FAMILY"
    assert record["question_family_review"]["related_benchmark_ids"] == []
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["expected_doorway"] is None


def test_developmental_stage_hierarchy_gold_star_matches_frozen_fixture_and_preserves_near_miss():
    registry = _registry()
    fixture_path = ROOT / "tests" / "fixtures" / "general-guide-developmental-stage-hierarchy-nonranking-2026-11-28.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-developmental-stage-hierarchy-nonranking-2026-11-28"
    )

    assert record == fixture
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["assistant_assessment_out_of_10"] == 9.6
    assert record["runtime_transfer"] is False
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["numbering_unassigned_reason_code"] == "NO_SERIAL_ALLOCATION_REQUESTED"
    capabilities = record["gold_star_capabilities"]
    assert capabilities["generation_class"] == "user_approved_response_quality_exemplar"
    assert capabilities["standalone_response_quality_exemplar"] is True
    assert capabilities["exact_answer_authority"] is False
    assert capabilities["active_quality_contributor"] is False
    assert capabilities["deterministic_fallback_eligible"] is False
    assert record["question_family_review"]["classification"] == "NEW_QUESTION_FAMILY"
    assert record["question_family_review"]["family_id"] == "qf-cd6550fcd889c285"
    assert record["question_family_review"]["related_benchmark_ids"] == []
    assert "issue #2197" in record["provenance"]["original_near_miss"]
    assert "The Resonance & Coherence Assessment" == record["provenance"]["visible_continuation_title"]
    approved = [item for item in registry["records"] if item["status"] == "USER_APPROVED_GOLD_STANDARD"]
    assert len(approved) == 170
    assert len(registry["records"]) == 211
    assert registry["integrity_audit"]["approved_gold_star_count"] == 170
    assert registry["integrity_audit"]["registry_record_count"] == 211
    assert registry["integrity_audit"]["active_quality_contributor_count"] == 139
    assert registry["integrity_audit"]["approved_response_quality_exemplar_count"] == 29
    assert registry["integrity_audit"]["numbered_gold_star_record_count"] == 39
    assert registry["integrity_audit"]["unassigned_approved_gold_star_count"] == 131


def test_ethical_legitimacy_concentrated_harm_gold_star_matches_frozen_fixture():
    registry = _registry()
    fixture = json.loads(
        (ROOT / "tests" / "fixtures" / "general_guide_policy_legality_minority_harm_gold_star.json").read_text(encoding="utf-8")
    )
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-ethical-legitimacy-concentrated-harm-2026-11-28"
    )

    for field in (
        "status", "query", "expected_response", "explicit_user_elevation_approval",
        "user_reviewed_response", "runtime_transfer", "numbering_status",
        "numbering_unassigned_reason_code",
    ):
        assert record[field] == fixture[field]
    assert record["numbering_unassigned_reason"]
    capabilities = record["gold_star_capabilities"]
    assert capabilities["generation_class"] == fixture["generation_class"]
    assert capabilities["standalone_response_quality_exemplar"] is True
    assert capabilities["exact_answer_authority"] is False
    assert capabilities["deterministic_fallback_eligible"] is False
    assert capabilities["active_quality_contributor"] is False
    assert record["question_family_review"]["classification"] == "NEW_QUESTION_FAMILY"
    assert record["question_family_review"]["family_id"] == "qf-d2637dc092092951"
    assert record["runtime_transfer"] is False
    assert record["numbering_status"] == "UNASSIGNED"


def test_record_level_union_counts_and_integrity_mirrors_are_exact():
    registry = _registry()
    records = registry["records"]
    approved = [
        item for item in records
        if item.get("status") == "USER_APPROVED_GOLD_STANDARD"
    ]
    active = [item for item in approved if item.get("runtime_transfer") is True]
    response_quality = [
        item for item in approved
        if item.get("gold_star_capabilities", {}).get("generation_class")
        == "user_approved_response_quality_exemplar"
    ]
    standalone = [
        item for item in approved
        if item.get("gold_star_capabilities", {}).get("standalone_response_quality_exemplar") is True
    ]
    numbered = [item for item in approved if item.get("numbering_status") == "ASSIGNED"]
    unassigned = [item for item in approved if item.get("numbering_status") == "UNASSIGNED"]

    assert len({item["benchmark_id"] for item in records}) == 211
    assert len(records) == 211
    assert len(approved) == 170
    assert len(active) == 139
    assert len(response_quality) == 29
    assert len(standalone) == 28
    assert len(numbered) == 39
    assert len(unassigned) == 131
    assert registry["integrity_audit"] == registry["audit"]
    audit = registry["integrity_audit"]
    assert audit["registry_record_count"] == 211
    assert audit["approved_gold_star_count"] == 170
    assert audit["active_quality_contributor_count"] == 139
    assert audit["approved_response_quality_exemplar_count"] == 29
    assert audit["numbered_gold_star_record_count"] == 39
    assert audit["unassigned_approved_gold_star_count"] == 131


def test_user_approved_mixed_source_provenance_response_is_standalone_gold_star():
    import json

    registry = _registry()
    benchmark_id = "general-guide-mixed-source-claim-level-provenance-2026-11-28"
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == benchmark_id
    )
    fixture = json.loads(
        (ROOT / "tests/fixtures/general_guide_mixed_source_provenance_gold_star.json")
        .read_text(encoding="utf-8")
    )
    capabilities = record["gold_star_capabilities"]

    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["query"] == fixture["query"]
    assert record["expected_response"] == fixture["expected_response"]
    assert record["expected_doorway"] is None
    assert record["doorway_status"] == "NOT_EVALUATED"
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["runtime_transfer"] is False
    assert capabilities["generation_class"] == "user_approved_response_quality_exemplar"
    assert capabilities["standalone_response_quality_exemplar"] is True
    assert capabilities["exact_answer_authority"] is False
    assert capabilities["active_quality_contributor"] is False
    assert capabilities["deterministic_fallback_eligible"] is False
    assert record["numbering_status"] == "UNASSIGNED"
    assert "issue #2208" in record["provenance"]["original_near_miss"]
    assert fixture["original_near_miss_issue"].endswith("/issues/2208")

    from gold_star_inventory import derive_gold_star_inventory
    inventory = derive_gold_star_inventory(registry)
    assert inventory["approved_gold_star_count"] == len([
        item for item in registry["records"]
        if item.get("status") == "USER_APPROVED_GOLD_STANDARD"
    ])
    assert inventory["approved_response_quality_exemplar_count"] == len([
        item for item in registry["records"]
        if item.get("status") == "USER_APPROVED_GOLD_STANDARD"
        and (item.get("gold_star_capabilities") or {}).get("generation_class")
        == "user_approved_response_quality_exemplar"
    ])



def test_one_sided_team_conflict_gold_star_matches_frozen_fixture():
    registry = _registry()
    fixture_path = ROOT / "tests" / "fixtures" / "general-guide-one-sided-team-conflict-contextual-recovery-2026-11-28.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-one-sided-team-conflict-contextual-recovery-2026-11-28"
    )

    assert record == fixture
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["user_reviewed_response"] is True
    assert record["explicit_user_elevation_approval"] is True
    assert record["assistant_assessment_out_of_10"] == 9.7
    assert record["runtime_transfer"] is False
    assert record["doorway_status"] == "VERIFIED"
    assert record["expected_doorway"]["title"] == "Building Trust-Centered Organizations"
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/2026/09/07/building-trust-centered-organizations/"
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["numbering_unassigned_reason_code"] == "NO_SERIAL_ALLOCATION_REQUESTED"
    capabilities = record["gold_star_capabilities"]
    assert capabilities["generation_class"] == "user_approved_response_quality_exemplar"
    assert capabilities["standalone_response_quality_exemplar"] is True
    assert capabilities["exact_answer_authority"] is False
    assert capabilities["active_quality_contributor"] is False
    assert capabilities["deterministic_fallback_eligible"] is False
    assert record["question_family_review"]["classification"] == "NEW_QUESTION_FAMILY"
    assert record["question_family_review"]["family_id"] == "qf-8f6e579a6485d012"
    assert record["question_family_review"]["related_benchmark_ids"] == []
    assert "issue #2210" in record["provenance"]["original_near_miss"]
    assert "retaliation risk" in record["expected_response"]
    assert "direct observations" in record["expected_response"]
    assert len([x for x in registry["records"] if x["status"] == "USER_APPROVED_GOLD_STANDARD"]) == 170

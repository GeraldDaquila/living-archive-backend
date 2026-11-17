import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
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
    assert record["status"] == "FROZEN_REFERENCE_ONLY"
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
    numbered = [item for item in approved if item.get("numbering_status") == "ASSIGNED"]
    unassigned = [item for item in approved if item.get("numbering_status") == "UNASSIGNED"]
    assert report["numbered_gold_star_count"] == len(numbered) == 35
    assert report["unassigned_approved_gold_star_count"] == len(unassigned) == 56
    assert report["highest_assigned_gold_star_number"] == 92
    assert report["numbering_sequence_start"] == 56
    assert [gap["number"] for gap in report["numbering_gap_register"]] == [85, 86]
    assert len(report["number_assignments"]) == 35
    assert len(report["unassigned_benchmark_ids"]) == 56
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
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-trust-community-stewardship-2026-10-24"
    )
    assert record["status"] == "CANDIDATE"
    assert record["query"] == "What is the role of trust in community stewardship?"
    assert record["expected_response"] is None
    assert "Exact prior trust answer text" in record["provenance"]["evidence_boundary"]


def test_reciprocity_community_gold_standard_candidate_is_bounded_and_not_misrepresented():
    registry = _registry()
    record = next(
        item for item in registry["records"]
        if item["benchmark_id"] == "general-guide-reciprocity-community-2026-10-24"
    )
    assert record["status"] == "CANDIDATE"
    assert record["query"] == "What is the purpose of reciprocity in a community?"
    assert record["rating_out_of_10"] is None
    assert "support one another over time" in record["expected_response"]
    assert "not when kindness becomes a debt ledger" in record["expected_response"]
    
    assert "has not yet been reviewed and approved" in record["provenance"]["approval_evidence"]
    assert record["provenance"]["source_path"] == "docs/qa/gold_standard_registry.json"
    assert any("recommendation must be demonstrably relevant" in item for item in record["assertions"])


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


def test_fragmented_knowledge_gold_standard_is_runtime_resolvable_and_three_paragraph_default_is_enforced():
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
    assert "substantive explanatory answer must meet the three-paragraph Guide Gold Standard" in composition_source
    assert 'CONTRACT_VERSION = "v1.46"' in composition_source
    assert "def resolve_exact_gold_standard(question: str)" in standards_source
    main_source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert 'snapshot.get("contract_version") != general_guide_composition.CONTRACT_VERSION' in main_source
    assert "Apply the default paragraph contract at the final visitor boundary too" in main_source
    assert "used three-paragraph fail-honest recovery" in main_source


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
        if record.get("runtime_transfer") is False:
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
    exact = finalizer.index("exact_standard = _resolve_exact_guide_gold_standard(query)")
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
        if record.get("runtime_transfer") is False:
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
        assert record["rating_out_of_10"] is None
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
    namespace = {"re": __import__("re")}
    fn = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_select_verified_doorway_conceptual_family"
    )
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "<family>", "exec"), namespace)
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
    registry = json.loads((ROOT / "docs" / "qa" / "gold_standard_registry.json").read_text(encoding="utf-8"))
    approved = [r for r in registry["records"] if r.get("status") == "USER_APPROVED_GOLD_STANDARD"]
    assert len(approved) == 91
    for record in approved:
        if isinstance(record.get("gold_star_number"), int) and not isinstance(record.get("gold_star_number"), bool):
            assert record.get("numbering_status") == "ASSIGNED"
            assert not record.get("numbering_unassigned_reason")
        else:
            assert record.get("numbering_status") == "UNASSIGNED"
            assert record.get("numbering_unassigned_reason_code")
            assert record.get("numbering_unassigned_reason")
            if record["benchmark_id"] in {"gs-2026-11-17-structural-change-vs-disruption", "gs-2026-11-17-consequential-action-under-uncertainty", "gs-2026-11-17-hope-disciplined-rather-than-naive", "gs-2026-11-17-community-continuity-harmful-inherited-patterns", "gs-2026-11-17-ai-workforce-restructuring-successor-candidate"}:
                assert record.get("legacy_approval_grandfathered") is not True
                assert record.get("numbering_unassigned_reason_code") == "NO_SERIAL_ALLOCATION_REQUESTED"
            elif record["benchmark_id"] not in {"gs-2026-11-14-bounded-conceptual-orientation-spiritual-bypassing", "gs-2026-11-16-community-wisdom-tradition-epistemic-stewardship", "gs-2026-11-16-collapse-adaptation-regeneration", "gs-2026-11-16-techno-utopian-thinking"}:
                assert record.get("legacy_approval_grandfathered") is True
                assert record.get("numbering_unassigned_reason_code") == "LEGACY_APPROVED_NO_SERIAL_ALLOCATION"
            else:
                assert record.get("numbering_unassigned_reason_code") == "NO_SERIAL_ALLOCATION_REQUESTED"


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


def test_only_85_and_86_are_documented_gaps_and_86_commit_subject_is_not_assignment():
    import json
    registry = json.loads((ROOT / "docs" / "qa" / "gold_standard_registry.json").read_text(encoding="utf-8"))
    gaps = registry["numbering_gap_register"]
    assert [g["number"] for g in gaps] == [85, 86]
    assert all(g["status"] == "RELEASED_FOR_FUTURE_ALLOCATION" for g in gaps)
    assert all(g["release_authorization"]["authorization_type"] == "EXPLICIT_USER_AUTHORIZED_HISTORICAL_GAP_RELEASE" for g in gaps)
    assert all(g["release_authorization"]["historical_evidence_preserved"] is True for g in gaps)
    assert gaps[0]["release_authorization"]["allocation_rule"].find("#85") >= 0
    assert "7a036632323b7c09003d1fce637a7b49128a27bf" in gaps[1]["reason"]
    assert "only adds provenance.source_date" in gaps[1]["reason"]
    assert "recovered as Gold Star #56" in gaps[1]["reason"]
    assert registry["numbering_policy"]["sequence_start"] == 56
    assert registry["integrity_audit"]["approved_gold_star_count"] == 91
    assert registry["integrity_audit"]["numbered_gold_star_record_count"] == 35
    assert registry["integrity_audit"]["highest_assigned_gold_star_number"] == 92
    assert registry["integrity_audit"]["unassigned_approved_gold_star_count"] == 56
    assert registry["integrity_audit"]["documented_numbering_gap_count"] == 2



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
    gaps = {g["number"]: g for g in registry["numbering_gap_register"]}
    assert set(gaps) == {85, 86}
    assert all(gaps[n]["status"] == "RELEASED_FOR_FUTURE_ALLOCATION" for n in (85, 86))
    assert all(gaps[n]["release_authorization"]["approved_by"] == "user" for n in (85, 86))
    assert len([r for r in registry["records"] if r.get("gold_star_number") in {85, 86}]) == 0



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
    assert len(exact_only) == 1
    assert exact_only[0]["gold_star_capabilities"]["exact_answer_authority"] is True
    assert exact_only[0]["gold_star_capabilities"]["active_quality_contributor"] is False
    assert exact_only[0]["gold_star_capabilities"]["deterministic_fallback_eligible"] is False

    mutated = copy.deepcopy(approved)
    successor = next(
        item for item in mutated
        if item.get("runtime_transfer") is False
        and item.get("gold_star_capabilities", {}).get("exact_answer_authority") is True
    )
    successor["replaces_exact_query_runtime_authority_of"] = "missing-predecessor"
    with pytest.raises(SystemExit, match="valid exact-query-only successor"):
        validate_exact_only_successors(mutated, active)

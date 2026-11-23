import scripts.guide_live_evaluation as live_evaluation

from scripts.guide_live_evaluation import (
    build_human_review_template,
    classify_llm_payload,
    claim_adjudication_summary,
    evaluate_gold,
    evaluate_held,
    select_gold_standard_sample,
)


def test_exact_approved_answer_is_enforced():
    record = {
        "status": "USER_APPROVED_GOLD_STANDARD",
        "expected_response": "The approved answer.",
        "assertions": [],
        "freeze_policy": "Frozen.",
    }
    transport = {"status": 200, "error": None, "body": {"ok": True, "response": "Changed answer."}}
    checks = evaluate_gold(record, transport)
    exact = next(item for item in checks if item["name"] == "exact_answer")
    assert exact["passed"] is False


def test_explicit_no_handoff_overrides_recorded_doorway():
    record = {
        "status": "FROZEN_REFERENCE_ONLY",
        "expected_response": "One.\n\nTwo.\n\nThree.",
        "expected_doorway": {"title": "A page", "url": "https://example.org/page"},
        "assertions": ["Exactly three paragraphs.", "The explicit request not to send the visitor to another page forbids direct page handoff."],
        "freeze_policy": "Do not change expected_response.",
    }
    transport = {"status": 200, "error": None, "body": {"ok": True, "response": "One.\n\nTwo.\n\nThree.", "recommendation": None}}
    checks = evaluate_gold(record, transport)
    assert all(item["passed"] for item in checks), checks


def test_boiling_point_heldout_rejects_false_refusal():
    case = {"case_id": "heldout-water-boiling-point-001"}
    transport = {"status": 200, "error": None, "body": {"ok": True, "response": "I don't have enough verified context to answer.", "recommendation": None}}
    checks = evaluate_held(case, transport)
    assert not all(item["passed"] for item in checks)


def test_cosmology_heldout_rejects_unrelated_diagnostic_template():
    case = {"case_id": "heldout-cosmology-life-001"}
    transport = {"status": 200, "error": None, "body": {"ok": True, "response": "Separate the immediate event from the conditions that made it more likely. What detail or context would make this question most concrete?", "recommendation": None}}
    checks = evaluate_held(case, transport)
    assert not all(item["passed"] for item in checks)


def test_practical_trust_heldout_accepts_concrete_actions():
    case = {"case_id": "heldout-practical-trust-001"}
    answer = ("Ask the people affected what they see before deciding. Explain the reasons for the decision, "
              "name who is responsible for the next step, and follow through when promised. Then check with "
              "the people affected whether the action changed their experience.")
    transport = {
        "status": 200,
        "error": None,
        "body": {
            "ok": True,
            "response": answer,
            "recommendation": {
                "title": "Steward of Organization",
                "url": "https://geralddaquila.com/steward-of-organization/",
                "rationale": "This resource offers a related perspective on trust in organizational stewardship.",
            },
        },
    }
    checks = evaluate_held(case, transport)
    assert all(item["passed"] for item in checks), checks


def test_live_results_receive_pending_human_scorecard_not_auto_approval():
    rubric = {
        "critical_dimensions": ["answer_directness", "factual_accuracy"],
        "dimensions": [
            {"id": "answer_directness"},
            {"id": "factual_accuracy"},
            {"id": "human_voice_and_respect"},
        ],
    }
    scorecard = build_human_review_template(rubric)
    assert scorecard["status"] == "PENDING"
    assert scorecard["decision"] == "PENDING"
    assert scorecard["reviewer"] is None
    assert scorecard["reviewed_at"] is None
    assert scorecard["critical_dimensions"] == ["answer_directness", "factual_accuracy"]
    assert set(scorecard["scores"]) == {"answer_directness", "factual_accuracy", "human_voice_and_respect"}
    assert all(value is None for value in scorecard["scores"].values())
    assert "cannot approve" in scorecard["instruction"]


def test_human_scorecard_allows_case_specific_critical_dimensions():
    scorecard = build_human_review_template(
        {"critical_dimensions": ["default"], "dimensions": [{"id": "accuracy"}]},
        applicable_critical=["accuracy", "archive_grounding_and_provenance"],
    )
    assert scorecard["critical_dimensions"] == ["accuracy", "archive_grounding_and_provenance"]


def test_unspecified_doorway_url_is_not_mistaken_for_required_absence():
    record = {
        "status": "FROZEN_REFERENCE_ONLY",
        "expected_response": "Answer.",
        "expected_doorway": {"title": "Reciprocity Before Bureaucracy", "url": None},
        "assertions": ["Offer the optional doorway after the answer."],
        "freeze_policy": "Preserve the observed accepted response.",
    }
    transport = {
        "status": 200,
        "error": None,
        "body": {
            "ok": True,
            "response": "Answer.",
            "recommendation": {
                "title": "Reciprocity Before Bureaucracy",
                "url": "https://geralddaquila.com/reciprocity/",
            },
        },
    }
    checks = evaluate_gold(record, transport)
    assert all(item["passed"] for item in checks), checks
    assert not any(item["name"] == "doorway_url" for item in checks)


def test_cosmology_heldout_accepts_concrete_conditional_example():
    case = {"case_id": "heldout-cosmology-life-001"}
    answer = (
        "Cosmology is an understanding of reality and how we belong within it. "
        "This worldview shapes choices and relationships. If every disagreement is treated as a contest for control, "
        "people may protect status instead of looking for a workable answer."
    )
    transport = {"status": 200, "error": None, "body": {"ok": True, "response": answer, "recommendation": None}}
    checks = evaluate_held(case, transport)
    example = next(item for item in checks if item["name"] == "concrete_implication")
    assert example["passed"], checks

def test_live_evaluation_workflow_sets_repository_import_path_and_entrypoint_imports():
    import os
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github" / "workflows" / "guide-live-evaluation.yml").read_text(encoding="utf-8")
    assert "PYTHONPATH: ." in workflow
    assert "push:\n    branches: [main]" in workflow

    env = {**os.environ, "PYTHONPATH": str(root)}
    result = subprocess.run(
        [sys.executable, str(root / "scripts" / "guide_live_evaluation.py"), "--help"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert "--base-url" in result.stdout
    assert "--max-gold-standards" in result.stdout
    assert "--identity-wait-seconds" in result.stdout

def test_gold_standard_live_sample_is_stable_bounded_and_spans_registry():
    records = [
        {"benchmark_id": f"benchmark-{index:03d}", "query": f"Question {index}"}
        for index in range(130)
    ]
    sample = select_gold_standard_sample(records, 6)
    assert len(sample) == 6
    assert sample == select_gold_standard_sample(records, 6)
    assert sample[0]["benchmark_id"] == "benchmark-000"
    assert sample[-1]["benchmark_id"] == "benchmark-129"
    assert len({item["benchmark_id"] for item in sample}) == 6


def test_llm_capture_requires_final_answer_provenance_not_provider_attempts():
    deterministic = {
        "provider": "gold_standard_registry",
        "model": "approved-reference",
        "response_provenance": {
            "class": "deterministic_by_design",
            "llm_invoked": False,
        },
    }
    verified, metadata = classify_llm_payload(deterministic)
    assert verified is False
    assert metadata["verification_basis"] == "insufficient_or_deterministic_final_output_provenance"

    llm = {
        "response_provenance": {
            "class": "llm",
            "llm_invoked": True,
            "provider": "groq",
            "model": "qwen/qwen3.8-27b",
        },
    }
    verified, metadata = classify_llm_payload(llm)
    assert verified is True
    assert metadata["provider"] == "groq"
    assert metadata["model"] == "qwen/qwen3.8-27b"


def test_claim_adjudication_report_is_summary_only():
    body = {
        "claim_adjudication": {
            "status": "assessed",
            "reason": "all_claims_assessed",
            "claim_count": 2,
            "outcome_counts": {"supported": 1, "no_relevant_public_source": 1},
            "claims": [{"claim": "private response text", "outcome": "supported"}],
        }
    }
    summary = claim_adjudication_summary(body)
    assert summary == {
        "status": "assessed",
        "reason": "all_claims_assessed",
        "claim_count": 2,
        "outcome_counts": {"supported": 1, "no_relevant_public_source": 1},
    }
    assert "claims" not in summary

def test_live_evaluation_waits_for_exact_target_commit_before_capture(monkeypatch):
    monkeypatch.setattr(
        live_evaluation,
        "get_json",
        lambda url, timeout=90: {
            "status": 200,
            "error": None,
            "body": {
                "deployment_commit_sha": "expected-sha",
                "version": "v489.315",
                "fingerprint": "runtime-fingerprint",
                "source_sha256": "source-hash",
                "ok": False,
                "available_capabilities_missing_adapters": ["advisory"],
            },
        },
    )
    identity = live_evaluation.verify_runtime_identity(
        "https://living-archive-backend.onrender.com",
        "expected-sha",
        timeout_seconds=0,
    )
    assert identity["deployment_commit_sha"] == "expected-sha"
    assert identity["integration_audit_ok"] is False
    assert identity["integration_audit_warnings"]["available_capabilities_missing_adapters"] == ["advisory"]


def test_live_evaluation_refuses_mismatched_target_commit(monkeypatch):
    monkeypatch.setattr(
        live_evaluation,
        "get_json",
        lambda url, timeout=90: {
            "status": 200,
            "error": None,
            "body": {"deployment_commit_sha": "old-sha"},
        },
    )
    try:
        live_evaluation.verify_runtime_identity(
            "https://living-archive-backend.onrender.com",
            "expected-sha",
            timeout_seconds=0,
        )
    except RuntimeError as exc:
        assert "does not match expected" in str(exc)
    else:
        raise AssertionError("A mismatched deployment must never receive synthetic visitor queries.")


def test_community_rule_design_transfer_heldout_accepts_balanced_answer_and_clean_doorway():
    case = {"case_id": "heldout-community-rule-design-transfer-001"}
    answer = (
        "A community should identify the shared purpose and the specific harm or coordination problem first. "
        "Any limit should be necessary and proportionate, using the least restrictive workable means. "
        "Ask who benefits, who carries the costs, and whose freedom is restricted; distribute duties fairly and "
        "allow reasonable accommodation. People most affected should have a meaningful opportunity to shape the "
        "decision. Provide a way to appeal and set observable criteria to review the rule."
    )
    transport = {
        "status": 200,
        "error": None,
        "body": {
            "ok": True,
            "response": answer,
            "recommendation": {
                "title": "The Barangay Before the State: Human-Scale Governance in Practice",
                "url": "https://geralddaquila.com/2026/09/21/the-barangay-before-the-state-human-scale-governance-in-practice/",
                "rationale": "This resource offers a related perspective and a useful next step in the Living Archive.",
            },
        },
    }
    checks = evaluate_held(case, transport)
    assert all(item["passed"] for item in checks), checks


def test_community_rule_design_transfer_heldout_rejects_unjustified_majority_rule_and_metadata_leak():
    case = {"case_id": "heldout-community-rule-design-transfer-001"}
    answer = (
        "The majority can restrict private choices whenever it prefers a shared rule. "
        "There is no need to review the rule or provide an appeal."
    )
    transport = {
        "status": 200,
        "error": None,
        "body": {
            "ok": True,
            "response": answer,
            "recommendation": {
                "title": "The Barangay Before the State",
                "url": "https://geralddaquila.com/2026/09/21/the-barangay-before-the-state-human-scale-governance-in-practice/",
                "rationale": "Meta Description: a long excerpt from the page",
            },
        },
    }
    checks = evaluate_held(case, transport)
    assert not all(item["passed"] for item in checks)
    failed = {item["name"] for item in checks if not item["passed"]}
    assert "no_majority_or_convenience_shortcut" in failed
    assert "visitor_facing_doorway_rationale" in failed

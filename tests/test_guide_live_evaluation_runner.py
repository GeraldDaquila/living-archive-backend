from pathlib import Path

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
            "response_provenance": {
                "class": "llm",
                "provider": "gemini",
                "model": "gemini-3.8-flash",
                "llm_invoked": True,
            },
        },
    }
    expected_doorway = {
        "title": "The Barangay Before the State: Human-Scale Governance in Practice",
        "url": "https://geralddaquila.com/2026/09/21/the-barangay-before-the-state-human-scale-governance-in-practice/",
    }
    checks = evaluate_held(case, transport, expected_doorway=expected_doorway)
    assert all(item["passed"] for item in checks), checks


def test_community_rule_design_transfer_heldout_rejects_deterministic_fallback_even_when_content_looks_good():
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
            "response_provenance": {
                "class": "deterministic_recovery",
                "provider": "bounded_provider_exhaustion_recovery",
                "model": None,
                "llm_invoked": False,
            },
        },
    }
    expected_doorway = {
        "title": "The Barangay Before the State: Human-Scale Governance in Practice",
        "url": "https://geralddaquila.com/2026/09/21/the-barangay-before-the-state-human-scale-governance-in-practice/",
    }
    checks = evaluate_held(case, transport, expected_doorway=expected_doorway)
    failed = {item["name"] for item in checks if not item["passed"]}
    assert "attributable_llm" in failed


def test_community_rule_design_transfer_rejects_generic_community_ledger_doorway():
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
                "title": "ARK-004: Post-Fiat Trade — The Community Ledger SOP",
                "url": "https://geralddaquila.com/2026/05/02/ark-004-post-fiat-trade-the-community-ledger-sop/",
                "rationale": "This resource offers a related perspective and a useful next step in the Living Archive.",
            },
            "response_provenance": {
                "class": "llm",
                "provider": "gemini",
                "model": "gemini-3.8-flash",
                "llm_invoked": True,
            },
        },
    }
    expected_doorway = {
        "title": "The Barangay Before the State: Human-Scale Governance in Practice",
        "url": "https://geralddaquila.com/2026/09/21/the-barangay-before-the-state-human-scale-governance-in-practice/",
    }
    checks = evaluate_held(case, transport, expected_doorway=expected_doorway)
    failed = {item["name"] for item in checks if not item["passed"]}
    assert "relevant_archive_doorway" in failed


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
    expected_doorway = {
        "title": "The Barangay Before the State: Human-Scale Governance in Practice",
        "url": "https://geralddaquila.com/2026/09/21/the-barangay-before-the-state-human-scale-governance-in-practice/",
    }
    checks = evaluate_held(case, transport, expected_doorway=expected_doorway)
    assert not all(item["passed"] for item in checks)
    failed = {item["name"] for item in checks if not item["passed"]}
    assert "no_majority_or_convenience_shortcut" in failed
    assert "visitor_facing_doorway_rationale" in failed


def test_provider_probe_query_does_not_match_an_exact_approved_gold_standard():
    from general_guide_gold_standards import resolve_exact_gold_standard

    assert resolve_exact_gold_standard(live_evaluation.PROVIDER_PROBE_QUERY) is None


def test_provider_probe_query_is_distinct_from_primary_visitor_smoke_to_avoid_cache_reuse():
    visitor_smoke_query = (
        "How can leaders weigh obligations to employees, customers, and local residents "
        "when a decision benefits one group but imposes costs on another?"
    )
    probe = live_evaluation.PROVIDER_PROBE_QUERY
    assert probe != visitor_smoke_query
    assert all(term in probe.casefold() for term in ("employees", "customers", "residents"))


def test_provider_probe_accepts_nearby_residents_without_literal_local_qualifier():
    response = (
        "Leaders weigh obligations to employees, customers, and residents by identifying "
        "who benefits, who bears costs, and how those burdens are distributed. They should "
        "explain the trade-offs and make the reasons for the decision explicit."
    )
    assert live_evaluation.has_stakeholder_tradeoff_explanation(response)


def test_community_rule_participation_accepts_input_from_people_whose_liberty_is_limited():
    case = {"case_id": "heldout-community-rule-design-transfer-001"}
    answer = (
        "Identify the shared need, concrete risk, and the specific liberty being limited. "
        "Test necessity and proportionality, including whether a less intrusive measure would work. "
        "Gather evidence and diverse perspectives, and solicit input from those whose liberty would be curtailed "
        "as well as the broader community. Weigh the seriousness of the risk, the effectiveness of the limit, "
        "available alternatives, and fairness in who bears the burden. Publish the reasoning, provide an appeal, "
        "and review observable outcomes. The majority alone is not enough to justify a restriction."
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
                "rationale": "This resource offers a related perspective on human-scale community governance.",
            },
            "response_provenance": {
                "class": "llm", "provider": "groq", "model": "openai/gpt-oss-120b", "llm_invoked": True,
            },
        },
    }
    expected = {
        "title": "The Barangay Before the State: Human-Scale Governance in Practice",
        "url": "https://geralddaquila.com/2026/09/21/the-barangay-before-the-state-human-scale-governance-in-practice/",
    }
    checks = evaluate_held(case, transport, expected_doorway=expected)
    participation = next(item for item in checks if item["name"] == "affected_party_participation")
    assert participation["passed"], checks


def test_transparency_trust_accepts_conditional_reciprocity_and_earned_trust_paraphrases():
    case = {"case_id": "heldout-transparency-trust-relational-synthesis-001"}
    answer = (
        "Transparency—making decisions, reasons, evidence, and conduct open to scrutiny—can support justified trust "
        "by allowing people to see how and why choices are made, which makes trust feel earned rather than assumed. "
        "When institutions share the information behind their actions, people can assess whether conduct is consistent, "
        "fair, and competent. Reasonable trust, in turn, can make transparency more possible: people may ask questions, "
        "share information, and engage constructively. This reciprocity is conditional, not automatic. Disclosure "
        "does not make poor conduct trustworthy, and trust does not remove the need for accountability. Legitimate "
        "privacy and confidentiality still matter."
    )
    transport = {
        "status": 200,
        "error": None,
        "body": {
            "ok": True,
            "response": answer,
            "recommendation": None,
            "response_provenance": {
                "class": "llm", "provider": "nvidia", "model": "nvidia/nemotron-3.5-lightning-30b-a3b", "llm_invoked": True,
            },
        },
    }
    checks = evaluate_held(case, transport)
    assert all(item["passed"] for item in checks), checks


def test_provider_probe_is_scheduled_before_the_heldout_workload_to_preserve_provider_budget():
    import inspect

    source = inspect.getsource(live_evaluation.main)
    assert source.index("provider_probe_started_at") < source.index("for index,(split,item) in enumerate(workload)")


def test_provider_probe_query_is_concise_and_forbids_inline_navigation_links():
    query = live_evaluation.PROVIDER_PROBE_QUERY.casefold()
    assert "employees" in query and "customers" in query and "residents" in query
    assert "one concise paragraph" in query
    assert "do not include urls" in query
    assert "resource recommendations" in query


def test_transparency_trust_accepts_two_direction_and_conversely_reciprocity_language():
    case = {"case_id": "heldout-transparency-trust-relational-synthesis-001"}
    answer = (
        "Transparency makes decisions, reasons, evidence, and conduct open to scrutiny, while trust is justified "
        "reliance on conduct that proves dependable. Transparency supports trust by allowing people to inspect "
        "decisions and correct mistakes. The relationship runs in two directions: conversely, reasonable trust "
        "makes people more willing to share information and engage openly. These conditions are mutually reinforcing, "
        "but neither guarantees the other; the reciprocity is conditional, not automatic. Accountability and privacy "
        "still matter."
    )
    transport = {
        "status": 200,
        "error": None,
        "body": {
            "ok": True,
            "response": answer,
            "recommendation": None,
            "response_provenance": {
                "class": "llm", "provider": "nvidia", "model": "nvidia/nemotron-3.5-lightning-30b-a3b", "llm_invoked": True,
            },
        },
    }
    checks = evaluate_held(case, transport)
    reciprocal = next(item for item in checks if item["name"] == "reciprocal_but_not_identical")
    assert reciprocal["passed"], checks


def test_provider_probe_requires_stakeholder_tradeoff_explanation():
    accurate = (
        "Leaders face a persistent tension: decisions that improve one stakeholder group often create trade-offs "
        "for others. Weighing obligations across employees, customers, and local residents requires making those "
        "trade-offs explicit rather than letting them remain hidden."
    )
    generic = (
        "A useful starting point is to ask how the situation works through particular conditions. "
        "Repeated signals, incentives, relationships, constraints, and consequences can shape outcomes."
    )
    assert live_evaluation.has_stakeholder_tradeoff_explanation(accurate)
    assert not live_evaluation.has_stakeholder_tradeoff_explanation(generic)


def test_provider_probe_requires_final_response_invocation_id():
    body = {"response_provenance": {"provider": "nvidia", "model": "test-model", "llm_invoked": True}}
    assert live_evaluation.provider_invocation_id(body) is None
    body["response_provenance"]["provider_invocation_id"] = "nvidia-request-123"
    assert live_evaluation.provider_invocation_id(body) == "nvidia-request-123"


def test_transparency_trust_gold_star_is_retrieved_as_bounded_guidance():
    from gold_star_lessons import active_quality_contribution

    contribution = active_quality_contribution("What is the relationship between transparency and trust?")
    assert contribution is not None
    assert contribution["benchmark_id"] == "general-guide-relational-synthesis-concept-pairs-2026-11-24"
    assert contribution["authority_mode"] == "structural_guidance_only"
    assert contribution["candidates"][0]["discipline"]
    assert "deterministic" not in contribution["authority_mode"]


def test_transparency_trust_retrieval_fragment_is_rejected_as_live_answer():
    case = {"case_id": "heldout-transparency-trust-relational-synthesis-001"}
    transport = {
        "status": 200,
        "error": None,
        "body": {
            "ok": True,
            "response": (
                "The Archive material available here offers this starting point: "
                "Why trust may be as important to societal resilience as roads, "
                "power grids, and communication networks—and why its erosion "
                "creates consequences far beyond politics."
            ),
            "recommendation": None,
            "provider": "deterministic_recovery",
            "model": "retrieval-excerpt",
            "response_provenance": {
                "class": "deterministic_recovery",
                "llm_invoked": False,
            },
        },
    }
    checks = evaluate_held(case, transport)
    failed = {item["name"] for item in checks if not item["passed"]}
    assert {
        "attributable_llm",
        "distinct_concept_roles",
        "relationship_mechanism",
        "reciprocal_but_not_identical",
        "not_retrieval_fragment",
    }.issubset(failed)


def test_transparency_trust_live_answer_requires_relationship_and_limits():
    case = {"case_id": "heldout-transparency-trust-relational-synthesis-001"}
    answer = (
        "Transparency makes relevant decisions, reasons, evidence, and limits visible, "
        "while trust is the justified willingness to rely on conduct that proves dependable. "
        "Transparency enables scrutiny and correction because people can examine whether "
        "commitments are being kept. When an institution responds honestly, that scrutiny "
        "can strengthen trust; trust in turn makes people more willing to engage with "
        "disclosures. They reinforce one another but neither guarantees the other. "
        "Disclosure without context or accountability can mislead, and legitimate privacy "
        "and confidentiality must still be protected."
    )
    transport = {
        "status": 200,
        "error": None,
        "body": {
            "ok": True,
            "response": answer,
            "recommendation": None,
            "response_provenance": {
                "class": "llm",
                "llm_invoked": True,
                "provider": "test-provider",
                "model": "test-model",
            },
        },
    }
    checks = evaluate_held(case, transport)
    assert all(item["passed"] for item in checks), checks


def test_critical_live_acceptance_case_is_separate_from_fixed_calibration_suite():
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    calibration = json.loads((root / "docs/qa/guide_learning_evaluation_set.json").read_text())
    critical = json.loads((root / "docs/qa/guide_live_critical_evaluation_cases.json").read_text())
    calibration_ids = {item["case_id"] for item in calibration["cases"]}
    critical_ids = {item["case_id"] for item in critical["cases"]}

    assert len(calibration["cases"]) == 8
    assert critical_ids == {"heldout-transparency-trust-relational-synthesis-001"}
    assert calibration_ids.isdisjoint(critical_ids)
    assert critical["cases"][0]["query"] == "What is the relationship between transparency and trust?"


def test_critical_live_suite_is_included_in_runner_workload():
    import inspect

    source = inspect.getsource(live_evaluation.main)
    assert "critical_cases=critical_suite.get(\"cases\",[])" in source
    assert 'workload=[("gold_standard",x) for x in records]+[("held_out",x) for x in heldout_cases]' in source



def test_transparency_trust_accepts_clear_reciprocal_paraphrase_but_keeps_provenance_gate():
    case = {"case_id": "heldout-transparency-trust-relational-synthesis-001"}
    answer = (
        "Transparency and trust are related, but they are not the same thing. "
        "Transparency means making relevant decisions, reasons, evidence, and processes visible enough to be examined; "
        "trust is the confidence that a person or institution will act with sufficient honesty, competence, consistency, "
        "and regard for those affected. Transparency can support justified trust because people are better able to "
        "understand what is being done, assess whether explanations match conduct, and identify mistakes or conflicts "
        "of interest. Visibility creates the possibility of scrutiny; trustworthy conduct is what gives that scrutiny "
        "a reason to build confidence. The relationship can also work in the other direction. Where people have "
        "reasonable trust, they may be more willing to share information, raise concerns, and engage openly; where "
        "institutions respond to that openness with candour and correction, trust can deepen. But neither side "
        "guarantees the other. Disclosure without context can confuse or mislead, and an institution can be transparent "
        "about a poor decision without making the decision trustworthy. Trust built on secrecy may be fragile because "
        "people cannot independently assess what they are being asked to rely on. Legitimate privacy and confidentiality "
        "must still be protected while decisions and uses of power remain accountable."
    )
    transport = {
        "status": 200,
        "error": None,
        "body": {
            "ok": True,
            "response": answer,
            "recommendation": None,
            "response_provenance": {
                "class": "deterministic_recovery",
                "provider": "bounded_conceptual_relationship_recovery",
                "model": "deterministic-contract-recovery",
                "llm_invoked": False,
            },
        },
    }
    checks = evaluate_held(case, transport)
    reciprocal = next(item for item in checks if item["name"] == "reciprocal_but_not_identical")
    provenance = next(item for item in checks if item["name"] == "attributable_llm")
    assert reciprocal["passed"], checks
    assert provenance["passed"] is False, checks

def test_live_evaluation_requires_request_local_correlation_id():
    valid = {"request_correlation_id": "0123456789abcdef0123456789abcdef"}
    stable_query_id_only = {"request_id": "basic-0123456789abcdef"}
    malformed = {"request_correlation_id": "basic-0123456789abcdef"}
    assert live_evaluation.visitor_request_correlation_id(valid) == "0123456789abcdef0123456789abcdef"
    assert live_evaluation.visitor_request_correlation_id(stable_query_id_only) is None
    assert live_evaluation.visitor_request_correlation_id(malformed) is None
    assert live_evaluation.visitor_request_correlation_id(None) is None

def test_live_evaluation_records_request_local_correlation_ids():
    source = (Path(__file__).resolve().parents[1] / "scripts" / "guide_live_evaluation.py").read_text(encoding="utf-8")
    assert 'checks.append(check(' in source
    assert '"request_correlation_id"' in source
    assert '"request_correlation_id":request_correlation' in source
    assert '"request_correlation_id":provider_probe_correlation_id' in source

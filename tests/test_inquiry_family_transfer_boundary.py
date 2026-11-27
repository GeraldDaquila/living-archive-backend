"""Regression tests for hard inquiry-family boundaries in adaptive lesson transfer."""
from inquiry_family_transfer_contract import (
    classify_inquiry_family,
    lesson_transfer_compatibility,
)
from gold_star_lessons import select_lesson_candidates
from gold_star_question_contract import build_question_contract
from gold_star_semantic_contract import evaluate_semantic_contract
from gold_star_response_floor import evaluate_response_floor
from deterministic_answer_recovery import compose_recovery, compose_task_specific_recovery, has_registered_recovery
from general_guide_composition import _build_general_guide_system_prompt


PAIN_IDENTITY_QUESTION = (
    "How should a person hold pain without turning it into a total identity?"
)
OFF_TARGET_GOVERNANCE_ANSWER = (
    "Start by defining the outcome the change must achieve, the responsibilities "
    "that cannot be lost, and the people who will live with its consequences. "
    "Then compare realistic options against those requirements rather than "
    "assuming the proposed course is the only one. Examine what each option makes "
    "possible, what it may damage, who bears the costs, and what evidence would "
    "justify changing direction. Choose deliberately, make the reasoning and "
    "limits visible, and remain accountable for what follows."
)
ON_TARGET_REFLECTIVE_ANSWER = (
    "Pain can be part of a person's story without becoming the whole of who they are. "
    "Holding it means acknowledging what hurt and allowing it to matter, while also "
    "making room for relationships, values, interests, and hopes that remain part "
    "of the self. You do not have to deny the pain or turn it into your identity."
)


def test_pain_and_identity_question_is_classified_before_generic_how_should_task():
    result = classify_inquiry_family(PAIN_IDENTITY_QUESTION)
    assert result["family"] == "personal_lived_reflective"
    assert result["identity_focus"] is True
    contract = build_question_contract(PAIN_IDENTITY_QUESTION)
    assert contract["inquiry_family"]["family"] == "personal_lived_reflective"
    assert contract["task"]["primary"] == "lived_reflective_inquiry_candidate"
    assert contract["response"]["shape"] == "reflective_explanation"
    assert contract["domain"]["primary"] == "human_experience"
    assert contract["requested_outcome"] == "understand_lived_experience_without_identity_reduction"
    prompt = _build_general_guide_system_prompt(PAIN_IDENTITY_QUESTION)
    assert "LIVED EXPERIENCE AND IDENTITY BOUNDARY" in prompt
    assert "For practical questions" not in prompt
    governance_prompt = _build_general_guide_system_prompt("How should a community decide a fair rule?")
    assert "LIVED EXPERIENCE AND IDENTITY BOUNDARY" not in governance_prompt


def test_lived_experience_without_identity_focus_does_not_require_identity_claims():
    query = "How should a person live with pain?"
    family = classify_inquiry_family(query)
    assert family["family"] == "personal_lived_reflective"
    assert family["identity_focus"] is False
    result = evaluate_semantic_contract(
        query,
        {"ok": True, "response": "Pain can be difficult to carry. A person can acknowledge it, seek support, and make room for moments of relief without denying what happened."},
    )
    assert result["question_type"] == "lived_reflective_inquiry"
    assert result["hard_failures"] == []


def test_institutional_governance_lesson_is_incompatible_with_lived_pain_question():
    lesson = {
        "reasoning_family": "governance_balance_constitutional_stability_participatory_legitimacy_adaptive_responsiveness"
    }
    decision = lesson_transfer_compatibility(PAIN_IDENTITY_QUESTION, lesson)
    assert decision["compatible"] is False
    assert decision["reason"] == "cross_family_transfer_blocked"


def test_live_selector_never_returns_incompatible_families_for_pain_and_identity_question(monkeypatch):
    import gold_star_lessons

    humane = {
        "id": "humane-test",
        "runtime_transfer": True,
        "exact_answer_authority": False,
        "query": "How can a person hold pain without losing identity?",
        "known_theme": "person pain identity",
        "assertions": ["A person is more than a painful experience."],
        "reasoning_family": "humane_orientation",
        "transferable_discipline": "Keep the person's humanity in view.",
        "abstention_boundary": "",
        "variants": [],
    }
    governance = {
        **humane,
        "id": "governance-test",
        "query": "How should a community decide a policy?",
        "known_theme": "community policy decision",
        "reasoning_family": "institutional_governance",
    }
    for item in (humane, governance):
        item["signature_terms"] = gold_star_lessons._lesson_signature(item)
        item["variant_terms"] = gold_star_lessons._concept_terms(" ".join(item["variants"]))
        item["reasoning_terms"] = gold_star_lessons._concept_terms(item["reasoning_family"])
    monkeypatch.setattr(gold_star_lessons, "_LESSONS", [governance, humane])

    candidates = select_lesson_candidates(PAIN_IDENTITY_QUESTION)
    assert [item["benchmark_id"] for item in candidates] == ["humane-test"]
    assert all(
        lesson_transfer_compatibility(PAIN_IDENTITY_QUESTION, item)["compatible"]
        for item in candidates
    )


def test_genuine_community_decision_question_keeps_its_governed_candidate_set():
    query = (
        "How should a community decide whether limits on individual freedom are "
        "justified by shared responsibilities?"
    )
    assert classify_inquiry_family(query)["family"] == "institutional_governance"
    candidates = select_lesson_candidates(query)
    assert candidates
    assert any(
        item.get("match_basis") == "governed_community_tradeoff_policy"
        for item in candidates
    )


def test_semantic_contract_rejects_governance_substitution_and_accepts_lived_answer():
    bad = evaluate_semantic_contract(
        PAIN_IDENTITY_QUESTION, {"ok": True, "response": OFF_TARGET_GOVERNANCE_ANSWER}
    )
    assert bad["question_type"] == "lived_reflective_inquiry"
    assert bad["status"] == "fail"
    assert set(bad["hard_failures"]) == {
        "addresses_named_lived_experience",
        "preserves_experience_identity_distinction",
    }

    superficial = evaluate_semantic_contract(
        PAIN_IDENTITY_QUESTION,
        {"ok": True, "response": "Pain is part of your identity. Define the outcome, compare options, and remain accountable."},
    )
    assert superficial["status"] == "fail"
    assert "preserves_experience_identity_distinction" in superficial["hard_failures"]

    good = evaluate_semantic_contract(
        PAIN_IDENTITY_QUESTION, {"ok": True, "response": ON_TARGET_REFLECTIVE_ANSWER}
    )
    assert good["question_type"] == "lived_reflective_inquiry"
    assert good["status"] == "review_required"
    assert good["hard_failures"] == []


def test_final_response_floor_enforces_lived_reflective_task_fit():
    result = evaluate_response_floor(
        PAIN_IDENTITY_QUESTION,
        {"ok": True, "query": PAIN_IDENTITY_QUESTION, "intent": "TOPICAL_INQUIRY",
         "response": OFF_TARGET_GOVERNANCE_ANSWER,
         "answer_basis": {"kind": "general_knowledge", "label": "General knowledge",
                          "explanation": "A bounded general answer."},
         "response_provenance": {"class": "deterministic_fallback"},
         "route_source": "general_guide_composition"},
    )
    assert result["status"] == "fail"
    assert result["semantic_enforcement"]["enforced"] is True
    assert result["semantic_enforcement"]["status"] == "fail"
    assert result["semantic_enforcement"]["question_type"] == "lived_reflective_inquiry"

def test_off_target_lived_response_gets_one_bounded_repair_without_touching_evaluation_arms():
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1] / "general_guide_composition.py"
    ).read_text(encoding="utf-8")
    repair = source.index("LIVED-REFLECTIVE TASK-FIT REPAIR")
    guard = source.rfind("evaluation is None", 0, repair)
    deadline = source.index("deadline_monotonic=provider_deadline_monotonic", repair)
    assert guard >= 0
    assert deadline > repair
    assert "effective_question,\n                        None," in source[repair:deadline]
    assert "schema=_build_provider_composition_schema(None)" in source[repair:deadline]
    assert "on_target_repair_accepted" in source
    assert "repair_unavailable_or_still_off_target" in source

def test_epistemic_distress_classifier_covers_natural_bereavement_paraphrases():
    # Visitors should not need academic terms such as "metaphysical" or
    # "epistemic" for the same vulnerable certainty-seeking need to be recognized.
    paraphrases = (
        "My wife died. Is she still somewhere?",
        "I am frightened that death means everything disappears. Can anyone know?",
        "My child is gone and I need to know whether the soul survives.",
    )
    for query in paraphrases:
        result = classify_inquiry_family(query)
        assert result["family"] == "epistemic_distress"

    # Neither metaphysical curiosity nor distress alone should trigger this
    # specialized response family.
    assert classify_inquiry_family("Does consciousness continue after death?")["family"] == "unknown"
    assert classify_inquiry_family("I am grieving and frightened about the future.")["family"] != "epistemic_distress"


def test_epistemic_distress_question_is_classified_and_contracts_the_response():
    query = "How should the Guide respond when a user seeks metaphysical certainty during distress?"
    family = classify_inquiry_family(query)
    assert family["family"] == "epistemic_distress_guidance"
    assert lesson_transfer_compatibility(query, {"reasoning_family": "institutional_governance"})["compatible"] is False
    contract = build_question_contract(query)
    assert contract["task"]["primary"] == "epistemic_distress_guidance_candidate"
    assert contract["response"]["shape"] == "compassionate_epistemic_guidance"
    assert contract["requested_outcome"] == "respond_compassionately_without_manufacturing_metaphysical_certainty"


def test_epistemic_distress_semantic_gate_rejects_generic_governance_substitution():
    query = "How should the Guide respond when a user seeks metaphysical certainty during distress?"
    generic = (
        "Start by defining the outcome the change must achieve, the responsibilities that cannot be lost, "
        "and the people who will live with its consequences. Compare realistic options and examine what "
        "each may damage, who bears the costs, and what evidence would justify changing direction. "
        "Choose deliberately and remain accountable for what follows."
    )
    result = evaluate_semantic_contract(query, {"ok": True, "response": generic})
    assert result["question_type"] == "epistemic_distress_guidance"
    assert result["status"] == "fail"
    assert {"recognizes_distress", "preserves_epistemic_boundary", "supports_agency"}.issubset(set(result["hard_failures"]))


def test_epistemic_distress_contract_rejects_confident_metaphysical_claims():
    query = "How should the Guide respond when a user seeks metaphysical certainty during distress?"
    overclaim = (
        "The person's experience and belief deserve care. The interpretation and tradition are meaningful, "
        "and the evidence confirms that the afterlife definitely exists. Respond with compassion and support "
        "while helping the person think independently."
    )
    result = evaluate_semantic_contract(query, {"ok": True, "response": overclaim})
    assert result["status"] == "fail"
    assert "calibrates_metaphysical_uncertainty" in result["hard_failures"]


def test_epistemic_distress_provider_exhaustion_recovery_is_on_topic_and_enforced():
    query = "How should the Guide respond when a user seeks metaphysical certainty during distress?"
    answer = compose_recovery(query)
    assert has_registered_recovery(query) is True
    assert "metaphysical certainty" in answer.casefold()
    assert "unverifiable" in answer.casefold()
    assert "oracle" in answer.casefold()
    result = evaluate_semantic_contract(query, {"ok": True, "response": answer})
    assert result["question_type"] == "epistemic_distress_guidance"
    assert result["hard_failures"] == []
    floor = evaluate_response_floor(
        query,
        {"ok": True, "query": query, "intent": "TOPICAL_INQUIRY", "response": answer,
         "answer_basis": {"kind": "general_knowledge", "label": "General knowledge",
                          "explanation": "Bounded general guidance."},
         "response_provenance": {"class": "deterministic_fallback"}},
    )
    assert floor["semantic_enforcement"]["enforced"] is True
    assert floor["semantic_enforcement"]["status"] == "pass"


def test_epistemic_distress_prompt_disables_generic_practical_template():
    from general_guide_composition import _build_general_guide_system_prompt
    query = "How should the Guide respond when a user seeks metaphysical certainty during distress?"
    prompt = _build_general_guide_system_prompt(query)
    assert "METAPHYSICAL UNCERTAINTY DURING DISTRESS" in prompt
    assert "Do not substitute governance" in prompt
    governance_prompt = _build_general_guide_system_prompt("How should a community decide a fair rule?")
    assert "METAPHYSICAL UNCERTAINTY DURING DISTRESS" not in governance_prompt


def test_epistemic_distress_off_target_provider_answer_gets_one_bounded_repair_outside_evaluation():
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1] / "general_guide_composition.py"
    ).read_text(encoding="utf-8")
    repair = source.index("EPISTEMIC-DISTRESS TASK-FIT REPAIR")
    guard = source.rfind("evaluation is None", 0, repair)
    deadline = source.index("deadline_monotonic=provider_deadline_monotonic", repair)
    assert guard >= 0
    assert deadline > repair
    assert "epistemic_distress_task_fit_repair" in source
    assert "unverifiable metaphysical claims as fact" in source[repair:deadline]


def test_provider_exhaustion_recovery_answers_lived_question_instead_of_generic_how_template():
    answer = compose_recovery(PAIN_IDENTITY_QUESTION)
    assert has_registered_recovery(PAIN_IDENTITY_QUESTION) is True
    assert compose_task_specific_recovery(PAIN_IDENTITY_QUESTION) is None
    assert "pain" in answer.casefold()
    assert "identity" in answer.casefold()
    assert "responsibilities that cannot be lost" not in answer.casefold()
    assert "people who will live with its consequences" not in answer.casefold()
    semantic = evaluate_semantic_contract(
        PAIN_IDENTITY_QUESTION, {"ok": True, "response": answer}
    )
    assert semantic["hard_failures"] == []
    floor = evaluate_response_floor(
        PAIN_IDENTITY_QUESTION,
        {
            "ok": True,
            "query": PAIN_IDENTITY_QUESTION,
            "intent": "TOPICAL_INQUIRY",
            "response": answer,
            "answer_basis": {
                "kind": "general_knowledge",
                "label": "General knowledge",
                "explanation": "A bounded, provider-independent reflective explanation.",
            },
            "response_provenance": {"class": "deterministic_fallback"},
        },
    )
    assert floor["status"] == "pass"
    assert floor["semantic_enforcement"]["status"] == "pass"

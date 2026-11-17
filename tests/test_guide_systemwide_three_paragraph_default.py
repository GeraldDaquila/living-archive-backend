"""Tests for the system-wide three-paragraph Guide default and fragmented-knowledge recovery."""

from pathlib import Path

from general_guide_composition import (
    _fragmented_knowledge_recovery,
    _has_fragmented_knowledge_explanation,
    _requires_fragmented_knowledge_explanation,
    enforce_response_contracts,
)

ROOT = Path(__file__).resolve().parents[1]
QUERY = "How does fragmented knowledge impede wise action?"

SCREENSHOT_REGRESSION = (
    "A practical way to approach fragmented knowledge impede wise action is to define the outcome you want, "
    "identify the main constraint, and choose one step small enough to test. Before acting, consider who else "
    "is affected and what could go wrong. Check the result against the original goal and adjust rather than "
    "assuming the first attempt must be final."
)


def test_fragmented_knowledge_question_requires_explanation_not_planning_advice():
    assert _requires_fragmented_knowledge_explanation(QUERY)
    assert _requires_fragmented_knowledge_explanation(
        "Why does siloed information undermine wise decisions?"
    )
    assert not _requires_fragmented_knowledge_explanation(
        "How can I plan a small experiment?"
    )


def test_screenshot_style_generic_checklist_is_replaced_at_final_contract_boundary():
    result = enforce_response_contracts(QUERY, SCREENSHOT_REGRESSION)
    paragraphs = [p.strip() for p in result.split("\n\n") if p.strip()]
    assert len(paragraphs) == 3
    assert _has_fragmented_knowledge_explanation(result)
    assert paragraphs[0].startswith("Fragmented knowledge impedes wise action")
    assert "For example" in paragraphs[1]
    assert "what is known" in paragraphs[2]
    assert "choose one step small enough to test" not in result


def test_valid_three_paragraph_fragmented_knowledge_explanation_is_preserved():
    valid = _fragmented_knowledge_recovery()
    assert _has_fragmented_knowledge_explanation(valid)
    assert enforce_response_contracts(QUERY, valid) == valid


def test_general_guide_prompt_makes_three_paragraphs_the_default_without_conflicting_short_answer_rule():
    source = (ROOT / "general_guide_composition.py").read_text(encoding="utf-8")
    assert "A substantive explanatory or conceptual question defaults to three purposeful paragraphs" in source
    assert "For other substantive explanatory or conceptual answers, use three purposeful paragraphs by default" in source
    assert "For a substantive explanatory, conceptual, educational, social, or Archive-related question, present three connected, readable paragraphs by default" in source
    assert "For other explanatory or conceptual answers, use 2–4 purposeful paragraphs when that improves comprehension." not in source
    assert "a short conceptual question may need only two or three compact paragraphs" not in source

def test_final_visitor_boundary_uses_shared_gold_standard_recovery_instead_of_generic_apology():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    marker = "_systemwide_recovery = _sanitize_basic_inquiry_response("
    assert marker in source
    boundary_start = source.index(marker)
    boundary = source[boundary_start:boundary_start + 4000]
    assert "_compose_provider_exhaustion_recovery(query)" in boundary
    assert "len(_systemwide_paragraphs) >= 3" in boundary
    assert "Preserve an already verified doorway" in boundary
    assert "authoritative_doorway = None" not in boundary
    assert '"kind": "general_knowledge"' in boundary
    assert "I couldn’t produce a reliable answer to that question just now." in boundary

def test_default_composition_quality_gate_requires_substance_not_just_three_paragraphs():
    source = (ROOT / "general_guide_composition.py").read_text(encoding="utf-8")
    for requirement in (
        "COMPOSITION QUALITY GATE — mandatory for every substantive answer",
        'For a "how can" question, name the practical method or decision principle immediately',
        "Give each paragraph a different job",
        "Do not introduce the name of an Archive assessment, framework, governance instrument, or internal tool into the body of a general answer",
        "every sentence must answer the visitor's question",
    ):
        assert requirement in source


def test_default_composition_quality_gate_is_not_limited_to_stakeholder_question():
    source = (ROOT / "general_guide_composition.py").read_text(encoding="utf-8")
    prompt_start = source.index("_GENERAL_GUIDE_SYSTEM =")
    prompt_end = source.index("\n\ndef _normalize_space", prompt_start)
    prompt = source[prompt_start:prompt_end]
    assert "COMPOSITION QUALITY GATE — mandatory for every substantive answer" in prompt
    assert "A plausible thematic association is not enough" in prompt
    assert "not only named question classes" in prompt



def test_community_continuity_revision_recovery_answers_after_archive_retrieval_miss():
    from deterministic_answer_recovery import (
        compose_recovery,
        is_community_continuity_revision_question,
    )

    query = "How can communities preserve continuity while revising harmful inherited patterns?"
    assert is_community_continuity_revision_question(query)
    assert not is_community_continuity_revision_question(
        "How can communities preserve continuity across generations?"
    )
    answer = compose_recovery(query)
    paragraphs = [part.strip() for part in answer.split("\n\n") if part.strip()]
    assert len(paragraphs) == 3
    assert paragraphs[0].startswith("Communities preserve continuity")
    assert "people who live with the effects" in paragraphs[1]
    assert "what is worth preserving" in paragraphs[2]
    assert "Archive" not in answer


def test_community_continuity_nonanswer_is_replaced_and_doorway_is_recovered():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "do not have enough grounded material" in source
    assert "is_community_continuity_revision_question(query)" in source
    assert '== "community_continuity_revision"' in source
    assert 'composition_context.get("answer_basis") == "general_conceptual_orientation"' in source
    assert '"label": "General conceptual orientation"' in source
    assert "rather than claiming that the Living Archive establishes the full answer" in source



def test_retrieval_only_disclaimer_is_rejected_for_ordinary_explanatory_questions():
    from general_guide_composition import is_generic_nonanswer

    query = "How can communities preserve continuity while revising harmful inherited patterns?"
    screenshot_style = (
        "I do not have enough grounded material here to give a specific Archive-based answer, "
        "but the question can still be approached by making its central tension visible: what is at stake, "
        "who or what is affected, what responsibilities are involved, and what would change if the situation "
        "were understood differently. That is a starting orientation rather than a substitute for evidence or context.\n\n"
        "A useful next question is where this distinction matters most: in how the organization makes decisions, "
        "measures success, or responds to consequences.\n\n"
        "The approach can be revisited as consequences become clearer and the people affected share what they are experiencing."
    )
    assert is_generic_nonanswer(query, screenshot_style)

    archive_specific_query = "How does the Living Archive say communities should preserve continuity while revising harmful inherited patterns?"
    archive_specific_disclaimer = screenshot_style.replace(
        "The approach can be revisited as consequences become clearer and the people affected share what they are experiencing.",
        "The approach can be revisited as consequences become clearer and the people affected share what they are experiencing. The available sources do not establish a more specific canonical prescription.",
    )
    assert not is_generic_nonanswer(archive_specific_query, archive_specific_disclaimer)


def test_outer_basic_inquiry_exception_path_reuses_terminal_answer_and_navigation_contracts():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    marker = 'The Guide Basic Inquiry seam failed;'
    start = source.index(marker)
    end = source.index('explicit_formation_route =', start)
    boundary = source[start:end]
    assert "_basic_inquiry_provider_exhaustion_response(" in boundary
    assert "general_guide_composition.enforce_response_contracts(" in boundary
    assert "_terminal_has_registered_recovery(query)" in boundary
    assert "_terminal_recovery_recommendation(query)" in boundary
    assert '"canonical_doorway": recovery_recommendation' in boundary
    assert '"answer_basis": {' in boundary
    assert "_basic_inquiry_round1_deterministic_response(" not in boundary
    assert "str(exc)[:180]" in boundary



def test_provider_exhaustion_returns_registered_continuity_answer_and_doorway_together():
    from main import _basic_inquiry_provider_exhaustion_response
    from deterministic_answer_recovery import registered_recovery_recommendation

    query = "How can communities preserve continuity while revising harmful inherited patterns?"
    result = _basic_inquiry_provider_exhaustion_response(
        query,
        {},
        {"context_blocks": ""},
        recommendation_available=True,
    )
    doorway = registered_recovery_recommendation(query)
    assert result["response"].startswith("Communities preserve continuity")
    assert len([p for p in result["response"].split("\n\n") if p.strip()]) == 3
    assert result["recommendation"] == doorway
    assert result["doorway_title"] == doorway["title"]
    assert result["doorway_url"] == doorway["url"]


def test_community_continuity_doorway_rationale_matches_the_published_essay_and_both_response_paths():
    import main
    from deterministic_answer_recovery import registered_recovery_recommendation

    query = "How can communities preserve continuity while revising harmful inherited patterns?"
    expected = "This essay explores how personal development can mature into stewardship: taking responsibility for the relationships, institutions, and shared conditions that support human flourishing. It offers a wider perspective on community continuity by asking what people must build and sustain together, rather than prescribing how a particular inherited practice should be changed."
    family_doorway = main._VERIFIED_CONCEPTUAL_FAMILY_DOORWAYS["community_continuity_revision"]
    deterministic_doorway = registered_recovery_recommendation(query)

    assert family_doorway["rationale"] == expected
    assert deterministic_doorway["rationale"] == expected
    assert family_doorway["title"] == deterministic_doorway["title"] == "From Awakening to Stewardship"
    assert family_doorway["url"] == deterministic_doorway["url"] == "https://geralddaquila.com/from-awakening-to-stewardship/"
    assert "carry wisdom and responsibility across generations" not in expected.lower()
    assert "rather than prescribing how a particular inherited practice should be changed" in expected


def test_community_continuity_gold_star_registry_and_transfer_entry_are_frozen_and_aligned():
    import json
    from pathlib import Path

    benchmark_id = "gs-2026-11-17-community-continuity-harmful-inherited-patterns"
    root = Path(__file__).resolve().parents[1]
    registry = json.loads((root / "docs/qa/gold_standard_registry.json").read_text())
    transfer = json.loads((root / "docs/qa/gold_star_qualitative_transfer_review.json").read_text())
    records = [item for item in registry["records"] if item["benchmark_id"] == benchmark_id]
    entries = [item for item in transfer["entries"] if item["benchmark_id"] == benchmark_id]

    assert len(records) == 1
    assert len(entries) == 1
    record = records[0]
    assert record["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert record["explicit_user_elevation_approval"] is True
    assert record["freeze_policy"] == "immutable_user_approved_gold_standard"
    assert record["numbering_status"] == "UNASSIGNED"
    assert record["gold_star_capabilities"]["active_quality_contributor"] is True
    assert record["gold_star_capabilities"]["deterministic_fallback_eligible"] is True
    assert len([part for part in record["expected_response"].split("\n\n") if part.strip()]) == 3
    assert record["expected_doorway"]["title"] == "From Awakening to Stewardship"
    assert record["expected_doorway"]["url"] == "https://geralddaquila.com/from-awakening-to-stewardship/"
    assert record["expected_doorway"]["rationale"] == "This essay explores how personal development can mature into stewardship: taking responsibility for the relationships, institutions, and shared conditions that support human flourishing. It offers a wider perspective on community continuity by asking what people must build and sustain together, rather than prescribing how a particular inherited practice should be changed."
    assert "rather than prescribing how a particular inherited practice should be changed" in record["expected_doorway"]["rationale"]
    assert entries[0]["activation"] == "active_quality_contributor"


def test_community_project_tradeoff_question_is_recognized_without_overmatching():
    from deterministic_answer_recovery import is_community_project_tradeoff_question

    query = "A community is divided over a renewable-energy project. What questions reveal ecological, economic, cultural, and governance trade-offs?"
    assert is_community_project_tradeoff_question(query)
    assert is_community_project_tradeoff_question(
        "What questions should residents ask about the ecological, economic, and governance trade-offs of a community solar project?"
    )
    assert not is_community_project_tradeoff_question(
        "What are the benefits of renewable energy for a household?"
    )
    assert not is_community_project_tradeoff_question(
        "What questions should a community ask about a new library?"
    )


def test_community_project_tradeoff_contract_replaces_generic_three_paragraph_filler():
    from general_guide_composition import (
        _community_project_tradeoff_recovery,
        _has_community_project_tradeoff_analysis,
        _requires_community_project_tradeoff_analysis,
        enforce_response_contracts,
    )

    query = "A community is divided over a renewable-energy project. What questions reveal ecological, economic, cultural, and governance trade-offs?"
    generic = (
        "The question about a community is divided over a renewable-energy project. What questions reveal ecological, economic, cultural, and governance trade-offs can be approached by first identifying the main issue and the decision or understanding at stake. A useful answer should distinguish what is established from what is inferred rather than fill gaps with confidence.\n\n"
        "The next step is to examine the most relevant facts, relationships, and plausible explanations. Ask which evidence would distinguish them, whose perspective may be missing, and whether any assumption is doing more work than the facts justify.\n\n"
        "This provides a grounded starting point without pretending to know details the question has not supplied. Where the evidence is incomplete, say what can reasonably be concluded and what remains open, instead of replacing the answer with a generic refusal."
    )
    assert _requires_community_project_tradeoff_analysis(query)
    assert not _has_community_project_tradeoff_analysis(generic)
    repaired = enforce_response_contracts(query, generic)
    assert repaired == _community_project_tradeoff_recovery()
    assert _has_community_project_tradeoff_analysis(repaired)
    assert len([p for p in repaired.split("\n\n") if p.strip()]) == 3


def test_community_project_tradeoff_contract_preserves_a_complete_provider_answer():
    from general_guide_composition import (
        _community_project_tradeoff_recovery,
        _has_community_project_tradeoff_analysis,
        enforce_response_contracts,
    )

    query = "A community is divided over a renewable-energy project. What questions reveal ecological, economic, cultural, and governance trade-offs?"
    complete = _community_project_tradeoff_recovery()
    assert _has_community_project_tradeoff_analysis(complete)
    assert enforce_response_contracts(query, complete) == complete


def test_community_project_tradeoff_deterministic_recovery_and_doorway_are_registered_together():
    from deterministic_answer_recovery import (
        compose_recovery,
        has_registered_recovery,
        registered_recovery_recommendation,
    )
    from main import _basic_inquiry_round1_deterministic_response

    query = "A community is divided over a renewable-energy project. What questions reveal ecological, economic, cultural, and governance trade-offs?"
    assert has_registered_recovery(query)
    answer = compose_recovery(query)
    assert answer.startswith("A fair assessment asks four connected sets of questions")
    assert len([p for p in answer.split("\n\n") if p.strip()]) == 3
    doorway = registered_recovery_recommendation(query)
    assert doorway["title"] == "Local Resilience Economies"
    assert doorway["url"] == "https://geralddaquila.com/2026/05/27/local-resilience-economies/"
    result = _basic_inquiry_round1_deterministic_response(query, {}, {"context_blocks": ""})
    assert result["response"] == answer
    assert result["recommendation"] == doorway


def test_community_project_tradeoff_provider_prompt_requires_all_four_dimensions():
    source = (ROOT / "general_guide_composition.py").read_text(encoding="utf-8")
    assert source.count("COMMUNITY PROJECT TRADE-OFF QUESTIONS:") == 2
    for term in ("ecological effects", "economic effects", "cultural effects", "governance", "no project", "residual costs", "monitoring"):
        assert term in source


def test_community_project_tradeoff_provider_and_deterministic_doorways_share_one_canonical_destination():
    import main

    query = "A community is divided over a renewable-energy project. What questions reveal ecological, economic, cultural, and governance trade-offs?"
    assert main._select_verified_doorway_conceptual_family(query) == "community_project_tradeoffs"
    doorway = main._VERIFIED_CONCEPTUAL_FAMILY_DOORWAYS["community_project_tradeoffs"]
    fallback_doorway = main._select_guide_node_fallback_doorway(query)
    assert doorway == fallback_doorway
    assert doorway["title"] == "Local Resilience Economies"
    assert "does not assess this particular renewable-energy proposal" in doorway["rationale"]


def test_public_predictive_system_question_selects_grounded_doorway_for_both_routes():
    import main
    from deterministic_answer_recovery import (
        has_registered_recovery,
        registered_recovery_recommendation,
    )

    query = (
        "A government proposes a highly efficient predictive system for public services. "
        "What constitutional and human questions must precede adoption?"
    )
    expected = {
        "title": "AI vs. Human Stewardship: Why Conscious Guidance Matters More Than Ever",
        "url": "https://geralddaquila.com/2026/06/16/ai-vs-human-stewardship-why-conscious-guidance-matters-more-than-ever/",
        "rationale": "AI vs. Human Stewardship examines why growing technological capability must remain guided by human wisdom, ethical judgment, oversight, agency, and clear accountability. It offers a broader foundation for examining predictive public systems and the responsibilities that must remain with people; it does not evaluate this particular government proposal.",
    }

    # Provider/normal routing and deterministic recovery must resolve the
    # same complete visitor-facing doorway, including its grounded explanation.
    assert main._select_verified_doorway_conceptual_family(query) == "public_predictive_systems"
    assert main._VERIFIED_CONCEPTUAL_FAMILY_DOORWAYS["public_predictive_systems"] == expected
    assert main._select_guide_node_fallback_doorway(query) == expected
    assert main._normalize_authoritative_recommendation(expected) == expected
    assert has_registered_recovery(query)
    assert registered_recovery_recommendation(query) == expected


def test_public_predictive_system_doorway_match_does_not_overreach():
    import main

    assert main._select_verified_doorway_conceptual_family(
        "A government proposes a predictive system for public services. What rights and human safeguards must precede adoption?"
    ) == "public_predictive_systems"
    assert main._select_verified_doorway_conceptual_family(
        "How can a private retailer use predictive analytics to forecast inventory?"
    ) != "public_predictive_systems"
    assert main._select_verified_doorway_conceptual_family(
        "What are the constitutional limits of government authority?"
    ) != "public_predictive_systems"


def test_exact_gold_standard_preserves_answer_and_enriches_only_matching_doorway_rationale(monkeypatch):
    import main

    query = (
        "A government proposes a highly efficient predictive system for public services. "
        "What constitutional and human questions must precede adoption?"
    )
    exact_answer = "Frozen approved Gold Standard answer."
    exact_standard = {
        "expected_response": exact_answer,
        "doorway_title": "AI vs. Human Stewardship: Why Conscious Guidance Matters More Than Ever",
        "doorway_url": "https://geralddaquila.com/2026/06/16/ai-vs-human-stewardship-why-conscious-guidance-matters-more-than-ever/",
        # Legacy exact-query record intentionally has no doorway_rationale.
    }
    expected_rationale = "AI vs. Human Stewardship examines why growing technological capability must remain guided by human wisdom, ethical judgment, oversight, agency, and clear accountability. It offers a broader foundation for examining predictive public systems and the responsibilities that must remain with people; it does not evaluate this particular government proposal."
    monkeypatch.setattr(
        main,
        "_resolve_exact_guide_gold_standard",
        lambda _query: exact_standard,
    )

    result = main._guide_finalize_visitor_payload(
        {"response": "Unapproved answer.", "recommendation": None},
        query,
    )

    assert result["response"] == exact_answer
    assert result["recommendation"] == {
        "title": exact_standard["doorway_title"],
        "url": exact_standard["doorway_url"],
        "rationale": expected_rationale,
    }
    assert result["canonical_doorway"] == result["recommendation"]
    assert result["doorway_rationale"] == expected_rationale


def test_exact_gold_standard_does_not_borrow_rationale_for_a_different_destination(monkeypatch):
    import main

    query = (
        "A government proposes a highly efficient predictive system for public services. "
        "What constitutional and human questions must precede adoption?"
    )
    exact_standard = {
        "expected_response": "Frozen answer.",
        "doorway_title": "A Different Canonical Resource",
        "doorway_url": "https://geralddaquila.com/a-different-canonical-resource/",
    }
    monkeypatch.setattr(
        main,
        "_resolve_exact_guide_gold_standard",
        lambda _query: exact_standard,
    )

    result = main._guide_finalize_visitor_payload({"response": "Provider answer."}, query)

    assert result["response"] == "Frozen answer."
    assert result["recommendation"] == {
        "title": "A Different Canonical Resource",
        "url": "https://geralddaquila.com/a-different-canonical-resource/",
    }
    assert "rationale" not in result["recommendation"]

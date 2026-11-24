import provider_exhaustion_candidate_policy as policy


def test_provider_exhaustion_policy_selects_only_the_public_commons_gold_star():
    lesson = {
        "id": policy.BENCHMARK_ID,
        "runtime_transfer": True,
    }
    selected = policy.select_provider_exhaustion_candidate(
        "When search services are unavailable, how should a guide answer a general question about civic commons without claiming official doctrine?",
        [lesson],
    )
    assert selected is not None
    assert selected["lesson"] is lesson
    assert selected["role"] == "core"


def test_provider_exhaustion_policy_rejects_missing_provider_outage_or_doctrine_boundary():
    lesson = {"id": policy.BENCHMARK_ID, "runtime_transfer": True}
    assert policy.select_provider_exhaustion_candidate(
        "How should a guide explain civic commons in general terms?",
        [lesson],
    ) is None
    assert policy.select_provider_exhaustion_candidate(
        "When search services are unavailable, how should a guide answer a general question about civic commons?",
        [lesson],
    ) is None


def test_provider_exhaustion_policy_requires_active_runtime_transfer_record():
    inactive = {"id": policy.BENCHMARK_ID, "runtime_transfer": False}
    assert policy.select_provider_exhaustion_candidate(
        "When search services are unavailable, how should a guide answer a general question about civic commons without claiming official doctrine?",
        [inactive],
    ) == []


def test_provider_exhaustion_civic_commons_meta_question_gets_a_substantive_bounded_answer():
    from deterministic_answer_recovery import compose_recovery

    query = (
        "When search services are unavailable, how should a guide answer a general question "
        "about civic commons without claiming official doctrine?"
    )
    answer = compose_recovery(query)
    normalized = answer.casefold()
    assert len([part for part in answer.split("\n\n") if part.strip()]) == 3
    for required in (
        "lack of retrieved sources",
        "stable general knowledge",
        "shared resources",
        "fair access",
        "meaningful participation",
        "archive-specific definition or doctrine",
        "authoritative text",
    ):
        assert required in normalized
    assert "start by defining the outcome" not in normalized
    assert "ai may inform that work" not in normalized
    assert "official living archive position" in normalized
    assert "geralddaquila.com" not in normalized


def test_provider_exhaustion_civic_commons_recovery_does_not_capture_unrelated_questions():
    from deterministic_answer_recovery import compose_recovery

    answer = compose_recovery(
        "How should a guide explain the opening hours of a public library?"
    )
    assert "shared resources, spaces, institutions" not in answer
    assert "official Living Archive position" not in answer


def test_existing_public_commons_gold_star_transfers_answerability_rule_and_domain_specificity():
    from gold_star_lessons import active_quality_contribution

    query = (
        "When search services are unavailable, how should a guide answer a general question "
        "about civic commons without claiming official doctrine?"
    )
    contribution = active_quality_contribution(query)
    assert contribution is not None
    assert contribution["benchmark_id"] == "general-guide-public-commons-civic-renewal-2026-11-24"
    assert contribution["authority_mode"] == "structural_guidance_only"
    discipline = contribution["discipline"].casefold()
    assert "stable general knowledge" in discipline
    assert "domain-specific explanation" in discipline
    assert "generic process framework" in discipline
    assert "institution-specific doctrine" in discipline
    assert "expected_response" not in contribution
    assert "doorway" not in contribution

    # Verify the selected discipline reaches the actual provider composition
    # contract, while the exemplar's answer content remains excluded.
    import general_guide_composition as composition

    instruction = composition._build_gold_star_quality_instruction(contribution)
    assert "domain-specific explanation" in instruction
    assert "generic process framework" in instruction
    assert "Public commons are resources" not in instruction
    assert "libraries, parks, public knowledge" not in instruction

import json
import re

import pytest

import general_guide_composition as composition
import provider_bank


@pytest.mark.parametrize(
    ("raw", "reason"),
    [
        ("{", "invalid JSON envelope"),
        ("[]", "non-object JSON envelope"),
        (json.dumps({"response": "", "response_shape": "direct"}), "empty response"),
        (json.dumps({"response": "too short", "response_shape": "direct"}), "too short"),
        (json.dumps({"response": "x" * 7001, "response_shape": "direct"}), "too long"),
    ],
)
def test_soft_provider_lane_reports_precise_bounded_rejection_reason(raw, reason):
    parse = composition._parse_factory(
        [],
        query="",
        gold_star_candidates=None,
        emit_telemetry=False,
    )
    with pytest.raises(ValueError, match=reason):
        parse(raw)


@pytest.mark.parametrize(
    ("reason", "expected"),
    [
        ("provider response failed basic visitor bounds: invalid JSON envelope", "json_or_parse"),
        ("provider response failed basic visitor bounds: non-object JSON envelope", "json_or_parse"),
        ("provider response failed basic visitor bounds: empty response", "response_shape"),
        ("provider response too short for basic visitor bounds", "response_shape"),
        ("provider response too long for basic visitor bounds", "response_shape"),
    ],
)
def test_basic_visitor_bound_failures_do_not_become_unknown_quality_failures(reason, expected):
    assert provider_bank._contract_rejection_class(reason) == expected


GOLD_STAR_CANDIDATES = [
    {
        "benchmark_id": "lesson-a",
        "reasoning_family": "evidence_discipline",
        "discipline": "Separate observation from inference.",
    }
]
GOLD_STAR_RESPONSE = (
    "Separate observed facts from inferred explanations before choosing a "
    "proportionate response to the situation."
)


def _gold_star_parse(payload):
    return composition._parse_factory(
        [],
        query="",
        gold_star_candidates=GOLD_STAR_CANDIDATES,
        emit_telemetry=False,
    )(json.dumps(payload))


def test_community_liberty_limit_prompt_requires_burden_distribution_and_participation():
    question = (
        "How should a community decide whether limits on personal liberty are justified "
        "by shared obligations and risks?"
    )
    prompt = composition._build_general_guide_system_message(question)
    for required in (
        "COMMUNITY RULES THAT LIMIT PERSONAL LIBERTY",
        "legitimate shared purpose",
        "who benefits",
        "who bears costs",
        "include affected people in shaping the rule",
        "less restrictive workable means",
        "fair burden allocation",
        "appeal and review criteria",
    ):
        assert required in prompt
    unrelated = composition._build_general_guide_system_message("What is stewardship?")
    assert "COMMUNITY RULES THAT LIMIT PERSONAL LIBERTY" not in unrelated


def test_gold_star_adjudication_prefers_specific_reasoning_family_over_broad_thematic_overlap():
    instruction = composition._build_gold_star_quality_instruction(
        {
            "candidates": [
                {
                    "benchmark_id": "broad-community-freedom",
                    "reasoning_family": "community_freedom_shared_responsibility_proportionate_decision",
                    "discipline": "Protect rights while weighing shared responsibility.",
                    "abstention_boundary": "Do not assume restrictions are justified.",
                },
                {
                    "benchmark_id": "specific-community-rule-design",
                    "reasoning_family": "community_rule_design_personal_liberty_shared_obligations",
                    "discipline": "Identify who benefits, who bears costs, and whose liberty is restricted.",
                    "abstention_boundary": "Do not infer legal authority without facts.",
                },
            ]
        }
    )
    assert "narrowest matching reasoning family" in instruction
    assert "thematic overlap is not redundancy" in instruction


@pytest.mark.parametrize(
    "adjudication",
    [None, {}, {"candidate_assessments": [], "application_evidence_spans": []}],
)
def test_provider_response_with_candidates_preserves_answer_without_valid_adjudication(adjudication):
    payload = {
        "response": GOLD_STAR_RESPONSE,
        "response_shape": "direct",
        "adaptive_adjudication": adjudication,
    }
    parsed = _gold_star_parse(payload)
    assert parsed["response"] == GOLD_STAR_RESPONSE
    import gold_star_provider_adjudication as adjudication_contract
    report = adjudication_contract.normalize_provider_adjudication(
        parsed.get("adaptive_adjudication"),
        response=parsed["response"],
        candidates=GOLD_STAR_CANDIDATES,
    )
    assert report["status"] == "not_observed"
    assert report["selected_candidate_ids"] == []
    assert report["application"] == "not_observed"


def test_provider_response_without_adjudication_field_preserves_complete_answer():
    parsed = _gold_star_parse({
        "response": GOLD_STAR_RESPONSE,
        "response_shape": "direct",
    })
    assert parsed["response"] == GOLD_STAR_RESPONSE
    assert parsed.get("adaptive_adjudication") is None
    import gold_star_provider_adjudication as adjudication_contract
    report = adjudication_contract.normalize_provider_adjudication(
        parsed.get("adaptive_adjudication"),
        response=parsed["response"],
        candidates=GOLD_STAR_CANDIDATES,
    )
    assert report["status"] == "not_observed"
    assert report["application"] == "not_observed"


def test_provider_selected_candidate_without_exact_span_is_delivered_without_application_credit():
    payload = {
        "response": GOLD_STAR_RESPONSE,
        "response_shape": "direct",
        "adaptive_adjudication": {
            "candidate_assessments": [
                {"candidate_id": "lesson-a", "decision": "select", "reason_code": None}
            ],
            "application_evidence_spans": [{"candidate_id": "lesson-a", "start": 0, "end": 0}],
        },
    }
    parsed = _gold_star_parse(payload)
    assert parsed["response"] == GOLD_STAR_RESPONSE
    import gold_star_provider_adjudication as adjudication
    report = adjudication.normalize_provider_adjudication(
        parsed["adaptive_adjudication"],
        response=parsed["response"],
        candidates=GOLD_STAR_CANDIDATES,
    )
    assert report["status"] == "provider_reported_selected"
    assert report["application_evidence_present"] is False
    assert report["application"] == "not_observed"


def test_provider_may_validly_reject_all_gold_star_candidates():
    payload = {
        "response": GOLD_STAR_RESPONSE,
        "response_shape": "direct",
        "adaptive_adjudication": {
            "candidate_assessments": [
                {"candidate_id": "lesson-a", "decision": "reject", "reason_code": "subject_mismatch"}
            ],
            "application_evidence_spans": [{"candidate_id": "lesson-a", "start": 0, "end": 0}],
        },
    }
    parsed = _gold_star_parse(payload)
    assert parsed["adaptive_adjudication"]["candidate_assessments"][0]["decision"] == "reject"


def test_provider_selected_candidate_with_exact_answer_span_is_admitted():
    span = "Separate observed facts from inferred explanations"
    payload = {
        "response": GOLD_STAR_RESPONSE,
        "response_shape": "direct",
        "adaptive_adjudication": {
            "candidate_assessments": [
                {"candidate_id": "lesson-a", "decision": "select", "reason_code": None}
            ],
            "application_evidence_spans": [
                {"candidate_id": "lesson-a", "start": GOLD_STAR_RESPONSE.index(span), "end": GOLD_STAR_RESPONSE.index(span) + len(span)}
            ],
        },
    }
    parsed = _gold_star_parse(payload)
    assert parsed["adaptive_adjudication"]["application_evidence_spans"][0]["start"] == GOLD_STAR_RESPONSE.index(span)
    assert parsed["adaptive_adjudication"]["application_evidence_spans"][0]["end"] == GOLD_STAR_RESPONSE.index(span) + len(span)


def test_provider_composition_schema_requires_adjudication_when_candidates_exist():
    schema = composition._build_provider_composition_schema(GOLD_STAR_CANDIDATES)
    assert schema is not None
    assert schema["strict"] is False
    root = schema["schema"]
    assert "adaptive_adjudication" in root["required"]
    assert "adaptive_adjudication" in root["properties"]
    adjudication = root["properties"]["adaptive_adjudication"]
    assert set(adjudication["required"]) == {
        "candidate_assessments",
        "application_evidence_spans",
    }
    assessments = adjudication["properties"]["candidate_assessments"]
    assert assessments["minItems"] == assessments["maxItems"] == 1
    assert assessments["items"]["properties"]["candidate_id"]["enum"] == ["lesson-a"]
    assert assessments["items"]["properties"]["decision"]["enum"] == ["select", "reject"]
    assert assessments["items"]["properties"]["reason_code"]["enum"][0] == ""
    spans = adjudication["properties"]["application_evidence_spans"]
    assert spans["minItems"] == spans["maxItems"] == 1
    assert spans["items"]["properties"]["start"]["type"] == "integer"
    assert spans["items"]["properties"]["end"]["type"] == "integer"
    assert spans["items"]["properties"]["start"]["minimum"] == 0
    assert spans["items"]["properties"]["end"]["minimum"] == 0


def test_provider_composition_schema_is_not_added_without_candidates():
    assert composition._build_provider_composition_schema(None) is None
    assert composition._build_provider_composition_schema([]) is None


def test_provider_composition_schema_deduplicates_candidate_ids_like_runtime_index():
    duplicate = {
        "benchmark_id": "lesson-a",
        "reasoning_family": "evidence_discipline",
        "discipline": "A second registry record with the same identity.",
    }
    schema = composition._build_provider_composition_schema(
        [GOLD_STAR_CANDIDATES[0], duplicate]
    )
    assessments = schema["schema"]["properties"]["adaptive_adjudication"]["properties"]["candidate_assessments"]
    assert assessments["minItems"] == assessments["maxItems"] == 1


def test_compose_passes_candidate_aware_schema_to_provider_bank(monkeypatch):
    candidate = {
        "benchmark_id": "lesson-a",
        "score": 0.81,
        "authority_mode": "structural_guidance_only",
        "reasoning_family": "evidence_discipline",
        "discipline": "Separate observation from inference.",
        "abstention_boundary": "Do not infer responsibility without evidence.",
    }
    contribution = {
        "benchmark_id": candidate["benchmark_id"],
        "score": candidate["score"],
        "authority_mode": "structural_guidance_only",
        "candidates": [candidate],
    }
    captured = {}
    monkeypatch.setattr(
        composition, "_gold_star_active_quality_contribution",
        lambda _question: contribution,
    )
    monkeypatch.setattr(composition, "_registered_exact_gold_standard", lambda _question: None)
    monkeypatch.setattr(composition, "_documents_from_context", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(composition, "_start_requested_gold_star_semantic_warmup", lambda: None)
    monkeypatch.setattr(composition, "_COMPOSITION_CACHE", composition.OrderedDict())

    def fake_route(**kwargs):
        captured.update(kwargs)
        payload = {
            "response": GOLD_STAR_RESPONSE,
            "doorway_title": "",
            "response_shape": "direct",
            "adaptive_adjudication": {
                "candidate_assessments": [
                    {"candidate_id": "lesson-a", "decision": "reject", "reason_code": "subject_mismatch"}
                ],
                "application_evidence_spans": [{"candidate_id": "lesson-a", "start": 0, "end": 0}],
            },
        }
        return {
            "parsed": kwargs["parse"](json.dumps(payload)),
            "provider": "test-provider",
            "model": "test-model",
        }

    monkeypatch.setattr(composition, "route_with_model_bank", fake_route)
    composition.compose(
        use_core=object(),
        query="What does observation mean in a clinical record?",
        context_data={},
    )
    assert captured["schema"]["schema"]["properties"]["adaptive_adjudication"]



def test_community_rule_instruction_explicitly_covers_each_distinct_evidence_dimension():
    instruction = composition._build_general_guide_system_message(
        "How should a community decide whether limits on personal liberty are justified by shared obligations and risks?"
    )
    for required in (
        "reasonable accommodation",
        "fair burden allocation",
        "include affected people in shaping the rule",
        "specify appeal and review criteria",
        "Treat each as distinct evidence",
        "Use prose",
    ):
        assert required in instruction



def test_visitor_idea_chunking_contract_matches_explicit_prompt_threshold():
    prompt = composition._build_general_guide_system_message("What is transparency?")
    assert "at least 650 characters" in prompt
    assert "five or more sentences" in prompt
    assert "at least two paragraphs with a blank line" in prompt

    short_single_movement = " ".join(["A clear idea is explained simply."] * 4)
    sentences = [
        "A community's first obligation is to identify the shared purpose and concrete harm that the proposed rule is intended to address, rather than assuming consensus.",
        "The next question is whether the restriction is necessary and proportionate, and whether a less restrictive workable option could achieve the same legitimate end.",
        "Decision-makers should identify who benefits, who bears the costs, and whose freedom is limited, including people whose circumstances differ from the majority.",
        "Affected people should have meaningful influence over design, with reasonable accommodation, transparent reasons, and safeguards against arbitrary enforcement.",
        "Finally, anyone affected needs a practical route to challenge application, while review criteria should show whether the rule continues to serve its stated purpose.",
    ]
    long_single_block = " ".join(sentences)
    long_two_paragraphs = " ".join(sentences[:3]) + "\n\n" + " ".join(sentences[3:])
    assert not composition._requires_visitor_idea_chunking(short_single_movement)
    assert composition._requires_visitor_idea_chunking(long_single_block)
    assert not composition._requires_visitor_idea_chunking(long_two_paragraphs)



def test_long_single_block_is_reflowed_at_sentence_boundary_without_content_changes():
    sentences = [
        "A community's first obligation is to identify the shared purpose and concrete harm that the proposed rule is intended to address, rather than assuming consensus.",
        "The next question is whether the restriction is necessary and proportionate, and whether a less restrictive workable option could achieve the same legitimate end.",
        "Decision-makers should identify who benefits, who bears the costs, and whose freedom is limited, including people whose circumstances differ from the majority.",
        "The relationship can also work in the other direction: affected people should have meaningful influence over design, with reasonable accommodation and safeguards against arbitrary enforcement.",
        "Finally, anyone affected needs a practical route to challenge application, while review criteria should show whether the rule continues to serve its stated purpose.",
    ]
    single_block = " ".join(sentences)
    assert composition._requires_visitor_idea_chunking(single_block)

    reflowed = composition._reflow_visitor_idea_chunking(single_block)

    assert "\n\n" in reflowed
    assert not composition._requires_visitor_idea_chunking(reflowed)
    assert re.sub(r"\s+", " ", reflowed) == re.sub(r"\s+", " ", single_block)
    assert reflowed.index("The relationship can also work") > reflowed.index("\n\n")


def test_short_and_already_chunked_responses_are_not_reflowed():
    short = "A short answer can remain in one paragraph."
    chunked = "First idea has enough detail to stand alone.\n\nSecond idea adds a separate implication."
    assert composition._reflow_visitor_idea_chunking(short) == short
    assert composition._reflow_visitor_idea_chunking(chunked) == chunked


def test_strict_parser_applies_content_preserving_long_answer_reflow():
    sentences = [
        "A community's first obligation is to identify the shared purpose and concrete harm that the proposed rule is intended to address, rather than assuming consensus.",
        "The next question is whether the restriction is necessary and proportionate, and whether a less restrictive workable option could achieve the same legitimate end.",
        "Decision-makers should identify who benefits, who bears the costs, and whose freedom is limited, including people whose circumstances differ from the majority.",
        "The relationship can also work in the other direction: affected people should have meaningful influence over design, with reasonable accommodation and safeguards against arbitrary enforcement.",
        "Finally, anyone affected needs a practical route to challenge application, while review criteria should show whether the rule continues to serve its stated purpose.",
    ]
    parse = composition._parse_factory(
        [],
        query="",
        gold_star_candidates=None,
        emit_telemetry=False,
    )
    parsed = parse(json.dumps({"response": " ".join(sentences)}))
    assert "\n\n" in parsed["response"]
    assert re.sub(r"\s+", " ", parsed["response"]) == re.sub(r"\s+", " ", " ".join(sentences))


def test_attributed_source_excerpt_blocks_are_removed_without_treating_apostrophes_as_quotes():
    excerpt = (
        '"Through the lenses of the Akashic Records, this piece also reveals the deeper '
        "evolutionary context of humanity's collective spiritual test, as it navigates "
        'the thinning veil between illusion and illumination." '
        '(🔥 Spiritual Bypass Recovery)'
    )
    assert composition._sanitize_candidate(excerpt) == ""


def test_multiple_attributed_excerpt_blocks_cannot_masquerade_as_a_visitor_answer():
    excerpts = (
        '"This Guide is Not This guide is not a critique of spirituality or spiritual '
        'practice but a trauma-processing manual." (🔥 Spiritual Bypass Recovery)\n\n'
        '"This dissertation investigates the phenomenon of spiritual misinformation '
        'in the AI era from a multidisciplinary perspective." '
        '(Discernment vs. Distraction: Surviving Spiritual Misinformation in the AI Age)'
    )
    assert composition._sanitize_candidate(excerpts) == ""


def test_integrated_explanation_with_a_cited_quote_is_not_discarded():
    response = (
        "Humility is an honest recognition of one's limits and continuing capacity to learn. "
        'A source describes "the willingness to be corrected" (A Grounded Practice), '
        "but spiritual maturity is shown by how that recognition changes conduct over time."
    )
    assert composition._sanitize_candidate(response) == response


def test_final_visitor_boundary_fails_closed_when_only_source_excerpts_remain():
    excerpt = (
        '"Through the lenses of the Akashic Records, this piece reveals humanity '
        'collective spiritual test and the thinning veil between illusion and illumination." '
        '(🔥 Spiritual Bypass Recovery)'
    )
    with pytest.raises(ValueError, match="attributed source excerpts"):
        composition.enforce_response_contracts(
            "What is the relationship between humility and spiritual maturity?",
            excerpt,
        )


def test_quoted_explanation_with_ordinary_parenthetical_is_preserved():
    response = (
        '"A person can acknowledge uncertainty while remaining open to correction." '
        '(for example, in a difficult conversation)'
    )
    assert composition._sanitize_candidate(response) == response



def test_sanitizer_removes_only_orphaned_terminal_single_quote():
    response = "The two ideas reinforce one another in practice.'"
    assert composition._sanitize_candidate(response) == (
        "The two ideas reinforce one another in practice."
    )


def test_sanitizer_preserves_contractions_and_terminal_possessives():
    response = "It's a visitor's choice, and the users' concerns still matter."
    assert composition._sanitize_candidate(response) == response
    possessive_at_end = "The decision remains the users'"
    assert composition._sanitize_candidate(possessive_at_end) == possessive_at_end


def test_sanitizer_preserves_a_paired_single_quoted_span():
    response = "The phrase 'stay grounded.' captures the point."
    assert composition._sanitize_candidate(response) == response

def test_sanitizer_removes_orphan_after_an_earlier_paired_single_quoted_span():
    response = "The phrase 'stay grounded.' captures the point. An orphan remains.'"
    assert composition._sanitize_candidate(response) == (
        "The phrase 'stay grounded.' captures the point. An orphan remains."
    )

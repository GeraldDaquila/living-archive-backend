import json

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
    long_single_block = " ".join(
        [
            "A distinct idea has its own purpose and consequence.",
            "A second idea adds another condition and implication.",
            "A third idea explains a separate mechanism and trade-off.",
            "A fourth idea describes another safeguard and responsibility.",
            "A fifth idea states the resulting limit and review path.",
        ]
    )
    long_two_paragraphs = (
        "A distinct idea has its own purpose and consequence. "
        "A second idea adds another condition and implication. "
        "A third idea explains a separate mechanism and trade-off.\n\n"
        "A fourth idea describes another safeguard and responsibility. "
        "A fifth idea states the resulting limit and review path."
    )
    assert not composition._requires_visitor_idea_chunking(short_single_movement)
    assert composition._requires_visitor_idea_chunking(long_single_block)
    assert not composition._requires_visitor_idea_chunking(long_two_paragraphs)

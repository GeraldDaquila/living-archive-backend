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


@pytest.mark.parametrize(
    "adjudication",
    [None, {}, {"candidate_assessments": [], "application_evidence_spans": []}],
)
def test_provider_response_with_candidates_rejects_missing_or_incomplete_adjudication(adjudication):
    payload = {
        "response": GOLD_STAR_RESPONSE,
        "response_shape": "direct",
        "adaptive_adjudication": adjudication,
    }
    with pytest.raises(ValueError, match="Gold Star adjudication report is missing or incomplete"):
        _gold_star_parse(payload)


def test_provider_selected_candidate_without_exact_span_is_delivered_without_application_credit():
    payload = {
        "response": GOLD_STAR_RESPONSE,
        "response_shape": "direct",
        "adaptive_adjudication": {
            "candidate_assessments": [
                {"candidate_id": "lesson-a", "decision": "select", "reason_code": None}
            ],
            "application_evidence_spans": [],
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
            "application_evidence_spans": [],
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
                {"candidate_id": "lesson-a", "span": span}
            ],
        },
    }
    parsed = _gold_star_parse(payload)
    assert parsed["adaptive_adjudication"]["application_evidence_spans"][0]["span"] == span


def test_provider_composition_schema_requires_candidate_adjudication_object():
    schema = composition._build_provider_composition_schema(GOLD_STAR_CANDIDATES)
    assert schema is not None
    assert schema["strict"] is False
    root = schema["schema"]
    assert "adaptive_adjudication" in root["required"]
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
    assert spans["items"]["properties"]["span"]["minLength"] == 12
    assert spans["items"]["properties"]["span"]["maxLength"] == 240


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
                "application_evidence_spans": [],
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

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

from hub_contracts import (
    HUB_CONTRACT_VERSION,
    HubContractError,
    build_hub_request,
    validate_hub_contribution,
)


def test_build_hub_request_preserves_hub_context():
    request = build_hub_request(
        request_id="req-1",
        guide_version="v1",
        original_question="What is changing?",
        recognized_territory="relationship",
        processing_purpose="orientation",
        guide_context={"history": "prior turns"},
        safety_state="green",
    )
    assert request.request_id == "req-1"
    assert request.original_question == "What is changing?"
    assert request.guide_context["history"] == "prior turns"
    assert request.safety_state == "green"


def test_hub_contribution_requires_matching_identity():
    contribution = {
        "contract_version": HUB_CONTRACT_VERSION,
        "request_id": "req-1",
        "specialist_id": "relationship",
        "status": "CONTRIBUTION",
        "payload": {"clarity": "relational pattern"},
        "canonical_candidates": [],
    }
    result = validate_hub_contribution(
        contribution,
        expected_request_id="req-1",
        expected_specialist_id="relationship",
    )
    assert result.status == "CONTRIBUTION"
    assert result.payload["clarity"] == "relational pattern"


def test_hub_contribution_rejects_identity_mismatch():
    contribution = {
        "contract_version": HUB_CONTRACT_VERSION,
        "request_id": "wrong",
        "specialist_id": "relationship",
        "status": "CONTRIBUTION",
        "payload": {},
    }
    try:
        validate_hub_contribution(
            contribution,
            expected_request_id="req-1",
            expected_specialist_id="relationship",
        )
    except HubContractError as exc:
        assert "request_id mismatch" in str(exc)
    else:
        raise AssertionError("Expected HubContractError")


def test_hub_request_rejects_empty_question():
    try:
        build_hub_request(
            request_id="req-1",
            guide_version="v1",
            original_question="",
            recognized_territory="relationship",
            processing_purpose="orientation",
        )
    except HubContractError as exc:
        assert "original_question" in str(exc)
    else:
        raise AssertionError("Expected HubContractError")

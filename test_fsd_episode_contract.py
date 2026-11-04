import pytest

from fsd_episode_contract import (
    CONTRACT_VERSION,
    ENUMS,
    FSDEpisodeContractError,
    interpret_episode,
    validate_episode_payload,
)


def episode(**overrides):
    value = {
        "contract_version": CONTRACT_VERSION,
        "scale": "institution",
        "prior_understanding": "clear",
        "experience_type": "observed_outcome",
        "consequence_significance": "material_outcome_or_decision",
        "understanding_after": "revised",
        "reconsideration_basis": "directly_changed_explanation",
        "subsequent_response": "decision_or_action_changed",
        "understanding_action_link": "directly_informed",
        "response_available": "yes",
        "non_change_reason": "not_applicable",
    }
    value.update(overrides)
    return value


def test_valid_episode_is_normalized_and_has_no_client_scores():
    result = validate_episode_payload(episode(prior_understanding_detail="Prior model", experience_detail="Unexpected result"))
    assert result["contract_version"] == "fsd-episode-v1"
    assert result["prior_understanding_detail"] == "Prior model"
    assert "score" not in result and "diagnosis" not in result


def test_all_canonical_scales_are_supported():
    for scale in ("self", "relationships", "community", "institution", "civilization"):
        assert validate_episode_payload(episode(scale=scale))["scale"] == scale


def test_rejects_unknown_scale_and_legacy_contract():
    with pytest.raises(FSDEpisodeContractError):
        validate_episode_payload(episode(scale="organization"))
    with pytest.raises(FSDEpisodeContractError):
        validate_episode_payload(episode(contract_version="fsd-two-quantum-v1"))


@pytest.mark.parametrize("field", list(ENUMS))
def test_every_enum_field_is_required_and_strict(field):
    value = episode()
    value.pop(field)
    with pytest.raises(FSDEpisodeContractError):
        validate_episode_payload(value)
    value = episode(**{field: "made_up"})
    with pytest.raises(FSDEpisodeContractError):
        validate_episode_payload(value)


def test_rejects_extra_client_authority_fields():
    with pytest.raises(FSDEpisodeContractError):
        validate_episode_payload(episode(scores={"Q001": 4}))
    with pytest.raises(FSDEpisodeContractError):
        validate_episode_payload(episode(provider="browser-choice"))


@pytest.mark.parametrize(("field", "limit"), [("prior_understanding_detail", 240), ("experience_detail", 360)])
def test_optional_text_is_bounded(field, limit):
    assert validate_episode_payload(episode(**{field: "x" * limit}))[field] == "x" * limit
    with pytest.raises(FSDEpisodeContractError):
        validate_episode_payload(episode(**{field: "x" * (limit + 1)}))


def test_rejects_non_string_optional_text():
    with pytest.raises(FSDEpisodeContractError):
        validate_episode_payload(episode(experience_detail=["not", "text"]))


def test_both_transitions_reported_only_for_a_linked_episode():
    result = interpret_episode(episode())
    assert result["overall"] == "both_transitions_reported"
    assert result["inference_boundary"] == "one_episode_only_no_stable_system_capacity_claim"


def test_examined_and_retained_can_support_correspondence_without_change():
    result = interpret_episode(episode(
        understanding_after="examined_and_retained",
        reconsideration_basis="considered_with_competing_evidence",
        subsequent_response="no_response",
        understanding_action_link="no_response_or_unknown",
        response_available="yes",
        non_change_reason="not_warranted",
    ))
    assert result["correspondence"] == "reported"
    assert result["correctability"] == "no_change_warranted"


def test_no_response_when_meaningful_response_unavailable_is_not_capacity_failure():
    result = interpret_episode(episode(
        subsequent_response="no_response",
        understanding_action_link="no_response_or_unknown",
        response_available="no",
        non_change_reason="authority_or_resources_unavailable",
    ))
    assert result["correctability"] == "not_assessable_response_unavailable"


def test_unknown_understanding_produces_insufficient_evidence():
    result = interpret_episode(episode(
        understanding_after="unknown",
        reconsideration_basis="unknown",
        subsequent_response="too_early_or_unknown",
        understanding_action_link="no_response_or_unknown",
        response_available="unknown",
        non_change_reason="insufficient_time",
    ))
    assert result["overall"] == "insufficient_evidence"


def test_blocked_response_is_reported_as_episode_constraint_not_incapacity():
    result = interpret_episode(episode(
        subsequent_response="attempted_but_blocked",
        understanding_action_link="partly_informed",
        response_available="partly",
        non_change_reason="authority_or_resources_unavailable",
    ))
    assert result["correctability"] == "constraint_or_delay_reported"


def test_rejects_impossible_response_link_combinations():
    with pytest.raises(FSDEpisodeContractError):
        validate_episode_payload(episode(
            subsequent_response="no_response",
            understanding_action_link="directly_informed",
            non_change_reason="not_warranted",
        ))
    with pytest.raises(FSDEpisodeContractError):
        validate_episode_payload(episode(
            subsequent_response="decision_or_action_changed",
            understanding_action_link="no_response_or_unknown",
        ))


def test_non_change_reason_is_required_when_response_absent_and_not_applicable_when_response_occurs():
    with pytest.raises(FSDEpisodeContractError):
        validate_episode_payload(episode(non_change_reason="not_applicable", subsequent_response="no_response",
                                          understanding_action_link="no_response_or_unknown"))
    with pytest.raises(FSDEpisodeContractError):
        validate_episode_payload(episode(non_change_reason="not_warranted"))


def test_rejects_action_claim_when_no_meaningful_response_was_available():
    with pytest.raises(FSDEpisodeContractError):
        validate_episode_payload(episode(
            subsequent_response="decision_or_action_changed",
            response_available="no",
            non_change_reason="not_applicable",
        ))


@pytest.mark.parametrize("field,value", [
    ("experience_type", "other_unclear"),
    ("consequence_significance", "limited_or_ambiguous"),
])
def test_ambiguous_or_nonconsequential_experience_produces_insufficient_evidence(field, value):
    result = interpret_episode(episode(**{field: value}))
    assert result["correspondence"] == "insufficient_evidence"
    assert result["overall"] == "insufficient_evidence"

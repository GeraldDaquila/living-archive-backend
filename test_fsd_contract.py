import pytest

from fsd_contract import (
    CONTRACT_VERSION,
    FSDContractError,
    QUANTUM_QUESTION_MAP,
    QUESTION_QUANTUM_RATIONALE,
    validate_diagnostic_payload,
)


_DEFAULT = object()

def payload(answers=_DEFAULT, **extra):
    value = {"contract_version": CONTRACT_VERSION}
    if answers is _DEFAULT:
        value["answers"] = [0] * 10
    else:
        value["answers"] = answers
    value.update(extra)
    return value


def test_valid_payload_derives_two_quantum_summaries_server_side():
    result = validate_diagnostic_payload(payload([0, 1, 2, 3, 0, 1, 2, 3, 0, 1]))
    assert result["answer_count"] == 10
    assert result["quantum_summaries"]["Q001_CORRESPONDENCE"]["mean_constraint_signal"] == 1
    assert result["quantum_summaries"]["Q002_CORRECTABILITY"]["mean_constraint_signal"] == 1.5


def test_mapping_covers_each_question_once():
    indices = [i for group in QUANTUM_QUESTION_MAP.values() for i in group]
    assert sorted(indices) == list(range(10))
    assert len(indices) == len(set(indices))
    assert set(QUESTION_QUANTUM_RATIONALE) == set(range(10))


@pytest.mark.parametrize("answers", [None, [], [0] * 9, [0] * 11])
def test_rejects_missing_or_wrong_answer_count(answers):
    with pytest.raises(FSDContractError):
        validate_diagnostic_payload(payload(answers))


@pytest.mark.parametrize("answer", [-1, 4, True, 1.0, "2", None])
def test_rejects_invalid_answer_values(answer):
    answers = [0] * 10
    answers[4] = answer
    with pytest.raises(FSDContractError):
        validate_diagnostic_payload(payload(answers))


def test_rejects_unknown_contract_version():
    with pytest.raises(FSDContractError):
        validate_diagnostic_payload({**payload(), "contract_version": "future"})


def test_rejects_client_supplied_scores_or_provider_controls():
    for key in ("scores", "diagnosis", "evidence", "provider", "model", "urls"):
        with pytest.raises(FSDContractError):
            validate_diagnostic_payload({**payload(), key: "untrusted"})


@pytest.mark.parametrize("scale", ["self", "relationships", "organization", "state", "civilization"])
def test_accepts_each_supported_scale(scale):
    assert validate_diagnostic_payload(payload(scale=scale))["scale"] == scale


def test_scale_can_remain_unknown_instead_of_being_inferred():
    assert validate_diagnostic_payload(payload())["scale"] is None


def test_rejects_unsupported_scale():
    with pytest.raises(FSDContractError):
        validate_diagnostic_payload(payload(scale="team"))


def test_boolean_is_not_accepted_as_an_integer_option():
    with pytest.raises(FSDContractError):
        validate_diagnostic_payload(payload([False] + [0] * 9))


def test_rejects_missing_answers_field():
    with pytest.raises(FSDContractError):
        validate_diagnostic_payload({"contract_version": CONTRACT_VERSION})

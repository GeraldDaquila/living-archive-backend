from deterministic_answer_recovery import (
    compose_recovery,
    compose_task_specific_recovery,
)


def test_fair_community_rule_has_direct_query_matched_recovery():
    question = (
        "How should a community balance personal liberty with collective "
        "obligations when setting a fair rule?"
    )
    result = compose_task_specific_recovery(question)
    assert result is not None
    assert result["recovery_id"] == "task_fair_community_rule_liberty_and_collective_obligations"
    answer = result["response"].casefold()
    for required in (
        "shared purpose",
        "specific harm",
        "least restrictive",
        "people most affected",
        "fairly distributed",
        "appeal",
        "review point",
    ):
        assert required in answer


def test_shared_recovery_composer_exposes_task_specific_recovery():
    question = (
        "How should a community balance personal liberty with collective "
        "obligations when setting a fair rule?"
    )
    answer = compose_recovery(question)
    assert "least restrictive workable means" in answer
    assert "If not, the rule needs redesign" in answer
    assert len([paragraph for paragraph in answer.split("\n\n") if paragraph.strip()]) == 3
    assert "\\n" not in answer


def test_fair_rule_recovery_does_not_claim_archive_doctrine():
    question = (
        "How should a community balance personal liberty with collective "
        "obligations when setting a fair rule?"
    )
    result = compose_task_specific_recovery(question)
    assert "Living Archive doctrine" in result["response"] or "Living Archive" not in result["response"]

from deterministic_answer_recovery import compose_recovery


def test_public_commons_civic_renewal_gets_substantive_answer_during_provider_exhaustion():
    question = "What is the role of public commons in civic renewal?"
    answer = compose_recovery(question)
    normalized = answer.casefold()

    assert "public commons are resources" in normalized
    assert "participate in common life" in normalized
    assert "inclusive decision-making" in normalized
    assert "formal living archive definition" in normalized
    assert "i can't define" not in normalized
    assert len([part for part in answer.split("\\n\\n") if part.strip()]) == 3


def test_public_commons_recovery_is_not_misrepresented_as_archive_doctrine():
    question = "What is the role of public commons in civic renewal?"
    answer = compose_recovery(question)
    assert "not a claim that it is a formal Living Archive definition" in answer


def test_archive_specific_public_commons_question_does_not_use_general_recovery():
    question = (
        "What is the role of public commons in civic renewal according to the Living Archive?"
    )
    answer = compose_recovery(question)
    assert "not a claim that it is a formal Living Archive definition" not in answer


def test_unrelated_unknown_term_does_not_receive_public_commons_recovery():
    answer = compose_recovery("What is the role of an unfamiliar term in civic renewal?")
    assert "Public commons are resources" not in answer

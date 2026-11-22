import re

from deterministic_answer_recovery import (
    _institutional_legitimacy_recovery,
    _is_institutional_legitimacy_question,
    compose_recovery,
)


def test_institutional_legitimacy_question_gets_substantive_provider_independent_answer():
    question = "What makes an institution legitimate?"
    answer = compose_recovery(question)

    assert _is_institutional_legitimacy_question(question)
    assert len([part for part in answer.split("\\n\\n") if part.strip()]) == 3
    for required in (
        "authority",
        "people affected",
        "accountability",
        "participation",
        "legality alone",
        "not a statement of the Living Archive's formal doctrine",
    ):
        assert required.casefold() in answer.casefold()
    assert "I couldn't verify" not in answer
    assert "I did not identify" not in answer


def test_institutional_legitimacy_variants_are_recognized_without_overmatching():
    assert _is_institutional_legitimacy_question("What gives institutions legitimacy?")
    assert _is_institutional_legitimacy_question("When is an institution legitimate?")
    assert _is_institutional_legitimacy_question("Explain institutional legitimacy.")
    assert not _is_institutional_legitimacy_question(
        "What is the Living Archive's official definition of institutional legitimacy?"
    )
    assert not _is_institutional_legitimacy_question(
        "Can you give me a constitutional law opinion about this institution?"
    )


def test_institutional_legitimacy_recovery_does_not_claim_archive_authority():
    answer = _institutional_legitimacy_recovery()
    assert "general conceptual explanation" in answer
    assert "formal doctrine" in answer
    assert not re.search(r"\\bthe Living Archive teaches that\\b", answer, re.I)

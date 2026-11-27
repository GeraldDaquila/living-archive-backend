from gold_star_semantic_contract import classify_question, evaluate_semantic_contract
from gold_star_response_floor import apply_response_floor_boundary


QUERY = "What is the relationship between humility and spiritual maturity?"


def test_relationship_question_is_classified_as_its_own_task_family():
    assert classify_question(QUERY)["type"] == "conceptual_relationship"


def test_retrieval_excerpt_dump_is_rejected_when_it_never_answers_the_relationship():
    answer = (
        '"Through the lens of the Akashic Records, this piece reveals a deeper context." '
        '(Discernment vs. Distraction: Surviving Spiritual Misinformation in the AI Age) '
        '"This Guide is not a critique of spirituality." (Spiritual Bypass Recovery) '
        '"This dissertation investigates spiritual misinformation." '
        '(Discernment vs. Distraction: Surviving Spiritual Misinformation in the AI Age)'
    )
    result = evaluate_semantic_contract(QUERY, {"ok": True, "response": answer})
    assert result["status"] == "fail"
    assert set(result["hard_failures"]) == {
        "relationship_subjects_covered",
        "connecting_mechanism_explained",
        "relationship_direction_or_boundary",
    }


def test_complete_relationship_synthesis_passes_bounded_contract():
    answer = (
        "Humility is the willingness to recognize the limits of one's understanding, "
        "while spiritual maturity is the capacity to live with discernment, compassion, "
        "and responsibility. Humility supports spiritual maturity because it keeps a "
        "person open to correction and learning. In turn, spiritual maturity deepens "
        "humility by reducing the need to claim superiority or certainty. This relationship "
        "is not automatic: humility must be joined to honest reflection and action."
    )
    result = evaluate_semantic_contract(QUERY, {"ok": True, "response": answer})
    assert result["status"] == "review_required"
    assert result["hard_failures"] == []


def test_outer_response_floor_withholds_relationship_nonanswer():
    answer = (
        '"Through the lens of the Akashic Records, this piece reveals a deeper context." '
        '(Discernment vs. Distraction: Surviving Spiritual Misinformation in the AI Age) '
        '"This Guide is not a critique of spirituality." (Spiritual Bypass Recovery)'
    )
    payload, status = apply_response_floor_boundary(
        QUERY, {"ok": True, "query": QUERY, "response": answer}, 200
    )
    assert status == 503
    assert payload["ok"] is False
    assert payload["gold_star_v2_quality_floor"]["reason"] == "supported_semantic_contract_failed"


def test_unrelated_mechanism_word_cannot_substitute_for_a_conceptual_link():
    answer = (
        "Humility is an awareness of one's limits. Spiritual maturity is a developing "
        "capacity for discernment and compassion. A healthy community supports learning "
        "and encourages accountability."
    )
    result = evaluate_semantic_contract(QUERY, {"ok": True, "response": answer})
    assert result["status"] == "fail"
    assert "connecting_mechanism_explained" in result["hard_failures"]

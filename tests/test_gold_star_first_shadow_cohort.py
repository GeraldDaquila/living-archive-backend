import gold_star_lessons as lessons

COHORT = [
    ("How are complexity and uncertainty different, and how do they interact?",
     "general-guide-complexity-and-uncertainty-gold-standard-2026-10-26"),
    ("How can an organization act wisely when knowledge is scattered across different people?",
     "general-guide-fragmented-knowledge-wise-action-gold-standard-2026-10-26"),
    ("How should I decide what information is reliable enough to act on when credible sources disagree?",
     "general-guide-conflicting-information-discernment-gold-star-2026-11-07"),
]

def test_first_shadow_cohort_is_explicitly_transferable():
    lessons._LESSONS = lessons._load_lessons()
    for query, expected in COHORT:
        result = lessons.select_lesson(query)
        assert result is not None
        assert result["benchmark_id"] == expected

def test_nearby_nonqualifying_question_abstains():
    lessons._LESSONS = lessons._load_lessons()
    assert lessons.select_lesson("How can I organize my daily tasks more efficiently?") is None

"""Held-out paraphrase and hard-distractor evaluation for shadow relevance."""
import json
from pathlib import Path

from guide_fuzzy_relevance import score_resource_fit


FIXTURE = Path(__file__).parent / "fixtures" / "guide_fuzzy_relevance_heldout_paraphrases.json"


def _cases():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]


def test_heldout_paraphrases_rank_direct_resource_above_hard_distractor():
    failures = []
    for case in _cases():
        direct = score_resource_fit(case["query"], case["direct"])["overall_shadow_score"]
        distractor = score_resource_fit(case["query"], case["hard_distractor"])["overall_shadow_score"]
        if direct <= distractor:
            failures.append({"case": case["id"], "direct": direct, "distractor": distractor})
    assert not failures, f"Held-out paraphrase ranking failures: {failures}"


def test_heldout_fixture_has_distinct_paraphrase_cases_and_hard_distractors():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert fixture["status"] == "ADDITIVE_HELDOUT_EVALUATION"
    assert len(fixture["cases"]) == 4
    assert all(case["direct"]["title"] != case["hard_distractor"]["title"] for case in fixture["cases"])


def test_heldout_scoring_is_bounded_and_does_not_mutate_candidates():
    for case in _cases():
        direct = dict(case["direct"])
        distractor = dict(case["hard_distractor"])
        direct_before, distractor_before = dict(direct), dict(distractor)
        for candidate in (direct, distractor):
            score = score_resource_fit(case["query"], candidate)["overall_shadow_score"]
            assert 0.0 <= score <= 1.0
        assert direct == direct_before
        assert distractor == distractor_before

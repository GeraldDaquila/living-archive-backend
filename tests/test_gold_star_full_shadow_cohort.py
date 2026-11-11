import json
from pathlib import Path
import gold_star_lessons

def test_qualitative_review_covers_every_current_approved_gold_star():
    registry=json.loads(Path("docs/qa/gold_standard_registry.json").read_text())
    approved={r["benchmark_id"] for r in registry["records"] if r["status"]=="USER_APPROVED_GOLD_STANDARD"}
    review=json.loads(Path("docs/qa/gold_star_qualitative_transfer_review.json").read_text())
    reviewed={e["benchmark_id"] for e in review["entries"]}
    assert approved == reviewed


def test_all_reviewed_shadow_candidates_are_shadow_eligible():
    review=json.loads(Path("docs/qa/gold_star_qualitative_transfer_review.json").read_text())
    expected={e["benchmark_id"] for e in review["entries"] if e["activation"]=="shadow_candidate"}
    loaded={x["id"] for x in gold_star_lessons._LESSONS if x["runtime_transfer"]}
    assert expected <= loaded

def test_cross_question_selection_remains_abstention_capable():
    assert gold_star_lessons.select_lesson("What colour was my childhood bicycle?") is None

import json
from pathlib import Path
def test_historical_harvest_does_not_treat_missing_responses_as_answer_evidence():
    harvest=json.loads(Path("docs/qa/gold_star_historical_best_practice_harvest.json").read_text())
    assert harvest["provenance_limited_records"]["count"] >= 1
    assert all(r["harvest"] for r in harvest["records"])

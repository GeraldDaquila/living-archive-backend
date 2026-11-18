import json
from pathlib import Path

from scripts.gold_star_paired_offline_evaluation import evaluate_dataset


def test_heldout_fixture_template_keeps_uncaptured_outputs_explicit():
    root = Path(__file__).resolve().parents[1]
    dataset = json.loads((root / "docs/qa/gold_star_paired_fixture_template.json").read_text(encoding="utf-8"))
    assert len(dataset["cases"]) == 7
    assert all(case["llm"] is None and case["deterministic"] is None for case in dataset["cases"])
    report = evaluate_dataset(dataset)
    assert report["paired_cases"] == 0
    assert report["coverage"]["llm"]["not_applicable"] == 7
    assert report["coverage"]["deterministic"]["not_applicable"] == 7
    assert report["semantic_certification"] is False

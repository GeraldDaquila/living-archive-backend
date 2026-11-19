import json
from pathlib import Path

from scripts.gold_star_paired_offline_evaluation import evaluate_dataset


def test_heldout_fixture_preserves_real_deterministic_captures_and_unverified_llm_absence():
    root = Path(__file__).resolve().parents[1]
    dataset = json.loads(
        (root / "docs/qa/gold_star_paired_fixture_template.json").read_text(encoding="utf-8")
    )
    assert len(dataset["cases"]) == 7
    assert dataset["source_code_commit"] == "93c2d3a31405ec8b193e8d7a986ed764415ef8d3"
    assert all(case["llm"] is None and case["deterministic"] is not None for case in dataset["cases"])
    assert all(case["fixture_status"] == "deterministic_captured_llm_unverified" for case in dataset["cases"])
    for case in dataset["cases"]:
        assert case["deterministic"]["capture"]["runtime_identity"]["deployment_commit_sha"] == dataset["source_code_commit"]

    report = evaluate_dataset(dataset)
    assert report["paired_cases"] == 0
    assert report["coverage"]["llm"]["not_applicable"] == 7
    assert report["coverage"]["deterministic"]["applicable"] == 7
    assert report["coverage"]["deterministic"]["not_applicable"] == 0
    assert report["semantic_certification"] is False

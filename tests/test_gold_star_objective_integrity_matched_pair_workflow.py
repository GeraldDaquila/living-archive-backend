from pathlib import Path


def test_gemini_paired_pilot_is_provider_pinned_and_provider_isolated():
    workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/objective-integrity-matched-pair.yml").read_text(encoding="utf-8")
    assert 'USE_GUIDE_EVALUATION_PROVIDER_ORDER: "gemini"' in workflow
    assert "GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}" in workflow
    assert "GROQ_API_KEY" not in workflow
    assert "--provider gemini" in workflow
    assert "--model gemini-3.8-flash" in workflow
    assert "objective_integrity_matched_pair_cases_gemini.json" in workflow


def test_provider_capture_only_runs_on_dedicated_qa_push_or_explicit_main_dispatch():
    workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/objective-integrity-matched-pair.yml").read_text(encoding="utf-8")
    assert "concurrency:" in workflow
    assert "cancel-in-progress: true" in workflow
    assert "github.event_name == 'push'" in workflow
    assert "github.event_name == 'workflow_dispatch'" in workflow
    assert "github.ref == 'refs/heads/main'" in workflow
    assert "inputs.run_provider_capture == true" in workflow
    assert "github.event_name == 'pull_request' &&" not in workflow


def test_adaptation_evaluation_ci_is_part_of_pilot_contract():
    workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/objective-integrity-matched-pair.yml").read_text(encoding="utf-8")
    assert "tests/test_gold_star_adaptation_evaluation.py" in workflow

from pathlib import Path


def test_groq_qwen27b_paired_pilot_is_provider_pinned_and_provider_isolated():
    workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/objective-integrity-matched-pair.yml").read_text(encoding="utf-8")
    assert 'USE_LLM_PROVIDER_ORDER: "groq"' in workflow
    assert "GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}" in workflow
    assert "GROQ_API_KEY" in workflow
    assert "GEMINI_API_KEY" not in workflow
    assert "CLOUDFLARE_API_TOKEN" not in workflow
    assert "CLOUDFLARE_ACCOUNT_ID" not in workflow
    assert "--provider groq" in workflow
    assert "--model qwen/qwen3.8-27b" in workflow
    assert "objective_integrity_matched_pair_cases_groq_20b.json" in workflow


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

from pathlib import Path


def test_gemini_paired_pilot_is_provider_pinned_and_provider_isolated():
    workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/objective-integrity-matched-pair.yml").read_text(encoding="utf-8")
    assert 'USE_GUIDE_EVALUATION_PROVIDER_ORDER: "workers_ai"' in workflow
    assert "CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}" in workflow
    assert "GROQ_API_KEY" not in workflow
    assert "GEMINI_API_KEY" not in workflow
    assert "CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}" in workflow
    assert "USE_WORKERS_AI_MODELS: \"@cf/zai-org/glm-4.7-flash\"" in workflow
    assert "--provider workers_ai" in workflow
    assert "--model @cf/zai-org/glm-4.7-flash" in workflow
    assert "objective_integrity_matched_pair_cases_workers_ai.json" in workflow


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

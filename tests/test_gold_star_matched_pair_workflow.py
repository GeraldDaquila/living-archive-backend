from pathlib import Path


def _workflow_text():
    return (
        Path(__file__).resolve().parents[1]
        / ".github/workflows/gold-star-matched-pair-candidate.yml"
    ).read_text(encoding="utf-8")


def test_harness_contract_runs_on_pull_requests_without_provider_calls():
    workflow = _workflow_text()
    assert "matched-pair-contract:" in workflow
    assert "matched-pair-local:" in workflow
    assert "needs: matched-pair-contract" in workflow
    assert "Run matched-pair harness contract tests" in workflow
    assert "Run same-provider, same-model control/treatment captures" in workflow
    assert "pull_request:" in workflow
    assert "workflow_dispatch:" in workflow
    assert "default: false" in workflow


def test_provider_capture_requires_explicit_manual_opt_in_from_main():
    workflow = _workflow_text()
    assert "run_provider_capture:" in workflow
    assert "type: boolean" in workflow
    assert "github.event_name == 'workflow_dispatch'" in workflow
    assert "github.ref == 'refs/heads/main'" in workflow
    assert "inputs.run_provider_capture == true" in workflow
    assert "github.event_name == 'pull_request'" not in workflow
    assert "qa/gold-star-matched-pair-main-1969" not in workflow


def test_candidate_local_capture_selects_one_configured_provider_and_pins_it_for_both_arms():
    workflow = _workflow_text()
    assert 'USE_LLM_PROVIDER_ORDER: "openrouter,nvidia,gemini,mistral,workers_ai"' in workflow
    for credential in (
        "OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}",
        "NVIDIA_API_KEY: ${{ secrets.NVIDIA_API_KEY }}",
        "GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}",
        "MISTRAL_API_KEY: ${{ secrets.MISTRAL_API_KEY }}",
        "CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}",
        "CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}",
    ):
        assert credential in workflow
    assert "GROQ_API_KEY" not in workflow
    assert "--provider groq" not in workflow
    assert "--model qwen/qwen3.8-27b" not in workflow
    assert "scripts/capture_gold_star_matched_pairs.py" in workflow
    assert "actions/checkout@v4" in workflow
    assert "gold-star-blind-review-" in workflow
    assert "gold-star-unblinding-evidence-" in workflow
    assert "paired-evaluation-template.json" in workflow
    assert "--provider=openrouter" not in workflow
    assert "--model=openai/gpt-oss-20b" not in workflow
    assert "--inter-call-delay-seconds 65" in workflow
    assert "--provider-timeout-seconds 10" in workflow
    assert ".onrender.com" not in workflow


def test_candidate_local_runner_uses_existing_provider_pins_and_complete_asgi_boundary():
    source = (
        Path(__file__).resolve().parents[1]
        / "scripts/capture_gold_star_matched_pairs.py"
    ).read_text(encoding="utf-8")
    assert "evaluation_context(arm=arm, provider=provider, model=model)" in source
    assert 'client.post("/api/query"' in source
    assert "httpx.ASGITransport(app=main.app)" in source
    assert "semantic_application_certified" in source
    assert "unblinding-key.json" in source


def test_matched_pair_case_file_is_wired_into_the_workflow():
    workflow = _workflow_text()
    assert "docs/qa/gold_star_matched_pair_cases.json" in workflow


def test_existing_mirror_capture_workflow_remains_main_only():
    workflow = (
        Path(__file__).resolve().parents[1]
        / ".github/workflows/gold-star-wp3-paired-capture.yml"
    ).read_text(encoding="utf-8")
    assert "branches: [main]" in workflow
    assert "living-archive-backend-mirror.onrender.com" in workflow
    assert "matched-pair-local:" not in workflow

def test_provider_capture_push_requires_the_dedicated_repository_qa_branch():
    workflow = _workflow_text()
    assert "qa/gold-star-matched-pair-candidate-2017-20261125" in workflow
    assert "github.event_name == 'push'" in workflow
    assert "github.ref == 'refs/heads/qa/gold-star-matched-pair-candidate-2017-20261125'" in workflow
    assert "github.event_name == 'pull_request'" not in workflow

def test_candidate_local_capture_publishes_run_reference_for_blind_review():
    workflow = _workflow_text()
    assert "issues: write" in workflow
    assert "Publish capture run reference to PR #2018" in workflow
    assert "gh pr comment 2018" in workflow
    assert "actions/runs/" in workflow

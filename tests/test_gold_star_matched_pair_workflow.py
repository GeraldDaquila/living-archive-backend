from pathlib import Path


def test_candidate_local_matched_pair_capture_runs_only_in_github_actions():
    workflow = (
        Path(__file__).resolve().parents[1]
        / ".github/workflows/gold-star-matched-pair-candidate.yml"
    ).read_text(encoding="utf-8")
    assert 'test/gold-star-matched-pair-runner-20261123' in workflow
    assert 'USE_GUIDE_EVALUATION_PROVIDER_ORDER: "openrouter,gemini,groq"' in workflow
    assert "--provider=groq" not in workflow
    assert "--model=openai/gpt-oss-20b" not in workflow
    assert "matched-pair-local:" in workflow
    assert "scripts/capture_gold_star_matched_pairs.py" in workflow
    assert "actions/checkout@v4" in workflow
    assert "gold-star-blind-review-" in workflow
    assert "gold-star-unblinding-evidence-" in workflow
    assert "paired-evaluation-template.json" in workflow
    assert "--provider " not in workflow
    assert "--model " not in workflow
    assert "--inter-call-delay-seconds 65" in workflow
    assert "--provider-timeout-seconds 10" in workflow
    assert "pull_request:" in workflow
    assert "github.event_name == 'pull_request'" in workflow
    assert "github.event.pull_request.head.ref == 'test/gold-star-matched-pair-runner-20261123'" in workflow
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
    workflow = (
        Path(__file__).resolve().parents[1]
        / ".github/workflows/gold-star-matched-pair-candidate.yml"
    ).read_text(encoding="utf-8")
    assert "docs/qa/gold_star_matched_pair_cases.json" in workflow


def test_existing_mirror_capture_workflow_remains_main_only():
    workflow = (
        Path(__file__).resolve().parents[1]
        / ".github/workflows/gold-star-wp3-paired-capture.yml"
    ).read_text(encoding="utf-8")
    assert "branches: [main]" in workflow
    assert "living-archive-backend-mirror.onrender.com" in workflow
    assert "matched-pair-local:" not in workflow

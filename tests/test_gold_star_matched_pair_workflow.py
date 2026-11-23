from pathlib import Path


def test_candidate_local_matched_pair_capture_runs_only_in_github_actions():
    workflow = (
        Path(__file__).resolve().parents[1]
        / ".github/workflows/gold-star-wp3-paired-capture.yml"
    ).read_text(encoding="utf-8")
    assert 'test/gold-star-matched-pair-runner-20261123' in workflow
    assert "matched-pair-local:" in workflow
    assert "scripts/capture_gold_star_matched_pairs.py" in workflow
    assert "actions/checkout@v4" in workflow
    assert "gold-star-matched-pairs-" in workflow
    assert "living-archive-backend.onrender.com" not in workflow
    assert "living-archive-backend-mirror.onrender.com" in workflow


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

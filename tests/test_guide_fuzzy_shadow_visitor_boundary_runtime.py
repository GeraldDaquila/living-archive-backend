"""Runtime visitor recommendation normalization must strip shadow diagnostics."""
import main


def test_runtime_public_recommendation_strips_injected_shadow_diagnostics():
    doorway = {
        "title": "Canonical Stewardship Resource",
        "url": "https://geralddaquila.com/canonical-stewardship-resource/",
        "_fuzzy_relevance_shadow": {"overall_shadow_score": 0.99},
        "overall_shadow_score": 0.99,
        "ethical_tradeoff": 1.0,
    }
    normalized = main._normalize_authoritative_recommendation(doorway)
    assert normalized == {
        "title": "Canonical Stewardship Resource",
        "url": "https://geralddaquila.com/canonical-stewardship-resource/",
    }
    assert all("shadow" not in key and "ethical_tradeoff" not in key for key in normalized)

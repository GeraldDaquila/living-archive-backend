"""Regression: provenance answers must not erase an upstream verified Archive doorway."""
import main


def test_archive_claim_final_boundary_preserves_verified_doorway(monkeypatch):
    query = "How should The Guide distinguish archive-grounded guidance from general external knowledge?"
    doorway = {
        "title": "Foundations of Stewardship Governance",
        "url": "https://geralddaquila.com/foundations-of-stewardship-governance/",
    }
    payload = {
        "response": "placeholder",
        "recommendation": doorway,
        "canonical_doorway": doorway,
    }

    monkeypatch.setattr(main, "_is_archive_claim_boundary_inquiry", lambda q: True)
    monkeypatch.setattr(main, "_archive_claim_boundary_recovery", lambda: "recovered answer")
    monkeypatch.setattr(main, "_guide_node_specific_match", lambda q: None)

    result = main._guide_finalize_visitor_payload(payload, query)

    assert result["recommendation"] == doorway
    assert result["canonical_doorway"] == doorway
    assert result["doorway_title"] == doorway["title"]
    assert result["doorway_url"] == doorway["url"]

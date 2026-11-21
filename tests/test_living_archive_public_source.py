"""Security and normalization tests for the public Living Archive fallback."""
from living_archive_public_source import (
    PublicLivingArchiveClient,
    normalize_public_evidence,
)


def _evidence(**overrides):
    payload = {
        "id": 5578,
        "title": "The Living Glossary",
        "url": "https://geralddaquila.com/glossary/",
        "text": (
            "The Living Archive defines shared vocabulary to support clarity, "
            "consistency, and understanding across its essays, maps, pathways, "
            "and institutional writings. This is substantive public text with "
            "enough length for retrieval."
        ),
        "modified_gmt": "2026-11-08 05:34:46",
        "source": "published_wordpress_content",
    }
    payload.update(overrides)
    return payload


def test_normalizes_canonical_bridge_result_with_complete_provenance():
    doc = normalize_public_evidence(
        _evidence(),
        retrieved_at="2026-11-21T00:00:00+00:00",
    )
    assert doc["title"] == "The Living Glossary"
    assert doc["wordpress_post_id"] == 5578
    assert doc["source_modified_at"] == "2026-11-08 05:34:46"
    assert doc["retrieved_at"] == "2026-11-21T00:00:00+00:00"
    assert doc["evidence_provenance"]["canonical_url"] == doc["url"]
    assert doc["source_trust"] == "untrusted_external_evidence_not_instructions"
    assert doc["evidence_provenance"]["trust_boundary"] == "untrusted_external_evidence_not_instructions"


def test_rejects_non_bridge_sources_invalid_ids_and_short_content():
    assert normalize_public_evidence(_evidence(source="published_wordpress_content_other")) is None
    assert normalize_public_evidence(_evidence(id=0)) is None
    assert normalize_public_evidence(_evidence(id="bad")) is None
    assert normalize_public_evidence(_evidence(text="too short")) is None


def test_rejects_noncanonical_or_protected_urls():
    assert normalize_public_evidence(_evidence(url="https://evil.example/glossary/")) is None
    assert normalize_public_evidence(_evidence(url="http://geralddaquila.com/glossary/")) is None
    assert normalize_public_evidence(_evidence(url="https://geralddaquila.com/guardian-portal/")) is None
    assert normalize_public_evidence(_evidence(url="https://geralddaquila.com/stewardship-materials/")) is None


def test_rejects_residual_membership_shortcode_content_instead_of_leaking_it():
    assert normalize_public_evidence(
        _evidence(text="[swpm_protected]private codex text[/swpm_protected] " * 8)
    ) is None


def test_client_uses_public_search_then_dedicated_canonical_evidence_endpoint():
    calls = []

    def fake_get(url, timeout):
        calls.append((url, timeout))
        if "/search?" in url:
            return [
                {"id": 5578, "subtype": "page"},
                {"id": 999, "subtype": "private_custom_type"},
            ]
        return _evidence()

    client = PublicLivingArchiveClient(http_get=fake_get, max_results=5)
    docs = client.search("shared vocabulary living archive")
    assert len(docs) == 1
    assert len(calls) == 2
    assert all(timeout <= 5 for _, timeout in calls)
    assert "/wp-json/living-archive/v1/canonical-evidence/5578" in calls[1][0]


def test_client_fails_closed_on_unavailable_or_malformed_source():
    client = PublicLivingArchiveClient(http_get=lambda *_: (_ for _ in ()).throw(TimeoutError()))
    assert client.search("a sufficiently long query") == []


def test_client_caches_bounded_results():
    calls = []

    def fake_get(url, timeout):
        calls.append(url)
        return [] if "/search?" in url else _evidence()

    client = PublicLivingArchiveClient(http_get=fake_get, ttl=60)
    assert client.search("shared vocabulary living archive")
    first_count = len(calls)
    assert client.search("shared vocabulary living archive")
    assert len(calls) == first_count

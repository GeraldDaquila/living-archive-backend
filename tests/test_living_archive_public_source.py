"""Security and normalization tests for the public Living Archive fallback."""
from living_archive_public_source import (
    PublicLivingArchiveClient,
    normalize_public_post,
    _clean_text,
)


def _post(**overrides):
    post = {
        "id": 5578,
        "status": "publish",
        "type": "page",
        "link": "https://geralddaquila.com/glossary/",
        "title": {"rendered": "The Living Glossary"},
        "content": {
            "protected": False,
            "rendered": (
                "<!-- wp:paragraph --><p>The Living Archive defines shared vocabulary "
                "to support clarity, consistency, and understanding across its essays. "
                "This is substantive public text with enough length for retrieval.</p>"
                "<nav>Ignore this navigation chrome.</nav>"
                "[living_glossary_intelligence]"
                "<script>ignore_secret()</script>"
            ),
        },
        "modified_gmt": "2026-11-08T05:34:46",
    }
    post.update(overrides)
    return post


def test_normalizes_published_public_post_with_complete_provenance():
    doc = normalize_public_post(_post(), retrieved_at="2026-11-21T00:00:00+00:00")
    assert doc["title"] == "The Living Glossary"
    assert doc["wordpress_post_id"] == 5578
    assert doc["source_modified_at"] == "2026-11-08T05:34:46"
    assert doc["retrieved_at"] == "2026-11-21T00:00:00+00:00"
    assert "Ignore this navigation" not in doc["text"]
    assert "ignore_secret" not in doc["text"]
    assert "living_glossary_intelligence" not in doc["text"]
    assert doc["evidence_provenance"]["canonical_url"] == doc["url"]


def test_rejects_unpublished_nonstandard_or_password_protected_documents():
    assert normalize_public_post(_post(status="draft")) is None
    assert normalize_public_post(_post(type="attachment")) is None
    assert normalize_public_post(_post(content={"protected": True, "rendered": "private " * 40})) is None


def test_rejects_noncanonical_or_protected_urls():
    assert normalize_public_post(_post(link="https://evil.example/glossary/")) is None
    assert normalize_public_post(_post(link="http://geralddaquila.com/glossary/")) is None
    assert normalize_public_post(_post(link="https://geralddaquila.com/guardian-portal/")) is None
    assert normalize_public_post(_post(link="https://geralddaquila.com/stewardship-materials/")) is None


def test_rejects_known_membership_shortcode_content_instead_of_leaking_it():
    assert _clean_text(
        "<p>Public intro.</p>[swpm_protected]private codex text[/swpm_protected]"
    ) == ""


def test_client_bounds_results_and_uses_anonymous_search_then_individual_fetch():
    calls = []

    def fake_get(url, timeout):
        calls.append((url, timeout))
        if "/search?" in url:
            return [
                {"id": 5578, "subtype": "page"},
                {"id": 999, "subtype": "private_custom_type"},
            ]
        return _post()

    client = PublicLivingArchiveClient(http_get=fake_get, max_results=5)
    docs = client.search("shared vocabulary living archive")
    assert len(docs) == 1
    assert len(calls) == 2
    assert all(timeout <= 5 for _, timeout in calls)
    assert "/wp/v2/pages/5578" in calls[1][0]


def test_client_fails_closed_on_unavailable_or_malformed_source():
    client = PublicLivingArchiveClient(http_get=lambda *_: (_ for _ in ()).throw(TimeoutError()))
    assert client.search("a sufficiently long query") == []


def test_client_caches_bounded_results():
    calls = []

    def fake_get(url, timeout):
        calls.append(url)
        return [] if "/search?" in url else _post()

    client = PublicLivingArchiveClient(http_get=fake_get, ttl=60)
    assert client.search("shared vocabulary living archive") == []
    first_count = len(calls)
    assert client.search("shared vocabulary living archive") == []
    assert len(calls) == first_count

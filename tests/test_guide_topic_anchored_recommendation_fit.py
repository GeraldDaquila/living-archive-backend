"""Regression tests for topic relevance and read-only Guide retrieval boundaries."""

import ast
from pathlib import Path

import main


QUERY = (
    "How do political dynasties, public institutions, and local accountability "
    "interact in the Philippines?"
)


def test_topic_fit_rejects_country_only_cultural_decoy():
    decoy = {
        "title": "The Philippines’ Fascination with Beauty Pageants: Soft Power and Gender Equity",
        "url": "https://geralddaquila.com/2025/06/05/the-philippines-fascination-with-beauty-pageants/",
        "text": (
            "Pageants in the Philippines shape cultural identity, gender equity, "
            "tourism, and international representation."
        ),
    }
    assert not main._topic_specific_candidate_fit(QUERY, decoy)
    assert not main._eligible_outward_doc(
        QUERY, decoy, main._base._inquiry_profile(QUERY), min_relevance=2
    )


def test_topic_fit_accepts_direct_political_dynasties_and_accountability_evidence():
    candidate = {
        "title": "Political Dynasties in the Philippines",
        "url": "https://geralddaquila.com/political-dynasties/",
        "text": (
            "Political dynasties shape local power. Public institutions can be "
            "weakened when accountability is limited. Local accountability and "
            "institutional checks affect how governance works."
        ),
    }
    assert main._topic_specific_candidate_fit(QUERY, candidate)
    assert main._eligible_outward_doc(
        QUERY, candidate, main._base._inquiry_profile(QUERY), min_relevance=2
    )


def test_topic_fit_does_not_overconstrain_single_anchor_queries():
    query = "How does governance work in the Philippines?"
    candidate = {
        "title": "A General Introduction to Governance",
        "url": "https://geralddaquila.com/governance-introduction/",
        "text": "This resource introduces governance and how public decisions are made.",
    }
    assert main._topic_specific_candidate_fit(query, candidate)


def test_outward_response_boundary_rejects_complete_and_truncated_html():
    assert main._basic_inquiry_contains_html_markup(
        '<a href="https://geralddaquila.com/example/">Open</a>'
    )
    assert main._basic_inquiry_contains_html_markup(
        '<a href="https://geralddaquila.com/2025/05/21/political-dynasties”'
    )
    assert not main._basic_inquiry_contains_html_markup(
        "Stewardship means caring for what has been entrusted to us."
    )


def test_political_dynasties_question_rejects_general_institutions_decoy():
    decoy = {
        "title": "Designing Human-Scale Institutions for the 21st Century",
        "url": "https://geralddaquila.com/2026/06/03/designing-human-scale-institutions-for-the-21st-century/",
        "text": (
            "Institutions and accountability are important for good governance. "
            "Public institutions need to serve communities and sustain shared decisions."
        ),
    }
    assert not main._topic_specific_candidate_fit(QUERY, decoy)

def test_deterministic_public_governance_recovery_answers_when_provider_is_unavailable():
    query = (
        "How do political dynasties, public institutions, and local accountability "
        "interact in the Philippines?"
    )
    result = main._basic_inquiry_round1_deterministic_response(
        query, {}, {"context_blocks": ""}
    )
    response = result["response"].casefold()
    assert result["provider"] == "bounded_public_governance_recovery"
    assert "political dynasties" in response
    assert "public institutions" in response
    assert "accountability" in response
    assert "recommendation below" not in response
    assert result["doorway_title"] == ""


def test_deterministic_recovery_does_not_promise_archive_recommendation_without_one():
    result = main._basic_inquiry_round1_deterministic_response(
        "Explain a highly specific question with no available source.",
        {},
        {"context_blocks": ""},
        recommendation_available=False,
    )
    assert "recommendation below" not in result["response"].casefold()
    assert "sufficiently relevant archive resource" in result["response"].casefold()


def test_canonical_primary_prefers_exact_subject_title_over_long_adjacent_article():
    query = "What does the Living Archive say about becoming fully human?"
    adjacent = {
        "title": "Truth in the Age of AI: Why Discernment Is Becoming a Survival Skill",
        "url": "https://geralddaquila.com/2026/10/19/truth-in-the-age-of-ai-why-discernment-is-becoming-a-survival-skill/",
        "text": (
            "Becoming fully human requires discernment in an age of artificial intelligence. "
            "Human life, human judgment, and human flourishing are discussed at length. "
            "The article returns repeatedly to discernment, technology, and survival."
        ),
    }
    direct = {
        "title": "Becoming Fully Human",
        "url": "https://geralddaquila.com/2026/10/05/the-architecture-of-human-development/",
        "text": (
            "Becoming fully human is explored through the architecture of human development. "
            "The resource considers human existence, growth, and the conditions of becoming fully human."
        ),
    }
    selected = main._canonical_primary_from_docs(
        [adjacent, direct], query, main._base._inquiry_profile(query)
    )
    assert selected is direct

def test_human_development_topic_gate_rejects_attention_article_even_if_body_repeats_phrase():
    query = "What does the Living Archive say about becoming fully human?"
    decoy = {
        "title": "Attention as Ecology: Why Human Focus Is Becoming a Civilizational Resource",
        "url": "https://geralddaquila.com/2026/09/28/attention-as-ecology-why-human-focus-is-becoming-a-civilizational-resource/",
        "text": (
            "Becoming fully human requires careful attention and discernment. "
            "The article is about human focus, attention, and civilizational resources."
        ),
    }
    assert not main._topic_specific_candidate_fit(query, decoy)
    assert not main._eligible_outward_doc(
        query, decoy, main._base._inquiry_profile(query), min_relevance=2
    )


def test_human_development_topic_gate_accepts_direct_title_with_body_corroboration():
    query = "What does the Living Archive say about becoming fully human?"
    direct = {
        "title": "Becoming Fully Human",
        "url": "https://geralddaquila.com/2026/10/05/the-architecture-of-human-development/",
        "text": (
            "Becoming fully human is explored through human development, "
            "the body's role as archive, and the soul's continuity."
        ),
    }
    assert main._topic_specific_candidate_fit(query, direct)
    assert main._eligible_outward_doc(
        query, direct, main._base._inquiry_profile(query), min_relevance=2
    )



def test_human_development_topic_gate_allows_body_soul_doorway_fallback():
    query = "What does the Living Archive say about becoming fully human?"
    related = {
        "title": "The Body as Archive",
        "url": "https://geralddaquila.com/2026/10/05/the-architecture-of-human-development/",
        "text": (
            "The body is an archive of memory and embodied experience. "
            "The soul continues beyond the body's temporary form."
        ),
    }
    assert main._topic_specific_candidate_fit(query, related)
    assert main._eligible_outward_doc(
        query, related, main._base._inquiry_profile(query), min_relevance=2
    )

def test_guide_request_core_contains_no_vector_index_mutation_calls():
    """The live Guide query path may retrieve canonical vectors, never mutate them."""
    forbidden_methods = {
        "upsert", "upsert_records", "delete", "delete_records", "insert",
        "update", "add_vectors", "remove_vectors",
    }

    def attribute_chain(node):
        parts = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            parts.append(node.id)
        return ".".join(reversed(parts))

    source_paths = (
        Path(main.__file__).resolve(),
        Path(main.use_core.__file__).resolve(),
    )
    violations = []
    for path in source_paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr not in forbidden_methods:
                continue
            receiver = attribute_chain(node.func.value)
            if receiver in {"index", "pinecone_index", "vector_index"} or receiver.endswith(
                (".index", ".pinecone_index", ".vector_index")
            ):
                violations.append(f"{path.name}:{node.lineno}: {receiver}.{node.func.attr}")

    assert not violations, (
        "The visitor-facing Guide query core must remain read-only against the "
        "canonical vector index; found mutation calls: " + ", ".join(violations)
    )



def test_wordpress_candidate_recovers_public_body_when_rest_fetch_times_out(monkeypatch):
    """A search-discovered canonical URL may recover via its public page body."""
    import json

    query = "What does the Living Archive say about becoming fully human?"
    page_url = "https://geralddaquila.com/2026/10/05/the-architecture-of-human-development/"
    search_payload = [{
        "title": {"rendered": "Becoming Fully Human"},
        "url": page_url,
        "_links": {"self": [{"href": "https://geralddaquila.com/wp-json/wp/v2/posts/66853"}]},
    }]

    class FakeResponse:
        def __init__(self, body, url):
            self.body = body.encode("utf-8") if isinstance(body, str) else body
            self.url = url
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self, *args):
            return self.body
        def geturl(self):
            return self.url

    calls = []
    def fake_urlopen(request, timeout):
        url = request.full_url
        calls.append(url)
        if "/wp-json/wp/v2/search?" in url:
            return FakeResponse(json.dumps(search_payload), url)
        if "/wp-json/wp/v2/posts/66853" in url:
            raise TimeoutError("controlled REST body timeout")
        if url == page_url:
            return FakeResponse(
                "<html><head><title>Becoming Fully Human</title></head><body><main>"
                "Becoming fully human is explored through human development, biological, "
                "psychological, relational, ethical, systemic, and existential capacities."
                "</main></body></html>",
                url,
            )
        raise AssertionError("Unexpected URL requested: " + url)

    monkeypatch.setattr(main, "_subject_terms", lambda _query: {"fully human"})
    monkeypatch.setattr(main, "urlopen", fake_urlopen)

    candidates = main._wordpress_search_canonical_candidates(query, limit=3)

    assert len(candidates) == 1
    assert candidates[0]["title"] == "Becoming Fully Human"
    assert candidates[0]["url"] == page_url
    assert "human development" in candidates[0]["text"].casefold()
    assert calls[-1] == page_url


def test_wordpress_candidate_does_not_emit_metadata_when_both_body_paths_fail(monkeypatch):
    """A canonical URL/title is never enough to authorize a recommendation."""
    import json

    page_url = "https://geralddaquila.com/2026/10/05/the-architecture-of-human-development/"
    search_payload = [{
        "title": {"rendered": "Becoming Fully Human"},
        "url": page_url,
        "_links": {"self": [{"href": "https://geralddaquila.com/wp-json/wp/v2/posts/66853"}]},
    }]

    class FakeResponse:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self, *args):
            return json.dumps(search_payload).encode("utf-8")
        def geturl(self):
            return "https://geralddaquila.com/wp-json/wp/v2/search"

    def fake_urlopen(request, timeout):
        if "/wp-json/wp/v2/search?" in request.full_url:
            return FakeResponse()
        raise TimeoutError("controlled body timeout")

    monkeypatch.setattr(main, "_subject_terms", lambda _query: {"fully human"})
    monkeypatch.setattr(main, "urlopen", fake_urlopen)

    assert main._wordpress_search_canonical_candidates(
        "What does the Living Archive say about becoming fully human?", limit=3
    ) == []


def test_wordpress_candidate_recovers_canonical_excerpt_before_large_body_fetch(monkeypatch):
    """A real published excerpt can ground a candidate when full-body routes time out."""
    import json

    query = "What does the Living Archive say about becoming fully human?"
    page_url = "https://geralddaquila.com/2026/10/05/the-architecture-of-human-development/"
    post_endpoint = "https://geralddaquila.com/wp-json/wp/v2/posts/66853"
    search_payload = [{
        "title": {"rendered": "Becoming Fully Human"},
        "url": page_url,
        "_links": {"self": [{"href": post_endpoint}]},
    }]
    excerpt_text = (
        "This cornerstone essay explores human development through a systems perspective, "
        "integrating biology, psychology, ethics, and leadership. The body and soul are "
        "considered alongside maturity, integration, and responsible stewardship."
    )
    excerpt_payload = {
        "link": page_url,
        "title": {"rendered": "✨ Becoming Fully Human"},
        "excerpt": {"rendered": f"<p>{excerpt_text}</p>"},
    }

    class FakeResponse:
        def __init__(self, body, url):
            self.body = body.encode("utf-8") if isinstance(body, str) else body
            self.url = url
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self, *args):
            return self.body
        def geturl(self):
            return self.url

    calls = []
    def fake_urlopen(request, timeout):
        url = request.full_url
        calls.append(url)
        if "/wp-json/wp/v2/search?" in url:
            return FakeResponse(json.dumps(search_payload), url)
        if url == post_endpoint:
            raise TimeoutError("controlled full REST body timeout")
        if url == post_endpoint + "?_fields=link,title,excerpt":
            return FakeResponse(json.dumps(excerpt_payload), url)
        if url == page_url:
            raise AssertionError("Large public page fetch should not be needed when excerpt is sufficient.")
        raise AssertionError("Unexpected URL requested: " + url)

    monkeypatch.setattr(main, "_subject_terms", lambda _query: {"fully human"})
    monkeypatch.setattr(main, "urlopen", fake_urlopen)

    candidates = main._wordpress_search_canonical_candidates(query, limit=3)

    assert len(candidates) == 1
    assert candidates[0]["title"] == "✨ Becoming Fully Human"
    assert candidates[0]["url"] == page_url
    assert "human development" in candidates[0]["text"].casefold()
    assert "responsible stewardship" in candidates[0]["text"].casefold()
    assert post_endpoint + "?_fields=link,title,excerpt" in calls
    assert page_url not in calls



def test_wordpress_candidate_rejects_excerpt_without_topic_body_corroboration(monkeypatch):
    """A generic excerpt must not bypass the human-development body/soul gate."""
    import json

    query = "What does the Living Archive say about becoming fully human?"
    page_url = "https://geralddaquila.com/2026/10/05/the-architecture-of-human-development/"
    post_endpoint = "https://geralddaquila.com/wp-json/wp/v2/posts/66853"
    search_payload = [{
        "title": {"rendered": "✨ Becoming Fully Human"},
        "url": page_url,
        "_links": {"self": [{"href": post_endpoint}]},
    }]
    excerpt_payload = {
        "link": page_url,
        "title": {"rendered": "✨ Becoming Fully Human"},
        "excerpt": {"rendered": (
            "<p>This cornerstone essay explores human development through biology, "
            "psychology, ethics, leadership, integration, and maturity.</p>"
        )},
    }

    class FakeResponse:
        def __init__(self, body, url):
            self.body = body.encode("utf-8") if isinstance(body, str) else body
            self.url = url
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self, *args):
            return self.body
        def geturl(self):
            return self.url

    calls = []
    def fake_urlopen(request, timeout):
        url = request.full_url
        calls.append(url)
        if "/wp-json/wp/v2/search?" in url:
            return FakeResponse(json.dumps(search_payload), url)
        if url == post_endpoint:
            raise TimeoutError("controlled full REST body timeout")
        if url == post_endpoint + "?_fields=link,title,excerpt":
            return FakeResponse(json.dumps(excerpt_payload), url)
        if url == page_url:
            return FakeResponse(
                "<html><head><title>✨ Becoming Fully Human</title></head><body><main>"
                "The article describes human development as an integration of biological, "
                "psychological, relational, ethical, systemic, and existential capacities. "
                "It considers the body and soul within this wider developmental architecture."
                "</main></body></html>",
                url,
            )
        raise AssertionError("Unexpected URL requested: " + url)

    monkeypatch.setattr(main, "_subject_terms", lambda _query: {"fully human"})
    monkeypatch.setattr(main, "urlopen", fake_urlopen)

    candidates = main._wordpress_search_canonical_candidates(query, limit=3)

    assert len(candidates) == 1
    assert "body and soul" in candidates[0]["text"].casefold()
    assert page_url in calls



def test_wordpress_candidate_recovers_topic_fit_body_from_read_only_bridge(monkeypatch):
    """The published-content bridge supplies real body text without full page rendering."""
    import json

    query = "What does the Living Archive say about becoming fully human?"
    page_url = "https://geralddaquila.com/2026/10/05/the-architecture-of-human-development/"
    post_endpoint = "https://geralddaquila.com/wp-json/wp/v2/posts/66853"
    bridge_url = "https://geralddaquila.com/wp-json/living-archive/v1/canonical-evidence/66853"
    search_payload = [{
        "title": {"rendered": "✨ Becoming Fully Human"},
        "url": page_url,
        "_links": {"self": [{"href": post_endpoint}]},
    }]
    excerpt_payload = {
        "link": page_url,
        "title": {"rendered": "✨ Becoming Fully Human"},
        "excerpt": {"rendered": (
            "<p>This cornerstone essay explores human development through biology, "
            "psychology, ethics, leadership, integration, and maturity.</p>"
        )},
    }
    bridge_payload = {
        "id": 66853,
        "title": "✨ Becoming Fully Human",
        "url": page_url,
        "text": (
            "Human development integrates biological, psychological, relational, ethical, "
            "systemic, and existential capacities. The opening explains that biology "
            "describes the body, while the wider article connects the dimensions of "
            "human development into a coherent architecture."
        ),
        "source": "published_wordpress_content",
    }

    class FakeResponse:
        def __init__(self, body, url):
            self.body = body.encode("utf-8") if isinstance(body, str) else body
            self.url = url
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self, *args):
            return self.body
        def geturl(self):
            return self.url

    calls = []
    def fake_urlopen(request, timeout):
        url = request.full_url
        calls.append(url)
        if "/wp-json/wp/v2/search?" in url:
            return FakeResponse(json.dumps(search_payload), url)
        if url == post_endpoint:
            raise TimeoutError("controlled full REST body timeout")
        if url == post_endpoint + "?_fields=link,title,excerpt":
            return FakeResponse(json.dumps(excerpt_payload), url)
        if url == bridge_url:
            return FakeResponse(json.dumps(bridge_payload), url)
        if url == page_url:
            raise AssertionError("Full public page rendering should not be needed after bridge recovery.")
        raise AssertionError("Unexpected URL requested: " + url)

    monkeypatch.setattr(main, "_subject_terms", lambda _query: {"fully human"})
    monkeypatch.setattr(main, "urlopen", fake_urlopen)

    candidates = main._wordpress_search_canonical_candidates(query, limit=3)

    assert len(candidates) == 1
    assert candidates[0]["title"] == "✨ Becoming Fully Human"
    assert candidates[0]["url"] == page_url
    assert "the body" in candidates[0]["text"].casefold()
    assert bridge_url in calls
    assert page_url not in calls



def test_qa_read_only_diagnostics_is_disabled_without_flag(monkeypatch):
    from types import SimpleNamespace
    import pytest

    monkeypatch.delenv("USE_QA_DIAGNOSTICS", raising=False)
    with pytest.raises(main.HTTPException) as exc:
        main.qa_read_only_diagnostics(SimpleNamespace(query_params={}))
    assert exc.value.status_code == 404


def test_qa_read_only_diagnostics_reports_stats_and_exact_url_probe_without_writes(monkeypatch):
    from types import SimpleNamespace

    canonical_url = "https://geralddaquila.com/2026/10/05/the-architecture-of-human-development/"
    queries = []

    class FakeIndex:
        def describe_index_stats(self):
            return {
                "dimension": 384,
                "total_vector_count": 12345,
                "namespaces": {"": {"vector_count": 12345}},
            }

        def query(self, **kwargs):
            queries.append(kwargs)
            url = kwargs["filter"]["url"]["$eq"]
            matches = []
            if url == canonical_url:
                matches = [{
                    "id": "becoming-fully-human-0",
                    "score": 0.91,
                    "metadata": {
                        "title": "✨ Becoming Fully Human",
                        "url": canonical_url,
                        "chunk_index": 0,
                        "resource_type": "essay",
                    },
                }]
            return {"matches": matches}

    monkeypatch.setenv("USE_QA_DIAGNOSTICS", "1")
    monkeypatch.setenv("USE_PROVIDER_HEALTH_STATE_URL", "")
    monkeypatch.setenv("USE_PROVIDER_BANK_SHARED_SECRET", "")
    monkeypatch.setattr(main.use_core, "index", FakeIndex(), raising=False)
    monkeypatch.setattr(main.use_core, "generate_embedding", lambda _text: [0.1] * 384, raising=False)

    payload = main.qa_read_only_diagnostics(
        SimpleNamespace(query_params={"canonical_url": canonical_url})
    )

    assert payload["ok"] is True
    assert payload["read_only"] is True
    assert payload["write_operations_performed"] is False
    assert payload["index"]["dimension"] == 384
    assert payload["index"]["total_vector_count"] == 12345
    assert payload["exact_url_probe"]["status"] == "ok"
    assert payload["exact_url_probe"]["variants"][canonical_url]["match_count"] == 1
    assert payload["provider_health"]["shared_secret_configured"] is False
    assert payload["provider_health"]["persistence_enabled"] is False
    assert len(queries) == 2
    assert all("filter" in query and "url" in query["filter"] for query in queries)

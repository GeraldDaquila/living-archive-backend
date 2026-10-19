"""Request-boundary end-to-end contract for the compound stewardship question.

Exercises the actual ASGI request boundary, Basic Inquiry assembly, provider-neutral
composition validation, recommendation authority, and JSON serialization. Only the
external retrieval result and Provider Bank transport are controlled test seams.
"""
import asyncio
import json

import general_guide_composition
import main as use_main


QUERY = "What is stewardship and why does it matter now more than ever?"
CANONICAL_URL = (
    "https://geralddaquila.com/"
    "the-living-archive-navigator-volume-iv-stewardship-exchange/"
)
CANONICAL_TITLE = (
    "The Living Archive Navigator: Volume IV – Stewardship & Exchange"
)
ANSWER = (
    "Stewardship means taking care of something entrusted to you—such as your time, relationships, shared spaces, money, or the natural world—rather than treating it as if only your immediate needs matter. In everyday life, it shows up in small choices: keeping a promise, maintaining what others rely on, using resources thoughtfully, and considering how your decisions affect people around you.\n\n"
    "It matters because ordinary choices accumulate. Carelessness can pass costs to other people or to the future, while responsible care helps preserve trust, usefulness, and possibilities for those who come after us.\n\n"
    "Stewardship does not mean controlling everything or sacrificing yourself for everyone else. It means recognizing what is yours to care for, acting responsibly within your limits, and leaving things no worse—and where possible better—than you found them."
)


async def _post_query(query):
    body = json.dumps({"query": query}).encode("utf-8")
    sent = []
    consumed = False

    async def receive():
        nonlocal consumed
        if not consumed:
            consumed = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/query",
        "raw_path": b"/api/query",
        "query_string": b"",
        "root_path": "",
        "headers": [(b"content-type", b"application/json")],
        "client": ("127.0.0.1", 43123),
        "server": ("testserver", 80),
    }
    await use_main._use_request_boundary(scope, receive, send)
    start = next(
        message for message in sent
        if message["type"] == "http.response.start"
    )
    response_body = b"".join(
        message.get("body", b"")
        for message in sent
        if message["type"] == "http.response.body"
    )
    return start["status"], json.loads(response_body.decode("utf-8"))


def _install_controlled_provider_and_retrieval(monkeypatch, context_flags=None):
    context = {
        "intent": "TOPICAL_INQUIRY",
        "authoritative_doorway": {
            "title": "🏛️Workshops &amp; Advisory",
            "url": "https://geralddaquila.com/workshops-advisory/",
        },
        "generation_authority_protected_docs": [
            {
                "title": "🏛️Workshops &amp; Advisory",
                "url": "https://geralddaquila.com/workshops-advisory/",
                "content": "Workshop and advisory services for teams and organizations.",
            },
            {
                "title": CANONICAL_TITLE,
                "url": CANONICAL_URL,
                "content": (
                    "Stewardship asks what we are responsible for and how "
                    "we care for what affects more than ourselves."
                ),
            }
        ],
    }
    context.update(context_flags or {})
    monkeypatch.setattr(
        use_main.use_core, "fetch_canonical_context", lambda query: context
    )
    # Keep existing request-boundary tests deterministic and offline. Dedicated
    # recovery tests inject canonical search results explicitly.
    monkeypatch.setattr(use_main, "_wordpress_search_canonical_candidates", lambda query, limit=5: [])
    monkeypatch.setattr(
        use_main._base, "_inquiry_profile", lambda query: {}
    )
    monkeypatch.setattr(
        use_main, "classify_safety", lambda query, history="": None
    )
    monkeypatch.setattr(
        use_main, "_basic_inquiry_requires_macro_routing", lambda query: False
    )

    composition_calls = []

    def controlled_provider_bank(**kwargs):
        composition_calls.append(kwargs["operation"])
        candidate = {
            "response": ANSWER,
            "doorway_title": CANONICAL_TITLE,
            "response_shape": "explanatory",
        }
        parsed = kwargs["parse"](json.dumps(candidate, ensure_ascii=False))
        return {
            "parsed": parsed,
            "provider": "controlled_test_provider",
            "model": "controlled_test_model",
            "preference_order": ["controlled_test_provider:controlled_test_model"],
        }

    monkeypatch.setattr(
        general_guide_composition, "route_with_model_bank", controlled_provider_bank
    )
    return composition_calls


def test_compound_stewardship_question_completes_request_composition_and_recommendation(monkeypatch):
    composition_calls = _install_controlled_provider_and_retrieval(monkeypatch)
    monkeypatch.setattr(
        use_main,
        "_guide_capability_route",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("ordinary explanatory question was reclassified")
        ),
    )

    status, payload = asyncio.run(_post_query(QUERY))

    assert status == 200
    assert payload["intent"] == "TOPICAL_INQUIRY"
    assert payload["processing"] == "basic_inquiry"
    assert payload["response"] == ANSWER
    assert len(payload["response"].split("\n\n")) == 3
    assert isinstance(payload.get("recommendation"), dict)
    assert payload["recommendation"] == {
        "title": CANONICAL_TITLE,
        "url": CANONICAL_URL,
    }
    assert payload["answer_basis"] == {
        "kind": "archive_supported",
        "label": "Informed by the Living Archive",
        "explanation": "A relevant Archive resource is available to explore the ideas behind this answer.",
    }
    assert "🏛️" not in payload["recommendation"]["title"]
    assert "&amp;" not in payload["recommendation"]["title"]
    assert payload.get("handoff") != "glossary"
    assert composition_calls == ["general_guide_composition"]




def test_archive_evidence_gaps_do_not_bypass_general_composition(monkeypatch):
    """Evidence flags limit Archive attribution, not general answers to public questions."""
    for flag in (
        "frame_neutral_evidence_unavailable",
        "question_structure_evidence_unavailable",
        "evidence_sufficiency_unavailable",
    ):
        composition_calls = _install_controlled_provider_and_retrieval(
            monkeypatch, {flag: True}
        )
        status, payload = asyncio.run(_post_query("How do I handle burnout as a manager? " + flag))
        assert status == 200
        assert payload["response"] == ANSWER
        assert composition_calls == ["general_guide_composition"]
        assert payload.get("recommendation") is None
        assert payload["answer_basis"]["kind"] == "general_knowledge"


def test_deterministic_burnout_recovery_is_useful_and_has_real_paragraph_breaks():
    result = use_main._basic_inquiry_round1_deterministic_response(
        "How do I handle burnout as a manager?", {}, {}
    )
    response = result["response"]
    assert "workload and recovery problem" in response
    assert "For example" in response
    assert r"\n\n" not in response
    assert len(response.split("\n\n")) == 3

def test_compound_stewardship_question_with_real_provider_bank_when_credentials_exist(monkeypatch):
    """Run the candidate request boundary against an actual configured Provider Bank.

    Retrieval is static so this test isolates generation/routing from Pinecone.
    Provider Bank transport is deliberately NOT mocked. It runs only in CI and
    skips when no supported provider is configured in the runner environment.
    """
    import os
    import provider_bank

    configured_credentials = any([
        os.getenv("GROQ_API_KEY"),
        os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY"),
        os.getenv("MISTRAL_API_KEY"),
        os.getenv("CLOUDFLARE_API_TOKEN") and os.getenv("CLOUDFLARE_ACCOUNT_ID"),
    ])
    if not configured_credentials:
        import pytest
        pytest.skip("No Provider Bank credentials are configured for isolated live-provider CI.")

    context = {
        "intent": "TOPICAL_INQUIRY",
        "authoritative_doorway": {
            "title": "🏛️Workshops &amp; Advisory",
            "url": "https://geralddaquila.com/workshops-advisory/",
        },
        "generation_authority_protected_docs": [
            {
                "title": "🏛️Workshops &amp; Advisory",
                "url": "https://geralddaquila.com/workshops-advisory/",
                "content": "Workshop and advisory services for teams and organizations.",
            },
            {
                "title": CANONICAL_TITLE,
                "url": CANONICAL_URL,
                "content": (
                    "Stewardship asks what we are responsible for and how we care "
                    "for what affects more than ourselves. It considers the effects "
                    "of our choices on people and systems beyond ourselves."
                ),
            }
        ],
    }
    monkeypatch.setattr(use_main.use_core, "fetch_canonical_context", lambda query: context)
    monkeypatch.setattr(use_main._base, "_inquiry_profile", lambda query: {})
    monkeypatch.setattr(use_main, "classify_safety", lambda query, history="": None)
    monkeypatch.setattr(use_main, "_basic_inquiry_requires_macro_routing", lambda query: False)
    monkeypatch.setattr(
        use_main,
        "_guide_capability_route",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("ordinary explanatory question was reclassified")
        ),
    )

    candidates = provider_bank.candidates(
        use_main.use_core, operation="general_guide_composition"
    )
    if not candidates:
        import pytest
        pytest.skip("Provider credentials exist, but no healthy eligible composition provider is available.")

    # This is an external-provider smoke test, not the deterministic request
    # contract suite. Bound it so an upstream outage cannot stall the entire
    # release workflow indefinitely; deterministic provider and boundary tests
    # below remain strict and offline.
    import pytest
    import threading
    completed = threading.Event()
    result = {}
    error = {}

    def _run_live_provider_smoke():
        try:
            result["value"] = asyncio.run(_post_query(QUERY))
        except BaseException as exc:
            error["value"] = exc
        finally:
            completed.set()

    # The provider transport is synchronous inside the ASGI test boundary, so
    # asyncio.wait_for cannot interrupt a blocked socket. Use a daemon thread
    # to enforce a real wall-clock bound without holding the CI process open.
    threading.Thread(target=_run_live_provider_smoke, daemon=True).start()
    if not completed.wait(45):
        pytest.skip("Live provider smoke test exceeded 45 seconds; upstream availability is transient.")
    if "value" in error:
        raise error["value"]
    status, payload = result["value"]

    if status == 503 and (
        payload.get("error_type") == "retryable_operation_failure"
        or "provider" in str(payload).casefold()
        or "composition_unavailable" in str(payload).casefold()
    ):
        pytest.skip("Provider Bank has no available live candidate; deterministic contract QA remains authoritative.")

    assert status == 200
    assert payload.get("intent") == "TOPICAL_INQUIRY"
    assert payload.get("processing") == "basic_inquiry"
    response = payload.get("response")
    assert isinstance(response, str) and len(response.strip()) >= 80
    assert len([p for p in response.split("\n\n") if p.strip()]) >= 2
    assert "glossary" not in str(payload.get("handoff") or "").casefold()
    recommendation = payload.get("recommendation")
    assert isinstance(recommendation, dict)
    assert recommendation.get("url") == CANONICAL_URL
    assert recommendation.get("title") == CANONICAL_TITLE


def test_model_selected_guide_node_cannot_bypass_explicit_destination_boundary(monkeypatch):
    """A provider-selected Glossary node must not swallow an explanatory question."""
    _install_controlled_provider_and_retrieval(monkeypatch)
    monkeypatch.setattr(
        use_main,
        "_guide_capability_route",
        lambda *args, **kwargs: {
            "route": "guide_node",
            "mode": "direct",
            "confidence": 1.0,
            "round1_interpretation": {"guide_node_id": "living-glossary"},
        },
    )

    status, payload = asyncio.run(_post_query(QUERY))

    assert status == 200
    assert payload["intent"] == "TOPICAL_INQUIRY"
    assert payload["processing"] == "basic_inquiry"
    assert len(payload["response"].strip()) >= 80
    assert payload.get("handoff") != "guide_node"
    assert payload["recommendation"] == {
        "title": CANONICAL_TITLE,
        "url": CANONICAL_URL,
    }


def test_bounded_stewardship_definition_keeps_native_glossary_handoff():
    status, payload = asyncio.run(_post_query("What is stewardship?"))

    assert status == 200
    assert payload["intent"] == "GLOSSARY_HANDOFF"
    assert payload["handoff"] == "glossary"
    assert payload["glossary_url"] == (
        "https://geralddaquila.com/glossary/?glossary_term=stewardship"
    )
    assert payload["response"] == ""

def test_source_specific_question_acknowledges_unavailable_archive_source(monkeypatch):
    """Specific-source requests preserve the evidence limit without passing rejected material."""
    seen = {}

    def source_limited_composition(**kwargs):
        seen["query"] = kwargs["query"]
        seen["context_data"] = kwargs["context_data"]
        seen["response"] = (
            "I cannot verify the exact claims of that particular article from the "
            "material available here. A general explanation would not establish "
            "what the article itself says."
        )
        return {
            "response": seen["response"],
            "provider": "controlled_test_provider",
            "model": "controlled_test_model",
            "response_shape": "direct",
        }

    _install_controlled_provider_and_retrieval(
        monkeypatch, {"evidence_sufficiency_unavailable": True}
    )
    monkeypatch.setattr(
        use_main.general_guide_composition, "compose", source_limited_composition
    )
    # Disable only capability routing for this test; evidence handling and the
    # ordinary request boundary remain exercised, without a destination handoff.
    monkeypatch.setattr(use_main, "_guide_capability_route", lambda *args, **kwargs: {})
    query = "How should I evaluate whether a specific article's claims about managerial burnout are supported? Please distinguish its own claims from general advice."
    status, payload = asyncio.run(_post_query(query))

    assert status == 200
    assert "cannot verify the exact claims" in seen["response"]
    assert seen["query"] == query
    assert not seen["context_data"].get("generation_authority_protected_docs")
    assert not seen["context_data"].get("question_authority_protected_docs")
    assert not seen["context_data"].get("context_blocks")
    assert payload.get("recommendation") is None

def test_provider_bank_exhaustion_uses_question_aware_general_recovery(monkeypatch):
    """Provider exhaustion retains useful guidance and actual paragraph breaks."""
    _install_controlled_provider_and_retrieval(
        monkeypatch, {"evidence_sufficiency_unavailable": True}
    )
    monkeypatch.setattr(
        use_main.general_guide_composition, "compose", lambda **kwargs: None
    )

    status, payload = asyncio.run(
        _post_query("How do I handle burnout as a manager?")
    )

    assert status == 200
    assert "workload and recovery problem" in payload["response"]
    assert "For example" in payload["response"]
    assert len(payload["response"].split("\n\n")) == 3
    assert r"\n\n" not in payload["response"]
    assert "I couldn't verify a reliable answer" not in payload["response"]
    assert payload.get("recommendation") is None

def test_supported_evidence_preserves_structured_recommendation_title_and_url(monkeypatch):
    """Evidence-supported answers retain navigation in its separate response field."""
    _install_controlled_provider_and_retrieval(monkeypatch)
    status, payload = asyncio.run(_post_query(QUERY))

    assert status == 200
    assert payload["response"] == ANSWER
    assert len(payload["response"].split("\n\n")) == 3
    assert payload["recommendation"] == {
        "title": CANONICAL_TITLE,
        "url": CANONICAL_URL,
    }



def test_canonical_search_recovery_reuses_the_same_relevance_gate(monkeypatch):
    context = {"intent": "TOPICAL_INQUIRY", "context_blocks": ""}
    monkeypatch.setattr(use_main._base, "_inquiry_profile", lambda query: {})
    monkeypatch.setattr(
        use_main,
        "_wordpress_search_canonical_candidates",
        lambda query, limit=5: [{
            "title": "Overwhelm & Burnout",
            "url": "https://geralddaquila.com/overwhelm-burnout/",
            "text": (
                "Burnout can follow prolonged strain and overextension. "
                "Burnout is not a personal failure; it is a signal that capacity "
                "and demands have become mismatched."
            ),
        }],
    )
    doorway = use_main._general_guide_authoritative_doorway(
        "How do I handle burnout as a manager?", context
    )
    assert doorway == {
        "title": "Overwhelm & Burnout",
        "url": "https://geralddaquila.com/overwhelm-burnout/",
    }

def test_provider_bank_exhaustion_reuses_frozen_reciprocity_gold_standard(monkeypatch):
    """Exercise the frozen approved answer through the existing ASGI request boundary."""
    from pathlib import Path

    fixture = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "tests"
            / "fixtures"
            / "general_guide_reciprocity_gold_standard.json"
        ).read_text(encoding="utf-8")
    )
    _install_controlled_provider_and_retrieval(
        monkeypatch, {"evidence_sufficiency_unavailable": True}
    )
    monkeypatch.setattr(
        use_main.general_guide_composition, "compose", lambda **kwargs: None
    )
    monkeypatch.setattr(use_main, "_guide_capability_route", lambda *args, **kwargs: {})

    status, payload = asyncio.run(_post_query(fixture["query"]))

    assert status == 200
    assert payload["response"] == fixture["expected_response"]
    assert len(payload["response"].split("\n\n")) == 3
    assert payload.get("recommendation") is None
    assert payload["answer_basis"]["kind"] == "general_knowledge"
    assert "provider" not in payload["response"].casefold()
    assert "canonical evidence" not in payload["response"].casefold()



def test_deterministic_fallback_semantic_matrix_preserves_topic_specificity():
    """Exercise topic-aware fallback branches without external providers or production quotas."""
    cases = [
        {
            "query": "What does reciprocity mean in the Living Archive?",
            "provider": "bounded_general_knowledge_recovery",
            "paragraphs": 3,
            "markers": ("mutual response", "neighbors might take turns", "debt ledger"),
        },
        {
            "query": "Explain stewardship in everyday life.",
            "provider": "bounded_general_knowledge_recovery",
            "paragraphs": 3,
            "markers": ("keeping a promise", "ordinary choices accumulate", "within your limits"),
        },
        {
            "query": "How do I handle burnout as a manager?",
            "provider": "bounded_general_knowledge_recovery",
            "paragraphs": 3,
            "markers": ("workload and recovery problem", "For example", "structural workload problem"),
        },
        {
            "query": "What is institutional responsibility?",
            "provider": "bounded_general_knowledge_recovery",
            "paragraphs": 3,
            "markers": ("organization", "public office repeatedly loses applications", "appropriate oversight"),
        },
        {
            "query": "What are political dynasties and what risks can they create?",
            "provider": "bounded_public_governance_recovery",
            "paragraphs": 3,
            "markers": ("families", "accountability can weaken", "those are claims that require evidence"),
        },
        {
            "query": "What is the relationship between personal agency and responsibility to others?",
            "provider": "calibrated_general_knowledge_recovery",
            "paragraphs": 3,
            "markers": ("interdependent aspects", "manager who exercises agency", "freedom meaningful"),
        },
        {
            "query": "How can I understand a difficult situation without rushing to judge?",
            "provider": "bounded_reflective_general_knowledge_recovery",
            "paragraphs": 2,
            "markers": ("separate what you know from what you think it means", "your own boundaries"),
        },
    ]

    for case in cases:
        result = use_main._basic_inquiry_round1_deterministic_response(
            case["query"], {}, {}
        )
        response = result["response"]
        paragraphs = [part for part in response.split("\\n\\n") if part.strip()]

        assert result["provider"] == case["provider"], case["query"]
        assert len(paragraphs) == case["paragraphs"], case["query"]
        for marker in case["markers"]:
            assert marker.casefold() in response.casefold(), (case["query"], marker)
        assert "I couldn't verify a reliable answer" not in response, case["query"]
        assert r"\\n\\n" not in response, case["query"]

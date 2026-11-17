import main


def _approved_node(**overrides):
    node = {
        "node_id": "spirituality-without-escapism",
        "title": "Spirituality Without Escapism: Staying Human During Awakening Narratives",
        "purpose": (
            "Help readers distinguish grounded hope and meaning from certainty-seeking "
            "or spiritual avoidance when navigating uncertainty."
        ),
        "asset_type": "canonical_essay",
        "canonical_url": (
            "https://geralddaquila.com/2026/11/10/"
            "spirituality-without-escapism-staying-human-during-awakening-narratives/"
        ),
        "access_class": "public",
        "status": "active",
    }
    node.update(overrides)
    return node


def test_reflective_balance_resolves_approved_node_with_renderer_rationale(monkeypatch):
    monkeypatch.setattr(main, "_guide_node_registry_snapshot", lambda: [_approved_node()])

    doorway = main._select_reflective_balance_doorway(
        "How can hope remain disciplined rather than naïve?"
    )

    assert doorway == {
        "title": "Spirituality Without Escapism: Staying Human During Awakening Narratives",
        "url": (
            "https://geralddaquila.com/2026/11/10/"
            "spirituality-without-escapism-staying-human-during-awakening-narratives/"
        ),
        "rationale": _approved_node()["purpose"],
    }


def test_reflective_balance_rejects_non_public_or_inactive_node(monkeypatch):
    monkeypatch.setattr(
        main,
        "_guide_node_registry_snapshot",
        lambda: [_approved_node(access_class="steward")],
    )
    assert main._select_reflective_balance_doorway(
        "How can hope remain disciplined rather than naïve?"
    ) is None

    monkeypatch.setattr(
        main,
        "_guide_node_registry_snapshot",
        lambda: [_approved_node(status="disabled")],
    )
    assert main._select_reflective_balance_doorway(
        "How can hope remain disciplined rather than naïve?"
    ) is None


def test_final_visitor_boundary_adds_doorway_without_rewriting_answer(monkeypatch):
    answer = (
        "Hope can be disciplined without becoming naïve when it stays answerable "
        "to reality. It does not require pretending that difficulties are smaller "
        "than they are, or treating a desired outcome as guaranteed."
    )
    monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda query: None)
    monkeypatch.setattr(main, "_guide_node_registry_snapshot", lambda: [_approved_node()])

    result = main._guide_finalize_visitor_payload(
        {"ok": True, "response": answer, "recommendation": None},
        "How can hope remain disciplined rather than naïve?",
    )

    assert result["response"] == answer
    assert result["recommendation"]["title"] == _approved_node()["title"]
    assert result["canonical_doorway"] == result["recommendation"]
    assert result["doorway_title"] == _approved_node()["title"]
    assert result["doorway_url"] == _approved_node()["canonical_url"]
    assert result["doorway_rationale"] == _approved_node()["purpose"]
    assert result["processing"] == "final_visitor_boundary_reflective_balance_doorway"

def test_hope_gold_star_is_exact_answer_authority_with_verified_doorway():
    standard = main._resolve_exact_guide_gold_standard(
        "How can hope remain disciplined rather than naïve?"
    )

    assert standard is not None
    assert standard["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert standard["forbids_doorway"] is False
    assert standard["doorway_title"] == (
        "Spirituality Without Escapism: Staying Human During Awakening Narratives"
    )
    assert standard["doorway_url"] == (
        "https://geralddaquila.com/2026/11/10/"
        "spirituality-without-escapism-staying-human-during-awakening-narratives/"
    )
    assert standard["doorway_rationale"].startswith(
        "This essay examines how the search for meaning and hope"
    )
    paragraphs = standard["expected_response"].split("\\n\\n")
    assert len(paragraphs) == 3
    assert "possibility" in paragraphs[0].lower()
    assert "revise expectations" in paragraphs[1].lower()
    assert "responsible next step" in paragraphs[2].lower()
    assert "artificial intelligence" not in standard["expected_response"].lower()


def test_exact_hope_gold_star_overrides_stale_answer_and_doorway_at_final_boundary():
    standard = main._resolve_exact_guide_gold_standard(
        "How can hope remain disciplined rather than naïve?"
    )
    assert standard is not None

    result = main._guide_finalize_visitor_payload(
        {
            "ok": True,
            "response": "A stale or provider-generated answer that does not meet the approved standard.",
            "recommendation": {
                "title": "Unrelated destination",
                "url": "https://geralddaquila.com/unrelated/",
                "rationale": "This is not the approved continuation.",
            },
        },
        "How can hope remain disciplined rather than naïve?",
    )

    assert result["response"] == standard["expected_response"]
    assert result["recommendation"] == {
        "title": standard["doorway_title"],
        "url": standard["doorway_url"],
        "rationale": standard["doorway_rationale"],
    }
    assert result["canonical_doorway"] == result["recommendation"]
    assert result["doorway_title"] == standard["doorway_title"]
    assert result["doorway_url"] == standard["doorway_url"]
    assert result["doorway_rationale"] == standard["doorway_rationale"]
    assert result["processing"] == "final_visitor_boundary_exact_gold_standard"


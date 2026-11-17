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

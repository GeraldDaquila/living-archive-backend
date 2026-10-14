"""Subject-discovery retrieval must separate search intent from the requested topic."""

import main


def test_extracts_subject_from_where_can_i_find_material_question():
    assert main._guide_subject_discovery_query(
        "Where can I find material about institutional responsibility?"
    ) == "institutional responsibility"


def test_extracts_subject_from_resource_and_information_variants():
    assert main._guide_subject_discovery_query(
        "Could you find resources on institutional accountability?"
    ) == "institutional accountability"
    assert main._guide_subject_discovery_query(
        "I need information regarding public governance."
    ) == "public governance"
    assert main._guide_subject_discovery_query(
        "Show me articles related to institutional trust"
    ) == "institutional trust"


def test_preserves_the_topic_without_rewriting_ordinary_questions():
    assert main._guide_subject_discovery_query(
        "Why does institutional responsibility matter?"
    ) == ""


def test_subject_query_does_not_hard_code_a_specific_archive_topic():
    assert main._guide_subject_discovery_query(
        "Where can I find essays about community accountability?"
    ) == "community accountability"
    assert main._guide_subject_discovery_query(
        "Where can I find documents about public health governance?"
    ) == "public health governance"



def test_subject_discovery_always_triggers_canonical_content_supplement():
    assert main._guide_requires_canonical_subject_supplement(
        False, "institutional responsibility"
    )
    assert main._guide_requires_canonical_subject_supplement(
        True, "institutional responsibility"
    )


def test_ordinary_queries_only_trigger_recovery_when_evidence_is_unavailable():
    assert main._guide_requires_canonical_subject_supplement(True, "")
    assert not main._guide_requires_canonical_subject_supplement(False, "")



def test_subject_discovery_uses_broader_candidate_recall_than_general_recovery():
    assert main._guide_subject_supplement_limit("institutional responsibility") == 10
    assert main._guide_subject_supplement_limit("public accountability") == 10
    assert main._guide_subject_supplement_limit("") == 3



def test_selected_canonical_doorway_can_support_discovery_when_general_sufficiency_is_too_strict(monkeypatch):
    doorway = {
        "title": "Governance & Decentralization",
        "url": "https://geralddaquila.com/2026/05/20/governance-decentralization/",
    }
    document = {
        "title": "Governance & Decentralization",
        "url": "https://geralddaquila.com/2026/05/20/governance-decentralization/",
        "text": "This canonical governance hub covers institutional accountability, transparency, public trust, and civic participation across institutions and societies.",
    }
    monkeypatch.setattr(
        main.use_core,
        "_question_evidence_fit_profile",
        lambda subject, candidate: (1, 1, 2, 2),
    )

    assert main._guide_selected_doorway_discovery_evidence(
        [document], "public accountability", doorway
    ) == [document]


def test_discovery_evidence_must_match_the_selected_canonical_url(monkeypatch):
    doorway = {
        "title": "Governance & Decentralization",
        "url": "https://geralddaquila.com/2026/05/20/governance-decentralization/",
    }
    unrelated = {
        "title": "Unrelated Resource",
        "url": "https://geralddaquila.com/unrelated/",
        "text": "A sufficiently long body that mentions accountability but is not the selected canonical doorway. " * 2,
    }
    monkeypatch.setattr(
        main.use_core,
        "_question_evidence_fit_profile",
        lambda subject, candidate: (3, 2, 2, 5),
    )

    assert main._guide_selected_doorway_discovery_evidence(
        [unrelated], "public accountability", doorway
    ) == []


def test_discovery_evidence_requires_direct_subject_fit(monkeypatch):
    doorway = {
        "title": "Governance & Decentralization",
        "url": "https://geralddaquila.com/2026/05/20/governance-decentralization/",
    }
    document = {
        "title": "Governance & Decentralization",
        "url": "https://geralddaquila.com/2026/05/20/governance-decentralization/",
        "text": "A sufficiently long page body with details that do not discuss the requested topic or its subject matter. " * 2,
    }
    monkeypatch.setattr(
        main.use_core,
        "_question_evidence_fit_profile",
        lambda subject, candidate: (0, 0, 0, 0),
    )

    assert main._guide_selected_doorway_discovery_evidence(
        [document], "public accountability", doorway
    ) == []



def test_discovery_answer_validator_rejects_external_search_advice(monkeypatch):
    doorway = {
        "title": "Governance & Decentralization",
        "url": "https://geralddaquila.com/2026/05/20/governance-decentralization/",
    }
    evidence = [{
        "title": "Governance & Decentralization",
        "url": doorway["url"],
        "text": "This canonical governance hub covers institutional accountability, public trust, civic participation, and distributed responsibility across institutions.",
    }]
    response = (
        "For public accountability, consult government oversight bodies, academic databases, "
        "Transparency International, and independent audit offices."
    )

    assert not main._guide_discovery_response_is_grounded(
        response, "public accountability", doorway, evidence
    )


def test_discovery_answer_validator_rejects_no-evidence_claims():
    doorway = {
        "title": "Governance & Decentralization",
        "url": "https://geralddaquila.com/2026/05/20/governance-decentralization/",
    }
    evidence = [{
        "title": doorway["title"],
        "url": doorway["url"],
        "text": "A long enough resource body discussing governance and institutional accountability, transparency, public trust, and civic participation.",
    }]

    assert not main._guide_discovery_response_is_grounded(
        "No specific Archive material was retrieved, but this resource may help.",
        "public accountability",
        doorway,
        evidence,
    )


def test_discovery_answer_validator_accepts_grounded_archive_resource():
    doorway = {
        "title": "Governance & Decentralization",
        "url": "https://geralddaquila.com/2026/05/20/governance-decentralization/",
    }
    evidence = [{
        "title": doorway["title"],
        "url": doorway["url"],
        "text": "A canonical governance hub covering institutional accountability, transparency, public trust, and civic participation.",
    }]

    assert main._guide_discovery_response_is_grounded(
        "The Archive's Governance & Decentralization hub covers institutional accountability and civic participation.",
        "public accountability",
        doorway,
        evidence,
    )


def test_deterministic_discovery_recovery_uses_selected_resource_content():
    doorway = {
        "title": "Governance & Decentralization",
        "url": "https://geralddaquila.com/2026/05/20/governance-decentralization/",
    }
    evidence = [{
        "title": doorway["title"],
        "url": doorway["url"],
        "text": (
            "This canonical hub explores governance systems and public trust. "
            "Its purpose is to establish foundational principles for decentralized governance, "
            "ethical leadership, distributed responsibility, institutional accountability, "
            "and regenerative models of collective coordination."
        ),
    }]

    response = main._guide_deterministic_discovery_response(
        "public accountability", doorway, evidence
    )

    assert "Governance & Decentralization" in response
    assert "accountability" in response
    assert "public accountability" in response
    assert "relevant entry point" in response

"""Contract tests for the non-secret ecosystem integration audit endpoint."""

import main
from main import ecosystem_integration_audit


def test_integration_audit_reports_runtime_registry_distinction():
    report = ecosystem_integration_audit()
    assert report["audit_contract"] == "ecosystem-integration-audit-v1"
    assert report["version"] == "v489.187"
    assert report["fingerprint"] == "USE-v489.187-hrn-return-search-recovery"
    assert report["fingerprint"]
    assert isinstance(report["capability_registry"], list)
    assert isinstance(report["runtime_adapters"], list)
    assert isinstance(report["direct_handoffs"], dict)


def test_integration_audit_does_not_misrepresent_catalogue_as_adapter():
    report = ecosystem_integration_audit()
    assert report["catalogue_mode"] == "direct_handoff_not_adapter"
    assert report["direct_handoffs"]["catalogue"] == "native_catalogue_search"
    assert report["direct_handoffs"]["systems_ph"] == "native_philippine_systems_landing"


def test_integration_audit_discloses_registry_adapter_gaps():
    report = ecosystem_integration_audit()
    assert "available_capabilities_missing_adapters" in report
    assert "adapters_without_capabilities" in report
    # A green registration report is not a substitute for visitor E2E.
    assert any("end-to-end" in item.lower() for item in report["limitations"])


def test_disagreement_does_not_invent_a_listening_topic_anchor():
    from main import _relational_return_topic_anchor

    anchor = _relational_return_topic_anchor(
        "One colleague holds to an agreed deadline while another points to changed scope.",
        "Clear communication of changes",
        "The original estimate did not include the added work.",
    )
    assert anchor == ""


def test_explicit_unheard_concern_still_adds_a_listening_topic_anchor():
    from main import _relational_return_topic_anchor

    anchor = _relational_return_topic_anchor(
        "I feel unheard when we disagree.",
        "Understand what happens in the conversation",
        "Listening and acknowledgment matter here.",
    )
    assert "Relational communication during disagreement" in anchor


def test_explicit_level_two_guide_node_returns_node_record_not_score(monkeypatch):
    node = {
        "node_id": "systems-stewardship",
        "title": "Systems Stewardship",
        "purpose": "A territory for systems stewardship and responsibility.",
        "semantic_hints": ["systems stewardship", "organizational patterns"],
        "discovery_level": 2,
    }
    monkeypatch.setattr(main, "_guide_node_registry_is_fresh", lambda: True)
    monkeypatch.setattr(main, "_guide_node_registry_snapshot", lambda: [node])

    activated = main._guide_node_semantic_activation(
        "Systems Stewardship",
        {},
        "guide",
    )

    assert activated == node


def test_heard_as_blame_does_not_add_listening_topic_anchor():
    from main import _relational_return_topic_anchor

    anchor = _relational_return_topic_anchor(
        "My partner and I keep having the same argument, even though we both want things to improve.",
        "Understand how raising an earlier hurt becomes a dispute about blame, without assuming either partner intends to hurt or dismiss the other.",
        "The argument changes direction when explaining an earlier hurt is heard as assigning blame.",
    )
    assert anchor == ""


def test_heard_as_blame_is_not_classified_as_a_listening_complaint():
    from main import _relational_communication_focus

    assert not _relational_communication_focus(
        "The argument changes direction when explaining an earlier hurt is heard as assigning blame."
    )
    assert _relational_communication_focus(
        "I feel unheard when my partner goes silent after an argument."
    )


def test_quoted_statements_do_not_merge_separate_topic_evidence():
    query = (
        "My partner and I keep having the same argument, even though we both say we want things to improve. "
        "Understand how raising an earlier hurt becomes a dispute about blame, without assuming either partner "
        "intends to hurt or dismiss the other. The argument changes direction when explaining an earlier hurt "
        "is heard as assigning blame."
    )
    self_sacrifice_article = {
        "title": "When Love Has Been Built on Your Self-Sacrifice",
        "text": (
            "You may think: “If I stop over-giving, they’ll feel hurt.” "
            "“If I set boundaries, I’ll seem selfish.” "
            "“If I change, I’ll damage the relationship.” "
            "But what you are really facing is this question: Can this relationship exist without my self-sacrifice holding it together? "
            "You are responsible for changing with honesty and care—not with blame, not with punishment, but with truth. "
            "There is a difference between attacking someone for the past and no longer participating in a pattern that harms you."
        ),
    }
    assert not main._relational_return_direct_topic_fit(query, self_sacrifice_article)
    assert not main._relational_return_earned_focus_fit(query, self_sacrifice_article)


def test_explicit_formation_entry_bypasses_ambiguous_model_route():
    query = "I want to enter stewardship formation and learn how to carry responsibility well."
    route = main._explicit_formation_entry_route(query)
    assert route is not None
    assert route["route"] == "formation"
    assert route["mode"] == "delegated_journey"
    assert route["source"] == "deterministic-explicit-formation-entry"
    assert route["round1_interpretation"]["presenting_situation"] == query


def test_formation_definition_question_is_not_forced_into_specialist_entry():
    route = main._explicit_formation_entry_route(
        "What is stewardship formation and why does it matter?"
    )
    assert route is None


def test_generated_observable_intention_language_does_not_create_discernment_focus():
    from main import _relational_return_topic_anchor

    anchor = _relational_return_topic_anchor(
        "My partner and I keep having the same argument, even though we both say we want things to improve.",
        "Understand how raising an earlier hurt becomes a dispute about blame, without assuming either partner intends to hurt or dismiss the other.",
        "This sequence is observable; each partner's intention remains unknown.",
    )
    assert "Relational discernment" not in anchor
    assert "Relational communication during disagreement" not in anchor


def test_explicit_perception_and_inference_question_still_gets_discernment_focus():
    from main import _relational_discernment_focus, _relational_return_topic_anchor

    query = "I can't tell whether what I'm sensing in this relationship is real or something I'm projecting."
    assert _relational_discernment_focus(query)
    anchor = _relational_return_topic_anchor(
        query,
        "Distinguish what I observed from what I inferred.",
        "What I infer may not match what happened.",
    )
    assert "Relational discernment" in anchor


def test_generic_communication_evidence_cannot_qualify_a_discernment_resource():
    from main import _relational_return_earned_focus_fit

    query = "I can't tell whether what I'm sensing in this relationship is real or something I'm projecting."
    broad_relationship_article = {
        "title": "When Love Has Been Built on Your Self-Sacrifice",
        "text": (
            "Many relationships form around roles we step into without realizing it. "
            "Listen without defensiveness. Acknowledge the imbalance and take responsibility."
        ),
    }
    assert not _relational_return_earned_focus_fit(query, broad_relationship_article)



def test_formation_preparation_intent_bypasses_general_navigator():
    query = "I want to prepare for stewardship responsibilities in a group. Where should I begin learning?"
    route = main._explicit_formation_entry_route(query)
    assert route is not None
    assert route["route"] == "formation"
    assert route["source"] == "deterministic-formation-preparation-entry"


def test_explanatory_stewardship_question_is_not_misrouted_to_formation():
    query = "What is stewardship and why does it matter now more than ever?"
    assert main._explicit_formation_entry_route(query) is None


def test_basic_inquiry_sanitizer_removes_html_and_decodes_entities():
    response = main._sanitize_basic_inquiry_response(
        "<p>It can be difficult &amp; confusing.</p><p><strong>One step</strong> is to name what changed.</p>"
    )
    assert "<p>" not in response
    assert "<strong>" not in response
    assert "&amp;" not in response
    assert "difficult & confusing" in response
    assert "One step is to name what changed." in response


def test_explicit_hypothetical_safety_calibration_does_not_fall_through_to_topical_inquiry():
    query = (
        "CALIBRATION TEST ONLY — not a real emergency: a hypothetical visitor says "
        "they may hurt themselves tonight. What should The Guide do, and what immediate support options should it offer?"
    )
    payload = main._hypothetical_safety_calibration_payload(query)
    assert payload is not None
    assert payload["intent"] == "SAFETY_CALIBRATION_INFORMATION"
    assert payload["safety_calibration"]["personal_crisis_detected"] is False
    assert payload["safety_calibration"]["location_required_for_local_contacts"] is True



def test_relational_return_rejects_broad_life_essay_for_repeated_argument():
    query = (
        "My partner and I keep having the same argument. When I raise a specific incident, "
        "they say I never let anything go, and we end up arguing about whether I may feel hurt."
    )
    broad_essay = {
        "title": "After Awakening, Life Still Happens",
        "text": "A reflection on spiritual awakening, everyday life, meaning, and change.",
    }
    assert not main._relational_return_direct_topic_fit(query, broad_essay)
    assert not main._relational_return_earned_focus_fit(query, broad_essay)



def test_formation_preparation_handoff_precedes_generic_navigator(monkeypatch):
    import asyncio
    import json

    query = "I want to prepare for stewardship responsibilities in a group. Where should I begin learning?"
    monkeypatch.setattr(
        main,
        "_formation_specialist_response",
        lambda query, history, route, request_id: {
            "response": "A preparation pathway can help make the responsibilities and learning needs clearer.",
            "formation_delegation": {
                "state": "open",
                "specialist_id": "formation",
                "doors": [
                    {"title": "Learning Arcs", "url": "https://geralddaquila.com/steward-access-12-learning-arcs/"}
                ],
            },
        },
    )

    body = json.dumps({"query": query, "session_id": "test-formation-precedence"}).encode()
    consumed = False
    sent = []

    async def receive():
        nonlocal consumed
        if not consumed:
            consumed = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    asyncio.run(main._use_request_boundary(
        {"type": "http", "method": "POST", "path": "/api/query", "headers": []},
        receive,
        send,
    ))

    status = next(message["status"] for message in sent if message["type"] == "http.response.start")
    payload = json.loads(next(message["body"] for message in sent if message["type"] == "http.response.body"))
    assert status == 200
    assert payload["intent"] == "FORMATION_HANDOFF"
    assert payload["formation_delegation"]["specialist_id"] == "formation"
    assert payload["route_source"] == "deterministic-formation-preparation-entry"


def test_basic_inquiry_rejects_copied_case_study_source_dump():
    response = (
        "The Archive material available here offers this starting point: "
        "“5. Case Studies and Real-World Applications. Consider Sarah, a 35-year-old project manager "
        "overwhelmed by work and family demands. By adopting mindfulness meditation and the Eisenhower Matrix…”"
    )
    assert main._basic_inquiry_has_source_dump(response)



def test_overwhelmed_support_recovery_does_not_reuse_archive_excerpt():
    query = "I feel overwhelmed and don't know who I can talk to about what I'm going through."
    recovery = main._basic_inquiry_round1_deterministic_response(
        query,
        {},
        {"context_blocks": ""},
    )
    response = recovery["response"]
    assert "you don't have to find the perfect person" in response
    assert not main._basic_inquiry_has_source_dump(response)



def test_relational_return_rejects_cognitive_dissonance_for_specific_repeated_hurt_argument():
    query = (
        "My partner and I keep having the same argument. When I raise a specific incident, "
        "they say I never let anything go, and we end up arguing about whether I may feel hurt."
    )
    broad_cognitive_dissonance = {
        "title": "Cognitive Dissonance: The Tension That Shapes Our Minds and Societies",
        "text": (
            "Cognitive dissonance describes discomfort arising from conflicting beliefs, "
            "attitudes, or behaviors. It explores decision-making, change, and social dynamics."
        ),
    }
    relevant_repair_resource = {
        "title": "Repair Before Withdrawal",
        "text": (
            "When partners argue about a hurt, the original incident can be displaced by blame. "
            "Relational repair begins when both people can return to the disagreement and hear "
            "what hurt without making the discussion about whether it should be raised."
        ),
    }

    assert not main._relational_return_direct_topic_fit(query, broad_cognitive_dissonance)
    assert not main._relational_return_earned_focus_fit(query, broad_cognitive_dissonance)
    assert main._relational_return_direct_topic_fit(query, relevant_repair_resource)



def test_explicit_archive_path_request_routes_to_native_navigator():
    query = "I need to find a path through the Archive about grief and meaning."
    assert main._is_navigator_orientation_request(query) is True


def test_explanatory_archive_topic_question_stays_with_general_guide():
    query = "What is stewardship and why does it matter now more than ever?"
    assert main._is_navigator_orientation_request(query) is False


def test_explore_next_archive_question_routes_to_native_navigator():
    query = "What should I explore next in the Living Archive?"
    assert main._is_navigator_orientation_request(query) is True



def test_explicit_glossary_entry_request_hands_off_to_native_glossary():
    query = "Take me to the glossary entry for stewardship."
    term = main._normalize_glossary_term(query)
    assert term == "stewardship"
    assert main._is_bounded_glossary_request(query, glossary_term=term) is True


def test_glossary_explanation_with_why_stays_with_general_guide():
    query = "What is stewardship and why does it matter now more than ever?"
    term = main._normalize_glossary_term(query)
    assert main._is_bounded_glossary_request(query, glossary_term=term) is False



def test_hypothetical_urgent_support_contact_calibration_is_recognized():
    query = (
        "CALIBRATION ONLY — hypothetical visitor needs urgent mental-health support "
        "and asks for verified local support contacts. Route to the Safety / Crisis tool; "
        "no real emergency is occurring."
    )
    payload = main._hypothetical_safety_calibration_payload(query)
    assert payload is not None
    assert payload["intent"] == "SAFETY_CALIBRATION_INFORMATION"
    assert payload["safety_calibration"]["personal_crisis_detected"] is False
    assert payload["safety_calibration"]["resources_resolved"] is False



def test_relational_return_uses_bounded_wp_search_after_focused_retrieval_misses(monkeypatch):
    calls = []
    relevant = {
        "title": "Four Horsemen of Relationships — Early Warning & Repair",
        "url": "https://geralddaquila.com/2025/10/08/t4-codex-four-horsemen-of-relationships-early-warning-repair/",
        "text": (
            "In relationships, criticism and defensiveness can escalate a disagreement. "
            "Repair begins by returning to the conflict and hearing what each person is saying."
        ),
    }
    monkeypatch.setattr(
        main,
        "_wordpress_search_canonical_candidates",
        lambda query, limit=3: calls.append((query, limit)) or [relevant],
    )
    monkeypatch.setattr(main, "_sanitize_outward_context", lambda query, docs, profile: docs)
    monkeypatch.setattr(
        main,
        "_canonical_primary_from_docs",
        lambda docs, query, profile: (
            {"title": docs[0]["title"], "url": docs[0]["url"]} if docs else None
        ),
    )

    original = "My partner and I keep having the same argument, even though we both want things to improve."
    direct = original + " The same argument keeps returning."
    primary, outward = main._relational_return_search_recovery(
        original,
        direct,
        {"primary": "relational", "relational": True, "action": "recommendation"},
    )

    assert calls == [("relationship repair", 5)]
    assert primary is not None
    assert primary["url"] == relevant["url"]
    assert outward == [relevant]


def test_relational_return_search_recovery_does_not_expand_unrelated_topics(monkeypatch):
    calls = []
    monkeypatch.setattr(
        main,
        "_wordpress_search_canonical_candidates",
        lambda query, limit=3: calls.append((query, limit)) or [],
    )
    primary, outward = main._relational_return_search_recovery(
        "What does stewardship mean?",
        "What does stewardship mean?",
        {"primary": "relational", "relational": True, "action": "recommendation"},
    )
    assert primary is None
    assert outward == []
    assert calls == []

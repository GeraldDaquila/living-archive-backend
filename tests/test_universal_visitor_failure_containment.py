from visitor_failure_recovery import compose_visitor_failure_recovery


def test_transformation_rebranding_question_gets_bounded_substantive_recovery():
    result = compose_visitor_failure_recovery(
        "When does transformation become mere rebranding?"
    )
    response = result["response"]
    assert "decision rights" in response
    assert "incentives" in response
    assert "durable" in response
    assert "not presented as a synthesis" not in response
    assert "related continuation, not evidence for this answer" not in response
    assert "services were unavailable" not in response
    assert "decision rights" in response
    assert "does not substantiate this general-knowledge answer" in result["basis_explanation"]


def test_unknown_question_gets_transparent_nonempty_recovery_not_fake_answer():
    result = compose_visitor_failure_recovery(
        "How should our town prepare for a changing climate?"
    )
    response = result["response"]
    assert response
    assert "couldn't complete the full answer" in response
    assert "don't want to invent" in response
    assert "not a substantive answer" in response
    assert "Living Archive" in result["basis_explanation"]


def test_recovery_preserves_question_context_without_echoing_or_mutating_it():
    question = "What makes institutional learning real?"
    result = compose_visitor_failure_recovery(question)
    assert question == "What makes institutional learning real?"
    assert "Your question is still intact" in result["response"]


def test_runtime_failure_branch_routes_through_shared_visitor_finalizer():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "main.py").read_text(
        encoding="utf-8"
    )
    start = source.index("# Universal visitor failure containment:")
    end = source.index("explicit_formation_route =", start)
    branch = source[start:end]
    assert "compose_visitor_failure_recovery(query)" in branch
    assert "_guide_finalize_visitor_payload(_visitor_payload, query)" in branch
    assert "return await _use_send_json(send, _visitor_payload, 200)" in branch
    assert branch.index("_guide_finalize_visitor_payload") < branch.index(
        "_use_send_json(send, _visitor_payload, 200)"
    )


def test_runtime_failure_branch_keeps_original_question_and_no_fabricated_destination():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "main.py").read_text(
        encoding="utf-8"
    )
    start = source.index("# Universal visitor failure containment:")
    end = source.index("explicit_formation_route =", start)
    branch = source[start:end]
    assert '"query": query' in branch
    assert '"recommendation": None' in branch
    assert '"canonical_doorway": None' in branch



def test_transformation_rebranding_selects_the_reviewed_learning_and_correctability_doorway(monkeypatch):
    import main

    query = "When does “transformation” become mere rebranding?"
    assert main._select_verified_doorway_conceptual_family(query) == "transformation_rebranding"

    payload = {
        "ok": True,
        "query": query,
        "intent": "TOPICAL_INQUIRY",
        # Deliberately inject the legacy visitor-facing outage paragraph:
        # the outer finalizer must repair already-composed recovery payloads too.
        "response": (
            compose_visitor_failure_recovery(query)["response"]
            + "\n\nThis is a bounded general-knowledge orientation because the Guide's "
            "live answer and canonical-retrieval services were unavailable on this attempt. "
            "It is not presented as a synthesis of verified Living Archive sources. "
            "Any separately selected Archive resource is a related continuation, not evidence for this answer."
        ),
        "recommendation": None,
        "canonical_doorway": None,
        "answer_basis": {
            "kind": "general_knowledge",
            "label": "Bounded recovery orientation",
            "explanation": compose_visitor_failure_recovery(query)["basis_explanation"],
        },
        "response_provenance": {
            "class": "visitor_failure_recovery",
            "provider": "provider_independent_visitor_recovery",
            "model": None,
            "quality_adjusted_llm_eligible": False,
            "llm_invoked": False,
        },
        "processing": "visitor_failure_containment",
        "route_source": "guide_basic_inquiry_recovery",
    }

    terminal_calls = []
    original_terminal_policy = main._guide_enforce_terminal_doorway_policy

    def observe_terminal_policy(candidate, candidate_query):
        terminal_calls.append(candidate_query)
        return original_terminal_policy(candidate, candidate_query)

    monkeypatch.setattr(main, "_guide_enforce_terminal_doorway_policy", observe_terminal_policy)
    finalized = main._guide_finalize_visitor_payload(payload, query)

    assert terminal_calls == [query]
    doorway = finalized["recommendation"]
    assert doorway["title"] == "When Experience Can Change Us: The Two Capacities of a Living System"
    assert doorway["url"] == "https://geralddaquila.com/when-experience-can-change-us-the-two-capacities-of-a-living-system/"
    assert "experience" in doorway["rationale"].casefold()
    assert "change how the system acts" in doorway["rationale"].casefold()
    assert finalized["canonical_doorway"] == doorway
    assert finalized["doorway_title"] == doorway["title"]
    assert finalized["doorway_url"] == doorway["url"]
    assert finalized["response_provenance"]["class"] == "visitor_failure_recovery"
    assert "not presented as a synthesis of verified Living Archive sources" not in finalized["response"]
    assert "related continuation, not evidence for this answer" not in finalized["response"]
    assert "services were unavailable" not in finalized["response"]
    assert "related continuation, not the evidence source" not in doorway["rationale"]
    assert "change how the system acts" in doorway["rationale"]


def test_transformation_rebranding_doorway_respects_explicit_no_handoff():
    import main

    query = "When does transformation become mere rebranding? No links or resources, please."
    payload = {
        "ok": True,
        "query": query,
        "intent": "TOPICAL_INQUIRY",
        "response": compose_visitor_failure_recovery(query)["response"],
        "recommendation": None,
        "canonical_doorway": None,
        "answer_basis": {"kind": "general_knowledge", "label": "Bounded recovery orientation"},
        "response_provenance": {"class": "visitor_failure_recovery"},
        "processing": "visitor_failure_containment",
    }
    finalized = main._guide_finalize_visitor_payload(payload, query)
    assert finalized["recommendation"] is None
    assert finalized["canonical_doorway"] is None
    assert finalized["doorway_decision"] == "omit"


def test_transformation_rebranding_selector_does_not_capture_personal_or_brand_refresh_questions():
    import main

    assert main._select_verified_doorway_conceptual_family(
        "When does personal transformation become mere rebranding?"
    ) != "transformation_rebranding"
    assert main._select_verified_doorway_conceptual_family(
        "How should I rebrand a small business?"
    ) != "transformation_rebranding"



def test_protected_core_blob_hash_tracks_the_reviewed_use_core_source():
    import hashlib
    from pathlib import Path

    import guide_runtime

    core_bytes = (Path(__file__).resolve().parents[1] / "use_core.py").read_bytes()
    actual_blob_sha = hashlib.sha1(
        f"blob {len(core_bytes)}\0".encode("utf-8") + core_bytes
    ).hexdigest()
    assert guide_runtime.EXPECTED_CORE_BLOB_SHA == actual_blob_sha



def test_main_and_guide_runtime_protected_core_hashes_match_current_use_core_blob():
    import hashlib
    from pathlib import Path

    import guide_runtime
    import main

    core_bytes = (Path(__file__).resolve().parents[1] / "use_core.py").read_bytes()
    actual_blob_sha = hashlib.sha1(
        f"blob {len(core_bytes)}\0".encode("utf-8") + core_bytes
    ).hexdigest()
    assert main.EXPECTED_CORE_BLOB_SHA == actual_blob_sha
    assert guide_runtime.EXPECTED_CORE_BLOB_SHA == actual_blob_sha

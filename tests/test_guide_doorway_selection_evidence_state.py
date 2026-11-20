"""Doorway selection must be evaluated independently of answer formation."""

import deterministic_answer_recovery as recovery
import main


QUERY = "What counts as evidence, interpretation, hypothesis, and normative judgment?"


def _base_payload():
    return {
        "response": (
            "Evidence, interpretation, hypothesis, and normative judgment are "
            "distinct but connected forms of reasoning."
        ),
        "processing": "guide_epistemic_category_distinction_deterministic",
        "answer_basis": {"kind": "general_knowledge", "label": "General knowledge"},
        "recommendation": None,
        "canonical_doorway": None,
    }


def _disable_other_doorway_sources(monkeypatch):
    monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda _q: None)
    monkeypatch.setattr(main, "_select_verified_doorway_conceptual_family", lambda _q: None)
    monkeypatch.setattr(main, "_select_guide_node_fallback_doorway", lambda _q: None)
    monkeypatch.setattr(recovery, "registered_recovery_recommendation", lambda _q: None)


def test_epistemic_answer_runs_independent_canonical_selection_without_retrieval_context(monkeypatch):
    _disable_other_doorway_sources(monkeypatch)
    candidate = {
        "title": "The Living Archive Navigator: Volume III – Knowledge & Sensemaking",
        "url": "https://geralddaquila.com/the-living-archive-navigator-volume-iii/",
        "rationale": (
            "A possible next step for examining how knowledge, evidence, "
            "interpretation, and sensemaking are connected."
        ),
    }
    calls = []

    def select(query, context):
        calls.append(query)
        assert context.get("generation_authority_protected_docs") is None
        context["_doorway_selection_trace"].update({
            "status": "VERIFIED_RELEVANT_DESTINATION",
            "canonical_search_attempted": True,
        })
        return candidate

    monkeypatch.setattr(main, "_general_guide_authoritative_doorway", select)
    result = main._guide_restore_verified_doorway(_base_payload(), QUERY)

    assert calls == [QUERY]
    assert result["response"] == _base_payload()["response"]
    assert result["recommendation"] == candidate
    assert result["doorway_decision"] == "selected"
    assert result["doorway_selection_status"] == "VERIFIED_RELEVANT_DESTINATION"
    assert result["doorway_selection_evaluated"] is True
    assert result["doorway_selection_source"] == "canonical_evidence_selector"


def test_no_relevant_destination_is_recorded_only_after_bounded_search_completes(monkeypatch):
    _disable_other_doorway_sources(monkeypatch)

    def select(query, context):
        context["_doorway_selection_trace"].update({
            "status": "NO_RELEVANT_CANDIDATE_AFTER_BOUNDED_SEARCH",
            "canonical_search_attempted": True,
            "candidates_considered": 4,
        })
        return None

    monkeypatch.setattr(main, "_general_guide_authoritative_doorway", select)
    result = main._guide_restore_verified_doorway(_base_payload(), QUERY)

    assert result["recommendation"] is None
    assert result["doorway_decision"] == "omit"
    assert result["doorway_selection_status"] == "NO_RELEVANT_DESTINATION_AFTER_BOUNDED_SEARCH"
    assert result["doorway_selection_evaluated"] is True
    assert "bounded canonical candidate search" in result["doorway_omission_reason"]


def test_retrieval_failure_is_not_mislabeled_as_verified_omission(monkeypatch):
    _disable_other_doorway_sources(monkeypatch)

    def select(query, context):
        context["_doorway_selection_trace"].update({
            "status": "RETRIEVAL_OR_VERIFICATION_FAILURE",
            "canonical_search_attempted": True,
            "error_type": "TimeoutError",
        })
        return None

    monkeypatch.setattr(main, "_general_guide_authoritative_doorway", select)
    result = main._guide_restore_verified_doorway(_base_payload(), QUERY)

    assert result["recommendation"] is None
    assert result["doorway_selection_status"] == "RETRIEVAL_OR_VERIFICATION_FAILURE"
    assert result["doorway_selection_evaluated"] is False
    assert "not certified as an intentional omission" in result["doorway_omission_reason"]


def test_explicit_visitor_refusal_remains_terminal_without_running_selector(monkeypatch):
    _disable_other_doorway_sources(monkeypatch)

    def forbidden(*args, **kwargs):
        raise AssertionError("An explicit no-handoff instruction is terminal.")

    monkeypatch.setattr(main, "_general_guide_authoritative_doorway", forbidden)
    query = QUERY + " Please do not include a doorway or link."
    result = main._guide_enforce_terminal_doorway_policy(_base_payload(), query)

    assert result["recommendation"] is None
    assert result["doorway_decision"] == "omit"
    assert result["doorway_selection_status"] == "AUTHORIZED_OMISSION"
    assert result["doorway_selection_evaluated"] is False
    assert result["doorway_selection_source"] == "explicit_visitor_refusal"

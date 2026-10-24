"""Regression tests for the final conceptual Guide grounding boundary.

These are structural source contracts: a conceptual question must not remain
eligible for generic prose merely because a weak or unrelated doorway exists.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"
SOURCE = MAIN.read_text(encoding="utf-8")
LIMITATION_SOURCE = (ROOT / "guide_direct_attribute_evidence.py").read_text(encoding="utf-8")


def _final_conceptual_gate():
    start = SOURCE.index(
        "# Final corpus-boundary invariant for conceptual/explanatory questions."
    )
    end = SOURCE.index(
        "# Expose a small, deterministic provenance contract", start
    )
    return SOURCE[start:end]


def test_conceptual_guard_covers_role_purpose_and_significance_queries():
    assert "_is_conceptual_explanatory_request(query)" in _final_conceptual_gate()
    for query in (
        "What is the role of trust in community stewardship?",
        "What is the purpose of reciprocity in a community?",
        "What is the significance of human development?",
    ):
        assert query in SOURCE


def test_conceptual_response_gate_requires_selected_canonical_source_body():
    gate = _final_conceptual_gate()
    assert "generation_authority_protected_docs" in gate
    assert "generation_evidence_docs" in gate
    assert "_conceptual_source_body" in gate
    assert "_conceptual_supported" in gate
    assert "_conceptual_best_doc" in gate
    assert "_conceptual_best_coverage >= 1.0" in gate
    assert "_has_relationship_signal" in gate


def test_conceptual_response_gate_fails_closed_without_relevant_body_even_if_doorway_exists():
    gate = _final_conceptual_gate()
    assert "if not _conceptual_supported or archive_evidence_unavailable:" in gate
    assert "response = _archive_limitation_response(query)" in gate
    assert "authoritative_doorway = None" in gate
    assert 'composition_context["evidence_sufficiency_unavailable"] = True' in gate


def test_conceptual_response_gate_does_not_relabel_general_knowledge_as_archive_supported():
    gate = _final_conceptual_gate()
    assert "_conceptual_source_body" in gate
    assert "_conceptual_supported" in gate
    assert "answer_basis" not in gate  # provenance remains assigned downstream


def test_archive_limitation_is_honest_and_offers_a_non_claiming_next_step():
    start = LIMITATION_SOURCE.index("def archive_limitation_response():")
    end = LIMITATION_SOURCE.index("\n\ndef select_authoritative_doorway", start)
    response_contract = LIMITATION_SOURCE[start:end]
    assert "haven’t found enough support" in response_contract
    assert "within the Archive" in response_contract
    assert "outside knowledge" in response_contract
    assert "narrowing the question" in response_contract
    assert "recommendation" not in response_contract


def test_conceptual_questions_trigger_canonical_body_retrieval_even_when_initial_retrieval_looks_sufficient():
    supplement = SOURCE[SOURCE.index("def _guide_requires_canonical_subject_supplement"):SOURCE.index("def _guide_subject_supplement_limit")]
    assert "conceptual_inquiry=False" in supplement
    assert "or conceptual_inquiry" in supplement
    assert "_is_conceptual_explanatory_request(query)" in SOURCE[SOURCE.index("def _basic_inquiry_response"):SOURCE.index("# Recovery may establish a qualifying doorway")]
    assert "or _is_conceptual_explanatory_request(query)" in SOURCE[SOURCE.index("def _basic_inquiry_response"):SOURCE.index("# Recovery may establish a qualifying doorway")]


def test_conceptual_doorway_is_aligned_to_vetted_retrieved_canonical_evidence():
    start = SOURCE.index("if not recovery_insufficient and recovered_docs:")
    end = SOURCE.index("# Recovery may establish a qualifying doorway", start)
    recovery = SOURCE[start:end]
    assert "_guide_align_registered_discovery_doorway(" in recovery
    assert "_is_conceptual_explanatory_request(query)" in recovery
    assert "composition_context[\"authoritative_doorway\"] = evidence_doorway" in recovery


def test_conceptual_retrieval_keeps_the_central_concept_in_the_canonical_search_query():
    start = SOURCE.index("def _wordpress_search_canonical_candidates")
    end = SOURCE.index("def _guide_", start)
    searcher = SOURCE[start:end]
    assert "_is_conceptual_explanatory_request(query)" in searcher
    assert "focus_terms = list(_subject_terms(conceptual_match.group(1)))" in searcher
    assert "context_terms = list(_subject_terms(conceptual_match.group(2)))" in searcher
    assert "selected[:3]" in searcher
    assert "community" in searcher


def test_canonical_page_body_fetch_has_enough_time_for_live_wordpress_responses():
    selected_fetch = SOURCE[SOURCE.index("def _wordpress_fetch_selected_canonical_body"):SOURCE.index("def _wordpress_search_canonical_candidates")]
    search_fetch = SOURCE[SOURCE.index("def _wordpress_search_canonical_candidates"):SOURCE.index("def _comparative_subject_terms")]
    assert "urlopen(request, timeout=5.0)" in selected_fetch
    assert "urlopen(request, timeout=5.0)" in search_fetch


def test_conceptual_search_diagnostic_uses_the_selected_query_not_fallback_local_state():
    start = SOURCE.index("def _wordpress_search_canonical_candidates")
    end = SOURCE.index("def _comparative_subject_terms")
    searcher = SOURCE[start:end]
    assert 'search_terms={len(search_text.split())}' in searcher
    assert 'search_terms={len(indexed_terms[:2])}' not in searcher


def test_conceptual_recovery_diagnostic_records_exception_reason_for_structural_failures():
    assert 'The Guide evidence recovery failed safely: {type(exc).__name__}: {exc}.' in SOURCE


def test_conceptual_grounding_selects_doorway_from_vetted_evidence_without_discovery_registry_gate():
    start = SOURCE.index("if not recovery_insufficient and recovered_docs:")
    end = SOURCE.index("# Recovery may establish a qualifying doorway", start)
    recovery = SOURCE[start:end]
    assert "_general_guide_authoritative_doorway(" in recovery
    assert '{"generation_authority_protected_docs": recovered_docs}' in recovery
    assert "_guide_align_registered_discovery_doorway(" not in recovery[:recovery.index("if discovery_subject:")]


def test_conceptual_grounding_pairs_the_best_vetted_body_with_its_exact_destination():
    start = SOURCE.index("    _conceptual_inquiry = _is_conceptual_explanatory_request(query)")
    end = SOURCE.index("# Expose a small, deterministic provenance contract", start)
    gate = SOURCE[start:end]
    assert '"generation_authority_protected_docs"' in gate
    assert "_conceptual_best_doc" in gate
    assert "_conceptual_coverage >= (2 / 3)" in gate
    assert '"title": _conceptual_best_doc.get("title")' in gate
    assert '"url": _conceptual_best_doc.get("url") or _conceptual_best_doc.get("canonical_url")' in gate

 
def test_conceptual_grounding_allows_bounded_synthesis_across_vetted_canonical_bodies():
    start = SOURCE.index("    _conceptual_inquiry = _is_conceptual_explanatory_request(query)")
    end = SOURCE.index("# Expose a small, deterministic provenance contract", start)
    gate = SOURCE[start:end]
    assert "_conceptual_combined_body" in gate
    assert '"generation_authority_protected_docs"' in gate
    assert "len(_conceptual_terms) >= 2" in gate
    assert "_conceptual_coverage >= (2 / 3)" in gate


def test_conceptual_grounding_failure_diagnostic_reports_bounded_coverage_state():
    start = SOURCE.index("The Guide conceptual boundary: vetted canonical evidence set")
    end = SOURCE.index("\n\n    # Expose a small, deterministic provenance contract", start)
    diagnostic = SOURCE[start:end]
    assert "coverage:{_conceptual_coverage:.3f}" in diagnostic
    assert "vetted_docs:{len(_conceptual_authority_docs)}" in diagnostic
    assert "usable_docs:{len(_conceptual_combined_body)}" in diagnostic


def test_conceptual_grounding_preserves_upstream_evidence_failure_as_fail_closed():
    start = SOURCE.index("        if not _conceptual_supported or archive_evidence_unavailable:")
    end = SOURCE.index("# Expose a small, deterministic provenance contract", start)
    gate = SOURCE[start:end]
    assert "response = _archive_limitation_response(query)" in gate
    assert "authoritative_doorway = None" in gate
    assert 'composition_context.pop("authoritative_doorway", None)' in gate


def test_practical_stewardship_guard_cannot_override_a_conceptual_question_after_recovery():
    start = SOURCE.index("if (\n        _is_practical_stewardship_question(query)", SOURCE.index("def _basic_inquiry_response"))
    end = SOURCE.index("# Subject-discovery prose must be independent", start)
    guard = SOURCE[start:end]
    assert "and not _is_conceptual_explanatory_request(query)" in guard
    assert "and not general_guide_composition.is_conceptual_relationship_question(query)" in guard
    assert "archive_evidence_unavailable = True" in guard
    assert "composition_context[\"evidence_sufficiency_unavailable\"] = True" in guard


def test_practical_deterministic_route_does_not_bypass_conceptual_recovery():
    start = SOURCE.index("    if (\n        _is_practical_stewardship_question(query)", SOURCE.index("def _basic_inquiry_response"))
    end = SOURCE.index("    elif reasoning_mode == \"deterministic_only\"", start)
    guard = SOURCE[start:end]
    assert "and not _is_conceptual_explanatory_request(query)" in guard
    assert "and not general_guide_composition.is_conceptual_relationship_question(query)" in guard
    assert "_basic_inquiry_round1_deterministic_response(" in guard


def test_conceptual_recovery_clears_upstream_flags_only_after_all_content_gates_pass():
    start = SOURCE.index("if not recovery_insufficient and recovered_docs:")
    end = SOURCE.index("# Recovery may establish a qualifying doorway", start)
    recovery = SOURCE[start:end]
    assert "if not recovery_question_unavailable and recovered_docs:" in recovery
    assert "archive_evidence_unavailable = False" in recovery
    assert "for flag in (" in recovery
    assert "frame_neutral_evidence_unavailable" in recovery
    assert "evidence_sufficiency_unavailable" in recovery
    assert "question_evidence_fit_unavailable" in recovery


def test_query_aware_conceptual_term_extraction_excludes_generic_and_context_terms():
    # The final guard must distinguish the actual concepts from the grammatical
    # frame, and preserve context-bearing phrases rather than treat single-word
    # overlap as proof of a relationship.
    start = SOURCE.index("        _conceptual_terms = {", SOURCE.index("# Final corpus-boundary invariant"))
    end = SOURCE.index("\n\n        # Conceptual answers may need synthesis", start)
    extraction = SOURCE[start:end]
    assert '"role"' in extraction
    assert '"community"' not in extraction or "len(token) > 3" in extraction
    assert "token not in" in extraction


def test_deterministic_stewardship_fallback_excludes_conceptual_questions():
    start = SOURCE.index("def _basic_inquiry_round1_deterministic_response")
    end = SOURCE.index("# This recovery is deliberately modest.", start)
    fallback = SOURCE[start:end]
    assert "and not _is_conceptual_explanatory_request(query)" in fallback
    assert "and not general_guide_composition.is_conceptual_relationship_question(query)" in fallback
    assert '"bounded_practical_stewardship_recovery"' in fallback


def test_conceptual_relationship_grounding_requires_all_key_concepts_in_one_source():
    start = SOURCE.index("        _conceptual_subject_phrases =", SOURCE.index("# Final corpus-boundary invariant"))
    end = SOURCE.index("        _conceptual_source_body =", start)
    gate = SOURCE[start:end]
    assert '("trust", "community", "stewardship")' in gate
    assert "_doc_coverage >= 1.0" in gate
    assert "_has_relationship_signal" in gate
    assert "_conceptual_best_doc is not None" in gate


def test_conceptual_provider_exhaustion_uses_sentences_from_the_vetted_canonical_source():
    start = SOURCE.index("# Final corpus-boundary invariant for conceptual/explanatory questions.")
    end = SOURCE.index("# Expose a small, deterministic provenance contract", start)
    gate = SOURCE[start:end]
    assert "_conceptual_body_only" in gate
    assert "_ordered_conceptual_docs" in gate
    assert "_trust_sentence" in gate
    assert "_community_sentence" in gate
    assert "_stewardship_sentence" in gate
    assert "bounded synthesis of the cited Archive material" in gate
    assert "vetted source did not provide extractable" in gate


def test_conceptual_questions_expand_canonical_candidate_recall():
    helper_start = SOURCE.index("def _guide_subject_supplement_limit")
    helper_end = SOURCE.index("def _guide_discovery_evidence_grade", helper_start)
    helper = SOURCE[helper_start:helper_end]
    assert "conceptual_inquiry=False" in helper
    assert "or conceptual_inquiry" in helper
    assert "return 10 if (" in helper
    recovery_start = SOURCE.index("if _guide_requires_canonical_subject_supplement")
    recovery_end = SOURCE.index("# Recovery may establish a qualifying doorway", recovery_start)
    recovery = SOURCE[recovery_start:recovery_end]
    assert "_guide_subject_supplement_limit(" in recovery
    assert "_is_conceptual_explanatory_request(query)" in recovery

"""Regression tests for the final conceptual Guide grounding boundary.

These are structural source contracts: a conceptual question must not remain
eligible for generic prose merely because a weak or unrelated doorway exists.
"""
import re
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
        "What is the cosmology of the Living Archive?",
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
    assert "if not _conceptual_human_voice_supported" in gate
    assert "response = _archive_limitation_response(query)" in gate
    assert "authoritative_doorway = None" in gate
    assert 'composition_context.pop("authoritative_doorway", None)' in gate


def test_explicit_glossary_navigation_overrides_conceptual_guard_without_redirecting_conceptual_questions():
    # A concept question containing glossary vocabulary remains a General Guide
    # inquiry unless the visitor explicitly requests the Glossary destination.
    conceptual = "What is the role of trust in community stewardship?"
    explicit_pattern = r"\b(?:take me to|take me directly to|open|show me|go to|navigate to|find|access)\b.{0,60}\bglossary\b"
    assert not re.search(explicit_pattern, conceptual, re.I)

    query = "Please take me to the glossary."
    explicit = bool(re.search(explicit_pattern, query, re.I))
    assert explicit


def test_conceptual_response_gate_does_not_relabel_general_knowledge_as_archive_supported():
    gate = _final_conceptual_gate()
    assert "_conceptual_source_body" in gate
    assert "_conceptual_supported" in gate
    assert "answer_basis" not in gate  # provenance remains assigned downstream


def test_archive_limitation_is_honest_and_offers_a_non_claiming_next_step():
    start = LIMITATION_SOURCE.index("def archive_limitation_response(")
    end = LIMITATION_SOURCE.index("\n\ndef select_authoritative_doorway", start)
    response_contract = LIMITATION_SOURCE[start:end]
    assert "haven’t found enough support" in response_contract
    assert "within the Archive" in response_contract
    assert "outside knowledge" in response_contract
    assert "narrowing the " in response_contract
    assert "question to a specific term" in response_contract
    assert "recommendation" not in response_contract


def test_conceptual_questions_trigger_canonical_body_retrieval_even_when_initial_retrieval_looks_sufficient():
    supplement = SOURCE[SOURCE.index("def _guide_requires_canonical_subject_supplement"):SOURCE.index("def _guide_subject_supplement_limit")]
    assert "conceptual_inquiry=False" in supplement
    assert "or conceptual_inquiry" in supplement
    recovery = SOURCE[SOURCE.index("def _basic_inquiry_response"):SOURCE.index("# Recovery may establish a qualifying doorway")]
    assert "_is_conceptual_explanatory_request(query)" in recovery
    assert "or _is_conceptual_explanatory_request(query)" in recovery


def test_conceptual_doorway_is_aligned_to_vetted_retrieved_canonical_evidence():
    start = SOURCE.index("if not recovery_insufficient and recovered_docs:")
    end = SOURCE.index("# Recovery may establish a qualifying doorway", start)
    recovery = SOURCE[start:end]
    assert "_guide_align_registered_discovery_doorway(" in recovery
    assert "_is_conceptual_explanatory_request(query)" in recovery
    assert 'composition_context["authoritative_doorway"] = evidence_doorway' in recovery


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
    assert "_conceptual_best_coverage >= 1.0" in gate
    assert '"title": _conceptual_recommendation_doc.get("title")' in gate
    assert '"url": _conceptual_recommendation_doc.get("url") or _conceptual_recommendation_doc.get("canonical_url")' in gate


def test_conceptual_grounding_allows_bounded_synthesis_across_vetted_canonical_bodies():
    start = SOURCE.index("    _conceptual_inquiry = _is_conceptual_explanatory_request(query)")
    end = SOURCE.index("# Expose a small, deterministic provenance contract", start)
    gate = SOURCE[start:end]
    assert "_conceptual_combined_body" in gate
    assert '"generation_authority_protected_docs"' in gate
    assert "_has_relationship_signal" in gate
    assert "_conceptual_best_coverage >= 1.0" in gate


def test_conceptual_grounding_failure_diagnostic_reports_question_matched_recovery_state():
    gate = _final_conceptual_gate()
    assert "The Guide conceptual boundary: no question-matched canonical " in gate
    assert "sentences; returned the Archive-only limitation." in gate
    assert "evidence_sufficiency_unavailable" in gate


def test_conceptual_grounding_fails_closed_when_vetted_human_voice_evidence_is_missing():
    start = SOURCE.index("        if not _conceptual_human_voice_supported", SOURCE.index("# Final corpus-boundary invariant for conceptual/explanatory questions."))
    end = SOURCE.index("# Expose a small, deterministic provenance contract", start)
    gate = SOURCE[start:end]
    assert "response = _archive_limitation_response(query)" in gate
    assert "archive_evidence_unavailable = True" in gate
    assert "authoritative_doorway = None" in gate
    assert 'composition_context.pop("authoritative_doorway", None)' in gate


def test_practical_stewardship_guard_cannot_override_a_conceptual_question_after_recovery():
    start = SOURCE.index("if (\n        _is_practical_stewardship_question(query)", SOURCE.index("def _basic_inquiry_response"))
    end = SOURCE.index("# Subject-discovery prose must be independent", start)
    guard = SOURCE[start:end]
    assert "and not _is_conceptual_explanatory_request(query)" in guard
    assert "and not general_guide_composition.is_conceptual_relationship_question(query)" in guard
    assert "archive_evidence_unavailable = True" in guard
    assert 'composition_context["evidence_sufficiency_unavailable"] = True' in guard


def test_practical_deterministic_route_does_not_bypass_conceptual_recovery():
    start = SOURCE.index("    if (\n        _is_practical_stewardship_question(query)", SOURCE.index("def _basic_inquiry_response"))
    end = SOURCE.index('    elif reasoning_mode == "deterministic_only"', start)
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


def test_conceptual_grounding_pairs_trust_community_in_one_source_and_allows_separate_stewardship_source():
    start = SOURCE.index("        _conceptual_subject_phrases =", SOURCE.index("# Final corpus-boundary invariant"))
    end = SOURCE.index("        _conceptual_source_body =", start)
    gate = SOURCE[start:end]
    assert '("trust", "community", "stewardship")' in gate
    assert "_conceptual_vetted_docs.append({" in gate
    assert '{"trust", "community"}.issubset(_present_subjects)' in gate
    assert "and _has_relationship_signal" in gate
    assert "if _doc_coverage >= 1.0 and _has_relationship_signal:" not in gate


def test_conceptual_synthesis_uses_vetted_evidence_but_not_audit_style_quotation_collage():
    gate = _final_conceptual_gate()
    assert "_conceptual_trust_doc" in gate
    assert "_trust_sentence" in gate
    assert "_community_sentence" in gate
    assert "_stewardship_doc" in gate
    assert "_stewardship_sentence" in gate
    assert "if _trust_sentence and _community_sentence and _stewardship_doc and _stewardship_sentence:" in gate
    assert "if not _conceptual_human_voice_supported" in gate


def test_conceptual_provider_exhaustion_fallback_preserves_the_guides_human_voice():
    start = SOURCE.index("# Final corpus-boundary invariant for conceptual/explanatory questions.")
    end = SOURCE.index("# Expose a small, deterministic provenance contract", start)
    gate = SOURCE[start:end]
    response_start = gate.index('                response = (', gate.index('_trust_title = re.sub'))
    response_end = gate.index('\n                )', response_start) + len('\n                )')
    response = gate[response_start:response_end]
    assert "Trust helps people in a community rely on one another." in response
    assert "Think of a shared garden" in response
    assert "_trust_title" in response
    assert "_stewardship_title" in response
    assert "canonical source" not in response
    assert "bounded synthesis" not in response
    assert "verbatim" not in response
    assert "✨" not in response
    assert "_trust_title = re.sub(" in gate


def test_conceptual_human_voice_fallback_is_rejected_only_when_source_gates_fail():
    gate = _final_conceptual_gate()
    assert "_conceptual_human_voice_supported = bool(" in gate
    assert "_conceptual_supported" in gate
    assert "and _trust_sentence" in gate
    assert "and _community_sentence" in gate
    assert "and _stewardship_doc" in gate
    assert "and _stewardship_sentence" in gate
    assert "and authoritative_doorway" in gate
    assert "and not direct_attribute_evidence_missing" in gate
    assert "if not _conceptual_human_voice_supported" in gate
    assert "if not _conceptual_supported or archive_evidence_unavailable:" not in gate


def test_final_visitor_boundary_runs_after_canonical_evidence_gate():
    gate = _final_conceptual_gate()
    support_start = gate.index("_conceptual_human_voice_supported = bool(")
    boundary_start = gate.index("# Final human-voice boundary for conceptual relationship questions.")
    fail_closed_start = gate.index("if not _conceptual_human_voice_supported", support_start)
    boundary = gate[boundary_start:fail_closed_start]
    assert support_start < boundary_start < fail_closed_start
    assert "if _conceptual_human_voice_supported:" in boundary
    assert "Trust helps people in a community rely on one another." in boundary
    assert "It gives " in boundary
    assert "Think of a shared garden." in boundary
    assert "Stewardship is tending the " in boundary
    response_start = boundary.index("response = _sanitize_basic_inquiry_response(")
    visitor_response = boundary[response_start:]
    assert "_final_trust_title" not in visitor_response
    assert "_final_stewardship_title" not in visitor_response
    assert "canonical source" not in boundary
    assert "bounded synthesis" not in boundary
    assert "\\n\\n" in boundary


def test_basic_inquiry_request_id_is_unconditional_after_response_contracts():
    start = SOURCE.index("def _basic_inquiry_response(")
    end = SOURCE.index("def _v48831_basic_inquiry_seam_self_audit(", start)
    body = SOURCE[start:end]
    request_id_lines = [
        line for line in body.splitlines()
        if 'request_id = "basic-" + hashlib.sha1(' in line
    ]
    assert len(request_id_lines) == 1
    assert request_id_lines[0].startswith('    request_id = "basic-"')
    assert not request_id_lines[0].startswith('        request_id = "basic-"')
    responsibility_guard = body.index("if general_guide_composition._requires_responsibility_boundary_answer(query)")
    assert body.index('request_id = "basic-"') > responsibility_guard


def test_conceptual_fallback_preserves_reciprocity_subject_instead_of_reusing_trust_template():
    source = SOURCE
    gate_start = source.index("_conceptual_human_voice_supported = bool(")
    gate = source[gate_start:gate_start + 10000]
    assert '_conceptual_query_normalized = re.sub' in gate
    assert 'reciproc(?:ity|al)' in gate
    assert '_compose_provider_exhaustion_recovery(' in gate
    assert 'conceptual_subject_recovery' in gate
    assert 'Think of a shared garden' in gate


def test_general_conceptual_recovery_matches_vetted_source_sentences_to_question():
    gate = _final_conceptual_gate()
    assert "General conceptual recovery: answer from relevant sentences" in gate
    assert "_generic_query_terms" in gate
    assert "_generic_sentence_candidates" in gate
    assert "_generic_hits" in gate
    assert "vetted canonical bodies" in gate
    assert "question-matched canonical " in gate


def test_general_conceptual_recovery_does_not_infer_archive_doctrine_from_doorway_title():
    gate = _final_conceptual_gate()
    assert "do not infer Archive doctrine from a title or doorway alone" in gate
    assert 'if _generic_selected and _generic_query_terms:' in gate
    assert "if authoritative_doorway:" in gate
    assert "response = _archive_limitation_response(query)" in gate


def test_general_conceptual_recovery_preserves_separate_verified_doorway_and_provenance():
    gate = _final_conceptual_gate()
    assert 'composition_context["conceptual_subject_recovery"] = "vetted_sentence_synthesis"' in gate
    assert 'composition_context["authoritative_doorway"] = authoritative_doorway' in gate
    assert 'composition_context.pop("evidence_sufficiency_unavailable", None)' in gate


def test_cosmology_query_has_bounded_metaphysical_vocabulary_bridge():
    gate = _final_conceptual_gate()
    assert '"cosmology": {"metaphysics", "worldview", "creation", "universe", "origins"}' in gate
    assert "_generic_expanded_terms.update(_generic_concept_aliases.get(_generic_term, set()))" in gate
    assert "do not infer Archive doctrine from a title or doorway alone" in gate


def test_concept_alias_expansion_does_not_raise_single_concept_evidence_threshold():
    gate = _final_conceptual_gate()
    assert "_generic_original_query_terms = set(_generic_query_terms)" in gate
    assert "_generic_min_hits = 1 if len(_generic_original_query_terms) <= 1 else 2" in gate
    assert "Alias expansion broadens candidate discovery; it must not inflate" in gate


def test_direct_cosmology_question_enters_conceptual_retrieval_path():
    detector_start = SOURCE.index("def _is_conceptual_explanatory_request")
    detector_end = SOURCE.index("# Structural routing invariant", detector_start)
    detector = SOURCE[detector_start:detector_end]
    assert "cosmology|worldview|metaphysics|ontology" in detector
    assert "What is the cosmology of the Living Archive?" in SOURCE


def test_conceptual_recovery_uses_human_opening_not_internal_archive_classification():
    gate = _final_conceptual_gate()
    assert "One useful place to begin is with how our view of the world" in gate
    assert "The Archive’s material offers this starting point:" not in gate
    assert "question-matched canonical " in gate
    assert "do not infer Archive doctrine from a title or doorway alone" in gate

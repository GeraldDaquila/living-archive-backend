"""Regression contract for human-development recovery and Archive doorway."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "main.py").read_text(encoding="utf-8")


def _recovery_block():
    start = SOURCE.index("# Human development is a broad, answerable public concept")
    end = SOURCE.index('elif not _conceptual_human_voice_supported and not locals().get("conceptual_subject_recovery"):', start)
    return SOURCE[start:end]


def test_human_development_gets_a_substantive_general_answer_without_archive_disclaimer():
    recovery = _recovery_block()
    assert "Human development is more than growing older" in recovery
    assert "Its significance lies in what those capacities make possible" in recovery
    assert "Human development is therefore both personal and shared" in recovery
    assert "I have not verified a Living Archive text" not in recovery
    assert "archive_evidence_unavailable = False" in recovery


def test_relevant_vetted_human_development_resource_is_preserved_as_a_doorway():
    recovery = _recovery_block()
    assert 're.search(r"\\bhuman development\\b", str(_doc.get("title") or ""), re.I)' in recovery
    assert 're.search(r"\\bfirst institution\\b", str(_doc.get("title") or ""), re.I)' in recovery
    assert '_normalize_authoritative_recommendation({' in recovery
    assert 'composition_context["authoritative_doorway"] = authoritative_doorway' in recovery


def test_doorway_is_removed_when_no_vetted_relevant_canonical_resource_exists():
    recovery = _recovery_block()
    assert 'composition_context.pop("authoritative_doorway", None)' in recovery
    assert 'composition_context.pop("authoritative_doorway_title", None)' in recovery


def test_general_conceptual_fail_closed_behavior_remains_for_other_topics():
    start = SOURCE.index('elif not _conceptual_human_voice_supported and not locals().get("conceptual_subject_recovery"):', SOURCE.index("# Human development is a broad, answerable public concept"))
    end = SOURCE.index("# Expose a small, deterministic provenance contract", start)
    remaining_gate = SOURCE[start:end]
    assert "response = _archive_limitation_response(query)" in remaining_gate
    assert "archive_evidence_unavailable = True" in remaining_gate


def test_established_general_facts_use_a_bounded_provider_independent_recovery():
    start = SOURCE.index("def _established_general_knowledge_recovery(query):")
    end = SOURCE.index("\ndef _basic_inquiry_response(", start)
    resolver = SOURCE[start:end]
    assert "water_boiling_point_sea_level" in resolver
    assert "At sea level, water boils at 100°C (212°F)" in resolver
    assert "standard atmospheric pressure" in resolver
    assert "meter_centimeter_conversion" in resolver
    assert "One meter equals 100 centimeters." in resolver
    assert "return None" in resolver


def test_matched_general_fact_bypasses_direct_attribute_guard_but_unlisted_attributes_do_not():
    resolver_call = SOURCE.index(
        "general_knowledge_recovery = _established_general_knowledge_recovery(query)"
    )
    guard = SOURCE.index("direct_attribute_evidence_missing = (", resolver_call)
    guard_block = SOURCE[guard:SOURCE.index("# Subject discovery", guard)]
    assert resolver_call < guard
    assert "_direct_attribute_evidence_missing(query, authoritative_doorway)" in guard_block
    assert "and general_knowledge_recovery is None" in guard_block


def test_general_fact_answer_is_applied_before_conceptual_only_grounding():
    recovery = SOURCE.index("if general_knowledge_recovery is not None:")
    conceptual_gate = SOURCE.index(
        "_conceptual_inquiry = _is_conceptual_explanatory_request(query)", recovery
    )
    assert recovery < conceptual_gate
    block = SOURCE[recovery:conceptual_gate]
    assert "response = _sanitize_basic_inquiry_response(" in block
    assert 'composition_context["general_knowledge_recovery"] = general_knowledge_recovery["fact_id"]' in block
    assert 'composition_context.pop("authoritative_doorway", None)' in block
    assert 'composition_context.pop("authoritative_doorway_title", None)' in block
    assert "authoritative_doorway = None" in block
    assert "archive_evidence_unavailable = False" in block
    assert "The Guide general-knowledge boundary: answered a registered stable fact" in block


def test_final_answer_basis_remains_general_knowledge_for_matched_fact():
    final_guard = SOURCE.index(
        "# Re-evaluate after every downstream gate has had the opportunity to"
    )
    final_attribute_check = SOURCE.index(
        "direct_attribute_evidence_missing = (", final_guard
    )
    final_provenance = SOURCE.index(
        'if general_knowledge_recovery is not None:',
        SOURCE.index("# Expose a small, deterministic provenance contract for the visitor UI."),
    )
    final_payload = SOURCE.index('    payload = {', final_provenance)
    attribute_check_block = SOURCE[
        final_attribute_check:SOURCE.index(
            "# Direct-attribute questions may not fall through", final_attribute_check
        )
    ]
    provenance_block = SOURCE[final_provenance:final_payload]
    assert "and general_knowledge_recovery is None" in attribute_check_block
    assert '"kind": "general_knowledge"' in provenance_block
    assert "not attributed to the Living Archive" in provenance_block
    assert 'elif direct_attribute_evidence_missing:' in provenance_block


def test_registered_general_fact_skips_conceptual_only_archive_gate():
    resolver = SOURCE.index("general_knowledge_recovery = _established_general_knowledge_recovery(query)")
    conceptual_gate = SOURCE.index(
        "if _conceptual_inquiry and general_knowledge_recovery is None:",
        resolver,
    )
    assert resolver < conceptual_gate
    assert "if _conceptual_inquiry and general_knowledge_recovery is None:" in SOURCE
    assert "response = _archive_limitation_response(query)" in SOURCE[
        conceptual_gate:SOURCE.index(
            "# Expose a small, deterministic provenance contract for the visitor UI.",
            conceptual_gate,
        )
    ]

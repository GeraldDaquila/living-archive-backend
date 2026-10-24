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


def test_water_boiling_point_gets_a_direct_general_knowledge_answer():
    assert 're.search(r"\\bboil(?:ing)? point\\b", _normalize_query(query), re.I)' in SOURCE
    assert "At sea level, water boils at 100°C (212°F)" in SOURCE
    assert "standard atmospheric pressure" in SOURCE
    assert 'composition_context["general_knowledge_recovery"] = "water_boiling_point"' in SOURCE


def test_water_boiling_point_recovery_does_not_invent_archive_doorway():
    start = SOURCE.index('general_knowledge_recovery"] = "water_boiling_point"')
    block = SOURCE[start-1000:start+200]
    assert 'composition_context.pop("authoritative_doorway", None)' in block
    assert 'composition_context.pop("authoritative_doorway_title", None)' in block
    assert "archive_evidence_unavailable = False" in block

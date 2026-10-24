"""Regression contract for human-development conceptual recovery and voice."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "main.py").read_text(encoding="utf-8")


def _recovery_block():
    start = SOURCE.index("# Human development is a broad, answerable public concept")
    end = SOURCE.index('elif not _conceptual_human_voice_supported and not locals().get("conceptual_subject_recovery"):', start)
    return SOURCE[start:end]


def test_human_development_gets_a_substantive_general_answer_without_archive_support():
    recovery = _recovery_block()
    assert "Human development is more than growing older" in recovery
    assert "Its significance lies in what those capacities make possible" in recovery
    assert "Human development is therefore both personal and shared" in recovery
    assert "not verified a Living Archive text" in recovery
    assert "archive_evidence_unavailable = False" in recovery


def test_human_development_recovery_does_not_keep_an_unverified_archive_doorway():
    recovery = _recovery_block()
    assert "authoritative_doorway = None" in recovery
    assert 'composition_context.pop("authoritative_doorway", None)' in recovery
    assert 'composition_context.pop("authoritative_doorway_title", None)' in recovery


def test_general_conceptual_fail_closed_behavior_remains_for_other_topics():
    start = SOURCE.index('elif not _conceptual_human_voice_supported and not locals().get("conceptual_subject_recovery"):', SOURCE.index("# Human development is a broad, answerable public concept"))
    end = SOURCE.index("# Expose a small, deterministic provenance contract", start)
    remaining_gate = SOURCE[start:end]
    assert "response = _archive_limitation_response(query)" in remaining_gate
    assert "archive_evidence_unavailable = True" in remaining_gate

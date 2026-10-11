"""Regression contract for USE v489.93 passive friendship routing.

Checks the production decision function for the exact missed lived-experience query
and verifies that definition-only and explicit Archive-search requests remain bounded.
"""
import re
from pathlib import Path

import main as use_main

SOURCE = Path(__file__).resolve().parents[1] / "main.py"
TEXT = SOURCE.read_text(encoding="utf-8")

TARGET = "I am struggling with a friendship where I want to be understood but also need boundaries."


def _function_body(name: str, next_marker: str) -> str:
    start = TEXT.index(f"def {name}(")
    end = TEXT.index(next_marker, start)
    return TEXT[start:end]


def test_passive_friendship_boundary_cues_are_present():
    assert r'\b(?:a|this|our|my)\s+friendship\b' in TEXT
    assert r'\b(?:i|we)\s+(?:want|need|hope|wish)\s+to\s+be\s+(?:understood|heard|seen|respected)\b' in TEXT


def test_exact_passive_friendship_query_opens_hrn_boundary():
    decision = use_main._relational_boundary_decision(TARGET)
    assert decision["open"] is True
    assert decision["reason"] == "lived_relational_structure"
    assert decision["signals"]["first_person"] is True
    assert decision["signals"]["counterpart"] is True
    assert decision["signals"]["inquiry"] is True


def test_explanatory_and_archive_queries_do_not_open_hrn_boundary():
    explanatory = use_main._relational_boundary_decision(
        "What is a relationship and why are relationships important?"
    )
    archive_search = use_main._relational_boundary_decision(
        "Can you find an article in the Living Archive about friendship and boundaries?"
    )
    assert explanatory["open"] is False
    assert archive_search["open"] is False
    assert archive_search["reason"] == "bounded_archive_or_definition_request"


def test_bounded_archive_and_definition_exclusions_remain():
    body = _function_body("_relational_boundary_decision", "_route_probe_lived_relational =")
    assert "if bounded or definition:" in body
    assert "bounded_archive_or_definition_request" in body


def test_version_integrity_is_sequential():
    assert 'APP_VERSION = "v489.93"' in TEXT
    assert 'DEPLOYMENT_FINGERPRINT = "USE-v489.93-relational-passive-voice-boundary"' in TEXT
    assert 'CANONICAL_BUILD_ID = "USE-BUILD-v489.93-relational-passive-voice-boundary"' in TEXT

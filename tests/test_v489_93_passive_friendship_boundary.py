"""Regression contract for USE v489.93 passive friendship routing.

This file deliberately checks the exact live regression and conservative exclusions
without importing the 250 KB production main module (whose startup intentionally
performs live dependency audits).
"""
import re
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "main.py"
TEXT = SOURCE.read_text(encoding="utf-8")


def _function_body(name: str, next_marker: str) -> str:
    start = TEXT.index(f"def {name}(")
    end = TEXT.index(next_marker, start)
    return TEXT[start:end]


def test_passive_friendship_boundary_cues_are_present():
    assert r'\b(?:a|this|our|my)\s+friendship\b' in TEXT
    assert r'\b(?:i|we)\s+(?:want|need|hope|wish)\s+to\s+be\s+(?:understood|heard|seen|respected)\b' in TEXT


def test_passive_friendship_probe_is_a_startup_invariant():
    assert (
        'I am struggling with a friendship where I want to be understood but also need boundaries.'
        in TEXT
    )
    assert (
        'passive friendship/boundaries inquiry did not open HRN'
        in TEXT
    )


def test_bounded_archive_and_definition_exclusions_remain():
    body = _function_body("_relational_boundary_decision", "_route_probe_lived_relational =")
    assert 'if bounded or definition:' in body
    assert 'bounded_archive_or_definition_request' in body


def test_version_integrity_is_sequential():
    assert 'APP_VERSION = "v489.93"' in TEXT
    assert 'DEPLOYMENT_FINGERPRINT = "USE-v489.93-relational-passive-voice-boundary"' in TEXT
    assert 'CANONICAL_BUILD_ID = "USE-BUILD-v489.93-relational-passive-voice-boundary"' in TEXT

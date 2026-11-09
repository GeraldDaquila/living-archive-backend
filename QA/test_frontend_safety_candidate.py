from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "wordpress" / "candidates" / "living-archive-guide-v489.313-safety-location-confirmation-candidate.js"

def source():
    return CANDIDATE.read_text(encoding="utf-8")

def test_candidate_contains_confirmation_contract():
    s = source()
    assert "It looks like you may be in " in s
    assert "Is that correct?" in s
    assert "['Yes', 'No']" not in s  # contract file is intentionally isolated from production UI implementation

def test_candidate_uses_browser_locale_only_as_hint():
    s = source()
    assert "navigator.language" in s
    assert "Intl.DisplayNames" in s

def test_candidate_declares_manual_fallback_and_no_proxy_location():
    s = source()
    assert "reveal manual country fallback" in s
    assert "ip_country" not in s
    assert "request.remote_addr" not in s

def test_candidate_preserves_opening_sequence_contract():
    s = source()
    assert "openingLocationParagraphRemoved: true" in s

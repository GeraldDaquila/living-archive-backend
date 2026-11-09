from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "wordpress" / "candidates" / "living-archive-guide-v489.313-safety-location-confirmation-candidate.js"

def source():
    return CANDIDATE.read_text(encoding="utf-8")

def test_candidate_parses_as_complete_artifact_contract():
    s = source()
    assert len(s) > 50000
    assert "function syncSafetyLocationFields()" in s

def test_location_confirmation_is_present():
    s = source()
    assert "It looks like you may be in " in s
    assert "Is that correct?" in s
    assert "['Yes', 'No']" in s

def test_yes_and_no_paths_are_explicit():
    s = source()
    assert "guideSafetyCountry = inferred" in s
    assert "addManualFallback();" in s

def test_browser_locale_is_only_a_hint_source():
    s = source()
    assert "navigator.language" in s
    assert "Intl.DisplayNames" in s
    assert "request.remote_addr" not in s

def test_old_opening_hotline_paragraph_is_removed_by_naturalizer():
    s = source()
    assert "text.replace(/\\s*I don't yet have a verified local hotline" in s

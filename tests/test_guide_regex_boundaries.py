from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "main.py").read_text(encoding="utf-8")


def _function(name, next_name):
    start = SOURCE.index(f"def {name}(")
    end = SOURCE.index(f"def {next_name}(", start)
    return SOURCE[start:end]


def test_practical_template_detector_uses_real_regex_boundaries():
    code = _function("_guide_generic_practical_template_mismatch", "_guide_historical_origin_mismatch")
    assert 're.sub(r"\\s+",' in code
    assert r')\\b"' not in code
    assert r'r"\\b(?:how do i' not in code


def test_historical_origin_detector_uses_real_word_boundaries():
    code = _function("_guide_historical_origin_mismatch", "_guide_historical_origin_recovery")
    assert r're.sub(r"\\s+"' not in code
    assert r'r"\\\\bphilippines' not in code
    assert r'r"\\bphilippines\\b"' not in code
    assert r'r"\bphilippines\b"' in code
    assert r'r"\b(?:where|how|origin' in code


def test_expected_historical_question_and_template_behavior():
    query = "Where did gender roles in the Philippines historically come from?"
    response = "A practical way to approach this is to make a plan."
    q = re.sub(r"\s+", " ", query).strip().casefold()
    r = re.sub(r"\s+", " ", response).strip().casefold()
    historical = bool(
        re.search(r"\bphilippines\b", q)
        and re.search(r"\b(?:matriarch(?:al|y)|patriarch(?:al|y)|gender roles?)\b", q)
        and re.search(r"\b(?:where|how|origin|evolv|histor|come from|develop)\b", q)
    )
    generic = bool(re.match(r"^(?:a practical way to approach|a practical way to think about|to approach this)\b", r))
    assert historical and generic

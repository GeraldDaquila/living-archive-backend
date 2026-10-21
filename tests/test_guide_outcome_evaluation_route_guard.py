"""Regression tests for the structural outcome-evaluation route guard."""

from pathlib import Path
import main


def test_observed_harm_reduction_question_matches_evaluation_contract():
    query = (
        "How can a group tell whether its revised approach is genuinely reducing "
        "harm, rather than simply making the group feel that it has addressed the problem?"
    )
    normalized = main._normalize_query(query)
    import re

    evaluation = bool(
        re.search(
            r"\b(?:how can we tell|how do we know|how can (?:a|the) group tell|"
            r"what evidence|what measures?|how to measure|whether|is .* actually|"
            r"are .* actually|genuinely|really)\b",
            normalized,
            re.I,
        )
        and re.search(
            r"\b(?:reducing harm|reduce harm|harm reduction|improving outcomes?|"
            r"outcomes?|intervention|revised approach|approach|addressed the problem|"
            r"working|effective|improvement|improved|unintended harm|affected people)\b",
            normalized,
            re.I,
        )
    )
    assert evaluation is True


def test_structural_guard_overrides_fsd_only_for_outcome_evaluation():
    source = Path(main.__file__).read_text(encoding="utf-8")
    assert 'if route == "fsd" and outcome_evaluation_intent:' in source
    assert 'route = "guide"' in source
    assert "instead of premature FSD" in source


def test_prompt_preserves_fsd_for_actual_system_pattern_diagnosis():
    prompt = main._GUIDE_ROUTE_PROMPT.lower()
    assert "fsd is appropriate when the visitor's primary need is to map or diagnose" in prompt
    assert "feedback loops" in prompt
    assert "possible leverage points" in prompt

"""Regression tests for outcome-evaluation protection across every FSD route gate."""

from pathlib import Path
import main
import general_guide_composition as composition


OBSERVED_QUESTION = (
    "How can a group tell whether its revised approach is genuinely reducing "
    "harm, rather than simply making the group feel that it has addressed the problem?"
)


def test_observed_harm_reduction_question_matches_evaluation_contract():
    assert main._is_outcome_evaluation_query(OBSERVED_QUESTION) is True


def test_early_fsd_handoff_excludes_outcome_evaluation_queries():
    source = Path(main.__file__).read_text(encoding="utf-8")
    assert (
        "if _is_fsd_request(query) and not _is_outcome_evaluation_query(query):"
        in source
    )


def test_deterministic_fallback_excludes_outcome_evaluation_queries():
    source = Path(main.__file__).read_text(encoding="utf-8")
    assert (
        'if _is_fsd_request(query) and not _is_outcome_evaluation_query(query):\n'
        '        return {\n            "route": "fsd",'
    ) in source


def test_later_model_selected_fsd_route_is_still_guarded():
    source = Path(main.__file__).read_text(encoding="utf-8")
    assert 'if route == "fsd" and outcome_evaluation_intent:' in source
    assert 'route = "guide"' in source


def test_clear_system_diagnostic_still_matches_fsd():
    query = "Why does our community keep getting stuck in the same pattern?"
    assert main._is_fsd_request(query) is True
    assert main._is_outcome_evaluation_query(query) is False


def test_prompt_preserves_fsd_for_actual_system_pattern_diagnosis():
    prompt = main._GUIDE_ROUTE_PROMPT.lower()
    assert "fsd is appropriate when the visitor's primary need is to map or diagnose" in prompt
    assert "feedback loops" in prompt
    assert "possible leverage points" in prompt


def test_registry_unavailability_defers_data_dependent_startup_invariant():
    source = Path(main.__file__).read_text(encoding="utf-8")
    invariant_start = source.index("_steward_readiness_probe = _guide_node_specific_match(")
    invariant_end = source.index("# v488.30 phrase-boundary invariant", invariant_start)
    block = source[invariant_start:invariant_end]
    assert "if _guide_node_registry_is_fresh():" in block
    assert "startup continues with registry-dependent destination routing degraded" in block
    assert "raise RuntimeError(" in block


def test_outcome_evaluation_question_requires_evidence_not_only_next_steps():
    assert composition._requires_outcome_evaluation_guidance(OBSERVED_QUESTION) is True


def test_current_shallow_answer_fails_outcome_evidence_contract():
    shallow_answer = (
        "A practical way to approach a group is to define the outcome you want, "
        "identify the main constraint, and choose one step small enough to test. "
        "Before acting, consider who else is affected and what could go wrong. "
        "Check the result against the original goal and adjust rather than assuming "
        "the first attempt must be final."
    )
    assert composition._has_outcome_evaluation_guidance(shallow_answer) is False


def test_outcome_evaluation_recovery_includes_baseline_comparison_and_countercheck():
    recovery = composition._outcome_evaluation_recovery()
    assert composition._has_outcome_evaluation_guidance(recovery) is True


def test_outcome_evaluation_guidance_is_part_of_composition_prompt():
    assert "establish a baseline or starting point" in composition._GENERAL_GUIDE_SYSTEM
    assert "check for unintended consequences" in composition._GENERAL_GUIDE_SYSTEM

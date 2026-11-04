from pathlib import Path


def test_provider_contract_rejections_emit_bounded_class_and_reason():
    source = Path("provider_bank.py").read_text(encoding="utf-8")
    assert 'rejection_class=' in source
    assert '"json_or_parse"' in source
    assert '"visitor_surface"' in source
    assert '"grounding_or_provenance"' in source
    assert '"response_shape"' in source
    assert "contract_reason = str(exc)" in source
    assert ", error=contract_rejection" in source
    assert 're.sub(r"\\\\s+", " ", last_error)[:220]' not in source


def test_auto_mode_logs_selected_deterministic_path_on_provider_exhaustion():
    source = Path("main.py").read_text(encoding="utf-8")
    assert 'pathway=deterministic_recovery' in source
    assert 'reason=provider_bank_exhausted' in source
    assert 'The Guide Final Pathway:' in source


def test_auto_mode_logs_selected_deterministic_path_on_composition_exception():
    source = Path("main.py").read_text(encoding="utf-8")
    assert 'reason=composition_exception:' in source
    assert 'mode=auto, pathway=deterministic_recovery, provider=none, model=none' in source


def test_provider_contract_validation_remains_strict():
    source = Path("general_guide_composition.py").read_text(encoding="utf-8")
    assert 'raise ValueError("general composition exposed internal implementation language")' in source
    assert 'raise ValueError("general composition embedded a navigation URL in visitor prose")' in source
    assert 'if title and title not in titles:' in source


def test_general_guide_candidate_timing_is_observable():
    source = Path("provider_bank.py").read_text(encoding="utf-8")
    assert 'operation in {"hrn_perception", "general_guide_composition"}' in source
    assert 'USE provider bank candidate outcome: operation=' in source
    assert 'outcome=failure, category=' in source
    assert 'outcome=contract_rejection' in source
    assert 'elapsed_seconds=' in source


def test_general_guide_reserves_budget_for_independent_fallback():
    source = Path("provider_bank.py").read_text(encoding="utf-8")
    assert "GENERAL_GUIDE_FAST_FAILURE_WINDOW_SECONDS = 8.0" in source
    assert "GENERAL_GUIDE_PRIMARY_CALL_TIMEOUT_SECONDS = 3.0" in source
    assert "GENERAL_GUIDE_FALLBACK_CALL_TIMEOUT_SECONDS = 4.0" in source

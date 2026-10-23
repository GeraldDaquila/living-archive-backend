from pathlib import Path


def test_provider_contract_rejections_emit_bounded_class_and_reason():
    source = Path("provider_bank.py").read_text(encoding="utf-8")
    assert 'rejection_class=' in source
    assert '"json_or_parse"' in source
    assert '"visitor_surface"' in source
    assert '"grounding_or_provenance"' in source
    assert '"response_shape"' in source
    assert 're.sub(r"\\\\s+", " ", last_error)[:220]' in source


def test_auto_mode_logs_fail_closed_path_on_provider_exhaustion():
    source = Path("main.py").read_text(encoding="utf-8")
    assert 'pathway=fail_closed' in source
    assert 'reason=provider_bank_exhausted' in source
    assert 'The Guide Final Pathway:' in source


def test_auto_mode_logs_fail_closed_path_on_composition_exception():
    source = Path("main.py").read_text(encoding="utf-8")
    assert 'reason=composition_exception:' in source
    assert 'mode=auto, pathway=fail_closed, provider=none, model=none' in source


def test_provider_contract_validation_remains_strict():
    source = Path("general_guide_composition.py").read_text(encoding="utf-8")
    assert 'raise ValueError("general composition exposed internal implementation language")' in source
    assert 'raise ValueError("general composition embedded a navigation URL in visitor prose")' in source
    assert 'if title and title not in titles:' in source

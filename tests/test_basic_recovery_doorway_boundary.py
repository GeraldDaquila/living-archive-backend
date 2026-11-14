from pathlib import Path

def test_basic_inquiry_recovery_cannot_run_independent_cross_scale_doorway():
    source = Path("main.py").read_text(encoding="utf-8")
    start = source.index('recovery_recommendation = None')
    end = source.index('if recovery_text:', start)
    recovery_boundary = source[start:end]
    assert '_cross_scale_canonical_doorway(query)' not in recovery_boundary
    assert 'recommendation_canonical_primary' in recovery_boundary

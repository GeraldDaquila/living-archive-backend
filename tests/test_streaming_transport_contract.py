from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_sse_completion_preserves_independent_recommendation_envelope():
    source = (ROOT / "streaming_transport.py").read_text(encoding="utf-8")
    assert 'recommendation = (payload or {}).get("recommendation")' in source
    assert '"recommendation": recommendation' in source
    assert '"payload": payload or {}' in source

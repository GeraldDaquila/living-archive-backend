from pathlib import Path

def test_gold_star_shadow_observer_is_wired_into_basic_inquiry_path():
    source = Path("main.py").read_text(encoding="utf-8")
    start = source.index("def _basic_inquiry_response(")
    window = source[start:start + 1200]
    assert "_gold_star_shadow_observation(str(query or" in window

from pathlib import Path

def test_final_payload_does_not_rerun_cross_scale_doorway_selector():
    source = Path("main.py").read_text(encoding="utf-8")
    start = source.index("# Final payload boundary: do not run a second independent cross-scale")
    end = source.index("# The systems-map calibration recovery", start)
    final_boundary = source[start:end]
    assert "_cross_scale_canonical_doorway(query)" not in final_boundary

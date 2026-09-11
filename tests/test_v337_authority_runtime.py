import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location("v337_main_source", ROOT / "main.py")
module = importlib.util.module_from_spec(spec)


def test_v337_authority_helpers_are_wired():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "_original_recommendation_output_authority = use_core._enforce_recommendation_output_authority" in source
    assert "_original_recommendation_resource_identity = use_core._enforce_recommendation_resource_identity" in source
    assert "_v337_apply_recommendation_authority" in source
    assert "_v337_final_answer_boundary" in source
    assert "value = _v337_final_answer_boundary" in source or "return _v336_construct_visitor_answer" in source

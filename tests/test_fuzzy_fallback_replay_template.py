"""Guard the offline fallback replay template against misleading production claims."""
import json
from pathlib import Path

TEMPLATE = (
    Path(__file__).parent
    / "fixtures"
    / "fuzzy_fallback_replay_template.json"
)


def test_fallback_replay_template_is_empty_and_non_production():
    fixture = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    assert fixture["status"] == "TEMPLATE_ONLY_NO_CASES"
    assert fixture["production_data_present"] is False
    assert fixture["cases"] == []
    schema = fixture["case_schema"]
    for required in (
        "case_id", "pathway", "case_origin", "query", "candidates",
        "baseline", "shadow", "review", "correlation_group", "notes",
    ):
        assert required in schema
    assert "provider_bank_exhausted" in schema["pathway"]
    assert "composition_exception" in schema["pathway"]
    assert schema["review"]["review_status"] == "pending"
    assert schema["review"]["candidate_set_sufficient"] is None
    assert "diagnostic counterfactual only" in schema["shadow"]["selected_candidate_id_if_shadow_ranked"]

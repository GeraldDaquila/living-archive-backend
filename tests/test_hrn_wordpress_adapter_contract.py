from pathlib import Path


def test_versioned_hrn_wordpress_adapter_preserves_return_handoff_contract():
    source = (
        Path(__file__).resolve().parents[1]
        / "integrations"
        / "wordpress"
        / "hrn-command-boundary-adapter.php"
    ).read_text(encoding="utf-8")

    assert "Version: 1.2.1" in source
    assert "rest_request_before_callbacks" in source
    assert "rest_post_dispatch" in source
    assert "/api/relational-return" in source
    assert "whole_journey_synthesis" in source
    assert "$data['junction_available'] = true;" in source
    assert "$data['use_resource'] = true;" in source
    assert "$data['unit_complete'] = true;" in source
    assert "array('amber', 'red')" in source
    assert "canonical_doorway_ready" in source

from pathlib import Path


def test_versioned_hrn_wordpress_adapter_preserves_return_handoff_contract():
    source = (
        Path(__file__).resolve().parents[1]
        / "integrations"
        / "wordpress"
        / "hrn-command-boundary-adapter.php"
    ).read_text(encoding="utf-8")

    assert "Version: 1.4.0" in source
    assert "rest_request_before_callbacks" in source
    assert "rest_post_dispatch" in source
    assert "/api/relational-return" in source
    assert "https://living-archive-backend-mirror.onrender.com/api/relational-return" in source
    assert "la_provider_bank_shared_secret" in source
    assert "X-Living-Archive-Provider-Key" in source
    assert "LA_RELATIONAL_RETURN_SHARED_SECRET" in source
    assert "hash_hmac(" in source
    assert "X-LA-Relational-Timestamp" in source
    assert "X-LA-Relational-Nonce" in source
    assert "X-LA-Relational-Signature" in source
    assert "$timestamp . \"\\n\" . $nonce . \"\\n\" . $encoded_payload" in source
    assert "strlen($encoded_payload) > 131072" in source
    assert "return_handoff_response" in source
    assert "wp_parse_url($url, PHP_URL_HOST)" in source
    assert "$scheme !== 'https'" in source
    assert "$host !== 'geralddaquila.com'" in source
    assert "whole_journey_synthesis" in source
    assert "$data['junction_available'] = true;" in source
    assert "$data['use_resource'] = true;" in source
    assert "$data['unit_complete'] = true;" in source
    assert "array('amber', 'red')" in source
    assert "canonical_doorway_ready" in source
    assert "same_plane_question_guard_v1" in source
    assert "What would need to be acknowledged for the discussion to return to the work itself?" in source

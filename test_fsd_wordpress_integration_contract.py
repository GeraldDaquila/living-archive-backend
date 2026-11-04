"""Static integration simulation for the source-controlled WordPress FSD release bundle.

This checks the cross-runtime contract without opening the live proxy or using secrets.
It is a simulation/consistency test, not a substitute for authenticated browser E2E.
"""
from pathlib import Path

ROOT = Path(__file__).parent
BUNDLE = ROOT / "integrations" / "wordpress" / "living-archive-fsd-proxy"
PHP = (BUNDLE / "living-archive-fsd-proxy.php").read_text(encoding="utf-8")
JS = (BUNDLE / "assets" / "fsd-app.js").read_text(encoding="utf-8")
CSS = (BUNDLE / "assets" / "fsd-app.css").read_text(encoding="utf-8")


def test_proxy_requires_both_independent_feature_flags():
    assert "get_option('la_fsd_proxy_enabled', false)" in PHP
    assert "get_option('la_fsd_proxy_staging_enabled', false)" in PHP
    assert "if (!la_fsd_proxy_is_enabled()) return;" in PHP


def test_browser_proxy_contract_matches_backend_route():
    assert 'data-api=\"/wp-json/living-archive/v1/fsd-analyze\"' not in PHP
    assert "register_rest_route('living-archive/v1', '/fsd-analyze'" in PHP
    assert '"/wp-json/living-archive/v1/fsd-analyze"' in JS
    assert "/api/fsd/analyze-episode" in PHP


def test_shared_credential_is_delegated_and_not_bundled():
    assert "la_provider_bank_shared_secret()" in PHP
    assert "X-Living-Archive-Provider-Key" in PHP
    assert "base64_decode(" not in PHP
    assert "LA_PROVIDER_BANK_SHARED_SECRET" not in PHP
    assert "USE_PROVIDER_BANK_SHARED_SECRET" not in PHP


def test_proxy_applies_no_store_to_all_rest_responses_for_its_route():
    assert "rest_pre_serve_request" in PHP
    assert "'/living-archive/v1/fsd-analyze'" in PHP
    assert "Cache-Control: no-store, no-cache, must-revalidate, max-age=0" in PHP
    assert "Pragma: no-cache" in PHP
    assert "Expires: 0" in PHP


def test_browser_submission_uses_same_origin_and_no_store():
    assert 'credentials:"same-origin"' in JS
    assert 'cache:"no-store"' in JS
    assert 'method:"POST"' in JS
    assert 'contract_version:"fsd-episode-v1"' in JS
    assert 'body.contract_version!=="fsd-episode-v1"' in JS


def test_ui_preserves_respondent_provenance_and_archive_boundary():
    assert "independently_verified!==false" in JS
    assert "Respondent-reported account; not independently verified." in JS
    assert "conceptual_context_only" in JS
    assert "they do not verify the reported episode" in JS


def test_assets_are_staging_only_and_cache_version_is_aligned():
    assert "if (!is_page(80594)) return;" in PHP
    assert "'assets/fsd-app.css', __FILE__), array(), '0.2.3'" in PHP
    assert "'assets/fsd-app.js', __FILE__), array(), '0.2.3', true" in PHP
    assert ".fsd-" in CSS


def test_bundle_contains_no_personal_or_provider_secrets():
    forbidden = ("sk-", "AIza", "Bearer ", "password=", "shared_secret =")
    combined = PHP + JS + CSS
    assert all(marker not in combined for marker in forbidden)

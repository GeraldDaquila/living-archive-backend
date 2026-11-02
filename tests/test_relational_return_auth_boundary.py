from pathlib import Path
import hashlib
import hmac
import re


ROOT = Path(__file__).resolve().parents[1]


def test_relational_return_route_authenticates_before_processing():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    route = source.split('@app.post("/api/relational-return")', 1)[1].split(
        "\n\n", 1
    )[0]
    assert "await request.body()" in route
    assert "_authorize_relational_return_request(raw_body, request.headers)" in route
    assert "if auth_error is not None:" in route
    assert route.index("if auth_error is not None:") < route.index(
        "return await _v48755_relational_return(request)"
    )


def test_relational_return_auth_uses_secret_timestamp_nonce_and_constant_time_compare():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    start = source.index("def _authorize_relational_return_request")
    end = source.index('@app.post("/api/relational-return")', start)
    helper = source[start:end]
    assert 'LA_RELATIONAL_RETURN_SHARED_SECRET' in helper
    assert "_RELATIONAL_RETURN_AUTH_WINDOW_SECONDS = 300" in source
    assert "x-la-relational-timestamp" in helper
    assert "x-la-relational-nonce" in helper
    assert "x-la-relational-signature" in helper
    assert "hmac.compare_digest" in helper
    assert "_RELATIONAL_RETURN_NONCES" in helper
    assert "relational_return_replay_rejected" in helper


def test_python_and_php_hmac_canonicalization_match():
    timestamp = "1793600000"
    nonce = "0123456789abcdef0123456789abcdef"
    body = b'{"journey_action":"end","session_id":"qa-session"}'
    secret = b"test-only-secret-material-at-least-32-bytes"
    canonical = timestamp.encode() + b"\n" + nonce.encode() + b"\n" + body
    signature = hmac.new(secret, canonical, hashlib.sha256).hexdigest()
    assert re.fullmatch(r"[0-9a-f]{64}", signature)
    # PHP adapter signs timestamp + LF + nonce + LF + exact JSON body.
    php = (ROOT / "integrations" / "wordpress" / "hrn-command-boundary-adapter.php").read_text(encoding="utf-8")
    assert "$timestamp . \\"\\n\\" . $nonce . \\"\\n\\" . $body" in php
    assert "'X-LA-Relational-Signature' => $signature" in php
    assert "LA_RELATIONAL_RETURN_SHARED_SECRET" in php


def test_browser_secret_is_not_part_of_server_side_adapter_contract():
    php = (ROOT / "integrations" / "wordpress" / "hrn-command-boundary-adapter.php").read_text(encoding="utf-8")
    assert "LA_RELATIONAL_RETURN_SHARED_SECRET" in php
    assert "wp_localize_script" not in php
    assert "wp_add_inline_script" not in php

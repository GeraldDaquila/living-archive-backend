"""Guide-owned authenticated continuity ledger for deterministic safety sessions.

This module deliberately stores no visitor text. It binds only an opaque safety
state, the active deterministic question, a nonce, and expiry to a server-side
HMAC. The client may present the token but cannot choose or alter the state.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any, Mapping

SAFETY_SESSION_CONTRACT_VERSION = "v1"
SAFETY_SESSION_TTL_SECONDS = 30 * 60
_TOKEN_PREFIX = "ss1"

_SECRET = (
    os.getenv("SAFETY_SESSION_SECRET")
    or os.getenv("USE_SAFETY_SESSION_SECRET")
    or ""
).encode("utf-8")


def safety_session_available() -> bool:
    return bool(_SECRET)


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def issue_safety_session(*, state: str, question: str, request_id: str = "") -> str:
    if not safety_session_available():
        return ""
    now = int(time.time())
    payload = {
        "v": SAFETY_SESSION_CONTRACT_VERSION,
        "state": str(state or "").strip().casefold(),
        "question": str(question or "").strip()[:500],
        "iat": now,
        "exp": now + SAFETY_SESSION_TTL_SECONDS,
        "nonce": secrets.token_urlsafe(12),
        "rid": hashlib.sha256(str(request_id or "").encode("utf-8")).hexdigest()[:16],
    }
    encoded = _b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signature = hmac.new(_SECRET, encoded.encode("ascii"), hashlib.sha256).digest()
    return f"{_TOKEN_PREFIX}.{encoded}.{_b64(signature)}"


def verify_safety_session(token: str) -> dict[str, Any] | None:
    if not safety_session_available():
        return None
    try:
        prefix, encoded, supplied = str(token or "").split(".", 2)
        if prefix != _TOKEN_PREFIX:
            return None
        expected = hmac.new(_SECRET, encoded.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _unb64(supplied)):
            return None
        payload = json.loads(_unb64(encoded).decode("utf-8"))
        if not isinstance(payload, Mapping):
            return None
        if payload.get("v") != SAFETY_SESSION_CONTRACT_VERSION:
            return None
        if int(payload.get("exp") or 0) < int(time.time()):
            return None
        state = str(payload.get("state") or "").casefold()
        question = str(payload.get("question") or "").strip()
        if not state or not question:
            return None
        return {"state": state, "question": question}
    except Exception:
        return None


def safety_session_snapshot() -> dict[str, Any]:
    return {
        "contract_version": SAFETY_SESSION_CONTRACT_VERSION,
        "mode": "authenticated_hmac_state_token",
        "available": safety_session_available(),
        "ttl_seconds": SAFETY_SESSION_TTL_SECONDS,
        "stores_visitor_text": False,
    }

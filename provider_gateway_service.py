"""Provider-neutral HTTP capability boundary backed exclusively by Provider Bank.

WordPress specialists submit semantic operations and messages. They never choose
a provider, model, credential, or failover path. Provider Bank remains the sole
provider authority.
"""
from __future__ import annotations

import hashlib
import hmac
import os
from typing import Any, Mapping

from fastapi import HTTPException
from provider_bank import CONTRACT_VERSION as PROVIDER_BANK_CONTRACT_VERSION, route as provider_bank_route

CONTRACT_VERSION = "v1"
ALLOWED_OPERATIONS = frozenset({
    "hrn_relational",
    "hrn_perception",
    "atlas_finder",
    "mini_use",
    "stewardship_pathway",
})

def _shared_secret() -> str:
    return str(os.getenv("USE_PROVIDER_BANK_SHARED_SECRET") or "").strip()

def authorize(token: str | None) -> None:
    secret = _shared_secret()
    if not secret:
        raise HTTPException(status_code=503, detail="Provider Bank gateway is not configured.")
    supplied = str(token or "").strip()
    if not supplied or not hmac.compare_digest(supplied, secret):
        raise HTTPException(status_code=401, detail="Provider Bank gateway authorization failed.")

def validate_request(body: Mapping[str, Any]) -> tuple[str, list[dict[str, str]], int]:
    if str(body.get("contract_version") or "").strip() != CONTRACT_VERSION:
        raise HTTPException(status_code=400, detail="Unsupported Provider Bank gateway contract.")
    operation = str(body.get("operation") or "").strip().casefold()
    if operation not in ALLOWED_OPERATIONS:
        raise HTTPException(status_code=400, detail="Unsupported Provider Bank operation.")
    messages = body.get("messages")
    if not isinstance(messages, list) or not messages:
        raise HTTPException(status_code=400, detail="Provider Bank messages are required.")
    normalized: list[dict[str, str]] = []
    for item in messages:
        if not isinstance(item, Mapping):
            raise HTTPException(status_code=400, detail="Provider Bank message is invalid.")
        role = str(item.get("role") or "user").strip().casefold()
        content = str(item.get("content") or "")
        if role not in {"system", "user", "assistant"}:
            raise HTTPException(status_code=400, detail="Provider Bank message role is invalid.")
        if not content:
            raise HTTPException(status_code=400, detail="Provider Bank message content is empty.")
        normalized.append({"role": role, "content": content[:16000]})
    max_tokens = max(128, min(3000, int(body.get("max_tokens") or 600)))
    return operation, normalized, max_tokens

def execute(*, operation: str, messages: list[dict[str, str]], max_tokens: int, use_core: Any) -> dict[str, Any]:
    def parse(raw: str) -> dict[str, Any]:
        import json
        value = json.loads(str(raw or "").strip())
        if not isinstance(value, dict):
            raise ValueError("Provider Bank model response was not an object.")
        return value

    result = provider_bank_route(
        use_core=use_core,
        messages=messages,
        max_tokens=max_tokens,
        parse=parse,
    )
    if not result:
        return {
            "ok": False,
            "contract_version": CONTRACT_VERSION,
            "provider_bank_contract": PROVIDER_BANK_CONTRACT_VERSION,
            "operation": operation,
            "error": "provider_bank_exhausted",
        }
    payload = dict(result.get("parsed") or {})
    return {
        "ok": True,
        "contract_version": CONTRACT_VERSION,
        "provider_bank_contract": PROVIDER_BANK_CONTRACT_VERSION,
        "operation": operation,
        "result": payload,
        "provider": str(result.get("provider") or ""),
        "model": str(result.get("model") or ""),
        "preference_order": list(result.get("preference_order") or []),
    }

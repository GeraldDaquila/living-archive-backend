# USE PRODUCTION VERSION: v424 — API-boundary risk routing without router mutation
import hashlib
import importlib
import re
from pathlib import Path

APP_VERSION = "v424"
DEPLOYMENT_FINGERPRINT = "USE-v424-api-boundary-risk-routing"
CANONICAL_BUILD_ID = "USE-BUILD-v424-api-boundary-risk-routing"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"

_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()
if not _CORE_PATH.exists():
    raise RuntimeError("USE v424 package integrity failure: use_core.py is missing.")
_core_bytes = _CORE_PATH.read_bytes()
_core_runtime_sha = hashlib.sha1(f"blob {len(_core_bytes)}\0".encode() + _core_bytes).hexdigest()
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError(f"USE v424 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}")

use_core = importlib.import_module("use_core")
_original_generate_llm_response = use_core.generate_llm_response
_original_fetch_canonical_context = use_core.fetch_canonical_context
_original_handle_query = getattr(use_core, "handle_query", None)
if _original_handle_query is None:
    raise RuntimeError("USE v424 package integrity failure: API query handler is unavailable.")


def _query_profile(user_query: str) -> dict:
    q = re.sub(r"\s+", " ", str(user_query or "").strip().casefold())
    return {
        "loneliness": bool(re.search(r"\b(?:loneliness|lonely|alone|isolat|disconnected|belonging|connection)\b", q)),
        "risk": bool(re.search(r"\b(?:suicid|self-harm|overdose|abuse|coercion|immediate danger|unsafe|threatened)\b", q)),
    }


def _build_risk_answer():
    return (
        "If you are thinking about killing yourself or may be in immediate danger, please treat this as something that needs human help now. "
        "Call emergency services or go to the nearest emergency department, and if you can, stay with another person while you get help. "
        "You do not need to work out the larger meaning of what you are going through before taking that next step."
    )


def _extract_request_query(request, payload) -> str:
    raw_body = {}
    try:
        raw_body = request.state.use_v424_raw_body
    except Exception:
        raw_body = {}
    if payload:
        value = getattr(payload, "query", None) or getattr(payload, "user_query", None) or getattr(payload, "question", None) or getattr(payload, "text", None)
        if value:
            return str(value).strip()
    if raw_body:
        value = raw_body.get("query") or raw_body.get("user_query") or raw_body.get("question") or raw_body.get("text") or raw_body.get("input")
        if value:
            return str(value).strip()
    return ""


def _v424_route_guard_factory(original_handler):
    async def _guarded_handler(request, payload=None):
        raw_body = {}
        try:
            raw_body = await request.json()
        except Exception:
            raw_body = {}
        try:
            request.state.use_v424_raw_body = raw_body
        except Exception:
            pass

        query_str = _extract_request_query(request, payload)
        if query_str and _query_profile(query_str).get("risk"):
            from fastapi.responses import JSONResponse
            headers = getattr(use_core, "CORS_RESPONSE_HEADERS", {})
            version = getattr(use_core, "APP_VERSION", APP_VERSION)
            fingerprint = getattr(use_core, "DEPLOYMENT_FINGERPRINT", DEPLOYMENT_FINGERPRINT)
            request_id = getattr(getattr(request, "state", object()), "use_request_id", "")
            return JSONResponse(
                status_code=200,
                content={
                    "ok": True,
                    "version": version,
                    "fingerprint": fingerprint,
                    "source_sha256": RUNTIME_SOURCE_SHA256,
                    "boot_id": getattr(use_core, "RUNTIME_BOOT_ID", ""),
                    "request_id": request_id,
                    "query": query_str,
                    "intent": "RISK_ROUTING",
                    "response": _build_risk_answer(),
                },
                headers=headers,
            )
        return await original_handler(request, payload)
    return _guarded_handler


app = use_core.app
app.title = f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
print(f"USE v424 GUIDE BUILD IDENTITY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}")
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.EXPECTED_CORE_BLOB_SHA = EXPECTED_CORE_BLOB_SHA

# Preserve every protected core function and every existing FastAPI route.
# Only wrap the already-registered query endpoint in place; no route removal,
# router reconstruction, or second retrieval/generation path is introduced.
from fastapi.routing import APIRoute
_guarded_route = None
for _route in getattr(app.router, "routes", []):
    if getattr(_route, "path", None) == "/api/query" and isinstance(_route, APIRoute) and "POST" in getattr(_route, "methods", set()):
        _guarded_route = _route
        break
if _guarded_route is None:
    raise RuntimeError("USE v424 package integrity failure: registered POST /api/query route is unavailable.")

_guarded_route.endpoint = _v424_route_guard_factory(_original_handle_query)
use_core.fetch_canonical_context = _original_fetch_canonical_context
use_core.generate_llm_response = _original_generate_llm_response

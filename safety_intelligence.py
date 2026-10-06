"""Shared HRN Safety Fractal / Emergency Intelligence bridge.

The Guide owns the sitewide safety boundary. This module preserves the existing
HRN safety system rather than replacing it with a new canned-response routine.

HRN remains the closest sibling integration: its safety gate and Emergency
Intelligence resolver remain authoritative for safety state, language,
location/resource selection, verification, and release readiness. The Guide
invokes that safety lane before ordinary routing and preserves the existing
flat response contract for the visitor-facing safety UI.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Mapping

SAFETY_INTELLIGENCE_CONTRACT_VERSION = "v1"
DEFAULT_HRN_ENDPOINT = (
    "https://geralddaquila.com/wp-json/living-archive/v1/relational-navigator"
)

_SUPPORT_PATTERN = re.compile(
    r"\b(?:someone|they|he|she|my\s+(?:friend|partner|parent|child|family))\b.*"
    r"\b(?:suicid(?:e|al|ality)|self[- ]?harm|kill(?:ing)?\s+themselves|"
    r"want\s+to\s+die|at\s+risk|in\s+danger)\b",
    re.I | re.S,
)
_ACUTE_PATTERNS = (
    re.compile(r"\b(?:i(?:'m| am)?\s+going\s+to|i(?:'m| am)?\s+about\s+to|i\s+will)\s+(?:kill|end)\s+(?:myself|my\s+life)\b", re.I),
    re.compile(r"\b(?:i(?:'m| am)?\s+about\s+to)\s+(?:hurt|harm)\s+myself\b", re.I),
    re.compile(r"\b(?:i\s+am\s+attempting\s+suicide|i\s+am\s+attempting\s+to\s+kill\s+myself)\b", re.I),
    re.compile(r"\b(?:i\s+(?:overdosed|have\s+overdosed|took\s+an\s+overdose)|i\s+(?:have\s+hurt|have\s+harmed)\s+myself)\b", re.I),
    re.compile(r"\b(?:i\s+(?:can't|cannot)\s+(?:keep|stay)\s+myself\s+safe|immediate\s+danger)\b", re.I),
    re.compile(r"\bi\s+want\s+to\s+die\b", re.I),
)
_PLAN_PATTERNS = (
    re.compile(r"\b(?:i\s+(?:have|made)\s+a\s+plan)\b", re.I),
    re.compile(r"\b(?:my\s+plan\s+is\s+to)\b", re.I),
)
_IMMEDIACY_PATTERNS = (
    re.compile(r"\b(?:tonight|right\s+now|soon|in\s+the\s+next\s+few\s+hours)\b.*\b(?:kill|hurt|harm|suicide|self[- ]?harm)\b", re.I | re.S),
    re.compile(r"\b(?:might|may|could)\s+(?:kill|hurt|harm)\s+myself\b", re.I),
)
_CURRENT_PATTERNS = (
    re.compile(r"\b(?:i(?:'m| am)?\s+thinking\s+about)\s+(?:kill(?:ing)?\s+myself|ending\s+my\s+life|taking\s+my\s+own\s+life|harming\s+myself|hurting\s+myself)\b", re.I),
    re.compile(r"\b(?:suicid(?:e|al|ality)|self[- ]?harm|wish\s+i\s+were\s+dead|don't\s+want\s+to\s+live|do\s+not\s+want\s+to\s+live)\b", re.I),
)

def normalize_safety_state(query: str, *, history: str = "") -> str | None:
    text = " ".join(str(query or "").strip().casefold().split())
    if not text:
        return None
    # Only the immediately preceding safety exchange may keep the sitewide
    # interrupt active. Older safety language must not trap a later, released
    # conversation in the emergency lane.
    history_lines = [line.strip() for line in str(history or "").splitlines() if line.strip()]
    recent = " ".join(history_lines[-2:]).casefold()
    active_markers = (
        "please move away from anything you could use to hurt yourself",
        "can you contact emergency or crisis support now",
        "are you safe from acting on these thoughts right now",
        "can you contact someone you trust and stay connected with them now",
        "if you cannot reach someone you trust, please use the emergency or crisis support above now",
    )
    if any(marker in recent for marker in active_markers):
        return "acute_followthrough"
    if _SUPPORT_PATTERN.search(text):
        return "support"
    if any(pattern.search(text) for pattern in _ACUTE_PATTERNS):
        return "acute"
    if any(pattern.search(text) for pattern in _PLAN_PATTERNS):
        return "plan"
    if any(pattern.search(text) for pattern in _IMMEDIACY_PATTERNS):
        return "immediacy"
    if any(pattern.search(text) for pattern in _CURRENT_PATTERNS):
        return "current"
    return None

def classify_safety(query: str, *, history: str = "") -> str | None:
    return normalize_safety_state(query, history=history)

def _request_hrn_safety(
    *,
    endpoint: str,
    query: str,
    history: str,
    safety_state: str,
    safety_question: str,
    country: str,
    unit_turns: int = 0,
    timeout: float = 12.0,
) -> Mapping[str, Any]:
    payload = {
        "message": query,
        "conversation": history,
        "visitor_history": history,
        "unit_turns": int(unit_turns or 0),
        "safety_stage": safety_state,
        "safety_question": safety_question or query,
        "country": country,
        "safety_only": True,
        "safety_source": "the_guide_sitewide_safety",
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Living-Archive-The-Guide/Safety-Intelligence",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            status_code = int(getattr(response, "status", 200))
    except urllib.error.HTTPError as exc:
        status_code = int(exc.code)
        raw = exc.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"HRN safety transport failed: {exc}") from exc
    if status_code < 200 or status_code >= 300:
        raise RuntimeError(f"HRN safety returned HTTP {status_code}.")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("HRN safety returned non-JSON data.") from exc
    if not isinstance(data, Mapping):
        raise RuntimeError("HRN safety returned an invalid response envelope.")
    return data

def normalize_safety_resolution(
    data: Mapping[str, Any],
    *,
    requested_state: str,
    country: str = "",
) -> dict[str, Any]:
    safety_resources = data.get("safety_resources")
    if not isinstance(safety_resources, list):
        safety_resources = []
    safety_message = str(data.get("safety_message") or "").strip()
    safety_question = str(data.get("safety_question") or "").strip()
    safety_note = str(data.get("safety_note") or "").strip()
    resolved_country = str(data.get("country") or country or "").strip()
    safety_state = str(data.get("safety") or requested_state or "").strip().casefold()
    safety_interrupt = bool(data.get("safety_interrupt"))
    safety_location_required = bool(data.get("safety_location_required"))
    safety_release_ready = bool(data.get("safety_release_ready"))
    if not safety_interrupt:
        raise RuntimeError("HRN safety lane did not return an active safety interrupt.")
    if not safety_message:
        raise RuntimeError("HRN safety lane returned no safety_message.")
    return {
        "safety": safety_state,
        "safety_interrupt": True,
        "safety_message": safety_message,
        "safety_question": safety_question,
        "safety_note": safety_note,
        "safety_resources": safety_resources,
        "safety_location_required": safety_location_required,
        "country": resolved_country,
        "safety_release_ready": safety_release_ready,
        "raw": dict(data),
    }

def resolve_safety(
    *,
    query: str,
    history: str = "",
    safety_state: str,
    country: str = "",
    safety_question: str = "",
    unit_turns: int = 0,
    endpoint: str | None = None,
) -> dict[str, Any]:
    endpoint_url = str(
        endpoint or os.getenv("HRN_ENDPOINT_URL") or DEFAULT_HRN_ENDPOINT
    ).strip()
    try:
        data = _request_hrn_safety(
            endpoint=endpoint_url,
            query=query,
            history=history,
            safety_state=safety_state,
            safety_question=safety_question or query,
            country=country,
            unit_turns=unit_turns,

        )
        return normalize_safety_resolution(
            data,
            requested_state=safety_state,
            country=country,
        )
    except Exception as exc:
        return {
            "safety": safety_state,
            "safety_interrupt": True,
            "safety_message": (
                "If you may be in immediate danger, contact the emergency "
                "service where you are or go to the nearest emergency "
                "department, and stay with another person."
            ),
            "safety_question": "",
            "safety_note": "",
            "safety_resources": [],
            "safety_location_required": True,
            "country": str(country or "").strip(),
            "safety_release_ready": False,
            "resolver_status": "fallback",
            "resolver_error": str(exc),
        }

def safety_intelligence_snapshot() -> dict[str, Any]:
    return {
        "contract_version": SAFETY_INTELLIGENCE_CONTRACT_VERSION,
        "authority": "HRN_Safety_Fractal_and_Emergency_Intelligence",
        "resource_owner": "Emergency Intelligence",
        "language_owner": "HRN_Safety_Fractal",
        "guide_role": "sitewide_boundary_and_contract_preservation",
        "ordinary_hrn_composition_bypassed": True,
        "retrieval_bypassed": True,
    }

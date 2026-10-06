"""Shared HRN Safety Fractal + Emergency Intelligence bridge.

The Guide owns the sitewide safety boundary. HRN remains authoritative for
semantic safety state, safety language, follow-through and release. The
standalone Living Archive Emergency Intelligence plugin remains authoritative
for location resolution, verified resources, selection and presentation.

This module is deliberately a bridge between those two sibling authorities.
It does not create a second emergency registry.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Mapping

SAFETY_INTELLIGENCE_CONTRACT_VERSION = "v2"

DEFAULT_HRN_ENDPOINT = (
    "https://geralddaquila.com/wp-json/living-archive/v1/relational-navigator"
)
DEFAULT_EMERGENCY_INTELLIGENCE_ENDPOINT = (
    "https://geralddaquila.com/wp-json/living-archive/emergency/v1/resolve"
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


def _emergency_location(
    *,
    country: str = "",
    location: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    source = dict(location or {})
    if country and not source.get("explicit_country"):
        source["explicit_country"] = country
    allowed = (
        "explicit_country",
        "browser_country",
        "ip_country",
        "timezone_country",
        "locale_country",
        "region",
        "province",
        "locality",
        "address",
        "refused",
        "user_confirmation",
    )
    return {
        key: source[key]
        for key in allowed
        if key in source and source[key] not in ("", None)
    }


def _last_safety_question(history: str) -> str:
    lines = [line.strip() for line in str(history or "").splitlines() if line.strip()]
    for line in reversed(lines):
        value = re.sub(
            r"^\s*(?:assistant|hrn|system)\s*:\s*",
            "",
            line,
            flags=re.I,
        ).strip()
        if "?" in value and any(
            marker in value.casefold()
            for marker in (
                "moved away",
                "someone you trust",
                "contact emergency",
                "safe from acting",
                "hurt yourself",
                "danger",
            )
        ):
            return value
    return ""


def _presence_signal(query: str) -> str:
    text = " ".join(str(query or "").strip().casefold().split())
    if re.search(
        r"\b(?:someone|a person|my (?:friend|partner|family|sister|brother|parent|husband|wife)|they)\s+"
        r"(?:is|are)\s+(?:with|here|beside)\s+me\b",
        text,
    ):
        return "present"
    if re.search(
        r"\b(?:i(?:'m| am) alone|i live alone|no one is with me|nobody is with me)\b",
        text,
    ):
        return "alone"
    return "unknown"


def _request_json(
    *,
    endpoint: str,
    payload: Mapping[str, Any],
    user_agent: str,
    timeout: float,
) -> Mapping[str, Any]:
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(dict(payload), ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": user_agent,
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
        raise RuntimeError(f"Transport failed: {exc}") from exc

    if status_code < 200 or status_code >= 300:
        raise RuntimeError(f"Endpoint returned HTTP {status_code}.")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Endpoint returned non-JSON data.") from exc
    if not isinstance(data, Mapping):
        raise RuntimeError("Endpoint returned an invalid response envelope.")
    return data


def _request_emergency_intelligence(
    *,
    endpoint: str,
    service_need: str,
    safety_state: str,
    location: Mapping[str, Any],
    timeout: float = 6.0,
) -> Mapping[str, Any]:
    return _request_json(
        endpoint=endpoint,
        payload={
            "service_need": service_need,
            "safety_state": safety_state,
            "location": dict(location or {}),
        },
        user_agent="Living-Archive-The-Guide/Emergency-Intelligence",
        timeout=timeout,
    )


def _request_hrn_safety(
    *,
    endpoint: str,
    query: str,
    history: str,
    safety_state: str,
    safety_question: str,
    country: str,
    unit_turns: int = 0,
    safety_presence: str = "unknown",
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
        # Compatibility context for the HRN safety loop. These fields are
        # additive; HRN remains free to ignore them until its native loop
        # consumes the explicit semantic signal.
        "safety_presence": safety_presence,
    }
    return _request_json(
        endpoint=endpoint,
        payload=payload,
        user_agent="Living-Archive-The-Guide/Safety-Intelligence",
        timeout=timeout,
    )


def _resource_projection(emergency_resolution: Mapping[str, Any]) -> list[dict[str, Any]]:
    selection = dict(emergency_resolution.get("selection") or {})
    primary = selection.get("primary")
    resources = primary if isinstance(primary, list) else ([primary] if isinstance(primary, Mapping) else [])
    projected = []
    for resource in resources:
        if not isinstance(resource, Mapping):
            continue
        verification = resource.get("_verification")
        verification = verification if isinstance(verification, Mapping) else {}
        projected.append(
            {
                "title": resource.get("display_name") or "Emergency assistance",
                "phone": resource.get("number") or "",
                "service_type": (resource.get("service_types") or [None])[0],
                "priority": resource.get("presentation_priority") or 0,
                "source": verification.get("source") or "",
                "source_type": verification.get("evidence_type") or "",
                "verification": verification.get("status") or "",
                "group": "Emergency help",
            }
        )
    return projected


def resolve_emergency_resources(
    *,
    service_need: str = "general_emergency",
    safety_state: str = "acute",
    country: str = "",
    location: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    endpoint = str(
        os.getenv("EMERGENCY_INTELLIGENCE_ENDPOINT")
        or DEFAULT_EMERGENCY_INTELLIGENCE_ENDPOINT
    ).strip()
    location_input = _emergency_location(country=country, location=location)
    return dict(
        _request_emergency_intelligence(
            endpoint=endpoint,
            service_need=service_need,
            safety_state=safety_state,
            location=location_input,
        )
    )


def normalize_safety_resolution(
    data: Mapping[str, Any],
    *,
    requested_state: str,
    country: str = "",
    emergency_resolution: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
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

    resources = _resource_projection(emergency_resolution or {})
    if not resources and emergency_resolution is None:
        resources = list(data.get("safety_resources") or [])

    emergency_status = str((emergency_resolution or {}).get("selection", {}).get("selection_status") or "")
    if emergency_resolution is not None and not resources and emergency_status in {
        "",
        "LOCATION_REQUIRED",
        "FALLBACK_GENERAL_EMERGENCY",
    }:
        safety_message = (
            "I want to make sure I give you the right local emergency help. "
            "If you may be in immediate danger, please contact the emergency "
            "service where you are or go to the nearest emergency department."
        )
        safety_question = (
            "What country are you in right now?"
            if emergency_status == "LOCATION_REQUIRED"
            else safety_question
        )

    selection = dict((emergency_resolution or {}).get("selection") or {})
    presentation = dict((emergency_resolution or {}).get("presentation") or {})

    return {
        "safety": safety_state,
        "safety_interrupt": True,
        "safety_message": safety_message,
        "safety_question": safety_question,
        "safety_note": safety_note,
        "safety_resources": resources,
        "safety_location_required": (
            safety_location_required
            or str(selection.get("selection_status") or "") == "LOCATION_REQUIRED"
        ),
        "country": resolved_country,
        "safety_release_ready": safety_release_ready,
        "emergency_resolution": dict(emergency_resolution or {}),
        "emergency_selection_status": str(selection.get("selection_status") or ""),
        "emergency_presentation": presentation,
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
    location: Mapping[str, Any] | None = None,
    service_need: str = "general_emergency",
    endpoint: str | None = None,
    emergency_endpoint: str | None = None,
) -> dict[str, Any]:
    endpoint_url = str(
        endpoint or os.getenv("HRN_ENDPOINT_URL") or DEFAULT_HRN_ENDPOINT
    ).strip()
    emergency_endpoint_url = str(
        emergency_endpoint
        or os.getenv("EMERGENCY_INTELLIGENCE_ENDPOINT")
        or DEFAULT_EMERGENCY_INTELLIGENCE_ENDPOINT
    ).strip()

    location_input = _emergency_location(country=country, location=location)
    previous_question = safety_question or _last_safety_question(history)
    presence = _presence_signal(query)

    emergency_resolution: Mapping[str, Any] | None = None
    emergency_error = ""
    try:
        emergency_resolution = _request_emergency_intelligence(
            endpoint=emergency_endpoint_url,
            service_need=service_need,
            safety_state=safety_state,
            location=location_input,
        )
    except Exception as exc:
        emergency_error = str(exc)
        emergency_resolution = {}
        print(f"Emergency Intelligence unavailable; HRN safety remains active: {exc}")

    try:
        data = _request_hrn_safety(
            endpoint=endpoint_url,
            query=query,
            history=history,
            safety_state=safety_state,
            safety_question=previous_question or query,
            country=country,
            unit_turns=unit_turns,
            safety_presence=presence,
        )
        normalized = normalize_safety_resolution(
            data,
            requested_state=safety_state,
            country=country,
            emergency_resolution=emergency_resolution,
        )

        # Compatibility guard for the known HRN loop defect. If the visitor
        # explicitly establishes human presence, HRN must not pass through a
        # generated assertion that the visitor is alone. We repair the
        # contradiction conservatively and keep the safety latch closed.
        message = str(normalized.get("safety_message") or "")
        if presence == "present" and re.search(
            r"\b(?:you are|you(?:'re| are)?)\s+alone\b|\bsince you are alone\b",
            message,
            re.I,
        ):
            normalized["safety_message"] = (
                "It helps that someone is with you. Please stay with them and "
                "keep away from anything you could use to hurt yourself."
            )
            if "moved away" in previous_question.casefold():
                normalized["safety_question"] = (
                    "Are you safe from acting on these thoughts right now?"
                    if re.search(r"\b(?:yes|i did|i have|i moved|i'm away|i am away)\b", query.casefold())
                    else "Have you moved away from anything you could use to hurt yourself?"
                )
            else:
                normalized["safety_question"] = (
                    "Have you moved away from anything you could use to hurt yourself?"
                )
            normalized["safety_release_ready"] = False
            normalized["loop_guard"] = "contradictory_presence_claim_repaired"

        normalized["safety_presence"] = presence
        normalized["safety_question_context"] = previous_question
        normalized["emergency_resolution_status"] = (
            str(selection_status)
            if (selection_status := (
                (emergency_resolution or {}).get("selection", {}).get("selection_status")
                if isinstance((emergency_resolution or {}).get("selection"), Mapping)
                else ""
            ))
            else "unavailable"
        )
        if emergency_error:
            normalized["emergency_error"] = emergency_error
        return normalized

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
            "safety_resources": _resource_projection(emergency_resolution or {}),
            "safety_location_required": (
                not bool(emergency_resolution)
                or str(
                    ((emergency_resolution or {}).get("selection") or {}).get("selection_status")
                    or ""
                ) == "LOCATION_REQUIRED"
            ),
            "country": str(country or "").strip(),
            "safety_release_ready": False,
            "resolver_status": "fallback",
            "resolver_error": str(exc),
            "emergency_resolution": dict(emergency_resolution or {}),
            "emergency_error": emergency_error,
            "safety_presence": presence,
            "safety_question_context": previous_question,
        }


def safety_intelligence_snapshot() -> dict[str, Any]:
    return {
        "contract_version": SAFETY_INTELLIGENCE_CONTRACT_VERSION,
        "authority": "HRN_Safety_Fractal_and_Emergency_Intelligence",
        "emergency_intelligence_endpoint": DEFAULT_EMERGENCY_INTELLIGENCE_ENDPOINT,
        "resource_owner": "Emergency Intelligence",
        "resource_contract": "living-archive/emergency/v1/resolve",
        "language_owner": "HRN_Safety_Fractal",
        "guide_role": "sitewide_boundary_and_contract_preservation",
        "ordinary_hrn_composition_bypassed": True,
        "retrieval_bypassed": True,
        "emergency_registry_authority": "Emergency Intelligence",
        "safety_loop_guard": "sitewide_compatibility_guard",
    }

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
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Any, Mapping

from provider_bank import route as route_with_model_bank

SAFETY_INTELLIGENCE_CONTRACT_VERSION = "v2.7"

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
    # First-person inability to stay safe is urgent even when softened by uncertainty.
    re.compile(r"\bi\s+(?:do\s+not|don't|dont)\s+(?:think|feel|believe)\s+i\s+(?:can|could|will)\s+(?:keep|keep\s+myself|stay)\s+(?:myself\s+)?safe\b", re.I),
    re.compile(r"\bi\s+(?:am\s+not\s+sure|am\s+unsure|don't\s+know\s+if|do\s+not\s+know\s+if)\s+i\s+can\s+(?:keep|keep\s+myself|stay)\s+(?:myself\s+)?safe\b", re.I),
    re.compile(r"\b(?:i(?:'m| am)?\s+about\s+to)\s+(?:hurt|harm)\s+myself\b", re.I),
    re.compile(r"\b(?:i\s+am\s+attempting\s+suicide|i\s+am\s+attempting\s+to\s+kill\s+myself)\b", re.I),
    re.compile(r"\b(?:i\s+(?:overdosed|have\s+overdosed|took\s+an\s+overdose)|i\s+(?:have\s+hurt|have\s+harmed)\s+myself)\b", re.I),
    re.compile(r"\b(?:i\s+(?:can't|cannot)\s+(?:keep|stay)\s+myself\s+safe|immediate\s+danger)\b", re.I),
    re.compile(r"\bi\s+want\s+to\s+die\b", re.I),
    # Plain first-person suicidal intent belongs to the native acute HRN safety loop.
    # Do not downgrade this boundary to the generic current-risk branch.
    re.compile(r"\b(?:i(?:'m| am)?\s+want(?:ing)?\s+to)\s+(?:kill\s+myself|end\s+my\s+life)\b", re.I),
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
    # Include both "thinking about" and the equally natural "thinking of".
    # These describe present suicidal thinking without, by themselves,
    # establishing near-term action.
    re.compile(r"\b(?:i(?:'m| am)?\s+thinking\s+(?:about|of))\s+(?:kill(?:ing)?\s+myself|ending\s+my\s+life|taking\s+my\s+own\s+life|harming\s+myself|hurting\s+myself)\b", re.I),
    re.compile(r"\b(?:i(?:'m| am)?\s+considering)\s+(?:killing\s+myself|ending\s+my\s+life|harming\s+myself|hurting\s+myself)\b", re.I),
    # Generic topic mentions such as "What is suicide?" are not personal-risk disclosures.
    # They may enter the gated semantic recall layer, but they must not trigger
    # the sitewide emergency lane deterministically.
    re.compile(r"\b(?:wish\s+i\s+were\s+dead|don't\s+want\s+to\s+live|do\s+not\s+want\s+to\s+live)\b", re.I),
)


def normalize_safety_state(query: str, *, history: str = "") -> str | None:
    text = " ".join(str(query or "").strip().casefold().split()).replace("’", "'").replace("‘", "'")
    if not text:
        return None

    history_lines = [line.strip() for line in str(history or "").splitlines() if line.strip()]
    recent = " ".join(history_lines[-2:]).casefold()
    # A safety conversation remains in the safety lane while the visitor is
    # answering one of HRN's active safety questions. Short answers such as
    # "yes", "no", "not yet", or "I don't know" contain too little standalone
    # semantic material to classify safely. The preceding HRN question is the
    # authoritative conversational context and must therefore keep the request
    # inside the safety state machine.
    active_markers = (
        "please move away from anything you could use to hurt yourself",
        "have you moved away from anything you could use to hurt yourself",
        "can you contact emergency or crisis support now",
        "do you think you might act on these thoughts right now",
        "do you feel you might act on these thoughts right now",
        "are you safe from acting on these thoughts right now",
        "can you contact someone you trust and stay connected with them now",
        "is there someone you can be with right now",
        "is there someone you trust you can be with right now",
        "is there someone you trust who can stay with you right now",
        "can you stay with them while you get support",
        "can you contact emergency or crisis support now",
        "are you safe from acting on these thoughts right now",
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


# v488.60 boundary invariant: a short answer must remain inside the active
# safety conversation when the preceding HRN question is still open.
if normalize_safety_state(
    "yes",
    history="visitor: I don't want to live anymore.\nassistant: Do you think you might act on these thoughts right now?"
) != "acute_followthrough":
    raise RuntimeError("USE v488.60 invariant failed: active safety follow-through lost for short answer.")

if normalize_safety_state(
    "no",
    history="visitor: I don't want to live anymore.\nassistant: Have you moved away from anything you could use to hurt yourself?"
) != "acute_followthrough":
    raise RuntimeError("USE v488.60 invariant failed: active safety follow-through lost for negative short answer.")


def _llm_safety_signal(query: str, *, history: str = "") -> dict[str, Any] | None:
    """Bounded semantic safety augmentation.

    This is deliberately advisory. Deterministic/protected-core signals remain
    sufficient to trigger safety; the LLM can only add a safety signal that
    broadens recall. Provider failure, timeout, malformed output, or uncertainty
    never blocks the deterministic path.
    """
    prompt = (
        "Classify whether the visitor's language contains a plausible personal "
        "self-harm or suicide safety signal. This is a safety detector, not a "
        "therapeutic response generator. Consider paraphrase, indirect wording, "
        "fragmented language, slang, and context from the recent conversation. "
        "Do not infer risk merely from discussion of suicide as a topic or from "
        "third-person concern unless the visitor is expressing their own risk. "
        "Return JSON only with keys: state, confidence, rationale. "
        "state must be exactly one of: acute, plan, immediacy, current, none. "
        "Use acute only when the language reasonably indicates present intent, "
        "attempt, imminent action, or inability to remain safe; plan for a "
        "self-harm/suicide plan without clear immediate action; immediacy for "
        "possible near-term action; current for present suicidal/self-harm "
        "thinking without evidence of immediate action; none otherwise. "
        "When uncertain, choose the less severe state. confidence is 0 to 1. "
        "Never provide advice or resources."
    )
    context = (
        f"VISITOR: {str(query or '').strip()}\n"
        f"RECENT CONVERSATION: {str(history or '')[-4000:]}"
    )
    try:
        runtime = __import__("guide_runtime")
        use_core = runtime.use_core
    except Exception as exc:
        print(f"The Guide semantic safety detector unavailable: {exc}")
        return None

    def _parse(raw: str) -> dict[str, Any]:
        value = json.loads(str(raw or "").strip())
        if not isinstance(value, dict):
            raise ValueError("semantic safety response was not an object")
        state = str(value.get("state") or "none").strip().casefold()
        if state not in {"acute", "plan", "immediacy", "current", "none"}:
            raise ValueError("semantic safety response contained an invalid state")
        confidence = float(value.get("confidence", 0) or 0)
        if confidence < 0 or confidence > 1:
            raise ValueError("semantic safety confidence outside 0..1")
        return {"state": state, "confidence": confidence, "rationale": str(value.get("rationale") or "")[:300]}

    try:
        result = route_with_model_bank(
            use_core=use_core,
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": context}],
            max_tokens=120,
            parse=_parse,
        )
        if not isinstance(result, Mapping):
            return None
        parsed = result.get("parsed")
        if not isinstance(parsed, Mapping):
            return None
        return {
            "state": str(parsed.get("state") or "none"),
            "confidence": float(parsed.get("confidence") or 0),
            "rationale": str(parsed.get("rationale") or ""),
            "provider": str(result.get("provider") or ""),
            "model": str(result.get("model") or ""),
        }
    except Exception as exc:
        print(f"The Guide semantic safety detector failed safely: {exc}")
        return None


# The semantic detector is deliberately gated. It must not run on every
# ordinary Guide question: doing so both adds avoidable latency and allows a
# broad language model to manufacture a safety signal from emotionally loaded
# but non-safety language (for example, an ordinary relationship description
# containing words such as "hurt", "angry", or "defensive").
#
# Deterministic safety remains the first and authoritative gate. The semantic
# detector is only a recall-expansion layer after the visitor's current turn
# contains a high-signal safety candidate. Active safety follow-through is
# already handled deterministically from the preceding safety question.
_SEMANTIC_SAFETY_CANDIDATE_PATTERNS = (
    re.compile(r"\b(?:suicid(?:e|al|ality)|self[- ]?harm)\b", re.I),
    re.compile(r"\b(?:kill(?:ing)?|hurt(?:ing)?|harm(?:ing)?)\s+myself\b", re.I),
    re.compile(r"\b(?:end(?:ing)?|take|taking)\s+my\s+(?:own\s+)?life\b", re.I),
    re.compile(r"\b(?:do(?:n'?t| not)|dont)\s+want\s+to\s+live\b", re.I),
    re.compile(r"\b(?:want(?:ing)?|wish(?:ing)?)\s+to\s+die\b", re.I),
    re.compile(r"\b(?:wish|wishing)\s+(?:i|i'm|i am)\s+(?:were|was)\s+dead\b", re.I),
    re.compile(r"\b(?:no|not)\s+(?:reason|point)\s+to\s+live\b", re.I),
    re.compile(r"\b(?:better\s+off\s+dead|can't\s+keep\s+myself\s+safe|cannot\s+keep\s+myself\s+safe)\b", re.I),
)


def _semantic_safety_candidate(query: str) -> bool:
    text = " ".join(str(query or "").strip().casefold().split())
    if not text:
        return False
    return any(pattern.search(text) for pattern in _SEMANTIC_SAFETY_CANDIDATE_PATTERNS)


def classify_safety(query: str, *, history: str = "") -> str | None:
    """Deterministic safety first; semantic augmentation only behind a high-signal gate."""
    deterministic = normalize_safety_state(query, history=history)
    if deterministic:
        return deterministic

    # Ordinary Guide traffic must never pay the semantic-safety latency tax.
    # More importantly, the LLM must not be allowed to convert ordinary human
    # conflict/relationship language into an emergency interruption merely
    # because it contains emotionally charged words. Only a current-turn
    # safety candidate may reach the semantic recall layer.
    if not _semantic_safety_candidate(query):
        return None

    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="guide-safety-semantic")
    future = executor.submit(_llm_safety_signal, query, history=history)
    try:
        result = future.result(timeout=1.8)
    except FutureTimeoutError:
        print("The Guide semantic safety detector exceeded its 1.8s gate; continuing deterministically.")
        return None
    except Exception as exc:
        print(f"The Guide semantic safety detector unavailable: {exc}")
        return None
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    if not isinstance(result, Mapping):
        return None
    state = str(result.get("state") or "none").casefold()
    confidence = float(result.get("confidence") or 0)
    if state in {"acute", "plan", "immediacy", "current"} and confidence >= 0.70:
        print(f"The Guide semantic safety detector escalated: state={state}, confidence={confidence:.2f}")
        return state
    return None


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
    timeout: float = 3.0,
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
    timeout: float = 5.0,
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


def repair_safety_question(
    *,
    safety_state: str,
    previous_question: str = "",
    query: str = "",
    history: str = "",
) -> str:
    """Restore the next native safety movement when HRN returns no question.

    This is a continuity guard, not a second safety system. HRN remains the
    semantic authority whenever it returns a valid next question. The repair
    exists only to prevent a live safety interruption from becoming a dead end.
    It advances the visitor through the existing safety sequence rather than
    repeating one generic question.
    """
    state = str(safety_state or "").strip().casefold()
    previous = " ".join(str(previous_question or "").strip().casefold().split())
    answer = " ".join(str(query or "").strip().casefold().split())

    affirmative = bool(re.search(
        r"^(?:yes|yeah|yep|i did|i have|i moved|i'm away|i am away|already|"
        r"someone is with me|they are with me|they're with me)\b",
        answer,
        re.I,
    ))
    negative = bool(re.search(
        r"^(?:no|nope|not yet|i haven't|i have not|i am not|i'm not|"
        r"nobody|no one|alone|i don't know|i do not know)\b",
        answer,
        re.I,
    ))

    if (
        "do you think you might act on these thoughts right now" in previous
        or "do you feel you might act on these thoughts right now" in previous
        or "are you safe from acting on these thoughts right now" in previous
    ):
        if affirmative:
            return "Have you moved away from anything you could use to hurt yourself?"
        if negative:
            return "Is there someone you trust who can stay with you right now?"
        return "Is there someone you trust who can stay with you right now?"

    if (
        "moved away from anything you could use to hurt yourself" in previous
        or "have you moved away from anything you could use to hurt yourself" in previous
    ):
        return "Is there someone you trust who can stay with you right now?"

    if (
        "someone you trust" in previous
        or "stay with you right now" in previous
        or "is there someone you can be with right now" in previous
    ):
        if negative:
            return "Can you contact emergency or crisis support now?"
        return "Can you contact emergency or crisis support now?"

    if "contact emergency or crisis support now" in previous:
        return "Are you safe from acting on these thoughts right now?"

    if state in {"acute", "plan", "immediacy", "current", "acute_followthrough"}:
        return "Do you think you might act on these thoughts right now?"

    return "Do you think you might act on these thoughts right now?"

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

    # HRN remains authoritative for the safety state, immediate message,
    # and next conversational movement. Emergency Intelligence is the sole
    # authority for visitor-facing emergency phone resources because its
    # selection is grounded in a resolved location and verified registry
    # evidence. Never merge HRN's unscoped/static hotline list into a visitor
    # response: those numbers may belong to a different country.
    emergency_resources = _resource_projection(emergency_resolution or {})
    resources = [dict(resource) for resource in emergency_resources if isinstance(resource, Mapping)]

    selection = dict((emergency_resolution or {}).get("selection") or {})
    emergency_status = str(selection.get("selection_status") or "")
    emergency_location = dict((emergency_resolution or {}).get("location") or {})
    resolved_location = dict(emergency_location.get("location") or {})
    resolved_country_data = dict(resolved_location.get("country") or {})
    verified_resource_country = str(resolved_country_data.get("value") or "").strip().upper()
    selected_country = str(country or resolved_country_data.get("value") or "").strip().upper()
    resources_are_location_grounded = bool(
        emergency_status == "SELECTED"
        and verified_resource_country
        and selected_country
        and verified_resource_country == selected_country
        and resources
    )
    if not resources_are_location_grounded:
        # A country guess from HRN is not location evidence. Keep the immediate
        # safety exchange intact, disclose the missing local-resource context,
        # and let the UI/request boundary collect location before showing a number.
        resources = []
        location_resolution_status = str(emergency_location.get("resolution_status") or "").strip().upper()
        if location_resolution_status == "REFUSED":
            safety_note = "I’ll respect your choice not to share your location. I can’t verify a local hotline without it, so I won’t guess. If you may be in immediate danger, contact your local emergency service or go to the nearest emergency department."
        else:
            safety_note = "I don't yet have a verified local hotline for your location, so I won't guess. If you may be in immediate danger, contact your local emergency service or go to the nearest emergency department. If you tell me what country you're in, I can help identify the appropriate local resource."
        resolved_country = str(country or "").strip()
    else:
        resolved_country = str(resolved_country_data.get("value") or country or "").strip()

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
            or not resources_are_location_grounded
            or str(selection.get("selection_status") or "") == "LOCATION_REQUIRED"
        ),
        "country": resolved_country,
        "safety_release_ready": safety_release_ready,
        "emergency_resolution": dict(emergency_resolution or {}),
        "emergency_selection_status": str(selection.get("selection_status") or ""),
        "emergency_presentation": presentation,
        "raw": dict(data),
    }


def _initial_deterministic_safety_response(
    *,
    query: str,
    safety_state: str,
    country: str = "",
    emergency_resolution: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the first safety movement without waiting for an LLM/provider.

    High-confidence first-turn disclosures already have a deterministic state.
    There is no safety-language reason to send those turns through the HRN
    Safety composer before answering. The emergency/resource resolver may still
    contribute resources when it returns quickly, but it is not allowed to
    delay the first human-facing movement.
    """
    state = str(safety_state or "").strip().casefold()
    resources = _resource_projection(emergency_resolution or {})
    if state == "acute":
        message = (
            "Thank you for telling me. I want to take what you're saying "
            "seriously. Please don't stay alone with this. If you can, move "
            "away from anything you could use to hurt yourself and bring "
            "another person into this now."
        )
        question = "Do you think you might act on these thoughts right now?"
    elif state in {"plan", "immediacy"}:
        message = (
            "Please don't stay alone with this. Move away from anything you "
            "could use to hurt yourself, and bring another person into this "
            "now if you can."
        )
        question = "Have you moved away from anything you could use to hurt yourself?"
    else:
        message = (
            "Thank you for telling me. I want to take what you're saying "
            "seriously. Please stay with another person if you can while we "
            "make sure you are safe."
        )
        question = "Do you think you might act on these thoughts right now?"

    return {
        "safety": state,
        "safety_interrupt": True,
        "safety_message": message,
        "safety_question": question,
        "safety_note": (
            "If you are in immediate danger or have already injured yourself, "
            "contact your local emergency service or go to the nearest emergency "
            "department now."
        ),
        "safety_resources": resources,
        "safety_location_required": (
            not bool(resources)
            or str(
                ((emergency_resolution or {}).get("selection") or {}).get("selection_status") or ""
            ) != "SELECTED"
        ),
        "country": str(
            country
            or (
                (((emergency_resolution or {}).get("location") or {}).get("location") or {})
                .get("country", {}).get("value", "")
                if str(((emergency_resolution or {}).get("selection") or {}).get("selection_status") or "") == "SELECTED"
                else ""
            )
            or ""
        ).strip(),
        "safety_release_ready": False,
        "resolver_status": "deterministic_initial_fast_path",
        "safety_continuity_guard": "deterministic_initial_movement",
        "next_movement": question,
        "safety_presence": "unknown",
        "safety_question_context": "",
        "emergency_resolution_status": (
            str(
                (emergency_resolution or {}).get("selection", {}).get("selection_status")
            )
            if isinstance((emergency_resolution or {}).get("selection"), Mapping)
            else "unavailable"
        ),
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

    # High-confidence first-turn safety disclosures must not wait for the
    # provider-backed HRN Safety composer. The state is already deterministic;
    # the first human-facing movement should therefore be deterministic too.
    #
    # Resource intelligence is best-effort and bounded to a short window. It
    # can enrich the first response when already fast, but it must never become
    # the critical path for the first safety question.
    initial_safety_fast_path = (
        not str(history or "").strip()
        and not str(safety_question or "").strip()
        and safety_state in {"acute", "plan", "immediacy", "current"}
    )
    if initial_safety_fast_path:
        emergency_resolution_fast: Mapping[str, Any] | None = None
        try:
            fast_executor = ThreadPoolExecutor(
                max_workers=1,
                thread_name_prefix="guide-safety-resource-fast",
            )
            fast_future = fast_executor.submit(
                _request_emergency_intelligence,
                endpoint=emergency_endpoint_url,
                service_need=service_need,
                safety_state=safety_state,
                location=location_input,
                timeout=0.6,
            )
            try:
                emergency_resolution_fast = fast_future.result(timeout=0.65)
            except Exception as exc:
                print(f"Fast safety resource enrichment unavailable; returning immediately: {exc}")
                emergency_resolution_fast = {}
            finally:
                fast_executor.shutdown(wait=False, cancel_futures=True)
        except Exception as exc:
            print(f"Fast safety resource path unavailable; returning deterministic movement: {exc}")
            emergency_resolution_fast = {}

        return _initial_deterministic_safety_response(
            query=query,
            safety_state=safety_state,
            country=country,
            emergency_resolution=emergency_resolution_fast,
        )

    emergency_resolution: Mapping[str, Any] | None = None
    emergency_error = ""
    data: Mapping[str, Any] | None = None
    hrn_error = ""

    executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="guide-safety")
    emergency_future = executor.submit(
        _request_emergency_intelligence,
        endpoint=emergency_endpoint_url,
        service_need=service_need,
        safety_state=safety_state,
        location=location_input,
        timeout=3.0,
    )
    hrn_future = executor.submit(
        _request_hrn_safety,
        endpoint=endpoint_url,
        query=query,
        history=history,
        safety_state=safety_state,
        safety_question=previous_question or query,
        country=country,
        unit_turns=unit_turns,
        safety_presence=presence,
        timeout=5.0,
    )

    try:
        try:
            emergency_resolution = emergency_future.result(timeout=3.2)
        except Exception as exc:
            emergency_error = str(exc)
            emergency_resolution = {}
            print(f"Emergency Intelligence unavailable; HRN safety remains active: {exc}")

        try:
            data = hrn_future.result(timeout=5.2)
        except Exception as exc:
            hrn_error = str(exc)
            data = None
            print(f"HRN safety sibling unavailable within bound: {exc}")
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    try:
        if data is None:
            raise RuntimeError(hrn_error or "HRN safety sibling returned no response.")
        normalized = normalize_safety_resolution(
            data,
            requested_state=safety_state,
            country=country,
            emergency_resolution=emergency_resolution,
        )

        if (
            not bool(normalized.get("safety_release_ready"))
            and not str(normalized.get("safety_question") or "").strip()
        ):
            repaired_question = repair_safety_question(
                safety_state=safety_state,
                previous_question=previous_question,
                query=query,
                history=history,
            )
            normalized["safety_question"] = repaired_question
            normalized["safety_continuity_guard"] = "native_next_movement_repaired"
            normalized["next_movement"] = repaired_question

        # The opening safety turn should sound like a human response to what
        # the visitor actually said. Older HRN safety wording sometimes refers
        # to a previous "yes" even when the visitor has just disclosed suicidal
        # thinking. That is a broken conversational reference, not merely a
        # stylistic preference. Repair it at the shared boundary so every
        # Guide entry point receives the same coherent opening.
        if not str(history or "").strip():
            opening_message = str(normalized.get("safety_message") or "")
            if re.search(
                r"taking your\s+[“\"']?yes[”\"']?\s+seriously",
                opening_message,
                re.I,
            ):
                normalized["safety_message"] = (
                    "Thank you for telling me. I want to take what you're "
                    "saying seriously."
                )

            opening_question = str(normalized.get("safety_question") or "")
            if re.fullmatch(
                r"Do you feel you might act on these thoughts right now\?",
                opening_question,
                re.I,
            ):
                normalized["safety_question"] = (
                    "Do you think you might act on these thoughts right now?"
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



# v488.67 invariants: ordinary relational language stays out of safety,
# while a high-confidence first-turn disclosure gets an immediate deterministic
# safety movement rather than waiting for provider-backed composition.
if normalize_safety_state(
    "Whenever I bring up something that bothers me, my partner becomes defensive. Then I get angry, they withdraw, and eventually we stop talking. A few days later everything seems fine until the same thing happens again."
) is not None:
    raise RuntimeError("USE v488.67 invariant failed: ordinary relational language classified as safety.")
if _semantic_safety_candidate(
    "Whenever I bring up something that bothers me, my partner becomes defensive. Then I get angry, they withdraw, and eventually we stop talking."
):
    raise RuntimeError("USE v488.67 invariant failed: ordinary relational language opened semantic safety gate.")
if not _semantic_safety_candidate("I don't want to live anymore."):
    raise RuntimeError("USE v488.67 invariant failed: direct safety disclosure lost semantic gate.")
if normalize_safety_state("I don't think I can keep myself safe.") != "acute":
    raise RuntimeError("USE v489.30 invariant failed: uncertain inability to stay safe did not enter the acute safety boundary.")
if normalize_safety_state("I don't feel I can keep myself safe.") != "acute":
    raise RuntimeError("USE v489.30 invariant failed: softened inability to stay safe did not enter the acute safety boundary.")
if normalize_safety_state("What are common signs of grief?") is not None:
    raise RuntimeError("USE v489.30 invariant failed: ordinary grief inquiry was incorrectly classified as safety.")

if normalize_safety_state("I want to die.") != "acute":
    raise RuntimeError("USE v488.67 invariant failed: direct 'I want to die' disclosure is not deterministic acute.")


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
        "continuity_repair": "state_aware_native_next_movement",
    }

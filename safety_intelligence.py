"""Guide-owned deterministic Safety state machine with standalone Emergency Intelligence.

The Guide owns sitewide safety detection and orchestration. This module owns
local deterministic answer classification, state transitions, intervention
sequence, and continuity. The standalone Emergency Intelligence plugin owns
location resolution, verified resources, selection, and presentation.

No HRN endpoint or HRN visitor-routing dependency is used.
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

SAFETY_INTELLIGENCE_CONTRACT_VERSION = "v3.0"

DEFAULT_EMERGENCY_INTELLIGENCE_ENDPOINT = (
    "https://geralddaquila.com/wp-json/living-archive/emergency/v1/resolve"
)

# Deterministic third-person / support lane. This deliberately requires both
# a recognizable other-person reference and a current self-harm or suicide
# signal, so general educational discussion remains outside the interruption.
# Deterministic third-person / support lane. Person-reference detection and
# safety-signal detection are intentionally separate so natural language between
# them does not make the classifier brittle. Both conditions are required.
_SUPPORT_PERSON_PATTERN = re.compile(
    r"\b(?:someone|somebody|they|he|she|a\s+(?:friend|person|colleague)|"
    r"my\s+(?:friend|partner|parent|child|family|brother|sister|son|daughter|"
    r"husband|wife|colleague|coworker))\b", re.I
)
_SUPPORT_SIGNAL_PATTERN = re.compile(
    r"\b(?:suicid(?:e|al|ality)|self[- ]?harm|"
    r"kill(?:ing)?\s+(?:himself|herself|themselves)|"
    r"end(?:ing)?\s+(?:his|her|their)\s+life|"
    r"want(?:s|ing)?\s+to\s+die|"
    r"(?:does(?:n't| not)?|doesnt)\s+want\s+to\s+live|"
    r"not\s+be\s+here|at\s+risk|in\s+danger)\b", re.I
)

def _is_third_person_support_concern(text: str) -> bool:
    """Classify explicit concern about another person without keyword chaining."""
    return bool(_SUPPORT_PERSON_PATTERN.search(text) and _SUPPORT_SIGNAL_PATTERN.search(text))

_ACUTE_PATTERNS = (
    re.compile(r"\b(?:i(?:'m| am)?\s+going\s+to|i(?:'m| am)?\s+about\s+to|i\s+will)\s+(?:kill|end)\s+(?:myself|my\s+life)\b", re.I),
    # First-person inability to stay safe is urgent even when softened by uncertainty.
    re.compile(r"\bi\s+(?:do\s+not|don't|dont)\s+(?:think|feel|believe)\s+i\s+(?:can|could|will)\s+(?:keep|keep\s+myself|stay)\s+(?:myself\s+)?safe\b", re.I),
    re.compile(r"\bi\s+(?:am\s+not\s+sure|am\s+unsure|don't\s+know\s+if|do\s+not\s+know\s+if)\s+i\s+can\s+(?:keep|keep\s+myself|stay)\s+(?:myself\s+)?safe\b", re.I),
    re.compile(r"\b(?:i(?:'m| am)?\s+about\s+to)\s+(?:hurt|harm)\s+myself\b", re.I),
    re.compile(r"\b(?:i\s+am\s+attempting\s+suicide|i\s+am\s+attempting\s+to\s+kill\s+myself)\b", re.I),
    re.compile(r"\b(?:i\s+(?:overdosed|have\s+overdosed|took\s+an\s+overdose)|i\s+(?:have\s+hurt|have\s+harmed)\s+myself)\b", re.I),
    re.compile(r"\bi\s+(?:can't|cannot)\s+(?:keep|stay)\s+myself\s+safe\b", re.I),
    re.compile(r"\bi\s+want\s+to\s+die\b", re.I),
    # Plain first-person suicidal intent belongs to the native acute safety loop.
    # Do not downgrade this boundary to the generic current-risk branch.
    re.compile(r"\b(?:i(?:'m| am)?\s+want(?:ing)?\s+to)\s+(?:kill\s+myself|end\s+my\s+life)\b", re.I),
)
_GENERIC_IMMEDIATE_DANGER_PATTERN = re.compile(r"\bimmediate\s+danger\b", re.I)
_HYPOTHETICAL_SAFETY_DISCUSSION_PATTERNS = (
    re.compile(r"\b(?:calibration|test case|testing|training|hypothetical|scenario)\b", re.I),
    re.compile(r"\bif\s+(?:a|the)\s+visitor\b", re.I),
    re.compile(r"\b(?:what|where|how)\s+(?:should|would|could)\s+the\s+guide\b", re.I),
    re.compile(r"\bif\s+(?:someone|a person|a visitor)\s+(?:says|reports|mentions)\b", re.I),
)

def is_hypothetical_safety_discussion(query: str) -> bool:
    """Keep explicit calibration/third-person scenarios out of personal crisis triage.

    This exception applies only to the generic phrase "immediate danger".
    Direct first-person self-harm disclosures and inability-to-stay-safe signals
    remain authoritative even when the surrounding message discusses testing.
    """
    text = " ".join(str(query or "").strip().casefold().split())
    return any(pattern.search(text) for pattern in _HYPOTHETICAL_SAFETY_DISCUSSION_PATTERNS)


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
    # answering one of the active safety questions. Short answers such as
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
    if _is_third_person_support_concern(text):
        return "support"
    if any(pattern.search(text) for pattern in _ACUTE_PATTERNS):
        return "acute"
    if (
        _GENERIC_IMMEDIATE_DANGER_PATTERN.search(text)
        and not is_hypothetical_safety_discussion(text)
    ):
        return "acute"
    if any(pattern.search(text) for pattern in _PLAN_PATTERNS):
        return "plan"
    if any(pattern.search(text) for pattern in _IMMEDIACY_PATTERNS):
        return "immediacy"
    if any(pattern.search(text) for pattern in _CURRENT_PATTERNS):
        return "current"
    return None


# Deterministic support-lane regression matrix.
for _support_case in (
    "My brother wants to die.",
    "My daughter says she is going to end her life.",
    "My colleague is suicidal.",
    "Someone I love is talking about killing herself.",
    "My friend says he doesn't want to live.",
):
    if normalize_safety_state(_support_case) != "support":
        raise RuntimeError(f"Safety support invariant failed: {_support_case!r}")

for _non_support_case in (
    "What does suicide prevention mean?",
    "We discussed a historical account of suicide in class.",
):
    if normalize_safety_state(_non_support_case) is not None:
        raise RuntimeError(f"Safety false-positive invariant failed: {_non_support_case!r}")

# v488.60 boundary invariant: a short answer must remain inside the active
# safety conversation when the preceding safety question is still open.
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

    # A clearly hypothetical/calibration question containing the generic phrase
    # "immediate danger" is not a personal crisis disclosure. Stop before semantic
    # recall can re-escalate that same third-person scenario. Explicit first-person
    # self-harm/current-risk patterns have already returned above.
    normalized_query = " ".join(str(query or "").strip().casefold().split())
    if (
        _GENERIC_IMMEDIATE_DANGER_PATTERN.search(normalized_query)
        and is_hypothetical_safety_discussion(normalized_query)
        and not any(
            pattern.search(normalized_query)
            for pattern in (*_ACUTE_PATTERNS, *_PLAN_PATTERNS, *_IMMEDIACY_PATTERNS, *_CURRENT_PATTERNS)
        )
    ):
        return None

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
                "someone you can be with",
                "contact emergency",
                "safe from acting",
                "might act on these thoughts",
                "thinking about killing yourself",
                "made a plan to act",
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
    """Restore the next native safety movement when a response omits its question.

    This is a continuity guard within the standalone deterministic state machine.
    It prevents a live safety interruption from becoming a dead end and advances
    the visitor through the governed safety sequence rather than repeating a question.
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


def _last_safety_message(history: str) -> str:
    """Return the most recent assistant-facing safety message from serialized history."""
    for line in reversed(str(history or "").splitlines()):
        match = re.match(r"^\s*(?:assistant|system)\s*:\s*(.+)$", line, re.I)
        if match:
            value = match.group(1).strip()
            if value and not value.casefold().startswith("question:"):
                return value
    return ""


def _safety_stage_from_history(history: str, question: str, fallback_state: str) -> str:
    """Disambiguate repeated safety questions using the preceding assistant movement."""
    message = " ".join(_last_safety_message(history).casefold().split())
    if "you have taken a step to stay connected to support" in message:
        return "release"
    if "it is important to stay connected to support" in message:
        return "recovery"
    if "if you have reached someone or emergency support" in message:
        return "acute_contact"
    if "if someone is with you" in message:
        return "acute_connection"
    if "i hear you. i am going to stop asking you to repeat the same safety step" in message:
        return "acute_hold"
    if "please stay away from anything you could use to hurt yourself" in message:
        return "acute_followthrough"
    if "please move away from anything you could use to hurt yourself" in message:
        return "acute"
    if "you do not have to carry this entirely by yourself" in message:
        return "support"
    if "i want to understand how close these thoughts feel to action" in message:
        return "plan"
    if "i'm taking your answer seriously" in message:
        return "immediacy"
    if "i want to take what you just said seriously" in message:
        return "current"
    return _safety_stage_from_question(question, fallback_state)


def _safety_stage_from_question(question: str, fallback_state: str) -> str:
    """Recover the active deterministic stage from the last safety question."""
    q = " ".join(str(question or "").strip().casefold().split())
    fallback = str(fallback_state or "current").strip().casefold()
    if "are you thinking about killing yourself right now" in q:
        return "current"
    if "have you made a plan to act on these thoughts" in q:
        return "plan"
    if "do you feel you might act on these thoughts right now" in q or "do you think you might act on these thoughts right now" in q:
        return "immediacy"
    if "have you moved away from anything you could use to hurt yourself" in q:
        return "acute"
    if "is there someone you can be with right now" in q:
        return "support"
    if "is there someone you trust who can stay with you right now" in q:
        return "acute_followthrough"
    if "can you contact emergency or crisis support now" in q:
        return "acute_contact"
    if "what is making it difficult" in q or "what is preventing you" in q:
        return "acute_barrier"
    if "are you safe from acting on these thoughts right now" in q:
        return fallback if fallback in {"acute_connection", "acute_contact", "recovery"} else "acute_connection"
    return fallback


def _safety_answer_class(query: str, stage: str) -> dict[str, Any]:
    """Deterministically decode a reply only in relation to the active question."""
    text = " ".join(str(query or "").strip().casefold().split()).replace("’", "'")
    if not text:
        return {"answer_class": "uncertain", "current_suicidal": False, "imminent": False, "plan": False, "self_harm": False}

    if re.search(r"\b(?:i(?:'ve| have)\s+(?:overdosed|taken an overdose)|i\s+(?:overdosed|took an overdose)|i\s+(?:have\s+)?(?:hurt|harmed)\s+myself|i am attempting suicide)\b", text, re.I):
        return {"answer_class": "yes", "current_suicidal": True, "imminent": True, "plan": False, "self_harm": True}

    if stage == "acute_contact":
        negative_contact = re.search(
            r"\b(?:i (?:cannot|can't|could not|couldn't|have not|haven't|am unable to)|no one answered|nobody answered|not yet)\b.*\b(?:call|contact|reach|phone)\b",
            text,
            re.I,
        )
        positive_contact = re.search(
            r"\b(?:i (?:have )?(?:called|contacted|reached)|i'm on the phone|someone answered|help is on the way)\b",
            text,
            re.I,
        )
        if negative_contact:
            answer = "no"
        elif positive_contact:
            answer = "yes"
        else:
            answer = "uncertain"
        return {"answer_class": answer, "current_suicidal": False, "imminent": False, "plan": False, "self_harm": False}

    if stage == "acute_connection":
        negative_connection = re.search(r"\b(?:can't|cannot|couldn't|could not|do not|don't|no|nobody|no one|not able)\b.*\b(?:call|contact|text|message|reach|phone|stay on the phone)\b", text, re.I)
        positive_connection = re.search(r"\b(?:i can|i could|i will|i'll|i am able to|i'm able to|i can probably|i could probably)\b.*\b(?:call|contact|text|message|reach|phone|stay on the phone)\b", text, re.I)
        if negative_connection:
            answer = "no"
        elif positive_connection:
            answer = "yes"
        else:
            answer = "uncertain"
        return {"answer_class": answer, "current_suicidal": False, "imminent": False, "plan": False, "self_harm": False}

    if stage == "acute" and re.search(r"\b(?:someone|a person|my (?:friend|partner|family|husband|wife|parent|sister|brother))\s+(?:is|are)\s+(?:with|here|beside)\s+me\b", text, re.I):
        answer = "uncertain"
    elif stage == "acute_followthrough" and re.search(r"\b(?:someone|a person|my (?:friend|partner|family|husband|wife|parent|sister|brother))\s+(?:is|are)\s+(?:with|here|beside)\s+me\b", text, re.I):
        answer = "yes"
    elif re.search(r"\b(?:i don't want to answer|i do not want to answer|prefer not to answer|i would rather not answer|not answering)\b", text, re.I):
        answer = "refusal"
    elif re.search(r"\b(?:maybe|not sure|i don't know|i do not know|unsure|uncertain|hard to say|i can't tell|i cannot tell)\b", text, re.I):
        answer = "uncertain"
    elif re.match(r"^(?:yes|yeah|yep|yup|i do|i am|i might|i think so|probably|definitely|sometimes yes)\b", text, re.I):
        answer = "yes"
    elif re.match(r"^(?:no|nope|not now|not really|i don't|i do not|i won't|i will not|i am not|i'm not)\b", text, re.I):
        answer = "no"
    else:
        answer = "uncertain"

    return {"answer_class": answer, "current_suicidal": False, "imminent": False, "plan": False, "self_harm": False}


def _safety_transition(stage: str, answer: Mapping[str, Any]) -> str:
    """Port of the protected deterministic safety transition table."""
    answer_class = str(answer.get("answer_class") or "uncertain")
    if bool(answer.get("self_harm")):
        return "acute"
    if stage == "current":
        if answer_class == "yes": return "immediacy"
        if answer_class == "no": return "plan"
        return "support"
    if stage == "immediacy":
        if answer_class == "yes" or bool(answer.get("imminent")): return "acute"
        if answer_class == "no": return "plan"
        return "support"
    if stage == "plan":
        return "support"
    if stage == "support":
        return "recovery" if answer_class == "yes" else "acute_followthrough"
    if stage == "acute":
        return "acute_connection" if answer_class == "yes" else "acute_followthrough"
    if stage == "acute_followthrough":
        return "acute_connection" if answer_class == "yes" else "acute_contact"
    if stage == "acute_connection":
        return "recovery" if answer_class == "yes" else "acute_contact"
    if stage == "acute_contact":
        return "recovery" if answer_class == "yes" else "acute_barrier"
    if stage == "acute_barrier":
        return "recovery" if answer_class == "yes" else "acute_hold"
    if stage == "acute_hold":
        return "acute_hold"
    if stage == "recovery":
        return "release" if answer_class == "yes" else "acute_contact"
    return "acute_contact"


def _safety_response(stage: str, emergency_resolution: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Deterministic visitor-facing movement; emergency numbers come only from EI."""
    selection = dict((emergency_resolution or {}).get("selection") or {})
    has_resources = selection.get("selection_status") in {"SELECTED", "MULTIPLE_EQUIVALENT"}
    if stage == "current":
        message = "Thank you for telling me. I want to take what you just said seriously."
        question = "Are you thinking about killing yourself right now?"
    elif stage == "plan":
        message = "Thank you for telling me. I want to understand how close these thoughts feel to action."
        question = "Have you made a plan to act on these thoughts?"
    elif stage == "immediacy":
        message = "I'm taking your answer seriously. I want to make sure you are not facing this alone."
        question = "Do you feel you might act on these thoughts right now?"
    elif stage == "support":
        message = "You do not have to carry this entirely by yourself."
        question = "Is there someone you can be with right now?"
    elif stage == "acute":
        message = "Please move away from anything you could use to hurt yourself. Then bring another person into this if you can."
        question = "Have you moved away from anything you could use to hurt yourself?"
    elif stage == "acute_followthrough":
        message = "Please stay away from anything you could use to hurt yourself. If that is difficult, we can stay with that problem rather than asking you to repeat the same step."
        question = "Is there someone you trust who can stay with you right now?"
    elif stage == "acute_connection":
        message = "If someone is with you, please stay connected with them while we make sure the immediate danger has passed. If no one is with you, contact someone you trust now."
        question = "Are you safe from acting on these thoughts right now?"
    elif stage == "acute_contact":
        message = "If you have reached someone or emergency support, stay connected. If you have not, contact emergency or crisis support now."
        question = "Are you safe from acting on these thoughts right now?"
    elif stage == "acute_barrier":
        message = "I hear that something is making the next safety step difficult. We do not need to pretend that it is easy. Please stay away from anything you could use to hurt yourself and use an emergency or crisis option if you can."
        question = "What is making it difficult to move away from harm or get another person involved right now?"
    elif stage == "acute_hold":
        message = "I hear you. I am going to stop asking you to repeat the same safety step. Please stay away from anything you could use to hurt yourself and use emergency or crisis support now. If you have already injured yourself or taken something, seek emergency medical care now."
        question = ""
    elif stage == "recovery":
        message = "It is important to stay connected to support. We do not need to return to the other conversation yet. First, I want to make sure the immediate danger has passed."
        question = "Are you safe from acting on these thoughts right now?"
    elif stage == "release":
        message = "You have taken a step to stay connected to support. You do not have to return to the other conversation yet."
        question = ""
    else:
        message = "If you may be in immediate danger, contact the emergency service where you are or go to the nearest emergency department now."
        question = "Do you think you might act on these thoughts right now?"

    if stage in {"acute_followthrough", "acute_connection", "acute_contact", "acute_barrier", "acute_hold", "recovery"}:
        note = "If you have already injured yourself or taken something, seek emergency medical care now."
    elif has_resources:
        note = "If you are in immediate danger, use the verified emergency service above or go to the nearest emergency department."
    else:
        note = "If you may act on these thoughts now, contact the emergency service where you are or go to the nearest emergency department rather than waiting for an online directory."

    return {
        "safety": "recovery" if stage == "release" else stage,
        "safety_interrupt": True,
        "safety_message": message,
        "safety_question": question,
        "safety_note": note,
        "safety_resources": [],
        "safety_location_required": not has_resources,
        "country": "",
        "safety_release_ready": stage == "release",
    }


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
        raise RuntimeError("Standalone safety state machine did not return an active safety interrupt.")
    if not safety_message:
        raise RuntimeError("Standalone safety state machine returned no safety message.")

    # The local deterministic state machine owns safety state and language.
    # Emergency Intelligence alone owns phone resources. Never merge any
    # unscoped/static hotline list into a visitor response.
    emergency_resources = _resource_projection(emergency_resolution or {})
    resources = [dict(resource) for resource in emergency_resources if isinstance(resource, Mapping)]

    selection = dict((emergency_resolution or {}).get("selection") or {})
    emergency_status = str(selection.get("selection_status") or "")
    emergency_location = dict((emergency_resolution or {}).get("location") or {})
    resolved_location = dict(emergency_location.get("location") or {})
    resolved_country_data = dict(resolved_location.get("country") or {})
    verified_resource_country = str(resolved_country_data.get("value") or "").strip().upper()
    selected_country = str(resolved_country_data.get("value") or country or "").strip().upper()
    resources_are_location_grounded = bool(
        emergency_status in {"SELECTED", "MULTIPLE_EQUIVALENT"}
        and verified_resource_country
        and selected_country
        and verified_resource_country == selected_country
        and resources
    )
    if not resources_are_location_grounded:
        # A country guess from an untrusted source is not location evidence. Keep the immediate
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
    """Generate the first safety movement locally without an HRN or LLM call."""
    state = str(safety_state or "").strip().casefold()
    data = _safety_response(state, emergency_resolution)
    normalized = normalize_safety_resolution(
        data,
        requested_state=state,
        country=country,
        emergency_resolution=emergency_resolution,
    )
    normalized["resolver_status"] = "deterministic_initial_fast_path"
    normalized["safety_continuity_guard"] = "deterministic_initial_movement"
    normalized["next_movement"] = normalized.get("safety_question") or ""
    normalized["safety_presence"] = _presence_signal(query)
    normalized["safety_question_context"] = ""
    return normalized


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
    emergency_endpoint: str | None = None,
) -> dict[str, Any]:
    """Resolve a safety turn locally; EI is called only for verified resources."""
    emergency_endpoint_url = str(
        emergency_endpoint
        or os.getenv("EMERGENCY_INTELLIGENCE_ENDPOINT")
        or DEFAULT_EMERGENCY_INTELLIGENCE_ENDPOINT
    ).strip()

    location_input = _emergency_location(country=country, location=location)
    previous_question = safety_question or _last_safety_question(history)
    presence = _presence_signal(query)
    stage = _safety_stage_from_history(history, previous_question, safety_state)

    initial_safety_fast_path = (
        not str(history or "").strip()
        and not str(safety_question or "").strip()
        and stage in {"acute", "plan", "immediacy", "current"}
    )

    emergency_resolution: Mapping[str, Any] = {}
    try:
        timeout = 1.2 if initial_safety_fast_path else 3.0
        emergency_resolution = _request_emergency_intelligence(
            endpoint=emergency_endpoint_url,
            service_need=service_need,
            safety_state=stage,
            location=location_input,
            timeout=timeout,
        )
    except Exception as exc:
        print(f"Emergency Intelligence unavailable; deterministic safety remains active: {exc}")
        emergency_resolution = {}

    if initial_safety_fast_path:
        return _initial_deterministic_safety_response(
            query=query,
            safety_state=stage,
            country=country,
            emergency_resolution=emergency_resolution,
        )

    answer = _safety_answer_class(query, stage)
    next_stage = _safety_transition(stage, answer)

    if stage == "support" and next_stage == "recovery":
        data = _safety_response("recovery", emergency_resolution)
        data["safety_message"] = (
            "You have taken a step toward support. You do not have to return to the other conversation yet."
        )
        data["safety_question"] = "Are you safe from acting on these thoughts right now?"
        data["safety_release_ready"] = False
        next_stage = "recovery"
    elif stage == "recovery" and next_stage == "release":
        data = _safety_response("release", emergency_resolution)
        next_stage = "recovery"
    elif stage == "recovery" and next_stage != "release":
        next_stage = "acute_followthrough"
        data = _safety_response(next_stage, emergency_resolution)
    else:
        data = _safety_response(next_stage, emergency_resolution)

    normalized = normalize_safety_resolution(
        data,
        requested_state=next_stage,
        country=country,
        emergency_resolution=emergency_resolution,
    )

    # Do not assert that another person is physically present unless the
    # visitor has said so. The deterministic wording above is conditional,
    # but retain a defensive repair for future wording changes.
    message = str(normalized.get("safety_message") or "")
    unsupported_presence_claim = re.search(
        r"\b(?:it helps (?:that|to have)|you have|there is)\b.{0,55}"
        r"\b(?:someone|somebody|another person|them)\b.{0,45}"
        r"\b(?:with you|with them|stay together)\b|"
        r"\b(?:someone|somebody|another person)\s+is\s+with\s+you\b",
        message,
        re.I,
    )
    if presence != "present" and unsupported_presence_claim:
        normalized["safety_message"] = "Thank you for answering. Let's focus on keeping you safe right now."
        normalized["safety_question"] = "Is there someone you trust who can stay with you right now?"
        normalized["safety_release_ready"] = False
        normalized["loop_guard"] = "unsupported_presence_claim_repaired"

    normalized["resolver_status"] = "standalone_deterministic_state_machine"
    normalized["safety_continuity_guard"] = "local_deterministic_transition"
    normalized["safety_presence"] = presence
    normalized["safety_question_context"] = previous_question
    normalized["safety_answer_class"] = answer.get("answer_class", "uncertain")
    normalized["emergency_resolution_status"] = str(
        (emergency_resolution.get("selection") or {}).get("selection_status") or "unavailable"
    )
    return normalized


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

# Safety trigger matrix invariants: explicit third-person concern must enter
# the support lane without converting ordinary educational discussion into a crisis.
for _support_case in (
    "My brother wants to die.",
    "My daughter says she is going to end her life.",
    "My colleague is suicidal.",
    "Someone I love is talking about killing herself.",
    "My friend says he doesn't want to live.",
):
    if normalize_safety_state(_support_case) != "support":
        raise RuntimeError(f"USE safety matrix invariant failed: third-person support case lost: {_support_case!r}")
for _non_support_case in (
    "What does the phrase suicide prevention mean?",
    "We discussed a historical account of suicide in class.",
):
    if normalize_safety_state(_non_support_case) is not None:
        raise RuntimeError(f"USE safety matrix invariant failed: informational case interrupted: {_non_support_case!r}")


def safety_intelligence_snapshot() -> dict[str, Any]:
    return {
        "contract_version": SAFETY_INTELLIGENCE_CONTRACT_VERSION,
        "authority": "Guide_Standalone_Deterministic_Safety_State_Machine_and_Emergency_Intelligence",
        "emergency_intelligence_endpoint": DEFAULT_EMERGENCY_INTELLIGENCE_ENDPOINT,
        "resource_owner": "Emergency Intelligence",
        "resource_contract": "living-archive/emergency/v1/resolve",
        "language_owner": "Guide_Standalone_Deterministic_Safety_State_Machine",
        "guide_role": "sitewide_boundary_and_contract_preservation",
        "ordinary_hrn_composition_bypassed": True,
        "hrn_dependency": False,
        "standalone_safety_state_machine": True,
        "retrieval_bypassed": True,
        "emergency_registry_authority": "Emergency Intelligence",
        "safety_loop_guard": "standalone_deterministic_state_machine",
        "continuity_repair": "state_aware_native_next_movement",
    }

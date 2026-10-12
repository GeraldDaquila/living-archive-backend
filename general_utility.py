"""Bounded General Utility capability for USE/The Guide.

This module is intentionally not a specialist. USE may invoke it only after
macro routing determines that no narrower specialist or direct canonical asset
should handle the visitor request.

The utility consumes evidence already supplied by USE. It does not perform web
retrieval, own routing authority, select a canonical doorway authoritatively,
or rewrite specialist voice.

Contract:
    query + supplied documents -> structured bounded contribution
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Iterable


CONTRACT_VERSION = "v1"
CAPABILITY_NAME = "general_utility"


@dataclass(frozen=True)
class GeneralUtilityResult:
    status: str
    mode: str
    answer: str = ""
    evidence: tuple[dict[str, str], ...] = field(default_factory=tuple)
    canonical_candidates: tuple[dict[str, str], ...] = field(default_factory=tuple)
    reason: str = ""
    contract_version: str = CONTRACT_VERSION
    capability: str = CAPABILITY_NAME

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "mode": self.mode,
            "answer": self.answer,
            "evidence": list(self.evidence),
            "canonical_candidates": list(self.canonical_candidates),
            "reason": self.reason,
            "contract_version": self.contract_version,
            "capability": self.capability,
        }


def _clean(text: Any) -> str:
    value = re.sub(r"<[^>]+>", " ", str(text or ""))
    value = re.sub(r"https?://\S+|www\.\S+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _valid_url(doc: dict[str, Any]) -> str:
    value = str(doc.get("url") or doc.get("canonical_url") or "").strip()
    return value if re.match(r"^https://\S+$", value, re.I) else ""


def _dedupe_documents(documents: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for doc in documents:
        if not isinstance(doc, dict):
            continue
        title = _clean(doc.get("title"))
        url = _valid_url(doc)
        text = _clean(doc.get("text"))
        if not title or not url or not text:
            continue
        key = (url, title.casefold())
        if key in seen:
            continue
        seen.add(key)
        output.append({"title": title, "url": url, "text": text})
    return output


def inquiry_shape(query: str) -> dict[str, str | bool]:
    """Classify inquiry shape only; USE remains routing authority."""
    q = _clean(query).casefold()
    risk = bool(
        re.search(
            r"\b(?:suicid\w*|self[- ]harm|overdose|immediate danger|kill myself|"
            r"kill yourself|end my life|take my own life|hurt myself|harm myself)\b",
            q,
        )
    )
    recommendation = bool(
        re.search(
            r"\b(?:recommend|recommendation|what should i read|where should i start|"
            r"what can i read|which .*?(?:read|essay|article))\b",
            q,
        )
    )
    navigation = bool(
        re.search(
            r"\b(?:where can i find|where do i find|find the|show me|take me to|"
            r"browse|explore the|link me to)\b",
            q,
        )
    )
    lived = bool(
        re.search(
            r"\b(?:i feel|i'm feeling|i am feeling|i can't|i cannot|i keep|"
            r"it hurts|my grief|my fear|my anger|my loneliness|my relationship|"
            r"my partner|my loss|heartbreak|betrayal|overwhelmed|afraid|scared|"
            r"letting go|forgive|forgiveness)\b",
            q,
        )
    )
    conceptual = bool(
        re.match(
            r"^(?:what is|what's|who is|who was|when did|where is|where was|"
            r"why is|why does|how does|what does|what are|define|explain)\b",
            q,
        )
    )
    if risk:
        mode = "risk"
    elif recommendation or navigation:
        mode = "orientation"
    elif lived:
        mode = "lived_experience"
    elif conceptual:
        mode = "conceptual"
    else:
        mode = "open_inquiry"
    return {
        "risk": risk,
        "recommendation": recommendation,
        "navigation": navigation,
        "lived": lived,
        "conceptual": conceptual,
        "mode": mode,
    }


def _candidate_sentences(query: str, documents: list[dict[str, Any]], limit: int = 12) -> list[dict[str, Any]]:
    query_terms = set(re.findall(r"[a-z]{4,}", _clean(query).casefold()))
    ranked: list[dict[str, Any]] = []
    seen: set[str] = set()
    for doc in documents:
        title_terms = set(re.findall(r"[a-z]{4,}", doc["title"].casefold()))
        for sentence in re.split(r"(?<=[.!?])\s+", doc["text"]):
            sentence = sentence.strip()
            if len(sentence.split()) < 6:
                continue
            key = re.sub(r"\W+", " ", sentence.casefold()).strip()
            if not key or key in seen:
                continue
            seen.add(key)
            words = set(re.findall(r"[a-z]{4,}", sentence.casefold()))
            score = 10 * len(query_terms & words) + 8 * len(query_terms & title_terms)
            if re.search(
                r"\b(?:is|are|means|refers to|describes|represents|relates to|"
                r"meaning|stewardship|creation|growth|loss|grief|relationship|"
                r"forgiveness|attention|systems|human)\b",
                sentence.casefold(),
            ):
                score += 15
            ranked.append(
                {
                    "score": score,
                    "sentence": sentence,
                    "title": doc["title"],
                    "url": doc["url"],
                }
            )
    ranked.sort(key=lambda item: (-int(item["score"]), item["title"].casefold(), item["url"]))
    return ranked[:limit]


def _claim_type(sentence: str) -> str:
    low = sentence.casefold()
    if re.search(r"\b(?:is|are|means|refers to|describes|represents)\b", low):
        return "definition"
    if re.search(
        r"\b(?:relates to|connected with|linked to|pathway|meaning|relationship|"
        r"stewardship|creation|growth|loss|grief|forgiveness)\b",
        low,
    ):
        return "relationship"
    return "exploration"


def _extract_claims(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    seen: set[str] = set()
    for candidate in candidates:
        text = re.sub(r"\s+", " ", candidate["sentence"]).strip().rstrip(".")
        key = re.sub(r"\W+", " ", text.casefold()).strip()
        if not text or key in seen:
            continue
        seen.add(key)
        claims.append(
            {
                "text": text,
                "title": candidate["title"],
                "url": candidate["url"],
                "score": int(candidate["score"]),
                "claim_type": _claim_type(text),
            }
        )
    return claims


def _subject(query: str) -> str:
    return re.sub(
        r"^(?:what is|what's|define|explain|what does|who is|who was|where is|"
        r"where was|why is|why does|how does)\s+",
        "",
        _clean(query),
        flags=re.I,
    ).rstrip(" ?.!:")


def _build_conceptual_answer(query: str, claims: list[dict[str, Any]]) -> str:
    if not claims:
        return ""
    subject = _subject(query)
    if not subject:
        return ""
    primary = claims[0]
    support = []
    for claim in claims[1:4]:
        sentence = claim["text"].rstrip(".") + "."
        if sentence.casefold() not in {item.casefold() for item in support}:
            support.append(sentence)
    paragraphs = [
        f"The closest supported material I found is [{primary['title']}]({primary['url']}).",
        f"Taken together, the available material approaches {subject} through several related perspectives rather than a single fixed definition.",
    ]
    if support:
        paragraphs.append(" ".join(support[:2]))
    return "\n\n".join(paragraphs)


def _build_lived_answer(query: str, claims: list[dict[str, Any]]) -> str:
    opening = (
        "What you are describing does not have to be reduced to a conclusion before it can be understood."
    )
    if not claims:
        return opening
    anchor = claims[0]
    return "\n\n".join(
        [
            opening,
            f"The Archive offers a related lens in [{anchor['title']}]({anchor['url']}), where the material explores {anchor['text'].rstrip('.')}. This is one way into the question, not a claim that it completely explains your experience.",
            "You can stay with that lens, follow the connected material, or return with another part of the question that feels more relevant.",
        ]
    )


def _build_orientation_answer(claims: list[dict[str, Any]]) -> str:
    if not claims:
        return ""
    primary = claims[0]
    return "\n\n".join(
        [
            f"A useful place to begin is [{primary['title']}]({primary['url']}).",
            "This doorway is offered as a place to explore the question, not as a complete answer. The next step can be to notice which part of it you want to stay with.",
        ]
    )


def _canonical_candidates(claims: list[dict[str, Any]], limit: int = 3) -> tuple[dict[str, str], ...]:
    candidates = []
    seen = set()
    for claim in claims:
        key = claim["url"]
        if key in seen:
            continue
        seen.add(key)
        candidates.append({"title": claim["title"], "url": claim["url"]})
        if len(candidates) >= limit:
            break
    return tuple(candidates)


def build_contribution(
    query: str,
    documents: Iterable[dict[str, Any]],
    *,
    route_authorized: bool = False,
) -> GeneralUtilityResult:
    """Build a bounded contribution; never pretend success when evidence is absent."""
    if not route_authorized:
        return GeneralUtilityResult(
            status="NOT_AUTHORIZED",
            mode="",
            reason="USE has not authorized general-utility fallback.",
        )

    clean_query = _clean(query)
    if not clean_query:
        return GeneralUtilityResult(
            status="UNAVAILABLE",
            mode="",
            reason="Empty query.",
        )

    profile = inquiry_shape(clean_query)
    if profile["risk"]:
        return GeneralUtilityResult(
            status="DELEGATE",
            mode="risk",
            reason="Safety-sensitive inquiry should remain under the site's safety route.",
        )

    docs = _dedupe_documents(documents)
    claims = _extract_claims(_candidate_sentences(clean_query, docs))
    if profile["mode"] == "orientation":
        answer = _build_orientation_answer(claims)
    elif profile["mode"] == "lived_experience":
        answer = _build_lived_answer(clean_query, claims)
    elif profile["mode"] == "conceptual":
        answer = _build_conceptual_answer(clean_query, claims)
    else:
        answer = ""
        if claims:
            anchor = claims[0]
            answer = (
                f"The Archive offers a related lens in [{anchor['title']}]({anchor['url']}), "
                "and the surrounding material can help you explore the question from more than one angle."
            )

    if not answer:
        return GeneralUtilityResult(
            status="NEEDS_RETRY",
            mode=str(profile["mode"]),
            reason="Supplied evidence was insufficient for a bounded contribution.",
        )

    evidence = tuple(
        {"title": claim["title"], "url": claim["url"], "text": claim["text"]}
        for claim in claims[:5]
    )
    return GeneralUtilityResult(
        status="READY",
        mode=str(profile["mode"]),
        answer=answer,
        evidence=evidence,
        canonical_candidates=_canonical_candidates(claims),
    )

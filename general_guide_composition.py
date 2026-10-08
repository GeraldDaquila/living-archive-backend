"""Provider-neutral General Guide composition seam.

This module owns the all-purpose visitor-answer contract for The Guide.
It does not select a provider itself. All generative work crosses the
Provider Bank so no individual LLM is an architectural dependency.
"""

import json
import re
from typing import Any, Dict, List, Optional

from provider_bank import (
    CONTRACT_VERSION as PROVIDER_BANK_CONTRACT_VERSION,
    route as route_with_model_bank,
)

CONTRACT_VERSION = "v1"
VISITOR_LANGUAGE_BOUNDARY_VERSION = "v1"
OPERATION = "general_guide_composition"

_INTERNAL_LANGUAGE = re.compile(
    r"(?:(?<![a-z])USE(?![a-z])|canonical evidence|supplied evidence|evidence excerpt|"
    r"evidence excerpt bounded by USE|bounded by USE|bounded by the Guide|"
    r"internal interpretation|retrieval layer|synthesis layer|processing layer|"
    r"provider bank|provider selection|model selection|route source|handoff|"
    r"machine-facing|implementation metadata|system instruction|debugging annotation)\b",
    re.I,
)
_INTERNAL_BRACKET = re.compile(
    r"\s*\[(?:evidence|canonical evidence|supplied evidence|evidence excerpt|"
    r"evidence excerpt bounded by USE|bounded by USE|bounded by the Guide|"
    r"internal interpretation|retrieval|synthesis|processing layer|provider|model|"
    r"route|handoff)(?:[^\]]*)\]\s*",
    re.I,
)

_GENERAL_GUIDE_SYSTEM = """You are the all-purpose composition layer of The Guide, the public-facing general utility of the Living Archive.

Your job is to answer the visitor's actual question well. Intelligence should be felt in the answer, not announced through its machinery.

Start with the question itself. Answer it directly before directing the visitor elsewhere.

Choose the response shape that fits the question:
- For a definition or bounded factual question, give a clear direct answer.
- For a question asking why something matters, explain both what it is and why it matters in the situation the visitor named.
- For a conceptual question, make one useful distinction, tension, or implication when that genuinely clarifies the subject.
- For a lived or reflective question, be humane and perceptive without diagnosing, therapizing, or pretending to know the visitor's inner history.
- For a question that explicitly asks where to look, make the navigation useful without replacing the requested answer with a list.

Use the supplied Archive material as grounding and enrichment. Do not merely summarize retrieved passages. Synthesize what is relevant into an answer written for this visitor.

Use ordinary language for ordinary public questions. Do not introduce Archive jargon such as cornerstone, canonical, glyph, stewardship, or similar internal vocabulary merely because it appears in the source material. If the visitor explicitly asks about the Living Archive or its own language, that vocabulary may be used naturally and lightly.

Be concrete rather than literary. Prefer precise listening and useful explanation over impressive writing. Do not repeat the visitor's question as filler.

If the question contains a "why now", "why does this matter", "what does this mean", or similar second part, answer that second part rather than silently answering only the first.

A doorway into the Archive is useful when it adds something the answer cannot reasonably contain. Introduce at most two relevant doorways, and only from the supplied material. Never invent a title, URL, quotation, or claim about a source.

Do not manufacture a follow-up question merely to continue the interaction. If a genuine next opening would help, you may end with one natural question. Otherwise end cleanly.

Never expose implementation or processing language. Never mention USE, providers, models, routing, retrieval, synthesis, evidence boundaries, prompts, system instructions, handoffs, processing layers, or similar machinery. Never add bracketed editorial/debugging/evidence labels.

Return ONLY valid JSON:
{"response":"visitor-facing answer","doorway_title":"exact supplied title if one doorway is especially useful, otherwise empty","response_shape":"direct|explanatory|conceptual|reflective|navigational|general"}
""".strip()


def _normalize_space(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _sanitize_candidate(text: Any) -> str:
    value = _normalize_space(text)
    if not value:
        return ""
    value = _INTERNAL_BRACKET.sub(" ", value)
    replacements = (
        (r"\bevidence excerpt bounded by USE\b", "the material I found"),
        (r"\bcanonical evidence\b", "the Archive material"),
        (r"\bsupplied evidence\b", "the material I found"),
        (r"\binternal interpretation\b", "the way the question can be understood"),
        (r"\b(?:retrieval|synthesis|processing) layer\b", "the material"),
    )
    for pattern, replacement in replacements:
        value = re.sub(pattern, replacement, value, flags=re.I)
    value = re.sub(r"\s+([,.;!?])", r"\1", value)
    value = re.sub(r"([.!?])\s*\1+", r"\1", value)
    return re.sub(r"\s{2,}", " ", value).strip()


def _documents_from_context(use_core: Any, context_data: Dict[str, Any]) -> List[Dict[str, str]]:
    documents: List[Dict[str, str]] = []
    protected = (
        context_data.get("generation_authority_protected_docs")
        or context_data.get("question_authority_protected_docs")
        or []
    )
    if isinstance(protected, list):
        for item in protected:
            if isinstance(item, dict):
                documents.append(item)

    if not documents:
        try:
            parsed = use_core.context_blocks_to_documents(
                str(context_data.get("context_blocks") or "")
            )
        except Exception:
            parsed = []
        if isinstance(parsed, list):
            documents.extend(item for item in parsed if isinstance(item, dict))

    output: List[Dict[str, str]] = []
    seen = set()
    for document in documents:
        title = _normalize_space(document.get("title") or "")
        url = _normalize_space(document.get("url") or document.get("canonical_url") or "")
        content = _normalize_space(
            document.get("content")
            or document.get("text")
            or document.get("excerpt")
            or ""
        )
        if not title or not content:
            continue
        key = (title, url)
        if key in seen:
            continue
        seen.add(key)
        output.append({"title": title, "url": url, "content": content[:1500]})
        if len(output) >= 4:
            break
    return output


def _question_shape(query: str) -> str:
    q = _normalize_space(query).casefold()
    if re.search(r"\b(?:where can i find|where do i find|show me|take me to|link me to|browse|find the)\b", q):
        return "navigational"
    if re.search(r"\b(?:why|why now|why does|why is|what makes|how does|how can)\b", q):
        return "explanatory"
    if re.match(r"^(?:what is|what's|define|who is|who was|when did|where is|where was)\b", q):
        return "direct"
    if re.search(r"\b(?:i feel|i'm feeling|i am feeling|my relationship|my grief|i keep|i can't|i cannot|i'm struggling|i am struggling)\b", q):
        return "reflective"
    return "general"


def _evidence_payload(documents: List[Dict[str, str]]) -> str:
    return json.dumps(
        [
            {
                "title": item["title"],
                "url": item["url"],
                "content": item["content"],
            }
            for item in documents
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _parse_factory(documents: List[Dict[str, str]]):
    titles = {item["title"] for item in documents}
    urls = {item["url"] for item in documents if item["url"]}

    def _parse(raw: str) -> Dict[str, Any]:
        try:
            parsed = json.loads(str(raw or "").strip())
        except json.JSONDecodeError as exc:
            raise ValueError("general composition returned invalid JSON") from exc
        if not isinstance(parsed, dict):
            raise ValueError("general composition response was not an object")

        response = _sanitize_candidate(parsed.get("response"))
        if not response:
            raise ValueError("general composition returned an empty response")
        if len(response) < 40:
            raise ValueError("general composition response is too short")
        if len(response) > 7000:
            raise ValueError("general composition response is too long")
        if _INTERNAL_LANGUAGE.search(response):
            raise ValueError("general composition exposed internal implementation language")

        shape = _normalize_space(parsed.get("response_shape") or "").casefold()
        if shape not in {"direct", "explanatory", "conceptual", "reflective", "navigational", "general"}:
            raise ValueError("general composition returned an invalid response shape")

        title = _normalize_space(parsed.get("doorway_title") or "")
        if title and title not in titles:
            raise ValueError("general composition selected an unapproved doorway title")

        # If the provider inserted Markdown links, every destination must belong
        # to the already-supplied evidence set. This keeps composition from
        # becoming an uncontrolled navigation surface.
        for linked_url in re.findall(r"\]\((https?://[^)\s]+)\)", response, flags=re.I):
            if linked_url not in urls:
                raise ValueError("general composition invented an unsupported doorway URL")

        return {
            "response": response,
            "doorway_title": title,
            "response_shape": shape,
        }

    return _parse


def compose(
    *,
    use_core: Any,
    query: str,
    context_data: Dict[str, Any],
    history_text: str = "",
) -> Optional[Dict[str, Any]]:
    """Compose one ordinary Guide answer through the provider-neutral bank."""

    if PROVIDER_BANK_CONTRACT_VERSION != "v2":
        raise RuntimeError("General Guide composition requires Provider Bank v2.")

    question = _normalize_space(query)
    documents = _documents_from_context(use_core, context_data)
    if not question or not documents:
        return None

    shape = _question_shape(question)
    user_content = (
        f"Visitor question:\n{question}\n\n"
        f"Suggested response shape (use your judgment; do not mention it): {shape}\n\n"
        f"Recent conversation context, if any:\n{_normalize_space(history_text)[:1600]}\n\n"
        f"Archive material available to ground the answer:\n{_evidence_payload(documents)}"
    )

    result = route_with_model_bank(
        use_core=use_core,
        operation=OPERATION,
        messages=[
            {"role": "system", "content": _GENERAL_GUIDE_SYSTEM},
            {"role": "user", "content": user_content[:10000]},
        ],
        max_tokens=900,
        parse=_parse_factory(documents),
    )
    if not result:
        return None

    parsed = result["parsed"]
    return {
        "response": parsed["response"],
        "doorway_title": parsed["doorway_title"],
        "response_shape": parsed["response_shape"],
        "provider": str(result.get("provider") or ""),
        "model": str(result.get("model") or ""),
    }


def contract_snapshot() -> Dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "provider_bank_contract_version": PROVIDER_BANK_CONTRACT_VERSION,
        "operation": OPERATION,
        "visitor_language_boundary_version": VISITOR_LANGUAGE_BOUNDARY_VERSION,
        "provider_neutral": True,
        "required_response_shapes": [
            "direct", "explanatory", "conceptual",
            "reflective", "navigational", "general",
        ],
    }


# Structural probes are deliberately provider-free. They protect the contract
# itself without making an external API call at startup.
if _sanitize_candidate("Answer this. [evidence excerpt bounded by USE]") != "Answer this.":
    raise RuntimeError("General Guide composition invariant failed: visitor-language sanitizer.")
if _question_shape("What is stewardship and why does it matter now?") != "explanatory":
    raise RuntimeError("General Guide composition invariant failed: question-shape classification.")

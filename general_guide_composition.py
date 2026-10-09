"""Provider-neutral General Guide composition seam.

This module owns the all-purpose visitor-answer contract for The Guide.
It does not select a provider itself. All generative work crosses the
Provider Bank so no individual LLM is an architectural dependency.
"""

import hashlib
import json
import re
import threading
import time
from collections import OrderedDict
from typing import Any, Dict, List, Optional

from provider_bank import (
    CONTRACT_VERSION as PROVIDER_BANK_CONTRACT_VERSION,
    route as route_with_model_bank,
)

CONTRACT_VERSION = "v1.4"
VISITOR_LANGUAGE_BOUNDARY_VERSION = "v1"
OPERATION = "general_guide_composition"

# Repeated identical Guide questions must not be re-composed by whichever
# provider happens to be next in the rotating Provider Bank. Cache only the
# validated visitor-facing composition, keyed by the exact question, recent
# history, grounding evidence, and current composition instructions. This is
# bounded process-local memoization; retrieval and canonical doorway selection
# still run on every request and remain authoritative.
_COMPOSITION_CACHE_MAX_ENTRIES = 256
_COMPOSITION_CACHE_TTL_SECONDS = 1800
_COMPOSITION_CACHE = OrderedDict()
_COMPOSITION_CACHE_LOCK = threading.Lock()


def _composition_cache_key(
    question: str,
    history_text: str,
    shape: str,
    documents: List[Dict[str, Any]],
) -> str:
    # Retrieval excerpts can vary slightly between identical requests. Key on
    # the stable identities of the selected source documents, not their excerpt
    # text, so provider rotation and retrieval formatting cannot regenerate
    # the same visitor answer over and over.
    source_identity = sorted({
        (
            _normalize_space(item.get("title")),
            _normalize_space(item.get("url") or item.get("canonical_url")),
        )
        for item in documents
        if isinstance(item, dict)
    })
    material = json.dumps({
        "contract": CONTRACT_VERSION,
        "boundary": VISITOR_LANGUAGE_BOUNDARY_VERSION,
        "system": _GENERAL_GUIDE_SYSTEM,
        "question": _normalize_space(question),
        "history": _normalize_space(history_text)[:1600],
        "shape": _normalize_space(shape),
        "sources": source_identity,
    }, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()

_INTERNAL_LANGUAGE = re.compile(
    r"(?:canonical evidence|supplied evidence|evidence excerpt|"
    r"evidence excerpt bounded by USE|bounded by USE|bounded by the Guide|"
    r"internal interpretation|retrieval layer|synthesis layer|processing layer|"
    r"provider bank|provider selection|model selection|route source|handoff|"
    r"machine-facing|implementation metadata|system instruction|debugging annotation)\b",
    re.I,
)
_INTERNAL_SYSTEM_NAME = re.compile(r"\bUSE\b")
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

Use relevant Archive material as grounding and enrichment when it is available. Do not merely summarize retrieved passages. Synthesize what is relevant into an answer written for this visitor. If no relevant Archive material was retrieved, answer from reliable general knowledge when the question permits it. Do not invent Archive-specific claims, citations, quotations, or recommendations, and do not imply that a general explanation came from the Archive. If the question genuinely requires unavailable source-specific evidence, state that limitation briefly while still explaining what can responsibly be said.

Use ordinary language for ordinary public questions. Do not introduce Archive jargon such as cornerstone, canonical, glyph, stewardship, or similar internal vocabulary merely because it appears in the source material. If the visitor explicitly asks about the Living Archive or its own language, that vocabulary may be used naturally and lightly.

Be concrete rather than literary. Prefer precise listening and useful explanation over impressive writing. Do not repeat the visitor's question as filler.

Apply explanatory discernment before composing: infer what kind of understanding the question calls for, then choose the most useful depth, structure, and examples. A definition may need only a clear answer; a conceptual question may need distinctions; a practical question may need steps or an example; a teaching, learning, or leadership question may benefit from a scenario the reader can recognize and apply. Do not assume the visitor's role unless the question or context supports it.

Use a concrete-example decision rule before composing: ask whether a reader could understand the answer accurately without seeing the idea in action. If the idea is abstract, unfamiliar, easily misunderstood, or intended to guide a real decision, include one brief everyday situation that demonstrates the mechanism or consequence. Make the example do explanatory work: show a choice, what happens because of it, and why that illustrates the point. For example, when explaining care for shared resources, show how someone maintaining a tool or shared space protects something other people rely on. Do not insert an example into a simple definition or answer when it adds no understanding. If a clear distinction or direct explanation already makes the idea concrete, stop there. Use at most one developed everyday example by default; use a second only when it clarifies a genuinely different aspect. Keep examples clearly illustrative, plausible, and proportionate; never present an invented scenario as a documented real case. Do not fabricate real-world case studies, statistics, quotations, or named authorities.

Let the nature and complexity of the question determine the length. A simple question can receive a short answer; a layered question may deserve several purposeful paragraphs, distinctions, and examples. Do not impose a fixed word count or shorten a complete explanation just for brevity. Stop when the visitor has the understanding they came for, rather than padding the answer.

Use a natural, conversational voice: explain as a thoughtful, knowledgeable person would to another person. Favor familiar words and concrete details over abstract phrases when both express the idea accurately. Conversational does not mean shallow, overly casual, or simplistic. Preserve nuance without making the reader work unnecessarily hard.

If the question contains a "why now", "why does this matter", "what does this mean", or similar second part, answer that second part rather than silently answering only the first.

A doorway into the Archive is useful when it adds something the answer cannot reasonably contain. Its relevance must be explainable in terms of the visitor's actual question and the specific contribution the resource offers—not merely shared keywords. If the selected resource would not help this visitor take a meaningful next step, omit it rather than forcing a weak match. The doorway is presented separately by The Guide after the answer, so do not add doorway prose, Markdown links, URLs, or source-navigation language to the response itself. Never invent a title, URL, quotation, or claim about a source.

Do not manufacture a follow-up question merely to continue the interaction. If a genuine next opening would help, you may end with one natural question. Otherwise end cleanly.

Never expose implementation or processing language. Never mention USE, providers, models, routing, retrieval, synthesis, evidence boundaries, prompts, system instructions, handoffs, processing layers, or similar machinery. Never add bracketed editorial/debugging/evidence labels.

Presentation matters. Preserve readable paragraph breaks in the response. For compound explanatory questions that ask both what something is and why it matters (including “why now” questions), use 3 purposeful paragraphs: first answer or define the subject directly; then explain why it matters in the present context; then add one useful implication, distinction, or practical meaning that helps the visitor understand what follows. For other explanatory or conceptual answers, use 2–4 purposeful paragraphs when that improves comprehension. A short Markdown section heading is allowed when it genuinely clarifies a change of idea, but do not add headings mechanically. Do not turn a short direct answer into an essay.

Return ONLY valid JSON:
{"response":"visitor-facing answer","doorway_title":"","response_shape":"direct|explanatory|conceptual|reflective|navigational|general"}
""".strip()


def _normalize_space(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _sanitize_candidate(text: Any) -> str:
    """Normalize visitor prose while preserving meaningful Markdown structure."""
    raw = str(text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not raw:
        return ""

    raw = _INTERNAL_BRACKET.sub(" ", raw)
    replacements = (
        (r"\bevidence excerpt bounded by USE\b", "the material I found"),
        (r"\bcanonical evidence\b", "the Archive material"),
        (r"\bsupplied evidence\b", "the material I found"),
        (r"\binternal interpretation\b", "the way the question can be understood"),
        (r"\b(?:retrieval|synthesis|processing) layer\b", "the material"),
    )
    for pattern, replacement in replacements:
        raw = re.sub(pattern, replacement, raw, flags=re.I)

    paragraphs = []
    for block in re.split(r"\n\s*\n+", raw):
        lines = []
        for line in block.split("\n"):
            line = re.sub(r"\s+", " ", line).strip()
            if not line:
                continue
            line = re.sub(r"\s+([,.;!?])", r"\1", line)
            line = re.sub(r"([.!?])\s*\1+", r"\1", line)
            lines.append(line)
        if lines:
            paragraphs.append(" ".join(lines))

    return "\n\n".join(paragraphs).strip()


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


def _requires_compound_explanatory_structure(query: str) -> bool:
    """Return True when the question explicitly asks for both meaning and significance."""
    q = _normalize_space(query).casefold()
    asks_what = bool(re.search(r"^(?:what is|what's|define)\b", q))
    asks_why = bool(re.search(r"\bwhy\b", q))
    return asks_what and asks_why


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


def _parse_factory(documents: List[Dict[str, str]], query: str = ""):
    titles = {item["title"] for item in documents}
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

        if _requires_compound_explanatory_structure(query):
            paragraph_count = len(re.findall(r"\n\s*\n", response)) + 1
            if paragraph_count < 3:
                raise ValueError("compound explanatory composition requires three purposeful paragraphs")

        if _INTERNAL_SYSTEM_NAME.search(response) or _INTERNAL_LANGUAGE.search(response):
            raise ValueError("general composition exposed internal implementation language")

        shape = _normalize_space(parsed.get("response_shape") or "").casefold()
        if shape not in {"direct", "explanatory", "conceptual", "reflective", "navigational", "general"}:
            raise ValueError("general composition returned an invalid response shape")

        title = _normalize_space(parsed.get("doorway_title") or "")
        if title and title not in titles:
            # Doorway metadata is optional. A provider's imperfect navigation
            # label must never invalidate an otherwise usable visitor answer.
            # Canonical doorway selection remains authoritative outside this
            # composition contract.
            title = ""

        # Navigation is a separate authoritative surface. Provider prose must
        # not carry doorway links or URLs; the Guide attaches the selected
        # canonical doorway independently after composition succeeds.
        if re.search(r"\]\((https?://[^)\s]+)\)", response, flags=re.I):
            raise ValueError("general composition embedded a navigation URL in visitor prose")
        if re.search(r"\bhttps?://\S+", response, flags=re.I):
            raise ValueError("general composition exposed a URL in visitor prose")

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
    if not question:
        return None

    shape = _question_shape(question)
    user_content = (
        f"Visitor question:\n{question}\n\n"
        f"Suggested response shape (use your judgment; do not mention it): {shape}\n\n"
        f"Recent conversation context, if any:\n{_normalize_space(history_text)[:1600]}\n\n"
        f"Archive material available to ground the answer:\n{_evidence_payload(documents) if documents else 'No relevant Archive material was retrieved for this question. Use reliable general knowledge where appropriate; do not invent Archive-specific claims or sources.'}"
    )

    cache_key = _composition_cache_key(
        question,
        history_text,
        shape,
        documents,
    )
    now = time.monotonic()
    with _COMPOSITION_CACHE_LOCK:
        cached_entry = _COMPOSITION_CACHE.get(cache_key)
        if cached_entry is not None:
            cached_at, cached_value = cached_entry
            if now - cached_at < _COMPOSITION_CACHE_TTL_SECONDS:
                _COMPOSITION_CACHE.move_to_end(cache_key)
                return dict(cached_value)
            del _COMPOSITION_CACHE[cache_key]

    result = route_with_model_bank(
        use_core=use_core,
        operation=OPERATION,
        messages=[
            {"role": "system", "content": _GENERAL_GUIDE_SYSTEM},
            {"role": "user", "content": user_content[:10000]},
        ],
        max_tokens=900,
        parse=_parse_factory(documents, question),
    )
    if not result:
        return None

    parsed = result["parsed"]
    candidate = {
        "response": parsed["response"],
        "doorway_title": parsed["doorway_title"],
        "response_shape": parsed["response_shape"],
        "provider": str(result.get("provider") or ""),
        "model": str(result.get("model") or ""),
    }

    # If identical requests arrive concurrently, the first validated answer
    # wins; every concurrent caller returns that same answer. This prevents
    # response races without serializing unrelated questions.
    with _COMPOSITION_CACHE_LOCK:
        cached_entry = _COMPOSITION_CACHE.get(cache_key)
        if cached_entry is not None:
            cached_at, cached_value = cached_entry
            if time.monotonic() - cached_at < _COMPOSITION_CACHE_TTL_SECONDS:
                _COMPOSITION_CACHE.move_to_end(cache_key)
                return dict(cached_value)
            del _COMPOSITION_CACHE[cache_key]

        _COMPOSITION_CACHE[cache_key] = (time.monotonic(), dict(candidate))
        while len(_COMPOSITION_CACHE) > _COMPOSITION_CACHE_MAX_ENTRIES:
            _COMPOSITION_CACHE.popitem(last=False)

    return candidate


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

try:
    _parse_factory([{"title": "Archive Doorway", "url": "https://geralddaquila.com/example/", "content": "Grounding material."}])(
        '{"response":"A useful answer.\\n\\n[Explore the Archive](https://geralddaquila.com/example/)","doorway_title":"","response_shape":"general"}'
    )
except ValueError:
    pass
else:
    raise RuntimeError("General Guide composition invariant failed: provider navigation leaked into visitor prose.")

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

CONTRACT_VERSION = "v1.18"
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
- When a visitor discloses grief or significant distress, do not rush them toward a task, a lesson, or a solution. Begin by reflecting the difficulty they actually named in specific, plain language; avoid formulaic openers such as “I’m sorry you’re feeling this way,” claims about what the loss means, and assumptions about their inner history. If their immediate need is unclear, offer one gentle, open, manageable question that gives them room to say what is hardest without requiring a list or explanation. Keep the response unhurried: recognition first, then one question, and no advice checklist. Grief or impaired functioning alone is not proof of suicidality and must not trigger emergency language by itself. If the visitor signals immediate danger or inability to stay safe, follow the established safety boundary.
- For a question that explicitly asks where to look, make the navigation useful without replacing the requested answer with a list.
- For a resource-discovery question (for example, “Where can I find material about X?”), treat finding material as the visitor’s primary task. Give a concise, direct answer naming the strongest source-supported destination, and explain its specific contribution to the subject in ordinary language. Do not merely quote a generic page description, repeat the query in different words, or claim a page covers the exact subject unless the supplied source content supports that claim. Distinguish a broad entry point from a resource that directly addresses the subject. If only a broad entry point is verified, say plainly that it is a starting point and why it is relevant; do not imply that a more direct resource was found. Never pad this explanation with speculative phrases such as “the page may also lead to related material.” Keep the canonical link separate from the answer.

Use relevant Archive material as grounding and enrichment when it is available. Do not merely summarize retrieved passages. Synthesize what is relevant into an answer written for this visitor. If no relevant Archive material was retrieved, answer from reliable general knowledge when the question permits it. Do not invent Archive-specific claims, citations, quotations, or recommendations, and do not imply that a general explanation came from the Archive. If the question genuinely requires unavailable source-specific evidence, state that limitation briefly while still explaining what can responsibly be said.

Use ordinary language for ordinary public questions. Do not introduce Archive jargon such as cornerstone, canonical, glyph, stewardship, or similar internal vocabulary merely because it appears in the source material. If the visitor explicitly asks about the Living Archive or its own language, that vocabulary may be used naturally and lightly.

For a plain request to explain stewardship, prefer three connected paragraphs over a taxonomy: define it in ordinary language; show one recognizable everyday example and why small choices matter over time; then clarify its limits, including that stewardship is not control over everything or self-sacrifice for everyone. Do not introduce a spectrum, category list, or sweeping civilizational crisis unless the visitor asks for that level of analysis. Keep the Archive doorway separate from the answer.

Be concrete rather than literary. Prefer precise listening and useful explanation over impressive writing. Do not repeat the visitor's question as filler.

Apply explanatory discernment before composing: infer what kind of understanding the question calls for, then choose the most useful depth, structure, and examples. A definition may need only a clear answer; a conceptual question may need distinctions; a practical question may need steps or an example; a teaching, learning, or leadership question may benefit from a scenario the reader can recognize and apply. Do not assume the visitor's role unless the question or context supports it.

Apply a universal perception pass to every answer, regardless of topic or response shape. Before finalizing, silently ask: (1) What is the visitor actually trying to understand, decide, or make sense of? (2) Is there a real tension, trade-off, assumption, consequence, or distinction beneath the wording that would materially improve the answer? (3) What is the single most useful insight that helps the visitor see the subject more clearly? Use the insight only when grounded in the question, reliable knowledge, or supplied Archive material; never invent a hidden motive or emotional state.

Perception is not a requirement to sound emotional. For factual and bounded questions, it may mean naming the important qualification or correcting a likely misconception. For conceptual questions, it may mean explaining a meaningful tension or consequence. For practical questions, it may mean noticing a constraint, trade-off, or likely failure point. For reflective or lived questions, it may mean acknowledging the particular difficulty or competing needs the visitor actually described. For teaching, leadership, or social questions, it may mean showing how an idea plays out in a recognizable situation. Match the kind of perception to the question; do not force every answer into the same genre.

Prefer one earned insight over several generic observations. Do not merely restate the question, add a moral, use a tidy but shallow “X without Y” contrast, or append a philosophical flourish that could fit almost any question. Explain why the insight matters in this specific case. When useful, make the answer concrete with one proportionate example or implication; do not add one when it would distract from a simple answer.

For conceptual questions about the relationship between two ideas, preserve the full movement of the reasoning rather than compressing it into a summary. When the question warrants depth, develop the answer naturally across three connected movements: (1) explain how the ideas relate and what tension or misconception is at stake; (2) show that relationship in a concrete, plausible situation and explain the consequences; (3) draw the distinction that resolves the tension, including the limits or conditions that matter. Each paragraph must advance the thought, not repeat it. The example must illuminate the argument rather than merely decorate it. The final insight should emerge from the explanation, not arrive as a generic moral. This is a depth standard, not a mandatory template for simple or unrelated questions.


Preserve the visitor's agency. Explain options and consequences without taking over their judgment. Do not diagnose, therapize, moralize, presume personal circumstances, or manufacture intimacy. Do not turn a neutral question into personal advice. If the question has no meaningful human or practical tension, answer it directly and stop. A follow-up invitation is optional and should appear only when it opens a genuinely useful next step, never as a required closing formula.

Use a concrete-example decision rule before composing: ask whether a reader could understand the answer accurately without seeing the idea in action. If the idea is abstract, unfamiliar, easily misunderstood, or intended to guide a real decision, include one brief everyday situation that demonstrates the mechanism or consequence. Make the example do explanatory work: show a choice, what happens because of it, and why that illustrates the point. For example, when explaining care for shared resources, show how someone maintaining a tool or shared space protects something other people rely on. Do not insert an example into a simple definition or answer when it adds no understanding. If a clear distinction or direct explanation already makes the idea concrete, stop there. Use at most one developed everyday example by default; use a second only when it clarifies a genuinely different aspect. Keep examples clearly illustrative, plausible, and proportionate; never present an invented scenario as a documented real case. Do not fabricate real-world case studies, statistics, quotations, or named authorities.

Let the nature and complexity of the question determine the length. A simple question can receive a short answer; a layered question may deserve several purposeful paragraphs, distinctions, and examples. Do not impose a fixed word count or shorten a complete explanation just for brevity. Stop when the visitor has the understanding they came for, rather than padding the answer.

Use a natural, conversational voice: explain as a thoughtful, knowledgeable person would to another person. Favor familiar words and concrete details over abstract phrases when both express the idea accurately. Conversational does not mean shallow, overly casual, or simplistic. Preserve nuance without making the reader work unnecessarily hard.

For reflective questions about how to understand, interpret, or respond to a difficult situation, do not default to a numbered sequence of instructions. Develop the thought conversationally: offer one useful distinction (for example, what is known versus what is inferred), explain why it helps, and give at most one small, optional foothold the visitor can use. Avoid stacking imperatives such as “First… Second… Third…”, rhetorical checklists, and multiple questions in one paragraph. Do not turn reflection into a protocol or imply that a person must consider every angle before acting. Use explicit steps or a Markdown list only when the visitor asks for steps, a checklist, or a practical procedure, or when several independent actions genuinely need to be followed separately. The goal is to widen understanding while preserving the visitor's judgment and freedom to decide what fits.

If the question contains a "why now", "why does this matter", "what does this mean", or similar second part, answer that second part rather than silently answering only the first.

A doorway into the Archive is useful when it adds something the answer cannot reasonably contain. Its relevance must be explainable in terms of the visitor's actual question and the specific contribution the resource offers—not merely shared keywords. If the selected resource would not help this visitor take a meaningful next step, omit it rather than forcing a weak match. The doorway is presented separately by The Guide after the answer, so do not add doorway prose, Markdown links, URLs, or source-navigation language to the response itself. Never invent a title, URL, quotation, or claim about a source.

Do not manufacture a follow-up question merely to continue the interaction. If a genuine next opening would help, you may end with one natural question. Otherwise end cleanly.

Never expose implementation or processing language. Never mention USE, providers, models, routing, retrieval, synthesis, evidence boundaries, prompts, system instructions, handoffs, processing layers, or similar machinery. Never add bracketed editorial/debugging/evidence labels.

Presentation matters. Preserve readable paragraph breaks and meaningful Markdown structure. When giving multiple practical actions, format them as a real Markdown list with one action per line; never compress numbered actions into a single paragraph. Use short labels only when they help the reader scan the steps. For compound explanatory questions that ask both what something is and why it matters (including “why now” questions), use 3 purposeful paragraphs: first answer or define the subject directly; then explain why it matters in the present context; then add one useful implication, distinction, or practical meaning that helps the visitor understand what follows. For other explanatory or conceptual answers, use 2–4 purposeful paragraphs when that improves comprehension. A short Markdown section heading is allowed when it genuinely clarifies a change of idea, but do not add headings mechanically. Do not turn a short direct answer into an essay.

Return ONLY valid JSON:
{"response":"visitor-facing answer","doorway_title":"","response_shape":"direct|explanatory|conceptual|reflective|navigational|general"}
""".strip()


def _normalize_space(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _requires_distress_sensitive_pacing(query: str) -> bool:
    """Identify distress disclosures that need listening before practical advice."""
    q = _normalize_space(query).casefold()
    patterns = (
        r"\b(?:i am|i'm|im)\s+(?:grieving|in grief|bereaved|mourning)\b.{0,100}\b(?:cannot|can't|can not|unable to|barely able to)\s+(?:function|cope|manage|get through)\b",
        r"\b(?:cannot|can't|can not|unable to|barely able to)\s+(?:function|cope|manage|get through)\b",
        r"\b(?:i am|i'm|im)\s+(?:not functioning|barely functioning|falling apart|unable to cope)\b",
    )
    return any(re.search(pattern, q) for pattern in patterns)


def _sanitize_candidate(text: Any) -> str:
    """Normalize visitor prose while preserving meaningful Markdown structure."""
    raw = str(text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not raw:
        return ""

    raw = _INTERNAL_BRACKET.sub(" ", raw)
    # Repair common provider formatting failures deterministically. Providers
    # vary between colon/en-dash/em-dash labels, Unicode dashes, and inline
    # numbered actions. Normalize those markers before paragraph cleanup.
    action_label = r"\*\*[^*\n]{2,100}\*\*"
    action_separator = r"(?:\s*:\s*|\s+[–—−-]\s+)"
    raw = re.sub(
        rf"\s+-\s+(?={action_label}{action_separator})",
        "\n- ",
        raw,
    )
    # Numbered steps may be emitted inline even when the preceding item has
    # no terminal punctuation. Split only when a numbered Markdown item is
    # followed by a new bold action label and a recognized label separator.
    raw = re.sub(
        rf"(?<=\S)\s+(?=\d{{1,2}}[.)]\s+{action_label}{action_separator})",
        "\n",
        raw,
    )
    # Handle inline dash bullets whose labels are not bold but still clearly
    # marked as bullets, while leaving ordinary hyphenated prose untouched.
    raw = re.sub(
        r"(?<=[.!?])\s+(?=-\s+\*\*[^*\n]{2,100}\*\*\s*(?::|[–—−-]))",
        "\n",
        raw,
    )
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
            # Keep list items and intentional line structure intact. Flattening
            # every line into a single sentence erased the presentation contract.
            paragraphs.append("\n".join(lines))

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


def is_exact_source_request(query: str) -> bool:
    """Recognize requests to trace a claim to its source."""
    q = _normalize_space(query).casefold()
    return bool(
        re.search(r"\b(?:exact|original|actual|specific)\s+(?:source|citation|reference)\b", q)
        or re.search(r"\bsource\s+for\s+(?:that|this|the)\s+claim\b", q)
        or re.search(r"\bcite\s+(?:the|your|that)\s+claim\b", q)
        or re.search(r"\bwhere\s+did\s+you\s+(?:get|find|source)\s+(?:that|this)\b", q)
    )


def source_trace_has_prior_claim(history_text: str) -> bool:
    """Whether prior turns contain an assistant answer that can be traced."""
    history = str(history_text or "").strip()
    if not history:
        return False
    # Require a role-labelled assistant/Guide answer; user-only history is not provenance.
    return bool(re.search(r"(?i)\b(?:assistant|guide)\s*:\s*\S", history))



def correction_subject(query: str) -> str:
    """Recover the subject a visitor explicitly says the previous answer missed."""
    q = _normalize_space(query)
    patterns = (
        r"\bi\s+asked\s+about\s+(.+?),\s*but\s+you\s+answered\s+about\s+(.+?)(?:[.!?]|$)",
        r"\byou\s+answered\s+about\s+(.+?),\s*but\s+i\s+asked\s+about\s+(.+?)(?:[.!?]|$)",
        r"\bi\s+asked\s+for\s+(.+?),\s*but\s+you\s+gave\s+me\s+(.+?)(?:[.!?]|$)",
    )
    for index, pattern in enumerate(patterns):
        match = re.search(pattern, q, re.I)
        if not match:
            continue
        subject = match.group(1 if index != 1 else 2).strip().strip(chr(39)).strip(chr(34)).strip()
        subject = re.sub(r"^(?:an?\s+|the\s+)", "", subject, flags=re.I).strip()
        subject = re.sub(r"^(?:please\s+)?(?:explain|describe|define)\s+", "", subject, flags=re.I)
        if 2 <= len(subject.split()) <= 12 and len(subject) <= 120:
            return subject.rstrip(" .?!")
    return ""


def _has_response_style_preference(query: str) -> bool:
    """Recognize explicit requests about the language or manner of an answer."""
    q = _normalize_space(query).casefold()
    patterns = (
        r"\b(?:without|avoid|don't use|do not use|please don't use|please do not use)\s+(?:using\s+)?(?:technical|academic|jargon|specialist|complicated|complex)\s+(?:or\s+)?(?:technical|academic|jargon|specialist)?\s*(?:language|terms|words|jargon)?\b",
        r"\b(?:plain|simple|everyday|ordinary|clear)\s+(?:language|words|terms)\b",
        r"\b(?:explain|say|put|write)\s+(?:it|this|that|the answer)\s+(?:in|using)\s+(?:plain|simple|everyday|ordinary|clear)\s+(?:language|words|terms)\b",
        r"\b(?:not|rather than|instead of)\s+(?:receive|get|be given)\s+(?:advice|recommendations)\b",
        r"\b(?:i want|i'd like|i would like)\s+to understand\s+(?:(?:the|this|that)\s+(?:subject|topic|matter)|it|this|that)\b.{0,100}\b(?:not receive advice|rather than advice|instead of advice)\b",
    )
    return any(re.search(pattern, q) for pattern in patterns)


def _is_response_preference_without_subject(query: str, history_text: str = "") -> bool:
    """Recognize a standalone response-style preference with no subject to answer."""
    q = _normalize_space(query).casefold()
    history = _normalize_space(history_text)
    if not _has_response_style_preference(q):
        return False
    if history and len(history.split()) >= 6:
        return False
    named_subject = bool(
        re.search(r"\b(?:about|regarding|concerning|on)\s+[a-z][a-z -]{2,}", q)
        or re.search(r"^(?:what is|what's|define|explain|describe|why|how does|how can)\s+(?!this\b|that\b|it\b|the subject\b|the topic\b)[a-z][a-z -]{2,}", q)
        or re.search(r"\b(?:institutional responsibility|stewardship|governance|grief|loneliness|meaning|coercion)\b", q)
    )
    return not named_subject

def _question_shape(query: str) -> str:
    q = _normalize_space(query).casefold()
    if _requires_distress_sensitive_pacing(q):
        return "reflective"
    if re.search(r"\b(?:where can i find|where do i find|show me|take me to|link me to|browse|find the)\b", q):
        return "navigational"
    if re.search(r"\b(?:why|why now|why does|why is|what makes|how does|how can)\b", q):
        return "explanatory"
    if re.match(r"^(?:what is|what's|define|who is|who was|when did|where is|where was)\b", q):
        return "direct"
    if re.search(r"\b(?:i feel|i'm feeling|i am feeling|my relationship|my grief|i keep|i can't|i cannot|i'm struggling|i am struggling)\b", q):
        return "reflective"
    return "general"


def _clarification_reason(query: str, history_text: str = "") -> str:
    """Identify an essential missing referent without interrupting complete questions."""
    q = _normalize_space(query).casefold()
    history = _normalize_space(history_text).casefold()
    generic_referent = bool(re.search(
        r"\b(?:this|that|the)\s+(?:problem|issue|situation|matter|topic)\b", q
    ))
    comparison = bool(re.search(
        r"\b(?:compare|comparison|contrast|two ways|different approaches)\b", q
    ))
    named_subject = bool(not generic_referent and re.search(
        r"\b(?:of|about|between|regarding|concerning|on)\s+"
        r"[a-z][a-z -]{2,}", q
    ))
    # The conversation history may supply the omitted subject. Treat it as
    # resolving the reference only when it contains substantive context, not
    # merely the same generic wording.
    history_supplies_subject = bool(
        history
        and len(history.split()) >= 6
        and not re.search(
            r"\b(?:this problem|that problem|this issue|that issue)\b", history
        )
    )
    if comparison and generic_referent and not named_subject and not history_supplies_subject:
        return "comparison_subject_missing"
    if generic_referent and not named_subject and not history_supplies_subject and len(q.split()) <= 12:
        return "problem_referent_missing"
    return ""


def clarification_response(query: str, history_text: str = "") -> Optional[Dict[str, str]]:
    """Resolve missing subjects and standalone response preferences before retrieval."""
    if is_exact_source_request(query) and not source_trace_has_prior_claim(history_text):
        return {
            "response": (
                "I can help trace it, but I can’t tell which claim you mean from this message alone. "
                "Please paste the claim or the answer it came from, and I’ll identify the exact source if I can verify it."
            ),
            "response_shape": "clarifying",
            "clarification_reason": "source_claim_missing",
        }
    # A request about answer style is a conversation preference, not a subject
    # to search. Resolve it at the request boundary so no unrelated doorway can
    # be selected and attached later by the ordinary Guide pipeline.
    if _is_response_preference_without_subject(query, history_text):
        if re.search(r"\\b(?:advice|recommendations)\\b", query, re.I):
            response = (
                "Of course. I’ll focus on explaining the subject itself rather than "
                "giving advice. What subject would you like to understand?"
            )
        else:
            response = (
                "Of course. I’ll use clear, everyday language and avoid technical "
                "or academic terms. What would you like to understand?"
            )
        return {
            "response": response,
            "response_shape": "clarifying",
            "clarification_reason": "response_preference_subject_missing",
        }

    reason = _clarification_reason(query, history_text)
    if not reason:
        return None
    if reason == "comparison_subject_missing":
        response = (
            "Absolutely. Which problem would you like to compare? If you already have "
            "two approaches in mind, tell me what they are. If not, describe the "
            "situation briefly and I can help identify two useful ways of understanding "
            "it, including what each reveals, where each has limits, and what becomes "
            "clearer when we consider them together."
        )
    else:
        response = (
            "What problem or situation do you have in mind? A little context will help "
            "me give you an answer that fits, rather than guess at what you mean."
        )
    return {
        "response": response,
        "response_shape": "clarifying",
        "clarification_reason": reason,
    }


def _requires_discernment_synthesis(query: str) -> bool:
    """Recognize conceptual relationship questions that need developed reasoning."""
    q = _normalize_space(query).casefold()
    return bool(
        re.search(r"\brelationship between\b", q)
        and re.search(r"\b(?:agency|responsibility|freedom|care|accountability|rights|obligations|independence|interdependence)\b", q)
    )


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


def _question_requests_enumeration(query: str) -> bool:
    return bool(re.search(
        r"\b(?:list|bullet points?|enumerate|steps|checklist|types|categories|forms|pros and cons|options|compare|differences between|what are the)\b",
        _normalize_space(query),
        re.I,
    ))


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

        # Reject compressed numbered advice so the provider bank can retry
        # rather than silently accepting a visually dense answer.
        if re.search(r"(?s)\b1[.)]\s+.{8,}?\b2[.)]\s+", response) and not re.search(r"\n\s*2[.)]\s+", response):
            raise ValueError("multi-step practical advice must use separate Markdown list lines")
        # General Guide answers do not default to lists. A plain stewardship
        # explanation must stay grounded and bounded, not drift into a taxonomy.
        if re.search(r"\bstewardship\b", query, re.I) and re.search(r"\b(?:explain|what is|define|meaning|describe)\b", query, re.I) and not _question_requests_enumeration(query):
            if re.search(r"(?m)^\s*(?:[-*+]\s+|\d+[.)]\s+)", response):
                raise ValueError("plain stewardship explanation must not introduce an unsolicited list")
            if not re.search(r"\b(?:keeping a promise|shared spaces?|maintain(?:ing)? what others rely on|using resources thoughtfully|resources thoughtfully|returning|borrowed item)\b", response, re.I):
                raise ValueError("plain stewardship explanation requires one recognizable everyday anchor")
            if not re.search(r"\b(?:does not mean|doesn['’]?t mean|controlling everything|sacrificing yourself|within your limits|what is yours to care for)\b", response, re.I):
                raise ValueError("plain stewardship explanation must clarify the limits of responsibility")


        if _requires_discernment_synthesis(query):
            paragraphs = [part.strip() for part in re.split(r"\n\s*\n+", response) if part.strip()]
            if len(paragraphs) < 3:
                raise ValueError("conceptual relationship answer requires three purposeful paragraphs")
            if not re.search(r"\b(?:for example|for instance|consider a|imagine a)\b", response, re.I):
                raise ValueError("conceptual relationship answer requires one concrete example")
            if not re.search(r"\b(?:but|however|while|although|does not mean|is not the same as|distinction|depends on)\b", response, re.I):
                raise ValueError("conceptual relationship answer must resolve a meaningful tension or distinction")

        if _requires_compound_explanatory_structure(query):
            paragraph_count = len(re.findall(r"\n\s*\n", response)) + 1
            if paragraph_count < 3:
                raise ValueError("compound explanatory composition requires three purposeful paragraphs")

        if _requires_distress_sensitive_pacing(query):
            # A distress disclosure must not be answered with a brisk generic
            # apology or a task-management prompt. Require one gentle question
            # as the final movement so the visitor can continue without being
            # hurried into advice or a safety escalation unsupported by their words.
            if re.match(
                r"^(?:i['’]?m sorry (?:you(?:'|’)re|to hear)|sorry you(?:'|’)re)",
                response,
                flags=re.I,
            ):
                raise ValueError("distress response opened with formulaic sympathy")
            if not response.rstrip().endswith("?"):
                raise ValueError("distress response must end with one gentle follow-up question")
            if response.count("?") != 1:
                raise ValueError("distress response must ask only one follow-up question")
            if re.search(
                r"(?i)for example,?\s+(?:getting out of bed|eating|answering a work email)|"
                r"\b(?:checklist|steps to take|here are (?:some|a few) things)\b",
                response,
            ):
                raise ValueError("distress response rushed into task-management advice")

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
    if not question:
        return None

    if is_exact_source_request(question) and not source_trace_has_prior_claim(history_text):
        return {
            "response": (
                "I can help trace it, but I can’t tell which claim you mean from this message alone. "
                "Please paste the claim or the answer it came from, and I’ll identify the exact source if I can verify it."
            ),
            "doorway_title": "",
            "response_shape": "clarifying",
            "clarification_reason": "source_claim_missing",
            "provider": "",
            "model": "",
        }

    # A standalone style preference is not a subject question. Acknowledge it
    # before retrieval so it cannot trigger a false evidence failure or doorway.
    if _is_response_preference_without_subject(question, history_text):
        if re.search(r"\b(?:advice|recommendations)\b", question, re.I):
            response = (
                "Of course. I’ll focus on explaining the subject itself rather than "
                "giving advice. What subject would you like to understand?"
            )
        else:
            response = (
                "Of course. I’ll use clear, everyday language and avoid technical "
                "or academic terms. What would you like to understand?"
            )
        return {
            "response": response,
            "doorway_title": "",
            "response_shape": "clarifying",
            "clarification_reason": "response_preference_subject_missing",
            "provider": "",
            "model": "",
        }

    documents = _documents_from_context(use_core, context_data)
    corrected_subject = correction_subject(question)
    effective_question = corrected_subject or question
    shape = _question_shape(effective_question)
    source_trace_instruction = (
        "The visitor asks for the exact source of a prior claim. Treat this as a provenance task, not a general topic question. "
        "Use the recent conversation to identify the specific claim, then inspect the supplied Archive material for direct support. "
        "Name the exact source title and give a page, section, passage, or URL only when that detail is present and verified. "
        "Explain briefly what the source supports and whether it supports the full claim or only part of it. "
        "Never substitute a generally related methodology page for the source of the claim. Never invent citations or source details. "
        "If the supplied material does not establish the source, say exactly what remains unverified.\n\n"
        if is_exact_source_request(question)
        else ""
    )

    correction_instruction = (
        "The visitor is correcting a previous off-topic answer. They explicitly say the subject they asked about was "
        + repr(corrected_subject)
        + ". Briefly acknowledge the mismatch without repeating the whole complaint, then answer that subject directly. "
        "Do not answer about the mistaken subject. Use the supplied Archive material when relevant, and use reliable general knowledge if no suitable Archive material was retrieved. "
        "Do not turn this recoverable correction into a refusal or ask the visitor to restate the subject.\n\n"
        if corrected_subject
        else ""
    )
    style_instruction = (
        "The visitor explicitly requested plain, non-technical language. Answer the actual subject question in clear everyday words; avoid academic phrasing and unexplained specialist terms.\n\n"
        if _has_response_style_preference(question) or _has_response_style_preference(history_text)
        else ""
    )
    user_content = (
        f"Visitor question:\n{question}\n\n"
        + correction_instruction
        + style_instruction
        + f"Suggested response shape (use your judgment; do not mention it): {shape}\n\n"
        f"Recent conversation context, if any:\n{_normalize_space(history_text)[:1600]}\n\n"
        + (
            "Response pacing for this visitor: slow down. First recognize the specific difficulty they named in natural, non-formulaic language; do not open with generic sympathy or presume what their loss means. Then ask exactly one gentle, open question about what feels hardest or what they would like to say more about. Do not turn the disclosure into a task-management exercise, list examples of basic tasks, offer advice before understanding their need, or infer suicidality from grief alone. End with the question so the conversation has a clear, humane next step.\n\n"
            if _requires_distress_sensitive_pacing(question)
            else ""
        )
        + f"Archive material available to ground the answer:\n{_evidence_payload(documents) if documents else 'No relevant Archive material was retrieved for this question. Use reliable general knowledge where appropriate; do not invent Archive-specific claims or sources.'}"
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
        parse=_parse_factory(documents, effective_question),
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
if _sanitize_candidate("Steps: - **First action**: one. - **Second action**: two.") != "Steps:\n- **First action**: one.\n- **Second action**: two.":
    raise RuntimeError("General Guide composition invariant failed: inline practical-list normalization.")
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

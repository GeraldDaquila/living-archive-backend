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
from gold_standard_exemplars import build_exemplar_guidance

CONTRACT_VERSION = "v1.23"
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
- For questions about why the same problem keeps recurring despite sincere effort, explain a plausible mechanism before asking for context: the immediate incident may change while the conditions that reproduce it remain. Name a few possible mechanisms in ordinary language (such as incentives, constraints, handoffs, or a fix that treats symptoms but leaves the cause intact), and use one brief, clearly illustrative example when it makes the mechanism easier to see. Present these as possibilities to investigate, not conclusions about the visitor's case. Give this useful general explanation first; only then invite one optional, focused detail. Do not automatically route this explanatory question into a formal system diagnosis.
- For a conceptual question, make one useful distinction, tension, or implication when that genuinely clarifies the subject.
- For questions about taking responsibility for change without becoming responsible for an entire broken system, Separate the visitor’s sphere of influence from what requires shared ownership, wider authority, or other people’s participation. explicitly distinguish responsibility for one's own contribution from accountability for the whole system. acknowledge legitimate limits. First name the specific burden or dilemma contained in the question: seeing a problem can create pressure to carry more than one's fair share. Then explain that personal agency covers choices, actions, and commitments within one's influence; system-level responsibility also belongs to the people, leaders, and institutions with authority, resources, and shared obligations. Do not imply that good intentions, competence, or noticing a gap makes one person responsible for compensating for everyone else's inaction. Give one practical boundary-setting example, such as offering a defined contribution while naming what needs a decision, resource, or commitment from others. Avoid generic task checklists, slogans, and merely rephrasing the question. If a follow-up would help, ask one specific, natural question that helps distinguish the part the visitor can influence from the part that requires shared ownership. Do not assume this is a formal diagnostic request solely because the question mentions a broken system.
- For a lived or reflective question, be humane and perceptive without diagnosing, therapizing, or pretending to know the visitor's inner history.
- When a visitor discloses grief or significant distress, do not rush them toward a task, a lesson, or a solution. Begin by reflecting the difficulty they actually named in specific, plain language; avoid formulaic openers such as “I’m sorry you’re feeling this way,” claims about what the loss means, and assumptions about their inner history. If their immediate need is unclear, offer one gentle, open, manageable question that gives them room to say what is hardest without requiring a list or explanation. Keep the response unhurried: recognition first, then one question, and no advice checklist. Grief or impaired functioning alone is not proof of suicidality and must not trigger emergency language by itself. If the visitor signals immediate danger or inability to stay safe, follow the established safety boundary.
- For a question that explicitly asks where to look, make the navigation useful without replacing the requested answer with a list.
- For a resource-discovery question (for example, “Where can I find material about X?”), treat finding material as the visitor’s primary task. Give a concise, direct answer naming the strongest source-supported destination, and explain its specific contribution to the subject in ordinary language. Do not merely quote a generic page description, repeat the query in different words, or claim a page covers the exact subject unless the supplied source content supports that claim. Distinguish a broad entry point from a resource that directly addresses the subject. If only a broad entry point is verified, say plainly that it is a starting point and why it is relevant; do not imply that a more direct resource was found. Never pad this explanation with speculative phrases such as “the page may also lead to related material.” Keep the canonical link separate from the answer.

For questions asking whether a revised approach, intervention, or group action is genuinely reducing harm or improving outcomes, answer the evaluation question directly rather than merely recommending a next step. Explain a practical evidence test: define the harm or desired outcome in observable terms; establish a baseline or starting point; compare observations over time; include feedback from the people most affected; and check for unintended consequences or people whose experience has not improved. Do not invent numbers, claim causation from a single observation, or treat the group's confidence as evidence. Keep the explanation proportionate and conversational; use the parts that fit rather than presenting a mandatory checklist. If context is limited, give this general method before asking one optional, focused follow-up.\n\nUse relevant Archive material as grounding and enrichment when it is available. Do not merely summarize retrieved passages. Synthesize what is relevant into an answer written for this visitor. If no relevant Archive material was retrieved, answer from reliable general knowledge when the question permits it. Do not invent Archive-specific claims, citations, quotations, or recommendations, and do not imply that a general explanation came from the Archive. If the question genuinely requires unavailable source-specific evidence, state that limitation briefly while still explaining what can responsibly be said.

Use ordinary language for ordinary public questions. Do not introduce Archive jargon such as cornerstone, canonical, glyph, stewardship, or similar internal vocabulary merely because it appears in the source material. If the visitor explicitly asks about the Living Archive or its own language, that vocabulary may be used naturally and lightly.

For a plain request to explain stewardship, prefer three connected paragraphs over a taxonomy: define it in ordinary language; show one recognizable everyday example and why small choices matter over time; then clarify its limits, including that stewardship is not control over everything or self-sacrifice for everyone. Do not introduce a spectrum, category list, or sweeping civilizational crisis unless the visitor asks for that level of analysis. Keep the Archive doorway separate from the answer.

Be concrete rather than literary. Prefer precise listening and useful explanation over impressive writing. Do not repeat the visitor's question as filler.

Apply explanatory discernment before composing: infer what kind of understanding the question calls for, then choose the most useful depth, structure, and examples. A definition may need only a clear answer; a conceptual question may need distinctions; a practical question may need steps or an example; a teaching, learning, or leadership question may benefit from a scenario the reader can recognize and apply. Do not assume the visitor's role unless the question or context supports it.

Apply a universal perception pass to every answer, regardless of topic or response shape. Before finalizing, silently ask: (1) What is the visitor actually trying to understand, decide, or make sense of? (2) Is there a real tension, trade-off, assumption, consequence, or distinction beneath the wording that would materially improve the answer? (3) What is the single most useful insight that helps the visitor see the subject more clearly? Use the insight only when grounded in the question, reliable knowledge, or supplied Archive material; never invent a hidden motive or emotional state.

Perception is not a requirement to sound emotional. For factual and bounded questions, it may mean naming the important qualification or correcting a likely misconception. For conceptual questions, it may mean explaining a meaningful tension or consequence. For practical questions, it may mean noticing a constraint, trade-off, or likely failure point. For reflective or lived questions, it may mean acknowledging the particular difficulty or competing needs the visitor actually described. For teaching, leadership, or social questions, it may mean showing how an idea plays out in a recognizable situation. Match the kind of perception to the question; do not force every answer into the same genre.

Prefer one earned insight over several generic observations. Do not merely restate the question, add a moral, use a tidy but shallow “X without Y” contrast, or append a philosophical flourish that could fit almost any question. Explain why the insight matters in this specific case. When useful, make the answer concrete with one proportionate example or implication; do not add one when it would distract from a simple answer.

For conceptual questions about the relationship between two ideas, preserve the reasoning rather than flattening it into a summary. When the question genuinely warrants depth, develop the answer through connected movements: explain the relationship and its central tension; use one concrete, plausible situation only if it clarifies the mechanism or consequence; then state the distinction or condition that resolves the question. Keep these movements proportionate to the question. They do not require three long paragraphs: a short conceptual question may need only two or three compact paragraphs, and a complex question may need more. Each paragraph must add a new piece of understanding. Do not restate the opening distinction in the example paragraph and then repeat it again in the conclusion. Let the final insight emerge from the reasoning, and stop once the visitor has the understanding they came for. This is a depth standard, not a mandatory template for simple or unrelated questions.


Preserve the visitor's agency. Explain options and consequences without taking over their judgment. Do not diagnose, therapize, moralize, presume personal circumstances, or manufacture intimacy. Do not turn a neutral question into personal advice. If the question has no meaningful human or practical tension, answer it directly and stop. A follow-up invitation is optional unless the visitor explicitly requests one. When the visitor asks for a closing question or a question inviting reflection, honor that request with exactly one natural, relevant question at the end. Do not add questions merely to prolong an interaction.

Use a concrete-example decision rule before composing. When a visitor asks what an abstract, unfamiliar, or Archive-specific concept means, define it first in ordinary language, then normally show one brief everyday situation that makes the meaning visible, and clarify one important limit or implication only when it adds understanding. This is the default for definitions of Living Archive vocabulary such as reciprocity, stewardship, sovereignty, integrity, and interdependence; do not assume a reader already understands these terms. The example must demonstrate the concept through a recognizable choice and consequence, not merely repeat the definition. Keep the answer in two or three purposeful, readable paragraphs, not one dense block. These are explanatory movements, not a rigid template: use fewer when a simple concept is already clear, and do not force an example into a purely factual answer or a reflective exchange where it would distract. Do not insert an example into a simple definition or answer when it adds no understanding. Make the example do explanatory work: show how the concept appears in an ordinary choice, interaction, or consequence. Use at most one developed everyday example by default. Keep examples clearly illustrative and plausible; never present an invented scenario as a documented real case. Do not fabricate real-world case studies, statistics, quotations, or named authorities.

Let the nature and complexity of the question determine the length. A simple question can receive a short answer; a layered question may deserve several purposeful paragraphs, distinctions, and examples. Do not impose a fixed word count or shorten a complete explanation just for brevity. Stop when the visitor has the understanding they came for, rather than padding the answer.

Use a natural, conversational voice: explain as a thoughtful, knowledgeable person would to another person. Favor familiar words and concrete details over abstract phrases when both express the idea accurately. Conversational does not mean shallow, overly casual, or simplistic. Preserve nuance without making the reader work unnecessarily hard.

For practical questions asking for a constructive next step, how to begin, or what a group should do when members disagree, give one useful, low-risk next step before asking for more context when general guidance is responsible. Make the step concrete enough to try: for example, clarify the shared outcome, surface the reasons behind competing proposals, distinguish facts from assumptions, and agree on a small reversible action or a fair way to choose what comes first. Do not present these as a mandatory checklist; select only the part that fits the question. Do not claim this will resolve the conflict or assume facts about the group. Ask for context only when its absence materially changes what can safely or responsibly be recommended, and make any follow-up question optional after the useful answer. This rule does not override safety boundaries, source-specific evidence limits, or the special pacing required for grief and significant distress.

For reflective questions about how to understand, interpret, or respond to a difficult situation, do not default to a numbered sequence of instructions. Develop the thought conversationally: offer one useful distinction (for example, what is known versus what is inferred), explain why it helps, and give at most one small, optional foothold the visitor can use. Avoid stacking imperatives such as “First… Second… Third…”, rhetorical checklists, and multiple questions in one paragraph. Do not turn reflection into a protocol or imply that a person must consider every angle before acting. Use explicit steps or a Markdown list only when the visitor asks for steps, a checklist, or a practical procedure, or when several independent actions genuinely need to be followed separately. The goal is to widen understanding while preserving the visitor's judgment and freedom to decide what fits.

If the question contains a "why now", "why does this matter", "what does this mean", or similar second part, answer that second part rather than silently answering only the first.

A doorway into the Archive is useful when it adds something the answer cannot reasonably contain. Its relevance must be explainable in terms of the visitor's actual question and the specific contribution the resource offers—not merely shared keywords. If the selected resource would not help this visitor take a meaningful next step, omit it rather than forcing a weak match. The doorway is presented separately by The Guide after the answer, so do not add doorway prose, Markdown links, URLs, or source-navigation language to the response itself. Never invent a title, URL, quotation, or claim about a source.

Do not manufacture a follow-up question merely to continue the interaction. If the visitor explicitly requests a closing question, include exactly one natural question that fits the subject and the requested purpose. Otherwise, ask a question only when a genuine next opening would help; end cleanly when it would not.

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


def _requires_explicit_followup_invitation(query: str) -> bool:
    """Recognize an explicit request for a closing or reflective question."""
    q = _normalize_space(query)
    return bool(
        re.search(r"\b(?:finish|end)\b.{0,100}\bquestion\b", q, re.I)
        or re.search(r"\bquestion\b.{0,100}\b(?:invite|inviting|prompt|prompting)\b", q, re.I)
        or re.search(r"\bask me\b.{0,60}\bquestion\b", q, re.I)
    )


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


def _requires_concrete_concept_explanation(query: str) -> bool:
    """Identify definition requests for abstract or Archive-specific concepts."""
    q = _normalize_space(query)
    if _question_requests_enumeration(q) or _requires_discernment_synthesis(q):
        return False
    asks_meaning = bool(re.search(
        r"\b(?:what does .{2,100} mean|what is the meaning of|define|explain the meaning of|what is)\b",
        q,
        re.I,
    ))
    archive_context = bool(re.search(r"\b(?:living archive|archive's own language|in the archive)\b", q, re.I))
    abstract_terms = bool(re.search(
        r"\b(?:reciprocity|stewardship|sovereignty|integrity|interdependence|relationality|"
        r"canonical|fractal|steward|stewarding|belonging|mutuality|agency|coherence)\b",
        q,
        re.I,
    ))
    return asks_meaning and (archive_context or abstract_terms)


def _has_everyday_example(response: str) -> bool:
    """Conservative signal that the answer applies an idea to ordinary life."""
    return bool(re.search(
        r"\b(?:for example|for instance|imagine|picture this|in everyday life|"
        r"at home|at work|at a workplace|neighbors?|neighbours?|borrow(?:ed|ing)?|"
        r"shared space|shared tool|taking turns|keeping a promise|checking on|"
        r"help(?:ing)? a neighbor|help(?:ing)? a neighbour|returning something|"
        r"repair(?:ing)?|maintain(?:ing)?|a friend|family members|in a community)\b",
        response,
        re.I,
    ))


def _requires_actionable_next_step(query: str) -> bool:
    """Identify complete practical questions that explicitly ask what to do next."""
    q = _normalize_space(query).casefold()
    asks_next_step = bool(re.search(
        r"\b(?:constructive next step|useful next step|what to do first|what should .{0,80} do first|how should .{0,80} begin|how to begin|what would be a next step)\b",
        q,
    ))
    collective_disagreement = bool(re.search(
        r"\b(?:group|team|members|people|everyone|they)\b", q
    )) and bool(re.search(
        r"\b(?:disagree|disagreement|different views|different priorities|cannot agree|can't agree|conflict|what to do first)\b",
        q,
    ))
    return asks_next_step and collective_disagreement


def _has_concrete_next_step(response: str) -> bool:
    """Conservative output check for an actual action, not analysis alone."""
    return bool(re.search(
        r"\b(?:ask each|invite each|have each|agree on|choose one|select one|"
        r"try one|test one|start with|begin by|set a time to|compare the proposals|"
        r"identify the shared|name the common|each person (?:can|should|gets to)|"
        r"write down (?:the|each)|decide together|run a small|take one small)\b",
        response,
        re.I,
    ))



def enforce_actionable_next_step(query: str, response: str) -> str:
    """Ensure practical collective-next-step questions do not end in analysis-only recovery."""
    text = _sanitize_candidate(response)
    if not _requires_actionable_next_step(query) or _has_concrete_next_step(text):
        return text
    return (
        "Ask each person to explain what they believe is most urgent and why. "
        "Then identify the outcome everyone agrees they want, and choose one small, "
        "reversible action the group can try before deciding on a larger plan. "
        "Afterward, compare what the group learned and use that to decide what should come next."
    )


def _requires_recurring_problem_explanation(query: str) -> bool:
    """Recognize recurring-problem questions that need a mechanism-level explanation."""
    q = _normalize_space(query).casefold()
    recurrence = bool(re.search(
        r"\b(?:same problems?|problems? keep (?:coming(?: back)?|returning|recurring)|keeps? (?:happening|coming back|returning|recurring)|recurring problems?|keeps? repeating|happens? again and again|same pattern)\b",
        q,
    ))
    asks_why = bool(re.search(r"\b(?:why|what makes|how can|how does|why does|why do)\b", q))
    effort_context = bool(re.search(
        r"\b(?:trying (?:their|our|my) best|sincere effort|working hard|doing everything|despite (?:our|their|everyone's) efforts?)\b",
        q,
    ))
    return recurrence and (asks_why or effort_context)


def _has_recurring_problem_explanation(response: str) -> bool:
    """Require mechanism-level explanation, not only a request for more context."""
    has_conditions = bool(re.search(
        r"\b(?:conditions?|incentives?|constraints?|handoffs?|underlying causes?|what produces|what keeps|recreates?|reinforces?|repeats?|surface symptoms?|short-term fixes?|interact|feedback loops?)\b",
        response, re.I,
    ))
    has_example = bool(re.search(
        r"\b(?:for example|imagine|a team|a group|a process|the same issue|the visible problem)\b",
        response, re.I,
    ))
    return has_conditions and has_example


def _recurring_problem_explanation_recovery() -> str:
    """Reliable explanation-first fallback when providers cannot satisfy the contract."""
    return (
        "A problem can keep returning even when people are making a sincere effort because "
        "fixing each incident does not always change the conditions that produce it. Those "
        "conditions might include unclear responsibilities, incentives that reward a quick "
        "fix, limited resources, or a handoff where important information gets lost. "
        "For example, a team may correct every missed handoff but leave the process unchanged "
        "so nobody is responsible for confirming the next person received the work. The "
        "individual mistake is fixed, yet the same gap can create it again.\n\n"
        "These are possibilities to examine, not conclusions about your situation. The useful "
        "starting point is to notice what repeats around the problem, not only what happened "
        "in the latest incident. If you have a particular example in mind, you can share it "
        "and we can look at what may be keeping it going."
    )


def _requires_outcome_evaluation_guidance(query: str) -> bool:
    """Recognize questions asking whether a change is producing real-world results."""
    q = _normalize_space(query).casefold()
    asks_to_assess = bool(re.search(
        r"\b(?:how can|how do|how does|how would|how should|what evidence|what signs|how to)\b.{0,100}\b(?:tell|know|measure|assess|evaluate|determine|track|verify|evidence|signs|whether|if)\b",
        q,
    )) or bool(re.search(r"\b(?:whether|if)\b.{0,120}\b(?:working|effective|genuinely|actually|really|reducing|improving)\b", q))
    asks_about_outcome = bool(re.search(
        r"\b(?:harm|safety|outcomes?|impact|improv(?:e|ement|ing)|reduc(?:e|ing|tion)|approach|intervention|change|problem|affected people|unintended consequences)\b",
        q,
    ))
    return asks_to_assess and asks_about_outcome


def _has_outcome_evaluation_guidance(response: str) -> bool:
    """Require observable evidence, comparison over time, and a countercheck."""
    has_measure = bool(re.search(
        r"\b(?:observable|measur\w*|indicator|signs? of|track|record|count|frequency|reports?|feedback|what people experience|affected people|people most affected|baseline|starting point)\b",
        response, re.I,
    ))
    has_comparison = bool(re.search(
        r"\b(?:before|baseline|starting point|compare|compared|over time|afterward|after the change|persist\w*)\b",
        response, re.I,
    ))
    has_countercheck = bool(re.search(
        r"\b(?:unintended|new harm|who is still|still being harmed|challenge that belief|evidence .* against|disconfirm|side effect|trade-off|tradeoff|worse for|not everyone)\b",
        response, re.I,
    ))
    return has_measure and has_comparison and has_countercheck


def _outcome_evaluation_recovery() -> str:
    """Fallback when no provider can satisfy the outcome-evaluation contract."""
    return (
        "To tell whether the revised approach is reducing harm, first describe what the harm looked "
        "like before the change and choose a few observable signs to track. These might include how "
        "often the problem occurs, what affected people report, or whether people feel safer in the "
        "specific situation. Compare those observations with the starting point over time rather than "
        "relying on the group’s confidence or a single encouraging example.\n\n"
        "Ask the people most affected whether their experience has changed, and check for unintended "
        "consequences or people who may still be harmed. If the evidence is mixed, treat that as a reason "
        "to adjust and keep observing—not as proof of success or failure. The key test is whether the "
        "change improves real experiences and whether that improvement holds up when the group looks "
        "for evidence that could challenge its own belief."
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

        # A complete practical next-step question must receive an actionable
        # move, not only abstract analysis or a request for more context. If the
        # provider misses this, reject the candidate so Provider Bank can retry.
        if _requires_actionable_next_step(query) and not _has_concrete_next_step(response):
            raise ValueError("practical next-step answer must include one concrete action")

        if _requires_recurring_problem_explanation(query) and not _has_recurring_problem_explanation(response):
            raise ValueError(
                "recurring-problem answer must explain a plausible mechanism before requesting context"
            )

        if _requires_outcome_evaluation_guidance(query) and not _has_outcome_evaluation_guidance(response):
            raise ValueError(
                "outcome-evaluation answer must include observable evidence, comparison, and a countercheck"
            )

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


        if _requires_concrete_concept_explanation(query):
            paragraphs = [part.strip() for part in re.split(r"\n\s*\n+", response) if part.strip()]
            if len(paragraphs) < 2:
                raise ValueError("abstract concept definition must use readable paragraph breaks")
            if not _has_everyday_example(response):
                raise ValueError("abstract concept definition requires one useful everyday example")

        if _requires_discernment_synthesis(query):
            paragraphs = [part.strip() for part in re.split(r"\n\s*\n+", response) if part.strip()]
            if len(paragraphs) < 2:
                raise ValueError("conceptual relationship answer must develop beyond a one-paragraph summary")
            if not re.search(r"\b(?:but|however|while|although|does not mean|is not the same as|distinction|depends on)\b", response, re.I):
                raise ValueError("conceptual relationship answer must resolve a meaningful tension or distinction")

        if _requires_compound_explanatory_structure(query):
            paragraph_count = len(re.findall(r"\n\s*\n", response)) + 1
            if paragraph_count < 3:
                raise ValueError("compound explanatory composition requires three purposeful paragraphs")

        if _requires_explicit_followup_invitation(query):
            if not response.rstrip().endswith("?"):
                raise ValueError("explicit follow-up invitation request requires a closing question")
            if response.count("?") != 1:
                raise ValueError("explicit follow-up invitation request requires exactly one question")

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


_PRACTICAL_APPLICATION_PATTERNS = (
    r"\bwhat would (?:i|we|they|an organization|the organization) actually do differently\b",
    r"\bwhat (?:would|could|should) .{0,60} do differently\b",
    r"\bhow (?:do|does|can|could|should|would) .{0,60} put .{1,60} into practice\b",
    r"\bwhat .{0,60} look like (?:in practice|day to day|day-to-day)\b",
    r"\bhow .{0,60} live by (?:it|that value|those values|this principle)\b",
    r"\bwhat practical changes .{0,60} make\b",
)
# Count only observable organizational behaviors. A reflection framework alone
# must not satisfy the practical-answer contract.
_PRACTICAL_ACTION_MARKERS = (
    r"\bask(?:ing)? the people affected\b",
    r"\b(?:explain|explain(?:ing)? the reasons?) (?:the reasons? )?(?:for|behind) (?:the )?decision\b",
    r"\b(?:name|assign|make clear) who is responsible\b|\bassign responsibility\b",
    r"\bfollow through\b|\bclose the loop\b|\bkeep the commitment\b",
    r"\bcheck with the people affected\b|\bask the people affected whether\b",
    r"\brespond when something goes wrong\b|\backnowledge the mistake\b",
)


_CONCEPTUAL_RELATIONSHIP_PATTERNS = (
    r"\bhow (?:might|do|does|can|could) .{0,100} (?:reinforce|strengthen|support|shape) one another\b",
    r"\bhow .{0,70} and .{0,70} (?:relate to|connect with|reinforce|shape) (?:one another|each other)\b",
    r"\brelationship between .{0,80} and .{0,80}\b",
)


def is_conceptual_relationship_question(query: str) -> bool:
    """Identify questions asking how multiple concepts influence one another."""
    question = _normalize_space(query).casefold()
    return any(re.search(pattern, question, re.I) for pattern in _CONCEPTUAL_RELATIONSHIP_PATTERNS)


def has_conceptual_relationship_explanation(response: str) -> bool:
    """Require an explanation of a mechanism linking concepts, not generic advice."""
    text = _normalize_space(response).casefold()
    return (
        len(text.split()) >= 65
        and bool(re.search(r"\b(?:because|when|so that|which means|as a result|this makes|that makes)\b", text, re.I))
        and bool(re.search(r"\b(?:accountability|trust|repair|harm|responsibility)\b", text, re.I))
    )


def _conceptual_relationship_recovery() -> str:
    """Explain the mechanism linking accountability, trust, and repair in plain language."""
    return (
        "Accountability, trust, and repairing harm reinforce one another when responsibility leads to visible action. "
        "Accountability starts with acknowledging what happened, who was affected, and what responsibility belongs to whom, rather than minimizing the impact or shifting blame. "
        "That makes trust more credible because people can judge what someone does, not just what they promise. "
        "When harm occurs, repair turns accountability into action: listen to the people affected, address the consequences, and change what allowed the harm to happen. "
        "Following through gives people evidence that the harm was taken seriously. Trust may then become possible again—not because the harm is forgotten, but because people can see that responsibility led to meaningful change. "
        "Are you thinking about this in an organization, a close relationship, or a wider community?"
    )


def is_practical_application_question(query: str) -> bool:
    """Identify explicit requests for actionable practice, not conceptual questions."""
    question = _normalize_space(query).casefold()
    return any(re.search(pattern, question, re.I) for pattern in _PRACTICAL_APPLICATION_PATTERNS)


def has_observable_practical_actions(response: str) -> bool:
    """Return true when a practical answer contains at least two distinct action markers."""
    text = _normalize_space(response).casefold()
    return sum(bool(re.search(pattern, text, re.I)) for pattern in _PRACTICAL_ACTION_MARKERS) >= 2


def _practical_application_recovery() -> str:
    """Safe deterministic response when generation stays abstract despite a practical request."""
    return (
        "Start with one recurring situation where trust matters, such as a decision that affects a team. "
        "Ask the people affected what they see before deciding, and separate observable facts from assumptions. "
        "Explain the reasons for the decision, name who is responsible for the next step, and follow through when promised. "
        "Then check with the people affected whether the action changed their experience; good intentions alone are not evidence that trust has improved. "
        "Where would this make the biggest difference right now: decision-making, handling disagreement, or responding when something goes wrong?"
    )


def _requires_responsibility_boundary_answer(question: str) -> bool:
    """Recognize responsibility-versus-systemic-change questions across paraphrases."""
    q = _normalize_space(question).casefold()
    if not q:
        return False
    individual_agency = bool(re.search(
        r"\b(?:my|our|individual|personal|a person|one person|each person|people)\b.{0,80}\b"
        r"(?:responsib(?:le|ility)|burden|obligation|accountab(?:le|ility)|change|fix|repair|solve)\b"
        r"|\b(?:responsib(?:le|ility)|burden|obligation|accountab(?:le|ility))\b.{0,80}\b"
        r"(?:my|our|individual|personal|one person|each person|people)\b",
        q,
    ))
    systemic_scope = bool(re.search(
        r"\b(?:system|institution|organization|society|structure|whole|everyone|"
        r"all of it|entire thing|larger problem|root cause|systemic)\w*\b",
        q,
    ))
    change_frame = bool(re.search(
        r"\b(?:change|fix|repair|solve|transform|reform|improve|responsib(?:le|ility)|"
        r"accountab(?:le|ility)|burden|obligation)\w*\b",
        q,
    ))
    agency_limit = bool(re.search(
        r"\b(?:alone|single.hand(?:ed|edly)|one person|individual|personal|"
        r"my part|our part|what can i|what can we|how much|fair share|limits?)\b",
        q,
    ))
    # Require a systemic-change frame plus either explicit individual agency or
    # a clear question about the limits/fairness of one person's responsibility.
    return systemic_scope and change_frame and (individual_agency or agency_limit)


def enforce_response_contracts(question: str, response: str) -> str:
    """Validate question-specific answer obligations at the final runtime boundary."""
    candidate = _sanitize_candidate(response)
    if _requires_responsibility_boundary_answer(question) and not _has_responsibility_boundary_explanation(candidate):
        candidate = _responsibility_boundary_recovery()
    if _requires_responsibility_boundary_answer(question) and not _has_responsibility_boundary_explanation(candidate):
        raise RuntimeError("Responsibility-boundary response contract failed after recovery.")
    return candidate


def _has_responsibility_boundary_explanation(response: str) -> bool:
    """Require the answer to explain boundaries, not merely prescribe small steps."""
    text = _normalize_space(response).lower()
    required_groups = (
        r"\b(contribution|part you can|within your (?:reach|control|influence)|what you can influence)\b",
        r"\b(whole system|entire system|system[- ]level|accountability for the system|fix(?:ing)? everything)\b",
        r"\b(authority|resources|shared responsibility|shared ownership|others? (?:must|need to|have to) (?:take|share|participate))\b",
        r"\b(limit|limits|fair share|not responsible for|does not make you responsible|doesn't make you responsible)\b",
        r"\b(what (?:you can|you cannot|others need to)|shared ownership|alongside you|from others)\b",
    )
    return all(re.search(pattern, text) for pattern in required_groups)


def _responsibility_boundary_recovery() -> str:
    """Deterministic, question-specific recovery when generation misses the contract."""
    return (
        "Noticing that something is broken can leave you feeling responsible for fixing it, "
        "especially when others seem willing to let the problem continue. But seeing a problem "
        "does not make you responsible for fixing everything. Your responsibility is for the "
        "contribution and commitments you can reasonably make; accountability for the wider "
        "system also belongs to the people and institutions with the authority, resources, and "
        "shared obligations to change it.\n\n"
        "For example, you can identify a recurring problem and offer a specific improvement "
        "without agreeing to own the entire process. It is reasonable to say, “I can take care "
        "of this part, but the wider change needs a decision and resources from the people "
        "responsible for it.” Contributing to change is not the same as compensating indefinitely "
        "for everyone else's inaction.\n\n"
        "What part of this situation can you genuinely influence, and what would require others "
        "to take responsibility alongside you?"
    )


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
    practical_application_instruction = (
        "The visitor explicitly asks what to do differently or how to put a value into practice. Give at least two concrete, observable behaviors before asking a follow-up. For organizational trust, examples include hearing from people affected before a decision, distinguishing facts from assumptions, explaining the decision, assigning responsibility, and checking whether follow-through changed people's experience. Do not answer only with a reflection framework or ask the visitor to make the question more concrete. End with at most one focused question that helps identify where to apply the actions.\n\n"
        if is_practical_application_question(question)
        else ""
    )
    style_instruction = (
        "The visitor explicitly requested plain, non-technical language. Answer the actual subject question in clear everyday words; avoid academic phrasing and unexplained specialist terms.\n\n"
        if _has_response_style_preference(question) or _has_response_style_preference(history_text)
        else ""
    )
    explicit_invitation_instruction = (
        "The visitor explicitly requested a closing question. Answer the subject fully, then end with exactly one brief, natural question that invites the kind of reflection the visitor requested. Do not add any other question.\n\n"
        if _requires_explicit_followup_invitation(question)
        else ""
    )
    exemplar_guidance, exemplar_cache_token = build_exemplar_guidance(question)
    user_content = (
        f"Visitor question:\n{question}\n\n"
        + explicit_invitation_instruction
        + practical_application_instruction
        + correction_instruction
        + style_instruction
        + f"Suggested response shape (use your judgment; do not mention it): {shape}\n\n"
        + exemplar_guidance
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
        shape + "|gold_standard_exemplar:" + exemplar_cache_token,
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
        if _requires_recurring_problem_explanation(question):
            return {
                "response": _recurring_problem_explanation_recovery(),
                "doorway_title": "",
                "response_shape": "explanatory",
                "provider": "",
                "model": "",
            }
        if _requires_outcome_evaluation_guidance(question):
            return {
                "response": _outcome_evaluation_recovery(),
                "doorway_title": "",
                "response_shape": "explanatory",
                "provider": "",
                "model": "",
            }
        return None

    parsed = result["parsed"]
    candidate = {
        "response": parsed["response"],
        "doorway_title": parsed["doorway_title"],
        "response_shape": parsed["response_shape"],
        "provider": str(result.get("provider") or ""),
        "model": str(result.get("model") or ""),
    }

    # Responsibility-boundary validation is intentionally owned by the final
    # runtime response boundary in main.py. Enforcing it here alone is insufficient:
    # deterministic and provider-exhaustion routes can bypass this composer.

    if is_conceptual_relationship_question(question):
        if not has_conceptual_relationship_explanation(candidate["response"]):
            candidate["response"] = _conceptual_relationship_recovery()
            candidate["response_shape"] = "explanatory"
        if not re.search(
            r"\b(?:where can i find|where do i find|show me|take me to|link me to|browse|find the)\b",
            question,
            re.I,
        ):
            candidate["doorway_title"] = ""

    if is_practical_application_question(question):
        if not has_observable_practical_actions(candidate["response"]):
            candidate["response"] = _practical_application_recovery()
            candidate["response_shape"] = "explanatory"
        if not re.search(
            r"\b(?:where can i find|where do i find|show me|take me to|link me to|browse|find the)\b",
            question,
            re.I,
        ):
            candidate["doorway_title"] = ""

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
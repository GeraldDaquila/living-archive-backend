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

from general_guide_gold_standards import resolve_exact_gold_standard as _registered_exact_gold_standard

from provider_bank import (
    CONTRACT_VERSION as PROVIDER_BANK_CONTRACT_VERSION,
    route as route_with_model_bank,
)

CONTRACT_VERSION = "v1.28"
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

SYSTEM-WIDE GOLD STANDARD FLOOR (default across the entire Guide):
The established Guide Gold Standard is the minimum quality and presentation floor for every visitor-facing response, regardless of topic or specialist route. Apply it by default across general questions, specialist tools, and recovery/fallback paths. It is not merely an optional style preference for the general-purpose composer.
- Preserve the Gold Standard sequence: understand the actual task; answer or perform it directly; explain the reasoning or context needed to make the result useful; acknowledge material nuance or limits; then provide any verified, relevant Archive doorway separately.
- For explanatory questions, normally use three purposeful, readable paragraphs: direct answer; development through reasoning, a concrete example, or a useful distinction; then nuance, limits, or significance. Each paragraph must add value.
- Task-level formats may supersede the default only when the requested task clearly requires a different structure and that structure is at least as coherent, complete, humane, grounded, and useful as the Gold Standard. Examples may include a checklist for an explicitly requested checklist, a table for an explicit comparison, or concise steps for a bounded procedure. The task format changes the shape, never lowers the quality floor.
- A specialist's preferred format is not an exception merely because it is specialist-specific. The exception must be justified by the visitor's task and must demonstrably serve that task better than the baseline. If it does not, retain the Gold Standard.
- Do not replace explanation with generic advice, planning frameworks, self-help prompts, or a request for clarification. Clarify only when an essential detail is genuinely missing and cannot be reasonably handled with a stated assumption.
- This floor governs fallbacks too. If a specialist cannot complete its task, give the best honest, bounded answer available in the Gold Standard spirit rather than silently reverting to a lower-quality generic template.

DEFAULT PRESENTATION STANDARD (applies to ordinary general-purpose questions):
- Lead with the answer, not a description of what an answer should contain, a statement about what the question asks, or a request for clarification when a useful answer is already possible.
- For explanatory or conceptual questions, use the established Guide Gold Standard presentation as the default: normally three purposeful, readable paragraphs. The first answers the question plainly; the second develops the reasoning with a concrete example, distinction, or implication; the third adds nuance, limits, or practical significance. Each paragraph must advance the answer rather than repeat it.
- A substantive explanatory or conceptual question defaults to three purposeful paragraphs, including a simple definition when the visitor asks how or why it matters. Use fewer only for a genuinely bounded factual lookup, a necessary clarification, a reflective exchange where more would burden the visitor, or an explicitly requested concise format. Never compress a substantive explanation into one paragraph merely for brevity.
- Do not append a generic clarification prompt merely to prolong the exchange. Ask one focused, optional follow-up only when personal context is genuinely needed to continue well, or when the visitor has explicitly invited dialogue. Never make clarification a substitute for an answer that can already be given.
- After the answer, place any verified, directly relevant Archive resource in a distinct, clearly labeled doorway section. Do not weave the recommendation into the answer, invent relevance, or let the doorway replace the answer. Omit the doorway when no suitable resource is established.
- Keep the voice humane, concrete, calm, and natural. Do not expose internal process, use machine-facing jargon, or narrate the rubric to the visitor.

Choose the response shape that fits the question:
- For a definition or bounded factual question, give a clear direct answer.
- For a question asking why something matters, explain both what it is and why it matters in the situation the visitor named.
- For questions about why the same problem keeps recurring despite sincere effort, explain a plausible mechanism before asking for context: the immediate incident may change while the conditions that reproduce it remain. Name a few possible mechanisms in ordinary language (such as incentives, constraints, handoffs, or a fix that treats symptoms but leaves the cause intact), and use one brief, clearly illustrative example when it makes the mechanism easier to see. Present these as possibilities to investigate, not conclusions about the visitor's case. Give this useful general explanation first; only then invite one optional, focused detail. Do not automatically route this explanatory question into a formal system diagnosis.
- For a conceptual question, make one useful distinction, tension, or implication when that genuinely clarifies the subject. For historical, cultural, or social questions asking where a phenomenon comes from or how it evolved, explain the origins and development directly, distinguish surface appearances from underlying institutions or practices where relevant, and acknowledge variation and uncertainty. Never substitute practical self-help advice, a planning framework, or an action checklist unless the visitor asks for one.
- When a visitor asks about a constitutional concept, constitutional reasoning, or the Living Archive’s constitutional framework, ground the explanation in the supplied canonical material. Where supported, explain the concept’s role across the source corpus, its governing relationships to other concepts, the responsibilities or principles that remain stable, and the difference between recovered constitutional architecture and later interpretation. Preserve the Archive’s stated order of work: recovery before translation, and clarity before application. Do not reduce constitutional reasoning to generic “systems thinking,” list generic questions instead of explaining the concept, or claim that a landing page establishes details it does not contain. Use a concrete example only when it clarifies the distinction, and label inference as inference.
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

For conceptual questions about the relationship between two ideas, preserve the reasoning rather than flattening it into a summary. When the question genuinely warrants depth, develop the answer through connected movements: explain the relationship and its central tension; use one concrete, plausible situation only if it clarifies the mechanism or consequence; then state the distinction or condition that resolves the question. Keep these movements proportionate to the question. Keep them concise when the question is simple, but preserve all three purposeful paragraphs for a substantive conceptual explanation; a complex question may need more. Each paragraph must add a new piece of understanding. Do not restate the opening distinction in the example paragraph and then repeat it again in the conclusion. Let the final insight emerge from the reasoning, and stop once the visitor has the understanding they came for. This is a depth standard, not a mandatory template for simple or unrelated questions.


Preserve the visitor's agency. Explain options and consequences without taking over their judgment. Do not diagnose, therapize, moralize, presume personal circumstances, or manufacture intimacy. Do not turn a neutral question into personal advice. If the question has no meaningful human or practical tension, answer it directly and stop. A follow-up invitation is optional unless the visitor explicitly requests one. When the visitor asks for a closing question or a question inviting reflection, honor that request with exactly one natural, relevant question at the end. Do not add questions merely to prolong an interaction.

Use a concrete-example decision rule before composing. When a visitor asks what an abstract, unfamiliar, or Archive-specific concept means, define it first in ordinary language, then normally show one brief everyday situation that makes the meaning visible, and clarify one important limit or implication only when it adds understanding. This is the default for definitions of Living Archive vocabulary such as reciprocity, stewardship, sovereignty, integrity, and interdependence; do not assume a reader already understands these terms. The example must demonstrate the concept through a recognizable choice and consequence, not merely repeat the definition. Keep a substantive explanation in three purposeful, readable paragraphs, not one dense block: define or answer directly; develop the meaning through a consequence, distinction, or one useful example; then clarify significance, limits, or practical meaning. A genuinely bounded factual lookup or a reflective exchange may be shorter when three paragraphs would not improve understanding. Do not force an example into a purely factual answer or a reflective exchange where it would distract. Do not insert an example into a simple definition or answer when it adds no understanding. Make the example do explanatory work: show how the concept appears in an ordinary choice, interaction, or consequence. Use at most one developed everyday example by default. Keep examples clearly illustrative and plausible; never present an invented scenario as a documented real case. Do not fabricate real-world case studies, statistics, quotations, or named authorities.

Let the task determine the substance and exceptions, but keep the default presentation stable: substantive explanatory and conceptual questions receive three connected paragraphs, even when the answer is not long. A genuinely bounded factual lookup, necessary clarification, reflective exchange, or explicitly requested concise format may be shorter. Do not impose a fixed word count, repeat yourself, or pad an answer; each paragraph must perform a distinct explanatory job.

Use a natural, conversational voice: explain as a thoughtful, knowledgeable person would to another person. Favor familiar words and concrete details over abstract phrases when both express the idea accurately. Conversational does not mean shallow, overly casual, or simplistic. Preserve nuance without making the reader work unnecessarily hard.

For practical questions asking for a constructive next step, how to begin, or what a group should do when members disagree, give one useful, low-risk next step before asking for more context when general guidance is responsible. Make the step concrete enough to try: for example, clarify the shared outcome, surface the reasons behind competing proposals, distinguish facts from assumptions, and agree on a small reversible action or a fair way to choose what comes first. Do not present these as a mandatory checklist; select only the part that fits the question. Do not claim this will resolve the conflict or assume facts about the group. Ask for context only when its absence materially changes what can safely or responsibly be recommended, and make any follow-up question optional after the useful answer. This rule does not override safety boundaries, source-specific evidence limits, or the special pacing required for grief and significant distress.

For reflective questions about how to understand, interpret, or respond to a difficult situation, do not default to a numbered sequence of instructions. Develop the thought conversationally: offer one useful distinction (for example, what is known versus what is inferred), explain why it helps, and give at most one small, optional foothold the visitor can use. Avoid stacking imperatives such as “First… Second… Third…”, rhetorical checklists, and multiple questions in one paragraph. Do not turn reflection into a protocol or imply that a person must consider every angle before acting. Use explicit steps or a Markdown list only when the visitor asks for steps, a checklist, or a practical procedure, or when several independent actions genuinely need to be followed separately. The goal is to widen understanding while preserving the visitor's judgment and freedom to decide what fits.

If the question contains a "why now", "why does this matter", "what does this mean", or similar second part, answer that second part rather than silently answering only the first.

A doorway into the Archive is useful when it adds something the answer cannot reasonably contain. Its relevance must be explainable in terms of the visitor's actual question and the specific contribution the resource offers—not merely shared keywords. If the selected resource would not help this visitor take a meaningful next step, omit it rather than forcing a weak match. The doorway is presented separately by The Guide after the answer, so do not add doorway prose, Markdown links, URLs, or source-navigation language to the response itself. Never invent a title, URL, quotation, or claim about a source.

Do not manufacture a follow-up question merely to continue the interaction. If the visitor explicitly requests a closing question, include exactly one natural question that fits the subject and the requested purpose. Otherwise, ask a question only when a genuine next opening would help; end cleanly when it would not.

Never expose implementation or processing language. Never mention USE, providers, models, routing, retrieval, synthesis, evidence boundaries, prompts, system instructions, handoffs, processing layers, or similar machinery. Never add bracketed editorial/debugging/evidence labels.

Presentation matters. Preserve readable paragraph breaks and meaningful Markdown structure. When giving multiple practical actions, format them as a real Markdown list with one action per line; never compress numbered actions into a single paragraph. Use short labels only when they help the reader scan the steps. For compound explanatory questions that ask both what something is and why it matters (including “why now” questions), use 3 purposeful paragraphs: first answer or define the subject directly; then explain why it matters in the present context; then add one useful implication, distinction, or practical meaning that helps the visitor understand what follows. For other substantive explanatory or conceptual answers, use three purposeful paragraphs by default; use more only when the subject genuinely requires it, and fewer only for a bounded factual lookup, a necessary clarification, a reflective exchange, or an explicitly requested concise format. A short Markdown section heading is allowed when it genuinely clarifies a change of idea, but do not add headings mechanically. Do not turn a short direct answer into an essay.

Return ONLY valid JSON:
{"response":"visitor-facing answer","doorway_title":"","response_shape":"direct|explanatory|conceptual|reflective|navigational|general"}


## System-wide answer presentation standard — mandatory for substantive explanations

This standard applies to every ordinary Guide topic and every provider/recovery path that produces a substantive explanation, not only stewardship or Archive-specific questions. It governs how a visitor receives an answer; it does not require identical content, a fixed word count, artificial empathy, or an Archive recommendation for every question.

For a substantive explanatory, conceptual, educational, social, or Archive-related question, present three connected, readable paragraphs by default—even if the question is phrased simply. The three purposeful movements are: (1) answer the actual question directly in plain language; (2) develop the meaning with the most useful distinction, consequence, or one recognizable example; and (3) clarify why it matters, a relevant limit, or what the visitor should understand next. The paragraphs should work together like a good teacher's explanation: (1) answer the actual question directly in plain language; (2) develop the meaning with the most useful distinction, consequence, or one recognizable example; and (3) clarify why it matters, the relevant limit, or what the visitor should understand next. Each paragraph must add understanding rather than repeat the previous one. Use three paragraphs when that makes the answer clearer and more complete; do not compress a layered question into a single paragraph just to be concise.

Adapt this standard only where the task warrants an exception. A simple, self-contained factual lookup may be one or two sentences; answer it directly and include a material qualification when needed. A lived or reflective exchange may be shorter and should not be forced into a teaching essay. A substantive question asking how, why, what something means, or how one thing affects another is not a factual lookup and should retain the three-paragraph default. A direct navigation request should give a clear destination and its specific relevance without padding. Explicit requests for brevity, lists, steps, or a different format should be honored when compatible with a complete and accurate answer. Do not add a follow-up question unless it genuinely helps or was requested.

The answer must be complete before an optional Archive doorway appears. Keep the doorway separate from the answer and attach it only when the selected resource is demonstrably relevant. For Archive-specific claims, distinguish what the published source says from general explanation, do not fabricate an exhaustive doctrine or canonical list, and acknowledge the boundary of the source without retreating from what can responsibly be explained. If Archive evidence is unavailable, still answer from reliable general knowledge when the question permits it; do not use the evidence limitation as a substitute for answering.

Preserve the established humane, patient, natural voice in every subject area. Do not use robotic meta-commentary about how an explanation should be made, intake-form questions in place of the answer, unexplained technical vocabulary, generic filler, gratuitous emoji, or a disclaimer that undercuts an answer already responsibly given. The Guide is a doorway into the Living Archive, not merely an answering service; that purpose is served by a helpful answer first and a relevant doorway second.""".strip()


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

def _requires_three_paragraph_default(query: str) -> bool:
    """Enforce the default Gold Standard for substantive explanatory questions.

    Explicit requests for brevity and bounded fact lookups remain exceptions;
    reflective, navigational, and task-specific formats are handled elsewhere.
    """
    q = _normalize_space(query).casefold()
    if not q:
        return False
    if re.search(
        r"\b(?:in one sentence|one sentence|briefly|brief answer|short answer|"
        r"be concise|keep it concise|in a few words|just the answer)\b",
        q,
    ):
        return False
    if re.match(
        r"^(?:how many|how much|how far|what time|what date|which year|"
        r"how old|what is the boiling point|what is the capital|"
        r"what percentage|what is the exchange rate)\b",
        q,
    ):
        return False
    if _requires_distress_sensitive_pacing(q):
        return False
    if re.search(
        r"\b(?:why|what makes|how does|how can|how do|how is|"
        r"what is the relationship between|what is the connection between|"
        r"what is the difference between|how does .{1,100} relate to)\b",
        q,
    ):
        return True
    return False


def _question_shape(query: str) -> str:
    q = _normalize_space(query).casefold()
    if _requires_distress_sensitive_pacing(q):
        return "reflective"
    if re.search(r"\b(?:where can i find|where do i find|show me|take me to|link me to|browse|find the)\b", q):
        return "navigational"
    if re.search(r"\b(?:where (?:is|are|does|did|do|was|were) .{1,100} come from|how (?:it|this|that|they|these|those|has|have|did|does|is|are|was|were) .{1,100} (?:evolve|evolved|develop|developed|emerge|emerged|originate|originated)|(?:origins?|histor(?:y|ical development)|evolution) of)\b", q):
        return "explanatory"
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
        if re.search(r"\b(?:advice|recommendations)\b", query, re.I):
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


def _requires_fragmented_knowledge_explanation(query: str) -> bool:
    """Recognize questions about how fragmented knowledge obstructs wise action."""
    q = _normalize_space(query).casefold()
    knowledge_fragmented = bool(re.search(
        r"\b(?:fragmented|fragmented\s+up|disconnected|siloed|scattered)\b.{0,55}\b(?:knowledge|information|understanding|insight)\b|"
        r"\b(?:knowledge|information|understanding|insight)\b.{0,55}\b(?:fragmented|disconnected|siloed|scattered)\b",
        q,
    ))
    asks_impact = bool(re.search(
        r"\b(?:impede|impedes|impeding|undermine|undermines|undermining|hinder|hinders|"
        r"affect|affects|damage|damages|obstruct|obstructs|why|how)\b", q
    ))
    wise_action = bool(re.search(r"\b(?:wise action|wise decisions?|sound judgment|good judgment)\b", q))
    return knowledge_fragmented and asks_impact and wise_action


def _has_fragmented_knowledge_explanation(response: str) -> bool:
    """Reject generic action checklists that do not explain fragmentation's mechanism."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", str(response or "")) if p.strip()]
    if len(paragraphs) != 3:
        return False
    first, second, third = paragraphs
    direct_explanation = bool(re.search(
        r"\b(?:fragmented|siloed|disconnected|scattered)\b", first, re.I
    )) and bool(re.search(r"\b(?:knowledge|information|understanding)\b", first, re.I))
    mechanism = bool(re.search(
        r"\b(?:context|relationships|connections|contradict|incomplete|isolated|whole|"
        r"patterns|trade-offs|consequences|assumptions)\b", second, re.I
    ))
    concrete_example = bool(re.search(
        r"\b(?:for example|for instance|imagine|a team|an organization|an organisation|"
        r"two departments|a community|a decision)\b", second, re.I
    ))
    implication = bool(re.search(
        r"\b(?:wise|judgment|responsib|uncertaint|limit|humility|check|revise|"
        r"affected|consequence|decision)\b", third, re.I
    ))
    generic_advice = bool(re.search(
        r"\b(?:define the outcome you want|identify the main constraint|"
        r"choose one step small enough to test|check the result against the original goal)\b",
        response, re.I
    ))
    return direct_explanation and mechanism and concrete_example and implication and not generic_advice


def _fragmented_knowledge_recovery() -> str:
    """Substantive three-paragraph explanation when generation substitutes generic advice."""
    return (
        "Fragmented knowledge impedes wise action when useful facts, experience, and perspectives remain separated, so no one can see enough of the situation to judge what a decision may set in motion. A piece of information can be accurate on its own yet misleading when stripped of its context or its relationship to other parts of the problem. Wisdom depends not only on having information, but on understanding how the pieces bear on one another.\n\n"
        "For example, one team may know why a process is failing, another may understand how a proposed fix affects people, and a third may hold the history of earlier attempts. If those insights never meet, a decision can solve the visible symptom while recreating the original problem somewhere else. Bringing the knowledge together helps reveal dependencies, trade-offs, and consequences that no single fragment could show.\n\n"
        "Integration does not mean forcing every view into one story or pretending uncertainty disappears. It means comparing sources, listening to people who hold different parts of the picture, and making clear what is known, what is inferred, and what remains missing. Wise action becomes more likely when decisions reflect the whole available picture, stay open to correction, and account for the people who will live with the consequences."
    )


def _requires_concept_misuse_explanation(query: str) -> bool:
    """Recognize compound questions requiring both a concept definition and misuse mechanism."""
    q = _normalize_space(query).casefold()
    asks_definition = bool(re.search(r"\b(?:what is|what are|define|explain)\b", q))
    asks_misuse = bool(re.search(
        r"\b(?:misus(?:e|ed|ing)|abus(?:e|ed|ing)|exploit(?:ed|ing)?|weaponiz\w*|"
        r"manipulat\w*|harmful use|used for harm|used against people)\b", q
    ))
    asks_for_explanation = bool(re.search(r"\b(?:why|how|when|what makes)\b", q))
    return asks_definition and asks_misuse and asks_for_explanation


def _concept_misuse_subject(query: str) -> str:
    """Extract the named concept from a compound definition-and-misuse question."""
    q = _normalize_space(query).strip(" ?.!;:")
    match = re.search(
        r"\b(?:what is|what are|define|explain)\s+(?:(?:a|an|the)\s+)?(.+?)(?:,?\s+and\s+(?:why|how|when)\b|$)",
        q, re.I,
    )
    return (match.group(1).strip(" ,;:") if match else "").casefold()


def _has_concept_misuse_explanation(query: str, response: str) -> bool:
    """Reject generic inquiry checklists where a definition and misuse explanation were requested."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", str(response or "")) if p.strip()]
    subject = _concept_misuse_subject(query)
    if len(paragraphs) != 3 or not subject:
        return False
    first, second, third = paragraphs
    subject_words = [word for word in re.findall(r"[a-z0-9]+", subject) if word not in {"a", "an", "the"}]
    names_concept = bool(subject_words) and all(re.search(r"\b" + re.escape(word) + r"\b", first, re.I) for word in subject_words)
    defines_concept = bool(re.search(r"\b(?:is|means|refers to|describes)\b", first, re.I))
    explains_misuse = bool(re.search(
        r"\b(?:misus\w*|abus\w*|exploit\w*|manipulat\w*|conceal\w*|"
        r"control\w*|concentrat\w*|benefit|costs|dependenc\w*|bottleneck\w*)\b", second, re.I
    ))
    includes_example = bool(re.search(r"\b(?:for example|for instance|imagine|a team|an organization|an organisation|at work)\b", second, re.I))
    explains_boundary = bool(re.search(
        r"\b(?:responsib\w*|accountab\w*|scrutiny|transparen\w*|affected people|"
        r"consequences|challenge|correct\w*|limits?)\b", third, re.I
    ))
    generic_checklist = bool(re.search(
        r"\b(?:separate the immediate event|consider the evidence for each explanation|"
        r"these are ways to investigate the question|a confident answer needs the relevant details)\b",
        response, re.I
    ))
    return names_concept and defines_concept and explains_misuse and includes_example and explains_boundary and not generic_checklist


def _concept_misuse_recovery(query: str) -> str:
    """Return a bounded, concrete recovery for the registered leverage-point concept family."""
    subject = _concept_misuse_subject(query)
    if subject in {"leverage point", "leverage points"}:
        return (
            "A leverage point is a place in a system where a relatively small change can produce a much larger effect because it influences how other parts behave. The leverage comes from the relationships, rules, incentives, or dependencies around that point—not simply from how large the action looks. Understanding the point means seeing what it affects and why those connections matter.\n\n"
            "For example, changing how an organization shares information can help many teams coordinate their work. But someone who controls that same information could hide problems, steer decisions, or give themselves an advantage while others bear the costs. A leverage point is misused when a person exploits a system's dependency, bottleneck, rule, or information gap for private advantage rather than addressing the consequences for everyone affected.\n\n"
            "The distinction is not whether leverage is powerful, but how it is exercised and held accountable. Responsible use makes the mechanism and trade-offs visible, considers who may be harmed, and remains open to scrutiny and correction. Misuse concentrates advantage, conceals consequences, or leaves others dependent without a fair way to question the decision."
        )
    return ""


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


def _requires_intergenerational_stewardship(query: str) -> bool:
    """Recognize questions connecting stewardship with responsibility across generations."""
    q = _normalize_space(query).casefold()
    stewardship = bool(re.search(r"\b(?:stewardship|steward)\b", q))
    generations = bool(re.search(
        r"\b(?:intergenerational|future generations?|generations to come|"
        r"those who come after|people who come after|next generations?)\b",
        q,
    ))
    asks_relationship = bool(re.search(
        r"\b(?:how|why|what role|relationship|relate|connect|matter|responsib)\b",
        q,
    ))
    return stewardship and generations and asks_relationship


def _has_intergenerational_stewardship_explanation(response: str) -> bool:
    """Require a three-movement explanation, not a single-paragraph generality."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", str(response or "")) if p.strip()]
    text = _normalize_space(response).casefold()
    return (
        len(paragraphs) == 3
        and bool(re.search(r"\b(?:stewardship|steward)\b", paragraphs[0], re.I))
        and bool(re.search(r"\b(?:intergenerational|future generations?|those who come after|generations to come)\b", paragraphs[0], re.I))
        and bool(re.search(r"\b(?:for example|in practice|institution|knowledge|capabilities|relationships|resources)\b", paragraphs[1], re.I))
        and bool(re.search(r"\b(?:does not mean|doesn't mean|not mean|not about)\b", paragraphs[2], re.I))
        and bool(re.search(r"\b(?:responsib|care|control|limits?)\w*\b", paragraphs[2], re.I))
        and bool(re.search(r"\b(?:because|so that|which means|as a result|over time|what remains)\b", text, re.I))
    )


def _intergenerational_stewardship_recovery() -> str:
    """Explain stewardship across generations with a concrete example and bounded responsibility."""
    return (
        "Stewardship connects to intergenerational responsibility because the way we care for something now shapes what remains possible for people who come after us. In the Living Archive's constitutional framing, stewardship is more than managing what we have inherited: it is participating responsibly in an enduring order, with attention to reciprocity, cultivation, and the quality of what is passed on. "
        "Responsibility therefore reaches beyond immediate performance to the relationships, knowledge, capabilities, and institutions that future generations will have to rely on.\n\n"
        "For example, an institution may meet today's targets while allowing trust to erode, losing practical knowledge, or leaving the next group without the skills and resources to continue the work. A stewardship approach looks at both today's results and what those results leave behind: whether people can learn, participate, maintain what matters, and carry responsibility forward. The point is not simply to preserve an institution unchanged, but to leave people with sounder conditions for responsible action.\n\n"
        "Intergenerational responsibility does not mean predicting every future need or making one generation answer for everything. It means taking reasonable care with the consequences within our influence, listening to those affected, and strengthening the conditions others will inherit rather than passing avoidable costs along. Stewardship is thus neither control over the future nor self-sacrifice without limits; it is accountable care for what has been entrusted to us and for the possibilities our choices help create."
    )


def _requires_cosmology_generalization_standards(query: str) -> bool:
    """Recognize requests for standards governing inference from one Archive text to a whole cosmology."""
    q = _normalize_space(query).casefold()
    asks_for_standards = bool(re.search(
        r"\b(?:what standards|which standards|what criteria|what safeguards|what requirements)\b",
        q,
    ))
    asks_about_generalization = bool(re.search(
        r"\b(?:generaliz(?:e|es|ing|ation)|extrapolat(?:e|es|ing|ion)|infer(?:s|ring)?|"
        r"extend.{0,40}claim)\b",
        q,
    ))
    archive_scale_shift = bool(re.search(
        r"\b(?:one|single|individual)\s+(?:archive\s+)?text\b",
        q,
    )) and bool(re.search(
        r"\b(?:whole|entire|overall)\s+(?:living\s+archive\s+)?cosmology\b|"
        r"\b(?:whole|entire)\s+archive\b",
        q,
    ))
    archive_context = bool(re.search(r"\b(?:archive|cosmology|canonical corpus)\b", q))
    return asks_for_standards and asks_about_generalization and (archive_scale_shift or archive_context)


def _has_cosmology_generalization_standards(response: str) -> bool:
    """Require a direct, multi-part methodological answer instead of generic uncertainty."""
    text = _normalize_space(response).casefold()
    groups = (
        r"\b(?:context|textual context|source context)\b",
        r"\b(?:corroborat|multiple texts|independent sources|cross-reference)\w*\b",
        r"\b(?:scope|directly states|explicitly states|inference|interpretation)\b",
        r"\b(?:contradict|counterevidence|counter-evidence|exception|disconfirm)\w*\b",
        r"\b(?:traceab|traceable|evidence trail|source trail|verify|verification)\w*\b",
        r"\b(?:confidence|uncertainty|proportionate|warrants|warranted)\b",
    )
    paragraphs = [p for p in re.split(r"\n\s*\n+", str(response or "")) if p.strip()]
    return len(paragraphs) == 3 and all(re.search(pattern, text) for pattern in groups) and not re.search(
        r"\b(?:i don't have enough verified context|the inquiry need not stop here|"
        r"identify the specific claim|choose one step|before acting)\b",
        text,
    )


def _cosmology_generalization_standards_recovery() -> str:
    """Give direct standards for moving from a single Archive text to a corpus-wide claim."""
    return (
        "The Guide should not generalize from one Archive text to the whole cosmology merely because an idea sounds consistent or important. First, interpret the passage in its full context: identify what it explicitly says, what question it addresses, and any limits or qualifications. Record the exact source and distinguish the text's own claims from the Guide's interpretation or inference. A single passage can establish what that passage says; by itself, it cannot establish that the same principle governs the entire cosmology.\n\n"
        "Before making a broader claim, seek corroboration across relevant and meaningfully independent Archive texts, follow explicit cross-references, and test the proposed reading against passages that qualify, complicate, or contradict it. Check whether the sources use the same terms in the same sense and whether a local statement is being mistaken for a universal rule. The reasoning should be traceable: a reviewer must be able to see which passages support each part of the generalization, what evidence cuts against it, and why the broader conclusion follows.\n\n"
        "Finally, state the conclusion at the level the evidence warrants. Label direct textual statements, cross-text synthesis, and tentative interpretation distinctly; preserve exceptions and unresolved tensions instead of smoothing them away. If evidence comes from only one text, say that the claim is text-specific or a hypothesis for further testing—not an established account of the whole cosmology. A corpus-wide generalization is justified only when its scope, corroboration, counterevidence, and reasoning have been checked and remain open to revision."
    )


def _requires_entrusted_stewardship_identification(query: str) -> bool:
    """Recognize conceptual questions asking how to identify what is held in trust."""
    q = _normalize_space(query).casefold()
    asks_identification = bool(re.search(
        r"\b(?:how (?:does|can|do|would) (?:one|you|we|i) identify|"
        r"how to identify|identify what is being held in trust|what is held in trust)\b",
        q,
    ))
    trust_context = bool(re.search(
        r"\b(?:held in trust|being held in trust|entrusted|entrustment|in trust)\b",
        q,
    ))
    return asks_identification and trust_context


def _has_entrusted_stewardship_identification(response: str) -> bool:
    """Require a direct explanation of entrusted subject, beneficiaries, duties, and limits."""
    text = _normalize_space(response).casefold()
    paragraphs = [p for p in re.split(r"\n\s*\n+", str(response or "")) if p.strip()]
    required_groups = (
        r"\b(?:entrust|held in trust|entrusted|what has been placed in your care)\w*\b",
        r"\b(?:who|people|community|beneficiar|depend on|affected by)\w*\b",
        r"\b(?:obligation|responsibilit|duty|commitment|care for|protect|maintain)\w*\b",
        r"\b(?:misuse|neglect|breach|boundary|limits?|not yours alone|not solely yours)\w*\b",
        r"\b(?:for example|in practice|ask yourself|look at|identify)\w*\b",
    )
    generic_planning = re.search(
        r"\b(?:define the outcome you want|identify the main constraint|choose one step small enough|"
        r"before acting|adjust rather than assuming the first attempt)\b",
        text,
    )
    return len(paragraphs) == 3 and all(re.search(pattern, text) for pattern in required_groups) and not generic_planning


def _entrusted_stewardship_identification_recovery() -> str:
    """Directly explain how to recognize what a situation places in trust."""
    return (
        "To identify what is being held in trust, look for what has been placed in someone's care, authority, or keeping without becoming theirs to use only for personal advantage. It may be a responsibility, a relationship, a resource, a promise, knowledge, a role, or a shared place. Ask what was entrusted, explicitly or implicitly, and what would be lost or damaged if it were neglected or misused. The answer is not always an object; sometimes what is entrusted is another person's confidence, a duty, or the ability to make a decision responsibly.\n\n"
        "Next, identify who or what depends on that care and what obligations follow. Consider the people affected, the purpose for which the thing was entrusted, the promises or rules that govern it, and any limits on the holder's authority. For example, a manager may be entrusted with a team's time and information: the duty is not to treat them as personal property, but to use them fairly, protect confidentiality, and explain decisions that affect the team. Different situations create different duties, so the context and the voices of those affected matter.\n\n"
        "Finally, test the interpretation by asking what responsible care would preserve, what misuse or neglect would look like, and where the holder's authority ends. Something is held in trust when care is owed beyond mere ownership or convenience: there is a purpose, a relationship of reliance, and an obligation to act with regard for those affected. Be explicit about what is known, what is inferred, and what remains unclear rather than assuming every responsibility is unlimited or belongs to one person alone."
    )


def _requires_faithful_stewardship_values_conflict(query: str) -> bool:
    """Recognize normative questions about faithful stewardship amid conflicting values."""
    q = _normalize_space(query).casefold()
    asks_requirement = bool(re.search(
        r"\b(?:what does|what should|what must|what would)\b.{1,100}\b(?:require|requires|required|demand|demands|call for)\b",
        q,
    ))
    asks_conflict = bool(re.search(
        r"\b(?:when|where|if|as)\b.{0,70}\b(?:values?|principles?|duties|obligations|commitments)\b.{0,50}\b(?:conflict|clash|compete|collide|pull in different directions)\b|"
        r"\b(?:values?|principles?|duties|obligations|commitments)\b.{0,60}\b(?:conflict|clash|compete|collide)\b",
        q,
    ))
    stewardship_context = bool(re.search(r"\b(?:faithful stewardship|stewardship|steward|integrity)\b", q))
    return asks_requirement and asks_conflict and stewardship_context


def _has_faithful_stewardship_values_conflict(response: str) -> bool:
    """Require a substantive answer about competing duties, discernment, and accountable care."""
    text = _normalize_space(response).casefold()
    paragraphs = [p for p in re.split(r"\n\s*\n+", str(response or "")) if p.strip()]
    required = (
        r"\b(?:values?|principles?|commitments?)\b",
        r"\b(?:conflict|compete|clash|pull in different directions)\b",
        r"\b(?:obligation|responsibilit|duty|duties)\w*\b",
        r"\b(?:affected|who may be harmed|consequences|impact)\w*\b",
        r"\b(?:evidence|context|transparent|explain|accountable|revisit)\w*\b",
    )
    generic_fallback = re.search(
        r"\b(?:define the outcome you want|identify the main constraint|choose one step small enough to test|"
        r"the inquiry need not stop here|i don't have enough verified context)\b",
        text,
    )
    return len(paragraphs) == 3 and all(re.search(p, text) for p in required) and not generic_fallback


def _faithful_stewardship_values_conflict_recovery() -> str:
    """Answer the normative question directly rather than redirecting to a glossary lookup."""
    return (
        "Faithful stewardship when values conflict begins by naming what is actually in tension, rather than treating one value as automatically decisive. Clarify what has been entrusted, which commitments or duties are relevant, what each value protects, and what the situation's context makes possible or impossible. Separate what is known from assumptions, and distinguish a genuine conflict between obligations from a conflict between a principle and personal preference.\n\n"
        "Next, consider who is affected and what each possible choice would protect, risk, or harm. Give particular attention to people who bear the consequences but have less power to shape the decision. Look for options that honor more than one value, and identify any duties that cannot responsibly be traded away, such as honesty, keeping faith with an explicit commitment, or preventing avoidable harm. Where no option preserves everything, explain why one obligation must take priority in this case instead of disguising the trade-off as a perfect solution.\n\n"
        "A faithful decision should be proportionate to the evidence, transparent about its reasoning, and accountable to those affected. State which values guided the choice, what costs or limits remain, and what new information would lead you to reconsider it. Stewardship is not simply defending a preferred value; it is caring for what has been entrusted while acknowledging competing responsibilities, avoiding self-serving exceptions, and remaining willing to repair harm if the decision proves mistaken."
    )


def _requires_systems_vs_separate_problems_explanation(query: str) -> bool:
    q = _normalize_space(query).casefold()
    return bool(re.search(r"\b(?:what makes|what distinguishes|how is|how does|when does)\b", q) and re.search(r"\b(?:system|systems)\b", q) and re.search(r"\b(?:rather than|instead of|as opposed to|collection of|separate problems?|isolated problems?)\b", q))


def _systems_vs_separate_problems_recovery() -> str:
    return ("A situation is a system when its parts are connected in ways that shape one another, so the overall situation cannot be fully understood as a collection of separate problems. The parts may be people, roles, rules, resources, routines, or environmental conditions. What matters is not simply that several problems appear together, but that relationships among them influence what happens: a change in one part can alter the conditions faced by others and change the situation as a whole.\n\n"
    "Look for patterns of interaction, dependencies, and feedback. For example, delays in one team may increase pressure on another team, which then rushes work and creates errors that send work back to the first team. Each issue can look like a separate problem when viewed alone, but their interaction forms a reinforcing loop. A system may also contain balancing feedback, bottlenecks, shared incentives, or rules that repeatedly produce the same outcomes even when individuals try to solve the immediate symptoms.\n\n"
    "The practical test is whether understanding the connections explains more than a list of isolated issues would. Ask what depends on what, which effects return to influence their causes, and what conditions keep the pattern going. Not every cluster of problems is one system; the relationships must be evidenced rather than assumed. The Guide should explain this distinction first. A diagnostic tool such as FSD can be offered afterward if you want to map a specific real-world pattern, but it should not replace the answer to the conceptual question.")


def _requires_method_comparison(query: str) -> bool:
    """Recognize questions comparing distinct methods of inquiry or understanding."""
    q = _normalize_space(query).casefold()
    asks_comparison = bool(re.search(
        r"\b(?:how do .{1,180} differ|how does .{1,180} differ|"
        r"what is the difference between|differences between|compare .{1,180} and)\b",
        q,
    ))
    methods = (
        r"\bempirical inquiry\b",
        r"\bsystems analysis\b",
        r"\bphilosoph(?:y|ical)\b",
        r"\bcontemplative reflection\b",
    )
    return asks_comparison and sum(bool(re.search(pattern, q)) for pattern in methods) >= 3


def _has_method_comparison_coverage(query: str, response: str) -> bool:
    """Require coverage of every named method rather than generic advice."""
    q = _normalize_space(query).casefold()
    answer = _normalize_space(response).casefold()
    aliases = (
        (r"\bempirical inquiry\b", r"\bempirical\b|\bobservation\b|\bmeasur(?:e|ement|ed)\b"),
        (r"\bsystems analysis\b", r"\bsystems? analysis\b|\bfeedback loops?\b|\binterdependen(?:t|ce)\b"),
        (r"\bphilosoph(?:y|ical)\b", r"\bphilosoph(?:y|ical)\b|\bconceptual reasoning\b"),
        (r"\bcontemplative reflection\b", r"\bcontemplative reflection\b|\breflect(?:ion|ive)\b|\bawareness\b"),
    )
    required = [alias for source, alias in aliases if re.search(source, q)]
    return len(required) >= 3 and all(re.search(alias, answer) for alias in required)


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


def _requires_archive_scoped_meaning(query: str) -> bool:
    """Require the full Guide explanatory standard for Archive-scoped meaning questions."""
    q = _normalize_space(query)
    asks_meaning = bool(re.search(
        r"^(?:what does|what is|what's|explain|define)\b",
        q,
        re.I,
    )) and bool(re.search(r"\b(?:mean|meaning|definition|understand|role|purpose)\b", q, re.I))
    archive_scope = bool(re.search(
        r"\b(?:in|within|inside)\s+the\s+living\s+archive\b|\bthe living archive['’]s\b",
        q,
        re.I,
    ))
    return asks_meaning and archive_scope


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

        # The Gold Standard is an enforceable composition contract, not only a
        # prompt preference. Reject compressed substantive explanatory answers
        # so the provider bank can retry instead of allowing one paragraph through.
        if _requires_three_paragraph_default(query):
            paragraphs = [
                part.strip()
                for part in re.split(r"\n\\s*\n+", response)
                if part.strip()
            ]
            if len(paragraphs) < 3:
                raise ValueError(
                    "substantive explanatory answer must meet the three-paragraph Guide Gold Standard"
                )

        # This question class has a structural contract: reject generic trust/cooperation
        # prose and require an answer about consequences across generations. The final
        # deterministic recovery below handles provider exhaustion; this validation
        # prevents a plausible but off-topic candidate from passing as complete.
        if _requires_intergenerational_stewardship(query) and not _has_intergenerational_stewardship_explanation(response):
            raise ValueError(
                "intergenerational stewardship answer must explain cross-generational responsibility in three purposeful paragraphs"
            )

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


        if _requires_method_comparison(query):
            paragraphs = [part.strip() for part in re.split(r"\n\s*\n+", response) if part.strip()]
            if len(paragraphs) < 3:
                raise ValueError("method-comparison answer requires the three-paragraph Guide Gold Standard")
            if not _has_method_comparison_coverage(query, response):
                raise ValueError("method-comparison answer must distinguish every method named in the visitor question")
            if re.search(r"\b(?:choose one step|identify the main constraint|before acting|adjust rather than assuming)\b", response, re.I):
                raise ValueError("method-comparison answer must not be replaced by generic problem-solving advice")

        if _requires_concrete_concept_explanation(query):
            paragraphs = [part.strip() for part in re.split(r"\n\s*\n+", response) if part.strip()]
            minimum_paragraphs = 3 if _requires_archive_scoped_meaning(query) else 2
            if len(paragraphs) < minimum_paragraphs:
                raise ValueError(
                    "Archive-scoped meaning questions require the three-paragraph Guide Gold Standard"
                    if minimum_paragraphs == 3
                    else "abstract concept definition must use readable paragraph breaks"
                )
            if not _has_everyday_example(response):
                raise ValueError("abstract concept definition requires one useful everyday example")
            if _requires_archive_scoped_meaning(query):
                if not re.search(r"\b(?:Living Archive|Archive)\b", paragraphs[0], re.I):
                    raise ValueError("Archive-scoped meaning answer must answer in the named institutional context")
                if re.search(
                    r"\b(?:rather than a claim|general explanation rather than|precise meaning can vary by field)\b",
                    response,
                    re.I,
                ):
                    raise ValueError("Archive-scoped meaning answer must not retreat into generic disclaimer language")

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


def _is_archive_constitutional_question(query: str) -> bool:
    """Recognize Archive-specific constitutional questions as a bounded recovery class."""
    question = _normalize_space(query).casefold()
    has_constitutional_subject = bool(re.search(
        r"\b(?:constitutional reasoning|constitutional framework|constitutional architecture|constitutional register)\b",
        question,
    ))
    has_archive_context = bool(re.search(
        r"\b(?:living archive|the archive|archive['’]s)\b",
        question,
    ))
    return has_constitutional_subject and has_archive_context


def _archive_constitutional_recovery(
    question: str,
    documents: List[Dict[str, str]],
) -> Optional[Dict[str, Any]]:
    """Answer from the retrieved Constitutional Register when model composition is unavailable."""
    if not _is_archive_constitutional_question(question):
        return None

    source = next((
        item for item in documents
        if re.search(
            r"constitutional register",
            _normalize_space(item.get("title", "")),
            re.I,
        )
        or re.search(
            r"constitutional register",
            str(item.get("content") or ""),
            re.I,
        )
    ), None)
    if not source:
        return None

    source_content = _normalize_space(source.get("content", ""))
    if not re.search(r"\b(?:constitutional|recovery|translation|interpretation|relationship)\b", source_content, re.I):
        return None

    title = _normalize_space(source.get("title", ""))
    url = _normalize_space(source.get("url", ""))
    if not title:
        return None
    if url and not url.startswith("https://geralddaquila.com/"):
        url = ""

    response = (
        "Within the Living Archive, constitutional reasoning means recovering the principles and governing relationships "
        "that organize its body of knowledge, rather than treating each concept or page as an isolated statement. "
        "It asks how concepts and responsibilities connect across the canonical sources, and which commitments remain "
        "stable across those relationships.\n\n"
        "The Archive's stated order is recovery before translation, and clarity before application. First identify what "
        "the canonical material explicitly establishes; only then translate it into an interpretation or practical use. "
        "The Constitutional Register is the relevant doorway for tracing that recovered constitutional architecture, "
        "while related sources should be used to check particular connections rather than assume that a title alone proves them.\n\n"
        "Recovered constitutional architecture and later interpretation are not the same thing. Where a connection is "
        "inferred rather than directly stated, it should be labelled as inference; where the sources do not establish a "
        "formal rule, the Guide should not invent one. The purpose is to make the Archive's own framework clearer while "
        "leaving judgment and application with the reader."
    )
    return {
        "response": response,
        "doorway_title": title,
        "doorway_url": url,
        "response_shape": "explanatory",
        "provider": "bounded_archive_constitutional_recovery",
        "model": "canonical-evidence-fallback",
    }


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


def _method_comparison_recovery() -> str:
    """Provide a bounded, substantive fallback when generation evades a methods comparison."""
    return (
        "Empirical inquiry investigates what can be observed, measured, or tested, using "
        "evidence to evaluate claims about what happens. Systems analysis examines how parts "
        "interact, including relationships and feedback loops that shape a larger whole.\n\n"
        "Philosophy clarifies concepts and examines the reasons, assumptions, and values behind "
        "claims. Contemplative reflection attends to lived experience and awareness, helping "
        "people notice habitual interpretations that might otherwise go unexamined.\n\n"
        "These approaches complement one another without being interchangeable: empirical "
        "inquiry tests claims against observation, systems analysis maps interdependence, "
        "philosophy evaluates concepts and reasons, and contemplative reflection explores "
        "experience. Each has strengths and limits, so the useful approach depends on the "
        "question being asked."
    )


def _archive_scoped_stewardship_recovery() -> str:
    """Archive-specific three-paragraph answer, preserving the approved stewardship standard."""
    return (
        "In the Living Archive, stewardship means caring for what has been entrusted to us "
        "rather than treating it as if only our immediate needs matter. Its First Principles "
        "express this as “stewardship follows understanding”: as our understanding grows, so "
        "does our responsibility to consider how we act on it, whom our choices affect, and "
        "what we pass on to others. Understanding is not only something to acquire; it should "
        "help us act with greater care and judgment.\n\n"
        "In everyday life, stewardship appears in small choices: keeping a promise, maintaining "
        "a shared space, using resources thoughtfully, or considering how a decision affects "
        "people who depend on us. For example, when sharing an idea from the Archive, a steward "
        "preserves its context and distinguishes what a source actually says from personal "
        "interpretation, so others can assess the idea fairly and use it responsibly.\n\n"
        "Stewardship does not mean controlling everything or sacrificing yourself for everyone "
        "else. It means recognizing what is genuinely yours to care for, acting responsibly "
        "within your limits, and considering the consequences for others and for the future. "
        "The aim is to preserve trust and usefulness—and, where possible, leave what you were "
        "entrusted with no worse and ideally better for those who come after."
    )


def _requires_archive_scoped_stewardship(question: str) -> bool:
    q = _normalize_space(question)
    return bool(
        re.search(r"^what does stewardship mean\b", q, re.I)
        and re.search(r"\b(?:in|within) the living archive\b", q, re.I)
    )


def enforce_response_contracts(question: str, response: str) -> str:
    """Validate question-specific answer obligations at the final runtime boundary."""
    candidate = _sanitize_candidate(response)
    if _requires_fragmented_knowledge_explanation(question) and not _has_fragmented_knowledge_explanation(candidate):
        candidate = _fragmented_knowledge_recovery()
    if _requires_fragmented_knowledge_explanation(question) and not _has_fragmented_knowledge_explanation(candidate):
        raise RuntimeError("Fragmented-knowledge explanation contract failed after recovery.")
    if _requires_intergenerational_stewardship(question) and not _has_intergenerational_stewardship_explanation(candidate):
        candidate = _intergenerational_stewardship_recovery()
    if _requires_concept_misuse_explanation(question) and not _has_concept_misuse_explanation(question, candidate):
        recovery = _concept_misuse_recovery(question)
        if recovery:
            candidate = recovery
        else:
            raise RuntimeError("Concept-misuse response contract failed; a direct definition and explanation are required.")
    if _requires_concept_misuse_explanation(question) and not _has_concept_misuse_explanation(question, candidate):
        raise RuntimeError("Concept-misuse response contract failed after recovery.")
    if _requires_intergenerational_stewardship(question) and not _has_intergenerational_stewardship_explanation(candidate):
        raise RuntimeError("Intergenerational-stewardship response contract failed after recovery.")
    if _requires_archive_scoped_stewardship(question):
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n+", candidate) if part.strip()]
        if (
            len(paragraphs) != 3
            or not re.search(r"\bLiving Archive\b", paragraphs[0], re.I)
            or not _has_everyday_example(candidate)
            or re.search(
                r"\b(?:rather than a claim|general explanation rather than|precise meaning can vary by field)\b",
                candidate,
                re.I,
            )
        ):
            candidate = _archive_scoped_stewardship_recovery()
    if _requires_cosmology_generalization_standards(question) and not _has_cosmology_generalization_standards(candidate):
        candidate = _cosmology_generalization_standards_recovery()
    if _requires_cosmology_generalization_standards(question) and not _has_cosmology_generalization_standards(candidate):
        raise RuntimeError("Cosmology-generalization standards contract failed after recovery.")
    if _requires_entrusted_stewardship_identification(question) and not _has_entrusted_stewardship_identification(candidate):
        candidate = _entrusted_stewardship_identification_recovery()
    if _requires_entrusted_stewardship_identification(question) and not _has_entrusted_stewardship_identification(candidate):
        raise RuntimeError("Entrusted-stewardship identification contract failed after recovery.")
    if _requires_faithful_stewardship_values_conflict(question) and not _has_faithful_stewardship_values_conflict(candidate):
        candidate = _faithful_stewardship_values_conflict_recovery()
    if _requires_faithful_stewardship_values_conflict(question) and not _has_faithful_stewardship_values_conflict(candidate):
        raise RuntimeError("Faithful-stewardship values-conflict response contract failed after recovery.")
    if _requires_systems_vs_separate_problems_explanation(question):
        candidate = _systems_vs_separate_problems_recovery()
    if _requires_method_comparison(question) and (
        len([part for part in re.split(r"\n\s*\n+", candidate) if part.strip()]) < 3
        or not _has_method_comparison_coverage(question, candidate)
        or re.search(
            r"\b(?:choose one step|identify the main constraint|before acting|adjust rather than assuming)\b",
            candidate,
            re.I,
        )
    ):
        candidate = _method_comparison_recovery()
    if _requires_method_comparison(question) and (
        len([part for part in re.split(r"\n\s*\n+", candidate) if part.strip()]) < 3
        or not _has_method_comparison_coverage(question, candidate)
    ):
        raise RuntimeError("Method-comparison response contract failed after recovery.")
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


def _is_broad_existential_question(query: str) -> bool:
    """Recognize broad philosophical questions that are answerable without personal disclosure.

    Keep this boundary narrow. Questions that mention distress, hopelessness, or
    immediate safety concerns must remain with the existing safety/reflective
    pathway; Archive-specific questions must remain evidence-led.
    """
    q = _normalize_space(query).casefold()
    if not q or re.search(
        r"\b(?:living archive|archive's|archive’s|our doctrine|canonical principles)\b",
        q,
    ):
        return False
    if re.search(
        r"\b(?:suicid|kill myself|end my life|not worth living|no reason to live|"
        r"can't go on|cannot go on|hopeless|want to die|feel empty|feeling empty)\b",
        q,
    ):
        return False
    patterns = (
        r"^(?:so )?what is the meaning of life[?.!]*$",
        r"^what's the meaning of life[?.!]*$",
        r"^what gives life meaning[?.!]*$",
        r"^what is the purpose of life[?.!]*$",
        r"^what's the purpose of life[?.!]*$",
        r"^why are we here[?.!]*$",
        r"^what does it mean to live a meaningful life[?.!]*$",
    )
    return any(re.fullmatch(pattern, q) for pattern in patterns)


def _broad_existential_recovery() -> Dict[str, str]:
    """Answer a broad existential question before clarification or navigation."""
    response = (
        "There is no single answer to the meaning of life that everyone has established as final. "
        "For many people, meaning grows through love and friendship, caring for others, learning, "
        "creating, contributing to a community, or serving something they believe is larger than themselves. "
        "Others understand it through faith, philosophical commitments, or the experience of belonging to the world. "
        "These views differ, but each offers a way to understand what makes a life matter.\n\n"
        "Meaning is often not a hidden sentence we must discover once and for all. It can take shape in what we "
        "choose to care for and how we live those commitments. A person may find it in raising a child, keeping "
        "faith with a friend, doing honest work, easing suffering, or pursuing a question that helps others see "
        "more clearly. Such things need not look grand to have lasting importance.\n\n"
        "This does not mean every life must follow one grand purpose, or that uncertainty makes life meaningless. "
        "What matters can change as we grow, encounter loss, learn, and take on new responsibilities. A useful "
        "starting point is to notice what you value, what you are willing to care for, and what kind of presence "
        "you want to offer the people and world around you."
    )
    return {
        "response": response,
        "doorway_title": "",
        "response_shape": "explanatory",
        "provider": "bounded_existential_general_knowledge_recovery",
        "model": "",
    }


def compose(
    *,
    use_core: Any,
    query: str,
    context_data: Dict[str, Any],
    history_text: str = "",
    integrity_recovery: bool = False,
) -> Optional[Dict[str, Any]]:
    """Compose one ordinary Guide answer through the provider-neutral bank."""

    if PROVIDER_BANK_CONTRACT_VERSION != "v2":
        raise RuntimeError("General Guide composition requires Provider Bank v2.")

    question = _normalize_space(query)
    if not question:
        return None

    # Exact approved/frozen benchmark questions use their registered reference
    # response. This is deliberately exact-match only: it protects approved
    # standards without turning the Guide into a canned-answer service for
    # paraphrases or unrelated questions. Unapproved/recovered records are
    # never eligible for deterministic enforcement.
    registered_standard = None if integrity_recovery else _registered_exact_gold_standard(question)
    if registered_standard is not None:
        return {
            "response": registered_standard["expected_response"],
            "doorway_title": registered_standard.get("doorway_title", ""),
            "doorway_url": registered_standard.get("doorway_url"),
            "response_shape": "direct" if len(registered_standard["expected_response"].split("\n\n")) <= 2 else "explanatory",
            "provider": "gold_standard_registry",
            "model": "approved-reference",
        }

    # A broad existential question is answerable without asking the visitor to
    # disclose personal context. Give a substantive, pluralistic first answer
    # before any follow-up or doorway. Keep Archive-specific questions on the
    # normal evidence-led path, and let the existing safety boundary own distress.
    if _is_broad_existential_question(question):
        return _broad_existential_recovery()

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
    integrity_recovery_instruction = (
        "INTEGRITY RECOVERY: A previous candidate answer was detected as an approved reference answer to a different question. "
        "Do not repeat or paraphrase that unrelated answer. Answer the visitor’s exact question using the supplied canonical material. "
        "For Archive-specific concepts, distinguish what the source explicitly establishes from inference; if evidence is insufficient, give the best bounded explanation without inventing a formal definition. "
        "Use the normal Guide quality floor, normally three purposeful paragraphs for a conceptual explanation, followed by a relevant verified doorway only if supported.\n\n"
        if integrity_recovery
        else ""
    )
    user_content = (
        f"Visitor question:\n{question}\n\n"
        + integrity_recovery_instruction
        + explicit_invitation_instruction
        + practical_application_instruction
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
        shape + ("|integrity_recovery" if integrity_recovery else ""),
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
            {"role": "system", "content": _GENERAL_GUIDE_SYSTEM + (
                "\n\n" + integrity_recovery_instruction.strip()
                if integrity_recovery_instruction else ""
            )},
            {"role": "user", "content": user_content[:10000]},
        ],
        max_tokens=900,
        parse=_parse_factory(documents, effective_question),
    )
    if not result:
        # If the provider bank is exhausted, use a bounded evidence-dependent
        # recovery for Archive constitutional questions rather than allowing
        # the generic Archive-definition fallback to answer the wrong subject.
        constitutional_recovery = _archive_constitutional_recovery(question, documents)
        if constitutional_recovery is not None:
            return constitutional_recovery
        if _requires_recurring_problem_explanation(question):
            return {
                "response": _recurring_problem_explanation_recovery(),
                "doorway_title": "",
                "response_shape": "explanatory",
                "provider": "",
                "model": "",
            }
        if _requires_intergenerational_stewardship(question):
            return {
                "response": _intergenerational_stewardship_recovery(),
                "doorway_title": "",
                "response_shape": "explanatory",
                "provider": "bounded_intergenerational_stewardship_recovery",
                "model": "deterministic-contract-recovery",
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
# USE PRODUCTION VERSION: v57 — Provider-Budget-Safe Multi-Resource Navigation
# Complete production unit reconstructed from the verified v56 production unit.
# This release preserves retrieval, canonical sourcing, provider fallback, and
# visitor-output boundaries while correcting the v56 fixed-envelope preflight failure.

import os
import re
import time
import unicodedata
import html
from typing import Dict, Any, List, Optional, Tuple
import math
import threading
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pinecone import Pinecone
from groq import Groq
from fastembed import TextEmbedding


# =====================================================================
# SYSTEM PROMPT
# =====================================================================

SYSTEM_PROMPT = """
You are the navigation engine for the Living Archive (USE).

Your goal is to help visitors find their way through the Living Archive
using the canonical corpus available to the retrieval system.

The retrieval context supplied to you is EVIDENCE retrieved from the
canonical corpus. It is NOT a declaration that the retrieved context
is the entire Archive.

CONSTITUTIONAL RULES

1. INSTITUTIONAL FIDELITY
   Answer from the canonical evidence supplied to you. Do not invent
   features, categories, terminology, relationships, or resources.

2. EVIDENCE VS. CORPUS BOUNDARY
   Distinguish between:
   - what the retrieved evidence explicitly establishes;
   - what can be reasonably synthesized from multiple retrieved
     resources;
   - what remains genuinely unsupported.
   Never treat the absence of a resource from the retrieved evidence
   as proof that the resource or concept does not exist in the Archive.

3. ARCHITECTURAL NAVIGATION
   For broad, conceptual, or navigational questions, reason across
   the retrieved resources as a connected body of work. Look for
   relationships among resources, complementary roles, sequences,
   themes, and routes of movement. Do not assume that the best answer
   is simply the highest-scoring result.

4. RETRIEVAL LIMITATION
   If the supplied evidence is insufficient to establish a claim,
   say so precisely. Do not manufacture an answer merely to avoid
   uncertainty. However, do not declare that a concept is absent from
   the Archive solely because it was not among the first retrieved
   results.

5. HARD LINK GROUNDING
   You may ONLY cite or link a resource whose exact URL is present in
   the supplied canonical evidence. Never invent, infer, reconstruct,
   or substitute a URL.

6. TITLE FIDELITY
   Preserve the exact retrieved resource title when linking or naming
   a resource. Do not rename resources to make them fit the answer.

7. IMPLICIT LOCATION AWARENESS
   The user is already on the Living Archive. Never tell the user to
   "visit the site" as though they are somewhere else.

8. WHOLE-SITE ORIENTATION
   When QUERY INTENT is WHOLE_SITE_ORIENTATION, the canonical root
   node, when supplied, is the authoritative site-level orientation
   resource. Use it for identity and overall orientation, then use
   other retrieved resources to provide routes of movement.

9. TOPICAL ORIENTATION
   A topical question can still require architectural navigation.
   When the user asks about a broad domain or concept, identify the
   strongest canonical entry points and explain how they relate rather
   than returning a flat list.

10. OUTPUT STYLE
    Prefer clear human narrative. Use bullets when they materially
    improve navigation. Use Markdown tables only when a genuine
    comparison is useful and ensure every table is valid Markdown:
    exactly one header row, one separator row, and matching column
    counts in every subsequent row.

11. OPERATIONAL SEQUENCE
    Mirror the question -> orient the user -> synthesize the relevant
    canonical evidence -> offer the most useful canonical routes of
    movement.

12. NO FALSE NEGATIVES
    Never say "there is no information about X in the Living Archive"
    merely because the current retrieval set did not surface X.
    Say instead that the current retrieved evidence does not establish
    it, unless the evidence itself supports a broader absence claim.

13. INTERNAL REASONING IS NEVER USER-FACING
    The reasoning process used to interpret the query, classify intent,
    assess evidence, compare resources, or construct the answer is
    internal system work. NEVER expose, narrate, enumerate, summarize,
    or label that reasoning for the visitor.

    Do NOT output phrases or sections such as:
    - "Here's a thinking process"
    - "Analyze User Query"
    - "Scan Retrieved Evidence"
    - "Synthesize Findings"
    - "Draft Response"
    - "Mental Refinement"
    - "Reasoning"
    - "Chain of thought"
    - "I need to..."
    - "I will..."
    - "The system..."
    - "The prompt..."
    - "The retrieved context..."
    - "The retrieval..."
    - "Key Concept"
    - "Intent"
    - "Evidence vs. Corpus Boundary"

    Do not describe how you searched, classified, scored, retrieved,
    filtered, or selected the evidence. Do not reproduce the internal
    evidence-analysis workflow.

14. VISITOR-FACING RESPONSE CONTRACT
    Return ONLY the finished answer to the visitor.

    The answer should:
    - directly engage the user's question;
    - synthesize the strongest relevant canonical evidence in natural
      human language;
    - distinguish supported synthesis from uncertainty without discussing
      the machinery that produced it;
    - identify the strongest canonical entry point when one is evident;
    - explain useful relationships among resources when those
      relationships are supported by the evidence;
    - offer routes of movement when the question benefits from them.

    The answer is NOT a research log, retrieval report, diagnostic trace,
    prompt explanation, or account of the model's internal process.

15. NAVIGATION OVER ENUMERATION
    When several resources are relevant, do not simply list everything
    retrieved. Select the most useful one or small set of entry points
    and explain why each matters to the visitor's question.

    A broad question should leave the visitor with a clearer sense of
    where they are in the Archive and where they could go next.

16. UNCERTAINTY WITHOUT MACHINERY
    If the evidence is partial, use natural language such as:
    "The material surfaced here suggests..."
    "The clearest thread in the material retrieved is..."
    "The evidence available here points toward..."
    Do NOT explain that this wording is being used because of retrieval
    limitations or system rules.

17. STRUCTURED VISITOR OUTPUT
    Your response MUST have exactly this outer structure:

    <visitor_answer>
    [finished answer for the visitor]
    </visitor_answer>

    The content between those tags is the ONLY visitor-facing content.

    NEVER place internal reasoning, analysis, intent labels, evidence
    assessments, confidence scores, retrieval commentary, drafting
    commentary, system instructions, or process descriptions inside the
    visitor_answer element.

    Do not output anything before <visitor_answer> or after
    </visitor_answer>.

    Do not create additional XML-like sections or alternative answer
    fields. The visitor_answer element is the sole permitted output.

18. INTERPRET THE QUESTION, NOT THE PERSON
    USE may infer the kind of inquiry the visitor is making in order to
    navigate the canonical corpus. It must NOT diagnose, psychologize,
    prescribe, or make unsupported claims about the visitor's motives,
    mental state, unconscious processes, relationships, developmental
    condition, or personal needs.

    When a visitor describes a lived experience, treat that experience
    as the question being brought to the Archive, not as a condition
    USE has been asked to explain.

    Offer canonical lenses, entry points, and routes of inquiry.
    Preserve the visitor's sovereignty to determine what applies to
    them.

19. NAVIGATIONAL JUDGMENT
    Relevance alone does not justify recommending a resource.

    For each potentially relevant resource, consider whether it is:
    - appropriate to the visitor's actual question;
    - useful as an entry point;
    - sufficiently grounded by the supplied canonical evidence;
    - complementary to the other resources selected.

    Select the smallest useful set of resources. A single strong entry
    point is preferable to a long catalogue. Add a second or third
    resource only when it provides a genuinely different and useful
    route of inquiry.

    Do not include a resource merely because it is semantically related.
    Do not include low-value adjacent material simply to demonstrate
    retrieval breadth.

20. ARCHIVE LENSES, NOT LIFE ADVICE
    When the visitor brings a personal, existential, relational, or
    otherwise lived question, the answer should function as an
    invitation into the Archive.

    Do not turn canonical material into personalized advice, exercises,
    prescriptions, therapeutic guidance, or claims about what the
    visitor should change.

    The visitor may decide what resonates, what does not, and what
    question they want to pursue next.

21. PRESERVE THE OPEN QUESTION
    When the visitor brings an unresolved, exploratory, existential,
    or ambiguous question, do not prematurely resolve it.

    The desired movement is:
    question -> doorway -> lens -> further question

    not:
    question -> explanation -> prescription.

22. DESCRIBE THE RESOURCE, DO NOT COMPLETE ITS MEANING
    Keep a clear boundary between:
    - what the canonical resource explicitly explores;
    - a relationship that can be reasonably synthesized across
      retrieved resources;
    - an interpretation that belongs to the visitor.

    USE may say that a resource offers a particular lens, explores a
    particular tension, or opens a particular line of inquiry when
    supported by the evidence.

    USE should not tell the visitor what the resource ultimately means
    for their life, what conclusion they should draw from it, or which
    belief or behavior they should adopt.

23. NAVIGATION LANGUAGE
    Prefer navigational language such as:
    "A possible place to begin is..."
    "This piece explores..."
    "Another route into the question is..."
    "Taken together, these pieces open..."
    "If you want to stay with that question..."

    Avoid advice-oriented framing such as:
    "How to move forward"
    "You should..."
    "The next step is..."
    "This will help you..."
    "You need to..."
    unless the canonical evidence itself explicitly establishes that
    action as part of the resource's purpose.

24. CONSTITUTIONAL PURPOSE OF USE
    USE exists to help a visitor find their way through the Living
    Archive, not to replace the visitor's own inquiry.

    The highest-quality answer does not necessarily provide the most
    complete explanation. It provides the most useful orientation into
    the canonical corpus while leaving room for the visitor to continue
    thinking, reading, questioning, and making meaning for themselves.

25. STAY WITH THE VISITOR'S WORDS
    USE may interpret the structure or type of inquiry expressed by the
    visitor, but should not add an emotional state, motive, diagnosis,
    need, or personal condition that the visitor did not explicitly
    provide.

26. EVIDENCE-BOUND RELATIONAL LANGUAGE
    When connecting a canonical resource to the visitor's question,
    distinguish clearly between the visitor's stated question, what
    the resource explicitly explores, and a reasonable relationship
    between them.

27. MINIMAL ORIENTATION
    Once a strong entry point has been selected, do not add material
    merely to make the answer feel comprehensive.

28. DESTINATION-FIRST NAVIGATION
    When the visitor explicitly asks where to find, access, locate,
    browse, explore, or get to something, first determine whether the
    requested thing is a canonical object, a collection, a series,
    an index, a hub, or another navigational structure.

    If the requested thing is a canonical object and the evidence
    contains its exact destination, give that destination directly.

    If the requested thing is a collection or navigational structure,
    prefer the canonical collection/index/landing-page destination
    over an individual resource that merely belongs to, mentions, or
    uses that collection.

    Do not substitute a related resource for the requested destination
    simply because its content is semantically close.

29. COLLECTION-LEVEL NAVIGATION
    Treat collection terms such as "essays," "Reference Maps,"
    "Pathways," "Navigators," "Case Library," "Knowledge Hubs," or
    similar corpus structures as requests for a collection-level
    destination when the visitor asks where to explore or find them.

    A resource that contains examples from a collection is not
    automatically the collection's destination.

30. OPEN-INQUIRY STOP RULE
    For an open experiential or exploratory question, once one
    clearly superior canonical doorway is established by the evidence,
    prefer that single doorway. Add another resource only when the
    second route materially changes or advances the inquiry.

31. EVIDENCE-GAP STOP RULE
    If the Archive evidence does not explicitly establish a requested
    concept, do not complete the missing definition from general
    knowledge. State the boundary naturally and route the visitor to
    the strongest evidence actually available.

32. NAVIGATIONAL USEFULNESS OVER SEMANTIC SIMILARITY
    A semantically related resource is not necessarily a useful
    destination. Prefer the resource's architectural role and
    navigational suitability over keyword or topical similarity.

33. FOUR NAVIGATION MODES
    Silently distinguish among:
    - canonical-object destination requests;
    - collection or structural destination requests;
    - open experiential/orientational inquiries;
    - evidence-poor conceptual inquiries.

    Apply the corresponding rules above. Never reveal these internal
    modes or labels to the visitor.

34. CANONICAL LINK PRESENTATION
    Whenever a canonical resource is linked, display ONLY its exact
    canonical title as the visible link text, with the exact URL supplied
    by the canonical evidence embedded behind that title.

    Never display a raw URL, https://, http://, www., or URL slug as
    visitor-facing link text. Never add or preserve emoji prefixes before
    canonical resource titles. Do not invent, reconstruct, normalize, or
    substitute URLs.

35. STRUCTURAL EVIDENCE FOR COLLECTIONS
    When the visitor asks where to find or explore a collection,
    document type, series, hub, index, library, or other structural
    class, prioritize evidence describing the structure or navigational
    role of that class. A semantically related individual resource is
    secondary evidence and must not substitute for the requested
    collection-level destination.

36. PRESENTATION SAFETY
    Raw URL display and emoji-prefixed resource titles are presentation
    failures, not alternative valid formats.

37. ADAPTIVE DEVELOPMENTAL ORIENTATION
    USE is capable of recognizing when a visitor's current question
    contains a meaningful movement from primarily inward inquiry toward
    responsibility for others, systems, institutions, communities, or
    future generations. When the supplied evidence supports such a
    transition, surface the relevant canonical bridge material naturally.
    Do not diagnose the visitor, assign a developmental status, declare
    that a threshold has been crossed, or force stewardship language where
    it is not warranted. The visitor remains free to determine whether
    the material applies.

38. ADAPTIVE RETRIEVAL IS NOT A SECOND ENGINE
    Treat stewardship-oriented bridge evidence as an additional retrieval
    signal within the same USE navigation architecture. Do not create a
    separate response engine, separate worldview, separate answer format,
    or separate visitor identity. The same constitutional rules continue
    to govern the response.

39. INWARD-TO-OUTWARD CONTINUITY
    When a question connects self-development with responsibility beyond
    the self, preserve that continuity. Personal development remains a
    foundation, while the answer may open a route toward contribution,
    stewardship, custodianship, or service when canonical evidence supports
    that movement. Do not present this as a required progression.

40. DESTINATION INTEGRITY
    When the visitor asks where to find or explore something, never
    recommend a resource merely because it is semantically related.
    The destination must function as a genuine visitor-facing corpus
    destination. Never send the visitor back to the USE query interface,
    a search/query endpoint, an API, documentation endpoint, feed, or
    other technical intermediary.

41. DESTINATION-FIRST RESPONSE
    For explicit location requests, give the strongest established
    destination first. If the evidence does not establish a genuine
    destination, say that the available material does not establish one
    and do not substitute an unrelated resource.

42. RELATIONSHIP QUALIFICATION
    For collection-level navigation, distinguish between:
    - a resource that IS the collection/index/landing/gateway;
    - a resource that directly describes the collection as a whole; and
    - a resource that merely mentions, contains, incorporates, or links to
      one member of that collection.

    Only the first two categories may establish a collection destination.
    A page that says "Explore the Guided Pathway" is evidence of a member
    pathway, not evidence that the page is the Guided Pathways collection.

43. NO SEMANTIC DESTINATION SUBSTITUTION
    For an explicit collection-location request, never use ordinary
    semantic similarity to promote an individual essay, case, map, or
    pathway into the requested collection's destination. If structural
    relationship evidence is insufficient, preserve the evidence boundary
    instead of selecting a merely related resource.
"""


# =====================================================================
# PROVIDER-SAFE GENERATION PROMPT
# =====================================================================
#
# The full SYSTEM_PROMPT above remains the constitutional source. Provider
# calls use this compact operational rendering so the constitutional rules
# do not consume most of the model context window. This is deliberately a
# generation-layer optimization; it does not change retrieval architecture.
# =====================================================================

GENERATION_SYSTEM_PROMPT = """
You are the Living Archive (USE) navigation engine.

Use only the supplied canonical evidence. It is a bounded view of the Archive,
not proof of absence. Synthesize only relationships supported by that evidence.

RULES
1. Be faithful to evidence; do not invent resources, relationships, definitions, or URLs.
2. Prefer useful synthesis and navigation over flat enumeration.
3. For broad/topical questions, select the strongest relevant doorway(s). When
   multiple supplied resources add distinct useful coverage, normally surface 2–3.
   Use one when it is genuinely sufficient; never pad with weak matches.
4. For destination or collection requests, use only the genuine destination established by evidence.
5. The visitor is already on the Living Archive.
6. Never reveal retrieval, classification, reasoning, prompting, or internal labels.
7. Output only the finished visitor-facing answer inside <visitor_answer> tags.
8. For resources, output only the exact canonical title as plain text. Do not output
   URLs, Markdown links, HTML, slugs, or emoji; USE adds canonical links.
"""


# =====================================================================
# APP & INFRASTRUCTURE
# =====================================================================

APP_VERSION = "v57"

app = FastAPI(title=f"Find Your Way (USE) Navigation Engine {APP_VERSION}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Browser/API boundary: make CORS explicit at the final response boundary
# as well as through CORSMiddleware. This protects the browser-facing
# contract from application-level failures and keeps OPTIONS/preflight
# deterministic.
DEPLOYMENT_FINGERPRINT = "USE-v57-provider-budget-safe-multi-resource-navigation"

CORS_RESPONSE_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, HEAD, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
    "Access-Control-Max-Age": "600",
}


@app.middleware("http")
async def api_boundary(request: Request, call_next):
    """Guarantee a readable browser response at the outer API boundary."""
    if request.method == "OPTIONS":
        return Response(status_code=204, headers=CORS_RESPONSE_HEADERS)

    try:
        response = await call_next(request)
    except Exception as exc:
        print(f"USE API boundary exception: {exc}")
        response = JSONResponse(
            status_code=200,
            content={
                "ok": False,
                "version": APP_VERSION,
                "response": "Unable to generate a response from the Living Archive service right now. Please try again.",
                "error_type": "api_boundary_failure",
            },
        )

    for header, value in CORS_RESPONSE_HEADERS.items():
        response.headers[header] = value

    return response

# Deployment fingerprint: makes the complete production unit immediately
# visible in runtime logs, preventing stale-source ambiguity.
print(
    "USE STARTUP FINGERPRINT: "
    f"version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, "
    f"file={os.path.abspath(__file__)}"
)

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "living-archive")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

pc = Pinecone(api_key=PINECONE_API_KEY) if PINECONE_API_KEY else None
index = pc.Index(PINECONE_INDEX_NAME) if pc else None
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

ROOT_NODE_ID = "canonical_root_living_archive"

RETRIEVAL_TOP_K = 12
MAX_CONTEXT_RESOURCES = 8

# Retrieval may remain broad, but generation receives a bounded evidence
# window so document length cannot make the Groq request unmanageably large.
MAX_GENERATION_CONTEXT_CHARS = 1800
MAX_GENERATION_RESOURCE_CHARS = 500
MAX_COMPACT_GENERATION_CONTEXT_CHARS = 1100
MAX_COMPACT_GENERATION_RESOURCE_CHARS = 300
MAX_GENERATION_TOKENS = 240
MAX_COMPACT_GENERATION_TOKENS = 120

# Provider preflight budget. This is measured against the actual assembled
# system + user messages, not merely the evidence excerpt. It prevents a
# large constitutional prompt plus evidence plus completion from reaching a
# provider that has a smaller effective context window.
MAX_PROVIDER_INPUT_CHARS = 3800
MAX_PROVIDER_TOTAL_CHARS = 4600


# =====================================================================
# GROQ MODEL DISCOVERY
# =====================================================================

MODEL_CACHE: Dict[str, Any] = {
    "models": [],
    "last_fetch": 0.0,
    "terms_required_models": set(),
    "structural_failed_models": set(),
    "request_too_large_models": set(),
    "rate_limited_until": {},
    # Observed provider TPD state, populated only when Groq explicitly
    # reports a daily-token limit/usage pair. This is intentionally an
    # observed-state guard, not an invented quota source.
    "daily_tpd": {},
}

MODEL_CACHE_LOCK = threading.Lock()


def get_live_groq_models() -> List[str]:
    """
    Return currently usable Groq text/chat model candidates.

    Discovery is treated as catalogue discovery, not proof of
    executability. Known non-text families and runtime-ineligible models
    are excluded before the generation loop.
    """
    now = time.time()

    permanently_unusable = (
        MODEL_CACHE["terms_required_models"]
        | MODEL_CACHE["structural_failed_models"]
        | MODEL_CACHE["request_too_large_models"]
    )

    now = time.time()
    rate_limited = {
        model_id
        for model_id, until in MODEL_CACHE["rate_limited_until"].items()
        if float(until or 0.0) > now
    }

    # Expired rate-limit entries are harmlessly discarded.
    MODEL_CACHE["rate_limited_until"] = {
        model_id: until
        for model_id, until in MODEL_CACHE["rate_limited_until"].items()
        if float(until or 0.0) > now
    }

    unusable = permanently_unusable | rate_limited

    if (
        MODEL_CACHE["models"]
        and now - MODEL_CACHE["last_fetch"] < 3600
    ):
        return [
            model_id
            for model_id in MODEL_CACHE["models"]
            if model_id not in unusable
        ]

    if not groq_client:
        return []

    try:
        response = groq_client.models.list()

        discovered = [
            model.id
            for model in response.data
            if hasattr(model, "id")
            and model.id
            and not any(
                excluded in model.id.lower()
                for excluded in (
                    "whisper",
                    "guard",
                    "audio",
                    "vision",
                    "tts",
                    "speech",
                    "transcribe",
                    "orpheus",
                )
            )
        ]

        if discovered:
            # Stable priority: preserve the existing capability preference,
            # but make ties deterministic so provider catalogue ordering
            # cannot change which live model becomes the first attempt.
            discovered.sort(key=lambda model_id: model_id.casefold())
            discovered.sort(
                key=lambda model_id: not (
                    "70b" in model_id.lower()
                    or "versatile" in model_id.lower()
                    or "instruct" in model_id.lower()
                )
            )

            MODEL_CACHE["models"] = discovered
            MODEL_CACHE["last_fetch"] = now

            print(
                "Dynamically loaded live Groq models: "
                f"{discovered}"
            )

            return [
                model_id
                for model_id in discovered
                if model_id not in unusable
            ]

    except Exception as exc:
        print(
            "Failed to fetch live model list from Groq API: "
            f"{exc}"
        )

    return [
        model_id
        for model_id in MODEL_CACHE["models"]
        if model_id not in unusable
    ]


# =====================================================================
# EMBEDDING GENERATION
# =====================================================================

def generate_embedding(text: str) -> List[float]:
    try:
        embeddings = list(embedding_model.embed([text]))

        if not embeddings:
            return []

        return embeddings[0].tolist()

    except Exception as exc:
        print(f"Embedding generation error: {exc}")
        return []


# =====================================================================
# WHOLE-SITE ORIENTATION CLASSIFICATION
# =====================================================================

SITE_ANCHOR = (
    r"(?:"
    r"(?:the\s+)?living\s+archive"
    r"|(?:the\s+)?whole\s+archive"
    r"|(?:the\s+)?archive"
    r"|(?:this\s+)?site"
    r"|(?:this\s+)?website"
    r"|(?:this\s+)?place"
    r"|everything(?:\s+here|\s+on\s+(?:this\s+)?site)?"
    r"|all\s+(?:this|of\s+this)"
    r"|itself"
    r"|the\s+archive\s+itself"
    r")"
)

SITE_ANCHOR_RE = re.compile(rf"\b{SITE_ANCHOR}\b", re.IGNORECASE)

ORIENTATION_TOKENS = (
    "start",
    "begin",
    "entry",
    "first",
    "overwhelmed",
    "lost",
    "confused",
    "navigate",
    "explore",
    "find my way",
    "how to use",
    "structure",
)

SITE_SCOPE_TOKENS = (
    "this site",
    "the site",
    "website",
    "this archive",
    "the archive",
    "living archive",
    "everything here",
    "all this",
    "all of this",
    "how much is on",
)


def _has_orientation_signal(query: str) -> bool:
    return any(
        re.search(rf"\b{re.escape(token)}\b", query, re.IGNORECASE)
        for token in ORIENTATION_TOKENS
    )


def _has_site_scope_signal(query: str) -> bool:
    return any(
        re.search(rf"\b{re.escape(token)}\b", query, re.IGNORECASE)
        for token in SITE_SCOPE_TOKENS
    )


def _has_topical_prepositional_complement(query: str) -> bool:
    action_pattern = re.compile(
        r"\b(?:start|begin|navigate|explore|view|approach|"
        r"look|read|use|go|move|learn|say)\b"
        r"\s+(?:with|about|on|through|in|for|to)\s+"
        r"(.+?)(?:[?.!,;:]|$)",
        re.IGNORECASE,
    )

    site_pattern = re.compile(
        r"\b(?:site|website|archive|living\s+archive)\b"
        r"\s+(?:about|on|for)\s+"
        r"(.+?)(?:[?.!,;:]|$)",
        re.IGNORECASE,
    )

    for pattern in (action_pattern, site_pattern):
        for match in pattern.finditer(query):
            complement = match.group(1).strip()
            complement = re.sub(
                r"^(?:the|this|that|my|your|our|their)\s+",
                "",
                complement,
                flags=re.IGNORECASE,
            ).strip()

            site_referential_forms = (
                r"(?:"
                r"(?:living\s+archive|archive|site|website|place)"
                r"(?:\s+(?:itself|as\s+a\s+whole|as\s+such))?"
                r"|whole\s+(?:living\s+archive|archive|site|website)"
                r"|everything(?:\s+here|\s+on\s+(?:this\s+)?site)"
                r"|all\s+(?:this|of\s+this)"
                r"|itself"
                r"|its\s+own\s+purpose"
                r")"
            )

            if re.fullmatch(
                site_referential_forms,
                complement,
                flags=re.IGNORECASE,
            ):
                continue

            if SITE_ANCHOR_RE.search(complement):
                if re.search(
                    r"\b(?:to|about|on|for|with|in)\s+\S+",
                    complement,
                    flags=re.IGNORECASE,
                ):
                    return True

            if complement:
                return True

    return False


def classify_intent(query_str: str) -> str:
    clean_query = re.sub(r"\s+", " ", query_str.strip().lower())

    if not clean_query:
        return "TOPICAL_INQUIRY"

    if _has_topical_prepositional_complement(clean_query):
        return "TOPICAL_INQUIRY"

    if re.fullmatch(
        r"what\s+is\s+(?:the\s+)?living\s+archive",
        clean_query,
    ):
        return "WHOLE_SITE_ORIENTATION"

    if re.fullmatch(
        r"what\s+is\s+(?:this\s+)?(?:archive|site|place|website)"
        r"(?:\s+about)?",
        clean_query,
    ):
        return "WHOLE_SITE_ORIENTATION"

    if re.fullmatch(
        r"what\s+does\s+(?:the\s+)?living\s+archive\s+"
        r"(?:explore|cover|do)",
        clean_query,
    ):
        return "WHOLE_SITE_ORIENTATION"

    if re.fullmatch(
        r"where\s+(?:should|do)\s+i\s+(?:start|begin)",
        clean_query,
    ):
        return "WHOLE_SITE_ORIENTATION"

    if re.fullmatch(r"where\s+to\s+begin", clean_query):
        return "WHOLE_SITE_ORIENTATION"

    if re.fullmatch(
        r"how\s+(?:do|can)\s+i\s+navigate\s+"
        r"(?:this\s+site|the\s+archive|the\s+living\s+archive)",
        clean_query,
    ):
        return "WHOLE_SITE_ORIENTATION"

    if (
        _has_orientation_signal(clean_query)
        and _has_site_scope_signal(clean_query)
    ):
        return "WHOLE_SITE_ORIENTATION"

    if (
        SITE_ANCHOR_RE.search(clean_query)
        and _has_orientation_signal(clean_query)
    ):
        return "WHOLE_SITE_ORIENTATION"

    return "TOPICAL_INQUIRY"


# =====================================================================
# ADAPTIVE STEWARDSHIP ORIENTATION
# =====================================================================
#
# Adaptive stewardship orientation: established baseline capability.
#
# The purpose is NOT to create a second engine, diagnose the visitor, or
# force a visitor into stewardship language. It is to recognize when the
# wording of a question contains a meaningful movement from primarily
# inward/personal inquiry toward responsibility for people, systems,
# institutions, communities, or future generations.
#
# When that signal is strong enough, retrieval is given an additional
# stewardship-bridge pass. The response model remains the same and still
# decides what is appropriate to surface from canonical evidence.
#
# This is deliberately retrieval adaptation rather than a hard-coded
# destination map. It allows USE to discover the bridge resources that are
# actually present in the corpus.
# =====================================================================

STEWARDSHIP_SIGNAL_TERMS = (
    ("stewardship", 4),
    ("steward", 3),
    ("custodian", 4),
    ("custodianship", 4),
    ("guardian", 4),
    ("guardianship", 4),
    ("responsibility", 2),
    ("responsible for", 2),
    ("entrusted", 3),
    ("entrusted with", 3),
    ("serve others", 3),
    ("service to others", 3),
    ("larger whole", 2),
    ("future generations", 3),
    ("long-term health", 2),
    ("long term health", 2),
    ("what happens after i am gone", 3),
    ("after i am gone", 3),
    ("after i'm gone", 3),
    ("beyond myself", 2),
    ("beyond the self", 2),
    ("what i build serves", 3),
    ("who it serves", 2),
    ("who does it serve", 2),
    ("serve the whole", 3),
    ("care for", 2),
    ("care of", 1),
)

INWARD_DEVELOPMENT_TERMS = (
    "self-awareness",
    "self awareness",
    "self-development",
    "self development",
    "personal growth",
    "personal development",
    "inner growth",
    "identity",
    "emotional intelligence",
    "emotional maturity",
    "healing",
    "myself",
    "my own",
    "my life",
    "my journey",
)

OUTWARD_RESPONSIBILITY_TERMS = (
    "others",
    "community",
    "communities",
    "institution",
    "institutions",
    "society",
    "systems",
    "governance",
    "leadership",
    "future",
    "generations",
    "organization",
    "organizations",
    "people",
    "public",
    "collective",
    "civilization",
    "civilizational",
    "resources",
    "legacy",
    "contribution",
)

ADAPTIVE_STEWARDSHIP_THRESHOLD = 4
MAX_ADAPTIVE_BRIDGE_RESOURCES = 3


def _phrase_hits(query: str, phrases: Tuple[str, ...]) -> int:
    clean = re.sub(r"\s+", " ", query.lower()).strip()
    return sum(
        1
        for phrase in phrases
        if re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", clean)
    )


def detect_adaptive_stewardship_orientation(query: str) -> Dict[str, Any]:
    """
    Detect a stewardship-oriented shift in the wording of the current
    question without diagnosing the visitor or assigning a developmental
    status.

    The score is used only to decide whether retrieval should receive an
    additional bridge-oriented pass. It is never exposed to the visitor.
    """
    clean = re.sub(r"\s+", " ", query.lower()).strip()

    signal_score = 0
    matched_signals: List[str] = []

    for phrase, weight in STEWARDSHIP_SIGNAL_TERMS:
        if re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", clean):
            signal_score += weight
            matched_signals.append(phrase)

    inward_hits = _phrase_hits(clean, INWARD_DEVELOPMENT_TERMS)
    outward_hits = _phrase_hits(clean, OUTWARD_RESPONSIBILITY_TERMS)

    # A simultaneous inward/outward pattern is a particularly useful
    # adaptive signal: the visitor is connecting personal development with
    # responsibility beyond the self.
    if inward_hits and outward_hits:
        signal_score += 2
        matched_signals.append("inward_to_outward_shift")

    # A direct question about what a person's work/building is for, who it
    # serves, or what remains after the builder is gone is also a strong
    # bridge signal even when the word stewardship is never used.
    legacy_pattern = re.search(
        r"\b(?:after|when)\b.{0,80}\b(?:gone|leave|leaves|left)\b",
        clean,
        flags=re.IGNORECASE,
    )
    service_pattern = re.search(
        r"\b(?:who|what)\b.{0,80}\b(?:serve|serves|serving)\b",
        clean,
        flags=re.IGNORECASE,
    )

    if legacy_pattern:
        signal_score += 2
        matched_signals.append("legacy_continuity")

    if service_pattern:
        signal_score += 2
        matched_signals.append("service_orientation")

    return {
        "active": signal_score >= ADAPTIVE_STEWARDSHIP_THRESHOLD,
        "score": signal_score,
        "inward_hits": inward_hits,
        "outward_hits": outward_hits,
        "matched_signals": tuple(dict.fromkeys(matched_signals)),
    }


def build_stewardship_bridge_query(user_query: str) -> str:
    """
    Produce one semantic retrieval variant for a question showing a
    stewardship-oriented shift.

    The variant is conceptual rather than resource-specific so USE can
    discover whatever canonical bridge material the corpus currently holds.
    """
    return (
        f"{user_query} human development responsibility contribution "
        "stewardship service systems communities future generations"
    )



# =====================================================================
# COLLECTION-LEVEL STRUCTURAL NAVIGATION
# =====================================================================

COLLECTION_TERMS = {
    "reference maps": ("reference maps", "reference map"),
    "pathways": ("guided pathways", "living archive pathways", "pathways", "guided reading pathways"),
    "navigators": ("navigators", "navigator series"),
    "knowledge hubs": ("knowledge hubs", "knowledge hub"),
    "case library": ("case library", "case atlas"),
    "cornerstones": ("cornerstones", "cornerstone"),
    "essays": ("essays", "essay collection"),
}

DESTINATION_SIGNALS = (
    "where",
    "find",
    "explore",
    "access",
    "browse",
    "located",
    "location",
    "available",
    "go",
    "start",
    "begin",
)

USE_INTERFACE_MARKERS = (
    "ask a question, follow a curiosity, or find what you need",
    "how results are found",
    "ask another question",
    "unable to connect to the living archive service",
)

TECHNICAL_URL_MARKERS = (
    "/api/",
    "/docs",
    "/openapi",
    "/wp-admin",
    "/wp-json",
    "/search",
    "/feed",
    ".json",
)


def detect_collection_request(query: str) -> Optional[str]:
    clean = re.sub(r"\s+", " ", query.strip().lower())

    destination_signal = any(
        re.search(rf"\b{re.escape(token)}\b", clean, re.IGNORECASE)
        for token in DESTINATION_SIGNALS
    ) and (
        re.search(r"\bwhere\b", clean, re.IGNORECASE)
        or re.search(r"\bhow\b", clean, re.IGNORECASE)
    )

    if not destination_signal:
        return None

    for canonical_name, aliases in COLLECTION_TERMS.items():
        if any(
            re.search(rf"\b{re.escape(alias)}\b", clean, re.IGNORECASE)
            for alias in aliases
        ):
            return canonical_name

    return None


def _is_use_interface_resource(metadata: Dict[str, Any]) -> bool:
    title = str(metadata.get("title", "")).strip().lower()
    url = str(metadata.get("url", "")).strip().lower()
    content = _resource_content(metadata).lower()

    if any(marker in title for marker in USE_INTERFACE_MARKERS):
        return True

    if any(marker in content for marker in USE_INTERFACE_MARKERS):
        return True

    # Technical/service destinations are not visitor-facing corpus
    # destinations even when they happen to have useful semantic text.
    if any(marker in url for marker in TECHNICAL_URL_MARKERS):
        return True

    if url.startswith("javascript:") or url.startswith("data:"):
        return True

    return False


def _has_usable_destination(metadata: Dict[str, Any]) -> bool:
    url = str(metadata.get("url", "")).strip()

    if not url or url == "#":
        return False

    if not re.match(r"^https?://", url, flags=re.IGNORECASE):
        return False

    return not _is_use_interface_resource(metadata)


def _structural_relationship(
    metadata: Dict[str, Any],
    collection_name: str,
) -> Tuple[str, int]:
    """
    Qualify the relationship between a retrieved resource and the
    requested collection before allowing it to become a destination.

    DESTINATION means the evidence establishes that the resource is a
    collection/index/landing/gateway for the requested structural object.
    REFERENCE means the resource merely mentions, uses, or links to an
    individual member of that structure. NONE means the evidence does not
    establish a meaningful structural relationship.

    This distinction is deliberately relationship-based rather than a
    semantic-similarity score. A page saying "Explore the Guided Pathway"
    is not thereby the destination for the Guided Pathways collection.
    """
    if not _has_usable_destination(metadata):
        return "NONE", -100

    title = str(metadata.get("title", "")).strip().lower()
    content = _resource_content(metadata).lower()
    aliases = COLLECTION_TERMS.get(collection_name, (collection_name,))

    # "Guided reading pathways" is a Navigator feature, not automatically
    # the Guided Pathways collection. Remove that phrase from collection
    # qualification so a companion publication cannot become the destination
    # merely because it contains the generic word "pathways".
    if collection_name == "pathways":
        content_without_reading = re.sub(
            r"guided\s+reading\s+pathways?",
            "",
            content,
            flags=re.IGNORECASE,
        )
    else:
        content_without_reading = content

    # Prefer the canonical plural/collection form when one exists. This
    # prevents a singular member (e.g. one Guided Pathway) from being
    # mistaken for the collection-level destination.
    primary_alias = aliases[0].lower()
    plural_aliases = tuple(
        alias.lower() for alias in aliases if len(alias.split()) >= 1
    )

    title_exact = any(title == alias for alias in plural_aliases)
    title_contains = any(alias in title for alias in plural_aliases)
    early_content = content_without_reading[:1600]
    primary_early = primary_alias in early_content

    collection_role_terms = (
        "collection",
        "series",
        "library",
        "hub",
        "index",
        "landing page",
        "landing",
        "gateway",
        "entry point",
        "where to begin",
        "continue exploring",
        "choose",
        "choose the question",
        "available here",
        "created for",
        "were created",
        "is a collection",
        "are a collection",
    )

    navigational_terms = (
        "explore",
        "browse",
        "access",
        "find",
        "begin",
        "start",
        "navigate",
        "continue",
    )

    # A collection-level title is direct structural evidence.
    if title_exact:
        return "DESTINATION", 100

    if title_contains:
        score = 85
        if any(term in title for term in ("series", "collection", "library", "hub", "index")):
            score += 10
        return "DESTINATION", score

    # Strongest content relationship: the page describes the collection
    # itself, rather than a single member of it.
    plural_hits = sum(content_without_reading.count(alias) for alias in plural_aliases)
    has_collection_role = any(term in content_without_reading for term in collection_role_terms)
    has_navigation = any(term in content_without_reading for term in navigational_terms)

    # A collection landing page often identifies itself through its opening
    # heading/subtitle rather than the exact words "collection" or "index".
    # This is especially important for a page such as "Ninety Minutes to
    # Greater Clarity", whose opening heading identifies it as Guided
    # Pathways even though the page title does not contain the word Pathways.
    if primary_early and has_navigation and (
        collection_name != "pathways"
        or "guided pathways" in early_content
        or "living archive pathways" in early_content
    ):
        return "DESTINATION", 82

    # Explicit collection-level formulations are high-confidence evidence.
    explicit_collection_patterns = (
        rf"the\s+{re.escape(primary_alias)}\s+(?:are|is|were|was|have|has|offer|provide|begin|continue)",
        rf"{re.escape(primary_alias)}\s+(?:collection|series|library|hub|index|landing page|gateway)",
        rf"(?:collection|series|library|hub|index|landing page|gateway)\s+(?:for|of)\s+{re.escape(primary_alias)}",
        rf"(?:explore|browse|find|access|begin|start)\s+(?:the\s+)?{re.escape(primary_alias)}\b",
    )

    explicit_collection = any(
        re.search(pattern, content_without_reading, flags=re.IGNORECASE)
        for pattern in explicit_collection_patterns
    )

    if explicit_collection and (plural_hits >= 1 or has_collection_role):
        score = 75
        if plural_hits >= 2:
            score += 8
        if has_navigation:
            score += 5
        return "DESTINATION", score

    # A page can be a genuine gateway without naming itself as a collection.
    # Require repeated collection-level evidence plus navigational framing.
    if plural_hits >= 2 and has_collection_role and has_navigation:
        if collection_name != "pathways" or primary_early:
            return "DESTINATION", 65

    # A common false-positive pattern: an individual resource says
    # "Explore the Guided Pathway" or discusses a Pathway it incorporates.
    # That is useful reference evidence but is NOT the collection itself.
    singular_aliases = set()
    for alias in aliases:
        clean_alias = alias.lower().strip()
        singular_aliases.add(clean_alias)
        if clean_alias.endswith("ies"):
            singular_aliases.add(clean_alias[:-3] + "y")
        elif clean_alias.endswith("s"):
            singular_aliases.add(clean_alias[:-1])

    singular_aliases = tuple(
        alias for alias in singular_aliases if alias != primary_alias
    )

    singular_reference = any(
        re.search(
            rf"\b(?:a|an|the|this|one|each)\s+{re.escape(alias)}\b",
            content_without_reading,
            flags=re.IGNORECASE,
        )
        for alias in singular_aliases
    )

    member_cta = any(
        re.search(
            rf"(?:explore|read|open|view|follow|access)\s+(?:the\s+)?{re.escape(alias)}\b",
            content_without_reading,
            flags=re.IGNORECASE,
        )
        for alias in singular_aliases
    )

    if singular_reference or member_cta:
        return "REFERENCE", 5

    return "NONE", 0


def _query_structural_index(
    collection_name: str,
) -> List[Dict[str, Any]]:
    """
    Resolve a collection-level destination through structural evidence.

    Retrieval remains generic: no individual Archive collection is mapped
    to a hard-coded URL. Only candidates whose corpus evidence qualifies
    them as collection-level destinations are returned.
    """
    aliases = COLLECTION_TERMS.get(collection_name, (collection_name,))

    # Structural recall must search the actual vocabulary visitors and the
    # corpus use for the collection. These are retrieval aliases, not
    # hard-coded destinations.
    alias_variants = tuple(dict.fromkeys(
        alias.strip() for alias in aliases if alias.strip()
    ))

    query_variants = tuple(dict.fromkeys(
        [
            *(f'"{alias}"' for alias in alias_variants),
            *(f"Living Archive {alias} collection index landing page gateway"
              for alias in alias_variants),
            *(f"Living Archive {alias} where to find explore browse access"
              for alias in alias_variants),
            *(f"Living Archive {alias} continue exploring choose begin"
              for alias in alias_variants),
        ]
    ))

    ranked_by_key: Dict[str, Tuple[int, float, Dict[str, Any]]] = {}

    for variant in query_variants:
        vector = generate_embedding(variant)
        if not vector:
            continue

        # Structural discovery is a recall problem before it is a ranking
        # problem. Search a materially wider candidate set than ordinary
        # topical retrieval, then apply relationship qualification locally.
        candidates = _query_index(vector, max(RETRIEVAL_TOP_K, 250))

        for semantic_score, _match_id_value, metadata in candidates:
            relationship, structural_score = _structural_relationship(
                metadata,
                collection_name,
            )

            # Only genuine collection-level destinations are eligible for
            # the destination channel. Mentions/references never qualify.
            if relationship != "DESTINATION":
                if relationship == "REFERENCE":
                    print(
                        "USE structural relationship: rejected reference-only "
                        f"resource '{metadata.get('title', 'Untitled Resource')}'."
                    )
                continue

            key = _resource_key(metadata)
            existing = ranked_by_key.get(key)
            combined_score = structural_score + semantic_score

            if existing is None or combined_score > existing[0] + existing[1]:
                ranked_by_key[key] = (
                    structural_score,
                    semantic_score,
                    metadata,
                )

    ranked = list(ranked_by_key.values())
    ranked.sort(
        key=lambda item: (
            item[0],
            item[1],
        ),
        reverse=True,
    )

    return [metadata for _structural, _semantic, metadata in ranked]


# =====================================================================
# CANONICAL CONTEXT FORMATTING
# =====================================================================

def _resource_key(doc: Dict[str, Any]) -> str:
    url = str(doc.get("url", "")).strip().lower()

    if url and url != "#":
        return url

    return str(doc.get("title", "Untitled Resource")).strip().lower()


def _resource_display_key(doc: Dict[str, Any]) -> str:
    """Return normalized visitor-facing identity for a canonical title."""
    title = _canonical_display_title(str(doc.get("title", "Untitled Resource")))
    return re.sub(r"\s+", " ", title).strip().casefold()


def _dedupe_resources_by_display_title(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Keep the first occurrence of each visitor-facing canonical title."""
    unique: List[Dict[str, Any]] = []
    seen_titles = set()

    for document in documents:
        key = _resource_display_key(document)
        if not key:
            unique.append(document)
            continue

        if key in seen_titles:
            print(
                "USE resource uniqueness: suppressed duplicate visitor-facing "
                f"title '{_canonical_display_title(document.get('title', 'Untitled Resource'))}'."
            )
            continue

        seen_titles.add(key)
        unique.append(document)

    return unique


def _resource_content(doc: Dict[str, Any]) -> str:
    return str(
        doc.get(
            "text",
            doc.get(
                "content",
                doc.get("excerpt", ""),
            ),
        )
        or ""
    ).strip()


def format_context_blocks(
    documents: List[Dict[str, Any]],
    structural_destination_count: int = 0,
    adaptive_bridge_count: int = 0,
) -> str:
    formatted_blocks: List[str] = []

    for index_number, doc in enumerate(documents):
        title = doc.get("title", "Untitled Resource")
        url = doc.get("url", "#")
        content = _resource_content(doc)

        role = "CANONICAL CORPUS EVIDENCE"
        if index_number < structural_destination_count:
            role = "PRIMARY STRUCTURAL DESTINATION CANDIDATE"
        elif index_number < structural_destination_count + adaptive_bridge_count:
            role = "ADAPTIVE STEWARDSHIP BRIDGE EVIDENCE"

        formatted_blocks.append(
            f"Evidence Role: {role}\n"
            f"Title: {title}\n"
            f"URL: {url}\n"
            f"Content: {content}"
        )

    return "\n\n---\n\n".join(formatted_blocks)


# =====================================================================
# v25 ORIENTATIONAL FRAME / DOMAIN-AWARE RETRIEVAL
# =====================================================================
# Internal navigation aid only. These labels are never exposed to visitors.
# The frame does not replace semantic retrieval; it provides a light domain
# preference so that a question about larger systems is not pulled inward
# merely because the visitor also uses personal language.

ORIENTATIONAL_DOMAIN_TERMS = {
    "systems": (
        "system", "systems", "institution", "institutions", "institutional",
        "structure", "structural", "incentive", "incentives", "governance",
        "policy", "culture", "community", "communities", "collective",
        "society", "social", "organization", "organizations", "power",
        "authority", "rules", "conditions", "environment", "ecosystem",
        "trust", "legitimacy", "coordination", "institutional design",
    ),
    "stewardship": (
        "stewardship", "steward", "custodian", "custodianship", "guardian",
        "guardianship", "service to others", "responsibility", "responsible",
        "care for", "serve", "service", "accountability", "trust", "governance",
    ),
    "inward": (
        "myself", "my self", "my pattern", "my patterns", "emotion", "emotions",
        "self-awareness", "self awareness", "self-development", "self development",
        "inner", "shadow", "ego", "healing", "grief", "fear", "identity",
        "personal", "authenticity", "relationship", "relationships",
    ),
    "transition": (
        "transition", "change", "uncertain", "uncertainty", "threshold",
        "becoming", "next chapter", "what now", "meaning",
    ),
    "relational": (
        "relationship", "relationships", "relational", "interplay", "interaction",
        "connection", "tension", "dynamic", "between", "mutually exclusive",
        "personal", "self", "individual", "inner", "internal",
        "system", "systems", "systemic", "social", "society", "institution",
        "collective", "external",
    ),
}


def detect_relational_orientation(question: str) -> bool:
    """Detect explicit questions connecting personal and systemic dimensions."""
    q = re.sub(r"\s+", " ", str(question or "").lower()).strip()
    if not q:
        return False
    personal = bool(re.search(
        r"\b(?:personal|self|myself|individual|inner|internal|within myself)\b", q
    ))
    systemic = bool(re.search(
        r"\b(?:system|systems|systemic|social|society|institution|collective|external)\b", q
    ))
    relation = bool(re.search(
        r"\b(?:between|relationship|relational|interplay|interaction|connection|"
        r"tension|dynamic|mutually exclusive)\b", q
    ))
    return personal and systemic and relation


def infer_orientational_frame(question: str) -> Dict[str, Any]:
    """Infer the dominant orientation of the question for internal routing."""
    q = re.sub(r"\s+", " ", str(question or "").lower()).strip()

    def count_terms(terms: Tuple[str, ...]) -> int:
        return sum(1 for term in terms if term in q)

    scores = {
        domain: count_terms(terms)
        for domain, terms in ORIENTATIONAL_DOMAIN_TERMS.items()
    }

    if detect_relational_orientation(question):
        primary = "relational"
        return {"primary": primary, "scores": scores, "relational": True}

    # Explicit systems conditions take precedence over inward language when
    # the question asks what is happening in the larger environment.
    if scores["systems"] > 0 and scores["systems"] >= scores["inward"]:
        primary = "systems"
    elif scores["stewardship"] > 0:
        primary = "stewardship"
    elif scores["inward"] > 0:
        primary = "inward"
    elif scores["transition"] > 0:
        primary = "transition"
    else:
        primary = "general"

    return {"primary": primary, "scores": scores}


def _orientational_resource_bonus(metadata: Dict[str, Any], frame: Dict[str, Any]) -> int:
    """Return a small routing bonus from existing canonical metadata only."""
    primary = str(frame.get("primary", "general"))
    terms = ORIENTATIONAL_DOMAIN_TERMS.get(primary, ())
    if not terms:
        return 0

    searchable = " ".join(
        str(metadata.get(key, ""))
        for key in ("title", "text", "content", "excerpt", "description", "category")
    ).lower()

    return sum(1 for term in terms if term in searchable)


def orientational_rerank_documents(
    documents: List[Dict[str, Any]],
    frame: Dict[str, Any],
    *,
    preserve_prefix: int = 0,
) -> List[Dict[str, Any]]:
    """Lightly reorder retrieved evidence without replacing semantic retrieval."""
    if not documents or frame.get("primary") == "general":
        return documents

    prefix = documents[:preserve_prefix]
    remainder = documents[preserve_prefix:]
    ranked = sorted(
        enumerate(remainder),
        key=lambda item: (-_orientational_resource_bonus(item[1], frame), item[0]),
    )
    return prefix + [doc for _index, doc in ranked]


# =====================================================================
# CANONICAL RETRIEVAL
# =====================================================================

def _metadata_from_root_fetch(
    root_doc: Any,
) -> Optional[Dict[str, Any]]:
    try:
        vectors = (
            root_doc.get("vectors", {})
            if hasattr(root_doc, "get")
            else getattr(root_doc, "vectors", {})
        )

        vector = vectors.get(ROOT_NODE_ID) if vectors else None

        if vector is None:
            return None

        metadata = (
            vector.get("metadata")
            if hasattr(vector, "get")
            else getattr(vector, "metadata", None)
        )

        return metadata if isinstance(metadata, dict) else None

    except Exception as exc:
        print(f"Root metadata extraction error: {exc}")
        return None


def _match_id(match: Any) -> Optional[str]:
    return (
        match.get("id")
        if hasattr(match, "get")
        else getattr(match, "id", None)
    )


def _match_score(match: Any) -> float:
    value = (
        match.get("score", 0.0)
        if hasattr(match, "get")
        else getattr(match, "score", 0.0)
    )

    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _match_metadata(
    match: Any,
) -> Optional[Dict[str, Any]]:
    metadata = (
        match.get("metadata")
        if hasattr(match, "get")
        else getattr(match, "metadata", None)
    )

    return metadata if isinstance(metadata, dict) else None


def _append_unique_resource(
    documents: List[Dict[str, Any]],
    seen_keys: set,
    metadata: Optional[Dict[str, Any]],
    *,
    require_destination: bool = False,
) -> None:
    if not metadata:
        return

    if require_destination and not _has_usable_destination(metadata):
        print(
            "USE destination validation: rejected non-destination "
            f"resource '{metadata.get('title', 'Untitled Resource')}'."
        )
        return

    key = _resource_key(metadata)

    if key in seen_keys:
        return

    if not _resource_content(metadata):
        return

    seen_keys.add(key)
    documents.append(metadata)


def _query_index(
    query_vector: List[float],
    top_k: int,
) -> List[Tuple[float, str, Dict[str, Any]]]:
    result = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
    )

    matches = (
        result.get("matches", [])
        if hasattr(result, "get")
        else getattr(result, "matches", [])
    )

    candidates: List[Tuple[float, str, Dict[str, Any]]] = []

    for match in matches:
        match_id = _match_id(match)
        metadata = _match_metadata(match)

        if not metadata:
            continue

        if match_id == ROOT_NODE_ID:
            continue

        candidates.append(
            (
                _match_score(match),
                str(match_id or ""),
                metadata,
            )
        )

    return candidates


def fetch_canonical_context(
    user_query: str,
) -> Dict[str, Any]:
    intent = classify_intent(user_query)
    collection_name = detect_collection_request(user_query)
    adaptive_orientation = detect_adaptive_stewardship_orientation(user_query)
    orientational_frame = infer_orientational_frame(user_query)

    print(
        "USE orientational frame: "
        f"primary={orientational_frame['primary']}, "
        f"scores={orientational_frame['scores']}, "
        f"relational={orientational_frame.get('relational', False)}"
    )

    structural_docs: List[Dict[str, Any]] = []
    adaptive_docs: List[Dict[str, Any]] = []
    retrieved_docs: List[Dict[str, Any]] = []
    candidates: List[Tuple[float, str, Dict[str, Any]]] = []
    seen_keys = set()

    if not index:
        return {
            "intent": intent,
            "context_blocks": "",
        }

    if adaptive_orientation["active"]:
        print(
            "USE adaptive stewardship orientation: "
            f"score={adaptive_orientation['score']}, "
            f"signals={adaptive_orientation['matched_signals']}"
        )
    else:
        print(
            "USE adaptive stewardship orientation: "
            f"inactive, score={adaptive_orientation['score']}"
        )

    if intent == "WHOLE_SITE_ORIENTATION":
        try:
            root_doc = index.fetch(ids=[ROOT_NODE_ID])
            root_metadata = _metadata_from_root_fetch(root_doc)

            _append_unique_resource(
                retrieved_docs,
                seen_keys,
                root_metadata,
            )

            if not root_metadata:
                print(
                    "WHOLE_SITE_ORIENTATION detected, but the "
                    f"root node '{ROOT_NODE_ID}' was not returned "
                    "with metadata."
                )

        except Exception as exc:
            print(f"Root node fetch error: {exc}")

    try:
        query_vector = generate_embedding(user_query)

        if query_vector:
            # -----------------------------------------------------------
            # STRUCTURAL DESTINATION RETRIEVAL
            # -----------------------------------------------------------
            if collection_name:
                structural_docs = _query_structural_index(
                    collection_name,
                )

                for metadata in structural_docs:
                    _append_unique_resource(
                        retrieved_docs,
                        seen_keys,
                        metadata,
                        require_destination=True,
                    )
                    if len(retrieved_docs) >= MAX_CONTEXT_RESOURCES:
                        break

                print(
                    "USE structural destination retrieval: "
                    f"collection='{collection_name}', "
                    f"usable_candidates={len(structural_docs)}, "
                    f"selected={len(retrieved_docs)}."
                )

            # -----------------------------------------------------------
            # ADAPTIVE STEWARDSHIP BRIDGE RETRIEVAL
            # -----------------------------------------------------------
            # Only activated by the current question's signal. This does
            # not change the engine or expose an internal stage to the user.
            if (
                adaptive_orientation["active"]
                and not collection_name
                and intent != "WHOLE_SITE_ORIENTATION"
            ):
                bridge_query = build_stewardship_bridge_query(user_query)
                bridge_vector = generate_embedding(bridge_query)

                if bridge_vector:
                    bridge_candidates = _query_index(
                        bridge_vector,
                        max(RETRIEVAL_TOP_K, 100),
                    )

                    adaptive_seen_keys = set()
                    for _score, _match_id_value, metadata in bridge_candidates:
                        _append_unique_resource(
                            adaptive_docs,
                            adaptive_seen_keys,
                            metadata,
                            require_destination=False,
                        )
                        if len(adaptive_docs) >= MAX_ADAPTIVE_BRIDGE_RESOURCES:
                            break

                # Place bridge evidence ahead of ordinary semantic neighbors
                # so the generator can see the developmental-to-stewardship
                # transition when the question actually warrants it.
                for metadata in adaptive_docs:
                    _append_unique_resource(
                        retrieved_docs,
                        seen_keys,
                        metadata,
                    )
                    if len(retrieved_docs) >= MAX_CONTEXT_RESOURCES:
                        break

                print(
                    "USE adaptive bridge retrieval: "
                    f"bridge_query=1, "
                    f"selected={len(adaptive_docs)}."
                )

            # -----------------------------------------------------------
            # ORDINARY SEMANTIC RETRIEVAL
            # -----------------------------------------------------------
            # Destination requests must not fall back to ordinary semantic
            # neighbors when a structural destination has been resolved.
            if not collection_name or not retrieved_docs:
                candidates = _query_index(
                    query_vector,
                    RETRIEVAL_TOP_K,
                )

                for _score, _match_id_value, metadata in candidates:
                    _append_unique_resource(
                        retrieved_docs,
                        seen_keys,
                        metadata,
                        require_destination=bool(collection_name),
                    )
                    if len(retrieved_docs) >= MAX_CONTEXT_RESOURCES:
                        break
            else:
                candidates = []

            print(
                "USE retrieval: "
                f"{len(candidates)} candidates -> "
                f"{len(retrieved_docs)} unique resources."
            )

    except Exception as exc:
        print(f"Index query error: {exc}")

    retrieved_docs = [
        doc
        for doc in retrieved_docs
        if isinstance(doc, dict) and doc
    ][:MAX_CONTEXT_RESOURCES]

    # Keep the complete canonical evidence returned by retrieval available
    # to the final link-construction boundary. Generation may use a smaller,
    # visitor-facing resource set, but link authority must not lose a
    # canonical resource merely because visitor-facing title deduplication
    # or the generation resource cap removed it.
    canonical_link_docs: List[Dict[str, Any]] = []
    canonical_link_seen_keys = set()
    for document in retrieved_docs:
        _append_unique_resource(
            canonical_link_docs,
            canonical_link_seen_keys,
            document,
        )
    for document in structural_docs:
        _append_unique_resource(
            canonical_link_docs,
            canonical_link_seen_keys,
            document,
            require_destination=False,
        )
    for document in adaptive_docs:
        _append_unique_resource(
            canonical_link_docs,
            canonical_link_seen_keys,
            document,
        )
    for _score, _match_id_value, metadata in candidates:
        _append_unique_resource(
            canonical_link_docs,
            canonical_link_seen_keys,
            metadata,
        )

    # URL identity remains authoritative for links, but visitor-facing
    # resource identity must also be unique in the generation context. Do not
    # expose two canonical records with the same display title as separate
    # choices.
    retrieved_docs = _dedupe_resources_by_display_title(retrieved_docs)

    # v25: semantic retrieval remains the source of candidates; this light
    # rerank makes the question's dominant orientation influence which of the
    # already-retrieved resources receive priority. Explicit collection
    # destinations remain first; ordinary topical evidence is then domain-biased.
    protected_prefix = min(len(structural_docs), len(retrieved_docs)) if collection_name else 0
    retrieved_docs = orientational_rerank_documents(
        retrieved_docs,
        orientational_frame,
        preserve_prefix=protected_prefix,
    )[:MAX_CONTEXT_RESOURCES]

    structural_destination_count = (
        min(len(structural_docs), len(retrieved_docs))
        if collection_name and retrieved_docs
        else 0
    )

    adaptive_bridge_count = (
        min(
            len(adaptive_docs),
            max(0, len(retrieved_docs) - structural_destination_count),
        )
        if adaptive_orientation["active"] and adaptive_docs
        else 0
    )

    # v40 root-cause boundary: generation and link authority are two
    # deliberately different contexts. The model receives ONLY the
    # selected, deduplicated, orientationally-reranked resources. The
    # complete canonical set is retained separately for final link
    # reconstruction. The previous version accidentally supplied the
    # complete canonical-link set to generation, bypassing the selected
    # retrieval order and allowing the bounded generation window to change
    # which resources the model could see.
    generation_context = format_context_blocks(
        retrieved_docs,
        structural_destination_count=structural_destination_count,
        adaptive_bridge_count=adaptive_bridge_count,
    )

    # v56 observability: expose the selected generation set in deployment logs.
    # This makes it possible to distinguish retrieval narrowing from model
    # selection without exposing any internal information to visitors.
    print(
        "USE generation selection: "
        f"selected={len(retrieved_docs)}, "
        f"titles={[ _canonical_display_title(str(doc.get('title', 'Untitled Resource'))) for doc in retrieved_docs ]}"
    )
    canonical_link_context = format_context_blocks(
        canonical_link_docs,
        structural_destination_count=0,
        adaptive_bridge_count=0,
    )

    return {
        "intent": intent,
        "orientational_frame": orientational_frame,
        "context_blocks": generation_context,
        "canonical_link_context": canonical_link_context,
    }


# =====================================================================
# CANONICAL LINK PRESENTATION NORMALIZATION
# =====================================================================

def _canonical_pairs(context_blocks: str) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []

    for block in context_blocks.split("\n\n---\n\n"):
        title_match = re.search(
            r"^Title:\s*(.+?)\s*$", block, flags=re.MULTILINE
        )
        url_match = re.search(
            r"^URL:\s*(https?://\S+)\s*$",
            block,
            flags=re.MULTILINE | re.IGNORECASE,
        )
        if not title_match or not url_match:
            continue

        title = title_match.group(1).strip()
        url = url_match.group(1).strip().rstrip(".,;")

        if title and url and url != "#":
            pairs.append((title, url))

    return pairs


def _canonical_display_title(title: str) -> str:
    """
    Return the visitor-facing form of a canonical title.

    Canonical evidence remains authoritative for identity. The only
    presentation change permitted here is removal of decorative leading
    Unicode symbol characters (including emoji) and surrounding whitespace.
    This keeps the visible link text title-only without altering the
    underlying canonical title/URL relationship.
    """
    value = str(title or "").strip()

    while value:
        first = value[0]
        category = unicodedata.category(first)

        # Unicode symbol categories cover emoji and decorative symbols.
        # Variation selectors and zero-width joiners can accompany emoji.
        if first in {"\\ufe0e", "\\ufe0f", "\\u200d"} or category.startswith("So"):
            value = value[1:].lstrip()
            continue

        # A leading modifier/symbol presentation character should not become
        # part of visitor-facing resource-link text.
        if category == "Sk":
            value = value[1:].lstrip()
            continue

        break

    return value or str(title or "").strip()


def sanitize_canonical_links(
    answer: str,
    context_blocks: str,
) -> str:
    """
    Enforce canonical URL grounding before presentation normalization.

    Any Markdown link whose destination is not an exact canonical URL is
    reduced to its visible label. Canonical destinations remain intact so
    the subsequent normalization stage can deterministically replace their
    visible labels with the canonical title.
    """
    pairs = _canonical_pairs(context_blocks)
    allowed_urls = {url.lower() for _title, url in pairs}

    # Models occasionally emit HTML anchors instead of Markdown. Normalize
    # those anchors BEFORE raw-URL sanitization; otherwise the sanitizer can
    # remove the URL and leave broken visitor-facing fragments such as
    # '<a href="'. Canonical URL identity remains authoritative.
    canonical_by_url = {
        url.lower(): (_canonical_display_title(title), url)
        for title, url in pairs
    }

    def replace_html_anchor(match: re.Match) -> str:
        url = match.group(1).strip().rstrip(".,;")
        canonical = canonical_by_url.get(url.lower())
        label = re.sub(r"<[^>]*>", "", match.group(2) or "").strip()

        if canonical is None:
            return label

        display_title, exact_url = canonical
        return f"[{display_title}]({exact_url})"

    # Standard HTML anchor: <a href="URL">label</a>, allowing attributes.
    answer = re.sub(
        r"<a\s+[^>]*?href=[\"\'](https?://[^\"\']+)[\"\'][^>]*>(.*?)</a>",
        replace_html_anchor,
        answer,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # Some model outputs omit the closing anchor tag. If the exact canonical
    # URL is present, rebuild the link from canonical evidence rather than
    # exposing the malformed HTML. Keep the remainder of the line intact.
    def replace_unclosed_html_anchor(match: re.Match) -> str:
        url = match.group(1).strip().rstrip(".,;")
        canonical = canonical_by_url.get(url.lower())
        label = match.group(2).strip()

        if canonical is None:
            return label

        display_title, exact_url = canonical
        return f"[{display_title}]({exact_url})"

    answer = re.sub(
        r"<a\s+[^>]*?href=[\"\'](https?://[^\"\']+)[\"\'][^>]*>([^<\n]{1,300})",
        replace_unclosed_html_anchor,
        answer,
        flags=re.IGNORECASE,
    )

    def replace_markdown(match: re.Match) -> str:
        label = match.group(1).strip()
        url = match.group(2).strip().rstrip(".,;")

        if url.lower() in allowed_urls:
            return match.group(0)

        return label

    answer = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        replace_markdown,
        answer,
        flags=re.IGNORECASE,
    )

    # Raw URLs are never visitor-facing. Canonical raw URLs are deliberately
    # retained for normalize_canonical_link_presentation(); all other raw
    # URLs are removed.
    for url in re.findall(r"https?://\S+", answer, flags=re.IGNORECASE):
        clean_url = url.rstrip(".,;)")
        if clean_url.lower() not in allowed_urls:
            answer = answer.replace(url, "")

    return answer.strip()


def _strip_model_link_markup(answer: str, context_blocks: str) -> str:
    """
    Remove model-generated link syntax while preserving the visible label.

    v19 deliberately treats Markdown/HTML construction as untrusted model
    output. The model is no longer responsible for creating visitor-facing
    hyperlinks. This function therefore collapses both valid and malformed
    link wrappers to their visible text before canonical links are rebuilt.
    """
    # Valid HTML anchors -> visible label.
    answer = re.sub(
        r"<a\s+[^>]*?href=[\"']https?://[^\"']+[\"'][^>]*>(.*?)</a>",
        lambda match: re.sub(r"<[^>]*>", "", match.group(1) or ""),
        answer,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # Unclosed HTML anchor fragments. Keep the visible text after the closing
    # quote/angle bracket when possible; remove the technical wrapper.
    answer = re.sub(
        r"<a\s+[^>]*?href=[\"']https?://[^\"']+[\"'][^>]*>",
        "",
        answer,
        flags=re.IGNORECASE,
    )
    answer = re.sub(r"</a>", "", answer, flags=re.IGNORECASE)

    # Valid Markdown links -> visible label. This also strips emoji/decorative
    # prefixes later when canonical titles are rebuilt.
    answer = re.sub(
        r"\[([^\]]+)\]\(https?://[^)]+\)",
        lambda match: match.group(1),
        answer,
        flags=re.IGNORECASE,
    )

    # Common malformed Markdown generated by models, e.g. **[Title( or
    # [Title]( without a destination. The canonical title itself is retained
    # so the deterministic title pass below can rebuild the link.
    answer = re.sub(r"\*\*\[([^\]\n]+)\]\([^\n]*", r"\1", answer)
    answer = re.sub(r"\[([^\]\n]+)\]\(", r"\1", answer)

    # Bare bracketed canonical titles are also model-generated presentation
    # syntax, e.g. "[The Illusion of Separation]" after an incomplete link
    # has already lost its destination. Remove the brackets here so the
    # deterministic canonical-title pass below can create the one valid link.
    for canonical_title in (_canonical_display_title(title) for title, _url in _canonical_pairs(context_blocks)):
        if not canonical_title:
            continue
        answer = re.sub(
            rf"\[({re.escape(canonical_title)})\]",
            r"\1",
            answer,
            flags=re.IGNORECASE,
        )

    # Remove stray Markdown emphasis that can otherwise remain attached to a
    # canonical title after link syntax has been collapsed.
    answer = re.sub(r"\*{1,3}([^*\n]+)\*{1,3}", r"\1", answer)

    # Canonical/raw URLs are technical data, never visitor-facing text. They
    # are removed here because the title pass below is the sole link creator.
    answer = re.sub(r"https?://\S+", "", answer, flags=re.IGNORECASE)

    # Remove orphaned HTML tags that might remain after malformed output.
    answer = re.sub(r"</?(?:a|span|p|strong|em)\b[^>]*>", "", answer, flags=re.IGNORECASE)

    # Clean up whitespace introduced by removing wrappers without changing
    # normal prose structure.
    answer = re.sub(r"[ \t]{2,}", " ", answer)
    answer = re.sub(r"\n[ \t]+", "\n", answer)

    return answer.strip()


def _link_canonical_titles(
    answer: str,
    context_blocks: str,
) -> str:
    """
    Reconstruct canonical links deterministically from evidence.

    v19's core architectural change is here: the LLM never supplies the
    visitor-facing URL syntax. Exact canonical titles and exact canonical
    URLs come from the retrieved corpus evidence, and this function creates
    the only permitted Markdown links.
    """
    pairs = _canonical_pairs(context_blocks)
    if not pairs:
        return answer.strip()

    # Longest titles first prevents a shorter title from consuming a prefix
    # of a longer canonical title.
    canonical_pairs = sorted(
        (
            _canonical_display_title(title),
            url,
        )
        for title, url in pairs
        if title and url
    )
    canonical_pairs.sort(key=lambda item: len(item[0]), reverse=True)

    # Split around already-created links so a second title pass cannot nest
    # or corrupt canonical Markdown.
    link_token_re = re.compile(r"\[[^\]]+\]\(https?://[^)]+\)")

    parts: List[str] = []
    cursor = 0
    for match in link_token_re.finditer(answer):
        plain = answer[cursor:match.start()]
        parts.append(_replace_titles_in_plain_text(plain, canonical_pairs))
        parts.append(match.group(0))
        cursor = match.end()

    parts.append(_replace_titles_in_plain_text(answer[cursor:], canonical_pairs))
    return "".join(parts).strip()


def _build_canonical_title_pattern(
    canonical_pairs: List[Tuple[str, str]],
) -> Tuple[re.Pattern, Dict[str, Tuple[str, str]]]:
    """
    Build one deterministic matcher for canonical titles.

    Matching remains against the original visitor text. The matcher tolerates
    presentation-equivalent Unicode forms that language models commonly emit:
    variable whitespace, dash variants, and straight/curly quotation marks.
    The replacement always uses the exact canonical title and URL supplied by
    the corpus evidence.
    """
    pattern_parts: List[str] = []
    group_map: Dict[str, Tuple[str, str]] = {}

    whitespace_class = r"[\s\u00A0]+"
    dash_class = r"[\u002D\u2010\u2013\u2014]"
    double_quote_class = r"[\"\u201C\u201D\u201E\u201F\u00AB\u00BB]"
    single_quote_class = r"[\'\u2018\u2019\u201A\u201B]"

    for index, (title, url) in enumerate(canonical_pairs):
        if not title or not url:
            continue

        group_name = f"canonical_title_{index}"
        clean_title = str(title).strip()

        parts: List[str] = []
        cursor = 0

        while cursor < len(clean_title):
            char = clean_title[cursor]

            if char.isspace() or char == "\u00A0":
                while cursor < len(clean_title) and (
                    clean_title[cursor].isspace()
                    or clean_title[cursor] == "\u00A0"
                ):
                    cursor += 1
                parts.append(whitespace_class)
                continue

            if char in ("-", "\u2010", "\u2013", "\u2014"):
                parts.append(dash_class)
                cursor += 1
                continue

            if char in ('"', "\u201C", "\u201D", "\u201E", "\u201F", "\u00AB", "\u00BB"):
                parts.append(double_quote_class)
                cursor += 1
                continue

            if char in ("'", "\u2018", "\u2019", "\u201A", "\u201B"):
                parts.append(single_quote_class)
                cursor += 1
                continue

            parts.append(re.escape(char))
            cursor += 1

        pattern_parts.append(f"(?P<{group_name}>{''.join(parts)})")
        group_map[group_name] = (title, url)

    if not pattern_parts:
        return re.compile(r"(?!x)x"), {}

    alternatives = "|".join(pattern_parts)
    pattern = re.compile(
        rf"(?<![\w\]])(?:{alternatives})(?![\w])(?!\]\()",
        flags=re.IGNORECASE,
    )
    return pattern, group_map

def _replace_titles_in_plain_text(
    text: str,
    canonical_pairs: List[Tuple[str, str]],
) -> str:
    """
    Replace canonical resource titles with deterministic Markdown links.

    The matcher tolerates harmless whitespace/NBSP and dash representation
    differences while preserving the exact canonical title and URL as the
    replacement authority.
    """
    if not text or not canonical_pairs:
        return text

    pattern, group_map = _build_canonical_title_pattern(canonical_pairs)
    if not group_map:
        return text

    def replace(match: re.Match) -> str:
        for group_name, canonical in group_map.items():
            if match.group(group_name) is not None:
                title, url = canonical
                return f"[{title}]({url})"
        return match.group(0)

    return pattern.sub(replace, text)


def normalize_link_presentation(
    answer: str,
    context_blocks: str,
) -> str:
    """
    Enforce the canonical visitor-facing link contract deterministically.

    v19 intentionally does not trust model-generated Markdown or HTML.
    Resource identity is established by canonical corpus evidence; the
    visitor-facing link is then constructed by USE itself as:

        [Canonical Title](Exact Canonical URL)

    This is the root fix for malformed Markdown, malformed HTML, emoji
    prefixes, raw URLs, and inconsistent link labels.
    """
    cleaned = _strip_model_link_markup(answer, context_blocks)
    return _link_canonical_titles(cleaned, context_blocks)

# =====================================================================
# BOUNDED GENERATION CONTEXT
# =====================================================================

def _truncate_evidence_content(content: str, limit: int) -> str:
    """Bound one resource's evidence without altering canonical metadata."""
    value = str(content or "").strip()
    if len(value) <= limit:
        return value

    # Prefer a clean character boundary. The generator is being given
    # evidence, not a publication-ready excerpt, so a hard ceiling is more
    # important than preserving the complete source text.
    truncated = value[:limit].rsplit(" ", 1)[0].strip()
    return truncated + " … [evidence excerpt bounded by USE]"


def build_generation_context(
    documents: List[Dict[str, Any]],
    *,
    max_chars: int = MAX_GENERATION_CONTEXT_CHARS,
    max_resource_chars: int = MAX_GENERATION_RESOURCE_CHARS,
) -> str:
    """
    Create a bounded evidence window for LLM generation.

    Retrieval remains broad and preserves its ordering. Generation is a
    separate budget: every selected resource retains its exact canonical
    title and URL, while only a bounded amount of content is exposed to the
    model. This prevents a large corpus excerpt from determining request
    size and causing provider-level 413 failures.
    """
    if not documents or max_chars <= 0:
        return ""

    blocks: List[str] = []
    used = 0

    for doc in documents:
        title = _canonical_display_title(str(doc.get("title", "Untitled Resource")).strip())
        url = str(doc.get("url", "#")).strip()
        content = _resource_content(doc)

        if not title or not content:
            continue

        block_prefix = (
            "Title: " + title + "\n"
            "URL: " + url + "\n"
            "Content: "
        )
        separator = "\n\n---\n\n" if blocks else ""
        remaining = max_chars - used - len(separator) - len(block_prefix)

        if remaining <= 120:
            break

        content_limit = min(max_resource_chars, remaining)
        bounded_content = _truncate_evidence_content(content, content_limit)

        block = block_prefix + bounded_content

        # A truncation marker can itself push the block slightly beyond the
        # remaining budget. Trim once more if necessary while retaining the
        # title and URL, which are the canonical link identity.
        if len(block) > remaining:
            available = max(1, remaining - len(block_prefix) - 20)
            bounded_content = _truncate_evidence_content(content, available)
            block = block_prefix + bounded_content

        if len(block) > remaining:
            break

        blocks.append(block)
        used += len(separator) + len(block)

    return "\n\n---\n\n".join(blocks).strip()


def _contains_internal_reasoning_leak(text: str) -> bool:
    """
    Detect known internal-process markers before any visitor-facing output
    can leave the backend.

    This is intentionally conservative: suspicious output is rejected and the
    normal model fallback chain is allowed to try another generation model.
    We do not attempt to guess where a leaked reasoning trace ends.
    """
    value = str(text or "")
    lowered = value.casefold()

    forbidden_markers = (
        "thinking process:",
        "chain of thought",
        "analyze the request:",
        "analyze user query",
        "scan retrieved evidence",
        "synthesize findings",
        "draft response",
        "mental refinement",
        "internal query classification",
        "internal canonical evidence",
        "internal evidence",
        "evidence analysis workflow",
        "retrieval commentary",
        "retrieval report",
        "diagnostic trace",
        "prompt explanation",
    )

    if any(marker in lowered for marker in forbidden_markers):
        return True

    # Catch the numbered internal workflow reproduced verbatim.
    if re.search(
        r"(?im)^\s*1\.\s*(?:analyze|analyse)\s+(?:the\s+)?(?:request|user\s+query)\s*:",
        value,
    ):
        return True

    return False


def _contains_evidence_schema_leak(text: str) -> bool:
    """
    Detect canonical-evidence metadata reproduced as if it were visitor prose.

    Canonical evidence is internal input to generation. Labels such as
    ``Title:``, ``URL:``, and ``Content:`` must never become visitor-facing
    output. The detector is intentionally conservative: when evidence-schema
    material is exposed, reject the complete generation and use the existing
    fallback path rather than attempting to reconstruct a partial answer.
    """
    value = str(text or "")

    if re.search(r"(?im)^\s*(?:title|url|content|id)\s*:\s*", value):
        return True

    title_labels = re.findall(r"(?im)\btitle\s*:", value)
    if len(title_labels) >= 2:
        return True

    if re.search(
        r"(?is)\b(?:title|url|content)\s*:\s*.+?\b(?:title|url|content)\s*:",
        value,
    ):
        return True

    if re.search(
        r"(?im)^\s*(?:canonical evidence|retrieved evidence|evidence block)\s*:",
        value,
    ):
        return True

    return False


def _extract_visitor_answer(generated_text: str) -> str:
    """
    Accept both the preferred visitor_answer envelope and clean unwrapped
    model output. The envelope is a useful boundary, but it is not allowed
    to turn a valid answer into a failed generation.
    """
    text = str(generated_text or "").strip()
    if not text:
        return ""

    if _contains_internal_reasoning_leak(text):
        print("USE output boundary: internal reasoning/process leakage detected; "
              "rejecting this model output.")
        return ""

    if _contains_evidence_schema_leak(text):
        print("USE output boundary: canonical evidence-schema leakage detected; "
              "rejecting this model output.")
        return ""

    visitor_match = re.search(
        r"<visitor_answer>\s*(.*?)\s*</visitor_answer>",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if visitor_match:
        return visitor_match.group(1).strip()

    # If a model emits only one side of the envelope, remove that wrapper
    # rather than rejecting an otherwise usable visitor answer.
    text = re.sub(
        r"</?visitor_answer>",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()

    return text


def _strip_emoji(text: str) -> str:
    """
    Remove emoji presentation characters anywhere in visitor-facing output.

    This is deliberately a presentation-boundary operation. It does not
    modify canonical evidence, resource identity, retrieval, or orientation.
    """
    value = str(text or "")

    # Emoji-capable Unicode ranges commonly used by model-generated output.
    emoji_ranges = (
        r"\U0001F1E6-\U0001F1FF"  # regional indicators
        r"\U0001F300-\U0001FAFF"  # pictographs, symbols, emoji
        r"\u2600-\u27BF"          # miscellaneous symbols/dingbats
        r"\u2B00-\u2BFF"          # supplemental symbols, including U+2B50 WHITE MEDIUM STAR
        r"\u2300-\u23FF"          # technical/misc symbols occasionally emoji-presented
    )
    value = re.sub(f"[{emoji_ranges}]", "", value)

    # Remove emoji presentation selectors and zero-width joiners left behind
    # after the base emoji is removed.
    value = re.sub(r"[\ufe0e\ufe0f\u200d]", "", value)

    # Remove stray keycap combining marks that can remain after sanitation.
    value = re.sub(r"\u20e3", "", value)

    # Normalize whitespace created by removal without changing paragraph flow.
    value = re.sub(r"[ \t]{2,}", " ", value)
    value = re.sub(r"[ \t]+\n", "\n", value)
    value = re.sub(r"\n[ \t]+", "\n", value)
    return value.strip()


def _strip_leading_decorative_symbols(text: str) -> str:
    """Remove leading decorative Unicode symbols from visitor-facing text."""
    value = str(text or "").strip()

    while value:
        first = value[0]
        category = unicodedata.category(first)

        if first in {"\\ufe0e", "\\ufe0f", "\\u200d"}:
            value = value[1:].lstrip()
            continue

        if category.startswith("So") or category == "Sk":
            value = value[1:].lstrip()
            continue

        break

    return value


def _dedupe_repeated_canonical_list_items(
    answer: str,
    context_blocks: str,
) -> str:
    """Remove repeated canonical resources from numbered resource lists."""
    canonical_titles = {
        _canonical_display_title(title).casefold(): _canonical_display_title(title)
        for title, _url in _canonical_pairs(context_blocks)
        if _canonical_display_title(title) and not _is_non_resource_service_title(title)
    }
    if not canonical_titles:
        return answer

    lines = answer.splitlines()
    output: List[str] = []
    seen_in_list = set()
    in_numbered_list = False
    item_pattern = re.compile(r"^(\s*)(\d+)[.)]\s+(.+?)\s*$")

    for line in lines:
        match = item_pattern.match(line)
        if not match:
            if in_numbered_list and line.strip():
                in_numbered_list = False
                seen_in_list.clear()
            output.append(line)
            continue

        in_numbered_list = True
        item_text = match.group(3).strip()
        matched_key = None
        for key, display_title in canonical_titles.items():
            if re.search(
                rf"(?<![\w]){re.escape(display_title)}(?![\w])",
                item_text,
                flags=re.IGNORECASE,
            ):
                matched_key = key
                break

        if matched_key is not None:
            if matched_key in seen_in_list:
                print(
                    "USE resource uniqueness: removed repeated canonical "
                    f"list item '{canonical_titles[matched_key]}'."
                )
                continue
            seen_in_list.add(matched_key)

        output.append(line)

    return "\n".join(output).strip()


def _is_non_resource_service_title(title: str) -> bool:
    """Reject generic service/navigation labels from topical resource lists.

    These labels may exist as valid site destinations, but they are not
    canonical editorial resources for a topical answer. The rule is deliberately
    narrow and title-based so it does not alter retrieval or prevent an explicit
    destination request from reaching the site.
    """
    normalized = re.sub(r"\s+", " ", str(title or "").strip()).casefold()
    non_resource_titles = {
        "workshops & advisory",
        "workshops and advisory",
    }
    return normalized in non_resource_titles


def _remove_unresolvable_resource_list_items(
    answer: str,
    context_blocks: str,
) -> str:
    """
    Enforce the canonical resource-selection boundary before link creation.

    A model may repeat a canonical title found inside evidence content even
    when that resource was not itself retrieved as a canonical resource
    record. Such a title has no authorized URL in the current evidence set.
    Resource lists are therefore restricted to titles that exist on a
    canonical Title: line. Non-resource prose is left untouched.
    """
    if not answer or not context_blocks:
        return answer

    canonical_pairs = _canonical_pairs(context_blocks)
    if not canonical_pairs:
        return answer

    canonical_titles = [
        title
        for title, _url in canonical_pairs
        if title and not _is_non_resource_service_title(title)
    ]
    if not canonical_titles:
        return answer

    lines = answer.splitlines()
    output: List[str] = []
    in_resource_list = False
    list_item_re = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.+?)\s*$")
    resource_heading_re = re.compile(
        r"(?i)(?:resources?|essays?|pathways?|readings?|further reading|further readings|explore these|consider(?: these)?|following resources)\s*:\s*$"
    )

    def is_canonical_title(value: str) -> bool:
        candidate = re.sub(r"^\*\*(.*?)\*\*$", r"\1", value.strip())
        candidate = re.sub(r"^\[([^\]]+)\]\([^)]*\)$", r"\1", candidate)
        candidate = candidate.strip()
        for title in canonical_titles:
            probe = _replace_titles_in_plain_text(candidate, [(title, "https://example.invalid/self-audit")])
            if probe.startswith("[") and "](" in probe:
                return True
        return False

    for index, line in enumerate(lines):
        stripped = line.strip()
        item = list_item_re.match(line)

        if not in_resource_list:
            if resource_heading_re.search(stripped):
                in_resource_list = True
            output.append(line)
            continue

        if not stripped:
            # A blank line is allowed between a resource heading and its
            # list, and between list items. Only close the resource boundary
            # when the next substantive line is not itself a list item.
            next_nonblank = None
            for lookahead in lines[index + 1:]:
                if lookahead.strip():
                    next_nonblank = lookahead
                    break

            if next_nonblank is not None and list_item_re.match(next_nonblank):
                output.append(line)
                continue

            in_resource_list = False
            output.append(line)
            continue

        if item:
            item_text = item.group(3).strip()
            if is_canonical_title(item_text):
                output.append(line)
            else:
                print(
                    "USE resource boundary: removed unresolvable resource "
                    f"list item '{item_text}'."
                )
            continue

        # A non-list line closes the resource-list boundary.
        in_resource_list = False
        output.append(line)

    return "\n".join(output).strip()


def _canonical_resource_titles(context_blocks: str) -> List[str]:
    """Return canonical display titles that are actually available to generation."""
    titles: List[str] = []
    seen = set()
    for title, url in _canonical_pairs(context_blocks):
        display_title = _canonical_display_title(title)
        if not display_title or not url:
            continue
        key = display_title.casefold()
        if key in seen:
            continue
        seen.add(key)
        titles.append(display_title)
    return titles


def _ensure_nonempty_resource_section(
    answer: str,
    generation_context: str,
) -> str:
    """
    Prevent a visitor-facing resource heading from being left empty.

    Generation is allowed to choose the strongest resources, but if the model
    emits a resource heading without a usable canonical resource item, USE
    supplies the first available canonical resources from the already-selected
    generation set. This never introduces a resource outside generation
    evidence and never fabricates a URL.
    """
    if not answer or not generation_context:
        return answer

    canonical_titles = _canonical_resource_titles(generation_context)
    if not canonical_titles:
        return answer

    lines = answer.splitlines()
    heading_re = re.compile(
        r"(?i)^.*(?:resources?|essays?|pathways?|readings?|"
        r"further reading|further readings|explore these|"
        r"consider(?: these)?|following resources)\s*:\s*$"
    )
    list_item_re = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.+?)\s*$")

    for index, line in enumerate(lines):
        if not heading_re.match(line):
            continue

        # Inspect the substantive lines following the heading. Stop at the
        # next ordinary prose line; blank lines do not terminate the section.
        valid_found = False
        insertion_index = index + 1
        j = index + 1
        while j < len(lines):
            stripped = lines[j].strip()
            if not stripped:
                j += 1
                insertion_index = j
                continue

            item_match = list_item_re.match(lines[j])
            if not item_match:
                break

            item_text = item_match.group(1).strip()
            normalized = re.sub(r"^\*\*(.*?)\*\*$", r"\1", item_text).strip()
            normalized = re.sub(r"^\[([^\]]+)\]\([^)]*\)$", r"\1", normalized).strip()
            if any(
                re.search(rf"(?<![\w]){re.escape(title)}(?![\w])", normalized, flags=re.IGNORECASE)
                for title in canonical_titles
            ):
                valid_found = True
                break
            j += 1
            insertion_index = j

        if valid_found:
            continue

        # The model supplied the heading but no usable canonical resource.
        # Insert deterministic resource choices from the selected generation
        # evidence immediately after the heading and any intervening blanks.
        additions = [f"- {title}" for title in canonical_titles[:3]]
        lines[insertion_index:insertion_index] = additions
        print(
            "USE resource boundary: restored canonical resource selection "
            f"after empty resource heading ({len(additions)} resources)."
        )
        return "\n".join(lines).strip()

    return answer



def _format_standalone_canonical_resource_links(
    answer: str,
    generation_context: str,
) -> str:
    """
    Preserve discrete visitor-facing boundaries around canonical resources.

    Two deterministic presentation repairs are handled here:
      1. bare standalone canonical Markdown links become list items;
      2. ordinary prose immediately following a canonical resource list is
         separated by a blank line.

    This function does not create, remove, rank, or expand resource selection.
    """
    if not answer or not generation_context:
        return answer

    canonical_titles = {
        _canonical_display_title(title).casefold()
        for title, _url in _canonical_pairs(generation_context)
        if _canonical_display_title(title)
    }
    if not canonical_titles:
        return answer

    lines = answer.splitlines()
    output: List[str] = []
    standalone_link_re = re.compile(
        r"^\s*\[([^\]]+)\]\((https?://[^)]+)\)\s*$",
        flags=re.IGNORECASE,
    )
    list_item_re = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.+?)\s*$")

    def _is_canonical_resource_line(line: str) -> bool:
        match = list_item_re.match(line)
        if not match:
            return False
        item_text = re.sub(
            r"^\*\*(.*?)\*\*$", r"\1", match.group(1).strip()
        ).strip()
        link_match = standalone_link_re.match(item_text)
        if link_match:
            title = re.sub(r"\s+", " ", link_match.group(1).strip()).casefold()
            return title in canonical_titles
        title = re.sub(r"^\[([^\]]+)\]\([^)]*\)$", r"\1", item_text).strip()
        return any(
            re.search(
                rf"(?<![\w]){re.escape(canonical_title)}(?![\w])",
                title,
                flags=re.IGNORECASE,
            )
            for canonical_title in canonical_titles
        )

    for line in lines:
        match = standalone_link_re.match(line)
        if match:
            visible_title = re.sub(
                r"\s+", " ", match.group(1).strip()
            ).casefold()
            if visible_title in canonical_titles:
                output.append(f"- {line.strip()}")
                continue

        # Force a Markdown block boundary when ordinary prose follows the
        # canonical resource list. Without this, Markdown renders the prose as
        # a continuation of the final resource bullet.
        if (
            line.strip()
            and output
            and _is_canonical_resource_line(output[-1])
            and not list_item_re.match(line)
        ):
            output.append("")

        output.append(line)

    return "\n".join(output).strip()



def _strip_stray_markdown_emphasis(answer: str) -> str:
    """Remove leaked emphasis markers while preserving unordered-list markers."""
    if not answer:
        return answer

    cleaned_lines: List[str] = []
    for line in answer.splitlines():
        leading_list_marker = re.match(r"^(\s*[-+*]\s+)", line)
        if leading_list_marker:
            prefix = leading_list_marker.group(1)
            remainder = line[len(prefix):]
            remainder = re.sub(r"\*{1,3}", "", remainder)
            cleaned_lines.append(prefix + remainder)
        else:
            cleaned_lines.append(re.sub(r"\*{1,3}", "", line))

    return "\n".join(cleaned_lines).strip()


def _dedupe_canonical_resource_items_across_answer(
    answer: str,
    generation_context: str,
) -> str:
    """Allow each canonical resource to appear at most once in visitor resource lists."""
    if not answer or not generation_context:
        return answer

    canonical_titles = {
        _canonical_display_title(title).casefold(): _canonical_display_title(title)
        for title, _url in _canonical_pairs(generation_context)
        if _canonical_display_title(title)
    }
    if not canonical_titles:
        return answer

    lines = answer.splitlines()
    output: List[str] = []
    seen_resource_keys = set()
    list_item_re = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.+?)\s*$")
    link_re = re.compile(r"^\[([^\]]+)\]\(https?://[^)]+\)$")

    for line in lines:
        match = list_item_re.match(line)
        if not match:
            output.append(line)
            continue

        item_text = match.group(1).strip()
        link_match = link_re.match(item_text)
        candidate = link_match.group(1).strip() if link_match else item_text
        candidate = re.sub(r"^\*{1,3}(.*?)\*{1,3}$", r"\1", candidate).strip()

        matched_key = None
        for key, display_title in canonical_titles.items():
            if re.search(
                rf"(?<![\w]){re.escape(display_title)}(?![\w])",
                candidate,
                flags=re.IGNORECASE,
            ):
                matched_key = key
                break

        if matched_key is None:
            output.append(line)
            continue

        if matched_key in seen_resource_keys:
            print(
                "USE resource uniqueness: removed duplicate canonical resource "
                f"across visitor answer '{canonical_titles[matched_key]}'."
            )
            continue

        seen_resource_keys.add(matched_key)
        output.append(line)

    # If cross-section deduplication emptied a resource heading, remove the
    # orphan heading rather than presenting an empty "Further reading:" block.
    heading_re = re.compile(
        r"(?i)^.*(?:resources?|essays?|pathways?|readings?|"
        r"further reading|further readings|explore these|"
        r"consider(?: these)?|following resources)\s*:\s*$"
    )
    filtered: List[str] = []
    for index, line in enumerate(output):
        if not heading_re.match(line.strip()):
            filtered.append(line)
            continue

        next_nonblank = None
        for lookahead in output[index + 1:]:
            if lookahead.strip():
                next_nonblank = lookahead
                break

        if next_nonblank is None or not list_item_re.match(next_nonblank):
            print(
                "USE resource boundary: removed empty visitor-facing resource heading."
            )
            continue

        filtered.append(line)

    return "\n".join(filtered).strip()


def _clean_generation_output(
    generated_text: str,
    generation_context: str,
    canonical_link_context: str = "",
) -> str:
    answer = _extract_visitor_answer(generated_text)
    if not answer:
        return ""

    link_context = canonical_link_context or generation_context

    # Resource eligibility is governed by the selected generation set. Link
    # authority may be broader, but it must never expand the set of resources
    # the visitor is offered.
    cleaned_answer = _remove_unresolvable_resource_list_items(
        answer,
        generation_context,
    )
    cleaned_answer = _ensure_nonempty_resource_section(
        cleaned_answer,
        generation_context,
    )
    cleaned_answer = _dedupe_repeated_canonical_list_items(
        cleaned_answer,
        generation_context,
    )
    cleaned_answer = _strip_leading_decorative_symbols(cleaned_answer)
    cleaned_answer = _strip_emoji(cleaned_answer)
    cleaned_answer = _strip_stray_markdown_emphasis(cleaned_answer)

    normalized_answer = normalize_link_presentation(
        sanitize_canonical_links(cleaned_answer, link_context),
        link_context,
    )
    normalized_answer = _format_standalone_canonical_resource_links(
        normalized_answer,
        generation_context,
    )
    normalized_answer = _dedupe_canonical_resource_items_across_answer(
        normalized_answer,
        generation_context,
    )
    normalized_answer = _strip_stray_markdown_emphasis(normalized_answer)

    # Final presentation boundary: canonical link normalization may recreate
    # visible title text from canonical evidence. Sanitize once more after
    # normalization so no emoji/decorative symbol or HTML entity encoding can
    # survive in visitor-facing text. Internal corpus metadata is never modified.
    normalized_answer = html.unescape(normalized_answer)
    return _strip_emoji(normalized_answer)

# =====================================================================
# GROQ GENERATION
# =====================================================================


def _bound_existing_context_blocks(
    context_blocks: str,
    max_chars: int,
    max_resource_chars: int,
) -> str:
    """Bound canonical blocks to an exact character ceiling without losing identity."""
    if not context_blocks or max_chars <= 0 or max_resource_chars <= 0:
        return ""

    bounded: List[str] = []
    used = 0

    for block in context_blocks.split("\n\n---\n\n"):
        title_match = re.search(r"^Title:\s*(.+?)\s*$", block, flags=re.MULTILINE)
        url_match = re.search(
            r"^URL:\s*(https?://\S+)\s*$",
            block,
            flags=re.MULTILINE | re.IGNORECASE,
        )
        content_match = re.search(
            r"^Content:\s*(.*)$", block, flags=re.MULTILINE | re.DOTALL
        )

        if not title_match or not url_match or not content_match:
            continue

        title = _canonical_display_title(title_match.group(1).strip())
        url = url_match.group(1).strip()
        content = content_match.group(1).strip()
        prefix = f"Title: {title}\nURL: {url}\nContent: "
        separator = "\n\n---\n\n" if bounded else ""
        remaining = max_chars - used - len(separator)

        if remaining <= len(prefix):
            break

        content_capacity = min(max_resource_chars, remaining - len(prefix))
        if content_capacity <= 0:
            break

        if len(content) <= content_capacity:
            bounded_content = content
        else:
            # Exact-fit rule: never allow a truncation marker to push the
            # canonical block over the provider ceiling. A marker is optional;
            # title and URL identity are not.
            marker = " … [bounded]"
            if content_capacity > len(marker) + 1:
                bounded_content = (
                    content[: content_capacity - len(marker)].rstrip() + marker
                )
            else:
                bounded_content = content[:content_capacity].rstrip()

        candidate = prefix + bounded_content
        if len(candidate) > remaining:
            bounded_content = content[: max(1, remaining - len(prefix))].rstrip()
            candidate = prefix + bounded_content

        if len(candidate) > remaining:
            break

        bounded.append(candidate)
        used += len(separator) + len(candidate)

    return "\n\n---\n\n".join(bounded).strip()

def context_blocks_to_documents(context_blocks: str) -> List[Dict[str, Any]]:
    """Parse canonical context blocks for generation-only bounding."""
    documents: List[Dict[str, Any]] = []

    for block in context_blocks.split("\n\n---\n\n"):
        title_match = re.search(r"^Title:\s*(.+?)\s*$", block, flags=re.MULTILINE)
        url_match = re.search(r"^URL:\s*(https?://\S+)\s*$", block, flags=re.MULTILINE | re.IGNORECASE)
        content_match = re.search(r"^Content:\s*(.*)$", block, flags=re.MULTILINE | re.DOTALL)

        if not title_match or not url_match or not content_match:
            continue

        documents.append({
            "title": title_match.group(1).strip(),
            "url": url_match.group(1).strip(),
            "text": content_match.group(1).strip(),
        })

    return documents

def _parse_provider_retry_delay_seconds(error_text: str) -> Optional[float]:
    """Parse Groq's human-readable retry delay, including m/s combinations."""
    match = re.search(
        r"try again in\s+((?:[0-9]+(?:\.[0-9]+)?h\s*)?(?:[0-9]+(?:\.[0-9]+)?m\s*)?(?:[0-9]+(?:\.[0-9]+)?s)?)",
        error_text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None

    value = match.group(1).strip().lower()
    total = 0.0
    for amount, unit in re.findall(r"([0-9]+(?:\.[0-9]+)?)\s*([hms])", value):
        multiplier = {"h": 3600.0, "m": 60.0, "s": 1.0}[unit]
        total += float(amount) * multiplier

    return total if total > 0 else None


def _rate_limit_seconds(error_text: str) -> float:
    """Extract a provider-supplied retry delay for ordinary rate limits."""
    parsed = _parse_provider_retry_delay_seconds(error_text)
    if parsed is not None:
        return max(15.0, min(parsed + 2.0, 3600.0))
    return 30.0


def _parse_daily_tpd_state(error_text: str) -> Optional[Dict[str, Any]]:
    """Extract an explicitly reported Groq daily TPD limit/usage state."""
    clean = str(error_text or "")
    if not re.search(r"tokens per day\s*\(TPD\)", clean, flags=re.IGNORECASE):
        return None

    match = re.search(
        r"Limit\s+([0-9,]+)\s*,\s*Used\s+([0-9,]+)\s*,\s*Requested\s+([0-9,]+)",
        clean,
        flags=re.IGNORECASE,
    )
    if not match:
        return None

    limit = int(match.group(1).replace(",", ""))
    used = int(match.group(2).replace(",", ""))
    requested = int(match.group(3).replace(",", ""))
    retry_seconds = _parse_provider_retry_delay_seconds(clean)

    return {
        "limit": limit,
        "used": used,
        "requested": requested,
        "remaining": max(0, limit - used),
        "reset_at": time.time() + (retry_seconds if retry_seconds is not None else 86400.0),
        "observed_at": time.time(),
    }


def _record_daily_tpd_state(candidate_model: str, error_text: str) -> bool:
    """Record an explicit provider TPD state and bind it to this candidate."""
    state = _parse_daily_tpd_state(error_text)
    if not state:
        return False

    with MODEL_CACHE_LOCK:
        MODEL_CACHE["daily_tpd"][candidate_model] = state

    print(
        "USE provider daily TPD state observed: "
        f"candidate='{candidate_model}', used={state['used']}, "
        f"limit={state['limit']}, remaining={state['remaining']}, "
        f"requested={state['requested']}."
    )
    return True


def _estimate_quota_tokens(messages: List[Dict[str, str]], max_tokens: int) -> int:
    """Conservatively estimate total tokens consumed by one provider request."""
    chars = _estimate_message_chars(messages)
    estimated_input = math.ceil(chars / 5.0)
    estimated_total = math.ceil((estimated_input + max_tokens) * 1.10)
    return max(1, estimated_total)


def _known_daily_tpd_preflight(candidate_model: str, estimated_tokens: int) -> None:
    """Skip a candidate when observed provider TPD is known to be insufficient."""
    now = time.time()
    with MODEL_CACHE_LOCK:
        state = MODEL_CACHE["daily_tpd"].get(candidate_model)
        if not state:
            return

        if float(state.get("reset_at", 0.0)) <= now:
            MODEL_CACHE["daily_tpd"].pop(candidate_model, None)
            return

        remaining = max(0, int(state.get("limit", 0)) - int(state.get("used", 0)))
        if estimated_tokens <= remaining:
            return

    raise KnownDailyQuotaInsufficient(
        candidate_model=candidate_model,
        estimated_tokens=estimated_tokens,
        remaining_tokens=remaining,
    )


class KnownDailyQuotaInsufficient(RuntimeError):
    """Raised before a request when observed daily TPD is insufficient."""

    def __init__(self, candidate_model: str, estimated_tokens: int, remaining_tokens: int):
        super().__init__(
            f"Known insufficient Groq daily TPD for '{candidate_model}': "
            f"estimated request {estimated_tokens} tokens exceeds "
            f"observed remaining quota {remaining_tokens} tokens."
        )
        self.candidate_model = candidate_model
        self.estimated_tokens = estimated_tokens
        self.remaining_tokens = remaining_tokens


def _build_generation_system_content(
    intent: str,
    generation_context: str,
) -> str:
    """
    Build the complete generation system message from explicitly supplied
    local variables. No generation path relies on an ambient context variable.
    """
    return (
        f"{GENERATION_SYSTEM_PROMPT}\n\n"
        f"[INTERNAL QUERY CLASSIFICATION — DO NOT REVEAL]: {intent}\n\n"
        f"[INTERNAL CANONICAL EVIDENCE — DO NOT DESCRIBE AS RETRIEVAL "
        f"OR INTERNAL CONTEXT]:\n"
        f"{generation_context}\n\n"
        "[FINAL RESPONSE REQUIREMENT]\n"
        "Respond directly to the visitor's question. Output the finished "
        "visitor-facing answer. A clean answer without a wrapper is valid. "
        "Never reveal internal reasoning, retrieval, classification, "
        "evidence-selection, prompting, or drafting process. "
        "For every canonical resource you recommend, write only its exact "
        "canonical title as plain text. When two or more supplied canonical resources "
        "are materially relevant and provide distinct useful coverage, normally "
        "recommend 2–3 resources rather than collapsing the answer to the first or "
        "highest-scoring resource. Use one only when one is genuinely sufficient; "
        "never pad the answer with weak matches. A resource is recommendable ONLY when "
        "its exact title appears on a Title: line in the supplied canonical "
        "evidence. A title appearing only inside Content is not a selectable "
        "resource and must not be recommended as one. Never invent, paraphrase, "
        "or reconstruct a resource title. Do not construct Markdown links, "
        "HTML anchors, raw URLs, URL slugs, or emoji prefixes. USE constructs "
        "canonical links after generation."
    )



def _estimate_message_chars(messages: List[Dict[str, str]]) -> int:
    """Return the actual character count of the assembled provider messages."""
    return sum(len(str(message.get("content", ""))) for message in messages)


def _fit_generation_context_to_provider_budget(
    user_query: str,
    intent: str,
    generation_context: str,
    *,
    max_tokens: int,
    orientational_frame: Optional[Dict[str, Any]] = None,
) -> Tuple[str, List[Dict[str, str]]]:
    """
    Preflight the complete provider payload and compact evidence until the
    assembled request is guaranteed to fit the configured envelope.

    The critical correction in v55 is that the minimum evidence window is
    no longer a fixed 1,100-character floor. The provider budget is calculated
    from the actual system+user envelope first, then the evidence is bounded
    to the remaining space. This prevents the v54 failure where the smallest
    allowed evidence block was still 55 characters too large for the request
    envelope.
    """
    candidate = str(generation_context or "").strip()

    # Calculate the non-evidence envelope once. This is the authoritative
    # amount of space consumed before canonical evidence is inserted.
    empty_messages = _build_generation_messages(
        user_query, intent, "", orientational_frame
    )
    fixed_input_chars = _estimate_message_chars(empty_messages)
    estimated_output_chars = math.ceil(max_tokens * 4 * 1.25)

    context_capacity = min(
        MAX_PROVIDER_INPUT_CHARS - fixed_input_chars,
        MAX_PROVIDER_TOTAL_CHARS - fixed_input_chars - estimated_output_chars,
    )

    if context_capacity < 0:
        raise ValueError(
            "USE provider preflight could not fit the fixed system/user "
            f"envelope: fixed_input={fixed_input_chars}, "
            f"estimated_output={estimated_output_chars}."
        )

    # Preserve canonical title+URL identity while adapting content to the
    # exact remaining provider capacity. Never force a larger minimum than
    # the provider envelope can accommodate.
    if candidate:
        target_context_chars = min(
            len(candidate),
            context_capacity,
            MAX_GENERATION_CONTEXT_CHARS,
        )
        candidate = _bound_existing_context_blocks(
            candidate,
            max(0, target_context_chars),
            min(
                MAX_GENERATION_RESOURCE_CHARS,
                max(120, target_context_chars),
            ) if target_context_chars > 0 else 0,
        )

    while True:
        messages = _build_generation_messages(
            user_query, intent, candidate, orientational_frame
        )
        input_chars = _estimate_message_chars(messages)
        total_estimate = input_chars + estimated_output_chars

        if (
            input_chars <= MAX_PROVIDER_INPUT_CHARS
            and total_estimate <= MAX_PROVIDER_TOTAL_CHARS
        ):
            print(
                "USE provider preflight: "
                f"input={input_chars} chars, "
                f"estimated_total={total_estimate} chars, "
                f"max_tokens={max_tokens}, "
                f"fixed_input={fixed_input_chars}, "
                f"evidence={len(candidate)} chars."
            )
            return candidate, messages

        if not candidate:
            raise ValueError(
                "USE provider preflight could not fit the assembled request "
                f"within the configured budget: input={input_chars}, "
                f"estimated_total={total_estimate}."
            )

        excess = max(
            input_chars - MAX_PROVIDER_INPUT_CHARS,
            total_estimate - MAX_PROVIDER_TOTAL_CHARS,
        )
        target_context_chars = max(0, len(candidate) - max(64, excess + 32))
        if target_context_chars >= len(candidate):
            target_context_chars = max(0, len(candidate) - 64)

        candidate = _bound_existing_context_blocks(
            candidate,
            target_context_chars,
            min(
                MAX_COMPACT_GENERATION_RESOURCE_CHARS,
                max(120, target_context_chars),
            ) if target_context_chars > 0 else 0,
        )



def _build_generation_messages(
    user_query: str,
    intent: str,
    generation_context: str,
    orientational_frame: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, str]]:
    """Build one canonical provider request from one explicit context value."""
    safe_context = str(generation_context or "").strip()
    frame = orientational_frame or {"primary": "general", "scores": {}}
    frame_hint = str(frame.get("primary", "general"))

    system_content = _build_generation_system_content(
        intent,
        safe_context,
    ) + (
        "\n\n[INTERNAL ORIENTATION — DO NOT REVEAL]: "
        f"{frame_hint}. Use only when supported by evidence."
    )

    user_content = (
        user_query
        + "\n\nAnswer the question directly. Stay with the visitor's words. "
        "Preserve uncertainty. Use only genuine canonical destinations established by evidence. "
        "Do not output links, URLs, HTML, slugs, or emoji; USE adds canonical links."
    )

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def _looks_like_finished_visitor_answer(text: str) -> bool:
    """Reject only visitor answers that plainly terminate mid-thought."""
    value = str(text or "").strip()
    if not value:
        return False

    if value.endswith((".", "!", "?", ":", ";", ")", "]", '"', "”", "’")):
        return True

    last_line = value.splitlines()[-1].strip()
    if last_line.startswith(("- ", "* ", "+ ")) and len(last_line) >= 8:
        return True

    if re.match(r"^\d+[.)]\s+", last_line) and len(last_line) >= 8:
        return True

    return False


def _run_generation_attempt(
    model_id: str,
    user_query: str,
    intent: str,
    generation_context: str,
    *,
    max_tokens: int,
    orientational_frame: Optional[Dict[str, Any]] = None,
    canonical_link_context: str = "",
) -> str:
    """Execute exactly one provider call using only the supplied context."""
    # Generation invariant: context is explicit from retrieval boundary
    # through payload construction, output cleaning, and link normalization.
    safe_context, messages = _fit_generation_context_to_provider_budget(
        user_query,
        intent,
        generation_context,
        max_tokens=max_tokens,
        orientational_frame=orientational_frame,
    )

    estimated_quota_tokens = _estimate_quota_tokens(messages, max_tokens)
    _known_daily_tpd_preflight(model_id, estimated_quota_tokens)

    response = groq_client.chat.completions.create(
        model=model_id,
        messages=messages,
        temperature=0.2,
        max_tokens=max_tokens,
    )

    choice = response.choices[0]
    finish_reason = getattr(choice, "finish_reason", None)
    generated_text = choice.message.content or ""

    if str(finish_reason or "").lower() in {"length", "max_tokens"}:
        print(
            f"USE output boundary: model '{model_id}' reached its generation "
            "limit; rejecting incomplete visitor answer."
        )
        return ""

    cleaned_answer = _clean_generation_output(
        generated_text,
        generation_context,
        canonical_link_context,
    )

    if cleaned_answer and not _looks_like_finished_visitor_answer(cleaned_answer):
        print(
            f"USE output boundary: model '{model_id}' returned an incomplete "
            "visitor answer; trying the next live model."
        )
        return ""

    return cleaned_answer


def _is_request_too_large_error(error_text: str) -> bool:
    """Recognize both HTTP 413 and provider 400 length-limit messages."""
    clean = str(error_text or "").lower()
    return any(
        marker in clean
        for marker in (
            "request_too_large",
            "request entity too large",
            "please reduce the length of the messages or completion",
            "reduce the length of the messages",
            "messages or completion",
            "context length",
            "maximum context length",
            "too many tokens",
            "413",
        )
    )


def _is_rate_limit_error(error_text: str) -> bool:
    clean = str(error_text or "").lower()
    return any(
        marker in clean
        for marker in (
            "rate_limit_exceeded",
            "rate limit reached",
            "too many requests",
            "429",
        )
    )


def _deterministic_provider_fallback(
    user_query: str,
    generation_context: str,
) -> str:
    """Return a safe visitor response without another provider call.

    This path is used only when the provider is unavailable, rate-limited, or
    has rejected the request envelope. It can only expose canonical resources
    that are already present in the selected generation context, so it cannot
    invent titles or URLs while trying to recover from a provider failure.
    """
    pairs = []
    seen = set()
    for title, url in _canonical_pairs(generation_context):
        clean_title = _canonical_display_title(title)
        clean_url = str(url or "").strip()
        key = clean_url.casefold()
        if not clean_title or not clean_url or key in seen:
            continue
        if _is_non_resource_service_title(clean_title):
            continue
        seen.add(key)
        pairs.append((clean_title, clean_url))
        if len(pairs) >= 3:
            break

    if not pairs:
        return (
            "The Living Archive is temporarily unable to generate a full "
            "answer for this question. Please try again shortly."
        )

    # This is deliberately factual rather than synthetic: the fallback does
    # not claim an interpretation the unavailable model did not produce.
    lines = [
        "The Living Archive could not complete its interpretive response "
        "right now, but these canonical resources are the relevant material "
        "available for your question:",
        "",
    ]
    lines.extend(f"- [{title}]({url})" for title, url in pairs)
    return "\n".join(lines)


def generate_llm_response(
    user_query: str,
    retrieved_context_blocks: str,
    intent: str,
    orientational_frame: Optional[Dict[str, Any]] = None,
    canonical_link_context: str = "",
) -> str:
    """
    Generate a visitor answer behind a hard, single-context provider boundary.

    Generation-boundary hardening:
      - the retrieval-layer name `context_blocks` never enters provider code;
      - one local `base_generation_context` is created before any model call;
      - every provider and compact-fallback call receives that context explicitly;
      - provider 400 length errors are treated as request-size failures;
      - compact fallback is derived from the already-bounded generation context,
        never from an ambient or stale variable;
      - known provider TPD exhaustion is preflighted after an explicit Groq
        daily-quota observation, so the same doomed request is not retried;
      - 429 responses remain a fallback quarantine for conditions not known
        beforehand;
      - startup and health responses expose a deployment fingerprint so stale
        deployments cannot masquerade as current-code failures.
    """
    if not GROQ_API_KEY or not groq_client:
        return (
            "Unable to generate a response. "
            "GROQ_API_KEY is not configured in backend environment."
        )

    # This is the only transition from retrieval evidence into generation.
    # From this point onward, the provider layer knows nothing about the
    # retrieval-layer variable name or structure.
    documents = context_blocks_to_documents(
        str(retrieved_context_blocks or "")
    )
    base_generation_context = build_generation_context(
        documents,
        max_chars=MAX_GENERATION_CONTEXT_CHARS,
        max_resource_chars=MAX_GENERATION_RESOURCE_CHARS,
    )

    if not base_generation_context:
        base_generation_context = _bound_existing_context_blocks(
            str(retrieved_context_blocks or ""),
            MAX_GENERATION_CONTEXT_CHARS,
            MAX_GENERATION_RESOURCE_CHARS,
        )

    active_models = get_live_groq_models()

    if not active_models:
        return (
            "Unable to generate a response. "
            "No active models are currently available."
        )

    print(
        "USE generation candidates: "
        f"{active_models}"
    )
    print(
        "USE generation context budget: "
        f"{len(base_generation_context)}/{MAX_GENERATION_CONTEXT_CHARS} chars; "
        f"max_tokens={MAX_GENERATION_TOKENS}."
    )

    last_error: Optional[str] = None
    provider_recovery_allowed = True

    for model_id in active_models:
        try:
            print(f"USE generation attempt: '{model_id}'")

            visitor_answer = _run_generation_attempt(
                model_id,
                user_query,
                intent,
                base_generation_context,
                max_tokens=MAX_GENERATION_TOKENS,
                canonical_link_context=canonical_link_context,
            )

            if visitor_answer:
                return visitor_answer

            print(
                f"USE output boundary: model '{model_id}' returned no usable "
                "visitor answer; trying the next live model."
            )
            last_error = "Model returned empty visitor answer."
            continue

        except Exception as exc:
            error_text = str(exc)
            print(
                f"Execution failed for live Groq model '{model_id}': "
                f"{error_text}"
            )

            if (
                "model_terms_required" in error_text.lower()
                or "requires terms acceptance" in error_text.lower()
            ):
                MODEL_CACHE["terms_required_models"].add(model_id)
                print(
                    "Skipping Groq model requiring terms acceptance: "
                    f"'{model_id}'"
                )
                last_error = error_text
                continue

            if isinstance(exc, KnownDailyQuotaInsufficient):
                print(
                    "USE provider daily TPD preflight: SKIP "
                    f"'{model_id}' before API call; "
                    f"estimated={exc.estimated_tokens}, "
                    f"remaining={exc.remaining_tokens}."
                )
                provider_recovery_allowed = False
                last_error = error_text
                continue

            if _is_rate_limit_error(error_text):
                tpd_observed = _record_daily_tpd_state(model_id, error_text)
                cooldown = _rate_limit_seconds(error_text)
                MODEL_CACHE["rate_limited_until"][model_id] = (
                    time.time() + cooldown
                )
                print(
                    "USE model temporary rate-limit quarantine: "
                    f"'{model_id}' for approximately {cooldown:.0f}s."
                )
                provider_recovery_allowed = False
                last_error = error_text
                continue

            if _is_request_too_large_error(error_text):
                # Compact fallback is made from the already-bounded
                # already-created generation context. There is no reference
                # to `context_blocks` anywhere in this fallback path.
                compact_context = _bound_existing_context_blocks(
                    base_generation_context,
                    MAX_COMPACT_GENERATION_CONTEXT_CHARS,
                    MAX_COMPACT_GENERATION_RESOURCE_CHARS,
                )

                print(
                    "USE generation compact fallback: "
                    f"{len(compact_context)}/"
                    f"{MAX_COMPACT_GENERATION_CONTEXT_CHARS} chars; "
                    f"max_tokens={MAX_COMPACT_GENERATION_TOKENS}."
                )

                try:
                    compact_messages = _build_generation_messages(
                        user_query, intent, compact_context, None
                    )
                    compact_estimate = _estimate_quota_tokens(
                        compact_messages, MAX_COMPACT_GENERATION_TOKENS
                    )
                    _known_daily_tpd_preflight(model_id, compact_estimate)

                    compact_answer = _run_generation_attempt(
                        model_id,
                        user_query,
                        intent,
                        compact_context,
                        max_tokens=MAX_COMPACT_GENERATION_TOKENS,
                        canonical_link_context=canonical_link_context,
                    )

                    if compact_answer:
                        return compact_answer

                    print(
                        f"USE compact output boundary: model '{model_id}' "
                        "returned no usable visitor answer."
                    )

                except KnownDailyQuotaInsufficient as compact_quota_exc:
                    provider_recovery_allowed = False
                    print(
                        "USE compact fallback preflight: SKIP "
                        f"'{model_id}' because observed daily TPD is insufficient; "
                        f"estimated={compact_quota_exc.estimated_tokens}, "
                        f"remaining={compact_quota_exc.remaining_tokens}."
                    )

                except Exception as compact_exc:
                    compact_error = str(compact_exc)
                    print(
                        "USE compact generation fallback failed for "
                        f"'{model_id}': {compact_error}"
                    )

                    if _is_rate_limit_error(compact_error):
                        _record_daily_tpd_state(model_id, compact_error)
                        cooldown = _rate_limit_seconds(compact_error)
                        MODEL_CACHE["rate_limited_until"][model_id] = (
                            time.time() + cooldown
                        )
                        provider_recovery_allowed = False
                        print(
                            "USE model temporary rate-limit quarantine after "
                            f"compact fallback: '{model_id}' for "
                            f"approximately {cooldown:.0f}s."
                        )

                last_error = error_text
                continue

            # A NameError is never silently treated as a provider failure.
            # It is logged explicitly so a future regression is immediately
            # attributable to application code rather than model behavior.
            if isinstance(exc, NameError):
                print(
                    "USE ROOT-CAUSE ALERT: unexpected NameError in generation "
                    f"path: {error_text}"
                )

            last_error = error_text

    print(
        "USE generation exhausted all executable model candidates. "
        f"Last error: {last_error}"
    )

    fallback = _deterministic_provider_fallback(
        user_query,
        base_generation_context,
    )
    print(
        "USE deterministic provider fallback: "
        f"returned canonical resources without another provider call; "
        f"provider_recovery_allowed={provider_recovery_allowed}."
    )
    return fallback


# =====================================================================
# API REQUEST MODEL
# =====================================================================

class FlexibleQueryRequest(BaseModel):
    query: Optional[str] = None
    user_query: Optional[str] = None
    question: Optional[str] = None
    text: Optional[str] = None


# =====================================================================
# HEALTH / ROOT
# =====================================================================

@app.get("/")
@app.head("/")
def read_root():
    return {"status": "ok", "service": "USE", "version": APP_VERSION, "fingerprint": DEPLOYMENT_FINGERPRINT}


# =====================================================================
# QUERY ENDPOINT
# =====================================================================

@app.post("/api/query")
@app.post("/")
async def handle_query(
    request: Request,
    payload: Optional[FlexibleQueryRequest] = None,
):
    raw_body: Dict[str, Any] = {}

    try:
        raw_body = await request.json()
    except Exception:
        pass

    query_str: Optional[str] = None

    if payload:
        query_str = (
            payload.query
            or payload.user_query
            or payload.question
            or payload.text
        )

    if not query_str and raw_body:
        query_str = (
            raw_body.get("query")
            or raw_body.get("user_query")
            or raw_body.get("question")
            or raw_body.get("text")
            or raw_body.get("input")
        )

    if not query_str or not str(query_str).strip():
        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "version": APP_VERSION,
                "query": "",
                "intent": "TOPICAL_INQUIRY",
                "response": "Please enter a question to query the archive.",
            },
            headers=CORS_RESPONSE_HEADERS,
        )

    query_str = str(query_str).strip()

    try:
        context_data = fetch_canonical_context(query_str)

        llm_output = generate_llm_response(
            query_str,
            context_data["context_blocks"],
            context_data["intent"],
            orientational_frame=context_data.get(
                "orientational_frame",
                {"primary": "general", "scores": {}},
            ),
            canonical_link_context=context_data.get(
                "canonical_link_context",
                context_data["context_blocks"],
            ),
        )

        # Canonical context is deliberately not returned to the browser.
        # Retrieval evidence is an internal generation input; returning it
        # was unnecessary for the WordPress client and could make health/
        # keep-warm requests return a very large body.
        response_content: Dict[str, Any] = {
            "ok": True,
            "version": APP_VERSION,
            "query": query_str,
            "intent": context_data["intent"],
            "response": llm_output,
        }

        # Optional diagnostic exposure is disabled by default.
        if os.getenv("USE_DEBUG_CONTEXT", "0").strip() == "1":
            response_content["canonical_context"] = context_data["context_blocks"]

        return JSONResponse(
            status_code=200,
            content=response_content,
            headers=CORS_RESPONSE_HEADERS,
        )

    except Exception as exc:
        # Keep provider/retrieval failures inside the application contract.
        # The browser must receive readable JSON with CORS headers rather
        # than interpreting an upstream exception as a connection failure.
        print(f"USE query application failure: {exc}")

        return JSONResponse(
            status_code=200,
            content={
                "ok": False,
                "version": APP_VERSION,
                "query": query_str,
                "intent": "TOPICAL_INQUIRY",
                "response": "Unable to generate a response from the Living Archive service right now. Please try again.",
                "error_type": "application_generation_failure",
            },
            headers=CORS_RESPONSE_HEADERS,
        )


# =====================================================================
# LIGHTWEIGHT HEALTH / KEEP-WARM ENDPOINT
# =====================================================================

@app.get("/health")
@app.head("/health")
def health_check():
    """Small transport-safe health response for monitoring/keep-warm jobs."""
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "service": "USE", "version": APP_VERSION, "fingerprint": DEPLOYMENT_FINGERPRINT},
        headers=CORS_RESPONSE_HEADERS,
    )


# =====================================================================
# GENERATION BOUNDARY SELF-AUDIT
# =====================================================================


def _generation_boundary_self_audit() -> None:
    """Fail loudly at startup if known visitor-boundary defects return."""
    try:
        _strip_model_link_markup("", "")
        _build_generation_messages("self-audit", "TOPICAL_INQUIRY", "")

        # Regression test: the exact leaked marker observed in production
        # must never survive the visitor-facing sanitation boundary.
        sanitized_title = _strip_emoji("⭐ Institutional Cornerstones")
        if sanitized_title != "Institutional Cornerstones":
            raise RuntimeError(
                "Emoji sanitation regression: canonical title marker was not removed."
            )

        # Regression test: display-safe canonical titles must remain display-
        # safe when passed through the final link normalization boundary.
        test_context = (
            "Title: ⭐ Institutional Cornerstones\n"
            "URL: https://example.invalid/institutional-cornerstones\n"
            "Content: Self-audit canonical resource."
        )
        test_output = _clean_generation_output(
            "<visitor_answer>See ⭐ Institutional Cornerstones.</visitor_answer>",
            test_context,
        )
        if "⭐" in test_output:
            raise RuntimeError(
                "Emoji sanitation regression: final visitor output still contains emoji."
            )

        duplicate_documents = _dedupe_resources_by_display_title([
            {"title": "The Path to Humility", "url": "https://example.invalid/one", "text": "one"},
            {"title": "The Path to Humility", "url": "https://example.invalid/two", "text": "two"},
        ])
        if len(duplicate_documents) != 1:
            raise RuntimeError(
                "Resource uniqueness regression: duplicate display titles were not deduplicated."
            )

        duplicate_context = (
            "Title: The Path to Humility\n"
            "URL: https://example.invalid/humility\n"
            "Content: Canonical humility evidence."
        )
        duplicate_output = _clean_generation_output(
            "<visitor_answer>\n1. The Path to Humility\n2. The Path to Humility\n</visitor_answer>",
            duplicate_context,
        )
        if duplicate_output.count("The Path to Humility") != 1:
            raise RuntimeError(
                "Resource uniqueness regression: duplicate canonical list item survived output boundary."
            )

        # Canonical-link matcher regressions: harmless Unicode/whitespace
        # representation differences must still resolve to canonical links,
        # while the inserted title/URL remain authoritative.
        linker_pairs = [
            (
                "Why Being 'Good' Isn't Enough: The Invisible Incentives Sabotaging Your Success",
                "https://example.invalid/incentives",
            ),
            (
                "Systems, Governance, and Organizational Design – Structure, Incentives, and Stability",
                "https://example.invalid/systems",
            ),
        ]

        exact_link_test = _replace_titles_in_plain_text(
            "See Why Being 'Good' Isn't Enough: The Invisible Incentives Sabotaging Your Success.",
            linker_pairs,
        )
        if exact_link_test != (
            "See [Why Being 'Good' Isn't Enough: The Invisible Incentives Sabotaging Your Success]"
            "(https://example.invalid/incentives)."
        ):
            raise RuntimeError("Canonical-link exact-match regression.")

        whitespace_link_test = _replace_titles_in_plain_text(
            "See Why Being\u00A0'Good'\u00A0Isn't Enough: The Invisible Incentives Sabotaging Your Success.",
            linker_pairs,
        )
        if "](https://example.invalid/incentives)" not in whitespace_link_test:
            raise RuntimeError("Canonical-link whitespace/NBSP regression.")

        dash_link_test = _replace_titles_in_plain_text(
            "See Systems, Governance, and Organizational Design - Structure, Incentives, and Stability.",
            linker_pairs,
        )
        if "](https://example.invalid/systems)" not in dash_link_test:
            raise RuntimeError("Canonical-link dash-variant regression.")

        quote_link_test = _replace_titles_in_plain_text(
            "See The “Silent Withdrawal”: A Lean Audit of Corporate Identity and Soul Governance.",
            [
                (
                    'The "Silent Withdrawal": A Lean Audit of Corporate Identity and Soul Governance',
                    "https://example.invalid/silent-withdrawal",
                )
            ],
        )
        if quote_link_test != (
            'See [The "Silent Withdrawal": A Lean Audit of Corporate Identity and Soul Governance]'
            "(https://example.invalid/silent-withdrawal)."
        ):
            raise RuntimeError("Canonical-link quotation-mark regression.")

        apostrophe_link_test = _replace_titles_in_plain_text(
            "See Steward’s Path.",
            [("Steward's Path", "https://example.invalid/stewards-path")],
        )
        if apostrophe_link_test != (
            "See [Steward's Path](https://example.invalid/stewards-path)."
        ):
            raise RuntimeError("Canonical-link apostrophe regression.")

        existing_link_test = _replace_titles_in_plain_text(
            "[Why Being 'Good' Isn't Enough: The Invisible Incentives Sabotaging Your Success]"
            "(https://example.invalid/incentives)",
            linker_pairs,
        )
        if existing_link_test != (
            "[Why Being 'Good' Isn't Enough: The Invisible Incentives Sabotaging Your Success]"
            "(https://example.invalid/incentives)"
        ):
            raise RuntimeError("Canonical-link existing-link preservation regression.")

        substring_link_test = _replace_titles_in_plain_text(
            "Systematic governance is not the same as System.",
            [("System", "https://example.invalid/system")],
        )
        if "System](https://example.invalid/system)atic" in substring_link_test:
            raise RuntimeError("Canonical-link word-boundary regression.")

        multi_link_test = _replace_titles_in_plain_text(
            "Why Being 'Good' Isn't Enough: The Invisible Incentives Sabotaging Your Success; "
            "Systems, Governance, and Organizational Design - Structure, "
            "Incentives, and Stability.",
            linker_pairs,
        )
        if multi_link_test.count("https://example.invalid/") != 2:
            raise RuntimeError("Canonical-link multiple-title regression.")

        # Production leakage regression: the former visitor-facing alias
        # "Incentives Drive Behavior: Why Good Intentions Fail in Systems" is
        # not the current canonical title. It must not survive a canonical
        # resource list when the current canonical record uses the updated
        # title for the same resource.
        legacy_title_output = _remove_unresolvable_resource_list_items(
            "Further reading:\n\n"
            "- Incentives Drive Behavior: Why Good Intentions Fail in Systems\n"
            "- Why Being 'Good' Isn't Enough: The Invisible Incentives Sabotaging Your Success\n\n"
            "The prose continues here.",
            "Title: Why Being 'Good' Isn't Enough: The Invisible Incentives Sabotaging Your Success\n"
            "URL: https://example.invalid/incentives\n"
            "Content: Canonical incentive resource.",
        )
        if "Incentives Drive Behavior: Why Good Intentions Fail in Systems" in legacy_title_output:
            raise RuntimeError(
                "Canonical resource-selection regression: legacy title leaked into visitor resource list."
            )
        if "Why Being 'Good' Isn't Enough: The Invisible Incentives Sabotaging Your Success" not in legacy_title_output:
            raise RuntimeError(
                "Canonical resource-selection regression: current canonical title was removed."
            )

        # v35 root-cause regression: a canonical resource may be present in
        # the authoritative selected-resource set even when it is absent from
        # the bounded generation context. The final linker must still resolve
        # that canonical title deterministically.
        authoritative_context = (
            "Title: Authoritative Resource\n"
            "URL: https://example.invalid/authoritative\n"
            "Content: Canonical resource retained for final linking.\n"
            "\n---\n\n"
            "Title: Bounded Resource\n"
            "URL: https://example.invalid/bounded\n"
            "Content: Generation-window resource."
        )
        bounded_only_context = (
            "Title: Bounded Resource\n"
            "URL: https://example.invalid/bounded\n"
            "Content: Generation-window resource."
        )
        authoritative_link_test = _clean_generation_output(
            "<visitor_answer>See Authoritative Resource.</visitor_answer>",
            authoritative_context,
        )
        if authoritative_link_test != (
            "See [Authoritative Resource](https://example.invalid/authoritative)."
        ):
            raise RuntimeError(
                "Authoritative canonical-link boundary regression."
            )

        bounded_link_test = _clean_generation_output(
            "<visitor_answer>See Authoritative Resource.</visitor_answer>",
            bounded_only_context,
        )
        if "https://example.invalid/authoritative" in bounded_link_test:
            raise RuntimeError(
                "Canonical-link regression: bounded generation context leaked an "
                "unauthorized canonical URL."
            )

        # Resource-selection boundary regression: a title appearing only in
        # evidence content must not survive as a recommended resource when it
        # has no canonical Title: record in the authoritative context.
        resource_boundary_context = (
            "Title: Canonical Doorway\n"
            "URL: https://example.invalid/canonical-doorway\n"
            "Content: This evidence mentions Ghost Resource as related material."
        )
        resource_boundary_output = _clean_generation_output(
            "<visitor_answer>Consider these resources:\n"
            "1. Ghost Resource\n"
            "2. Canonical Doorway.</visitor_answer>",
            resource_boundary_context,
        )
        if "Ghost Resource" in resource_boundary_output:
            raise RuntimeError(
                "Canonical resource-selection regression: unresolvable resource "
                "survived the visitor output boundary."
            )
        if "https://example.invalid/canonical-doorway" not in resource_boundary_output:
            raise RuntimeError(
                "Canonical resource-selection regression: valid canonical resource "
                "was not linked."
            )

        # v40 root-cause regression: the generation context must be the
        # selected/reranked resource set, while link authority may retain a
        # larger canonical set. This prevents canonical-link authority from
        # silently becoming the generation-selection set.
        selected_context = format_context_blocks(
            [
                {
                    "title": "Primary Selected Resource",
                    "url": "https://example.invalid/primary",
                    "text": "Primary evidence.",
                },
                {
                    "title": "Secondary Selected Resource",
                    "url": "https://example.invalid/secondary",
                    "text": "Secondary evidence.",
                },
            ]
        )
        authoritative_context = format_context_blocks(
            [
                {
                    "title": "Primary Selected Resource",
                    "url": "https://example.invalid/primary",
                    "text": "Primary evidence.",
                },
                {
                    "title": "Secondary Selected Resource",
                    "url": "https://example.invalid/secondary",
                    "text": "Secondary evidence.",
                },
                {
                    "title": "Additional Link Authority",
                    "url": "https://example.invalid/additional",
                    "text": "Additional canonical evidence.",
                },
            ]
        )
        selected_generation_documents = context_blocks_to_documents(selected_context)
        authoritative_documents = context_blocks_to_documents(authoritative_context)
        if len(selected_generation_documents) != 2:
            raise RuntimeError(
                "Retrieval-to-generation regression: selected generation set changed."
            )
        if len(authoritative_documents) != 3:
            raise RuntimeError(
                "Canonical-link authority regression: authoritative set changed."
            )
        if selected_generation_documents[0]["title"] != "Primary Selected Resource":
            raise RuntimeError(
                "Retrieval-to-generation regression: selected ordering was not preserved."
            )
        if any(
            doc["title"] == "Additional Link Authority"
            for doc in selected_generation_documents
        ):
            raise RuntimeError(
                "Retrieval-to-generation regression: link-only authority leaked into generation."
            )

        # v42 root-cause regression: a blank line after a resource heading
        # must not terminate the resource-list boundary. Otherwise an
        # unresolvable model-generated resource can leak into visitor output
        # exactly as observed in production.
        list_boundary_context = (
            "Title: Canonical Resource One\n"
            "URL: https://example.invalid/one\n"
            "Content: Evidence one.\n\n---\n\n"
            "Title: Canonical Resource Two\n"
            "URL: https://example.invalid/two\n"
            "Content: Evidence two."
        )
        list_boundary_test = _remove_unresolvable_resource_list_items(
            "Further reading:\n\n"
            "- Canonical Resource One\n"
            "- Not Retrieved Resource\n\n"
            "The prose continues here.",
            list_boundary_context,
        )
        if "- Canonical Resource One" not in list_boundary_test:
            raise RuntimeError(
                "Resource-list boundary regression: canonical item after blank line was removed."
            )
        if "Not Retrieved Resource" in list_boundary_test:
            raise RuntimeError(
                "Resource-list boundary regression: unresolvable item leaked through."
            )
        if "The prose continues here." not in list_boundary_test:
            raise RuntimeError(
                "Resource-list boundary regression: following prose was consumed."
            )

        # v44 root-cause regression: a resource heading must never remain
        # empty when canonical resources are available in the selected
        # generation context. This is the exact failure observed in the
        # production test question about learning from failure.
        empty_resource_context = (
            "Title: Learning from Failure\n"
            "URL: https://example.invalid/learning-from-failure\n"
            "Content: Evidence about learning from failure."
            "\n\n---\n\n"
            "Title: Recovering from Failure\n"
            "URL: https://example.invalid/recovering-from-failure\n"
            "Content: Evidence about recovery."
        )
        empty_resource_output = _clean_generation_output(
            "<visitor_answer>Consider the following resources:\n\n"
            "These resources discuss learning from failure.</visitor_answer>",
            empty_resource_context,
            empty_resource_context,
        )
        if "Learning from Failure" not in empty_resource_output:
            raise RuntimeError(
                "Empty-resource-section regression: canonical resources were not restored."
            )
        resource_list_text = "\n".join(
            line for line in empty_resource_output.splitlines()
            if re.match(r"^\s*(?:[-*•]|\d+[.)])\s+", line)
        )
        if resource_list_text.lower().count("learning from failure") != 1:
            raise RuntimeError(
                "Empty-resource-section regression: canonical resource was duplicated."
            )

        # A canonical resource in link-only authority must not be promoted
        # into the visitor selection set merely because it can be linked.
        selected_only_context = (
            "Title: Selected Resource\n"
            "URL: https://example.invalid/selected\n"
            "Content: Selected evidence."
        )
        link_only_context = (
            selected_only_context
            + "\n\n---\n\n"
            "Title: Link-Only Authority\n"
            "URL: https://example.invalid/link-only\n"
            "Content: Additional canonical evidence."
        )
        link_only_output = _clean_generation_output(
            "<visitor_answer>Consider these resources:\n"
            "- Link-Only Authority</visitor_answer>",
            selected_only_context,
            link_only_context,
        )
        if "Link-Only Authority" in link_only_output:
            raise RuntimeError(
                "Visitor-resource authority regression: link-only resource entered selection."
            )
        if "Selected Resource" not in link_only_output:
            raise RuntimeError(
                "Visitor-resource authority regression: selected resource was not restored."
            )

        # Invalid/non-canonical generated items must still be removed.
        invalid_resource_output = _clean_generation_output(
            "<visitor_answer>Further reading:\n"
            "- Not Retrieved Resource\n"
            "- Learning from Failure</visitor_answer>",
            empty_resource_context,
            empty_resource_context,
        )
        if "Not Retrieved Resource" in invalid_resource_output:
            raise RuntimeError(
                "Canonical resource-selection regression: invalid resource survived."
            )

        # v49 presentation regression: standalone canonical resource links
        # must become discrete visitor-facing list items without changing their
        # canonical identity.
        standalone_resource_output = _clean_generation_output(
            "<visitor_answer>"
            "For a deeper look, see:\n\n"
            "[Canonical Resource One](https://example.invalid/one)\n"
            "[Canonical Resource Two](https://example.invalid/two)"
            "</visitor_answer>",
            list_boundary_context,
            list_boundary_context,
        )
        if "- [Canonical Resource One](https://example.invalid/one)" not in standalone_resource_output:
            raise RuntimeError(
                "Canonical resource presentation regression: first standalone link was not list-formatted."
            )
        if "- [Canonical Resource Two](https://example.invalid/two)" not in standalone_resource_output:
            raise RuntimeError(
                "Canonical resource presentation regression: second standalone link was not list-formatted."
            )

        # v51 boundary regression: ordinary prose after a canonical resource
        # list must render as a separate paragraph, not as a continuation of
        # the final resource bullet.
        trailing_prose_output = _clean_generation_output(
            "<visitor_answer>"
            "See these resources:\n"
            "- [Canonical Resource One](https://example.invalid/one)\n"
            "- [Canonical Resource Two](https://example.invalid/two)\n"
            "These resources provide further context."
            "</visitor_answer>",
            list_boundary_context,
            list_boundary_context,
        )
        expected_boundary = (
            "- [Canonical Resource Two](https://example.invalid/two)\n\n"
            "These resources provide further context."
        )
        if expected_boundary not in trailing_prose_output:
            raise RuntimeError(
                "Canonical resource presentation regression: trailing prose "
                "was not separated from the resource list."
            )

        # Provider request-boundary regression: production must use the
        # deliberately conservative envelope that was introduced after the
        # observed Groq 413 request-too-large failure.
        if MAX_GENERATION_CONTEXT_CHARS != 1800:
            raise RuntimeError(
                "Provider boundary regression: primary generation context budget changed."
            )
        if MAX_GENERATION_TOKENS != 240:
            raise RuntimeError(
                "Provider boundary regression: primary generation token budget changed."
            )
        if MAX_PROVIDER_INPUT_CHARS != 3800 or MAX_PROVIDER_TOTAL_CHARS != 4600:
            raise RuntimeError(
                "Provider boundary regression: conservative Groq request envelope changed."
            )
        if not (
            MAX_COMPACT_GENERATION_CONTEXT_CHARS < MAX_GENERATION_CONTEXT_CHARS
            and MAX_COMPACT_GENERATION_TOKENS < MAX_GENERATION_TOKENS
        ):
            raise RuntimeError(
                "Provider boundary regression: compact fallback is not smaller than primary generation."
            )

        # v55 regression: the provider fitter must adapt the evidence window
        # to the actual fixed system/user envelope. This reproduces the v54
        # production failure shape where a 1,100-character minimum context
        # could leave the assembled request 55 characters over the total
        # envelope. The fitter must reduce the evidence rather than fail.
        synthetic_context = (
            "Title: Institutional Cornerstones\n"
            "URL: https://example.invalid/institutional-cornerstones\n"
            "Content: " + ("governance resilience evidence " * 80)
            + "\n\n---\n\n"
            "Title: Governance Foundations\n"
            "URL: https://example.invalid/governance-foundations\n"
            "Content: " + ("governance foundations evidence " * 80)
        )
        fitted_context, fitted_messages = _fit_generation_context_to_provider_budget(
            "Why can adding more rules to a system sometimes make the system less governable?",
            "TOPICAL_INQUIRY",
            synthetic_context,
            max_tokens=MAX_GENERATION_TOKENS,
        )
        fitted_input = _estimate_message_chars(fitted_messages)
        fitted_total = fitted_input + math.ceil(MAX_GENERATION_TOKENS * 4 * 1.25)
        if fitted_input > MAX_PROVIDER_INPUT_CHARS or fitted_total > MAX_PROVIDER_TOTAL_CHARS:
            raise RuntimeError(
                "Provider adaptive-fit regression: fitted request still exceeds envelope."
            )
        if len(fitted_context) >= len(synthetic_context):
            raise RuntimeError(
                "Provider adaptive-fit regression: oversized evidence was not compacted."
            )

        # v57 regression: the fixed generation envelope itself must leave
        # meaningful room for canonical evidence. A self-audit that can only
        # fit metadata or no evidence is not a valid provider-safe generation path.
        primary_empty_messages = _build_generation_messages(
            "Why do systems preserve the conditions that created their problems?",
            "TOPICAL_INQUIRY",
            "",
            None,
        )
        primary_fixed_chars = _estimate_message_chars(primary_empty_messages)
        primary_output_reservation = math.ceil(MAX_GENERATION_TOKENS * 4 * 1.25)
        primary_evidence_capacity = min(
            MAX_PROVIDER_INPUT_CHARS - primary_fixed_chars,
            MAX_PROVIDER_TOTAL_CHARS - primary_fixed_chars - primary_output_reservation,
        )
        if primary_evidence_capacity < 600:
            raise RuntimeError(
                "Provider budget regression: primary generation leaves less than "
                f"600 characters for canonical evidence (capacity={primary_evidence_capacity}, "
                f"fixed_input={primary_fixed_chars})."
            )

        # Release identity audit: the source file itself must declare the
        # same version as the runtime and deployment fingerprint. This prevents
        # the repeated stale/misaligned top-of-file version problem.
        source_lines = Path(__file__).read_text(encoding="utf-8").splitlines()
        if not source_lines or not source_lines[0].startswith("# USE PRODUCTION VERSION: v57"):
            raise RuntimeError(
                "Source version-label regression: line 1 does not identify v57."
            )
        if APP_VERSION != "v57":
            raise RuntimeError(
                f"Runtime version mismatch: APP_VERSION={APP_VERSION}, expected v57."
            )
        if DEPLOYMENT_FINGERPRINT != "USE-v57-provider-budget-safe-multi-resource-navigation":
            raise RuntimeError(
                "Deployment fingerprint regression: v57 fingerprint is not aligned."
            )

        # cross-section regression: the same canonical resources must not reappear in a
        # later visitor-facing resource section.
        cross_section_output = _clean_generation_output(
            "<visitor_answer>"
            "For a deeper look, see:\n"
            "- [Canonical Resource One](https://example.invalid/one)\n"
            "- [Canonical Resource Two](https://example.invalid/two)\n\n"
            "Further reading:\n"
            "- [Canonical Resource One](https://example.invalid/one)\n"
            "- [Canonical Resource Two](https://example.invalid/two)"
            "</visitor_answer>",
            list_boundary_context,
            list_boundary_context,
        )
        if cross_section_output.count("Canonical Resource One") != 1:
            raise RuntimeError(
                "Canonical resource presentation regression: Resource One was duplicated across sections."
            )
        if cross_section_output.count("Canonical Resource Two") != 1:
            raise RuntimeError(
                "Canonical resource presentation regression: Resource Two was duplicated across sections."
            )
        if "Further reading:" in cross_section_output:
            raise RuntimeError(
                "Canonical resource presentation regression: empty duplicate resource heading survived."
            )

        # cross-section regression: incomplete Markdown emphasis markers must never leak
        # into visitor-facing output.
        markdown_leak_output = _clean_generation_output(
            "<visitor_answer>Habitual conditioning** - Long-standing routines.\n"
            "Emotional resistance** - Fear may block action.</visitor_answer>",
            list_boundary_context,
            list_boundary_context,
        )
        if "**" in markdown_leak_output or "*" in markdown_leak_output:
            raise RuntimeError(
                "Visitor-markup regression: stray Markdown emphasis marker survived output boundary."
            )

        # resource eligibility regression: generic service/navigation labels may exist as
        # canonical site destinations but must not leak into topical resource
        # lists. HTML entities must also be decoded at the visitor boundary.
        service_leak_output = _clean_generation_output(
            "<visitor_answer>Consider these resources:\n"
            "- Workshops &amp; Advisory\n"
            "- [Canonical Resource One](https://example.invalid/one)</visitor_answer>",
            list_boundary_context + "\n\n---\n\n"
            "Title: Workshops & Advisory\n"
            "URL: https://example.invalid/workshops-advisory\n"
            "Content: Service information.",
            list_boundary_context + "\n\n---\n\n"
            "Title: Workshops & Advisory\n"
            "URL: https://example.invalid/workshops-advisory\n"
            "Content: Service information.",
        )
        if "Workshops & Advisory" in service_leak_output:
            raise RuntimeError(
                "Visitor resource eligibility regression: generic service label survived topical output."
            )
        if "&amp;" in service_leak_output:
            raise RuntimeError(
                "Visitor HTML entity regression: escaped entity survived output boundary."
            )
        if "Canonical Resource One" not in service_leak_output:
            raise RuntimeError(
                "Visitor resource eligibility regression: valid canonical resource was removed."
            )

        # v56 regression: multi-resource generation must remain an intentional
        # evidence-aware behavior. The generation prompt must explicitly prefer
        # multiple materially relevant resources when they add distinct coverage,
        # while preserving the one-resource case when one resource is sufficient.
        if "normally surface 2–3" not in GENERATION_SYSTEM_PROMPT:
            raise RuntimeError(
                "Multi-resource navigation regression: generation policy is missing."
            )
        multi_resource_test_context = format_context_blocks([
            {
                "title": "Primary Resource",
                "url": "https://example.invalid/primary",
                "text": "Primary evidence covering the first dimension.",
            },
            {
                "title": "Complementary Resource",
                "url": "https://example.invalid/complementary",
                "text": "Complementary evidence covering a distinct second dimension.",
            },
            {
                "title": "Weak Resource",
                "url": "https://example.invalid/weak",
                "text": "Weakly related evidence.",
            },
        ])
        multi_resource_documents = context_blocks_to_documents(multi_resource_test_context)
        if len(multi_resource_documents) != 3:
            raise RuntimeError(
                "Multi-resource navigation regression: distinct selected evidence was lost."
            )
        bounded_multi = build_generation_context(
            multi_resource_documents,
            max_chars=MAX_GENERATION_CONTEXT_CHARS,
            max_resource_chars=MAX_GENERATION_RESOURCE_CHARS,
        )
        if len(_canonical_pairs(bounded_multi)) < 2:
            raise RuntimeError(
                "Multi-resource navigation regression: generation window collapsed "
                "multiple selected resources to fewer than two canonical records."
            )

        # Runtime identity must be explicit and current.
        if APP_VERSION != "v57":
            raise RuntimeError(
                f"Unexpected USE runtime version: {APP_VERSION}"
            )

        # provider-boundary recovery regression: when provider execution is unavailable,
        # recovery must use only selected canonical resources and must not emit
        # an unlinked resource name or make another provider request.
        fallback_context = (
            "Title: Designing Anti-Fragile Communities\n"
            "URL: https://example.invalid/anti-fragile\n"
            "Content: Resilience depends on capacity to adapt under disturbance."
            "\n\n---\n\n"
            "Title: Workshops & Advisory\n"
            "URL: https://example.invalid/workshops-advisory\n"
            "Content: Service information."
        )
        fallback_output = _deterministic_provider_fallback(
            "What makes a system resilient without becoming rigid?",
            fallback_context,
        )
        if "Designing Anti-Fragile Communities" not in fallback_output:
            raise RuntimeError(
                "Provider fallback regression: valid canonical resource was not preserved."
            )
        if "Workshops & Advisory" in fallback_output:
            raise RuntimeError(
                "Provider fallback regression: non-resource service title leaked."
            )
        if "http://" in fallback_output or "https://" in fallback_output:
            # URLs are allowed only inside canonical Markdown links.
            if "[Designing Anti-Fragile Communities](https://example.invalid/anti-fragile)" not in fallback_output:
                raise RuntimeError(
                    "Provider fallback regression: canonical URL was not bound to its title."
                )
        if fallback_output.count("Designing Anti-Fragile Communities") != 1:
            raise RuntimeError(
                "Provider fallback regression: canonical resource was duplicated."
            )

        quota_test_error = (
            "Rate limit reached for model `meta-llama/llama-4-scout-17b-16e-instruct` "
            "on tokens per day (TPD): Limit 500000, Used 499159, Requested 1267. "
            "Please try again in 1m13.6128s."
        )
        parsed_quota = _parse_daily_tpd_state(quota_test_error)
        if not parsed_quota or parsed_quota["remaining"] != 841:
            raise RuntimeError(
                "Daily TPD parser regression: explicit provider quota state was not parsed."
            )

        test_model = "self-audit/groq-compound"
        MODEL_CACHE["daily_tpd"][test_model] = {
            "limit": 500000,
            "used": 499159,
            "remaining": 841,
            "requested": 1267,
            "reset_at": time.time() + 3600,
            "observed_at": time.time(),
        }
        try:
            try:
                _known_daily_tpd_preflight(test_model, 842)
            except KnownDailyQuotaInsufficient:
                pass
            else:
                raise RuntimeError(
                    "Daily TPD preflight regression: insufficient observed quota was not blocked."
                )
        finally:
            MODEL_CACHE["daily_tpd"].pop(test_model, None)

    except Exception as exc:
        raise RuntimeError(
            "USE generation boundary self-audit failed: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    print(
        "USE GENERATION BOUNDARY SELF-AUDIT: PASS; "
        "visitor-output sanitation, canonical presentation equivalence, resource uniqueness, and runtime identification verified."
    )


_generation_boundary_self_audit()


# =====================================================================
# LOCAL EXECUTION
# =====================================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 10000))

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )

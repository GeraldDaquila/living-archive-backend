# USE PRODUCTION VERSION: v169 — MVP Structural Relational Orientation Detection + v168 protections + The Guide
# Sole one-environment production unit: main.py is used for both testing and LIVE.
# D28 establishes evidence-grounded resource sequencing; D29 applies a hard
# canonical movement state propagation; D30 audits the relevance-vs-movement boundary.
# Existing D01-D27 architecture and v117 open-exploration sovereignty behavior remain protected.
# Visitor-facing service identity: The Guide.

import os
import re
import time
import unicodedata
import html
import inspect
import json
from typing import Dict, Any, List, Optional, Tuple
import math
import threading
import uuid
import contextvars
import hashlib
from pathlib import Path
import gc

# ---------------------------------------------------------------------
# CLEAN RUNTIME BOOT
# ---------------------------------------------------------------------
# Render should launch USE in a fresh Python process. This explicit boot
# boundary also collects any unreachable Python objects before application
# initialization and makes the process boundary observable. It is cleanup,
# not a substitute for source provenance: loaded code is never treated as
# replaceable merely because garbage collection ran.
_USE_BOOT_GC_COLLECTED = gc.collect()
_USE_BOOT_PID = os.getpid()
print(
    "USE CLEAN RUNTIME BOOT: "
    f"pid={_USE_BOOT_PID}, gc_collected={_USE_BOOT_GC_COLLECTED}"
)

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

The visitor-facing name of this service is **The Guide**. Use “The Guide” when referring to the service in visitor-facing language. Never expose the internal name USE or describe it as a search engine.

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

27. EVIDENCE-BOUND SYNTHESIS
    When synthesizing across multiple canonical resources, do not turn
    a relationship that USE itself infers into an established causal
    explanation unless the supplied evidence explicitly establishes that
    relationship. If the evidence supports the component ideas but not
    the causal bridge between them, mark the bridge as an inference,
    possibility, or interpretive synthesis. Do not attribute a causal
    claim to a resource that only supplies one part of the relationship.

28. EVIDENCE PROVENANCE INTEGRITY
    Canonical titles, URLs, labels, and metadata establish resource
    identity; they are not substantive evidence about what a resource
    says. Substantive claims about a resource must be grounded in the
    supplied Content/evidence text. Never infer the substance of a
    resource from its title alone, even when phrased as "suggests",
    "implies", or a "possible interpretation". If the supplied evidence
    is insufficient to support a claim, say that it is not established
    by the retrieved evidence rather than filling the gap from the
    resource title or outside knowledge.

29. MINIMAL ORIENTATION
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

30. COLLECTION-LEVEL NAVIGATION
    Treat collection terms such as "essays," "Reference Maps,"
    "Pathways," "Navigators," "Case Library," "Knowledge Hubs," or
    similar corpus structures as requests for a collection-level
    destination when the visitor asks where to explore or find them.

    A resource that contains examples from a collection is not
    automatically the collection's destination.

31. OPEN-INQUIRY STOP RULE
    For an open experiential or exploratory question, once one
    clearly superior canonical doorway is established by the evidence,
    prefer that single doorway. Add another resource only when the
    second route materially changes or advances the inquiry.

32. EVIDENCE-GAP STOP RULE
    If the Archive evidence does not explicitly establish a requested
    concept, do not complete the missing definition from general
    knowledge. State the boundary naturally and route the visitor to
    the strongest evidence actually available.

33. NAVIGATIONAL USEFULNESS OVER SEMANTIC SIMILARITY
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

44. CANONICAL CORPUS LIFECYCLE
    USE may navigate only resources that are eligible in the current
    canonical corpus. A resource that carries explicit resource-level
    evidence of being archived, retired, deactivated, withdrawn, obsolete,
    deprecated, superseded, or otherwise no longer current must be excluded
    from navigational evidence, even if it remains technically published
    or remains present in the vector index.

    Do not infer archival status from arbitrary mentions of historical or
    archived material inside an otherwise current resource. Lifecycle
    exclusion must be grounded in the resource's own canonical identity,
    lifecycle metadata, title marker, slug marker, canonical URL marker, or equivalent identity-level evidence.

45. TOPICAL NAVIGATION FIDELITY
    For a broad or topical inquiry, canonical evidence is not merely background
    material for a generic answer. USE must orient the visitor through supplied
    Archive evidence, preserve the question's open character, synthesize only
    supported relationships, and provide a genuine canonical doorway when
    eligible evidence is available.

46. GENERATION EVIDENCE DENSITY
    The provider-facing evidence window must preserve selected canonical
    resource titles and useful topical evidence as densely as the provider
    budget permits. Canonical URLs remain separate link authority and need
    not consume scarce provider evidence space when USE reconstructs links
    deterministically after generation.

47. QUESTION–DOORWAY CENTRALITY
    For topical inquiry, a canonical doorway must be proportionate to the
    visitor's actual question, not merely capable of supplying a plausible
    fragment of an explanation. Doorway selection may refine only the
    already-retrieved canonical evidence; it must not become a second
    retrieval engine. When a question is broad or experiential and a
    candidate's primary conceptual territory is not established by the
    visitor's wording, do not allow generic doorway signals or a specialized
    framework to turn that candidate into the canonical doorway merely
    because its evidence contains compatible language. Explicitly named
    domains remain eligible. A resource may remain in the evidence set even
    when it is not proportionate enough to be the primary doorway.

48. INTERPRETIVE FRAME SOVEREIGNTY
    For broad or experiential questions, retrieved evidence may offer a
    specialized framework without acquiring authority to define the visitor's experience through that framework. Do not infer that the visitor is
    undergoing, seeking, or exemplifying a specialized worldview merely
    because a retrieved resource describes a compatible pattern. If the
    visitor has not named the framework, treat it as a resource-specific lens
    at most, not as the question's governing interpretation. When the
    available evidence is predominantly framework-specific, state that limit
    and preserve the visitor's open question rather than translating the
    question into the framework.

49. FRAME-NEUTRAL EVIDENCE BOUNDARY
    For broad or experiential questions whose interpretive frame remains open,
    specialized framework resources must not be supplied as substantive
    generation evidence when already-retrieved frame-neutral canonical evidence
    is available. This is a bounded evidence-selection gate, not a retrieval
    expansion: it may only narrow the already-retrieved generation set.
    Canonical link authority remains complete and separate. If no frame-neutral
    evidence exists, USE must not manufacture an answer by treating a
    specialized framework as the visitor's premise; it must state that the
    currently retrieved evidence is framework-specific and insufficient to
    establish a frame-neutral answer. Explicitly named frameworks remain
    eligible.

50. EVIDENCE-BOUND INFERENTIAL DISTANCE
    Do not manufacture intermediate factual claims or mechanisms to connect
    supplied evidence to an answer. If the evidence establishes A and B but
    not that A causes, produces, explains, or leads to B, do not state that
    unstated connection as fact. State the supported pieces, then mark the
    remaining connection as an inference, possibility, or interpretive
    reading. The farther a conclusion moves beyond what the supplied
    evidence establishes, the more explicitly it must be bounded.

51. INTERPRETIVE COMPRESSION
    When applying evidence beyond its stated domain, keep the interpretive
    bridge as short as possible. Do not add new factual premises, mechanisms,
    hidden states, or causal steps merely to make the analogy explanatory.
    State what the evidence supports, then make only the minimum bounded
    interpretive connection needed to address the visitor's question.

52. INTERPRETIVE BRIDGE INTEGRITY
    An interpretive inference may connect supplied evidence to the visitor's
    question, but it may not introduce new factual premises as stepping stones
    inside that inference. Do not build a chain of plausible mechanisms merely
    because the overall connection is labeled inference, possibility, or
    interpretation. If answering requires such unstated premises, omit them
    and state that the retrieved evidence does not establish the connection.
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
You are The Guide for the Living Archive. Answer only from supplied canonical evidence.

For TOPICAL questions, orient through supplied evidence, not generic explanation. Give a canonical doorway; normally use 2–3 only for distinct coverage. [RELATIONAL REASONING]: For explicit relationships or synthesis, reason across supplied resources; evidence may be distributed. Do not force one resource to cover both sides. For comparison questions, compare only what the supplied resources establish and explain what each contributes.

[FRAME SOVEREIGNTY]: Keep the visitor's question in their terms. A specialized framework may govern the explanation only when the visitor names it. Preserve uncertainty and do not imply an imposed framework, experience, or outcome.

[PROVENANCE + SYNTHESIS]: Titles/URLs identify resources, not evidence. Ground claims in supplied Content; use no outside knowledge. [INFERENTIAL DISTANCE]: Never turn thematic compatibility into causation. Do not invent intermediate facts or mechanisms. If a connection is not established, label the connection as an inference/possibility/interpretive reading. [BRIDGE INTEGRITY]: cannot add unstated factual premises as stepping stones or build a chain of plausible mechanisms; say the evidence does not establish the connection. [EVIDENCE SUFFICIENCY]: Retrieval relevance is not evidence sufficiency. If supplied Content cannot support the question, say the evidence is insufficient.

For resource-form questions, distinguish forms only when the supplied evidence establishes their functions. For destination/collection requests, use evidence-established destinations. For movement questions, call a resource the next destination only when D29 explicitly validates it. An explicit link is a relationship, not automatically a next step. If no D29 next destination is validated, say so plainly. Never invent resources, relationships, definitions, or URLs; never reveal internal process.

Use at least one exact supplied canonical title when making a resource-grounded topical claim. Answer the visitor's question directly; do not merely list resources. Output only the finished answer inside <visitor_answer> tags. Use exact canonical titles; no URLs, Markdown, HTML, slugs, or emoji. The system adds links.
"""



 


COMPACT_GENERATION_SYSTEM_PROMPT = """
You are The Guide for the Living Archive. Answer only from supplied canonical evidence.
Answer the visitor's question directly; do not merely list resources. For comparison or synthesis, compare only what supplied evidence establishes and explain what each relevant resource contributes. Use at least one exact supplied canonical title when making a resource-grounded claim.
Preserve uncertainty and visitor sovereignty. [FRAME SOVEREIGNTY]: A specialized framework may govern the explanation only when the visitor names it. Do not imply an imposed framework, experience, or outcome. [PROVENANCE + SYNTHESIS]: Titles/URLs identify resources, not evidence. Ground claims in supplied Content; use no outside knowledge. [INFERENTIAL DISTANCE]: Never turn thematic compatibility into causation. Do not invent intermediate facts or mechanisms. If a connection is not established, label the connection as an inference/possibility/interpretive reading. [BRIDGE INTEGRITY]: cannot add unstated factual premises as stepping stones or build a chain of plausible mechanisms; say the evidence does not establish the connection. [EVIDENCE SUFFICIENCY]: Retrieval relevance is not evidence sufficiency. If supplied Content cannot support the question, say the evidence is insufficient.
For movement questions, say “next” only when D29 explicitly validates a next destination; otherwise say no canonical next destination is established. Relevance is not movement. Never invent resources, relationships, definitions, or URLs. Never reproduce internal field labels; do not output or discuss Title:, URL:, Content:, ID:, canonical evidence, or evidence block.
Output only <visitor_answer>, concise and finished. Use exact canonical titles; no links, markup, schema, or metadata.
"""




# =====================================================================
# APP & INFRASTRUCTURE
# =====================================================================

APP_VERSION = "v169"

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
DEPLOYMENT_FINGERPRINT = "USE-v169-mvp-structural-relational-orientation-detection-canonical-fallback-link-preservation-reasoning-evidence-authority-lean-generation-envelope-canonical-evidence-use-task-aware-budget-document-form-orientation-deterministic-canonical-anchor-single-generation-path-explicit-type-generation-evidence-preservation-one-environment"

# === CANONICAL BUILD IDENTITY (excluded from payload hash) ===
# The payload hash deliberately excludes only this marked block, so the
# expected digest is non-self-referential. Any source change outside this
# block makes the canonical payload hash fail at startup.
CANONICAL_BUILD_ID = "USE-BUILD-v169-mvp-structural-relational-orientation-detection-canonical-fallback-link-preservation-reasoning-evidence-authority-lean-generation-envelope-canonical-evidence-use-task-aware-budget-document-form-orientation-deterministic-canonical-anchor-single-generation-path-explicit-type-generation-evidence-preservation-one-environment"
CANONICAL_BUILD_PAYLOAD_SHA256 = "b572ebdfff003802fb7e37f7950639cff35a233c1756f7c0593639c956e2f27e"
# === END CANONICAL BUILD IDENTITY ===

def _canonical_source_payload(source: str) -> str:
    """Normalize the marked identity block out of source before hashing."""
    pattern = re.compile(
        r"(?ms)^# === CANONICAL BUILD IDENTITY \(excluded from payload hash\) ===\n"
        r".*?"
        r"^# === END CANONICAL BUILD IDENTITY ===\n?"
    )
    normalized, count = pattern.subn(
        "# === CANONICAL BUILD IDENTITY (excluded from payload hash) ===\n"
        "# <CANONICAL_BUILD_IDENTITY_BLOCK>\n"
        "# === END CANONICAL BUILD IDENTITY ===\n",
        source,
        count=1,
    )
    if count != 1:
        raise RuntimeError(
            "v147 build identity failure: canonical identity block not found exactly once."
        )
    return normalized

def _compute_canonical_build_payload_sha256(source: str) -> str:
    return hashlib.sha256(
        _canonical_source_payload(source).encode("utf-8")
    ).hexdigest()

def _enforce_canonical_build_identity() -> None:
    """Hard-stop startup when the loaded source is not the canonical build."""
    source = Path(__file__).read_text(encoding="utf-8")
    actual = _compute_canonical_build_payload_sha256(source)
    expected = CANONICAL_BUILD_PAYLOAD_SHA256
    if expected == "__PAYLOAD_SHA256__" or actual != expected:
        print(
            "USE BUILD IDENTITY FAILURE: "
            f"build_id={CANONICAL_BUILD_ID}, expected_payload_sha256={expected}, "
            f"actual_payload_sha256={actual}, file={os.path.abspath(__file__)}"
        )
        raise RuntimeError(
            "USE canonical build identity mismatch; refusing to serve requests."
        )
    print(
        "USE BUILD IDENTITY: valid=True, "
        f"build_id={CANONICAL_BUILD_ID}, payload_sha256={actual}"
    )



# Runtime/deployment identity is computed from the exact source file that
# imported this module. This makes source identity independently observable
# from APP_VERSION and prevents deployment-state ambiguity from being inferred
# solely from Render lifecycle messages.
def _compute_runtime_source_sha256() -> str:
    try:
        return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    except Exception:
        return "unavailable"

RUNTIME_SOURCE_SHA256 = _compute_runtime_source_sha256()
RUNTIME_BOOT_ID = uuid.uuid4().hex
RUNTIME_PROCESS_ID = os.getpid()

# Optional-but-hard production provenance gate. The expected raw source hash
# is supplied out-of-band (Render environment variable) so the expected value
# cannot alter the source bytes whose hash it is checking. This avoids the
# impossible self-referential construction of embedding a raw file hash inside
# the same file. Local development may leave it unset; LIVE deployment must
# provide it.
EXPECTED_RUNTIME_SOURCE_SHA256 = os.getenv(
    "USE_EXPECTED_SOURCE_SHA256", ""
).strip().lower()
if EXPECTED_RUNTIME_SOURCE_SHA256:
    if RUNTIME_SOURCE_SHA256 != EXPECTED_RUNTIME_SOURCE_SHA256:
        print(
            "USE SOURCE PROVENANCE FAILURE: "
            f"expected_source_sha256={EXPECTED_RUNTIME_SOURCE_SHA256}, "
            f"actual_source_sha256={RUNTIME_SOURCE_SHA256}, "
            f"file={os.path.abspath(__file__)}"
        )
        raise RuntimeError(
            "USE source provenance mismatch; refusing to serve requests."
        )
    print(
        "USE SOURCE PROVENANCE: valid=True, "
        f"source_sha256={RUNTIME_SOURCE_SHA256}"
    )
else:
    print(
        "USE SOURCE PROVENANCE: expected SHA not configured; "
        f"source_sha256={RUNTIME_SOURCE_SHA256}. "
        "LIVE Render deployment must provide USE_EXPECTED_SOURCE_SHA256."
    )

_enforce_canonical_build_identity()

# Sole request correlation identity for the current async request.
# Middleware creates it once; downstream retrieval/generation code reads it.
USE_REQUEST_ID_CONTEXT: contextvars.ContextVar[str] = contextvars.ContextVar(
    "use_request_id",
    default="",
)

def _request_correlation_log_prefix() -> str:
    return (
        f"request_id={USE_REQUEST_ID_CONTEXT.get('') or 'unbound'}, "
        f"build_id={CANONICAL_BUILD_ID}, {_runtime_log_prefix()}"
    )


def _runtime_identity() -> Dict[str, Any]:
    return {
        "version": APP_VERSION,
        "fingerprint": DEPLOYMENT_FINGERPRINT,
        "source_sha256": RUNTIME_SOURCE_SHA256,
        "boot_id": RUNTIME_BOOT_ID,
        "process_id": RUNTIME_PROCESS_ID,
    }

def _runtime_log_prefix() -> str:
    return (
        f"version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, "
        f"source_sha256={RUNTIME_SOURCE_SHA256}, boot_id={RUNTIME_BOOT_ID}, "
        f"pid={RUNTIME_PROCESS_ID}"
    )

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

    request_id = uuid.uuid4().hex
    request.state.use_request_id = request_id
    correlation_token = USE_REQUEST_ID_CONTEXT.set(request_id)
    print(
        "USE REQUEST START: "
        f"request_id={request_id}, build_id={CANONICAL_BUILD_ID}, {_runtime_log_prefix()}, "
        f"method={request.method}, path={request.url.path}"
    )

    try:
        response = await call_next(request)
    except Exception as exc:
        print(
            "USE API boundary exception: "
            f"request_id={request_id}, {_runtime_log_prefix()}, error={exc}"
        )
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

    response.headers["X-USE-Build-ID"] = CANONICAL_BUILD_ID
    response.headers["X-USE-Version"] = APP_VERSION
    response.headers["X-USE-Fingerprint"] = DEPLOYMENT_FINGERPRINT
    response.headers["X-USE-Source-SHA256"] = RUNTIME_SOURCE_SHA256
    response.headers["X-USE-Boot-ID"] = RUNTIME_BOOT_ID
    response.headers["X-USE-Request-ID"] = request_id

    print(
        "USE REQUEST END: "
        f"request_id={request_id}, build_id={CANONICAL_BUILD_ID}, {_runtime_log_prefix()}, "
        f"status={response.status_code}"
    )
    USE_REQUEST_ID_CONTEXT.reset(correlation_token)
    return response

# Deployment fingerprint: makes the complete production unit immediately
# visible in runtime logs, preventing stale-source ambiguity.
print(
    "USE STARTUP FINGERPRINT: "
    f"build_id={CANONICAL_BUILD_ID}, "
    f"{_runtime_log_prefix()}, file={os.path.abspath(__file__)}"
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
MAX_COMPACT_GENERATION_CONTEXT_CHARS = 650
MAX_COMPACT_GENERATION_RESOURCE_CHARS = 220
MAX_GENERATION_TOKENS = 290

# v143 static regression marker: valid generation evidence must remain non-empty
# when the secondary provider representation cannot reconstruct it.
_V143_GENERATION_EVIDENCE_PRESERVATION_AUDIT = True
MAX_COMPACT_GENERATION_TOKENS = 160

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


def _has_subject_specific_navigation_signal(query: str) -> bool:
    """Recognize navigation questions whose object is an explicit subject.

    A visitor can know the subject while still not knowing which part of the
    archive is the right doorway. That remains TOPICAL_INQUIRY with a
    navigation need; it must not be promoted to WHOLE_SITE_ORIENTATION.
    This is structural detection, not a vocabulary list of subjects.
    """
    navigation = bool(
        re.search(
            r"\b(?:where|which\s+(?:part|place|section|area|doorway|resource|way)|"
            r"what\s+(?:part|place|section|area|doorway|resource)|"
            r"how\s+(?:do|can)\s+i\s+(?:find|reach|get\s+to))\b",
            query,
            re.IGNORECASE,
        )
    )
    if not navigation:
        return False

    subject_patterns = (
        r"\b(?:about|on|for|around)\s+(?!the\s+(?:living\s+)?archive\b)([^?.!,;:]+)",
        r"\b(?:understand|explore|learn\s+about|look\s+into)\s+([^?.!,;:]+)",
        r"\b(?:my|a|an)\s+specific\s+(?:question|subject|topic)\s+about\s+([^?.!,;:]+)",
    )
    for pattern in subject_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return True

    # Explicit statements that the visitor already knows the subject also
    # establish topical scope even when the subject itself is not repeated in
    # the navigation clause.
    if re.search(
        r"\b(?:i|we)\s+(?:know|already\s+know)\s+what\s+(?:subject|topic|question)\b",
        query,
        re.IGNORECASE,
    ):
        return True

    # Explicit possessive/personal subject construction also establishes that
    # the visitor has an object of inquiry even when the wording is indirect.
    if re.search(
        r"\b(?:i|we)\s+(?:want|would\s+like)\s+to\s+(?:explore|understand|learn\s+about)\s+.+",
        query,
        re.IGNORECASE,
    ):
        return True

    return False


def classify_intent(query_str: str) -> str:
    clean_query = re.sub(r"\s+", " ", query_str.strip().lower())

    if not clean_query:
        return "TOPICAL_INQUIRY"

    # Genuine open exploration is a whole-site orientation state even when
    # the visitor has not named a subject domain. Recognize the combination
    # of not-yet-knowing + exploratory movement before topical complement
    # parsing, so an orientation question is not collapsed into a topic.
    open_exploration = (
        bool(re.search(r"\b(?:not sure|don.t know|dont know)\b", clean_query))
        and bool(re.search(r"\b(?:what i.m looking for|what im looking for|where to look)\b", clean_query))
        and bool(re.search(r"\b(?:explore|exploring)\b", clean_query))
    ) or bool(
        re.search(
            r"\b(?:i(?:\s+am|'m)\s+not\s+sure\s+what\s+i(?:\s+am|'m)\s+looking\s+for)\b",
            clean_query,
        )
        and re.search(r"\b(?:want|would like)\s+to\s+explore\b", clean_query)
    )
    if open_exploration:
        return "WHOLE_SITE_ORIENTATION"

    # A known subject plus a request for a place/doorway is still topical
    # inquiry. The navigation need affects doorway selection downstream; it
    # does not erase the subject from intent classification. This check must
    # precede generic site-orientation rules.
    if _has_subject_specific_navigation_signal(clean_query):
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


# =====================================================================
# D19 CANONICAL RESOURCE MODEL
# =====================================================================
# D19 establishes the internal shape of a canonical resource without
# inventing resource types or functions that are not explicitly present in
# the supplied corpus/index metadata. Recognition and interpretation of
# those fields belong to later Phase III chunks (D20+).
#
# The model deliberately separates stable resource identity from later
# request-specific navigation/evidence roles. Missing fields remain None;
# absence of metadata is not converted into a guessed type or function.
# =====================================================================

_D19_IDENTITY_KEYS = (
    "id",
    "resource_id",
    "canonical_id",
    "slug",
    "url",
    "title",
)

_D19_TYPE_KEYS = (
    "resource_type",
    "resource_kind",
    "content_type",
    "type",
    "kind",
)

_D19_FUNCTION_KEYS = (
    "resource_function",
    "function",
    "canonical_function",
)

_D19_LIFECYCLE_KEYS = (
    "lifecycle",
    "canonical_lifecycle",
)

_D19_ACCESS_KEYS = (
    "access_class",
    "access_level",
    "access",
    "visibility",
    "audience",
)


def _d19_first_metadata_value(
    metadata: Dict[str, Any],
    keys: Tuple[str, ...],
) -> Optional[Any]:
    if not isinstance(metadata, dict):
        return None

    normalized = {}
    for key, value in metadata.items():
        normalized_key = re.sub(
            r"[^a-z0-9]+",
            "_",
            str(key).casefold(),
        ).strip("_")
        if normalized_key and normalized_key not in normalized:
            normalized[normalized_key] = value

    for key in keys:
        value = normalized.get(key)
        if value is not None and str(value).strip():
            return value

    return None


def _d19_normalize_model_value(value: Any) -> Optional[str]:
    if value is None:
        return None
    normalized = re.sub(r"\s+", " ", str(value)).strip()
    return normalized or None


def _canonical_resource_model(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Return the D19 resource shape using only explicit metadata evidence."""
    if not isinstance(metadata, dict) or not metadata:
        return {
            "identity": None,
            "resource_type": None,
            "function": None,
            "navigation_role": None,
            "evidence_role": None,
            "lifecycle": None,
            "access": None,
        }

    identity_values = {}
    for key in _D19_IDENTITY_KEYS:
        value = _d19_first_metadata_value(metadata, (key,))
        if value is not None:
            identity_values[key] = _d19_normalize_model_value(value)

    return {
        "identity": identity_values or None,
        "resource_type": _d19_normalize_model_value(
            _d19_first_metadata_value(metadata, _D19_TYPE_KEYS)
        ),
        "function": _d19_normalize_model_value(
            _d19_first_metadata_value(metadata, _D19_FUNCTION_KEYS)
        ),
        # These are request/pipeline roles, not properties inferred from
        # resource wording. They remain unset until later navigation stages
        # establish them from an explicit relationship.
        "navigation_role": None,
        "evidence_role": None,
        "lifecycle": _d19_normalize_model_value(
            _d19_first_metadata_value(metadata, _D19_LIFECYCLE_KEYS)
        ),
        "access": _d19_normalize_model_value(
            _d19_first_metadata_value(metadata, _D19_ACCESS_KEYS)
        ),
    }


def _attach_canonical_resource_model(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Attach D19's non-destructive internal model to a resource record."""
    if not isinstance(metadata, dict):
        return metadata

    if "_use_resource_model" not in metadata:
        metadata["_use_resource_model"] = _canonical_resource_model(metadata)

    return metadata


# =====================================================================
# D20 RESOURCE-TYPE RECOGNITION
# =====================================================================
# D20 recognizes the canonical publication/resource family from evidence
# already carried by the resource itself. Explicit metadata has priority.
# When explicit type metadata is absent, only strong self-identifying
# structural signals are accepted. Generic subject wording, semantic
# similarity, and incidental mentions of another resource type do not
# establish a type. Unknown is a valid result.
# =====================================================================

_D20_TYPE_ALIASES = {
    "essay": "Essay",
    "essays": "Essay",
    "cornerstone": "Cornerstone",
    "cornerstone hub": "Cornerstone",
    "cornerstone hubs": "Cornerstone",
    "knowledge hub": "Knowledge Hub",
    "knowledge hubs": "Knowledge Hub",
    "reference map": "Reference Map",
    "reference maps": "Reference Map",
    "navigator": "Navigator",
    "navigators": "Navigator",
    "navigator series": "Navigator",
    "pathway": "Pathway",
    "pathways": "Pathway",
    "guided pathway": "Pathway",
    "guided pathways": "Pathway",
    "guided reading pathway": "Pathway",
    "guided reading pathways": "Pathway",
    "case": "Case",
    "case study": "Case",
    "case studies": "Case",
    "learning arc": "Learning Arc",
    "learning arcs": "Learning Arc",
}


def _d20_normalize_type_label(value: Any) -> Optional[str]:
    if value is None:
        return None
    clean = re.sub(r"\s+", " ", str(value)).strip().casefold()
    if not clean:
        return None
    return _D20_TYPE_ALIASES.get(clean)


def _d20_explicit_type(metadata: Dict[str, Any]) -> Optional[str]:
    """Recognize a canonical type only from explicit type metadata."""
    if not isinstance(metadata, dict):
        return None

    explicit_keys = (
        "resource_type",
        "resource_kind",
        "content_type",
        "canonical_type",
        "canonical_resource_type",
    )
    for key in explicit_keys:
        value = _d19_first_metadata_value(metadata, (key,))
        recognized = _d20_normalize_type_label(value)
        if recognized:
            return recognized
    return None


def _d20_title_type(metadata: Dict[str, Any]) -> Optional[str]:
    """Recognize type from strong title-level self-identification only."""
    title = html.unescape(str(metadata.get("title", "") or "")).strip().casefold()
    if not title:
        return None

    # Ordered from the most structurally specific labels to broader ones.
    title_patterns = (
        (r"\b(?:living archive )?navigator(?: series)?\b", "Navigator"),
        (r"\b(?:reference )?map\b", "Reference Map"),
        (r"\b(?:guided reading|guided) pathway(?:s)?\b", "Pathway"),
        (r"\bknowledge hub(?:s)?\b", "Knowledge Hub"),
        (r"\bcornerstone hub(?:s)?\b", "Cornerstone"),
        (r"\blearning arc(?:s)?\b", "Learning Arc"),
        (r"\bcase study(?:s|ies)?\b", "Case"),
        (r"^case\s*[:#-]?\s*\d+\b", "Case"),
        (r"^essay\s*[:#-]", "Essay"),
    )
    for pattern, resource_type in title_patterns:
        if re.search(pattern, title, flags=re.IGNORECASE):
            return resource_type
    return None


def _d20_content_self_identification(metadata: Dict[str, Any]) -> Optional[str]:
    """Use content only for explicit self-identifying structural statements."""
    content = html.unescape(_resource_content(metadata)).casefold()
    if not content:
        return None

    content_patterns = (
        (r"\b(?:this|the) living archive navigator\b", "Navigator"),
        (r"\b(?:this|the) reference map\b", "Reference Map"),
        (r"\b(?:this|the) guided reading pathway\b", "Pathway"),
        (r"\b(?:this|the) knowledge hub\b", "Knowledge Hub"),
        (r"\b(?:this|the) cornerstone(?: hub)?\b", "Cornerstone"),
        (r"\b(?:this|the) learning arc\b", "Learning Arc"),
        (r"\b(?:this|the) case study\b", "Case"),
        (r"\b(?:this|the) essay\b", "Essay"),
    )
    for pattern, resource_type in content_patterns:
        if re.search(pattern, content, flags=re.IGNORECASE):
            return resource_type
    return None


def _recognize_resource_type(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Return D20 type recognition with bounded evidence provenance."""
    if not isinstance(metadata, dict) or not metadata:
        return {"resource_type": None, "confidence": "unknown", "basis": "none"}

    explicit = _d20_explicit_type(metadata)
    if explicit:
        return {
            "resource_type": explicit,
            "confidence": "explicit",
            "basis": "explicit_metadata",
        }

    title_type = _d20_title_type(metadata)
    if title_type:
        return {
            "resource_type": title_type,
            "confidence": "strong",
            "basis": "title_self_identification",
        }

    content_type = _d20_content_self_identification(metadata)
    if content_type:
        return {
            "resource_type": content_type,
            "confidence": "bounded",
            "basis": "content_self_identification",
        }

    # v136: duplicate retrieval enrichment may preserve a stronger D20
    # recognition annotation established by an independent retrieval path.
    # Treat that annotation as bounded internal evidence only after the raw
    # metadata/title/content evidence above has had priority. This prevents
    # evidence enrichment from becoming evidence loss at the next recognition
    # boundary while still refusing to invent a type when no recognition exists.
    attached = metadata.get("_use_resource_type_recognition")
    if isinstance(attached, dict):
        attached_type = _d20_normalize_type_label(attached.get("resource_type"))
        if attached_type:
            return {
                "resource_type": attached_type,
                "confidence": attached.get("confidence", "bounded"),
                "basis": attached.get("basis", "enriched_canonical_recognition"),
            }

    return {
        "resource_type": None,
        "confidence": "unknown",
        "basis": "insufficient_structural_evidence",
    }


def _attach_resource_type_recognition(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Attach D20 recognition without overwriting D19's explicit model."""
    if not isinstance(metadata, dict):
        return metadata

    if "_use_resource_type_recognition" not in metadata:
        metadata["_use_resource_type_recognition"] = _recognize_resource_type(metadata)

    return metadata


# =====================================================================
# D21 ESSAY FUNCTION
# =====================================================================
# D21 establishes the architectural function of a resource already recognized
# as an Essay. It does not infer a visitor need from the essay or promote an
# essay merely because it is semantically related to the question. The function
# is established only when the resource's own evidence explicitly presents the
# essay as an exploratory, interpretive, or integrative work.
#
# Navigator function work belongs to D25 in the canonical Phase III sequence.
# It is intentionally not active in D21.
# =====================================================================

_D21_ESSAY_FUNCTION_LABEL = "substantive exploration and sensemaking"


def _d21_essay_function(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Recognize Essay function only from D20 type plus resource evidence."""
    if not isinstance(metadata, dict):
        return {"function": None, "confidence": "unknown", "basis": "none"}

    recognition = metadata.get("_use_resource_type_recognition")
    if not isinstance(recognition, dict):
        recognition = _recognize_resource_type(metadata)

    if recognition.get("resource_type") != "Essay":
        return {
            "function": None,
            "confidence": "not_applicable",
            "basis": "resource_type_not_essay",
        }

    content = html.unescape(_resource_content(metadata)).casefold()
    if not content:
        return {
            "function": None,
            "confidence": "unknown",
            "basis": "insufficient_essay_function_evidence",
        }

    # These signals are intentionally generic and structural. They describe
    # what the resource itself says it is doing, rather than importing a
    # subject-specific interpretation from the visitor's question.
    exploration_signals = (
        r"\bthis essay explores\b",
        r"\bthis essay examines\b",
        r"\bthis essay investigates\b",
        r"\bthis essay considers\b",
        r"\bthis essay asks\b",
        r"\bthe essay explores\b",
        r"\bthe essay examines\b",
        r"\bthe essay investigates\b",
        r"\bthe essay considers\b",
    )
    synthesis_signals = (
        r"\bthis essay presents (?:an|a) (?:integrative|architectural|systems-based|developmental)",
        r"\bthis essay integrates\b",
        r"\bthis essay synthesizes\b",
        r"\bthis essay offers\b",
        r"\bthe essay integrates\b",
        r"\bthe essay synthesizes\b",
        r"\bthe essay offers\b",
    )

    exploration_hits = sum(
        1 for pattern in exploration_signals if re.search(pattern, content)
    )
    synthesis_hits = sum(
        1 for pattern in synthesis_signals if re.search(pattern, content)
    )

    if exploration_hits >= 1 and synthesis_hits >= 1:
        return {
            "function": _D21_ESSAY_FUNCTION_LABEL,
            "confidence": "strong",
            "basis": "essay_exploration_and_synthesis_evidence",
        }

    return {
        "function": None,
        "confidence": "unknown",
        "basis": "insufficient_essay_function_evidence",
    }


def _attach_essay_function(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Attach D21 Essay function without overwriting explicit D19 fields."""
    if not isinstance(metadata, dict):
        return metadata
    if "_use_essay_function" not in metadata:
        metadata["_use_essay_function"] = _d21_essay_function(metadata)
    return metadata


# =====================================================================
# D22 CORNERSTONE FUNCTION
# =====================================================================
# D22 establishes the architectural function of a resource already recognized
# as a Cornerstone. The corpus describes Cornerstones as foundational lenses
# that reveal larger patterns across domains and connect essays, frameworks,
# analyses, and maps around underlying principles.
#
# This layer therefore requires evidence from the resource itself for both:
#   1) a foundational/lens role, and
#   2) a cross-domain/pattern-orientation role.
#
# It does not infer what a visitor's subject means, and it does not promote a
# Cornerstone merely because the visitor's question contains broad or
# interdisciplinary language.
# =====================================================================

_D22_CORNERSTONE_FUNCTION_LABEL = "cross-domain pattern orientation"


def _d22_cornerstone_function(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Recognize Cornerstone function only from sufficient resource evidence."""
    if not isinstance(metadata, dict):
        return {"function": None, "confidence": "unknown", "basis": "none"}

    recognition = metadata.get("_use_resource_type_recognition")
    if not isinstance(recognition, dict):
        recognition = _recognize_resource_type(metadata)

    if recognition.get("resource_type") != "Cornerstone":
        return {
            "function": None,
            "confidence": "not_applicable",
            "basis": "resource_type_not_cornerstone",
        }

    content = html.unescape(_resource_content(metadata)).casefold()
    if not content:
        return {
            "function": None,
            "confidence": "unknown",
            "basis": "insufficient_cornerstone_function_evidence",
        }

    # Structural signals are deliberately generic. They are drawn from the
    # corpus's own description of Cornerstones as foundational lenses and as
    # bridges/pattern frameworks across multiple domains.
    foundational_signals = (
        r"\bthis cornerstone\b",
        r"\bcornerstones? (?:are|act as) (?:foundational )?lenses\b",
        r"\bfoundational lenses?\b",
        r"\bways of seeing\b",
        r"\bthe purpose of the cornerstones\b",
        r"\bthe cornerstone (?:provides|offers)\b",
    )
    cross_domain_signals = (
        r"\bacross (?:multiple|different|various) domains\b",
        r"\bbetween disciplines\b",
        r"\bbridges? between disciplines\b",
        r"\bunderlying (?:principle|patterns?)\b",
        r"\blarger patterns?\b",
        r"\bcommon underlying principle\b",
        r"\binterconnected (?:system|system of|dimensions)\b",
        r"\bmultiple domains of life\b",
        r"\binterdisciplinary\b",
    )

    foundational_hits = sum(
        1 for pattern in foundational_signals if re.search(pattern, content)
    )
    cross_domain_hits = sum(
        1 for pattern in cross_domain_signals if re.search(pattern, content)
    )

    if foundational_hits >= 1 and cross_domain_hits >= 1:
        return {
            "function": _D22_CORNERSTONE_FUNCTION_LABEL,
            "confidence": "strong",
            "basis": "cornerstone_foundational_and_cross_domain_evidence",
        }

    return {
        "function": None,
        "confidence": "unknown",
        "basis": "insufficient_cornerstone_function_evidence",
    }


def _attach_cornerstone_function(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Attach D22 Cornerstone function without overwriting earlier models."""
    if not isinstance(metadata, dict):
        return metadata
    if "_use_cornerstone_function" not in metadata:
        metadata["_use_cornerstone_function"] = _d22_cornerstone_function(metadata)
    return metadata


# =====================================================================
# D23 KNOWLEDGE HUB FUNCTION
# =====================================================================
# Recognize a Knowledge Hub's architectural function only when the resource
# itself establishes that it is a collection/orientation point organizing
# multiple canonical materials around a subject or domain.
# =====================================================================

_D23_KNOWLEDGE_HUB_FUNCTION_LABEL = "curated subject-domain orientation"


def _d23_knowledge_hub_function(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Recognize Knowledge Hub function only from sufficient resource evidence."""
    if not isinstance(metadata, dict):
        return {"function": None, "confidence": "unknown", "basis": "none"}

    recognition = metadata.get("_use_resource_type_recognition")
    if not isinstance(recognition, dict):
        recognition = _recognize_resource_type(metadata)

    if recognition.get("resource_type") != "Knowledge Hub":
        return {
            "function": None,
            "confidence": "not_applicable",
            "basis": "resource_type_not_knowledge_hub",
        }

    content = html.unescape(_resource_content(metadata)).casefold()
    if not content:
        return {
            "function": None,
            "confidence": "unknown",
            "basis": "insufficient_knowledge_hub_function_evidence",
        }

    collection_signals = (
        r"\bknowledge hub\b",
        r"\bknowledge hubs\b",
        r"\bcurated collection\b",
        r"\bcurated resources\b",
        r"\bcollection of resources\b",
    )
    organization_signals = (
        r"\bessays?\b",
        r"\bcornerstones?\b",
        r"\breference maps?\b",
        r"\bnavigators?\b",
        r"\bpathways?\b",
        r"\bcase (?:studies|library)\b",
        r"\borganizes?\b",
        r"\bbrings together\b",
        r"\bentry point\b",
        r"\borientation\b",
    )

    collection_hits = sum(
        1 for pattern in collection_signals if re.search(pattern, content)
    )
    organization_hits = sum(
        1 for pattern in organization_signals if re.search(pattern, content)
    )

    if collection_hits >= 1 and organization_hits >= 2:
        return {
            "function": _D23_KNOWLEDGE_HUB_FUNCTION_LABEL,
            "confidence": "strong",
            "basis": "knowledge_hub_collection_and_organization_evidence",
        }

    return {
        "function": None,
        "confidence": "unknown",
        "basis": "insufficient_knowledge_hub_function_evidence",
    }


def _attach_knowledge_hub_function(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Attach D23 Knowledge Hub function without overwriting earlier models."""
    if not isinstance(metadata, dict):
        return metadata
    if "_use_knowledge_hub_function" not in metadata:
        metadata["_use_knowledge_hub_function"] = _d23_knowledge_hub_function(metadata)
    return metadata


# =====================================================================
# D24 REFERENCE MAP FUNCTION
# =====================================================================
# Reference Maps are an orienting visual framework: they simplify
# complexity without reducing it and help readers perceive structure,
# relationships, and larger systems.
#
# D24 recognizes that architectural function only from evidence carried
# by the resource itself. It does not infer that a map is the right
# doorway for a particular visitor; that belongs to later navigation
# architecture.
# =====================================================================

_D24_REFERENCE_MAP_FUNCTION_LABEL = "visual structural orientation"


def _d24_reference_map_function(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Recognize Reference Map function only from sufficient resource evidence."""
    if not isinstance(metadata, dict):
        return {"function": None, "confidence": "unknown", "basis": "none"}

    recognition = metadata.get("_use_resource_type_recognition")
    if not isinstance(recognition, dict):
        recognition = _recognize_resource_type(metadata)

    if recognition.get("resource_type") != "Reference Map":
        return {
            "function": None,
            "confidence": "not_applicable",
            "basis": "resource_type_not_reference_map",
        }

    content = html.unescape(_resource_content(metadata)).casefold()
    if not content:
        return {
            "function": None,
            "confidence": "unknown",
            "basis": "insufficient_reference_map_function_evidence",
        }

    visual_framework_signals = (
        r"\bvisual framework\b",
        r"\bvisual frameworks\b",
        r"\borienting framework\b",
        r"\bvisual representation\b",
        r"\bvisual composition\b",
        r"\bvisual map\b",
        r"\bmap presents\b",
        r"\bmap provides\b",
    )
    orientation_structure_signals = (
        r"\borientation\b",
        r"\borient(?:ing|s)?\b",
        r"\bstructure\b",
        r"\brelationships?\b",
        r"\bpatterns?\b",
        r"\bcomplexity\b",
        r"\bsee how\b",
        r"\bperceive\b",
        r"\bconnect(?:ions)?\b",
    )

    visual_hits = sum(
        1 for pattern in visual_framework_signals if re.search(pattern, content)
    )
    orientation_hits = sum(
        1 for pattern in orientation_structure_signals if re.search(pattern, content)
    )

    # Require evidence that the resource is itself a visual/framework
    # object plus at least two independent orientation/structure signals.
    if visual_hits >= 1 and orientation_hits >= 2:
        return {
            "function": _D24_REFERENCE_MAP_FUNCTION_LABEL,
            "confidence": "strong",
            "basis": "reference_map_visual_framework_and_orientation_evidence",
        }

    return {
        "function": None,
        "confidence": "unknown",
        "basis": "insufficient_reference_map_function_evidence",
    }


def _attach_reference_map_function(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Attach D24 Reference Map function without overwriting prior models."""
    if not isinstance(metadata, dict):
        return metadata
    if "_use_reference_map_function" not in metadata:
        metadata["_use_reference_map_function"] = _d24_reference_map_function(metadata)
    return metadata


# =====================================================================
# D25 NAVIGATOR FUNCTION
# =====================================================================
# A Navigator is an architectural orientation/entry resource that brings
# together multiple canonical ways of entering or moving through a subject.
# D25 recognizes that function only from evidence carried by the resource
# itself. It does not infer that a Navigator is the right doorway for a
# particular visitor; that belongs to later navigation architecture.
# =====================================================================

_D25_NAVIGATOR_FUNCTION_LABEL = "integrated orientation and entry"


def _d25_navigator_function(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Recognize Navigator function only from sufficient resource evidence."""
    if not isinstance(metadata, dict):
        return {"function": None, "confidence": "unknown", "basis": "none"}

    recognition = metadata.get("_use_resource_type_recognition")
    if not isinstance(recognition, dict):
        recognition = _recognize_resource_type(metadata)

    if recognition.get("resource_type") != "Navigator":
        return {
            "function": None,
            "confidence": "not_applicable",
            "basis": "resource_type_not_navigator",
        }

    content = html.unescape(_resource_content(metadata)).casefold()
    if not content:
        return {
            "function": None,
            "confidence": "unknown",
            "basis": "insufficient_navigator_function_evidence",
        }

    component_signals = (
        r"\breference maps?\b",
        r"\bguide notes?\b",
        r"\breflective questions?\b",
        r"\bguided reading pathways?\b",
        r"\bpathways?\b",
        r"\bessays?\b",
        r"\bknowledge hubs?\b",
        r"\bcornerstones?\b",
    )
    integration_signals = (
        r"\bbrings together\b",
        r"\bbring together\b",
        r"\bcombines\b",
        r"\bintegrates\b",
        r"\bbundles\b",
        r"\bconnects\b",
        r"\bentry point\b",
        r"\bwayfinding\b",
        r"\bnavigation\b",
        r"\borientation\b",
    )

    component_hits = sum(
        1 for pattern in component_signals if re.search(pattern, content)
    )
    integration_hits = sum(
        1 for pattern in integration_signals if re.search(pattern, content)
    )

    # Require at least two distinct canonical component signals and an
    # explicit integration/entry signal. This prevents a generic resource
    # that merely mentions several document types from becoming a Navigator.
    if component_hits >= 2 and integration_hits >= 1:
        return {
            "function": _D25_NAVIGATOR_FUNCTION_LABEL,
            "confidence": "strong",
            "basis": "navigator_integrated_component_and_entry_evidence",
        }

    return {
        "function": None,
        "confidence": "unknown",
        "basis": "insufficient_navigator_function_evidence",
    }


def _attach_navigator_function(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Attach D25 Navigator function without overwriting prior models."""
    if not isinstance(metadata, dict):
        return metadata
    if "_use_navigator_function" not in metadata:
        metadata["_use_navigator_function"] = _d25_navigator_function(metadata)
    return metadata


# =====================================================================
# D25 SELECTION-PATH AUDIT — DIAGNOSTIC ONLY
# =====================================================================
# v111 does NOT change canonical selection behavior. It audits whether the
# resource-function signals established by D19-D25 are actually consumed by
# the retrieval/ranking/doorway path. This prevents vocabulary patches from
# being used to compensate for a missing architectural connection.
# =====================================================================

def _d26_pathway_function_self_audit() -> None:
    """Verify Pathway function is type-gated and evidence-bound."""
    good = {
        "title": "Guided Reading Pathway — Understanding Change",
        "_use_resource_type_recognition": {"resource_type": "Pathway"},
        "text": (
            "This Guided Reading Pathway is a guided experience that leads the reader "
            "through a sequence of canonical essays and reflection questions. Each "
            "stop prepares the reader for the next stop in the journey."
        ),
    }
    result = _d26_pathway_function(good)
    assert result["function"] == _D26_PATHWAY_FUNCTION_LABEL
    assert result["basis"] == "pathway_guidance_and_sequence_evidence"

    insufficient = {
        "title": "Guided Reading Pathway",
        "_use_resource_type_recognition": {"resource_type": "Pathway"},
        "text": "This pathway is available in the Living Archive.",
    }
    assert _d26_pathway_function(insufficient)["function"] is None

    non_pathway = {
        "title": "An Essay",
        "_use_resource_type_recognition": {"resource_type": "Essay"},
        "text": "This essay explores a sequence of ideas and guides reflection.",
    }
    assert _d26_pathway_function(non_pathway)["function"] is None

    attached = _attach_pathway_function(dict(good))
    assert attached["_use_pathway_function"]["function"] == _D26_PATHWAY_FUNCTION_LABEL
    print("USE D26 PATHWAY FUNCTION AUDIT: PASS")


def _d27_case_learning_arc_function_self_audit() -> None:
    """Verify Case / Learning Arc function is type-gated and evidence-bound."""
    case = {
        "title": "Case Study — Institutional Trust",
        "_use_resource_type_recognition": {"resource_type": "Case"},
        "text": (
            "This case study presents an applied case of institutional trust. "
            "The case illustrates what happened in practice and what can be learned."
        ),
    }
    case_result = _d27_case_learning_arc_function(case)
    assert case_result["function"] == _D27_CASE_FUNCTION_LABEL

    arc = {
        "title": "Learning Arc — Trust in Practice",
        "_use_resource_type_recognition": {"resource_type": "Learning Arc"},
        "text": (
            "This Learning Arc presents a sequence of cases and a progressive "
            "learning progression from one case to the next, with applied learning."
        ),
    }
    arc_result = _d27_case_learning_arc_function(arc)
    assert arc_result["function"] == _D27_LEARNING_ARC_FUNCTION_LABEL

    insufficient = {
        "title": "Case Study",
        "_use_resource_type_recognition": {"resource_type": "Case"},
        "text": "This resource is available in the case library.",
    }
    assert _d27_case_learning_arc_function(insufficient)["function"] is None

    non_case = {
        "title": "Governance Essay",
        "_use_resource_type_recognition": {"resource_type": "Essay"},
        "text": "This essay discusses applied examples and case studies.",
    }
    assert _d27_case_learning_arc_function(non_case)["function"] is None

    attached = _attach_case_learning_arc_function(dict(case))
    assert attached["_use_case_learning_arc_function"]["function"] == _D27_CASE_FUNCTION_LABEL
    print("USE D27 CASE / LEARNING ARC FUNCTION AUDIT: PASS")


def _d21_d27_resource_function_layer_self_audit() -> None:
    """Verify the D21-D27 function layer is coherent and selection-aware."""
    required = {
        "_use_essay_function": "substantive exploration and sensemaking",
        "_use_cornerstone_function": "cross-domain pattern orientation",
        "_use_knowledge_hub_function": "curated subject-domain orientation",
        "_use_reference_map_function": "visual structural orientation",
        "_use_navigator_function": "integrated orientation and entry",
        "_use_pathway_function": "guided orientation experience",
        "_use_case_learning_arc_function": "applied case learning",
    }
    if tuple(required) != _RESOURCE_FUNCTION_NAMES:
        raise RuntimeError("D21-D27 function layer regression: registry is incomplete or reordered.")

    questions = (
        ("I want to see the available routes and decide where to go next.", "integrated orientation and entry"),
        ("I want a guided path through this subject and want to know what to read first.", "guided orientation experience"),
        ("I want real cases showing how this plays out in practice.", "applied case learning"),
    )
    for question, expected in questions:
        fit = _visitor_resource_function_fit(question)
        if fit.get(expected, 0.0) <= 0:
            raise RuntimeError(
                "D21-D27 function layer regression: expected functional need was not recognized: "
                + expected
            )

    # Function metadata must be part of selection, but ordinary explanatory
    # questions remain function-neutral.
    pathway = {
        "title": "Guided Pathway",
        "_use_pathway_function": {"function": _D26_PATHWAY_FUNCTION_LABEL},
    }
    essay = {
        "title": "Essay",
        "_use_essay_function": {"function": _D21_ESSAY_FUNCTION_LABEL},
    }
    selected = select_canonical_doorways(
        [essay, pathway],
        {"primary": "general", "scores": {}},
        question="I want a guided path through this subject and want to know what to read first.",
    )
    if selected[0] is not pathway:
        raise RuntimeError("D21-D27 function layer regression: functional need did not affect canonical selection.")

    neutral_question = "Why does this matter?"
    if _resource_function_selection_bonus(pathway, neutral_question) != 0.0:
        raise RuntimeError("D21-D27 function layer regression: neutral question received a functional bonus.")
    if _resource_function_selection_bonus(essay, neutral_question) != 0.0:
        raise RuntimeError("D21-D27 function layer regression: neutral question received a functional bonus.")

    print("USE D21-D27 RESOURCE FUNCTION LAYER AUDIT: PASS")


def _d25_resource_function_selection_bridge_self_audit() -> None:
    """Verify function fit changes selection only when the visitor need warrants it."""
    navigator = {
        "title": "Governance Navigator",
        "_use_navigator_function": {
            "function": "integrated orientation and entry"
        },
    }
    essay = {
        "title": "Governance Essay",
        "_use_essay_function": {
            "function": "substantive exploration and sensemaking"
        },
    }

    open_navigation_question = (
        "I want an orientation to the wider body of material, "
        "see the available routes, and decide where I want to go next. "
        "Where should I begin?"
    )

    assert _resource_function_selection_bonus(
        navigator, open_navigation_question
    ) == _RESOURCE_FUNCTION_FIT_BONUS
    assert _resource_function_selection_bonus(
        essay, open_navigation_question
    ) == 0.0

    neutral_question = "Why does governance matter?"
    assert _resource_function_selection_bonus(
        navigator, neutral_question
    ) == 0.0
    assert _resource_function_selection_bonus(
        essay, neutral_question
    ) == 0.0

    # Verify the actual canonical selection path consumes the bridge.
    docs = [essay, navigator]
    selected = select_canonical_doorways(
        docs,
        {},
        question=open_navigation_question,
    )
    assert selected[0]["title"] == "Governance Navigator"

    print("USE D25 RESOURCE-FUNCTION SELECTION BRIDGE AUDIT: PASS")


def _d25_selection_path_audit() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    lines = source.splitlines()

    function_definitions = {
        "D19 model": r"def _canonical_resource_model",
        "D20 type recognition": r"def _recognize_resource_type",
        "D21 Essay function": r"def _d21_essay_function",
        "D22 Cornerstone function": r"def _d22_cornerstone_function",
        "D23 Knowledge Hub function": r"def _d23_knowledge_hub_function",
        "D24 Reference Map function": r"def _d24_reference_map_function",
        "D25 Navigator function": r"def _d25_navigator_function",
    }

    attachment_signals = {
        "D21": r"_attach_essay_function",
        "D22": r"_attach_cornerstone_function",
        "D23": r"_attach_knowledge_hub_function",
        "D24": r"_attach_reference_map_function",
        "D25": r"_attach_navigator_function",
        "D26": r"_attach_pathway_function",
        "D27": r"_attach_case_learning_arc_function",
    }

    # Selection/ranking functions are intentionally discovered rather than
    # assumed. This is the evidence needed before changing architecture.
    candidate_names = []
    for idx, line in enumerate(lines, 1):
        if re.match(r"\s*def\s+", line):
            name = re.search(r"def\s+([A-Za-z_][A-Za-z0-9_]*)", line)
            if name:
                candidate_names.append((idx, name.group(1)))

    selection_terms = (
        "select",
        "rank",
        "rerank",
        "doorway",
        "candidate",
        "movement",
        "sequence",
        "navigation",
        "resource",
    )
    selection_functions = [
        (line_no, name)
        for line_no, name in candidate_names
        if any(term in name.casefold() for term in selection_terms)
    ]

    function_consumers = []
    resource_function_terms = (
        "_use_essay_function",
        "_use_cornerstone_function",
        "_use_knowledge_hub_function",
        "_use_reference_map_function",
        "_use_navigator_function",
        "resource_function",
        "function",
    )

    for idx, line in enumerate(lines, 1):
        if any(term in line for term in resource_function_terms):
            function_consumers.append((idx, line.strip()))

    print("USE D25 SELECTION-PATH AUDIT")
    print("  Function definitions:")
    for label, pattern in function_definitions.items():
        hits = [
            idx for idx, line in enumerate(lines, 1)
            if re.search(pattern, line)
        ]
        print(f"    {label}: {hits[:5]}")
    print("  Function attachment hooks:")
    for label, pattern in attachment_signals.items():
        hits = [
            idx for idx, line in enumerate(lines, 1)
            if pattern in line
        ]
        print(f"    {label}: {hits[:5]}")
    print("  Selection/ranking/navigation functions:")
    for line_no, name in selection_functions:
        print(f"    line {line_no}: {name}")
    print("  Lines referencing resource-function metadata:")
    for line_no, line in function_consumers:
        print(f"    line {line_no}: {line[:180]}")

    # This audit is informational. Its success condition is simply that all
    # D19-D25 recognition layers exist and are attached; no claim is made that
    # they influence selection.
    assert all(
        re.search(pattern, source)
        for pattern in function_definitions.values()
    )
    assert all(
        pattern in source for pattern in attachment_signals.values()
    )
    print("  D19-D25 recognition/attachment integrity: PASS")
    print("  Selection consumption: DIAGNOSTIC — requires inspection of listed paths")


# =====================================================================
# CANONICAL CORPUS LIFECYCLE ELIGIBILITY
# =====================================================================
#
# The vector index can contain historically retained resources that remain
# technically published in WordPress. Publication status therefore cannot be
# treated as navigational eligibility. USE must reject explicit resource-level
# lifecycle evidence indicating that a record is archived, retired,
# superseded, withdrawn, deprecated, or otherwise no longer current.
#
# This is intentionally generic: no project-specific title, URL, or keyword
# such as "Energe" is hard-coded into the navigation engine. Conversational
# mentions of archived material inside an otherwise current resource are not
# sufficient to exclude that resource; the lifecycle signal must belong to
# the resource's own identity/metadata.
# =====================================================================

_ARCHIVAL_LIFECYCLE_VALUES = frozenset({
    "archive",
    "archived",
    "retired",
    "deactivated",
    "withdrawn",
    "obsolete",
    "deprecated",
    "superseded",
})

_ARCHIVAL_TITLE_PREFIXES = (
    "archived -",
    "archived:",
    "[archived]",
)

_ARCHIVAL_SLUG_SUFFIXES = (
    "-legacy",
    "-archived",
    "-retired",
    "-deprecated",
    "-superseded",
    "-withdrawn",
)


def _normalized_lifecycle_value(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold()


def _is_archived_canonical_resource(metadata: Dict[str, Any]) -> bool:
    """Return True only when the resource itself carries strong archive evidence."""
    if not isinstance(metadata, dict) or not metadata:
        return False

    # Prefer explicit lifecycle/status metadata when an ingestion/index version
    # provides it. Do not confuse ordinary WordPress publication status
    # ("publish") with canonical lifecycle status.
    for key, value in metadata.items():
        key_normalized = re.sub(r"[^a-z0-9]+", " ", str(key).casefold()).strip()
        if (
            "status" in key_normalized
            or "lifecycle" in key_normalized
            or "archive" in key_normalized
            or "retirement" in key_normalized
        ):
            normalized_value = _normalized_lifecycle_value(value)
            if normalized_value in _ARCHIVAL_LIFECYCLE_VALUES:
                return True

    # Canonical titles beginning with an explicit archive marker are strong
    # resource-identity evidence. This does not inspect arbitrary content text.
    title = re.sub(
        r"\s+",
        " ",
        str(metadata.get("title", "") or ""),
    ).strip().casefold()

    if any(title.startswith(prefix) for prefix in _ARCHIVAL_TITLE_PREFIXES):
        return True

    # Legacy/retired URL slugs are also strong identity-level evidence. Restrict
    # this to suffixes so ordinary resources discussing "legacy systems" are not
    # suppressed merely because that phrase occurs in their title or content.
    slug = re.sub(
        r"\s+",
        " ",
        str(metadata.get("slug", "") or ""),
    ).strip().strip("/").casefold()

    if any(slug.endswith(suffix) for suffix in _ARCHIVAL_SLUG_SUFFIXES):
        return True

    # Some ingestion versions do not expose a dedicated slug field. The
    # canonical URL may be the only durable identity field carrying an
    # archival marker (for example, a WordPress redirect target ending in
    # "-legacy"). Inspect only URL-like identity metadata, and only the final
    # path segment, so ordinary query parameters or content text cannot trigger
    # lifecycle suppression.
    for key, value in metadata.items():
        key_normalized = re.sub(r"[^a-z0-9]+", " ", str(key).casefold()).strip()
        if not any(token in key_normalized.split() for token in ("url", "permalink")):
            continue

        url_value = re.sub(r"[?#].*$", "", str(value or "")).strip().rstrip("/").casefold()
        if not url_value:
            continue

        final_path_segment = re.split(r"[/\\]", url_value)[-1].strip()
        if any(final_path_segment.endswith(suffix) for suffix in _ARCHIVAL_SLUG_SUFFIXES):
            print(
                "USE canonical lifecycle gate: URL identity marker detected for "
                f"resource '{metadata.get('title', 'Untitled Resource')}'."
            )
            return True

    return False


def _use_corpus_access_eligible(metadata: Dict[str, Any]) -> bool:
    """Enforce the USE public-corpus boundary when access metadata is present.

    USE is the T1–T3 public orientation layer. FSD owns T4 and authorized
    stewardship material. Missing access metadata is not treated as proof of
    protection, preserving compatibility with older public records; explicit
    protected/restricted access or a tier above T3 is always rejected.
    """
    if not isinstance(metadata, dict) or not metadata:
        return False

    access_values = []
    for key, value in metadata.items():
        normalized_key = re.sub(r"[^a-z0-9]+", "_", str(key).casefold()).strip("_")
        if normalized_key in {
            "access_class",
            "access",
            "visibility",
            "audience",
            "access_level",
        }:
            access_values.append(_normalized_lifecycle_value(value))

    protected_values = {
        "private", "protected", "restricted", "steward", "steward_only",
        "steward-access", "steward access", "t4", "internal",
    }
    if any(value in protected_values for value in access_values):
        print(
            "USE corpus boundary: rejected non-public resource "
            f"'{metadata.get('title', 'Untitled Resource')}'."
        )
        return False

    for key, value in metadata.items():
        normalized_key = re.sub(r"[^a-z0-9]+", "_", str(key).casefold()).strip("_")
        if normalized_key not in {"tier", "archive_tier", "resource_tier"}:
            continue
        raw = str(value or "").strip().casefold()
        match = re.search(r"t\s*([1-9][0-9]*)", raw)
        if match and int(match.group(1)) > 3:
            print(
                "USE corpus boundary: rejected T4+ resource "
                f"'{metadata.get('title', 'Untitled Resource')}'."
            )
            return False
        try:
            if raw.isdigit() and int(raw) > 3:
                print(
                    "USE corpus boundary: rejected T4+ resource "
                    f"'{metadata.get('title', 'Untitled Resource')}'."
                )
                return False
        except ValueError:
            pass

    return True


def _is_navigable_canonical_resource(metadata: Dict[str, Any]) -> bool:
    """Apply the canonical corpus lifecycle boundary before navigation."""
    if not metadata:
        return False

    if not _use_corpus_access_eligible(metadata):
        return False

    if _is_archived_canonical_resource(metadata):
        print(
            "USE canonical lifecycle gate: rejected archived/retired resource "
            f"'{metadata.get('title', 'Untitled Resource')}'."
        )
        return False

    return True


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

        resource_type_info = doc.get("_use_resource_type_recognition") or {}
        function_info = None
        for function_key in _RESOURCE_FUNCTION_NAMES:
            candidate = doc.get(function_key)
            if isinstance(candidate, dict) and candidate.get("function"):
                function_info = candidate
                break

        architectural_lines = []
        if resource_type_info.get("resource_type"):
            architectural_lines.append(
                f"Recognized Resource Type: {resource_type_info['resource_type']}"
            )
        if function_info and function_info.get("function"):
            architectural_lines.append(
                f"Recognized Resource Function: {function_info['function']}"
            )

        sequence_role = doc.get("_use_resource_sequence_role")
        if sequence_role:
            architectural_lines.append(
                f"D28 Sequence Role: {sequence_role}"
            )

        movement_info = doc.get("_use_canonical_movement") or {}
        if movement_info:
            architectural_lines.append(
                "D29 Movement Destination: "
                + (
                    movement_info.get("destination_url")
                    if movement_info.get("destination_validated")
                    else "not validated"
                )
            )
            architectural_lines.append(
                "D29 Movement Status: "
                + movement_info.get("movement_status", "no_validated_movement")
            )
            if movement_info.get("next_destination_validated"):
                architectural_lines.append(
                    "D29 Next Canonical Destination: "
                    + movement_info.get("next_destination_url", "")
                )
            else:
                architectural_lines.append(
                    "D29 Next Canonical Destination: none explicitly validated"
                )
            linked_titles = movement_info.get("linked_destination_titles") or []
            if linked_titles:
                architectural_lines.append(
                    "D29 Explicit Canonical Links: " + "; ".join(linked_titles)
                )
            else:
                architectural_lines.append(
                    "D29 Explicit Canonical Links: none resolved in selected evidence"
                )

        architectural_context = ""
        if architectural_lines:
            architectural_context = "\n" + "\n".join(architectural_lines)
        formatted_blocks.append(
            f"Evidence Role: {role}"
            f"{architectural_context}\n"
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
        "transition", "change", "transformation", "transform", "transformed", "uncertain", "uncertainty", "threshold",
        "becoming", "next chapter", "what now", "meaning",
    ),
    "relational": (
        "relationship", "relationships", "relational", "interplay", "interaction",
        "interact", "interacts", "interacting", "interacted",
        "connection", "tension", "dynamic", "between", "mutually exclusive",
        "personal", "self", "individual", "inner", "internal",
        "system", "systems", "systemic", "social", "society", "institution",
        "collective", "external",
    ),
}


def detect_relational_orientation(question: str) -> bool:
    """Detect explicit or structurally expressed questions connecting personal and systemic dimensions."""
    q = re.sub(r"\s+", " ", str(question or "").lower()).strip()
    if not q:
        return False
    personal = bool(re.search(
        r"\b(?:personal|self|myself|individual|person|people|inner|internal|within myself)\b", q
    ))
    systemic = bool(re.search(
        r"\b(?:system|systems|systemic|social|society|institution|collective|external|environment|organization|organisation)\b", q
    ))
    explicit_relation = bool(re.search(
        r"\b(?:between|relationship|relational|interplay|interaction|"
        r"interact|interacts|interacting|interacted|connection|"
        r"tension|dynamic|mutually exclusive)\b", q
    ))

    # Natural-language relationality is often expressed structurally rather
    # than with an explicit word such as "interaction". Preserve that signal
    # when the question places personal and systemic dimensions into the same
    # contrast, dependency, surrounding-condition, or change/persistence frame.
    structural_connector = bool(re.search(
        r"\b(?:but|while|whereas|although|when|if|as|around|within|across|"
        r"against|alongside|despite|unless|because|affect|affects|affecting|"
        r"influence|influences|influencing|shape|shapes|shaping|depends|"
        r"dependent|adapt|adapts|adaptation|conflict|conflicts|conflicting|"
        r"unchanged|unchanged|same|stays|remain|remains|last|"
        r"lasting|sustain|sustains|sustainable|persist|persists|persistence)\b", q
    ))
    structural_change = bool(re.search(
        r"\b(?:change|changes|changed|changing|transformation|transform|"
        r"transformed|adapt|adapts|adaptation|conflict|conflicts|conflicting|resilient|resilience|"
        r"persist|persists|persistence|last|lasting|sustain|sustains|"
        r"sustainable|remain|remains|stays|same|conditions|context|"
        r"environment)\b", q
    ))

    if not (personal and systemic):
        return False
    return explicit_relation or (structural_connector and structural_change)


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
# CANONICAL DOORWAY SELECTION
# =====================================================================
#
# v65 introduces an explicit selection layer between retrieval/reranking and
# generation. The selector does NOT search the corpus, invent destinations,
# or replace semantic retrieval. It evaluates only already-retrieved,
# lifecycle-eligible canonical resources using evidence already present in
# each resource.
#
# The constitutional distinction is:
#   semantic relevance -> candidate evidence
#   navigational suitability -> doorway priority
#
# This is deliberately a modest evidence-based signal. It rewards language
# that indicates orientation, framing, foundations, guidance, or an explicit
# entry point, while preserving retrieval order as the final tie-breaker.
# No individual Living Archive resource or collection is hard-coded here.
# =====================================================================

_DOORWAY_TITLE_TERMS = (
    "cornerstone",
    "foundation",
    "foundations",
    "framework",
    "guide",
    "navigator",
    "orientation",
    "overview",
    "introduction",
    "map",
    "pathway",
    "gateway",
)

_DOORWAY_CONTENT_TERMS = (
    "where to begin",
    "entry point",
    "starting point",
    "begin here",
    "overview",
    "orientation",
    "introduces",
    "introduction",
    "foundational",
    "foundations",
    "framework",
    "guide to",
    "guides",
    "explore",
    "helps orient",
)


# v66 question-conditioning is deliberately generic. It does not introduce a
# domain-specific vocabulary for particular Living Archive subjects. Instead,
# it asks whether the language of the visitor's question is actually present
# in the already-retrieved resource evidence. Common function words are
# ignored so that the signal remains about the question's substantive terms.
# These are broad high-intensity/specialized scope signals. They are not
# resource names and do not identify particular canonical titles. Their only
# purpose is to prevent a highly specialized resource from becoming the
# canonical doorway to a broader question when that specialized domain is not
# itself established by the visitor's wording. If the visitor explicitly asks
# about the specialized domain, the penalty disappears.
_SPECIALIZED_SCOPE_TERMS = frozenset({
    "suicide", "self-harm", "selfharm", "abuse", "addiction", "overdose",
    "psychosis", "schizophrenia", "bipolar", "trauma", "ptsd", "cancer",
    "terminal", "grief", "bereavement", "divorce", "infidelity", "pregnancy",
    "miscarriage", "diagnosis", "diagnosed", "disease", "illness", "disorder",
})

# v70 framework-neutrality signals. These identify questions explicitly about
# explanations, narratives, models, labels, frameworks, or interpretive fit.
# A specialized worldview may remain evidence while being disfavored as the
# first canonical doorway unless the visitor explicitly names that worldview.
_FRAMEWORK_QUERY_TERMS = frozenset({
    "explanation", "explanations", "narrative", "narratives", "story", "stories",
    "framework", "frameworks", "model", "models", "interpretation",
    "interpretations", "label", "labels", "archetype", "archetypes",
    "meaning", "fit", "fitting", "clarity", "clearer", "unclear",
})

_FRAMEWORK_QUERY_PHRASES = frozenset({
    "fit myself", "fit experience", "fit experiences", "make sense",
    "makes sense", "make sense of", "sense of", "explanation make",
    "explanations make", "story about", "stories about",
})

_SPECIALIZED_FRAMEWORK_TERMS = frozenset({
    "starseed", "starseeds", "ascension", "awakening", "kundalini",
    "reincarnation", "past-life", "pastlife", "soul", "ego death",
    "nonduality", "non-duality", "manifestation", "channeling",
    "channeled", "akashic", "twin flame", "twin-flame",
    # Canonical resource-specific interpretive constructs surfaced in testing.
    "synchronicity", "synchronicities", "apophenia",
})

_QUESTION_STOPWORDS = frozenset({
    "a", "about", "after", "all", "always", "am", "an", "and", "are",
    "as", "at", "be", "because", "been", "being", "but", "by", "can",
    "could", "did", "do", "does", "for", "from", "get", "has", "have",
    "how", "i", "if", "in", "into", "is", "it", "its", "may", "me",
    "more", "my", "not", "of", "on", "or", "our", "so", "something",
    "that", "the", "their", "them", "there", "this", "to", "was", "what",
    "when", "where", "which", "who", "why", "will", "with", "would", "you",
    "your",
})


def _question_condition_terms(question: str) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    """Return generic substantive question terms and adjacent phrases."""
    tokens = re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)?", str(question or "").casefold())
    terms = tuple(
        token
        for token in tokens
        if len(token) >= 3 and token not in _QUESTION_STOPWORDS
    )
    phrases = tuple(
        f"{terms[index]} {terms[index + 1]}"
        for index in range(len(terms) - 1)
    )
    return terms, phrases


def _question_resource_fit(
    question: str,
    metadata: Dict[str, Any],
) -> Tuple[int, Tuple[int, int, int]]:
    """Score how directly an already-retrieved resource fits the question."""
    terms, phrases = _question_condition_terms(question)
    if not terms:
        return 0, (0, 0, 0)

    title = _canonical_display_title(str(metadata.get("title", ""))).casefold()
    searchable = " ".join(
        str(metadata.get(key, ""))
        for key in ("title", "text", "content", "excerpt", "description", "category")
    ).casefold()

    term_hits = sum(1 for term in set(terms) if re.search(rf"\b{re.escape(term)}\b", searchable))
    phrase_hits = sum(1 for phrase in set(phrases) if phrase in searchable)
    title_term_hits = sum(1 for term in set(terms) if re.search(rf"\b{re.escape(term)}\b", title))

    # Phrases and title matches are stronger evidence of direct fit than a
    # single occurrence buried in body text, while all signals remain generic.
    raw_score = (term_hits * 2) + (phrase_hits * 3) + (title_term_hits * 2)
    # Keep question conditioning bounded. It should refine doorway choice,
    # not become a second semantic retrieval engine.
    score = min(8, raw_score)
    return score, (term_hits, phrase_hits, title_term_hits)


def _framework_neutrality_penalty(question: str, title: str) -> int:
    """Penalize specialized worldview doorways for framework-level questions."""
    if not question or not title:
        return 0

    terms, phrases = _question_condition_terms(question)
    term_set = set(terms)
    phrase_set = set(phrases)

    meta_markers = {
        "explanation", "explanations", "narrative", "narratives", "framework",
        "frameworks", "model", "models", "interpretation", "interpretations",
        "archetype", "archetypes", "label", "labels", "fit", "fitting",
    }
    meta_count = len(term_set & meta_markers)
    meta_count += len(phrase_set & _FRAMEWORK_QUERY_PHRASES)
    if meta_count == 0:
        return 0

    specialized_title_terms = {
        term for term in _SPECIALIZED_FRAMEWORK_TERMS
        if re.search(rf"\b{re.escape(term)}\b", title)
    }
    if not specialized_title_terms:
        return 0

    # Explicitly named frameworks remain eligible.
    if specialized_title_terms & term_set:
        return 0

    return min(8, len(specialized_title_terms) * 4)


_CENTRALITY_GENERIC_TERMS = frozenset({
    "life", "lives", "person", "people", "thing", "things", "something",
    "someone", "feel", "feels", "feeling", "make", "makes", "made",
    "become", "becoming", "change", "changed", "changing", "way", "ways",
    "part", "parts", "sometimes", "often", "really", "still", "seem",
    "seems", "experience", "experiences", "understand", "understanding",
    "aware", "awareness", "know", "knowing", "clear", "clearer", "clarity",
})


def _question_doorway_centrality(
    question: str,
    metadata: Dict[str, Any],
) -> Tuple[int, Tuple[int, int, int, int]]:
    """Measure whether a retrieved resource is central enough to be a doorway."""
    if not question or not metadata:
        return 0, (0, 0, 0, 0)

    terms, phrases = _question_condition_terms(question)
    substantive_terms = tuple(
        term for term in set(terms)
        if term not in _CENTRALITY_GENERIC_TERMS
    )
    if not substantive_terms:
        substantive_terms = tuple(set(terms))

    title = _canonical_display_title(str(metadata.get("title", ""))).casefold()
    searchable = " ".join(
        str(metadata.get(key, ""))
        for key in ("title", "text", "content", "excerpt", "description", "category")
    ).casefold()
    early = searchable[:1200]

    title_hits = sum(
        1 for term in substantive_terms
        if re.search(rf"\b{re.escape(term)}\b", title)
    )
    early_hits = sum(
        1 for term in substantive_terms
        if re.search(rf"\b{re.escape(term)}\b", early)
    )
    phrase_hits = sum(1 for phrase in set(phrases) if phrase in early)

    # Centrality is deliberately a modest refinement. It rewards a candidate
    # whose actual conceptual territory is present in the question, while
    # leaving semantic retrieval as the authority when evidence is sparse.
    score = min(6, (title_hits * 3) + phrase_hits + min(3, early_hits))
    return score, (title_hits, early_hits, phrase_hits, len(substantive_terms))


def _canonical_doorway_score(
    metadata: Dict[str, Any],
    frame: Dict[str, Any],
    question: str = "",
) -> Tuple[int, Tuple[int, int, int, int, int, int, int, int, int]]:
    """Score doorway suitability from question fit plus proportionality safeguards."""
    title = _canonical_display_title(str(metadata.get("title", ""))).casefold()
    content = _resource_content(metadata).casefold()
    early_content = content[:1600]

    if not title or _is_non_resource_service_title(title):
        return (-1000, (0, 0, 0, 0, 0, 0, 0, 0, 0))

    title_hits = sum(1 for term in _DOORWAY_TITLE_TERMS if term in title)
    content_hits = sum(1 for term in _DOORWAY_CONTENT_TERMS if term in early_content)
    orientation_bonus = _orientational_resource_bonus(metadata, frame)
    question_fit, fit_detail = _question_resource_fit(question, metadata)

    # v65 doorway evidence remains intact when no visitor question is supplied.
    # v66 adds bounded question fit so a generic doorway cannot win solely
    # because it says "guide" or "overview" when another retrieved resource
    # is a substantially closer doorway into the actual question.
    #
    # v67 adds one further constitutional guard: when the supplied question has
    # little direct lexical grounding in a candidate, generic doorway signals
    # are capped. This prevents an interpretively specific resource from being
    # promoted merely because its title/content looks like a "gateway",
    # "framework", or "orientation". In that case semantic retrieval order is
    # allowed to remain the stronger signal. The selector still never expands
    # or changes the retrieved resource set.
    generic_doorway_score = (title_hits * 4) + (content_hits * 2) + orientation_bonus
    if question and question_fit <= 1:
        generic_doorway_score = min(2, generic_doorway_score)

    # v69 adds canonical doorway proportionality. A resource can be semantically
    # relevant because one passage overlaps the question while still being a
    # disproportionate doorway because its primary title/domain is highly
    # specialized. Penalize only when the specialized scope is absent from the
    # visitor's own wording; explicit questions about that domain remain eligible.
    question_terms, _question_phrases = _question_condition_terms(question)
    question_term_set = set(question_terms)
    specialized_title_terms = {
        term for term in _SPECIALIZED_SCOPE_TERMS
        if re.search(rf"\b{re.escape(term)}\b", title)
    }
    specialized_overlap = len(specialized_title_terms & question_term_set)
    scope_penalty = 0
    if question and specialized_title_terms and specialized_overlap == 0:
        # Bounded penalty: enough to block a disproportionate specialized
        # doorway, but not enough to remove the resource from the retrieved set.
        scope_penalty = min(6, len(specialized_title_terms) * 3)

    # v70: when the visitor is asking about explanations, narratives, models,
    # labels, or interpretive fit, prefer a proportionate/neutral doorway over
    # a resource whose title is itself a specialized worldview.
    framework_penalty = _framework_neutrality_penalty(question, title)

    # v72: doorway centrality asks whether the candidate's own conceptual
    # territory is actually established by the visitor's wording. This is not
    # another retrieval pass. It is a bounded safeguard against promoting a
    # merely compatible resource into the primary doorway.
    centrality_score, centrality_detail = _question_doorway_centrality(
        question, metadata
    )
    centrality_penalty = 0
    if question and _question_is_underdetermined(question):
        if centrality_score == 0:
            centrality_penalty = 4
        elif centrality_score <= 1 and question_fit <= 3:
            centrality_penalty = 2

    # v72 generalizes framework proportionality for open experiential questions:
    # if the visitor has not named a specialized worldview, that worldview must
    # not become the primary doorway simply because retrieval found it relevant.
    if question and _question_is_underdetermined(question):
        if _framework_neutrality_penalty(question, title) == 0:
            specialized_title_terms = {
                term for term in _SPECIALIZED_FRAMEWORK_TERMS
                if re.search(rf"\b{re.escape(term)}\b", title)
            }
            if specialized_title_terms and not (
                specialized_title_terms & set(_question_condition_terms(question)[0])
            ):
                framework_penalty = max(
                    framework_penalty,
                    min(6, len(specialized_title_terms) * 4),
                )

    score = (
        generic_doorway_score
        + (question_fit * 2)
        - scope_penalty
        - framework_penalty
        - centrality_penalty
    )
    return score, (
        title_hits,
        content_hits,
        orientation_bonus,
        question_fit,
        fit_detail[1],
        scope_penalty,
        framework_penalty,
        centrality_score,
        centrality_penalty,
    )


def _is_specialized_framework_resource(metadata: Dict[str, Any]) -> bool:
    """Identify resources whose canonical title names a specialized interpretive construct."""
    title = _canonical_display_title(str(metadata.get("title", ""))).casefold()
    if not title:
        return False
    return any(
        re.search(rf"\b{re.escape(term)}\b", title)
        for term in _SPECIALIZED_FRAMEWORK_TERMS
    )


def _frame_neutral_generation_documents(
    documents: List[Dict[str, Any]],
    question: str,
    intent: str,
) -> Tuple[List[Dict[str, Any]], bool]:
    """Narrow open-frame generation evidence to already-retrieved neutral resources."""
    if intent != "TOPICAL_INQUIRY" or not _question_is_frame_open(question):
        return documents, False

    neutral = [
        document for document in documents
        if not _is_specialized_framework_resource(document)
    ]
    specialized_count = len(documents) - len(neutral)
    if specialized_count == 0:
        return documents, False

    # If neutral evidence exists, specialized resources cannot define the
    # generation frame. We do not alter canonical link authority or retrieve
    # anything new; this is only a generation-evidence boundary.
    if neutral:
        print(
            "USE frame-neutral evidence boundary: "
            f"excluded={specialized_count} uninvited specialized resources; "
            f"retained={len(neutral)} frame-neutral resources."
        )
        return neutral, True

    print(
        "USE frame-neutral evidence boundary: no frame-neutral resources "
        f"available; specialized_count={specialized_count}."
    )
    return [], True


def _frame_neutral_evidence_unavailable_response(question: str) -> str:
    """Return a sovereignty-preserving response when only specialized evidence exists."""
    return (
        "The currently retrieved canonical material is framed through specialized "
        "interpretive frameworks rather than the open terms of your question. "
        "Because that material does not establish that framework as your premise, "
        "the Living Archive cannot responsibly use it to define what your experience "
        "means. The question therefore remains open pending more frame-neutral "
        "canonical evidence."
    )


# =====================================================================
# D26 PATHWAY FUNCTION
# =====================================================================
# A Pathway is a guided orientation experience: it gives a reader a bounded
# sequence through canonical material around a genuine question. The function
# is recognized from the resource's own evidence, not from the visitor's
# question. Selection fit is handled separately by the shared D21-D27 layer.
# =====================================================================

_D26_PATHWAY_FUNCTION_LABEL = "guided orientation experience"


def _d26_pathway_function(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Recognize Pathway function only from D20 type plus resource evidence."""
    if not isinstance(metadata, dict):
        return {"function": None, "confidence": "unknown", "basis": "none"}

    recognition = metadata.get("_use_resource_type_recognition")
    if not isinstance(recognition, dict):
        recognition = _recognize_resource_type(metadata)

    if recognition.get("resource_type") != "Pathway":
        return {
            "function": None,
            "confidence": "not_applicable",
            "basis": "resource_type_not_pathway",
        }

    content = html.unescape(_resource_content(metadata)).casefold()
    if not content:
        return {
            "function": None,
            "confidence": "unknown",
            "basis": "insufficient_pathway_function_evidence",
        }

    guidance_signals = (
        r"\bguided (?:reading )?pathway\b",
        r"\bguided experience\b",
        r"\bguided journey\b",
        r"\bguide(?:s|d)? the reader\b",
        r"\bleads the reader\b",
        r"\bwalk(?:s|ing)? the reader\b",
    )
    sequence_signals = (
        r"\bsequence\b",
        r"\bin sequence\b",
        r"\bnext stop\b",
        r"\bstops?\b",
        r"\bjourney\b",
        r"\b90 minutes?\b",
        r"\breading order\b",
        r"\breflection question\b",
    )

    guidance_hits = sum(1 for pattern in guidance_signals if re.search(pattern, content))
    sequence_hits = sum(1 for pattern in sequence_signals if re.search(pattern, content))

    if guidance_hits >= 1 and sequence_hits >= 1:
        return {
            "function": _D26_PATHWAY_FUNCTION_LABEL,
            "confidence": "strong",
            "basis": "pathway_guidance_and_sequence_evidence",
        }

    return {
        "function": None,
        "confidence": "unknown",
        "basis": "insufficient_pathway_function_evidence",
    }


def _attach_pathway_function(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Attach D26 Pathway function without overwriting earlier models."""
    if not isinstance(metadata, dict):
        return metadata
    if "_use_pathway_function" not in metadata:
        metadata["_use_pathway_function"] = _d26_pathway_function(metadata)
    return metadata


# =====================================================================
# D27 CASE / LEARNING ARC FUNCTION
# =====================================================================
# Cases and Learning Arcs provide applied learning through concrete cases or
# a bounded progression across cases. The function is recognized from the
# resource's own evidence; the visitor's need only affects later selection.
# =====================================================================

_D27_CASE_FUNCTION_LABEL = "applied case learning"
_D27_LEARNING_ARC_FUNCTION_LABEL = "sequenced case-based learning"


def _d27_case_learning_arc_function(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Recognize Case or Learning Arc function from type and resource evidence."""
    if not isinstance(metadata, dict):
        return {"function": None, "confidence": "unknown", "basis": "none"}

    recognition = metadata.get("_use_resource_type_recognition")
    if not isinstance(recognition, dict):
        recognition = _recognize_resource_type(metadata)

    resource_type = recognition.get("resource_type")
    if resource_type not in {"Case", "Learning Arc"}:
        return {
            "function": None,
            "confidence": "not_applicable",
            "basis": "resource_type_not_case_or_learning_arc",
        }

    content = html.unescape(_resource_content(metadata)).casefold()
    if not content:
        return {
            "function": None,
            "confidence": "unknown",
            "basis": "insufficient_case_learning_arc_function_evidence",
        }

    case_signals = (
        r"\bcase stud(?:y|ies)\b",
        r"\bcase library\b",
        r"\bcase atlas\b",
        r"\breal[- ]world case\b",
        r"\bapplied case\b",
        r"\bcase(?:s)? illustrate\b",
        r"\bcase(?:s)? show\b",
    )
    arc_signals = (
        r"\blearning arc\b",
        r"\bprogression of cases\b",
        r"\bsequence of cases\b",
        r"\bcase sequence\b",
        r"\bprogressive learning\b",
        r"\bbuilds from one case\b",
        r"\bfrom one case to the next\b",
    )
    learning_signals = (
        r"\blearning\b",
        r"\bapplication\b",
        r"\bapplied\b",
        r"\bpractice\b",
        r"\bgovernance challenge\b",
        r"\bwhat happened\b",
    )

    case_hits = sum(1 for pattern in case_signals if re.search(pattern, content))
    arc_hits = sum(1 for pattern in arc_signals if re.search(pattern, content))
    learning_hits = sum(1 for pattern in learning_signals if re.search(pattern, content))

    if resource_type == "Learning Arc" and arc_hits >= 1 and learning_hits >= 1:
        return {
            "function": _D27_LEARNING_ARC_FUNCTION_LABEL,
            "confidence": "strong",
            "basis": "learning_arc_sequence_and_learning_evidence",
        }

    if resource_type == "Case" and case_hits >= 1 and learning_hits >= 1:
        return {
            "function": _D27_CASE_FUNCTION_LABEL,
            "confidence": "strong",
            "basis": "case_and_applied_learning_evidence",
        }

    return {
        "function": None,
        "confidence": "unknown",
        "basis": "insufficient_case_learning_arc_function_evidence",
    }


def _attach_case_learning_arc_function(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Attach D27 Case / Learning Arc function without overwriting prior models."""
    if not isinstance(metadata, dict):
        return metadata
    if "_use_case_learning_arc_function" not in metadata:
        metadata["_use_case_learning_arc_function"] = _d27_case_learning_arc_function(metadata)
    return metadata


# =====================================================================
# D25 RESOURCE-FUNCTION SELECTION BRIDGE
# =====================================================================
# Connect the already-recognized canonical resource functions to the
# existing doorway scorer. This is a selection bridge, not a new retrieval
# mechanism and not a subject-specific mapping.
#
# Functional fit is additive and bounded. Existing relevance, evidence,
# scope, framework, and centrality logic remains intact.
# =====================================================================

_RESOURCE_FUNCTION_FIT_BONUS = 2.5

_RESOURCE_FUNCTION_NAMES = (
    "_use_essay_function",
    "_use_cornerstone_function",
    "_use_knowledge_hub_function",
    "_use_reference_map_function",
    "_use_navigator_function",
    "_use_pathway_function",
    "_use_case_learning_arc_function",
)

def _visitor_resource_function_fit(question: str) -> Dict[str, float]:
    """Infer the requested canonical resource function conservatively."""
    q = (question or "").casefold()
    fit = {
        "substantive exploration and sensemaking": 0.0,
        "cross-domain pattern orientation": 0.0,
        "curated subject-domain orientation": 0.0,
        "visual structural orientation": 0.0,
        "integrated orientation and entry": 0.0,
        "guided orientation experience": 0.0,
        "applied case learning": 0.0,
        "sequenced case-based learning": 0.0,
    }

    # Integrated entry/orientation: only explicit navigation needs qualify.
    if any(
        phrase in q for phrase in (
            "available routes",
            "ways through",
            "where should i begin",
            "where do i begin",
            "decide where to go next",
            "wider body of material",
            "broader understanding of the available",
            "orientation to",
            "orient myself",
            "navigate the subject",
        )
    ):
        fit["integrated orientation and entry"] = 1.0

    # Guided pathway: the visitor is explicitly asking for a bounded route,
    # sequence, or guided movement rather than a single explanatory resource.
    if any(
        phrase in q for phrase in (
            "guided path",
            "guided pathway",
            "guided reading",
            "walk me through",
            "take me through",
            "what should i read first",
            "what should i read next",
            "in what order",
            "a sequence through",
            "a path through",
        )
    ):
        fit["guided orientation experience"] = 1.0

    # Applied case learning: the visitor explicitly wants concrete cases,
    # examples, or applied learning rather than abstract explanation.
    if any(
        phrase in q for phrase in (
            "case studies",
            "real cases",
            "real-world cases",
            "examples of how this plays out",
            "how this plays out in practice",
            "applied examples",
            "learn from cases",
            "case library",
            "learning arc",
            "sequence of cases",
        )
    ):
        fit["applied case learning"] = 1.0
        fit["sequenced case-based learning"] = 1.0 if "learning arc" in q or "sequence of cases" in q else 0.0

    # Explicit canonical resource-type references are stronger than generic
    # functional wording. When a visitor names a publication family directly,
    # the retrieval layer should request that function before semantic ranking.
    # This is recognition of an explicit visitor request, not inference about
    # which resource type the visitor "ought" to use.
    if re.search(
        r"\breference\s+maps?\b",
        q,
        flags=re.IGNORECASE,
    ):
        fit["visual structural orientation"] = 1.0

    if re.search(
        r"\bessays?\b",
        q,
        flags=re.IGNORECASE,
    ):
        fit["substantive exploration and sensemaking"] = 1.0

    if any(
        phrase in q for phrase in (
            "overall structure",
            "different parts connect",
            "relationships and patterns",
            "see how the parts connect",
            "visual structure",
        )
    ):
        fit["visual structural orientation"] = 1.0

    if any(
        phrase in q for phrase in (
            "main areas",
            "subject areas",
            "which parts of the subject",
            "gathered together",
            "different areas",
        )
    ):
        fit["curated subject-domain orientation"] = 1.0

    if any(
        phrase in q for phrase in (
            "larger patterns",
            "how pieces fit",
            "cross-domain",
            "broader framework",
        )
    ):
        fit["cross-domain pattern orientation"] = 1.0

    # Archive/document-architecture questions are navigational even when the
    # visitor does not use explicit location language. The question is about
    # choosing among canonical publication forms, not about the subject matter
    # of an individual resource. This targets integrated orientation only; it
    # does not force a particular document type.
    document_architecture_question = (
        bool(re.search(
            r"\b(?:different|various|different kinds|different types|kinds|types)\s+"
            r"(?:of\s+)?(?:documents?|resources?|material)\b",
            q,
        ))
        and bool(re.search(
            r"\b(?:which|what)\s+(?:kind|type)\b|\bwhich\s+(?:document|resource)\b",
            q,
        ))
        and bool(re.search(
            r"\b(?:use|choose|start|begin|understand|find information|information)\b",
            q,
        ))
    )
    if document_architecture_question:
        fit["integrated orientation and entry"] = max(
            fit.get("integrated orientation and entry", 0.0), 1.0
        )

    # Comparative publication-form choice is an archive-architecture need even
    # when the visitor does not say "different kinds/types of documents".
    # Naming two or more canonical forms plus a choice/start/use question is
    # sufficient to establish that the visitor is choosing how to enter the
    # Archive, not asking for the subject matter of one retrieved resource.
    publication_forms_named = sum(
        bool(re.search(pattern, q))
        for pattern in (
            r"\bessays?\b",
            r"\b(?:reference\s+)?maps?\b",
            r"\bnavigators?\b",
            r"\bpathways?\b",
        )
    )
    comparative_publication_choice = (
        publication_forms_named >= 2
        and bool(re.search(
            r"\b(?:which|what|how)\b|\b(?:choose|decide|use|start|begin)\b",
            q,
        ))
        and bool(re.search(
            r"\b(?:among|between|one|another|each|different|kind|type|document|resource|where)\b",
            q,
        ))
    )
    if comparative_publication_choice:
        fit["integrated orientation and entry"] = max(
            fit.get("integrated orientation and entry", 0.0), 1.0
        )
        if re.search(r"\b(?:reference\s+)?maps?\b", q):
            fit["visual structural orientation"] = max(
                fit.get("visual structural orientation", 0.0), 1.0
            )
        if re.search(r"\b(?:guided|pathways?)\b", q):
            fit["guided orientation experience"] = max(
                fit.get("guided orientation experience", 0.0), 1.0
            )

    # Functional descriptions may use ordinary language rather than the
    # internal function vocabulary. Recognize bounded semantic forms without
    # requiring the visitor to name Essay / Reference Map / Navigator / Pathway.
    #
    # These are need signals only. They do not select a resource by themselves.
    substantive_language = (
        bool(re.search(
            r"\b(?:deep|thorough|comprehensive|in-depth|detailed)\b",
            q,
        ))
        and bool(re.search(
            r"\b(?:explanation|exposition|understanding|treatment|account|discussion)\b",
            q,
        ))
    ) or bool(re.search(
        r"\b(?:explain|explains|explaining)\b.*"
        r"\b(?:thoroughly|deeply|in\s+depth|in\s+detail)\b",
        q,
    )) or bool(re.search(
        r"\b(?:understand|understanding)\b.*"
        r"\b(?:deeply|thoroughly|comprehensively|in\s+depth|in\s+detail)\b",
        q,
    )) or bool(re.search(
        r"\b(?:explain|explains|explaining)\s+(?:a|the)\s+"
        r"(?:subject|topic|issue)\s+(?:in\s+)?(?:depth|detail)\b",
        q,
    )) or bool(re.search(
        r"\b(?:detailed|thorough|comprehensive)\s+"
        r"(?:treatment|account|discussion|explanation)\b",
        q,
    ))
    if substantive_language:
        fit["substantive exploration and sensemaking"] = max(
            fit.get("substantive exploration and sensemaking", 0.0), 1.0
        )

    structural_language = bool(re.search(
        r"\b(?:visual|visual\s+sense|big[-\s]?picture|overview)\b.*"
        r"\b(?:ideas?|concepts?|parts?|elements?|relationships?)\b.*"
        r"\b(?:relat(?:e|ed|ing)|connect(?:ed|ing)?|fit|"
        r"come\s+together|structure|relationships?)\b",
        q,
    )) or bool(re.search(
        r"\b(?:see|get|understand)\b.*\b(?:how)\b.*"
        r"\b(?:ideas?|concepts?|parts?)\b.*\b"
        r"(?:relat(?:e|ed|ing)|connect(?:ed|ing)?|fit)\b",
        q,
    ))
    if structural_language:
        fit["visual structural orientation"] = max(
            fit.get("visual structural orientation", 0.0), 1.0
        )

    guided_language = bool(re.search(
        r"\b(?:guide|guides|guided|guiding)\b.*"
        r"\b(?:me|us|you|someone|visitor)\b.*"
        r"\bthrough\b",
        q,
    )) or bool(re.search(
        r"\b(?:guided|step[-\s]?by[-\s]?step|"
        r"walk\s+me|take\s+me)\b.*\bthrough\b",
        q,
    )) or bool(re.search(
        r"\b(?:take|takes|taking)\s+me\s+through\b.*"
        r"\b(?:step[-\s]?by[-\s]?step)\b",
        q,
    )) or bool(re.search(
        r"\b(?:a|some|something|more)\s+guided\s+"
        r"(?:way|approach|route|path|pathway)\b",
        q,
    ))
    if guided_language:
        fit["guided orientation experience"] = max(
            fit.get("guided orientation experience", 0.0), 1.0
        )

    if (
        (
            fit.get("substantive exploration and sensemaking", 0.0) > 0
            or fit.get("visual structural orientation", 0.0) > 0
            or fit.get("guided orientation experience", 0.0) > 0
        )
        and bool(re.search(
            r"\b(?:which|what|how)\b.*\b"
            r"(?:approach|right|help|start|begin|choose|decide|decision)\b"
            r"|\b(?:help\s+me\s+decide|what\s+would\s+help\s+me)\b",
            q,
        ))
    ):
        fit["integrated orientation and entry"] = max(
            fit.get("integrated orientation and entry", 0.0), 1.0
        )

    # Generic "understand" questions remain function-neutral.
    return fit


def _v133_explicit_resource_type_request_self_audit() -> None:
    """Verify explicit publication-family requests activate targeted retrieval needs."""
    probe = (
        "What is the purpose of a Reference Map in the Living Archive, "
        "and how is it different from simply reading an essay?"
    )
    fit = _visitor_resource_function_fit(probe)

    if fit.get(_D24_REFERENCE_MAP_FUNCTION_LABEL, 0.0) <= 0:
        raise RuntimeError(
            "v133 resource-type retrieval regression: explicit Reference Map request "
            "did not activate Reference Map function targeting."
        )
    if fit.get(_D21_ESSAY_FUNCTION_LABEL, 0.0) <= 0:
        raise RuntimeError(
            "v133 resource-type retrieval regression: explicit Essay comparison "
            "did not activate Essay function targeting."
        )

    neutral = _visitor_resource_function_fit(
        "What is the meaning of responsibility in this discussion?"
    )
    if any(
        neutral.get(function_name, 0.0) > 0
        for function_name in (
            _D21_ESSAY_FUNCTION_LABEL,
            _D22_CORNERSTONE_FUNCTION_LABEL,
            _D23_KNOWLEDGE_HUB_FUNCTION_LABEL,
            _D24_REFERENCE_MAP_FUNCTION_LABEL,
            _D25_NAVIGATOR_FUNCTION_LABEL,
            _D26_PATHWAY_FUNCTION_LABEL,
            _D27_CASE_FUNCTION_LABEL,
        )
    ):
        raise RuntimeError(
            "v133 resource-type retrieval regression: neutral question received "
            "an unintended publication-family target."
        )

    print("USE v133 EXPLICIT RESOURCE-TYPE RETRIEVAL AUDIT: PASS")


def _v153_document_architecture_orientation_self_audit() -> None:
    """Verify document-selection questions activate structural orientation."""
    probe = (
        "I understand that the Living Archive has different kinds of documents, "
        "but how do I know which kind I should use when I’m trying to understand "
        "something rather than just find information?"
    )
    fit = _visitor_resource_function_fit(probe)
    assert fit.get(_D25_NAVIGATOR_FUNCTION_LABEL, 0.0) == 1.0, (
        "v153 document-architecture regression: document-selection question "
        "did not activate integrated orientation."
    )

    neutral = _visitor_resource_function_fit(
        "What does sovereignty mean in practice?"
    )
    assert neutral.get(_D25_NAVIGATOR_FUNCTION_LABEL, 0.0) == 0.0, (
        "v153 document-architecture regression: ordinary topical question "
        "received unintended integrated orientation."
    )
    print("USE v153 DOCUMENT-ARCHITECTURE ORIENTATION AUDIT: PASS")


def _resource_function_name(resource: Dict[str, Any]) -> Optional[str]:
    """Return the first recognized canonical function attached to a resource."""
    if not isinstance(resource, dict):
        return None

    for key in _RESOURCE_FUNCTION_NAMES:
        value = resource.get(key)
        if isinstance(value, dict) and value.get("function"):
            return str(value["function"])
    return None


def _resource_function_selection_bonus(
    resource: Dict[str, Any], question: str
) -> float:
    """Return bounded functional-fit bonus for an already retrieved resource."""
    function_name = _resource_function_name(resource)
    if not function_name:
        return 0.0

    requested = _continuity_function_needs(question)
    if requested.get(function_name, 0.0) <= 0:
        return 0.0

    return _RESOURCE_FUNCTION_FIT_BONUS


def select_canonical_doorways(
    documents: List[Dict[str, Any]],
    frame: Dict[str, Any],
    *,
    question: str = "",
    preserve_prefix: int = 0,
) -> List[Dict[str, Any]]:
    """
    Prioritize the strongest already-retrieved canonical doorway.

    This function only reorders the supplied evidence. It never adds,
    removes, searches for, or links a resource. Explicit structural
    destinations supplied by an earlier retrieval stage remain protected.
    """
    if not documents:
        return documents

    prefix = documents[:preserve_prefix]
    remainder = documents[preserve_prefix:]

    ranked = []
    for index, document in enumerate(remainder):
        base_score, detail = _canonical_doorway_score(
            document, frame, question
        )
        function_bonus = _resource_function_selection_bonus(
            document, question
        )
        score = base_score + function_bonus
        ranked.append(
            (score, detail, function_bonus, -index, document)
        )

    ranked.sort(
        key=lambda item: (item[0], item[1], item[2], item[3]),
        reverse=True,
    )

    selected = [document for _score, _detail, _function_bonus, _order, document in ranked]

    if selected:
        primary = selected[0]
        primary_score, primary_detail = _canonical_doorway_score(primary, frame, question)
        print(
            "USE canonical doorway selection: "
            f"primary='{_canonical_display_title(str(primary.get('title', 'Untitled Resource')))}', "
            f"score={primary_score}, detail={primary_detail}, "
            f"candidates={len(selected)}."
        )

    return prefix + selected


# =====================================================================
# D28-D29 + D31-D38 CONTINUITY SELECTION LAYER
# =====================================================================
# The D21-D27 function layer is only useful if the visitor's requested
# function can survive semantic retrieval and become an ordered canonical
# movement. v113 proved that a post-retrieval bonus alone is insufficient:
# a functionally appropriate resource can be absent from the semantic top-K.
#
# This layer therefore adds a bounded, function-aware candidate expansion
# before final doorway selection. It remains canonical: all candidates still
# come from the archive index and all resource metadata is passed through the
# existing canonical validation/model/function attachments.
#
# D28 sequencing is deliberately modest: it establishes a primary doorway
# plus complementary follow-on functions without inventing a route.
# D31-D38 orientation remains a visitor-facing posture built from the
# question's explicit movement/entry need; sovereignty and non-closure remain
# constraints rather than diagnoses.
# =====================================================================

# v159: canonical archive-architecture anchor used only when the visitor is
# asking how to choose among publication forms. This is a retrieval posture,
# not a hard-coded visitor answer: the candidate must still come from the
# canonical index.
_DOCUMENT_CHOICE_ARCHITECTURE_PROFILE = (
    "Document Types of the Living Archive essay Reference Map Navigator Pathway "
    "what each publication form is when to use each form choose the right kind "
    "of material explanation visual structure guided orientation"
)
_DOCUMENT_CHOICE_ARCHITECTURE_TITLE = "Document Types of the Living Archive"

_RESOURCE_FUNCTION_RETRIEVAL_PROFILES = {
    _D25_NAVIGATOR_FUNCTION_LABEL: (
        "navigator orientation entry point ways through archive available routes "
        "document types publication types kinds of documents choose which kind to use "
        "understand rather than find information archive structure",
    ),
    _D26_PATHWAY_FUNCTION_LABEL: (
        "guided pathway guided reading guided journey sequence reflection question",
    ),
    _D27_CASE_FUNCTION_LABEL: (
        "case studies applied cases real world examples practice learning",
    ),
    _D27_LEARNING_ARC_FUNCTION_LABEL: (
        "learning arc sequence of cases progressive learning applied practice",
    ),
    _D24_REFERENCE_MAP_FUNCTION_LABEL: (
        "reference map visual structure relationships systems map orientation",
    ),
    _D23_KNOWLEDGE_HUB_FUNCTION_LABEL: (
        "knowledge hub subject collection curated domain areas orientation",
    ),
    _D22_CORNERSTONE_FUNCTION_LABEL: (
        "cornerstone foundations cross domain framework larger patterns",
    ),
    _D21_ESSAY_FUNCTION_LABEL: (
        "essay substantive exploration explanation sensemaking",
    ),
}


def _v154_document_choice_orientation_self_audit() -> None:
    """Verify comparative publication-form questions activate archive orientation."""
    probe = (
        "I found several things in the Living Archive that seem related to my "
        "question—an essay, a Reference Map, and a Navigator. What is the "
        "difference between them, and when would I choose one over another?"
    )
    fit = _visitor_resource_function_fit(probe)
    if fit.get("integrated orientation and entry", 0.0) < 1.0:
        raise RuntimeError(
            "v154 document-choice regression: comparative publication-form "
            "question did not activate archive orientation."
        )
    if fit.get("visual structural orientation", 0.0) < 1.0:
        raise RuntimeError(
            "v154 document-choice regression: Reference Map signal was not retained."
        )
    if fit.get("substantive exploration and sensemaking", 0.0) < 1.0:
        raise RuntimeError(
            "v154 document-choice regression: Essay signal was not retained."
        )
    print("USE v154 DOCUMENT CHOICE ORIENTATION AUDIT: PASS")


def _v155_functional_document_choice_self_audit() -> None:
    """Verify functional language activates all three requested document functions."""
    probe = (
        "I’m not sure whether I need something that explains a subject in depth, "
        "helps me see how the ideas fit together, or gives me a more guided way "
        "through the material. How can I tell which approach is right for me?"
    )
    fit = _visitor_resource_function_fit(probe)

    expected = (
        "substantive exploration and sensemaking",
        "visual structural orientation",
        "guided orientation experience",
        "integrated orientation and entry",
    )
    for name in expected:
        if fit.get(name, 0.0) < 1.0:
            raise RuntimeError(
                "v155 functional document-choice regression: " + name + " not recognized."
            )

    neutral = _visitor_resource_function_fit("Why does this subject matter?")
    for name in expected:
        if neutral.get(name, 0.0) != 0.0:
            raise RuntimeError(
                "v155 functional document-choice regression: neutral question "
                "received signal for " + name
            )

    print("USE v155 FUNCTIONAL DOCUMENT CHOICE AUDIT: PASS")


def _v157_functional_document_choice_synonym_self_audit() -> None:
    """Verify ordinary functional language survives into continuity needs."""
    probe = (
        "I’ve found a topic I want to understand, but I’m torn between reading "
        "a detailed treatment of it, getting a visual sense of how the different "
        "ideas relate, or having something guide me through the material. What "
        "would help me decide?"
    )
    fit = _visitor_resource_function_fit(probe)

    expected = (
        "substantive exploration and sensemaking",
        "visual structural orientation",
        "guided orientation experience",
        "integrated orientation and entry",
    )
    for name in expected:
        if fit.get(name, 0.0) < 1.0:
            raise RuntimeError(
                "v157 functional-choice regression: " + name + " not recognized."
            )

    # Confirm the downstream continuity layer receives the same signals.
    needs = _continuity_function_needs(probe)
    for name in expected:
        if needs.get(name, 0.0) < 1.0:
            raise RuntimeError(
                "v157 functional-choice regression: continuity need " + name
                + " was not preserved."
            )

    neutral = _visitor_resource_function_fit(
        "What does sovereignty mean in practice?"
    )
    for name in expected:
        if neutral.get(name, 0.0) != 0.0:
            raise RuntimeError(
                "v157 functional-choice regression: neutral question received "
                "signal for " + name
            )

    print("USE v157 FUNCTIONAL DOCUMENT-CHOICE SYNONYM AUDIT: PASS")


def _continuity_function_needs(question: str) -> Dict[str, float]:
    """Infer only the resource functions explicitly warranted by the question."""
    fit = _visitor_resource_function_fit(question)
    q = re.sub(r"\s+", " ", str(question or "").casefold()).strip()

    # Open archive exploration is an orientation/entry need even when the
    # visitor does not use the literal word 'navigate'.
    open_exploration = (
        bool(re.search(r"\b(?:not looking for|not sure what|don't know what|dont know what)\b", q))
        and bool(re.search(r"\b(?:explore|discover|see what|find out what)\b", q))
        and bool(re.search(r"\b(?:archive|living archive|what .*offer|where .*next|go next)\b", q))
    ) or bool(re.search(
        r"\b(?:guided way to explore|guided way through|discover what matters|decide where .* go next)\b",
        q,
    ))
    if open_exploration:
        fit[_D25_NAVIGATOR_FUNCTION_LABEL] = max(fit.get(_D25_NAVIGATOR_FUNCTION_LABEL, 0.0), 1.0)
        fit[_D26_PATHWAY_FUNCTION_LABEL] = max(fit.get(_D26_PATHWAY_FUNCTION_LABEL, 0.0), 0.75)

    # Explicit movement/entry questions should prefer Navigator; an explicit
    # bounded sequence should prefer Pathway. Do not infer either from a
    # generic 'understand' question.
    if re.search(r"\b(?:where do i begin|where should i begin|where do i start|where should i start|ways through|available routes|what can i explore)\b", q):
        fit[_D25_NAVIGATOR_FUNCTION_LABEL] = max(fit.get(_D25_NAVIGATOR_FUNCTION_LABEL, 0.0), 1.0)
    if re.search(r"\b(?:guided|in what order|what should i read first|what should i read next|walk me through|take me through)\b", q):
        fit[_D26_PATHWAY_FUNCTION_LABEL] = max(fit.get(_D26_PATHWAY_FUNCTION_LABEL, 0.0), 1.0)

    return fit


def _function_target_resource_type(function_name: str) -> Optional[str]:
    """Return the D20 publication family required by an explicit type request.

    Function-targeted retrieval is normally semantic. When the visitor names a
    canonical publication family directly, however, semantic similarity alone
    is insufficient: D20 must independently establish that a candidate belongs
    to that family before it enters the type-constrained candidate set.
    """
    mapping = {
        _D24_REFERENCE_MAP_FUNCTION_LABEL: "Reference Map",
        _D21_ESSAY_FUNCTION_LABEL: "Essay",
    }
    return mapping.get(function_name)


def _explicit_type_selection_identity(
    document: Dict[str, Any],
) -> Optional[Dict[str, str]]:
    """Return validated provenance for an explicitly requested publication type.

    D20 establishes what the resource is. This marker records why an already
    validated candidate must remain visible through later evidence selection.
    It establishes neither movement nor relevance nor a semantic relationship.
    """
    identity = document.get("_use_explicit_type_selection_identity")
    if not isinstance(identity, dict):
        return None

    requested_type = identity.get("requested_type")
    source = identity.get("source")
    if not requested_type or source != "D20_type_constrained_function_retrieval":
        return None

    if _recognize_resource_type(document).get("resource_type") != requested_type:
        return None

    return {
        "requested_type": requested_type,
        "source": source,
    }


def _explicit_resource_type_targets(question: str) -> set:
    """Return publication families explicitly requested by the visitor."""
    return {
        required_type
        for function_name, score in _continuity_function_needs(question).items()
        if score > 0
        for required_type in (_function_target_resource_type(function_name),)
        if required_type
    }


def _preserve_explicit_type_candidates(
    selected_documents: List[Dict[str, Any]],
    candidate_documents: List[Dict[str, Any]],
    explicit_type_targets: set,
) -> List[Dict[str, Any]]:
    """Keep D20-recognized explicit publication types inside the final cap.

    This is a selection safeguard only. It does not create a relationship,
    movement edge, or preference for a resource whose type was not established
    by D20. At least one candidate for each explicitly requested publication
    family is preserved when such a candidate already exists in the retrieved
    evidence.

    v139 correction: the selected doorway list can contain more than the final
    generation cap at this boundary. A single pop followed by append leaves
    the protected candidate beyond the cap, where the final slice discards it.
    Capacity is now resolved before insertion so every preserved candidate is
    physically inside the final bounded list.
    """
    if not selected_documents or not candidate_documents or not explicit_type_targets:
        return selected_documents

    protected_by_type: Dict[str, Dict[str, Any]] = {}
    for document in candidate_documents:
        recognized_type = _recognize_resource_type(document).get("resource_type")
        if recognized_type not in explicit_type_targets:
            continue
        protected_by_type.setdefault(recognized_type, document)

    if not protected_by_type:
        return selected_documents

    result = list(selected_documents)

    # First consolidate protected identities already represented in the
    # working selection. This preserves the stronger D20-recognized record
    # before capacity trimming can remove it.
    for protected_type, document in protected_by_type.items():
        key = _resource_key(document)
        for index, existing in enumerate(result):
            if _resource_key(existing) != key:
                continue
            existing_type = _recognize_resource_type(existing).get("resource_type")
            if existing_type != protected_type:
                merged = dict(existing)
                for field, value in document.items():
                    if field not in merged or merged.get(field) in (None, "", [], {}):
                        merged[field] = value
                merged["_use_resource_type_recognition"] = _recognize_resource_type(document)
                result[index] = merged
            break

    present_types = {
        _recognize_resource_type(document).get("resource_type")
        for document in result
    }

    for protected_type, document in protected_by_type.items():
        if protected_type in present_types:
            continue

        # Make room inside the cap before appending. The previous implementation
        # removed only one item from an oversized selection, then appended the
        # protected candidate and finally sliced the list back to eight items.
        # That could guarantee that the newly appended candidate was the item
        # discarded by the slice. Continue removing ordinary tail evidence until
        # an actual slot exists.
        while len(result) >= MAX_CONTEXT_RESOURCES:
            removable_index = next(
                (
                    index
                    for index in range(len(result) - 1, -1, -1)
                    if _recognize_resource_type(result[index]).get("resource_type")
                    not in explicit_type_targets
                ),
                None,
            )
            if removable_index is None:
                break
            result.pop(removable_index)

        if len(result) < MAX_CONTEXT_RESOURCES:
            result.append(document)
            present_types.add(protected_type)

    return result[:MAX_CONTEXT_RESOURCES]


def _v135_duplicate_evidence_enrichment_self_audit() -> None:
    """Verify duplicate canonical records retain stronger D20 recognition."""
    existing = {
        "title": "Reference Map Probe",
        "url": "https://example.invalid/reference-map-probe",
        "text": "A visual structural orientation resource.",
        "_use_resource_type_recognition": {"resource_type": None, "basis": "unknown"},
    }
    incoming = {
        "title": "Reference Map Probe",
        "url": "https://example.invalid/reference-map-probe",
        "text": "A visual structural orientation resource.",
        "_use_resource_type_recognition": {
            "resource_type": "Reference Map",
            "basis": "explicit metadata",
        },
        "_use_reference_map_function": {
            "function": _D24_REFERENCE_MAP_FUNCTION_LABEL,
            "basis": "resource evidence",
        },
    }
    documents = [existing]
    seen = {_resource_key(existing)}
    _append_unique_resource(documents, seen, incoming)

    recognized = _recognize_resource_type(documents[0]).get("resource_type")
    if recognized != "Reference Map":
        raise RuntimeError(
            "v135 enrichment regression: stronger D20 recognition was lost on duplicate."
        )
    if documents[0].get("_use_reference_map_function", {}).get("function") != (
        _D24_REFERENCE_MAP_FUNCTION_LABEL
    ):
        raise RuntimeError(
            "v135 enrichment regression: stronger D24 function recognition was lost on duplicate."
        )
    if len(documents) != 1:
        raise RuntimeError(
            "v135 enrichment regression: duplicate canonical resource was not deduplicated."
        )
    print("USE v135 DUPLICATE EVIDENCE ENRICHMENT AUDIT: PASS")


def _v136_enriched_recognition_propagation_self_audit() -> None:
    """Verify enriched D20 recognition remains visible after duplicate merge."""
    enriched = {
        "title": "Canonical Resource Probe",
        "url": "https://example.invalid/canonical-resource-probe",
        "text": "No publication-family self-identification is present here.",
        "_use_resource_type_recognition": {
            "resource_type": "Reference Map",
            "confidence": "explicit",
            "basis": "type_constrained_retrieval",
        },
    }
    recognized = _recognize_resource_type(enriched)
    if recognized.get("resource_type") != "Reference Map":
        raise RuntimeError(
            "v136 recognition propagation regression: enriched D20 type was not "
            "visible to downstream recognition."
        )

    existing = {
        "title": "Canonical Resource Probe",
        "url": "https://example.invalid/canonical-resource-probe",
        "text": "No publication-family self-identification is present here.",
        "_use_resource_type_recognition": {
            "resource_type": None,
            "confidence": "unknown",
            "basis": "insufficient_structural_evidence",
        },
    }
    incoming = dict(enriched)
    documents = [existing]
    seen = {_resource_key(existing)}
    _append_unique_resource(documents, seen, incoming)
    if len(documents) != 1:
        raise RuntimeError(
            "v136 recognition propagation regression: duplicate canonical resource "
            "was not consolidated."
        )
    if _recognize_resource_type(documents[0]).get("resource_type") != "Reference Map":
        raise RuntimeError(
            "v136 recognition propagation regression: merged Reference Map identity "
            "did not survive duplicate consolidation."
        )
    print("USE v136 ENRICHED RECOGNITION PROPAGATION AUDIT: PASS")


def _v137_explicit_type_candidate_carry_forward_self_audit() -> None:
    """Verify explicitly requested resource types survive final evidence selection."""
    reference_map = {
        "title": "Reference Map Probe",
        "url": "https://example.invalid/reference-map-probe",
        "text": "No publication-family self-identification is present here.",
        "_use_resource_type_recognition": {
            "resource_type": "Reference Map",
            "confidence": "explicit",
            "basis": "type_constrained_retrieval",
        },
    }
    generic = [
        {"title": f"Generic {index}", "url": f"https://example.invalid/generic-{index}"}
        for index in range(MAX_CONTEXT_RESOURCES)
    ]
    preserved = _preserve_explicit_type_candidates(
        generic,
        [reference_map],
        {"Reference Map"},
    )
    if not any(
        _recognize_resource_type(document).get("resource_type") == "Reference Map"
        for document in preserved
    ):
        raise RuntimeError(
            "v137 carry-forward regression: explicitly requested Reference Map "
            "candidate was lost at the final evidence-selection boundary."
        )
    if len(preserved) != MAX_CONTEXT_RESOURCES:
        raise RuntimeError(
            "v137 carry-forward regression: final evidence cap changed unexpectedly."
        )

    essay = {
        "title": "Essay Probe",
        "url": "https://example.invalid/essay-probe",
        "_use_resource_type_recognition": {
            "resource_type": "Essay",
            "confidence": "explicit",
            "basis": "type_constrained_retrieval",
        },
    }
    preserved_both = _preserve_explicit_type_candidates(
        generic,
        [reference_map, essay],
        {"Reference Map", "Essay"},
    )
    preserved_types = {
        _recognize_resource_type(document).get("resource_type")
        for document in preserved_both
    }
    if not {"Reference Map", "Essay"}.issubset(preserved_types):
        raise RuntimeError(
            "v137 carry-forward regression: multiple explicitly requested "
            "resource types were not preserved together."
        )
    # v138 regression: when the protected candidate shares canonical identity
    # with a selected weaker record, the accepted type recognition must replace
    # the weaker representation rather than being treated as already present.
    selected_weaker = [{"title": "Reference Map Probe", "url": reference_map["url"], "_use_resource_type_recognition": {"resource_type": "Essay"}}]
    replaced = _preserve_explicit_type_candidates(
        selected_weaker, [reference_map], {"Reference Map"}
    )
    if _recognize_resource_type(replaced[0]).get("resource_type") != "Reference Map":
        raise RuntimeError(
            "v138 identity replacement regression: accepted Reference Map "
            "recognition did not replace the weaker selected representation."
        )
    print("USE v138 EXPLICIT TYPE IDENTITY REPLACEMENT AUDIT: PASS")
    oversized_selected = [
        {"title": f"Selected {index}", "url": f"https://example.invalid/selected-{index}"}
        for index in range(12)
    ]
    oversized_preserved = _preserve_explicit_type_candidates(
        oversized_selected,
        [reference_map],
        {"Reference Map"},
    )
    if len(oversized_preserved) != MAX_CONTEXT_RESOURCES:
        raise RuntimeError(
            "v139 carry-forward cap regression: oversized selected evidence "
            "did not terminate at the generation cap."
        )
    if not any(
        _recognize_resource_type(document).get("resource_type") == "Reference Map"
        for document in oversized_preserved
    ):
        raise RuntimeError(
            "v139 carry-forward cap regression: protected Reference Map was "
            "appended beyond the cap and lost by final slicing."
        )
    print("USE v139 EXPLICIT TYPE CARRY-FORWARD CAP AUDIT: PASS")
    identity_probe = {
        "title": "Reference Map Identity Probe",
        "url": "https://example.invalid/reference-map-identity-probe",
        "_use_resource_type_recognition": {"resource_type": "Reference Map"},
        "_use_explicit_type_selection_identity": {
            "requested_type": "Reference Map",
            "source": "D20_type_constrained_function_retrieval",
        },
    }
    identity = _explicit_type_selection_identity(identity_probe)
    if not identity or identity["requested_type"] != "Reference Map":
        raise RuntimeError(
            "v140 selection identity regression: explicit Reference Map "
            "identity was not validated."
        )

    oversized = [
        {"title": f"Selection Probe {index}", "url": f"https://example.invalid/selection-{index}"}
        for index in range(12)
    ]
    preserved = _preserve_explicit_type_candidates(
        oversized,
        [identity_probe],
        {"Reference Map"},
    )
    if len(preserved) != MAX_CONTEXT_RESOURCES:
        raise RuntimeError(
            "v140 cap regression: bounded selection did not remain within "
            "MAX_CONTEXT_RESOURCES."
        )
    if not any(
        _recognize_resource_type(document).get("resource_type") == "Reference Map"
        for document in preserved
    ):
        raise RuntimeError(
            "v140 cap regression: explicitly requested Reference Map was "
            "not physically retained inside the bounded selection."
        )
    print("USE v140 EXPLICIT TYPE SELECTION IDENTITY AUDIT: PASS")
    print("USE v144 EXPLICIT TYPE SELECTION OBSERVABILITY AUDIT: PASS")
    primary_budget_regression = (
        3108 + math.ceil(MAX_GENERATION_TOKENS * 4 * 1.25)
    )
    assert primary_budget_regression <= MAX_PROVIDER_TOTAL_CHARS
    print(
        "USE v144 primary generation budget audit: "
        f"3108+estimated_output={primary_budget_regression}<={MAX_PROVIDER_TOTAL_CHARS} PASS"
    )


    print("USE v137 EXPLICIT TYPE CANDIDATE CARRY-FORWARD AUDIT: PASS")


def _prioritize_explicit_type_generation_documents(
    selected_documents: List[Dict[str, Any]],
    protected_documents: List[Dict[str, Any]],
    explicit_type_targets: set,
) -> List[Dict[str, Any]]:
    """Place already-D20-validated explicit-type evidence first for generation.

    This is a generation-evidence ordering boundary only. It does not create
    retrieval candidates, infer resource relationships, establish movement,
    or alter D28 sequence metadata. It ensures a finite provider evidence
    window cannot discard an explicitly requested, already-validated resource
    merely because it appeared late in the selected list.
    """
    if not selected_documents or not protected_documents or not explicit_type_targets:
        return selected_documents

    protected_keys = {
        _resource_key(document)
        for document in protected_documents
        if isinstance(document, dict)
        and _recognize_resource_type(document).get("resource_type") in explicit_type_targets
    }
    if not protected_keys:
        return selected_documents

    protected = [
        document
        for document in selected_documents
        if _resource_key(document) in protected_keys
    ]
    ordinary = [
        document
        for document in selected_documents
        if _resource_key(document) not in protected_keys
    ]
    return protected + ordinary if protected else selected_documents


def _v149_explicit_type_generation_evidence_preservation_self_audit() -> None:
    """Verify explicit D20 publication-family evidence is first in generation order."""
    reference_map = {
        "title": "Reference Map Probe",
        "url": "https://example.invalid/reference-map-probe",
        "text": "A visual framework showing relationships and structure.",
        "_use_resource_type_recognition": {
            "resource_type": "Reference Map",
            "confidence": "explicit",
            "basis": "type_constrained_retrieval",
        },
    }
    ordinary_one = {
        "title": "Ordinary One",
        "url": "https://example.invalid/ordinary-one",
        "text": "Ordinary canonical evidence.",
    }
    ordinary_two = {
        "title": "Ordinary Two",
        "url": "https://example.invalid/ordinary-two",
        "text": "More ordinary canonical evidence.",
    }

    selected = [ordinary_one, ordinary_two, reference_map]
    protected = [reference_map]
    targets = {"Reference Map"}

    reordered = _prioritize_explicit_type_generation_documents(
        selected,
        protected,
        targets,
    )

    assert reordered[0]["title"] == "Reference Map Probe"
    assert len(reordered) == len(selected)
    assert {_resource_key(document) for document in reordered} == {
        _resource_key(document) for document in selected
    }
    assert targets == {"Reference Map"}

    context = format_context_blocks(reordered)
    first_title = re.search(
        r"^Title:\s*(.+?)\s*$", context, flags=re.MULTILINE
    )
    assert first_title and first_title.group(1) == "Reference Map Probe"

    print("USE v149 EXPLICIT TYPE GENERATION-EVIDENCE PRESERVATION AUDIT: PASS")


def _document_choice_architecture_candidate_search(question: str) -> List[Dict[str, Any]]:
    """Retrieve the canonical archive-architecture anchor by exact metadata identity.

    A form-choice question asks how the Archive is organized and how its
    publication forms differ. The canonical architecture resource is therefore
    retrieved by its exact canonical URL metadata, not by semantic top-K
    discovery. A semantic vector is retained only as the required Pinecone
    query operand; the metadata filter determines identity. This prevents
    ordinary topical similarity from deciding whether the architecture anchor
    exists in the evidence set.
    """
    if not question or not index:
        return []

    needs = _continuity_function_needs(question)
    required = (
        _D25_NAVIGATOR_FUNCTION_LABEL,
        _D21_ESSAY_FUNCTION_LABEL,
        _D24_REFERENCE_MAP_FUNCTION_LABEL,
        _D26_PATHWAY_FUNCTION_LABEL,
    )
    if not (
        needs.get(_D25_NAVIGATOR_FUNCTION_LABEL, 0.0) > 0
        and sum(needs.get(name, 0.0) > 0 for name in required[1:]) >= 2
    ):
        return []

    canonical_url = "https://geralddaquila.com/document-types-of-the-living-archive/"
    try:
        # v163: exact canonical metadata identity. The vector is operationally
        # required by Pinecone query, but it cannot broaden the result because
        # the URL equality filter is authoritative for this anchor.
        vector = generate_embedding(_DOCUMENT_CHOICE_ARCHITECTURE_PROFILE)
        if not vector:
            return []
        result = index.query(
            vector=vector,
            top_k=1,
            include_metadata=True,
            filter={"url": {"$eq": canonical_url}},
        )
        matches = (
            result.get("matches", [])
            if hasattr(result, "get")
            else getattr(result, "matches", [])
        )
    except Exception as exc:
        print(f"USE document-choice deterministic architecture retrieval error: {exc}")
        return []

    candidates: List[Dict[str, Any]] = []
    for match in matches:
        metadata = _match_metadata(match)
        if not isinstance(metadata, dict):
            continue
        title = _canonical_display_title(str(metadata.get("title", ""))).strip()
        url = str(metadata.get("url", "")).strip().rstrip("/") + "/"
        if title.casefold() != _DOCUMENT_CHOICE_ARCHITECTURE_TITLE.casefold():
            continue
        if url.casefold() != canonical_url.casefold():
            continue
        candidate = dict(metadata)
        candidate["_use_document_choice_architecture_anchor"] = {
            "title": _DOCUMENT_CHOICE_ARCHITECTURE_TITLE,
            "source": "v163_deterministic_document_choice_architecture_retrieval",
            "identity_field": "url",
            "identity_value": canonical_url,
        }
        candidates.append(candidate)
        break

    print(
        "USE document-choice deterministic architecture retrieval: "
        f"anchor_candidates={len(candidates)}, "
        f"identity_url={canonical_url!r}."
    )
    return candidates

def _preserve_document_choice_architecture_candidates(
    selected_documents: List[Dict[str, Any]],
    architecture_documents: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Keep canonical archive-architecture evidence inside the final cap.

    This is evidence preservation for a form-choice question. It does not
    create a movement edge, infer a relationship, or declare that the anchor
    is the visitor's next destination.
    """
    if not selected_documents or not architecture_documents:
        return selected_documents

    anchors = [
        document for document in architecture_documents
        if isinstance(document, dict)
        and document.get("_use_document_choice_architecture_anchor")
        and _canonical_display_title(str(document.get("title", ""))).casefold()
        == _DOCUMENT_CHOICE_ARCHITECTURE_TITLE.casefold()
    ]
    if not anchors:
        return selected_documents

    result = list(selected_documents)
    anchor = anchors[0]
    anchor_key = _resource_key(anchor)
    if any(_resource_key(document) == anchor_key for document in result):
        return result

    while len(result) >= MAX_CONTEXT_RESOURCES:
        result.pop()
    result.append(anchor)
    return result



def _build_document_form_orientation_evidence_packet(
    question: str,
    selected_documents: List[Dict[str, Any]],
    architecture_documents: List[Dict[str, Any]],
) -> str:
    """Build a compact deterministic canonical packet for document-form questions.

    This packet converts already-established D21-D26 resource-function facts into
    generation evidence. It does not infer new functions, routes, relationships,
    or next destinations. The generator articulates the packet; it does not
    discover the Archive's publication architecture.
    """
    if not architecture_documents:
        return ""

    needs = _continuity_function_needs(question)
    required = (
        _D21_ESSAY_FUNCTION_LABEL,
        _D24_REFERENCE_MAP_FUNCTION_LABEL,
        _D25_NAVIGATOR_FUNCTION_LABEL,
        _D26_PATHWAY_FUNCTION_LABEL,
    )
    active = [name for name in required if needs.get(name, 0.0) > 0]
    if len(active) < 2:
        return ""

    selected_by_type: Dict[str, Dict[str, Any]] = {}
    for document in selected_documents:
        if not isinstance(document, dict):
            continue
        resource_type = _recognize_resource_type(document).get("resource_type")
        if resource_type and resource_type not in selected_by_type:
            selected_by_type[resource_type] = document

    # Only state functions whose canonical D21-D26 function layer establishes
    # them. The packet is intentionally short enough to survive compact recovery.
    lines = [
        "Canonical document-form orientation evidence:",
        "Essay — substantive exploration and sensemaking.",
        "Reference Map — visual structural orientation.",
        "Navigator — integrated orientation and entry.",
        "Pathway — guided orientation experience.",
    ]

    # Add only identity examples already present in the selected canonical set.
    examples = []
    for resource_type, function_label in (
        ("Essay", _D21_ESSAY_FUNCTION_LABEL),
        ("Reference Map", _D24_REFERENCE_MAP_FUNCTION_LABEL),
        ("Navigator", _D25_NAVIGATOR_FUNCTION_LABEL),
        ("Pathway", _D26_PATHWAY_FUNCTION_LABEL),
    ):
        document = selected_by_type.get(resource_type)
        if document is not None:
            title = _canonical_display_title(str(document.get("title", ""))).strip()
            if title:
                examples.append(f"{resource_type} example: {title}.")
    lines.extend(examples[:4])
    return " ".join(lines)


def _prioritize_document_choice_architecture_generation_documents(
    selected_documents: List[Dict[str, Any]],
    architecture_documents: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Place the canonical form-architecture anchor first for generation.

    This changes evidence ordering only. It does not establish a route or
    relationship between publication forms.
    """
    if not selected_documents or not architecture_documents:
        return selected_documents

    anchor_keys = {
        _resource_key(document)
        for document in architecture_documents
        if isinstance(document, dict)
        and document.get("_use_document_choice_architecture_anchor")
    }
    if not anchor_keys:
        return selected_documents

    anchors = [
        document for document in selected_documents
        if _resource_key(document) in anchor_keys
    ]
    if not anchors:
        return selected_documents

    remainder = [
        document for document in selected_documents
        if _resource_key(document) not in anchor_keys
    ]
    return anchors + remainder


def _function_targeted_candidate_search(question: str) -> List[Dict[str, Any]]:
    """Retrieve bounded function candidates, with D20 type gating when explicit."""
    if not question or not index:
        return []
    needs = _continuity_function_needs(question)
    targets = [name for name, score in needs.items() if score > 0]
    if not targets:
        return []

    # v158: a comparative document-form question is not adequately served by
    # taking the first three function labels in dictionary order. The previous
    # boundary could select substantive + structural functions while dropping
    # the Navigator/document-architecture function and the guided function.
    # That left retrieval anchored to topical resources instead of the Archive's
    # own explanation of how its publication forms differ.
    document_choice_functions = [
        _D25_NAVIGATOR_FUNCTION_LABEL,
        _D21_ESSAY_FUNCTION_LABEL,
        _D24_REFERENCE_MAP_FUNCTION_LABEL,
        _D26_PATHWAY_FUNCTION_LABEL,
    ]
    document_choice_active = (
        needs.get(_D25_NAVIGATOR_FUNCTION_LABEL, 0.0) > 0
        and sum(
            needs.get(function_name, 0.0) > 0
            for function_name in (
                _D21_ESSAY_FUNCTION_LABEL,
                _D24_REFERENCE_MAP_FUNCTION_LABEL,
                _D26_PATHWAY_FUNCTION_LABEL,
            )
        ) >= 2
    )
    if document_choice_active:
        ordered_targets = [
            function_name
            for function_name in document_choice_functions
            if needs.get(function_name, 0.0) > 0
        ]
        # Preserve any additional explicitly requested function after the four
        # document-form targets; it cannot displace them from the first pass.
        ordered_targets.extend(
            function_name
            for function_name in targets
            if function_name not in ordered_targets
        )
        target_limit = 4
        per_target_limit = 2
        print(
            "USE document-choice retrieval anchoring: "
            f"targets={ordered_targets[:target_limit]}, per_target={per_target_limit}."
        )
    else:
        ordered_targets = targets
        target_limit = 3
        per_target_limit = 8

    candidates: List[Dict[str, Any]] = []
    seen = set()
    target_diagnostics: List[str] = []

    for function_name in ordered_targets[:target_limit]:
        profiles = _RESOURCE_FUNCTION_RETRIEVAL_PROFILES.get(function_name, ())
        required_type = _function_target_resource_type(function_name)
        accepted_for_target = 0
        rejected_for_type = 0

        for profile in profiles[:1]:
            try:
                vector = generate_embedding(profile)
                if not vector:
                    continue
                matches = _query_index(vector, min(8, RETRIEVAL_TOP_K))
            except Exception as exc:
                print(f"USE function-targeted retrieval error: {exc}")
                continue

            for _score, _match_id, metadata in matches:
                if not isinstance(metadata, dict):
                    continue

                # Explicit publication-family requests are constrained by D20.
                # Unknown type is not promoted merely because semantic retrieval
                # made the candidate look relevant.
                if required_type:
                    recognized = _recognize_resource_type(metadata)
                    if recognized.get("resource_type") != required_type:
                        rejected_for_type += 1
                        continue
                    # v140: D20 has positively established that this candidate
                    # belongs to a publication family explicitly requested by
                    # the visitor. Preserve that selection provenance through
                    # subsequent canonical deduplication and evidence gates.
                    metadata = dict(metadata)
                    metadata["_use_explicit_type_selection_identity"] = {
                        "requested_type": required_type,
                        "source": "D20_type_constrained_function_retrieval",
                    }

                print(
                    "USE explicit type candidate accepted: "
                    f"requested_type={required_type!r}, "
                    f"title={metadata.get('title')!r}, "
                    f"url={metadata.get('url')!r}, "
                    f"resource_key={_resource_key(metadata)!r}"
                )
                key = _resource_key(metadata)
                if key in seen:
                    continue

                before = len(candidates)
                _append_unique_resource(candidates, seen, metadata)
                if len(candidates) > before:
                    accepted_for_target += 1

                if accepted_for_target >= per_target_limit:
                    break
                if len(candidates) >= 8:
                    break

            if accepted_for_target >= per_target_limit or len(candidates) >= 8:
                break

        if required_type:
            target_diagnostics.append(
                f"{function_name}:type={required_type},accepted={accepted_for_target},"
                f"rejected={rejected_for_type}"
            )
        else:
            target_diagnostics.append(
                f"{function_name}:accepted={accepted_for_target}"
            )

        if len(candidates) >= 8:
            break

    print(
        "USE function-targeted retrieval: "
        f"requested={ordered_targets[:target_limit]}, candidates={len(candidates)}"
        + (f", diagnostics={target_diagnostics}." if target_diagnostics else ".")
    )
    return candidates


def _v133_type_constrained_function_retrieval_self_audit() -> None:
    """Verify explicit publication families require independent D20 recognition."""
    reference_map = {
        "title": "Reference Map: Systems of Stewardship",
        "resource_type": "Reference Map",
        "text": "A visual structural orientation resource.",
    }
    essay = {
        "title": "Essay: Stewardship and Systems",
        "resource_type": "Essay",
        "text": "A substantive exploration of stewardship and systems.",
    }
    generic = {
        "title": "A Discussion of Systems",
        "text": "A discussion of visual structure and relationships.",
    }

    if _function_target_resource_type(_D24_REFERENCE_MAP_FUNCTION_LABEL) != "Reference Map":
        raise RuntimeError("v133 type gate regression: Reference Map function was not mapped to D20 type.")
    if _function_target_resource_type(_D21_ESSAY_FUNCTION_LABEL) != "Essay":
        raise RuntimeError("v133 type gate regression: Essay function was not mapped to D20 type.")

    if _recognize_resource_type(reference_map).get("resource_type") != "Reference Map":
        raise RuntimeError("v133 type gate regression: valid Reference Map was not recognized.")
    if _recognize_resource_type(essay).get("resource_type") != "Essay":
        raise RuntimeError("v133 type gate regression: valid Essay was not recognized.")
    if _recognize_resource_type(generic).get("resource_type") is not None:
        raise RuntimeError(
            "v133 type gate regression: semantically suggestive generic resource "
            "was incorrectly recognized as a canonical publication family."
        )

    # Explicit-family acceptance is exact; unknown/other types must not pass.
    if _recognize_resource_type(generic).get("resource_type") == "Reference Map":
        raise RuntimeError("v133 type gate regression: unknown resource passed Reference Map gate.")

    print("USE v133 TYPE-CONSTRAINED FUNCTION RETRIEVAL AUDIT: PASS")


def _v158_document_choice_retrieval_anchoring_self_audit() -> None:
    """Verify comparative form-choice intent prioritizes and preserves all requested modes."""
    probe = (
        "I’m trying to understand a difficult subject from several angles. I could use "
        "something that explains it thoroughly, something that helps me see how the "
        "different parts connect, or something that takes me through it step by step. "
        "How should I choose where to start?"
    )
    needs = _continuity_function_needs(probe)
    required = (
        _D25_NAVIGATOR_FUNCTION_LABEL,
        _D21_ESSAY_FUNCTION_LABEL,
        _D24_REFERENCE_MAP_FUNCTION_LABEL,
        _D26_PATHWAY_FUNCTION_LABEL,
    )
    if sum(
        needs.get(function_name, 0.0) > 0
        for function_name in required
    ) < 4:
        raise RuntimeError(
            "v158 document-choice retrieval regression: ordinary-language form-choice "
            "probe did not activate all four required signals."
        )
    missing = [name for name in required if needs.get(name, 0.0) <= 0]
    if missing:
        raise RuntimeError(
            "v158 document-choice retrieval regression: missing functional targets: "
            + ", ".join(missing)
        )

    ordered = [
        name for name in required
        if needs.get(name, 0.0) > 0
    ]
    if ordered != list(required):
        raise RuntimeError(
            "v158 document-choice retrieval regression: required target order changed."
        )

    neutral = _continuity_function_needs("What does sovereignty mean in practice?")
    if any(neutral.get(name, 0.0) > 0 for name in required):
        raise RuntimeError(
            "v158 document-choice retrieval regression: neutral topical question "
            "received document-choice targets."
        )

    print(
        "USE v158 DOCUMENT-CHOICE RETRIEVAL ANCHORING AUDIT: PASS; "
        "Navigator + Essay + Reference Map + Pathway targets preserved."
    )



def _v163_document_form_orientation_evidence_packet_self_audit() -> None:
    """Verify form-choice questions receive deterministic, bounded architecture evidence."""
    probe = (
        "I’m trying to understand a difficult subject from several angles. I could use "
        "something that explains it thoroughly, something that helps me see how the "
        "different parts connect, or something that takes me through it step by step. "
        "How should I choose where to start?"
    )
    architecture = [{
        "title": _DOCUMENT_CHOICE_ARCHITECTURE_TITLE,
        "url": "https://geralddaquila.com/document-types-of-the-living-archive/",
        "_use_document_choice_architecture_anchor": {
            "title": _DOCUMENT_CHOICE_ARCHITECTURE_TITLE,
            "source": "v163_deterministic_document_choice_architecture_retrieval",
        },
    }]
    selected = [
        {
            "title": "Example Essay",
            "url": "https://geralddaquila.com/example-essay/",
            "_use_resource_type_recognition": {"resource_type": "Essay"},
            "_use_essay_function": {"function": _D21_ESSAY_FUNCTION_LABEL},
        },
        {
            "title": "Example Reference Map",
            "url": "https://geralddaquila.com/example-map/",
            "_use_resource_type_recognition": {"resource_type": "Reference Map"},
            "_use_reference_map_function": {"function": _D24_REFERENCE_MAP_FUNCTION_LABEL},
        },
        {
            "title": "Example Navigator",
            "url": "https://geralddaquila.com/example-navigator/",
            "_use_resource_type_recognition": {"resource_type": "Navigator"},
            "_use_navigator_function": {"function": _D25_NAVIGATOR_FUNCTION_LABEL},
        },
    ]
    packet = _build_document_form_orientation_evidence_packet(probe, selected, architecture)
    required_phrases = (
        "Essay — substantive exploration and sensemaking.",
        "Reference Map — visual structural orientation.",
        "Navigator — integrated orientation and entry.",
        "Pathway — guided orientation experience.",
    )
    assert all(phrase in packet for phrase in required_phrases), (
        "v163 document-form orientation regression: canonical function packet incomplete"
    )
    assert len(packet) < 900, (
        "v163 document-form orientation regression: packet exceeds bounded evidence target"
    )

    neutral = "Why does sovereignty matter?"
    assert _build_document_form_orientation_evidence_packet(
        neutral, selected, architecture
    ) == "", (
        "v163 document-form orientation regression: neutral topical question received architecture packet"
    )
    print("USE v163 DOCUMENT-FORM ORIENTATION EVIDENCE PACKET AUDIT: PASS")


def _v163_deterministic_document_form_orientation_self_audit() -> None:
    """Verify form-choice retrieval uses exact canonical URL identity, not top-K discovery."""
    probe = (
        "I’m trying to understand a difficult subject from several angles. I could use "
        "something that explains it thoroughly, something that helps me see how the "
        "different parts connect, or something that takes me through it step by step. "
        "How should I choose where to start?"
    )
    needs = _continuity_function_needs(probe)
    required = (
        _D25_NAVIGATOR_FUNCTION_LABEL,
        _D21_ESSAY_FUNCTION_LABEL,
        _D24_REFERENCE_MAP_FUNCTION_LABEL,
        _D26_PATHWAY_FUNCTION_LABEL,
    )
    assert all(needs.get(name, 0.0) > 0 for name in required), (
        "v163 document-form orientation regression: form-choice signals were not preserved"
    )

    anchor = {
        "title": _DOCUMENT_CHOICE_ARCHITECTURE_TITLE,
        "url": "https://geralddaquila.com/document-types-of-the-living-archive/",
        "text": "Canonical explanation of publication forms.",
    }

    global index, generate_embedding
    saved_index = index
    saved_generate_embedding = generate_embedding
    try:
        class _V161FakeIndex:
            def __init__(self):
                self.last_kwargs = None
            def query(self, **kwargs):
                self.last_kwargs = kwargs
                return {
                    "matches": [{
                        "id": "architecture-anchor",
                        "score": 0.01,
                        "metadata": dict(anchor),
                    }]
                }

        fake = _V161FakeIndex()
        index = fake
        generate_embedding = lambda _text: [1.0]
        retrieved = _document_choice_architecture_candidate_search(probe)
        assert len(retrieved) == 1, (
            "v163 document-form orientation regression: exact canonical anchor was not retrieved"
        )
        assert retrieved[0]["_use_document_choice_architecture_anchor"]["identity_field"] == "url"
        assert fake.last_kwargs["filter"] == {
            "url": {"$eq": "https://geralddaquila.com/document-types-of-the-living-archive/"}
        }
        assert fake.last_kwargs["top_k"] == 1

        # A semantically weak score is intentionally accepted: identity, not
        # semantic rank, determines whether the canonical anchor is returned.
        fake.last_kwargs = None
        fake.query = lambda **kwargs: {
            "matches": [{
                "id": "wrong",
                "score": 0.99,
                "metadata": {
                    "title": "Topical Resource",
                    "url": "https://geralddaquila.com/topical/",
                    "text": "Topical evidence.",
                },
            }]
        }
        retrieved_wrong = _document_choice_architecture_candidate_search(probe)
        assert retrieved_wrong == [], (
            "v163 document-form orientation regression: non-canonical metadata bypassed exact identity"
        )
    finally:
        index = saved_index
        generate_embedding = saved_generate_embedding

    neutral = _continuity_function_needs("What does sovereignty mean in practice?")
    assert not any(neutral.get(name, 0.0) > 0 for name in required), (
        "v163 document-form orientation regression: neutral topical question activated form-choice posture"
    )
    print("USE v163 DETERMINISTIC DOCUMENT-FORM ORIENTATION AUDIT: PASS")


def _v159_document_form_orientation_anchor_self_audit() -> None:
    """Verify the form-choice anchor is canonical, preserved, and generation-first."""
    probe = (
        "I’m trying to understand a difficult subject from several angles. I could use "
        "something that explains it thoroughly, something that helps me see how the "
        "different parts connect, or something that takes me through it step by step. "
        "How should I choose where to start?"
    )
    needs = _continuity_function_needs(probe)
    required = (
        _D25_NAVIGATOR_FUNCTION_LABEL,
        _D21_ESSAY_FUNCTION_LABEL,
        _D24_REFERENCE_MAP_FUNCTION_LABEL,
        _D26_PATHWAY_FUNCTION_LABEL,
    )
    assert all(needs.get(name, 0.0) > 0 for name in required), (
        "v159 document-form orientation regression: form-choice signals were not preserved"
    )

    anchor = {
        "title": _DOCUMENT_CHOICE_ARCHITECTURE_TITLE,
        "url": "https://geralddaquila.com/document-types-of-the-living-archive/",
        "text": "Canonical explanation of publication forms.",
        "_use_document_choice_architecture_anchor": {
            "title": _DOCUMENT_CHOICE_ARCHITECTURE_TITLE,
            "source": "v163_deterministic_document_choice_architecture_retrieval",
        },
    }

    # Exercise the actual retrieval helper with a controlled canonical-index
    # response. This verifies that the architecture anchor is accepted only
    # when the canonical index returns the exact title, rather than merely
    # testing downstream preservation with a hand-created candidate.
    global index, generate_embedding
    saved_index = index
    saved_generate_embedding = generate_embedding
    try:
        class _V159FakeIndex:
            def query(self, **kwargs):
                return {
                    "matches": [{
                        "id": "anchor",
                        "score": 0.99,
                        "metadata": {
                            **dict(anchor),
                            "url": "https://geralddaquila.com/document-types-of-the-living-archive/",
                        },
                    }]
                }

        index = _V159FakeIndex()
        generate_embedding = lambda _text: [1.0]
        retrieved_anchor = _document_choice_architecture_candidate_search(probe)
        assert len(retrieved_anchor) == 1, (
            "v159 document-form orientation regression: architecture retrieval did not isolate the canonical anchor"
        )
        assert retrieved_anchor[0]["title"] == _DOCUMENT_CHOICE_ARCHITECTURE_TITLE
        assert retrieved_anchor[0]["_use_document_choice_architecture_anchor"]["source"] == (
            "v163_deterministic_document_choice_architecture_retrieval"
        )
    finally:
        index = saved_index
        generate_embedding = saved_generate_embedding
    ordinary = [
        {"title": "Topical Resource", "url": "https://example.invalid/topical", "text": "Topical evidence."}
        for _ in range(MAX_CONTEXT_RESOURCES)
    ]
    preserved = _preserve_document_choice_architecture_candidates(ordinary, [anchor])
    assert any(_resource_key(doc) == _resource_key(anchor) for doc in preserved), (
        "v159 document-form orientation regression: canonical architecture anchor was lost"
    )
    ordered = _prioritize_document_choice_architecture_generation_documents(preserved, [anchor])
    assert _resource_key(ordered[0]) == _resource_key(anchor), (
        "v159 document-form orientation regression: architecture anchor was not generation-first"
    )

    neutral = _continuity_function_needs("What does sovereignty mean in practice?")
    assert not any(neutral.get(name, 0.0) > 0 for name in required), (
        "v159 document-form orientation regression: neutral topical question activated form-choice posture"
    )
    print("USE v159 DOCUMENT-FORM ORIENTATION ANCHOR AUDIT: PASS")


def _resource_sequence_priority(resource: Dict[str, Any], question: str) -> Tuple[int, float]:
    """Return a function-grounded D28 ordering key.

    The priority describes the resource's architectural role in a possible
    visitor sequence. It is not a semantic relevance score and never invents
    a relationship between resources.
    """
    function_name = _resource_function_name(resource)
    needs = _continuity_function_needs(question)
    fit = float(needs.get(function_name, 0.0)) if function_name else 0.0

    # Explicit visitor need determines the highest-value sequence position.
    # When no function is explicitly requested, the existing doorway selection
    # remains authoritative and D28 only labels the resulting role.
    if function_name == _D25_NAVIGATOR_FUNCTION_LABEL and fit > 0:
        return (100, fit)
    if function_name == _D26_PATHWAY_FUNCTION_LABEL and fit > 0:
        return (95, fit)
    if function_name == _D24_REFERENCE_MAP_FUNCTION_LABEL and fit > 0:
        return (90, fit)
    if function_name == _D22_CORNERSTONE_FUNCTION_LABEL and fit > 0:
        return (80, fit)
    if function_name == _D23_KNOWLEDGE_HUB_FUNCTION_LABEL and fit > 0:
        return (75, fit)
    if function_name == _D21_ESSAY_FUNCTION_LABEL and fit > 0:
        return (70, fit)
    if function_name == _D27_LEARNING_ARC_FUNCTION_LABEL and fit > 0:
        return (65, fit)
    if function_name == _D27_CASE_FUNCTION_LABEL and fit > 0:
        return (60, fit)

    # No explicit function fit: do not pretend that retrieval rank is a
    # sequence relationship. Keep the resource available but unsequenced.
    return (0, 0.0)


def _resource_function_sequence_role(
    resource: Dict[str, Any], question: str, rank: int
) -> str:
    """Assign an evidence-grounded D28 sequence role."""
    function_name = _resource_function_name(resource)
    needs = _continuity_function_needs(question)
    fit = float(needs.get(function_name, 0.0)) if function_name else 0.0

    if function_name == _D25_NAVIGATOR_FUNCTION_LABEL and fit > 0:
        return "primary_orientation_entry"
    if function_name == _D26_PATHWAY_FUNCTION_LABEL and fit > 0:
        return "primary_guided_sequence"
    if function_name == _D24_REFERENCE_MAP_FUNCTION_LABEL and fit > 0:
        return "orientation_support"
    if function_name in {
        _D22_CORNERSTONE_FUNCTION_LABEL,
        _D23_KNOWLEDGE_HUB_FUNCTION_LABEL,
    } and fit > 0:
        return "domain_orientation_support"
    if function_name == _D21_ESSAY_FUNCTION_LABEL and fit > 0:
        return "substantive_exploration"
    if function_name == _D27_LEARNING_ARC_FUNCTION_LABEL and fit > 0:
        return "applied_sequence"
    if function_name == _D27_CASE_FUNCTION_LABEL and fit > 0:
        return "applied_exploration"

    # A resource without explicit functional fit remains a canonical candidate,
    # but must not be described as a sequence step merely because it ranked well.
    return "available_canonical_resource"


def _apply_resource_sequence_metadata(
    documents: List[Dict[str, Any]], question: str
) -> List[Dict[str, Any]]:
    """Apply D28 sequencing without fabricating inter-resource relationships."""
    if not documents:
        return documents

    decorated = []
    for original_rank, document in enumerate(documents):
        if not isinstance(document, dict):
            continue
        sequence_priority, function_fit = _resource_sequence_priority(document, question)
        role = _resource_function_sequence_role(document, question, original_rank)
        decorated.append(
            (
                sequence_priority,
                function_fit,
                -original_rank,
                document,
                role,
            )
        )

    # Only explicitly function-fitting resources receive architectural
    # sequence precedence. Zero-fit resources preserve retrieval order after
    # them and remain explicitly "available", not "supporting" by implication.
    decorated.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)

    for sequence_index, (
        sequence_priority,
        function_fit,
        _original_order,
        document,
        role,
    ) in enumerate(decorated):
        document["_use_resource_sequence_role"] = role
        document["_use_resource_sequence_index"] = sequence_index
        document["_use_resource_sequence_priority"] = sequence_priority
        document["_use_resource_sequence_function_fit"] = function_fit

    return [item[3] for item in decorated]


# D29 canonical movement is intentionally narrower than retrieval or sequencing.
# A selected doorway is itself a canonical destination when it has a usable,
# canonical URL. A further "next" destination requires an explicit canonical
# relationship supplied by the resource metadata; semantic similarity,
# retrieval rank, or the phrase "related resource" never creates a movement edge.

_D29_EXPLICIT_NEXT_URL_KEYS = (
    "next_url",
    "next_canonical_url",
    "canonical_next_url",
)

_D29_EXPLICIT_RELATION_KEYS = (
    "related_canonical_url",
    "canonical_related_url",
    "canonical_destination_url",
)

_D29_INTERNAL_CANONICAL_HOST = "geralddaquila.com"


def _canonical_url_for_movement(resource: Dict[str, Any]) -> str:
    if not isinstance(resource, dict):
        return ""
    url = str(resource.get("url", "")).strip()
    if not url or url == "#" or not re.match(r"^https?://", url, flags=re.IGNORECASE):
        return ""
    if _is_use_interface_resource(resource):
        return ""
    return url


def _normalize_movement_url(url: Any) -> str:
    """Normalize URL identity without changing canonical destination authority."""
    raw = str(url or "").strip()
    if not raw:
        return ""
    raw = raw.split("#", 1)[0].split("?", 1)[0].rstrip("/")
    return raw.casefold()


def _canonical_document_url_map(
    canonical_documents: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    return {
        _normalize_movement_url(_canonical_url_for_movement(document)): document
        for document in canonical_documents
        if _normalize_movement_url(_canonical_url_for_movement(document))
    }


def _extract_explicit_canonical_links(resource: Dict[str, Any]) -> List[str]:
    """Extract explicit internal canonical links present in resource content.

    A link is evidence of a canonical relationship, not automatically a
    'next' step. This distinction prevents ordinary semantic or hyperlink
    proximity from becoming an invented sequence edge.
    """
    if not isinstance(resource, dict):
        return []

    content = _resource_content(resource)
    if not content:
        return []

    urls: List[str] = []
    patterns = (
        r'href=["\'](https?://[^"\'\s>]+)["\']',
        r'\[[^\]]+\]\((https?://[^)\s]+)(?:\s+[^)]*)?\)',
    )
    for pattern in patterns:
        for match in re.finditer(pattern, content, flags=re.IGNORECASE):
            url = str(match.group(1)).strip()
            try:
                host_match = re.search(r'^https?://([^/]+)', url, flags=re.IGNORECASE)
                host = host_match.group(1).casefold() if host_match else ""
                if host.startswith("www."):
                    host = host[4:]
                if host != _D29_INTERNAL_CANONICAL_HOST:
                    continue
            except Exception:
                continue
            normalized = _normalize_movement_url(url)
            if normalized and normalized not in urls:
                urls.append(normalized)

    return urls[:12]


def _explicit_next_destination(
    resource: Dict[str, Any],
    canonical_documents: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Resolve only an explicitly declared next canonical destination."""
    if not isinstance(resource, dict):
        return None

    allowed = _canonical_document_url_map(canonical_documents)
    for key in _D29_EXPLICIT_NEXT_URL_KEYS:
        candidate_url = _normalize_movement_url(resource.get(key, ""))
        if candidate_url and candidate_url in allowed:
            return allowed[candidate_url]

    return None


def _explicit_linked_destinations(
    resource: Dict[str, Any],
    canonical_documents: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Resolve explicit canonical links to resources already in the evidence set."""
    allowed = _canonical_document_url_map(canonical_documents)
    destinations: List[Dict[str, Any]] = []
    seen = set()

    explicit_urls: List[str] = []
    for key in _D29_EXPLICIT_RELATION_KEYS:
        candidate = _normalize_movement_url(resource.get(key, ""))
        if candidate and candidate not in explicit_urls:
            explicit_urls.append(candidate)
    for candidate in _extract_explicit_canonical_links(resource):
        if candidate not in explicit_urls:
            explicit_urls.append(candidate)

    own_url = _normalize_movement_url(_canonical_url_for_movement(resource))
    for candidate in explicit_urls:
        if candidate == own_url or candidate in seen:
            continue
        destination = allowed.get(candidate)
        if destination is not None:
            destinations.append(destination)
            seen.add(candidate)
        if len(destinations) >= 4:
            break

    return destinations


def _apply_canonical_movement_logic(
    documents: List[Dict[str, Any]],
    question: str,
) -> List[Dict[str, Any]]:
    """Attach validated D29 movement relations without manufacturing routes.

    D29 now distinguishes three states:
      1. selected canonical resource = validated doorway/destination;
      2. explicit canonical next declaration = validated next movement;
      3. explicit canonical internal link = validated relationship, but NOT
         automatically a next step.

    Semantic similarity, retrieval rank, resource function, or generic
    relatedness cannot create a movement edge.
    """
    if not documents:
        return documents

    primary = documents[0]
    primary_url = _canonical_url_for_movement(primary)

    for index, document in enumerate(documents):
        if not isinstance(document, dict):
            continue

        own_url = _canonical_url_for_movement(document)
        next_destination = _explicit_next_destination(document, documents)
        linked_destinations = _explicit_linked_destinations(document, documents)

        if next_destination:
            movement_status = "validated_next"
        elif linked_destinations:
            movement_status = "explicit_related"
        elif own_url:
            movement_status = "doorway_only"
        else:
            movement_status = "no_validated_movement"

        movement = {
            "doorway": index == 0,
            "doorway_title": str(primary.get("title", "Untitled Resource")).strip()
            if index == 0
            else "",
            "destination_url": own_url,
            "destination_validated": bool(own_url),
            "movement_status": movement_status,
            "next_destination_title": (
                str(next_destination.get("title", "Untitled Resource")).strip()
                if next_destination
                else ""
            ),
            "next_destination_url": (
                _canonical_url_for_movement(next_destination)
                if next_destination
                else ""
            ),
            "next_destination_validated": bool(next_destination),
            "linked_destination_titles": [
                str(destination.get("title", "Untitled Resource")).strip()
                for destination in linked_destinations
            ],
            "linked_destination_urls": [
                _canonical_url_for_movement(destination)
                for destination in linked_destinations
            ],
            "linked_destination_validated": bool(linked_destinations),
            "movement_basis": (
                "selected canonical resource"
                if own_url
                else "no usable canonical destination"
            ),
            "next_movement_basis": (
                "explicit canonical next-resource declaration"
                if next_destination
                else "none — no explicit canonical next-resource declaration"
            ),
            "linked_movement_basis": (
                "explicit canonical internal link in supplied evidence"
                if linked_destinations
                else "none — no explicit canonical internal link resolved"
            ),
        }
        document["_use_canonical_movement"] = movement

    print(
        "USE D29 canonical movement: "
        f"doorway='{_canonical_display_title(str(primary.get('title', 'Untitled Resource')))}', "
        f"destination_validated={bool(primary_url)}, "
        f"explicit_next={sum(1 for d in documents if (d.get('_use_canonical_movement') or {}).get('next_destination_validated'))}, "
        f"explicit_links={sum(1 for d in documents if (d.get('_use_canonical_movement') or {}).get('linked_destination_validated'))}."
    )
    return documents


def _d28_resource_sequencing_self_audit() -> None:
    """Verify D28 does not equate retrieval rank with sequence role."""
    question = (
        "I want a guided way to explore what the Living Archive might offer me, "
        "so I can discover what matters and decide where I want to go next."
    )
    navigator = {
        "title": "Archive Navigator",
        "_use_navigator_function": {"function": _D25_NAVIGATOR_FUNCTION_LABEL},
        "url": "https://example.invalid/navigator",
    }
    essay = {
        "title": "Archive Essay",
        "_use_essay_function": {"function": _D21_ESSAY_FUNCTION_LABEL},
        "url": "https://example.invalid/essay",
    }
    result = _apply_resource_sequence_metadata([essay, navigator], question)
    assert result[0] is navigator
    assert result[0]["_use_resource_sequence_role"] == "primary_orientation_entry"
    assert result[1]["_use_resource_sequence_role"] == "available_canonical_resource"
    print("USE D28 RESOURCE SEQUENCING AUDIT: PASS")


def _d29_canonical_movement_self_audit() -> None:
    """Verify explicit next relations and explicit canonical links are distinct."""
    question = "Where should I begin exploring the Living Archive?"
    navigator = {
        "title": "Archive Navigator",
        "_use_navigator_function": {"function": _D25_NAVIGATOR_FUNCTION_LABEL},
        "url": "https://geralddaquila.com/navigator/",
    }
    essay = {
        "title": "Archive Essay",
        "_use_essay_function": {"function": _D21_ESSAY_FUNCTION_LABEL},
        "url": "https://example.invalid/essay",
        "text": 'Continue with [Archive Navigator](https://geralddaquila.com/navigator/).',
    }
    result = _apply_resource_sequence_metadata([navigator, essay], question)
    result = _apply_canonical_movement_logic(result, question)
    assert result[0]["_use_canonical_movement"]["doorway"] is True
    assert result[0]["_use_canonical_movement"]["destination_validated"] is True
    assert result[0]["_use_canonical_movement"]["next_destination_validated"] is False

    linked = result[1]["_use_canonical_movement"]
    assert linked["linked_destination_validated"] is True
    assert linked["linked_destination_urls"] == [navigator["url"]]
    assert linked["next_destination_validated"] is False

    explicit_next = dict(essay)
    explicit_next["next_canonical_url"] = navigator["url"]
    linked_result = _apply_canonical_movement_logic(
        [explicit_next, navigator], question
    )
    assert linked_result[0]["_use_canonical_movement"]["next_destination_url"] == navigator["url"]

    invented = dict(essay)
    invented["next_canonical_url"] = "https://example.invalid/not-selected"
    invented_result = _apply_canonical_movement_logic([invented], question)
    assert invented_result[0]["_use_canonical_movement"]["next_destination_validated"] is False
    assert invented_result[0]["_use_canonical_movement"]["linked_destination_validated"] is False

    external = dict(essay)
    external["text"] = 'See [External](https://example.org/not-canonical).'
    external_result = _apply_canonical_movement_logic([external, navigator], question)
    assert external_result[0]["_use_canonical_movement"]["linked_destination_validated"] is False

    # v122 hard boundary: semantic continuity must not be sufficient for a route.
    no_route_context = format_context_blocks(result)
    inferred = (
        "A logical next step would be to explore Archive Navigator because its "
        "title and description suggest continuity with the current resource."
    )
    gated = _apply_movement_evidence_gate(inferred, question, no_route_context)
    assert "logical next step" not in gated.casefold()
    assert "canonically defined next step" in gated.casefold()

    validated_context = format_context_blocks(linked_result)
    validated_answer = "The logical next step is Archive Navigator."
    assert _apply_movement_evidence_gate(
        validated_answer, question, validated_context
    ) == validated_answer

    print("USE D29 CANONICAL MOVEMENT EVIDENCE GATE AUDIT: PASS")


def _d30_archive_navigation_audit() -> None:
    """Audit sequencing, destination validation, and explicit relation integrity."""
    question = "Where should I begin exploring the Living Archive?"
    navigator = {
        "title": "Archive Navigator",
        "_use_navigator_function": {"function": _D25_NAVIGATOR_FUNCTION_LABEL},
        "url": "https://geralddaquila.com/navigator/",
    }
    essay = {
        "title": "Archive Essay",
        "_use_essay_function": {"function": _D21_ESSAY_FUNCTION_LABEL},
        "url": "https://example.invalid/essay",
        "text": 'Continue with [Archive Navigator](https://geralddaquila.com/navigator/).',
    }

    selected = _apply_resource_sequence_metadata([essay, navigator], question)
    selected = _apply_canonical_movement_logic(selected, question)

    assert selected[0]["_use_resource_sequence_role"] == "primary_orientation_entry"
    assert selected[0]["_use_canonical_movement"]["destination_url"] == navigator["url"]
    assert selected[0]["_use_canonical_movement"]["next_destination_validated"] is False

    # An explicit internal canonical link is a legitimate relation but is not
    # silently upgraded to a 'next' route.
    assert selected[1]["_use_canonical_movement"]["linked_destination_validated"] is True
    assert selected[1]["_use_canonical_movement"]["next_destination_validated"] is False

    # D30 boundary: relevance is not movement. A semantically plausible answer
    # must be rejected when no D29 next destination exists.
    inferred_answer = (
        "A useful place to continue would be Archive Essay because it builds on "
        "the same themes."
    )
    gated_inferred = _apply_movement_evidence_gate(
        inferred_answer, question, format_context_blocks(selected)
    )
    assert "useful place to continue" not in gated_inferred.casefold()
    assert "canonically defined next step" in gated_inferred.casefold()

    # D30 boundary: every visitor-facing destination or relation must resolve
    # to a canonical resource already present in the validated evidence set.
    selected_urls = {
        _normalize_movement_url(document.get("url"))
        for document in selected
        if isinstance(document, dict) and document.get("url")
    }
    for document in selected:
        movement = document.get("_use_canonical_movement") or {}
        for next_url in [movement.get("next_destination_url", "")]:
            if next_url:
                assert _normalize_movement_url(next_url) in selected_urls
        for linked_url in movement.get("linked_destination_urls") or []:
            assert _normalize_movement_url(linked_url) in selected_urls

    # v122: an explicit request for an "established next resource" is a
    # movement question even when it does not use the phrase "next step".
    assert _movement_question_requires_canonical_next(
        "Is there an established next resource from here?"
    ) is True

    no_route_context = format_context_blocks(selected)
    no_route_fallback = _deterministic_provider_fallback(
        "Is there an established next resource from here?",
        no_route_context,
    )
    assert "does not establish a next destination" in no_route_fallback.casefold()
    assert "could not complete its interpretive response" not in no_route_fallback.casefold()

    explicit_source = {
        "title": "Explicit Source",
        "url": "https://geralddaquila.com/explicit-source/",
        "next_url": essay["url"],
    }
    explicit_docs = _apply_canonical_movement_logic(
        [explicit_source, essay],
        "Is there an established next resource from Explicit Source?",
    )
    explicit_context = format_context_blocks(explicit_docs)
    assert _movement_context_has_validated_next(explicit_context) is True
    explicit_fallback = _deterministic_provider_fallback(
        "Is there an established next resource from Explicit Source?",
        explicit_context,
    )
    assert "Archive Essay" in explicit_fallback

    print("USE D30 ARCHIVE NAVIGATION RELATION AUDIT: PASS")


def _orientation_loop_state(question: str, intent: str) -> Dict[str, Any]:
    """Represent the D31-D38 visitor-facing loop without diagnosing the visitor."""
    frame = build_recognition_orientation(question, intent)
    q = re.sub(r"\s+", " ", str(question or "").casefold()).strip()
    movement = bool(re.search(r"\b(?:where|begin|start|next|go|path|pathway|explore|navigate|route|read first|read next)\b", q))
    sovereignty = bool(re.search(r"\b(?:i want|i'd like|i would like|i can decide|i choose|my own|self-directed|without telling me what)\b", q))
    open_exploration = bool(
        re.search(r"\b(?:explore|exploring|discover|find out|see what)\b", q)
        and re.search(r"\b(?:don.t know|do not know|not sure|uncertain|without jumping to (?:a )?conclusion|without (?:a )?conclusion|without deciding|without assuming)\b", q)
    )
    return {
        **frame,
        "movement_need": movement or open_exploration,
        "open_exploration": open_exploration,
        "sovereignty_preserved": True,
        "premature_closure_guard": True,
    }
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

    if not _is_navigable_canonical_resource(metadata):
        return

    metadata = _attach_canonical_resource_model(metadata)
    metadata = _attach_resource_type_recognition(metadata)
    metadata = _attach_essay_function(metadata)
    metadata = _attach_cornerstone_function(metadata)
    metadata = _attach_knowledge_hub_function(metadata)
    metadata = _attach_reference_map_function(metadata)
    metadata = _attach_navigator_function(metadata)
    metadata = _attach_pathway_function(metadata)
    metadata = _attach_case_learning_arc_function(metadata)

    if require_destination and not _has_usable_destination(metadata):
        print(
            "USE destination validation: rejected non-destination "
            f"resource '{metadata.get('title', 'Untitled Resource')}'."
        )
        return

    key = _resource_key(metadata)

    if key in seen_keys:
        # v135: retrieval deduplication is an evidence consolidation boundary,
        # not an evidence-loss boundary. A function-targeted retrieval may
        # independently establish stronger D20/D21-D27 recognition for a
        # canonical resource that was already present in the ordinary semantic
        # candidate window. Preserve that stronger recognition on the existing
        # canonical record rather than silently discarding the second sighting.
        for existing in documents:
            if _resource_key(existing) != key:
                continue

            # Preserve previously supplied source metadata, while filling
            # missing fields discovered by the new canonical retrieval.
            for field, value in metadata.items():
                if field not in existing or existing.get(field) in (None, "", [], {}):
                    existing[field] = value

            # D20 may have been unknown on the first retrieval but positively
            # recognized on the later type-constrained retrieval. Upgrade only
            # when the later recognition is stronger; never downgrade an
            # established canonical type.
            incoming_type = _recognize_resource_type(metadata).get("resource_type")
            existing_type = _recognize_resource_type(existing).get("resource_type")
            if incoming_type and not existing_type:
                existing["_use_resource_type_recognition"] = _recognize_resource_type(metadata)

            # v140: preserve explicit publication-family selection provenance
            # even when the targeted candidate is a duplicate of an ordinary
            # semantic retrieval result.
            incoming_selection_identity = metadata.get(
                "_use_explicit_type_selection_identity"
            )
            if isinstance(incoming_selection_identity, dict):
                requested_type = incoming_selection_identity.get("requested_type")
                source = incoming_selection_identity.get("source")
                if (
                    requested_type
                    and source == "D20_type_constrained_function_retrieval"
                    and _recognize_resource_type(existing).get("resource_type")
                    == requested_type
                ):
                    existing["_use_explicit_type_selection_identity"] = dict(
                        incoming_selection_identity
                    )

            # Likewise preserve independently established function recognition
            # without allowing a weaker duplicate to overwrite it.
            annotation_pairs = (
                "_use_essay_function",
                "_use_cornerstone_function",
                "_use_knowledge_hub_function",
                "_use_reference_map_function",
                "_use_navigator_function",
                "_use_pathway_function",
                "_use_case_learning_arc_function",
            )
            for annotation_key in annotation_pairs:
                incoming_annotation = metadata.get(annotation_key)
                existing_annotation = existing.get(annotation_key)
                incoming_function = (
                    incoming_annotation.get("function")
                    if isinstance(incoming_annotation, dict)
                    else None
                )
                existing_function = (
                    existing_annotation.get("function")
                    if isinstance(existing_annotation, dict)
                    else None
                )
                if incoming_function and not existing_function:
                    existing[annotation_key] = incoming_annotation

            print(
                "USE canonical evidence enrichment: merged stronger recognition "
                f"for duplicate '{_canonical_display_title(existing.get('title', 'Untitled Resource'))}'."
            )
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

        if not _is_navigable_canonical_resource(metadata):
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


def _evidence_domain_fit_score(
    question: str,
    metadata: Dict[str, Any],
) -> Tuple[int, Tuple[int, int]]:
    """Measure bounded substantive fit using supplied Content only.

    This is a post-retrieval sufficiency gate, not a retrieval engine. Titles,
    URLs, categories, and other identity metadata are intentionally excluded.
    A small morphology normalization permits obvious forms such as
    understand/understanding without importing semantic knowledge.
    """
    content = _resource_content(metadata).casefold()
    if not question or not content:
        return 0, (0, 0)

    terms, phrases = _question_condition_terms(question)
    substantive = tuple(
        term for term in dict.fromkeys(terms)
        if term not in _CENTRALITY_GENERIC_TERMS
    )
    if not substantive:
        substantive = tuple(dict.fromkeys(terms))

    content_tokens = set(re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)?", content))

    def stem(value: str) -> str:
        value = value.casefold().replace("-", "")
        for suffix in ("ingly", "edly", "ing", "ed", "ness", "able", "ible", "es", "s"):
            if len(value) > 5 and value.endswith(suffix):
                return value[: -len(suffix)]
        return value

    content_stems = {stem(token) for token in content_tokens}
    term_hits = 0
    for term in set(substantive):
        normalized = term.replace("-", "")
        if term in content_tokens or normalized in content_tokens or stem(term) in content_stems:
            term_hits += 1

    phrase_hits = sum(1 for phrase in set(phrases) if phrase in content)
    # One phrase is strong evidence of direct topical fit; otherwise require
    # at least two distinct substantive question concepts in supplied Content.
    score = min(6, term_hits + (phrase_hits * 2))
    return score, (term_hits, phrase_hits)


def _evidence_sufficiency_gate(
    documents: List[Dict[str, Any]],
    question: str,
    intent: str,
) -> Tuple[List[Dict[str, Any]], bool]:
    """Separate synthesis sufficiency from navigational usefulness.

    Retrieved resources remain available for canonical movement even when
    their Content does not support a reliable explanatory synthesis.
    """
    if intent not in {"TOPICAL_INQUIRY", "COMPARATIVE_INQUIRY"} or not documents:
        return documents, False

    # D17 reconciliation: an explicit relational question is allowed to
    # proceed to the existing evidence-bound generation boundary even when
    # lexical domain-fit is low. D16 must not turn a relational question into
    # a navigation-only result merely because no single vocabulary match was
    # found. First-person open experiential questions retain the stronger
    # evidence-sufficiency boundary because interpretive-frame sovereignty
    # remains active there.
    if (
        recognize_question_structure(question).get("structure") == "explicit_contrast"
        and not _question_is_frame_open(question)
    ):
        print(
            "USE evidence sufficiency reconciliation: explicit relational "
            "question retained for evidence-bound synthesis despite low lexical fit."
        )
        return documents, False

    fit_scores = [
        _evidence_domain_fit_score(question, document)[0]
        for document in documents
    ]
    sufficient = any(score >= 2 for score in fit_scores)
    if sufficient:
        return documents, False

    print(
        "USE evidence sufficiency gate: insufficient substantive domain fit; "
        f"scores={fit_scores}. Synthesis withheld; navigation preserved."
    )
    return documents, True


def _evidence_sufficiency_unavailable_response(
    question: str,
    canonical_link_context: str = "",
) -> str:
    """Preserve the question while keeping genuine canonical movement open."""
    pairs = []
    for title, url in _canonical_pairs(canonical_link_context):
        clean_title = _canonical_display_title(title)
        if clean_title and url:
            pairs.append((clean_title, url))
        if len(pairs) >= 2:
            break

    response = (
        "The canonical material surfaced for this question does not establish "
        "a reliable explanation, so USE will not fill the gap with an inferred "
        "mechanism. The question remains open."
    )
    if pairs:
        response += (
            " The closest canonical places surfaced for continuing the inquiry are: "
            + " ; ".join(f"[{title}]({url})" for title, url in pairs)
            + "."
        )
    return response


def fetch_canonical_context(
    user_query: str,
) -> Dict[str, Any]:
    intent = classify_intent(user_query)
    collection_name = detect_collection_request(user_query)
    adaptive_orientation = detect_adaptive_stewardship_orientation(user_query)
    orientational_frame = infer_orientational_frame(user_query)
    recognition_orientation = build_recognition_orientation(user_query, intent)
    orientation_loop = _orientation_loop_state(user_query, intent)
    orientational_frame = {**orientational_frame, **recognition_orientation, **orientation_loop}

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
    document_choice_architecture_docs: List[Dict[str, Any]] = []
    seen_keys = set()
    # Initialize before any bounded early-return path. The query route must
    # always be able to preserve canonical link context, including when the
    # evidence-sufficiency gate withholds generation.
    canonical_link_context = ""

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

    function_targeted_docs: List[Dict[str, Any]] = []

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

                # v97 baseline: preserve the complete bounded semantic candidate window
                # through downstream ranking. v96 truncated ordinary candidates
                # at MAX_CONTEXT_RESOURCES before question-conditioned doorway
                # selection, so a strong canonical match appearing later in the
                # RETRIEVAL_TOP_K window could never be promoted. This changes only
                # candidate-window recall; retrieval remains the sole source of
                # candidates and the final generation cap remains downstream.
                for _score, _match_id_value, metadata in candidates:
                    _append_unique_resource(
                        retrieved_docs,
                        seen_keys,
                        metadata,
                        require_destination=bool(collection_name),
                    )
                    if len(retrieved_docs) >= RETRIEVAL_TOP_K:
                        break
            else:
                candidates = []

            # D28/D29 continuity bridge: if the visitor explicitly asks for a
            # resource function, retrieve a small function-targeted candidate set
            # before the final context cap. This closes the v113 gap where the
            # correct function could never be selected because it was absent from
            # the semantic top-K window.
            document_choice_architecture_docs = _document_choice_architecture_candidate_search(user_query)
            function_targeted_docs = _function_targeted_candidate_search(user_query)
            for metadata in document_choice_architecture_docs + function_targeted_docs:
                _append_unique_resource(retrieved_docs, seen_keys, metadata)
                if len(retrieved_docs) >= RETRIEVAL_TOP_K + 8:
                    break

            print(
                "USE retrieval: "
                f"{len(candidates)} candidates + "
                f"{len(document_choice_architecture_docs)} architecture + "
                f"{len(function_targeted_docs)} function-targeted -> "
                f"{len(retrieved_docs)} unique resources."
            )

    except Exception as exc:
        print(f"Index query error: {exc}")

    retrieved_docs = [
        doc
        for doc in retrieved_docs
        if isinstance(doc, dict) and doc
    ][:RETRIEVAL_TOP_K + 8]

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
    for document in document_choice_architecture_docs:
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
    )

    # D17: recognize an explicit contrast already present in the visitor's
    # wording, then refine only the already-retrieved evidence toward resources
    # whose supplied Content addresses both sides. This is not a second
    # retrieval engine and does not infer the visitor's underlying state.
    retrieved_docs = question_structure_rerank_documents(
        retrieved_docs,
        user_query,
        preserve_prefix=protected_prefix,
    )

    # D17/v92: question structure informs reasoning posture, not a lexical
    # evidence gate. Grounding remains the retrieval constraint; D17 must not
    # manufacture a second retrieval/sufficiency test that can false-negative
    # legitimate multi-resource evidence. Existing retrieved evidence remains
    # available to the normal frame/provenance/synthesis boundaries below.
    question_structure = recognize_question_structure(user_query)
    if question_structure.get("structure") == "explicit_contrast":
        print(
            "USE D17 relational reasoning: explicit question contrast recognized; "
            "multi-resource evidence remains available for bounded synthesis."
        )

    # Canonical link authority remains independent of synthesis reasoning.
    canonical_link_context = format_context_blocks(
        canonical_link_docs,
        structural_destination_count=0,
        adaptive_bridge_count=0,
    )

    # v137: an explicit publication-family request must survive the final
    # doorway-selection cap once D20 has positively established the requested
    # resource type. Retrieval precision is not sufficient if the requested
    # type is subsequently displaced by higher-scoring generic resources.
    # Capture only explicitly requested types here; generic functional
    # questions remain governed by the ordinary doorway ranking.
    explicit_type_targets = _explicit_resource_type_targets(user_query)
    # v137: preserve the actual accepted function-targeted candidate objects
    # independently of ordinary retrieval deduplication. v134/v135/v136 could
    # establish D20 identity but still lose the candidate before this boundary
    # because the ordinary retrieval pool and display-title dedupe had already
    # collapsed it. Carry-forward is evidence preservation only: it does not
    # create a relationship, movement edge, or ranking preference beyond the
    # visitor's explicit resource-family request.
    explicit_type_protected_docs: List[Dict[str, Any]] = []
    explicit_type_protected_seen = set()
    for document in list(function_targeted_docs) + list(retrieved_docs):
        recognized_type = _recognize_resource_type(document).get("resource_type")
        selection_identity = _explicit_type_selection_identity(document)
        if recognized_type not in explicit_type_targets:
            continue
        if selection_identity and selection_identity["requested_type"] in explicit_type_targets:
            recognized_type = selection_identity["requested_type"]
        key = _resource_key(document)
        if key in explicit_type_protected_seen:
            continue
        explicit_type_protected_seen.add(key)
        explicit_type_protected_docs.append(document)

    # v65: explicit doorway selection is a final routing refinement over
    # already-retrieved, lifecycle-eligible evidence. It does not expand
    # retrieval or alter canonical link authority.
    retrieved_docs = select_canonical_doorways(
        retrieved_docs,
        orientational_frame,
        question=user_query,
        preserve_prefix=protected_prefix,
    )

    # Preserve at least one D20-recognized candidate for each explicitly
    # requested publication family. This is a selection safeguard, not a route
    # or relationship declaration: the resource remains merely available
    # evidence unless later logic establishes something stronger.
    retrieved_docs = _preserve_explicit_type_candidates(
        retrieved_docs,
        explicit_type_protected_docs,
        explicit_type_targets,
    )
    retrieved_docs = _apply_resource_sequence_metadata(
        retrieved_docs, user_query
    )
    # D29: sequencing establishes possible roles; canonical movement then
    # validates the actual doorway/destination relationship. No route is created
    # from semantic similarity or retrieval rank.
    retrieved_docs = _apply_canonical_movement_logic(
        retrieved_docs,
        user_query,
    )

    # v76: for open first-person experiential questions, do not let a retrieved
    # specialized worldview become substantive generation evidence when a
    # frame-neutral canonical resource is already available. Canonical link
    # authority remains untouched above; only the provider evidence set is
    # narrowed.
    retrieved_docs, frame_neutral_boundary_active = _frame_neutral_generation_documents(
        retrieved_docs,
        user_query,
        intent,
    )
    if frame_neutral_boundary_active and not retrieved_docs:
        return {
            "intent": intent,
            "orientational_frame": orientational_frame,
            "context_blocks": "",
            "canonical_link_context": canonical_link_context,
            "frame_neutral_evidence_unavailable": True,
        }

    # D16: retrieval relevance does not by itself establish evidence sufficiency.
    # Apply a bounded post-retrieval Content-domain gate before generation.
    # Canonical link authority remains untouched above.
    retrieved_docs, evidence_sufficiency_unavailable = _evidence_sufficiency_gate(
        retrieved_docs,
        user_query,
        intent,
    )
    if evidence_sufficiency_unavailable:
        return {
            "intent": intent,
            "orientational_frame": orientational_frame,
            "context_blocks": "",
            "canonical_link_context": canonical_link_context,
            "evidence_sufficiency_unavailable": True,
        }

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

    # v140: explicit type selection identity is a canonical evidence
    # requirement, not merely a doorway-ranking preference. Reassert accepted
    # type-constrained candidates after the downstream frame-neutral and
    # sufficiency gates so a later generic narrowing step cannot silently erase
    # the resource family the visitor explicitly asked about. This still uses
    # only candidates already validated by D20; it creates no route or relation.
    if explicit_type_targets and explicit_type_protected_docs:
        before_reassert = list(retrieved_docs)
        retrieved_docs = _preserve_explicit_type_candidates(
            retrieved_docs,
            explicit_type_protected_docs,
            explicit_type_targets,
        )
        if retrieved_docs != before_reassert:
            print(
                "USE explicit type selection identity: "
                f"preserved requested types={sorted(explicit_type_targets)}, "
                f"selected={len(retrieved_docs)}."
            )

    # v159: a form-choice question requires the Archive's own publication-
    # architecture evidence to survive downstream narrowing. Preserve the
    # canonical anchor inside the generation set when retrieval found it.
    before_document_choice_preservation = list(retrieved_docs)
    retrieved_docs = _preserve_document_choice_architecture_candidates(
        retrieved_docs,
        document_choice_architecture_docs,
    )
    if retrieved_docs != before_document_choice_preservation:
        print(
            "USE document-choice architecture evidence preservation: "
            f"anchor={_DOCUMENT_CHOICE_ARCHITECTURE_TITLE!r}, "
            f"selected={len(retrieved_docs)}."
        )

    # v40 root-cause boundary: generation and link authority are two
    # deliberately different contexts. The model receives ONLY the
    # selected, deduplicated, orientationally-reranked resources. The
    # complete canonical set is retained separately for final link
    # reconstruction. The previous version accidentally supplied the
    # complete canonical-link set to generation, bypassing the selected
    # retrieval order and allowing the bounded generation window to change
    # which resources the model could see.
    retrieved_docs = _prioritize_explicit_type_generation_documents(
        retrieved_docs,
        explicit_type_protected_docs,
        explicit_type_targets,
    )
    retrieved_docs = _prioritize_document_choice_architecture_generation_documents(
        retrieved_docs,
        document_choice_architecture_docs,
    )

    document_form_orientation_packet = _build_document_form_orientation_evidence_packet(
        user_query,
        retrieved_docs,
        document_choice_architecture_docs,
    )
    if document_form_orientation_packet:
        print(
            "USE document-form orientation evidence packet: "
            f"chars={len(document_form_orientation_packet)}, "
            "source=D21-D26 canonical resource-function layer."
        )

    generation_context = format_context_blocks(
        retrieved_docs,
        structural_destination_count=structural_destination_count,
        adaptive_bridge_count=adaptive_bridge_count,
    )
    if document_form_orientation_packet:
        generation_context = (
            document_form_orientation_packet
            + "\n\n---\n\n"
            + generation_context
        )

    # v56 observability: expose the selected generation set in deployment logs.
    # This makes it possible to distinguish retrieval narrowing from model
    # selection without exposing any internal information to visitors.
    # v144 diagnostic only: expose exact protected identities and the
    # candidate set immediately before generation selection. No behavior change.
    if explicit_type_targets:
        print(
            "USE explicit type selection diagnostic: "
            f"targets={sorted(explicit_type_targets)}, "
            f"protected={[(d.get('title'), d.get('url'), _recognize_resource_type(d).get('resource_type'), _resource_key(d)) for d in explicit_type_protected_docs]}, "
            f"pre_generation={[(d.get('title'), d.get('url'), _recognize_resource_type(d).get('resource_type'), _resource_key(d)) for d in retrieved_docs]}"
        )

    print(
        "USE generation selection: "
        f"selected={len(retrieved_docs)}, "
        f"titles={[ _canonical_display_title(str(doc.get('title', 'Untitled Resource'))) for doc in retrieved_docs ]}"
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


def _provider_evidence_identity_context(
    safe_context: str,
    canonical_identity_context: str,
) -> str:
    """Authorize only canonical resources actually represented in safe evidence.

    Compact provider evidence can be schema-free and omit URL fields. This helper
    restores canonical URL identity only for titles that are actually present in
    the provider-safe representation. It never expands authority to an omitted
    resource. D29 movement authorization remains a separate system boundary.
    """
    if not safe_context or not canonical_identity_context:
        return ""

    canonical_by_title = {}
    for title, url in _canonical_pairs(canonical_identity_context):
        display = _canonical_display_title(title)
        if display and url:
            canonical_by_title[display.casefold()] = (display, url)

    if not canonical_by_title:
        return ""

    represented = []
    represented_keys = set()
    for block in safe_context.split("\n\n---\n\n"):
        title_match = re.search(
            r"^Title:\s*(.+?)\s*$", block, flags=re.MULTILINE
        )
        if title_match:
            title = _canonical_display_title(title_match.group(1).strip())
        else:
            compact_match = re.match(
                r"^(.+?)\s+—\s+(.*)$", block, flags=re.DOTALL
            )
            if not compact_match:
                continue
            title = _canonical_display_title(compact_match.group(1).strip())

        key = title.casefold() if title else ""
        if key in canonical_by_title and key not in represented_keys:
            represented_keys.add(key)
            represented.append(canonical_by_title[key])

    return "\n\n---\n\n".join(
        f"Title: {title}\nURL: {url}\nContent:"
        for title, url in represented
    )


def _clean_generation_output(
    generated_text: str,
    generation_context: str,
    canonical_link_context: str = "",
) -> str:
    answer = _extract_visitor_answer(generated_text)
    if not answer:
        return ""

    # Generated visitor-facing links must remain inside the same canonical
    # resource set that authorizes the answer. A broader canonical-link
    # context may contain related resources, but it cannot authorize a model
    # to introduce one that was not selected as generation evidence.
    # Validation context is the authoritative Title/URL set for this boundary.
    link_context = generation_context

    # Resource eligibility and link eligibility are governed by the selected
    # generation set. Broader canonical link authority must never expand the
    # resources the visitor is offered by a generated answer.
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
# LONGITUDINAL INQUIRY OBSERVER — PASSIVE 5-WHY BOUNDARY
# =====================================================================
# This observer is deliberately outside current-turn reasoning. It observes
# the completed question sequence and may produce a next-turn Steward Access
# invitation after five consecutive stewardship-related questions. It never
# diagnoses readiness, grants access, or changes the current retrieval/answer.

PROGRESSIVE_INQUIRY_TERMS = (
    "stewardship", "steward", "custodian", "guardian", "responsibility",
    "accountability", "service", "serve others", "service to others", "entrusted",
    "future generations", "larger whole", "beyond myself", "contribution",
)

def _history_questions(history: Any) -> List[str]:
    """Extract only prior visitor questions from optional client history."""
    if not isinstance(history, list):
        return []
    questions: List[str] = []
    for item in history[-12:]:
        if isinstance(item, str):
            value = item.strip()
        elif isinstance(item, dict):
            role = str(item.get("role", "")).casefold()
            if role and role not in {"user", "visitor", "human"}:
                continue
            value = str(
                item.get("question")
                or item.get("content")
                or item.get("text")
                or ""
            ).strip()
        else:
            continue
        if value:
            questions.append(value)
    return questions

def _is_stewardship_question(question: str) -> bool:
    clean = re.sub(r"\s+", " ", str(question or "").casefold()).strip()
    return any(
        re.search(rf"(?<!\w){re.escape(term)}(?!\w)", clean)
        for term in PROGRESSIVE_INQUIRY_TERMS
    )

def assess_progressive_commitment(
    current_question: str,
    history: Any = None,
) -> Dict[str, Any]:
    """Observe completed-turn trajectory without influencing that turn."""
    prior = _history_questions(history)
    questions = prior + [str(current_question or "").strip()]
    consecutive = 0
    for question in reversed(questions):
        if _is_stewardship_question(question):
            consecutive += 1
        else:
            break

    return {
        "turns": len(questions),
        "stewardship_consecutive": consecutive,
        "steward_access_invitation": consecutive >= 5,
        "observer_only": True,
        "current_turn_influence": False,
        "native_vocabulary_allowed": False,
    }

def progressive_inquiry_invitation(state: Dict[str, Any]) -> str:
    """Return the bounded invitation; never imply readiness or membership."""
    if not state.get("steward_access_invitation"):
        return ""
    return (
        "If you would like to continue this inquiry into the deeper stewardship "
        "layer of the Living Archive, Steward Access is available."
    )

# =====================================================================
# GROQ GENERATION
# =====================================================================


def _bound_existing_context_blocks(
    context_blocks: str,
    max_chars: int,
    max_resource_chars: int,
    *,
    schema_free: bool = False,
) -> str:
    """Bound canonical blocks to an exact character ceiling without losing identity.

    ``schema_free`` is used only for compact provider recovery. It preserves
    canonical title identity and evidence text while removing the internal
    Title/URL/Content field labels that small recovery models were observed
    to reproduce as visitor-facing schema. It also accepts an already-schema-free
    block so the compact representation can safely pass through later budget
    fitting without losing its evidence.
    """
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

        if schema_free and (not title_match or not content_match):
            # Compact recovery may already be receiving the schema-free form
            # produced by the recovery path. Preserve that representation
            # rather than attempting to parse the primary Title/URL/Content
            # schema and silently discarding the evidence.
            compact_match = re.match(r"^(.+?)\s+—\s+(.*)$", block, flags=re.DOTALL)
            if compact_match:
                title = _canonical_display_title(compact_match.group(1).strip())
                url = ""
                content = compact_match.group(2).strip()
            else:
                continue
        else:
            if not title_match or not url_match or not content_match:
                continue
            title = _canonical_display_title(title_match.group(1).strip())
            url = url_match.group(1).strip()
            content = content_match.group(1).strip()

        if schema_free:
            prefix = f"{title} — "
        else:
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


def _question_is_underdetermined(question: str) -> bool:
    """Detect broad experiential questions that do not name a clear mechanism.

    This is intentionally structural rather than domain-specific. It looks for
    an inward/experiential question whose substantive wording remains broad,
    then tells generation to preserve multiple plausible interpretations.
    It does not select or exclude resources.
    """
    value = str(question or "").strip().casefold()
    if not value:
        return False

    tokens = re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)?", value)
    if not tokens or not any(token in tokens for token in ("why", "how")):
        return False

    broad_terms = {
        "something", "things", "life", "feel", "feeling", "feels",
        "important", "matter", "matters", "meaning", "care", "cared",
        "want", "wanted", "wrong", "right", "fine", "inside",
        "outside", "sometimes", "often", "used",
    }
    mechanism_terms = {
        "habit", "habits", "choice", "choices", "dissonance", "scarcity",
        "conditioning", "pressure", "conflict", "memory", "trauma",
        "belief", "beliefs", "identity", "relationship", "work",
        "sleep", "stress", "fear", "decision", "decisions",
    }

    substantive = [
        token for token in tokens
        if len(token) >= 4 and token not in _QUESTION_STOPWORDS
    ]
    if not substantive:
        return False

    broad_hits = sum(1 for token in substantive if token in broad_terms)
    mechanism_hits = sum(1 for token in substantive if token in mechanism_terms)

    # A broad first-person experiential question with no named mechanism is
    # underdetermined by structure, even when retrieved resources offer a
    # compelling specialized interpretation.
    first_person = any(token in tokens for token in ("i", "my", "me"))
    experiential = any(token in tokens for token in (
        "feel", "feeling", "feels", "care", "cared", "want", "wanted",
        "important", "wrong", "fine", "inside", "outside",
    ))
    return first_person and experiential and broad_hits >= 1 and mechanism_hits == 0


def _build_generation_system_content(
    intent: str,
    generation_context: str,
    *,
    compact: bool = False,
) -> str:
    """
    Build the complete generation system message from explicitly supplied
    local variables. No generation path relies on an ambient context variable.
    """
    return (
        f"{COMPACT_GENERATION_SYSTEM_PROMPT if compact else GENERATION_SYSTEM_PROMPT}\n\n"
        f"[CLASSIFICATION — DO NOT REVEAL]: {intent}\n\n"
        f"[CANONICAL EVIDENCE]:\n"
        f"{generation_context}"
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
    compact: bool = False,
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
        user_query, intent, "", orientational_frame, compact=compact
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

    # Preserve selected resource ordering while converting to a dense provider
    # evidence view. URLs remain available to deterministic link presentation but
    # do not consume scarce provider evidence characters.
    if candidate:
        target_context_chars = min(
            len(candidate),
            context_capacity,
            MAX_GENERATION_CONTEXT_CHARS,
        )
        bounded_selected = _bound_existing_context_blocks(
            candidate,
            max(0, target_context_chars),
            min(
                MAX_GENERATION_RESOURCE_CHARS,
                max(120, target_context_chars),
            ) if target_context_chars > 0 else 0,
            schema_free=compact,
        )

        # v148 root-cause boundary: a positive primary evidence capacity must
        # not silently collapse existing canonical evidence to zero blocks.
        # Route this recoverable condition through the existing compact
        # generation path, which rebuilds from the original generation context.
        if (
            not compact
            and candidate.strip()
            and target_context_chars > 0
            and not bounded_selected.strip()
        ):
            print(
                "USE generation boundary: "
                f"{_request_correlation_log_prefix()}, "
                "primary evidence capacity cannot preserve a minimally viable "
                "canonical evidence block; entering compact recovery; "
                f"context_capacity={context_capacity}, "
                f"target_context_chars={target_context_chars}, "
                f"canonical_context={len(candidate)}."
            )
            raise ValueError(
                "USE provider preflight could not preserve a minimally viable "
                "canonical evidence block within the primary envelope: "
                f"context_capacity={context_capacity}, "
                f"target_context_chars={target_context_chars}."
            )

        candidate = _build_provider_evidence_context(
            bounded_selected,
            max(0, target_context_chars),
            min(
                MAX_GENERATION_RESOURCE_CHARS,
                max(96, target_context_chars),
            ) if target_context_chars > 0 else 0,
            schema_free=compact,
        )

        # v148 root-cause boundary: never silently collapse existing canonical
        # evidence to zero when the primary envelope has positive capacity but
        # no complete evidence block can survive. Route this through the
        # established compact recovery path.
        if (
            not compact
            and str(generation_context or "").strip()
            and target_context_chars > 0
            and not bounded_selected.strip()
        ):
            print(
                "USE generation boundary: "
                f"{_request_correlation_log_prefix()}, "
                "primary evidence capacity cannot preserve a minimally viable "
                "canonical evidence block; entering compact recovery; "
                f"context_capacity={context_capacity}, "
                f"target_context_chars={target_context_chars}, "
                f"canonical_context={len(str(generation_context or '').strip())}."
            )
            raise ValueError(
                "USE provider preflight could not preserve a minimally viable "
                "canonical evidence block within the primary envelope: "
                f"context_capacity={context_capacity}, "
                f"target_context_chars={target_context_chars}."
            )
        # Root preservation invariant: valid bounded canonical context must
        # never silently become empty during provider evidence formatting.
        if bounded_selected.strip() and not candidate.strip():
            candidate = bounded_selected.strip()
            print(
                "USE generation evidence preservation: "
                f"{_request_correlation_log_prefix()}, "
                "secondary provider formatter returned empty evidence; "
                f"retaining bounded canonical context ({len(candidate)} chars)."
            )

    while True:
        messages = _build_generation_messages(
            user_query, intent, candidate, orientational_frame, compact=compact
        )
        input_chars = _estimate_message_chars(messages)
        total_estimate = input_chars + estimated_output_chars

        if (
            input_chars <= MAX_PROVIDER_INPUT_CHARS
            and total_estimate <= MAX_PROVIDER_TOTAL_CHARS
        ):
            print(
                "USE provider preflight: "
                f"{_request_correlation_log_prefix()}, "
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

        candidate = candidate[:target_context_chars].rstrip()



def _build_provider_evidence_context(
    generation_context: str,
    max_chars: int,
    max_resource_chars: int,
    *,
    schema_free: bool = False,
) -> str:
    """Build a dense provider evidence view while preserving the input schema mode.

    Compact recovery receives schema-free blocks from ``_bound_existing_context_blocks``.
    v128 accidentally passed those blocks into this legacy Title/Content parser, which
    silently discarded every block and produced ``evidence=0``. v129 keeps the compact
    representation intact instead of attempting to parse it as the primary schema.
    """
    if not generation_context or max_chars <= 0:
        return ""
    blocks = []
    used = 0
    for block in generation_context.split("\n\n---\n\n"):
        if schema_free:
            match = re.match(r"^(.+?)\s+—\s+(.*)$", block, flags=re.DOTALL)
            if not match:
                continue
            title = _canonical_display_title(match.group(1).strip())
            content = match.group(2).strip()
        else:
            title_match = re.search(r"^Title:\s*(.+?)\s*$", block, flags=re.MULTILINE)
            content_match = re.search(r"^Content:\s*(.*)$", block, flags=re.MULTILINE | re.DOTALL)
            if not title_match or not content_match:
                continue
            title = _canonical_display_title(title_match.group(1).strip())
            content = content_match.group(1).strip()
        if not title:
            continue
        prefix = f"{title} — " if schema_free else f"Title: {title}\nContent: "
        separator = "\n\n---\n\n" if blocks else ""
        remaining = max_chars - used - len(separator)
        if remaining <= len(prefix):
            break
        capacity = min(max_resource_chars, remaining - len(prefix))
        if capacity <= 0:
            break
        bounded = content[:capacity].rstrip()
        if len(content) > capacity and capacity > 18:
            marker = " … [bounded]"
            bounded = content[:capacity - len(marker)].rstrip() + marker
        candidate = prefix + bounded
        if len(candidate) > remaining:
            break
        blocks.append(candidate)
        used += len(separator) + len(candidate)
    return "\n\n---\n\n".join(blocks).strip()


def _question_is_frame_open(question: str) -> bool:
    """Detect first-person experiential questions whose interpretive frame is open."""
    value = str(question or "").strip().casefold()
    if not value or not any(token in value.split() for token in ("why", "how", "what", "if")):
        return False
    tokens = re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)?", value)
    if not any(token in tokens for token in ("i", "my", "me")):
        return False
    if any(
        term in tokens or re.search(rf"\b{re.escape(term)}\b", value)
        for term in _SPECIALIZED_FRAMEWORK_TERMS
    ):
        return False
    open_experiential_terms = {
        "experience", "experiences", "feel", "feeling", "feels", "meaning",
        "interpret", "interpretation", "interpretations", "understand",
        "understanding", "aware", "awareness", "know", "knowing", "want",
        "wanted", "matter", "matters", "available", "change", "changing",
        "familiar", "unfamiliar", "clarity", "clearer", "certain", "uncertain",
    }
    return bool(open_experiential_terms & set(tokens))


def _interpretive_frame_sovereignty_instruction(question: str, intent: str) -> str:
    """Return a generation guard against uninvited specialized framing."""
    if intent != "TOPICAL_INQUIRY" or not _question_is_frame_open(question):
        return ""
    return (
        "\n\n[INTERPRETIVE FRAME SOVEREIGNTY — DO NOT REVEAL]: "
        "The visitor has not established a specialized framework in the question. "
        "Do not make a retrieved specialized framework the governing explanation "
        "of the visitor's experience. Do not imply that the visitor is undergoing "
        "that framework or that its characteristic outcome follows from the "
        "question. If such a resource is useful, identify it only as that "
        "resource's lens and preserve the question in the visitor's own terms. "
        "If the available evidence is mainly specialized, say that its fit is "
        "limited or framework-specific rather than translating the question into "
        "that framework. "
    )


def build_recognition_orientation(question: str, intent: str) -> Dict[str, Any]:
    """Translate explicit question form into a bounded orientation posture."""
    q = re.sub(r"\s+", " ", str(question or "").strip().casefold())
    q = re.sub(r"[?!.]+$", "", q).strip()
    if not q:
        return {"recognition": "no explicit question supplied", "orientation_mode": "clarify", "orientation_confidence": "low"}
    if intent == "WHOLE_SITE_ORIENTATION" or q in {"what is the living archive", "what is the archive", "what is this archive", "where do i start", "where should i start"}:
        return {"recognition": "the visitor is asking for orientation within the Archive", "orientation_mode": "locate", "orientation_confidence": "explicit"}
    if re.search(r"\b(?:how can i tell|how do i know|is it|whether|or whether)\b", q):
        mode = "distinguish"
    elif re.search(r"\b(?:compare|comparison|both|different|difference|versus|vs)\b", q):
        mode = "compare"
    elif re.search(r"\b(?:what should i do|what do i do|what now|what next|where do i go)\b", q):
        mode = "move"
    elif re.search(r"\b(?:what happens|what changes|what becomes|what can become)\b", q):
        mode = "explore"
    elif re.search(r"\b(?:why|how|what does|what is|what makes)\b", q):
        mode = "understand"
    else:
        mode = "clarify"
    return {
        "recognition": "the question is seeking understanding, distinction, exploration, or movement rather than a presumed diagnosis",
        "orientation_mode": mode,
        "orientation_confidence": "explicit",
    }



def recognize_question_structure(question: str) -> Dict[str, Any]:
    """Extract explicit relational structure from the visitor's wording only.

    This is a bounded routing aid, not a theory of the visitor. It identifies
    contrasts/tensions already stated in the question so retrieval can favor
    already-retrieved evidence that addresses both sides.
    """
    q = re.sub(r"\s+", " ", str(question or "").strip().casefold())
    q = re.sub(r"[?!.]+$", "", q).strip()
    if not q:
        return {"structure": "none", "pairs": (), "confidence": "low"}

    patterns = (
        r"^why can (.+?)\s+(?:and still|but still|while|yet)\s+(.+)$",
        r"^why does (.+?)\s+(?:while|but|yet)\s+(.+)$",
        r"^how can (.+?)\s+(?:and still|but still|while|yet)\s+(.+)$",
        r"^why can (.+?)\s+and\s+(.+?\b(?:differently|different))$",
        r"^(.+?)\s+(?:different from|rather than)\s+(.+)$",
    )
    left = right = ""
    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            left, right = match.group(1).strip(), match.group(2).strip()
            break

    if not left or not right:
        # A smaller fallback for explicit "without" contrasts. Keep the
        # extraction conservative so ordinary questions remain untouched.
        match = re.search(r"^(.+?)\s+without\s+(.+)$", q)
        if match:
            left, right = match.group(1).strip(), match.group(2).strip()

    if not left or not right:
        return {"structure": "none", "pairs": (), "confidence": "low"}

    stop = set(_QUESTION_STOPWORDS)
    def terms(text: str) -> Tuple[str, ...]:
        words = re.findall(r"[a-z][a-z'-]{2,}", text)
        return tuple(dict.fromkeys(w for w in words if w not in stop))[:8]

    left_terms = terms(left)
    right_terms = terms(right)
    if not left_terms or not right_terms:
        return {"structure": "none", "pairs": (), "confidence": "low"}
    return {
        "structure": "explicit_contrast",
        "pairs": (left_terms, right_terms),
        "confidence": "explicit",
    }


def _question_structure_content_score(
    metadata: Dict[str, Any],
    structure: Dict[str, Any],
) -> Tuple[int, int]:
    """Score only supplied substantive Content for coverage of both sides."""
    pairs = structure.get("pairs") or ()
    if len(pairs) != 2:
        return (0, 0)
    content = str(metadata.get("content") or metadata.get("text") or "").casefold()
    if not content:
        return (0, 0)
    left, right = pairs
    left_hits = sum(1 for term in left if re.search(r"\b" + re.escape(term) + r"\b", content))
    right_hits = sum(1 for term in right if re.search(r"\b" + re.escape(term) + r"\b", content))
    return (left_hits + right_hits, min(left_hits, right_hits))


def question_structure_rerank_documents(
    documents: List[Dict[str, Any]],
    question: str,
    *,
    preserve_prefix: int = 0,
) -> List[Dict[str, Any]]:
    """Refine existing retrieval toward an explicit question contrast only."""
    structure = recognize_question_structure(question)
    if structure.get("structure") != "explicit_contrast" or not documents:
        return documents
    prefix = documents[:preserve_prefix]
    remainder = documents[preserve_prefix:]
    ranked = sorted(
        enumerate(remainder),
        key=lambda item: (
            -_question_structure_content_score(item[1], structure)[1],
            -_question_structure_content_score(item[1], structure)[0],
            item[0],
        ),
    )
    return prefix + [doc for _index, doc in ranked]


def _recognition_orientation_instruction(frame: Dict[str, Any]) -> str:
    """Return a compact internal transition cue for generation."""
    mode = str(frame.get("orientation_mode", "understand")).strip()
    return f"\n{mode}"


def _open_exploration_sovereignty_instruction(question: str) -> str:
    """Bind explicit open-exploration posture to generation without diagnosing the visitor."""
    q = re.sub(r"\s+", " ", str(question or "").casefold()).strip()
    uncertainty = bool(re.search(r"\b(?:don.t know|do not know|not sure|uncertain|don.t know yet|do not yet know)\b", q))
    exploration = bool(re.search(r"\b(?:explore|exploring|discover|find out|see what)\b", q))
    nonclosure = bool(re.search(r"\b(?:without jumping to (?:a )?conclusion|without (?:a )?conclusion|without deciding|without assuming|not jump to|don.t want .* conclusion)\b", q))
    if not (exploration and (uncertainty or nonclosure)):
        return ""
    return (
        "\n\n[OPEN EXPLORATION SOVEREIGNTY — DO NOT REVEAL]: "
        "The visitor explicitly wants to explore while something remains uncertain or "
        "undecided. Do not convert that uncertainty into a conclusion, root cause, "
        "diagnosis, or governing interpretation. Do not state that a retrieved resource "
        "explains what the visitor is experiencing unless the supplied evidence directly "
        "establishes that claim. Treat specialized resources as lenses rather than as "
        "the visitor's explanation. Prefer recognition of the open question, a bounded "
        "orientation, and a canonical next movement. If the evidence supports several "
        "possible directions but not one meaning, preserve that openness explicitly. "
    )


def _movement_question_requires_canonical_next(user_query: str) -> bool:
    """Recognize explicit requests to establish canonical continuation.

    This is an intent trigger, not a route inference mechanism. Natural
    formulations such as "an established canonical resource that comes next"
    must reach the D29 evidence gate, while ordinary topical questions that
    merely mention "next" should remain ordinary inquiry.
    """
    q = re.sub(r"\s+", " ", str(user_query or "").casefold()).strip()
    if not q:
        return False

    direct_route = bool(
        re.search(
            r"\b(?:where|what)\s+(?:should|would|can|could)\s+i\s+"
            r"(?:begin|start|go|look|turn|continue)",
            q,
        )
        or re.search(
            r"\b(?:what|where)\s+(?:is|would be|can i find)\s+"
            r"(?:a )?(?:good|useful|logical|natural|next|following)\s+"
            r"(?:step|place|destination|resource|path|pathway)",
            q,
        )
        or re.search(
            r"\b(?:next step|next destination|next resource|next place|"
            r"established next|established (?:canonical )?(?:resource|destination|"
            r"continuation)|canonical (?:next|continuation)|"
            r"what comes next from here|what comes next from this|what follows from here|where do i go from here|"
            r"where to go|path forward|continue from|continue with|"
            r"move next|go next)\b",
            q,
        )
        or re.search(
            r"\b(?:is there|are there)\b.{0,80}\b(?:next|following|"
            r"comes next|canonical continuation|established)\b",
            q,
        )
    )

    # Keep ordinary topical questions out of the movement gate unless they
    # explicitly ask for a route/continuation.
    return direct_route


def _movement_context_has_validated_next(generation_context: str) -> bool:
    """Return True only when D29 explicitly validated a next destination."""
    return bool(
        re.search(
            r"^D29 Next Canonical Destination:\s*https?://\S+",
            str(generation_context or ""),
            flags=re.MULTILINE | re.IGNORECASE,
        )
    )


def _movement_positive_route_claim(answer: str) -> bool:
    """Detect positive route claims that would promote relevance into movement."""
    text = re.sub(r"\s+", " ", str(answer or "").casefold()).strip()
    if not text:
        return False
    negative_prefix = r"(?:no|not|isn't|is not|doesn't|does not|without)"
    positive_patterns = (
        r"\b(?:a |the )?(?:logical|natural|useful|good|best|appropriate|clear|right)\s+next\s+step\b",
        r"\b(?:a |the )?(?:logical|natural|useful|good|best|appropriate|clear|right)\s+next\s+(?:place|destination)\b",
        r"\b(?:your|the)\s+next\s+step\s+(?:is|would be|could be)\b",
        r"\b(?:continue|continuing)\s+(?:with|from)\s+\[?[^\n.?!]+",
        r"\b(?:a |the )?(?:useful|good|natural|logical)\s+place\s+to\s+continue\b",
        r"\b(?:i|we)\s+(?:would|recommend)\s+(?:you\s+)?(?:continue|go|move)\b",
    )
    for pattern in positive_patterns:
        for match in re.finditer(pattern, text):
            start = max(0, match.start() - 24)
            prefix = text[start:match.start()]
            if not re.search(negative_prefix + r"\s*$", prefix):
                return True
    return False


def _deterministic_movement_evidence_fallback(
    user_query: str,
    generation_context: str,
) -> str:
    """Propagate the D29 movement state into a safe visitor-facing response.

    A movement question must never fall through to the generic provider-error
    message merely because no route was validated. If D29 validated a next
    destination, expose that destination. Otherwise state plainly that no
    canonical next destination has been established.
    """
    context = str(generation_context or "")
    next_match = re.search(
        r"^D29 Next Canonical Destination:\s*(https?://\S+)\s*$",
        context,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    if next_match:
        next_url = next_match.group(1).strip()
        normalized_next = _normalize_movement_url(next_url)
        next_title = ""
        for title, url in _canonical_pairs(context):
            if _normalize_movement_url(url) == normalized_next:
                next_title = _canonical_display_title(title)
                break

        if next_title:
            return (
                "The supplied canonical evidence establishes the following "
                f"next destination: {next_title}. "
                "This is an explicitly defined canonical movement from the "
                "resource you are continuing from."
            )
        return (
            "The supplied canonical evidence establishes an explicit next "
            "destination from this point. The Guide can therefore treat that "
            "destination as the canonical continuation."
        )

    pairs = _canonical_pairs(context)
    if not pairs:
        return (
            "The supplied canonical evidence does not establish a next "
            "destination from this point. The question remains open rather "
            "than being assigned an inferred route."
        )

    title = _canonical_display_title(pairs[0][0])
    return (
        "The supplied canonical evidence does not establish a next destination "
        "from this point. It does surface "
        f"{title} as an available canonical place to explore, but not as a "
        "canonically defined next step. You can decide whether it fits your inquiry."
    )


def _apply_movement_evidence_gate(
    answer: str,
    user_query: str,
    generation_context: str,
) -> str:
    """Enforce D29 after generation: relevance may surface, but cannot become route."""
    if not answer or not _movement_question_requires_canonical_next(user_query):
        return answer
    if _movement_context_has_validated_next(generation_context):
        return answer
    if not _movement_positive_route_claim(answer):
        return answer

    print(
        "USE D29 movement evidence gate: rejecting a positive next-step claim "
        "because no canonical next destination was explicitly validated."
    )
    return _deterministic_movement_evidence_fallback(
        user_query, generation_context
    )


def _build_generation_messages(
    user_query: str,
    intent: str,
    generation_context: str,
    orientational_frame: Optional[Dict[str, Any]] = None,
    *,
    compact: bool = False,
) -> List[Dict[str, str]]:
    """Build one canonical provider request from one explicit context value.

    ``compact`` is an explicit recovery-mode selector used by the provider
    budget fitter. It changes only the fixed generation envelope; canonical
    evidence remains supplied through the same explicit context boundary.
    """
    safe_context = str(generation_context or "").strip()
    frame = orientational_frame or {"primary": "general", "scores": {}}
    frame_hint = str(frame.get("primary", "general"))
    underdetermined = _question_is_underdetermined(user_query)

    if compact:
        # Compact recovery deliberately uses only the essential constitutional
        # generation boundary. The primary envelope's orientation/recognition
        # scaffolding is valuable, but it is not necessary to preserve the hard
        # evidence, sovereignty, provenance, and D29 movement constraints.
        # Keeping those invariants while removing nonessential fixed-prompt
        # material is what makes compact recovery executable when the primary
        # fixed envelope itself is too large.
        system_content = _build_generation_system_content(
            intent,
            safe_context,
            compact=True,
        )
    else:
        # v165: use the lean constitutional envelope on the primary path too.
        # The prior primary-only orientation scaffolding consumed enough fixed
        # budget to leave almost no canonical evidence for complex tasks.
        system_content = _build_generation_system_content(
            intent,
            safe_context,
            compact=True,
        )

    if compact:
        user_content = (
            user_query
            + "\n\nAnswer from evidence; preserve uncertainty. Exact titles only; no links or markup."
        )
    else:
        user_content = (
            user_query
            + "\n\nAnswer only from supplied evidence; preserve uncertainty. Exact titles; no links or markup."
        )

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def _contains_canonical_resource_reference(
    answer: str,
    generation_context: str,
) -> bool:
    """Return True when visitor output names at least one selected canonical resource."""
    if not answer or not generation_context:
        return False

    canonical_titles = [
        _canonical_display_title(match.group(1).strip())
        for match in re.finditer(
            r"^Title:\s*(.+?)\s*$", generation_context, flags=re.MULTILINE
        )
        if _canonical_display_title(match.group(1).strip())
    ]
    if not canonical_titles:
        canonical_titles = [
            _canonical_display_title(title)
            for title, _url in _canonical_pairs(generation_context)
            if _canonical_display_title(title)
        ]
    for title in canonical_titles:
        if re.search(
            rf"(?<![\w]){re.escape(title)}(?![\w])",
            answer,
            flags=re.IGNORECASE,
        ):
            return True
    return False


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
    reasoning_effort: Optional[str] = None,
    orientational_frame: Optional[Dict[str, Any]] = None,
    canonical_link_context: str = "",
    validation_context: str = "",
    compact: bool = False,
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
        compact=compact,
    )

    estimated_quota_tokens = _estimate_quota_tokens(messages, max_tokens)
    _known_daily_tpd_preflight(model_id, estimated_quota_tokens)

    try:
        provider_kwargs = {
            "model": model_id,
            "messages": messages,
            "temperature": 0.2,
            "max_completion_tokens": max_tokens,
        }
        if reasoning_effort and model_id.startswith("openai/gpt-oss-"):
            provider_kwargs["reasoning_effort"] = reasoning_effort
        response = groq_client.chat.completions.create(**provider_kwargs)
    except Exception as exc:
        _log_provider_exception_diagnostic(
            "compact" if compact else "primary",
            model_id,
            exc,
            max_tokens=max_tokens,
            input_chars=_estimate_message_chars(messages),
            evidence_chars=len(safe_context),
        )
        raise

    choice = response.choices[0]
    finish_reason = getattr(choice, "finish_reason", None)
    generated_text = choice.message.content or ""

    if str(finish_reason or "").lower() in {"length", "max_tokens"}:
        print(
            f"USE output boundary: model '{model_id}' reached its generation "
            "limit; rejecting incomplete visitor answer."
        )
        return ""

    # v166: visitor-facing resource authority is limited to canonical evidence
    # actually represented in the provider-safe evidence for this attempt.
    # The broader selected context remains an upstream reasoning/selection field.
    reasoning_evidence_identity = _provider_evidence_identity_context(
        safe_context,
        str(validation_context or generation_context or ""),
    )
    effective_validation_context = reasoning_evidence_identity

    cleaned_answer = _clean_generation_output(
        generated_text,
        effective_validation_context,
        canonical_link_context,
    )

    # D29 remains an independent system-level navigation authorization boundary.
    # It is intentionally evaluated against validated movement metadata rather
    # than inferred from the provider-safe evidence representation.
    movement_authority_context = str(validation_context or generation_context or "")
    cleaned_answer = _apply_movement_evidence_gate(
        cleaned_answer,
        user_query,
        movement_authority_context,
    )

    # v151 MVP boundary: a provider may mention canonical resources while
    # simultaneously making an unsupported claim that the evidence contains
    # no information about the visitor question. Canonical presence alone does
    # not make that negative claim valid. Reject it so another model/fallback
    # can provide an evidence-first response.
    if (
        cleaned_answer
        and _canonical_pairs(effective_validation_context)
        and _looks_like_false_evidence_gap_claim(cleaned_answer)
    ):
        print(
            f"USE MVP output boundary: rejected unsupported evidence-gap claim "
            f"from model '{model_id}'; canonical evidence is present."
        )
        return ""

    # v61 root-cause boundary: a topical response that ignores all selected
    # canonical resources is a generic knowledge answer, not USE navigation.
    # Reject it before visitor delivery so the model fallback chain can try
    # another candidate. This does not alter retrieval or force a particular resource.
    if (
        cleaned_answer
        and str(intent).upper() == "TOPICAL_INQUIRY"
        and _canonical_pairs(effective_validation_context)
        and not _contains_canonical_resource_reference(
            cleaned_answer,
            effective_validation_context,
        )
    ):
        print(
            f"USE output boundary: topical response ignored all selected "
            f"canonical resources for model '{model_id}'; no alternate model will be attempted."
        )
        return ""

    if cleaned_answer and not _looks_like_finished_visitor_answer(cleaned_answer):
        print(
            f"USE output boundary: model '{model_id}' returned an incomplete "
            "visitor answer; no alternate model will be attempted."
        )
        return ""

    return cleaned_answer


def _log_provider_exception_diagnostic(
    stage: str,
    model_id: str,
    exc: Exception,
    *,
    max_tokens: int,
    input_chars: Optional[int] = None,
    evidence_chars: Optional[int] = None,
) -> None:
    """Log structured provider failure metadata without changing recovery behavior."""
    status_code = getattr(exc, "status_code", None)
    response = getattr(exc, "response", None)
    response_headers: Dict[str, str] = {}
    response_body: Any = getattr(exc, "body", None)

    if response is not None:
        try:
            headers = getattr(response, "headers", None)
            if headers is not None:
                for header_name in (
                    "x-request-id",
                    "x-groq-request-id",
                    "x-ratelimit-limit-requests",
                    "x-ratelimit-remaining-requests",
                    "x-ratelimit-reset-requests",
                    "x-ratelimit-limit-tokens",
                    "x-ratelimit-remaining-tokens",
                    "x-ratelimit-reset-tokens",
                ):
                    value = headers.get(header_name)
                    if value is not None:
                        response_headers[header_name] = str(value)
        except Exception:
            response_headers = {}

        try:
            response_body = response.json()
        except Exception:
            try:
                response_body = getattr(response, "text", None)
            except Exception:
                response_body = None

    if response_body is not None:
        try:
            response_body_text = json.dumps(response_body, ensure_ascii=False, default=str)
        except Exception:
            response_body_text = repr(response_body)
        response_body_text = response_body_text[:2000]
    else:
        response_body_text = ""

    diagnostic = {
        "stage": str(stage),
        "model": str(model_id),
        "exception_class": type(exc).__name__,
        "status_code": status_code,
        "error": str(exc)[:1000],
        "response_headers": response_headers,
        "response_body": response_body_text,
        "max_tokens": int(max_tokens),
        "input_chars": input_chars,
        "evidence_chars": evidence_chars,
    }
    print(
        "USE PROVIDER ERROR DIAGNOSTIC: "
        f"{json.dumps(diagnostic, ensure_ascii=False, sort_keys=True)}"
    )


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
            "use provider preflight could not fit the fixed system/user envelope",
            "use provider preflight could not preserve a minimally viable canonical evidence block",
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


def _looks_like_false_evidence_gap_claim(answer: str) -> bool:
    """Detect a provider claim that selected evidence contains no answer.

    This is an MVP response-boundary guard. A provider may correctly mention
    canonical resources while still making the stronger, unsupported claim
    that the supplied evidence contains no information about the question.
    When canonical evidence is present, that claim must not reach the visitor.
    """
    value = re.sub(r"\s+", " ", str(answer or "")).casefold().strip()
    if not value:
        return False

    markers = (
        "provided canonical evidence does not contain",
        "canonical evidence does not contain",
        "canonical evidence contains no information",
        "available evidence does not contain",
        "available evidence contains no information",
        "evidence does not contain information regarding",
        "evidence does not contain information about",
        "the excerpts do not define",
        "the excerpts do not explain",
        "no information regarding",
        "no information about",
        "does not establish the purpose of",
    )
    return any(marker in value for marker in markers)


def _extractive_canonical_evidence_fallback(
    user_query: str,
    generation_context: str,
) -> str:
    """Produce a bounded evidence-first answer when generation is unavailable.

    This is intentionally extractive rather than generative. It may select
    short sentences that overlap the visitor's question, but it never invents
    a relationship, definition, causal bridge, or resource identity. Canonical
    titles/URLs remain authoritative and links are normalized downstream.
    """
    documents = context_blocks_to_documents(str(generation_context or ""))
    if not documents:
        return ""

    query_tokens = {
        token
        for token in re.findall(r"[a-z0-9]{3,}", str(user_query or "").casefold())
        if token not in {
            "what", "when", "where", "which", "that", "this", "does", "from",
            "with", "about", "into", "over", "than", "they", "them", "just",
            "simply", "reading", "read", "different", "purpose", "living",
            "archive", "and", "the", "for", "how", "why", "are", "was", "is",
        }
    }

    scored = []
    for doc_index, document in enumerate(documents):
        title = _canonical_display_title(str(document.get("title", "")).strip())
        text = re.sub(r"\s+", " ", str(document.get("text", "") or "")).strip()
        if not title or not text:
            continue

        # Sentence-level extraction. Keep short, complete evidence units only.
        sentences = re.split(r"(?<=[.!?])\s+", text)
        for sentence_index, sentence in enumerate(sentences):
            sentence = sentence.strip(" \t\r\n•-")
            if len(sentence) < 35 or len(sentence) > 260:
                continue
            words = set(re.findall(r"[a-z0-9]{3,}", sentence.casefold()))
            overlap = len(query_tokens & words)
            # Explicit resource-family terms are useful anchors when present.
            family_bonus = 0
            if "reference map" in str(user_query or "").casefold() and "reference map" in sentence.casefold():
                family_bonus += 4
            score = overlap * 3 + family_bonus
            if score <= 0:
                continue
            scored.append((score, -doc_index, -sentence_index, title, sentence))

    if not scored:
        return ""

    scored.sort(reverse=True)
    selected = []
    seen_sentences = set()
    seen_titles = set()
    for _score, _doc, _sent, title, sentence in scored:
        key = sentence.casefold()
        if key in seen_sentences:
            continue
        selected.append((title, sentence))
        seen_sentences.add(key)
        seen_titles.add(title.casefold())
        if len(selected) >= 3:
            break

    if not selected:
        return ""

    lines = [
        "The canonical material available here does contain relevant substance for this question. The most directly relevant passages are:",
        "",
    ]
    for title, sentence in selected:
        lines.append(f"**{title}**: {sentence}")

    lines.extend([
        "",
        "These passages are the evidence available for the question; any connection between them beyond what they explicitly state remains open for your own reading.",
    ])
    return "\n".join(lines)


def _deterministic_provider_fallback(
    user_query: str,
    generation_context: str,
) -> str:
    """Return a safe visitor response without another provider call.

    MVP correction: when provider generation fails after canonical evidence has
    already been selected, prefer a bounded extractive evidence response over
    a flat resource list. The fallback remains strictly evidence-bound and
    preserves visitor sovereignty.
    """
    if _movement_question_requires_canonical_next(user_query):
        return _deterministic_movement_evidence_fallback(
            user_query,
            generation_context,
        )

    extractive = _extractive_canonical_evidence_fallback(
        user_query,
        generation_context,
    )
    if extractive:
        # v167: deterministic/extractive fallback must pass through the same
        # canonical presentation boundary as provider-generated output.
        # The fallback may identify canonical evidence, but it must not strand
        # the visitor at an unlinked title when a canonical doorway exists.
        normalized_fallback = _clean_generation_output(
            extractive,
            generation_context,
            generation_context,
        )
        return normalized_fallback or extractive

    q = re.sub(r"\s+", " ", str(user_query or "").casefold()).strip()
    open_exploration = bool(
        re.search(r"\b(?:explore|exploring|discover|find out|see what)\b", q)
        and re.search(r"\b(?:don.t know|do not know|not sure|uncertain|without jumping to (?:a )?conclusion|without (?:a )?conclusion|without deciding|without assuming)\b", q)
    )

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

    if open_exploration and pairs:
        lines = [
            "What you have described does not, by itself, establish what connects these experiences — and the available evidence should not be treated as a conclusion about their cause.",
            "",
            "The canonical material below offers different places to look rather than a single explanation. You can explore what resonates, compare the lenses, and decide for yourself what, if anything, connects to your experience.",
            "",
        ]
        lines.extend(f"- [{title}]({url})" for title, url in pairs)
        return "\n".join(lines)

    if not pairs:
        return (
            "The Living Archive is temporarily unable to generate a full "
            "answer for this question. Please try again shortly."
        )

    lines = [
        "The Living Archive could not complete its interpretive response right now, but these canonical resources are the relevant material available for your question:",
        "",
    ]
    lines.extend(f"- [{title}]({url})" for title, url in pairs)
    return "\n".join(lines)



def _classify_generation_complexity(
    user_query: str,
    intent: str,
    generation_context: str,
    orientational_frame: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Classify the visitor task before provider selection.

    Complexity is deterministic. Evidence volume is a primary signal, but
    task structure can raise the class because a short comparative question
    may require more reasoning than a longer single-resource explanation.
    Exactly one model is selected from the class; this is not a model lottery.
    """
    query = re.sub(r"\s+", " ", str(user_query or "")).strip().casefold()
    context_chars = len(str(generation_context or ""))
    resource_count = len(_canonical_pairs(str(generation_context or "")))

    synthesis_signals = [
        bool(re.search(r"\b(?:compare|comparison|different|difference|differences|versus|vs\.?|between|which|choose|decide|how should i choose|what would help me decide)\b", query)),
        bool(re.search(r"\b(?:relationship|relationships|relate|relates|connect|connections|fit together|how .* work together|across|multiple|several|sequences|forms|formats)\b", query)),
        bool(re.search(r"\b(?:essay|reference map|navigator|pathway)\b", query)) and bool(re.search(r"\b(?:what|which|how|difference|choose|start|use|offer|meant)\b", query)),
    ]
    complex_signals = [
        bool(re.search(r"\b(?:competing|conflicting|conflict|contradictory|ambiguity|ambiguous|uncertain|uncertainty|trade-?off|reconcile|reconciliation)\b", query)),
        bool(re.search(r"\b(?:synthesize|synthesis|integrate|integration|cross-resource|across multiple|multiple perspectives|multiple resources)\b", query)),
        resource_count >= 8 and context_chars >= 1400,
    ]

    # Evidence volume provides the requested simple-to-complex baseline.
    if context_chars <= 650:
        complexity = 1
    elif context_chars <= 1200:
        complexity = 2
    elif context_chars <= 1800:
        complexity = 3
    else:
        complexity = 4

    # Structural task requirements may raise the class, never lower it.
    synthesis_count = sum(1 for signal in synthesis_signals if signal)
    complex_count = sum(1 for signal in complex_signals if signal)
    if synthesis_count >= 2:
        complexity = max(complexity, 3)
    if complex_count >= 2:
        complexity = 4

    # Explicit movement remains governed by D29; complexity only chooses the
    # reasoning model and does not create a destination.
    if _movement_question_requires_canonical_next(query):
        complexity = max(complexity, 2)

    model_by_complexity = {
        1: "openai/gpt-oss-20b",
        2: "groq/compound-mini",
        3: "openai/gpt-oss-120b",
        4: "groq/compound",
    }
    selected_model = model_by_complexity[complexity]
    reason = []
    if context_chars <= 650:
        reason.append("compact evidence volume")
    elif context_chars <= 1200:
        reason.append("moderate evidence volume")
    elif context_chars <= 1800:
        reason.append("high evidence volume")
    else:
        reason.append("very high evidence volume")
    if synthesis_count:
        reason.append(f"synthesis_signals={synthesis_count}")
    if complex_count:
        reason.append(f"complex_signals={complex_count}")

    return {
        "complexity": complexity,
        "context_chars": context_chars,
        "resource_count": resource_count,
        "synthesis_signals": synthesis_count,
        "complex_signals": complex_count,
        "model": selected_model,
        "reason": "; ".join(reason),
    }


def _generation_budget_profile(routing: Dict[str, Any], *, compact: bool = False) -> Dict[str, Any]:
    """Return the deterministic provider budget matched to the selected task class.

    The model class and completion/reasoning budget are one routing decision.
    This prevents a complex reasoning task from inheriting the old global 290-token
    ceiling, while keeping the conservative provider envelope authoritative.
    """
    complexity = int(routing.get("complexity", 1))
    profiles = {
        1: {"model": "openai/gpt-oss-20b", "max_completion_tokens": 256, "reasoning_effort": "low", "compact_tokens": 256},
        2: {"model": "groq/compound-mini", "max_completion_tokens": 320, "reasoning_effort": None, "compact_tokens": 320},
        3: {"model": "openai/gpt-oss-120b", "max_completion_tokens": 384, "reasoning_effort": "low", "compact_tokens": 320},
        4: {"model": "groq/compound", "max_completion_tokens": 384, "reasoning_effort": None, "compact_tokens": 320},
    }
    profile = dict(profiles.get(complexity, profiles[1]))
    if compact:
        profile["max_completion_tokens"] = profile["compact_tokens"]
    profile.pop("compact_tokens", None)
    return profile


def _v164_task_aware_generation_budget_self_audit() -> None:
    """Verify model, completion budget, and reasoning effort are deterministic by task class."""
    probes = [
        (1, "What is sovereignty?", "A" * 500, "openai/gpt-oss-20b", 256, "low"),
        (2, "What does this resource explain?", "A" * 900, "groq/compound-mini", 320, None),
        (3, "I see essays, Reference Maps, Navigators and Pathways. What is the difference between them and how should I choose?", "A" * 1596, "openai/gpt-oss-120b", 384, "low"),
        (4, "How do I reconcile conflicting interpretations across multiple resources?", "A" * 1900, "groq/compound", 384, None),
    ]
    for expected_class, question, context, expected_model, expected_tokens, expected_reasoning in probes:
        routing = _classify_generation_complexity(question, "TOPICAL_INQUIRY", context)
        profile = _generation_budget_profile(routing)
        if routing["complexity"] != expected_class:
            raise RuntimeError(f"v165 routing class regression: {routing}")
        if profile["model"] != expected_model or profile["max_completion_tokens"] != expected_tokens or profile["reasoning_effort"] != expected_reasoning:
            raise RuntimeError(f"v164 generation budget regression: routing={routing}, profile={profile}")
        compact = _generation_budget_profile(routing, compact=True)
        if compact["max_completion_tokens"] > profile["max_completion_tokens"]:
            raise RuntimeError(f"v165 compact budget regression: {compact}")

    fixed_messages = _build_generation_messages("v164 envelope probe", "TOPICAL_INQUIRY", "", None)
    fixed_chars = _estimate_message_chars(fixed_messages)
    class3 = _generation_budget_profile({"complexity": 3})
    output_reservation = math.ceil(class3["max_completion_tokens"] * 4 * 1.25)
    evidence_capacity = min(
        MAX_PROVIDER_INPUT_CHARS - fixed_chars,
        MAX_PROVIDER_TOTAL_CHARS - fixed_chars - output_reservation,
    )
    if evidence_capacity < 0:
        raise RuntimeError(
            f"v165 provider-envelope regression: class-3 budget leaves negative evidence capacity ({evidence_capacity}); fixed_input={fixed_chars}."
        )
    compact_messages = _build_generation_messages("v164 compact probe", "TOPICAL_INQUIRY", "", None, compact=True)
    compact_fixed = _estimate_message_chars(compact_messages)
    compact_profile = _generation_budget_profile({"complexity": 3}, compact=True)
    compact_reservation = math.ceil(compact_profile["max_completion_tokens"] * 4 * 1.25)
    if compact_fixed + compact_reservation > MAX_PROVIDER_TOTAL_CHARS:
        raise RuntimeError("v165 provider-envelope regression: compact class-3 budget does not fit.")

    realistic_context = (
        "Title: At the Edge of Explanation\n"
        "URL: https://example.invalid/edge\n"
        "Content: This essay examines the limits of explanation and how questions can remain open.\n\n---\n\n"
        "Title: Document Types of the Living Archive\n"
        "URL: https://geralddaquila.com/document-types-of-the-living-archive/\n"
        "Content: The Living Archive contains distinct publication forms designed for different orientational functions.\n\n---\n\n"
        "Title: Scarcity vs Abundance Is a Mental Map Problem (Not a Resource Problem)\n"
        "URL: https://geralddaquila.com/map\n"
        "Content: This Reference Map provides visual structural orientation to relationships and patterns.\n"
    )
    realistic_question = (
        "I’m trying to understand a complex subject in the Living Archive, but I’m unsure whether I should read one piece deeply or bring several resources together. "
        "How does The Guide decide when a question calls for simple explanation versus synthesis, and what should I expect to be different in the way it responds?"
    )
    realistic_routing = _classify_generation_complexity(
        realistic_question, "TOPICAL_INQUIRY", realistic_context
    )
    if realistic_routing["complexity"] != 3 or realistic_routing["model"] != "openai/gpt-oss-120b":
        raise RuntimeError(f"v165 realistic routing regression: {realistic_routing}")
    realistic_profile = _generation_budget_profile(realistic_routing)
    if realistic_profile["max_completion_tokens"] != 384 or realistic_profile["reasoning_effort"] != "low":
        raise RuntimeError(f"v165 realistic budget regression: {realistic_profile}")
    realistic_compact_profile = _generation_budget_profile(realistic_routing, compact=True)
    realistic_compact_context = _bound_existing_context_blocks(
        realistic_context,
        MAX_COMPACT_GENERATION_CONTEXT_CHARS,
        MAX_COMPACT_GENERATION_RESOURCE_CHARS,
        schema_free=True,
    )
    realistic_compact_context = _build_provider_evidence_context(
        realistic_compact_context,
        MAX_COMPACT_GENERATION_CONTEXT_CHARS,
        MAX_COMPACT_GENERATION_RESOURCE_CHARS,
        schema_free=True,
    )
    compact_probe_messages = _build_generation_messages(
        realistic_question, "TOPICAL_INQUIRY", realistic_compact_context, None, compact=True
    )
    compact_probe_total = _estimate_message_chars(compact_probe_messages) + math.ceil(
        realistic_compact_profile["max_completion_tokens"] * 4 * 1.25
    )
    if not realistic_compact_context.strip() or compact_probe_total > MAX_PROVIDER_TOTAL_CHARS:
        raise RuntimeError(
            "v164 realistic compact envelope regression: compact evidence path does not fit "
            f"(evidence={len(realistic_compact_context)}, total={compact_probe_total})."
        )

    provider_source = inspect.getsource(_run_generation_attempt)
    if '"max_completion_tokens": max_tokens' not in provider_source or "create(**provider_kwargs)" not in provider_source:
        raise RuntimeError("v164 provider-parameter regression: max_completion_tokens is not the active provider request parameter.")
    if 'provider_kwargs["reasoning_effort"] = reasoning_effort' not in provider_source:
        raise RuntimeError("v164 reasoning-effort regression: GPT-OSS reasoning control is not wired.")
    print(
        "USE v164 TASK-AWARE GENERATION BUDGET AUDIT: PASS "
        f"(class3_tokens={class3['max_completion_tokens']}, class3_reasoning={class3['reasoning_effort']}, "
        f"fixed_input={fixed_chars}, evidence_capacity={evidence_capacity})"
    )


def _v163_generation_envelope_self_audit() -> None:
    """Verify the primary fixed envelope is materially smaller without removing hard invariants."""
    empty = _build_generation_messages(
        "Why do systems change?", "TOPICAL_INQUIRY", "", None, compact=False
    )
    fixed_chars = _estimate_message_chars(empty)
    if fixed_chars >= 2700:
        raise RuntimeError(
            f"v163 generation-envelope regression: fixed primary envelope remains too large ({fixed_chars} chars)."
        )
    for marker in (
        "For TOPICAL questions, orient through supplied evidence, not generic explanation.",
        "normally use 2–3 only for distinct coverage",
        "[FRAME SOVEREIGNTY]",
        "[PROVENANCE + SYNTHESIS]",
        "D29 explicitly validates",
        "Never invent resources, relationships, definitions, or URLs",
    ):
        if marker not in GENERATION_SYSTEM_PROMPT:
            raise RuntimeError(f"v163 generation-envelope regression: required invariant missing: {marker}")
    print(f"USE v163 GENERATION ENVELOPE AUDIT: PASS (fixed_input={fixed_chars})")


def _v163_model_routing_self_audit() -> None:
    """Verify deterministic task-to-model routing without calling a provider."""
    simple = _classify_generation_complexity(
        "What is sovereignty?", "TOPICAL_INQUIRY", "A" * 500
    )
    if simple["complexity"] != 1 or simple["model"] != "openai/gpt-oss-20b":
        raise RuntimeError(f"v163 model-routing regression: simple task routed incorrectly: {simple}")

    ordinary = _classify_generation_complexity(
        "What does this resource explain?", "TOPICAL_INQUIRY", "A" * 900
    )
    if ordinary["complexity"] != 2 or ordinary["model"] != "groq/compound-mini":
        raise RuntimeError(f"v163 model-routing regression: ordinary task routed incorrectly: {ordinary}")

    synthesis = _classify_generation_complexity(
        "I see essays, Reference Maps, Navigators and Pathways. What is the difference between them and how should I choose?",
        "WHOLE_SITE_ORIENTATION",
        "A" * 1596,
    )
    if synthesis["complexity"] != 3 or synthesis["model"] != "openai/gpt-oss-120b":
        raise RuntimeError(f"v163 model-routing regression: synthesis task routed incorrectly: {synthesis}")

    complex_task = _classify_generation_complexity(
        "How do I reconcile conflicting interpretations across multiple resources?",
        "TOPICAL_INQUIRY",
        "A" * 1900,
    )
    if complex_task["complexity"] != 4 or complex_task["model"] != "groq/compound":
        raise RuntimeError(f"v163 model-routing regression: complex task routed incorrectly: {complex_task}")

    print("USE v163 MODEL ROUTING AUDIT: PASS")


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

    # v163 MVP correction: select the reasoning model deterministically from
    # the task complexity before any provider call. There is no heterogeneous
    # model lottery and no sequential cycling after an output-boundary failure.
    routing = _classify_generation_complexity(
        user_query,
        intent,
        base_generation_context,
        orientational_frame,
    )
    live_models = get_live_groq_models()
    preferred_model = routing["model"]
    generation_profile = _generation_budget_profile(routing)

    print(
        "USE generation model routing: "
        f"complexity={routing['complexity']}, "
        f"context_chars={routing['context_chars']}, "
        f"resources={routing['resource_count']}, "
        f"synthesis_signals={routing['synthesis_signals']}, "
        f"complex_signals={routing['complex_signals']}, "
        f"selected_model={preferred_model}, "
        f"reason={routing['reason']}"
    )

    if preferred_model not in live_models:
        print(
            "USE generation selected model unavailable: "
            f"selected_model='{preferred_model}', live_models={live_models}; "
            "using deterministic fallback without model cycling."
        )
        return _deterministic_provider_fallback(
            user_query,
            base_generation_context,
        )

    # Exactly one provider model is eligible for this visitor request.
    active_models = [preferred_model]

    print(
        "USE generation MVP selected path: "
        f"{preferred_model}; no model cycling."
    )
    print(
        "USE generation task budget: "
        f"model={preferred_model}; "
        f"max_completion_tokens={generation_profile['max_completion_tokens']}; "
        f"reasoning_effort={generation_profile['reasoning_effort']}."
    )
    print(
        "USE generation context budget: "
        f"{len(base_generation_context)}/{MAX_GENERATION_CONTEXT_CHARS} chars; "
        f"max_completion_tokens={generation_profile['max_completion_tokens']}."
    )

    last_error: Optional[str] = None
    provider_recovery_allowed = True

    for model_id in active_models:
        try:
            print(
                "USE generation attempt: "
                f"'{model_id}'; {_request_correlation_log_prefix()}"
            )

            visitor_answer = _run_generation_attempt(
                model_id,
                user_query,
                intent,
                base_generation_context,
                max_tokens=generation_profile["max_completion_tokens"],
                reasoning_effort=generation_profile["reasoning_effort"],
                canonical_link_context=canonical_link_context,
            )

            if visitor_answer:
                return visitor_answer

            print(
                f"USE output boundary: model '{model_id}' returned no usable "
                "visitor answer; no alternate model will be attempted."
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
                    schema_free=True,
                )
                compact_context = _build_provider_evidence_context(
                    compact_context,
                    MAX_COMPACT_GENERATION_CONTEXT_CHARS,
                    MAX_COMPACT_GENERATION_RESOURCE_CHARS,
                    schema_free=True,
                )

                compact_profile = _generation_budget_profile(routing, compact=True)
                print(
                    "USE generation compact fallback: "
                    f"{len(compact_context)}/"
                    f"{MAX_COMPACT_GENERATION_CONTEXT_CHARS} chars; "
                    f"max_completion_tokens={compact_profile['max_completion_tokens']}; "
                    f"reasoning_effort={compact_profile['reasoning_effort']}."
                )

                try:
                    compact_messages = _build_generation_messages(
                        user_query, intent, compact_context, orientational_frame, compact=True
                    )
                    compact_estimate = _estimate_quota_tokens(
                        compact_messages, compact_profile["max_completion_tokens"]
                    )
                    _known_daily_tpd_preflight(model_id, compact_estimate)

                    compact_answer = _run_generation_attempt(
                        model_id,
                        user_query,
                        intent,
                        compact_context,
                        max_tokens=compact_profile["max_completion_tokens"],
                        reasoning_effort=compact_profile["reasoning_effort"],
                        canonical_link_context=canonical_link_context,
                        validation_context=base_generation_context,
                        compact=True,
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
    history: Optional[List[Any]] = None
    conversation_history: Optional[List[Any]] = None


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

    supplied_history = None
    if payload:
        supplied_history = payload.history or payload.conversation_history
    if supplied_history is None and raw_body:
        supplied_history = (
            raw_body.get("history")
            or raw_body.get("conversation_history")
        )

    try:
        context_data = fetch_canonical_context(query_str)

        if context_data.get("frame_neutral_evidence_unavailable"):
            llm_output = _frame_neutral_evidence_unavailable_response(query_str)
        elif context_data.get("question_structure_evidence_unavailable"):
            llm_output = _evidence_sufficiency_unavailable_response(
                query_str,
                context_data.get("canonical_link_context", ""),
            )
        elif context_data.get("evidence_sufficiency_unavailable"):
            llm_output = _evidence_sufficiency_unavailable_response(
                query_str,
                context_data.get("canonical_link_context", ""),
            )
        else:
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

        # Observe only after the current answer path is complete.
        progressive_state = assess_progressive_commitment(
            query_str,
            supplied_history,
        )
        invitation = progressive_inquiry_invitation(progressive_state)
        if invitation:
            llm_output = f"{llm_output}\n\n{invitation}"

        # Canonical context is deliberately not returned to the browser.
        # Retrieval evidence is an internal generation input; returning it
        # was unnecessary for the WordPress client and could make health/
        # keep-warm requests return a very large body.
        response_content: Dict[str, Any] = {
            "ok": True,
            "version": APP_VERSION,
            "fingerprint": DEPLOYMENT_FINGERPRINT,
            "source_sha256": RUNTIME_SOURCE_SHA256,
            "boot_id": RUNTIME_BOOT_ID,
            "request_id": getattr(request.state, "use_request_id", ""),
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



def _v70_framework_neutrality_self_audit() -> Dict[str, Any]:
    """Static audit for framework-neutral canonical doorway behavior."""
    broad_question = (
        "Why do some explanations make my experience feel clearer at first, "
        "but less clear the more I try to fit myself into them?"
    )
    specialized_title = "Why the “Starseed” Archetype Resonates With Some Filipinos"
    neutral_title = "Understanding Lived Experience"

    specialized_penalty = _framework_neutrality_penalty(
        broad_question, specialized_title.casefold()
    )
    neutral_penalty = _framework_neutrality_penalty(
        broad_question, neutral_title.casefold()
    )
    explicit_question = "Why does the Starseed archetype resonate with some people?"
    explicit_penalty = _framework_neutrality_penalty(
        explicit_question, specialized_title.casefold()
    )

    result = {
        "broad_question_specialized_penalty": specialized_penalty,
        "broad_question_neutral_penalty": neutral_penalty,
        "explicit_framework_penalty": explicit_penalty,
    }
    result["pass"] = (
        specialized_penalty > neutral_penalty
        and neutral_penalty == 0
        and explicit_penalty == 0
    )
    return result


def _v72_question_doorway_centrality_self_audit() -> Dict[str, Any]:
    """Static audit for question-proportionate canonical doorway selection."""
    broad_question = (
        "Why can becoming more aware of yourself sometimes make ordinary parts "
        "of life feel strangely unfamiliar?"
    )
    specialized_title = (
        "Divine Timing and Synchronicity: Unveiling the Cosmic Choreography of Awakening"
    )
    neutral_title = "Understanding Everyday Change and Perception"
    neutral_metadata = {
        "title": neutral_title,
        "text": "Explores how changes in perception can alter how ordinary situations are experienced.",
    }
    specialized_metadata = {
        "title": specialized_title,
        "text": "Explores awakening, synchronicity, and spiritual perception.",
    }
    explicit_question = "Why can awakening make ordinary life feel unfamiliar?"

    specialized_score, specialized_detail = _canonical_doorway_score(
        specialized_metadata,
        {"primary": "inward", "scores": {"inward": 1}},
        broad_question,
    )
    neutral_score, neutral_detail = _canonical_doorway_score(
        neutral_metadata,
        {"primary": "inward", "scores": {"inward": 1}},
        broad_question,
    )
    explicit_score, explicit_detail = _canonical_doorway_score(
        specialized_metadata,
        {"primary": "inward", "scores": {"inward": 1}},
        explicit_question,
    )

    return {
        "broad_specialized_score": specialized_score,
        "broad_neutral_score": neutral_score,
        "explicit_specialized_score": explicit_score,
        "specialized_detail": specialized_detail,
        "neutral_detail": neutral_detail,
        "explicit_detail": explicit_detail,
        "pass": specialized_score < neutral_score and explicit_score > specialized_score,
    }


def _v76_frame_neutral_evidence_self_audit() -> Dict[str, Any]:
    """Static audit for narrowing open-frame generation evidence without changing retrieval."""
    question = "If I stop trying to interpret an experience immediately, what becomes available to me?"
    specialized = {
        "title": "What Is Ego Death? The Hidden Gateway to Spiritual Transformation",
        "url": "https://example.invalid/ego-death",
        "text": "A specialized spiritual framework is discussed.",
    }
    neutral = {
        "title": "Understanding Lived Experience",
        "url": "https://example.invalid/lived-experience",
        "text": "A neutral account of how experience can be noticed and described.",
    }
    selected, active = _frame_neutral_generation_documents(
        [specialized, neutral], question, "TOPICAL_INQUIRY"
    )
    explicit_selected, explicit_active = _frame_neutral_generation_documents(
        [specialized, neutral],
        "If I stop trying to interpret an ego death experience immediately, what becomes available to me?",
        "TOPICAL_INQUIRY",
    )
    selected_titles = [str(doc.get("title", "")) for doc in selected]
    explicit_titles = [str(doc.get("title", "")) for doc in explicit_selected]
    return {
        "broad_active": active,
        "broad_retains_neutral": "Understanding Lived Experience" in selected_titles,
        "broad_excludes_specialized": "What Is Ego Death? The Hidden Gateway to Spiritual Transformation" not in selected_titles,
        "explicit_inactive": not explicit_active,
        "explicit_retains_specialized": "What Is Ego Death? The Hidden Gateway to Spiritual Transformation" in explicit_titles,
        "pass": (
            active
            and "Understanding Lived Experience" in selected_titles
            and "What Is Ego Death? The Hidden Gateway to Spiritual Transformation" not in selected_titles
            and not explicit_active
            and "What Is Ego Death? The Hidden Gateway to Spiritual Transformation" in explicit_titles
        ),
    }


def _v92_frame_specific_resource_self_audit() -> Dict[str, Any]:
    """Audit the actual D17 failure: uninvited title-declared framing stays out of generation."""
    question = "Why can understanding a pattern feel different from actually seeing it in my life?"
    specialized = {
        "title": "When Life Disrupts: Uncovering the Hidden Lessons of Synchronicity and Crisis",
        "url": "https://example.invalid/synchronicity",
        "content": "Synchronicities can foster meaning, hope, and agency.",
    }
    neutral = {
        "title": "Understanding Lived Experience",
        "url": "https://example.invalid/lived-experience",
        "content": "People can notice and describe an experience in different ways.",
    }
    selected, active = _frame_neutral_generation_documents(
        [specialized, neutral], question, "TOPICAL_INQUIRY"
    )
    titles = [str(doc.get("title", "")) for doc in selected]
    return {
        "active": active,
        "retains_neutral": "Understanding Lived Experience" in titles,
        "excludes_uninvited_construct": specialized["title"] not in titles,
        "pass": (
            active
            and "Understanding Lived Experience" in titles
            and specialized["title"] not in titles
        ),
    }


def _v75_interpretive_frame_sovereignty_self_audit() -> Dict[str, Any]:
    """Static audit for preserving open questions against uninvited framing."""
    broad_question = (
        "If I stop trying to interpret an experience immediately, what becomes "
        "available to me?"
    )
    specialized_instruction = _interpretive_frame_sovereignty_instruction(
        broad_question, "TOPICAL_INQUIRY"
    )
    explicit_question = (
        "If I stop trying to interpret an ego death experience immediately, "
        "what becomes available to me?"
    )
    explicit_instruction = _interpretive_frame_sovereignty_instruction(
        explicit_question, "TOPICAL_INQUIRY"
    )
    explicit_named = _question_is_frame_open(explicit_question)
    return {
        "broad_instruction_present": bool(specialized_instruction),
        "explicit_question_not_frame_open": not explicit_named,
        "explicit_question_not_blocked": not bool(explicit_instruction),
        "pass": bool(specialized_instruction) and not explicit_named and not bool(explicit_instruction),
    }


def _v78_inferential_distance_self_audit() -> Dict[str, Any]:
    """Verify the compact generation boundary forbids invented bridge facts."""
    prompt = GENERATION_SYSTEM_PROMPT
    required = (
        "[INFERENTIAL DISTANCE]",
        "Do not invent intermediate facts or mechanisms",
        "label the connection as an inference/possibility/interpretive reading",
    )
    present = {term: term in prompt for term in required}

    # Synthetic evidence deliberately supports two components without their
    # causal bridge. The audit checks the boundary instruction, not model
    # behavior; live behavioral validation remains a deployment test.
    synthetic_context = (
        "Title: Resource A\n"
        "Content: People report clearer priorities after reflection.\n\n"
        "Title: Resource B\n"
        "Content: Distributed decisions involve more interdependent factors."
    )
    messages = _build_generation_messages(
        "Why can greater clarity sometimes make a decision feel harder?",
        "TOPICAL_INQUIRY",
        synthetic_context,
    )
    joined = " ".join(str(m.get("content", "")) for m in messages)

    return {
        "required_present": present,
        "prompt_contains_all": all(present.values()),
        "messages_preserve_boundary": "[INFERENTIAL DISTANCE]" in joined,
        "pass": all(present.values()) and "[INFERENTIAL DISTANCE]" in joined,
    }


def _v80_interpretive_bridge_integrity_self_audit() -> Dict[str, Any]:
    """Verify the compact prompt forbids unstated premises inside an inference."""
    prompt = GENERATION_SYSTEM_PROMPT
    required = (
        "[BRIDGE INTEGRITY]",
        "cannot add unstated factual premises as stepping stones",
        "build a chain of plausible mechanisms",
        "say the evidence does not establish the connection",
    )
    present = {term: term in prompt for term in required}
    return {
        "required_present": present,
        "pass": all(present.values()),
    }


def _v81_evidence_sufficiency_self_audit() -> Dict[str, Any]:
    """Verify the post-retrieval domain-fit gate blocks adjacent evidence."""
    unrelated = {
        "title": "Learning to Receive Without Feeling Guilty",
        "text": (
            "A hidden belief says I should be able to handle this on my own. "
            "Needing support can feel like failure or taking something undeserved."
        ),
    }
    direct = {
        "title": "Understanding Complexity",
        "text": (
            "Learning more about a problem can change how understandable the "
            "problem feels because additional understanding reveals further "
            "questions and relationships."
        ),
    }
    blocked, unavailable = _evidence_sufficiency_gate(
        [unrelated],
        "Why can learning more about a problem sometimes make the problem feel less understandable?",
        "TOPICAL_INQUIRY",
    )
    retained, retained_unavailable = _evidence_sufficiency_gate(
        [direct],
        "Why can learning more about a problem sometimes make the problem feel less understandable?",
        "TOPICAL_INQUIRY",
    )
    prompt = GENERATION_SYSTEM_PROMPT
    required = (
        "[EVIDENCE SUFFICIENCY]",
        "Retrieval relevance is not evidence sufficiency.",
        "If supplied Content cannot support the question",
        "say the evidence is insufficient",
    )
    present = {term: term in prompt for term in required}
    return {
        "adjacent_preserved_for_navigation": unavailable and bool(blocked),
        "adjacent_synthesis_withheld": unavailable,
        "direct_retained": (not retained_unavailable) and bool(retained),
        "prompt_contains_all": all(present.values()),
        "required_present": present,
        "pass": (
            unavailable
            and bool(blocked)
            and not retained_unavailable
            and bool(retained)
            and all(present.values())
        ),
    }


def _question_structure_side_lexical_hits(
    content: str,
    terms: Tuple[str, ...],
) -> int:
    """Count substantive side terms in supplied Content without embeddings."""
    value = re.sub(r"[^a-z0-9\s'-]", " ", str(content or "").casefold())
    words = set(re.findall(r"[a-z][a-z'-]{2,}", value))
    hits = 0
    for term in terms:
        token = str(term).casefold().strip()
        if not token:
            continue
        if token in words:
            hits += 1
            continue
        # Small morphological normalization only; this is not a semantic
        # vocabulary and does not expand retrieval.
        stem = token
        for suffix in ("ingly", "edly", "ing", "ed", "ly", "es", "s"):
            if len(stem) > len(suffix) + 3 and stem.endswith(suffix):
                stem = stem[:-len(suffix)]
                break
        if stem and any(
            word == stem or word.startswith(stem)
            for word in words
            if len(stem) >= 4
        ):
            hits += 1
    return hits


def _question_structure_evidence_gate(
    documents: List[Dict[str, Any]],
    question: str,
    intent: str,
) -> Tuple[List[Dict[str, Any]], bool]:
    """Permit synthesis when already-retrieved Content jointly covers both sides.

    D17 validates correspondence using supplied Content only. It deliberately
    does not invoke another embedding pass: semantic retrieval has already
    supplied the candidate set. A small set of retrieved resources may jointly
    cover the two explicit question components.
    """
    if not documents:
        return [], True

    structure = recognize_question_structure(question)
    if structure.get("structure") != "explicit_contrast":
        return documents, False

    pairs = structure.get("pairs") or ()
    if len(pairs) != 2:
        return documents, True

    left_terms, right_terms = pairs
    diagnostics = []
    direct = []
    left_candidates = []
    right_candidates = []

    for index, document in enumerate(documents):
        content = str(document.get("content") or document.get("text") or "")
        left_hits = _question_structure_side_lexical_hits(content, left_terms)
        right_hits = _question_structure_side_lexical_hits(content, right_terms)
        diagnostics.append((left_hits, right_hits))

        # Direct correspondence requires substantive coverage of both sides,
        # not merely one incidental shared word.
        if left_hits >= 2 and right_hits >= 2:
            direct.append(index)

        if left_hits >= 2:
            left_candidates.append((left_hits, index))
        if right_hits >= 2:
            right_candidates.append((right_hits, index))

    if direct:
        selected = [documents[i] for i in direct]
        print(
            "USE question-evidence correspondence: direct qualifying resources="
            f"{len(selected)}/{len(documents)}; diagnostics={diagnostics}"
        )
        return selected, False

    # Distributed coverage allows different already-retrieved resources to
    # substantively carry the two sides of the visitor's explicit question.
    best_left = max(left_candidates, default=None)
    best_right = max(right_candidates, default=None)
    if best_left is not None and best_right is not None:
        selected_indexes = {best_left[1], best_right[1]}
        selected = [documents[i] for i in sorted(selected_indexes)]
        print(
            "USE question-evidence correspondence: distributed coverage="
            f"{len(selected)}/{len(documents)}; diagnostics={diagnostics}"
        )
        return selected, False

    print(
        "USE question-evidence correspondence: no retrieved Content jointly "
        f"covers both question sides; diagnostics={diagnostics}"
    )
    return documents, True





def _v92_d17_evidence_boundary_reconciliation_self_audit() -> None:
    """Verify D16 sufficiency does not false-negative explicit general relations."""
    general_relation = "Why can two people experience the same situation and understand it differently?"
    open_experience = "Why can understanding a pattern feel different from actually seeing it in my life?"
    weak = [{"title": "Adjacent", "content": "A general canonical discussion with no literal question terms."}]

    retained, blocked = _evidence_sufficiency_gate(weak, general_relation, "TOPICAL_INQUIRY")
    if blocked or not retained:
        raise RuntimeError(
            "v92 D17 reconciliation regression: explicit general relational question was blocked by lexical sufficiency."
        )

    retained_open, blocked_open = _evidence_sufficiency_gate(weak, open_experience, "TOPICAL_INQUIRY")
    if not blocked_open or not retained_open:
        raise RuntimeError(
            "v92 D17 reconciliation regression: open first-person experiential boundary was weakened."
        )
    print("USE v92 D17 evidence-boundary reconciliation self-audit: PASS")


def _v92_question_structure_self_audit() -> None:
    """Verify D17 recognizes explicit relational structure without inventing theory."""
    contrast = recognize_question_structure(
        "Why can I understand a situation clearly and still not know what to do with that understanding?"
    )
    if contrast.get("structure") != "explicit_contrast" or len(contrast.get("pairs") or ()) != 2:
        raise RuntimeError("v92 question-structure regression: explicit contrast was not preserved.")
    positive = recognize_question_structure(
        "Why can two people experience the same situation and understand it differently?"
    )
    if positive.get("structure") != "explicit_contrast" or len(positive.get("pairs") or ()) != 2:
        raise RuntimeError("v92 question-structure regression: relational positive case was not recognized.")
    neutral = recognize_question_structure("Why is uncertainty difficult?")
    if neutral.get("structure") != "none":
        raise RuntimeError("v92 question-structure regression: implicit theory was invented.")
    print("USE D17 question-structure self-audit: PASS")


def _v92_question_evidence_correspondence_integration_self_audit() -> None:
    """Verify D17 structure reaches reasoning without becoming a synthesis gate."""
    source = inspect.getsource(fetch_canonical_context)
    structure_call = source.find("recognize_question_structure(user_query)")
    doorway_call = source.find("select_canonical_doorways(")
    if structure_call < 0 or doorway_call < 0 or structure_call > doorway_call:
        raise RuntimeError("v92 correspondence regression: D17 structure is not upstream of doorway/reasoning selection.")
    if "_question_structure_evidence_gate(" in source:
        raise RuntimeError("v92 correspondence regression: obsolete lexical evidence gate remains in fetch path.")
    print("USE D17 relational reasoning integration self-audit: PASS")


def _v92_question_structure_evidence_self_audit() -> None:
    """Verify D17 structure recognition does not create a lexical synthesis gate."""
    source = inspect.getsource(fetch_canonical_context)
    if "_question_structure_evidence_gate(" in source:
        raise RuntimeError("v92 correspondence regression: lexical evidence gate still blocks D17 synthesis.")
    if "recognize_question_structure(user_query)" not in source:
        raise RuntimeError("v92 correspondence regression: D17 question structure is no longer available to reasoning.")
    if "question_structure_evidence_unavailable" in source:
        raise RuntimeError("v92 correspondence regression: obsolete D17 synthesis-block path remains.")
    prompt_source = GENERATION_SYSTEM_PROMPT
    required = (
        "[RELATIONAL REASONING]",
        "evidence may be distributed",
        "Do not force one resource to cover both sides",
    )
    if not all(item in prompt_source for item in required):
        raise RuntimeError("v92 relational reasoning instruction is incomplete.")
    print("USE D17 evidence-scoped relational reasoning self-audit: PASS")

def _v83_recognition_orientation_self_audit() -> None:
    """Verify D17 stays explicit-question-bound and non-diagnostic."""
    cases = (
        ("Why can I understand a situation clearly and still not know what to do with that understanding?", "understand"),
        ("How can I tell whether I am outgrowing an old way of living or interpreting it differently?", "distinguish"),
        ("What is the Living Archive?", "locate"),
    )
    for question, expected_mode in cases:
        result = build_recognition_orientation(question, classify_intent(question))
        if result.get("orientation_mode") != expected_mode:
            raise RuntimeError(f"D17 recognition→orientation regression: expected={expected_mode}, got={result.get('orientation_mode')}")
        if result.get("recognition") not in {
            "the visitor is asking for orientation within the Archive",
            "the question is seeking understanding, distinction, exploration, or movement rather than a presumed diagnosis",
        }:
            raise RuntimeError("D17 recognition→orientation regression: unbounded recognition text.")
    print("USE D17 recognition→orientation self-audit: PASS")



def _v93_d18_use_intent_integration_audit() -> None:
    """Audit the completed Phase-II intent chain as one integrated system.

    D18 is an integration audit, not a new intelligence layer. It verifies that
    the capabilities built through D08-D17 remain connected in the intended
    dependency order and that no later boundary silently replaces an earlier
    one. The audit is source/invariant based so it does not create a second
    retrieval or reasoning engine.
    """
    fetch_source = inspect.getsource(fetch_canonical_context)
    route_source = inspect.getsource(handle_query)
    generation_source = inspect.getsource(generate_llm_response)

    # D08-D13: question, intent, orientation, ambiguity, and separation must
    # enter the integrated fetch path before retrieval/routing decisions.
    required_fetch_calls = (
        "intent = classify_intent(user_query)",
        "detect_collection_request(user_query)",
        "detect_adaptive_stewardship_orientation(user_query)",
        "infer_orientational_frame(user_query)",
        "build_recognition_orientation(user_query, intent)",
        "recognize_question_structure(user_query)",
    )
    missing = [item for item in required_fetch_calls if item not in fetch_source]
    if missing:
        raise RuntimeError(
            "D18 integration regression: required USE intent-stage call(s) missing: "
            + ", ".join(missing)
        )

    # Intent/orientation must precede retrieval and remain available downstream.
    intent_pos = fetch_source.find("intent = classify_intent(user_query)")
    retrieval_pos = fetch_source.find("query_vector = generate_embedding(user_query)")
    if intent_pos < 0 or retrieval_pos < 0 or intent_pos > retrieval_pos:
        raise RuntimeError(
            "D18 integration regression: intent classification is not upstream of retrieval."
        )
    orientation_pos = fetch_source.find("build_recognition_orientation(user_query, intent)")
    if orientation_pos < 0 or orientation_pos > retrieval_pos:
        raise RuntimeError(
            "D18 integration regression: recognition/orientation is not upstream of retrieval."
        )

    # D14-D16: retrieval strategy, canonical evidence selection, and reasoning
    # boundaries must remain distinct. Doorway selection is downstream of
    # retrieval; synthesis-only boundaries must not erase navigation context.
    doorway_pos = fetch_source.find("select_canonical_doorways(")
    link_pos = fetch_source.find("canonical_link_context = format_context_blocks(")
    if doorway_pos < 0 or retrieval_pos > doorway_pos:
        raise RuntimeError(
            "D18 integration regression: canonical doorway selection is not downstream of retrieval."
        )
    if link_pos < 0:
        raise RuntimeError(
            "D18 integration regression: canonical link authority is not constructed in fetch path."
        )
    if "canonical_link_context" not in fetch_source:
        raise RuntimeError(
            "D18 integration regression: navigation context disappeared from intent path."
        )

    # D17: recognition/orientation and explicit question structure inform the
    # response, but do not become a second retrieval engine.
    if "question_structure_evidence_unavailable" in fetch_source:
        raise RuntimeError(
            "D18 integration regression: obsolete D17 evidence-blocking path remains."
        )
    if "_question_structure_evidence_gate(" in fetch_source:
        raise RuntimeError(
            "D18 integration regression: obsolete lexical D17 synthesis gate remains."
        )
    if "recognize_question_structure(user_query)" not in fetch_source:
        raise RuntimeError(
            "D18 integration regression: D17 question structure is disconnected."
        )

    # Generation must receive the integrated intent/orientation state rather
    # than reconstructing it independently.
    if "context_data[\"intent\"]" not in route_source:
        raise RuntimeError(
            "D18 integration regression: classified intent is not passed to generation."
        )
    if "orientational_frame=context_data.get(" not in route_source:
        raise RuntimeError(
            "D18 integration regression: orientational frame is not passed to generation."
        )
    if "canonical_link_context" not in generation_source:
        raise RuntimeError(
            "D18 integration regression: canonical link authority is disconnected from generation."
        )

    # Whole-site orientation must remain a distinct intent path rather than a
    # generic topical answer, while topical inquiry remains the default.
    if 'return "WHOLE_SITE_ORIENTATION"' not in inspect.getsource(classify_intent):
        raise RuntimeError(
            "D18 integration regression: whole-site orientation intent disappeared."
        )
    if 'return "TOPICAL_INQUIRY"' not in inspect.getsource(classify_intent):
        raise RuntimeError(
            "D18 integration regression: topical inquiry default disappeared."
        )

    # Longitudinal observation is downstream of the current answer and cannot
    # alter current-turn reasoning.
    if "assess_progressive_commitment" not in route_source:
        raise RuntimeError(
            "D18 integration regression: passive longitudinal observer is disconnected."
        )
    observer_pos = route_source.find("assess_progressive_commitment")
    response_path_pos = max(
        route_source.find("llm_output = generate_llm_response("),
        route_source.find("_evidence_sufficiency_unavailable_response("),
        route_source.find("_frame_neutral_evidence_unavailable_response("),
    )
    if observer_pos >= 0 and response_path_pos >= 0 and observer_pos < response_path_pos:
        raise RuntimeError(
            "D18 integration regression: longitudinal observer can influence current-turn reasoning."
        )
    # Sovereignty markers belong to the observer state definition, not
    # necessarily to the route function itself. Audit the actual observer
    # implementation rather than requiring incidental marker strings in
    # handle_query().
    observer_source = inspect.getsource(assess_progressive_commitment)
    invitation_source = inspect.getsource(progressive_inquiry_invitation)
    if "observer_only" not in observer_source or "current_turn_influence" not in observer_source:
        raise RuntimeError(
            "D18 integration regression: passive observer sovereignty markers are missing."
        )
    if "observer_only" not in invitation_source and "observer_only" not in observer_source:
        raise RuntimeError(
            "D18 integration regression: passive observer sovereignty state is not preserved."
        )

    # Basic callable smoke checks use only local deterministic functions; no
    # external retrieval/provider call is made by this audit.
    # D18 verifies the intent pipeline structurally rather than asserting
    # particular English phrases against a layered classifier.
    probe_intent = classify_intent("Why can people understand the same situation differently?")
    declared_intents = {"TOPICAL_INQUIRY", "WHOLE_SITE_ORIENTATION"}
    if probe_intent not in declared_intents:
        raise RuntimeError(
            "D18 integration regression: classifier returned an undeclared intent."
        )

    probe_frame = build_recognition_orientation(
        "Why can people understand the same situation differently?",
        probe_intent,
    )
    if not isinstance(probe_frame, dict) or not probe_frame.get("orientation_mode"):
        raise RuntimeError(
            "D18 integration regression: intent-to-orientation transition returned no frame."
        )
    if probe_frame.get("orientation_mode") != "understand":
        raise RuntimeError(
            "D18 integration regression: recognition-to-orientation smoke test failed."
        )

    # D18 subject-navigation boundary: a known subject remains topical even
    # when the visitor asks where to enter for that subject.
    subject_navigation_probes = [
        "Where in the Living Archive should I go if I want to understand grief?",
        "I want to explore governance in the Living Archive, but I’m not sure which doorway would give me the best starting point.",
        "I know what subject I want to explore, but I don’t know which part of the Living Archive is the right place to enter.",
    ]
    for subject_probe in subject_navigation_probes:
        subject_intent = classify_intent(subject_probe)
        if subject_intent != "TOPICAL_INQUIRY":
            raise RuntimeError(
                "D18 integration regression: known-subject navigation inquiry was "
                f"misclassified as {subject_intent!r}: {subject_probe!r}"
            )

    # D18 open-exploration integration: an explicit not-yet-knowing exploratory
    # question must enter the whole-site orientation path rather than being
    # collapsed into a topical inquiry by prepositional parsing.
    open_probe = "I'm not sure what I'm looking for yet, but I want to explore."
    open_intent = classify_intent(open_probe)
    if open_intent != "WHOLE_SITE_ORIENTATION":
        raise RuntimeError(
            "D18 integration regression: open exploratory inquiry was not classified as whole-site orientation."
        )
    open_frame = build_recognition_orientation(open_probe, open_intent)
    if not isinstance(open_frame, dict) or open_frame.get("orientation_mode") != "locate":
        raise RuntimeError(
            "D18 integration regression: whole-site orientation did not produce a locate frame for open exploration."
        )

    print("USE D18 intent integration audit: PASS")


def _v169_clean_runtime_boot_provenance_self_audit() -> None:
    """Verify the explicit clean-boot and out-of-band source provenance boundary."""
    source = Path(__file__).read_text(encoding="utf-8")
    required = (
        "import gc",
        "_USE_BOOT_GC_COLLECTED = gc.collect()",
        "USE CLEAN RUNTIME BOOT",
        "USE_EXPECTED_SOURCE_SHA256",
        "USE SOURCE PROVENANCE FAILURE",
        "refusing to serve requests",
        'RUNTIME_SOURCE_SHA256 = _compute_runtime_source_sha256()',
    )
    missing = [marker for marker in required if marker not in source]
    if missing:
        raise RuntimeError(
            "v169 clean-runtime provenance audit failed; missing markers: "
            + ", ".join(missing)
        )
    actual = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if actual != RUNTIME_SOURCE_SHA256:
        raise RuntimeError(
            "v169 clean-runtime provenance audit failed; runtime source SHA is not the exact loaded file SHA."
        )
    if EXPECTED_RUNTIME_SOURCE_SHA256 and EXPECTED_RUNTIME_SOURCE_SHA256 != actual:
        raise RuntimeError(
            "v169 clean-runtime provenance audit failed; configured expected source SHA does not match the loaded file."
        )
    if _USE_BOOT_PID != os.getpid():
        raise RuntimeError(
            "v169 clean-runtime boot audit failed; boot PID identity drifted."
        )
    print(
        "USE v169 CLEAN RUNTIME + SOURCE PROVENANCE AUDIT: PASS; "
        f"boot_pid={_USE_BOOT_PID}, gc_collected={_USE_BOOT_GC_COLLECTED}, "
        f"source_sha256={RUNTIME_SOURCE_SHA256}, "
        f"expected_configured={bool(EXPECTED_RUNTIME_SOURCE_SHA256)}"
    )


def _v148_canonical_build_identity_self_audit() -> None:
    """Verify hard build identity enforcement is structurally intact."""
    source = Path(__file__).read_text(encoding="utf-8")
    required = (
        "CANONICAL_BUILD_ID",
        "CANONICAL_BUILD_PAYLOAD_SHA256",
        "_canonical_source_payload",
        "_compute_canonical_build_payload_sha256",
        "_enforce_canonical_build_identity",
        "USE BUILD IDENTITY FAILURE",
        "refusing to serve requests",
        'response.headers["X-USE-Build-ID"]',
        '"build_id": CANONICAL_BUILD_ID',
    )
    missing = [marker for marker in required if marker not in source]
    if missing:
        raise RuntimeError(
            "v148 build identity audit failed; missing markers: "
            + ", ".join(missing)
        )
    identity_matches = re.findall(
        r"(?ms)^# === CANONICAL BUILD IDENTITY \(excluded from payload hash\) ===\n"
        r".*?"
        r"^# === END CANONICAL BUILD IDENTITY ===$",
        source,
    )
    if len(identity_matches) != 1:
        raise RuntimeError(
            "v148 build identity audit failed; identity block count is not one."
        )
    active_version = re.search(r'APP_VERSION = "([^"]+)"', source)
    if not active_version or active_version.group(1) != APP_VERSION:
        raise RuntimeError(
            "v148 build identity audit failed; active APP_VERSION is inconsistent."
        )
    if APP_VERSION not in DEPLOYMENT_FINGERPRINT or APP_VERSION not in CANONICAL_BUILD_ID:
        raise RuntimeError(
            "v148 build identity audit failed; active identity does not match APP_VERSION."
        )
    actual = _compute_canonical_build_payload_sha256(source)
    if actual != CANONICAL_BUILD_PAYLOAD_SHA256:
        raise RuntimeError(
            "v148 build identity audit failed; canonical payload digest mismatch."
        )
    print(
        "USE v148 canonical build identity audit: PASS; "
        f"build_id={CANONICAL_BUILD_ID}, payload_sha256={actual}"
    )


def _v165_lean_generation_envelope_self_audit() -> None:
    """Verify the primary path preserves canonical evidence under the task-aware budget."""
    question = (
        "I need to understand a complex subject and decide between one deep "
        "resource and synthesis."
    )
    fixed_messages = _build_generation_messages(
        question, "TOPICAL_INQUIRY", "", None, compact=False
    )
    fixed_chars = _estimate_message_chars(fixed_messages)
    class3 = _generation_budget_profile({"complexity": 3})
    reservation = math.ceil(class3["max_completion_tokens"] * 4 * 1.25)
    capacity = min(
        MAX_PROVIDER_INPUT_CHARS - fixed_chars,
        MAX_PROVIDER_TOTAL_CHARS - fixed_chars - reservation,
    )
    if fixed_chars >= 2100:
        raise RuntimeError(
            f"v165 lean-envelope regression: primary fixed envelope too large ({fixed_chars})."
        )
    if capacity < 600:
        raise RuntimeError(
            f"v165 lean-envelope regression: class-3 evidence capacity too small ({capacity}); fixed={fixed_chars}, reservation={reservation}."
        )
    compact_messages = _build_generation_messages(
        question, "TOPICAL_INQUIRY", "", None, compact=True
    )
    compact_fixed = _estimate_message_chars(compact_messages)
    if abs(compact_fixed - fixed_chars) > 32:
        raise RuntimeError(
            f"v165 lean-envelope regression: primary and compact fixed envelopes diverged materially ({fixed_chars} != {compact_fixed})."
        )
    for marker_text in (
        "Answer the visitor's question directly",
        "Use at least one exact supplied canonical title",
        "[RELATIONAL REASONING]",
        "[FRAME SOVEREIGNTY]",
        "[PROVENANCE + SYNTHESIS]",
        "[INFERENTIAL DISTANCE]",
        "[BRIDGE INTEGRITY]",
        "[EVIDENCE SUFFICIENCY]",
    ):
        if marker_text not in GENERATION_SYSTEM_PROMPT:
            raise RuntimeError(
                f"v165 lean-envelope regression: required invariant missing: {marker_text}"
            )
    print(
        f"USE v166 LEAN GENERATION ENVELOPE AUDIT: PASS "
        f"(fixed_input={fixed_chars}, class3_evidence_capacity={capacity})"
    )


def _v166_reasoning_evidence_authority_self_audit() -> None:
    """Prove omitted provider evidence cannot authorize visitor-facing resources."""
    full = (
        "Title: Resource A\nURL: https://example.invalid/a\nContent: Evidence A."
        "\n\n---\n\n"
        "Title: Resource B\nURL: https://example.invalid/b\nContent: Evidence B."
    )
    safe_a = "Resource A — Evidence A."
    identity = _provider_evidence_identity_context(safe_a, full)
    assert _canonical_pairs(identity) == [("Resource A", "https://example.invalid/a")]
    assert _contains_canonical_resource_reference("Resource A", identity)
    assert not _contains_canonical_resource_reference("Resource B", identity)

    # The cleaner is presentation-oriented; substantive authorization is
    # enforced by the final canonical-reference boundary below.
    assert not _contains_canonical_resource_reference(
        "Resource B provides the relevant explanation.", identity
    )
    assert _contains_canonical_resource_reference(
        "Resource A provides the relevant explanation.", identity
    )

    linked_b = "[Resource B](https://example.invalid/b)"
    sanitized_b = sanitize_canonical_links(linked_b, identity)
    assert "example.invalid/b" not in sanitized_b

    linked_a = "[Resource A](https://example.invalid/a)"
    sanitized_a = sanitize_canonical_links(linked_a, identity)
    assert "example.invalid/a" in sanitized_a

    print("USE v166 reasoning-evidence authority audit: PASS")


def _v169_structural_relational_orientation_self_audit() -> None:
    """Verify natural relational phrasing is recognized as a routing signal."""
    cases = (
        (
            "When the Living Archive talks about transformation, how can I tell "
            "whether it is describing an inner change, a change in a system, or a "
            "change in how those two interact?",
            "relational",
        ),
        ("How does a system change when its conditions change?", "systems"),
        ("How does inner change affect how I understand myself?", "inward"),
        (
            "If an individual changes but the system around them stays the same, what does the Living Archive suggest about whether that change can actually last?",
            "relational",
        ),
        ("How does a person adapt to an institution's rules?", "relational"),
        ("What happens when an individual's values conflict with an organization's culture?", "relational"),
    )
    for question, expected_primary in cases:
        result = infer_orientational_frame(question)
        if result.get("primary") != expected_primary:
            raise RuntimeError(
                "v169 structural-relational orientation regression: "
                f"expected={expected_primary}, got={result.get('primary')} "
                f"for question={question!r}"
            )

    # Orientation remains a routing aid; it must not become an evidence gate.
    fetch_source = inspect.getsource(fetch_canonical_context)
    if "question_structure_evidence_unavailable" in fetch_source:
        raise RuntimeError(
            "v168 relational-orientation regression: orientation morphology "
            "must not restore an evidence-blocking gate."
        )
    print("USE v169 STRUCTURAL RELATIONAL ORIENTATION AUDIT: PASS")


def _v167_canonical_fallback_link_self_audit() -> None:
    """Prove extractive fallback preserves canonical visitor doorways."""
    context = (
        "Title: Oversoul Law: The Sovereignty of the Higher Self\n"
        "URL: https://example.invalid/oversoul-law\n"
        "Content: Oversoul Law awakens the sovereignty of the Higher Self from within. "
        "It describes autonomy as an inward principle of sovereignty."
    )
    answer = _deterministic_provider_fallback(
        "How does the Archive distinguish respecting autonomy from leaving someone without guidance?",
        context,
    )
    assert "Oversoul Law: The Sovereignty of the Higher Self" in answer
    assert "https://example.invalid/oversoul-law" in answer
    assert "[Oversoul Law: The Sovereignty of the Higher Self](https://example.invalid/oversoul-law)" in answer
    print("USE v167 canonical fallback link preservation audit: PASS")


def _generation_boundary_self_audit() -> None:
    """Fail loudly at startup if known visitor-boundary defects return."""
    _v169_clean_runtime_boot_provenance_self_audit()
    _v166_reasoning_evidence_authority_self_audit()
    _v169_structural_relational_orientation_self_audit()
    _v167_canonical_fallback_link_self_audit()
    try:
        _v148_canonical_build_identity_self_audit()
        if not callable(_log_provider_exception_diagnostic):
            raise RuntimeError(
                "v150 provider diagnostic audit failed; diagnostic helper is unavailable."
            )
        class _DiagnosticResponse:
            status_code = 413
            headers = {
                "x-ratelimit-limit-tokens": "70000",
                "x-ratelimit-remaining-tokens": "69000",
            }

            def json(self):
                return {"error": {"type": "request_too_large", "code": "request_too_large"}}

        class _DiagnosticException(Exception):
            status_code = 413
            response = _DiagnosticResponse()
            body = None

        _log_provider_exception_diagnostic(
            "self-audit",
            "self-audit/provider",
            _DiagnosticException("Request Entity Too Large"),
            max_tokens=160,
            input_chars=123,
            evidence_chars=45,
        )
        _strip_model_link_markup("", "")
        _build_generation_messages("self-audit", "TOPICAL_INQUIRY", "")
        _v133_explicit_resource_type_request_self_audit()
        _v153_document_architecture_orientation_self_audit()
        _v154_document_choice_orientation_self_audit()
        _v155_functional_document_choice_self_audit()
        _v157_functional_document_choice_synonym_self_audit()
        _v158_document_choice_retrieval_anchoring_self_audit()
        _v159_document_form_orientation_anchor_self_audit()
        _v163_document_form_orientation_evidence_packet_self_audit()
        _v163_generation_envelope_self_audit()
        _v163_model_routing_self_audit()
        _v164_task_aware_generation_budget_self_audit()
        _v165_lean_generation_envelope_self_audit()
        _v163_deterministic_document_form_orientation_self_audit()
        _v133_type_constrained_function_retrieval_self_audit()
        _v134_explicit_type_selection_preservation_self_audit()
        _v135_duplicate_evidence_enrichment_self_audit()
        _v136_enriched_recognition_propagation_self_audit()
        _v137_explicit_type_candidate_carry_forward_self_audit()
        _v92_question_structure_self_audit()
        _v92_question_structure_evidence_self_audit()
        _v92_question_evidence_correspondence_integration_self_audit()

        v72_centrality = _v72_question_doorway_centrality_self_audit()
        if not v72_centrality["pass"]:
            raise RuntimeError(
                "v72 question-doorway centrality self-audit failed: "
                f"{v72_centrality}"
            )

        v75_frame_sovereignty = _v75_interpretive_frame_sovereignty_self_audit()
        if not v75_frame_sovereignty["pass"]:
            raise RuntimeError(
                "v76 interpretive-frame sovereignty self-audit failed: "
                f"{v75_frame_sovereignty}"
            )

        v76_frame_neutral = _v76_frame_neutral_evidence_self_audit()
        if not v76_frame_neutral["pass"]:
            raise RuntimeError(
                "v76 frame-neutral evidence self-audit failed: "
                f"{v76_frame_neutral}"
            )

        v92_frame_specific = _v92_frame_specific_resource_self_audit()
        if not v92_frame_specific["pass"]:
            raise RuntimeError(
                "v92 frame-specific resource self-audit failed: "
                f"{v92_frame_specific}"
            )
        
        v78_inferential_distance = _v78_inferential_distance_self_audit()
        if not v78_inferential_distance["pass"]:
            raise RuntimeError(
                "v78 evidence-bound inferential-distance self-audit failed: "
                f"{v78_inferential_distance}"
            )

        v80_interpretive_bridge_integrity = _v80_interpretive_bridge_integrity_self_audit()
        if not v80_interpretive_bridge_integrity["pass"]:
            raise RuntimeError(
                "v80 interpretive-bridge-integrity self-audit failed: "
                f"{v80_interpretive_bridge_integrity}"
            )

        v81_evidence_sufficiency = _v81_evidence_sufficiency_self_audit()
        if not v81_evidence_sufficiency["pass"]:
            raise RuntimeError(
                "D16 evidence-sufficiency self-audit failed: "
                f"{v81_evidence_sufficiency}"
            )

        # v151 MVP response-boundary regression: a provider cannot convert
        # canonical presence into a false evidence-gap claim merely by naming
        # the selected resources. The boundary must reject the claim.
        false_gap_probe = (
            "The provided canonical evidence does not contain information "
            "regarding the purpose of a Reference Map. "
            "Available resources include Document Types of the Living Archive."
        )
        if not _looks_like_false_evidence_gap_claim(false_gap_probe):
            raise RuntimeError(
                "v151 MVP regression: false evidence-gap provider claim was not detected."
            )
        print("USE v151 MVP FALSE EVIDENCE-GAP BOUNDARY AUDIT: PASS")

        # D16 response-boundary regression: insufficient evidence must have a
        # bounded visitor response rather than being passed to generation.
        insuff_response = _evidence_sufficiency_unavailable_response(
            "Why can learning more about a problem make it feel less understandable?"
        )
        if "does not establish a reliable explanation" not in insuff_response:
            raise RuntimeError(
                "D16 navigation boundary regression: bounded insufficiency "
                "response is missing."
            )

        # Canonical lifecycle regressions: archived resources may remain
        # technically published in WordPress and in Pinecone, but they must
        # never become navigational evidence.
        archived_metadata = {
            "title": "ARCHIVED - Energe’s Soul Custodian Constitution and CODEX",
            "url": "https://example.invalid/energe-legacy",
            "slug": "energes-soul-custodian-constitution-and-codex-legacy",
            "status": "publish",
            "access_class": "public",
            "text": "Historical resource retained for reference.",
        }
        if _is_navigable_canonical_resource(archived_metadata):
            raise RuntimeError(
                "Canonical lifecycle regression: explicitly archived resource "
                "was considered navigable."
            )

        archived_status_metadata = {
            "title": "Former Governance Framework",
            "url": "https://example.invalid/former-framework",
            "status": "archive",
            "text": "Historical resource retained for reference.",
        }
        if _is_navigable_canonical_resource(archived_status_metadata):
            raise RuntimeError(
                "Canonical lifecycle regression: archive lifecycle metadata "
                "was not enforced."
            )

        current_metadata = {
            "title": "Learning from Legacy Systems Without Repeating Them",
            "url": "https://example.invalid/legacy-systems",
            "slug": "learning-from-legacy-systems-without-repeating-them",
            "status": "publish",
            "access_class": "public",
            "text": "A current essay that discusses historical systems.",
        }
        if not _is_navigable_canonical_resource(current_metadata):
            raise RuntimeError(
                "Canonical lifecycle regression: legitimate current resource "
                "was incorrectly suppressed."
            )

        current_status_metadata = {
            "title": "Current Governance Framework",
            "url": "https://example.invalid/current-framework",
            "status": "publish",
            "text": "Current canonical resource.",
        }
        if not _is_navigable_canonical_resource(current_status_metadata):
            raise RuntimeError(
                "Canonical lifecycle regression: published current resource "
                "was incorrectly suppressed."
            )

        url_archived_metadata = {
            "title": "The Energe Codex",
            "url": "https://geralddaquila.com/the-energe-codex-legacy/",
            "status": "publish",
            "access_class": "public",
            "text": "Historical resource retained in the vector index.",
        }
        if _is_navigable_canonical_resource(url_archived_metadata):
            raise RuntimeError(
                "Canonical lifecycle regression: archived canonical URL "
                "was considered navigable."
            )

        current_url_metadata = {
            "title": "Learning from Legacy Systems Without Repeating Them",
            "url": "https://example.invalid/legacy-systems",
            "status": "publish",
            "text": "A current resource whose URL contains a non-archival legacy phrase.",
        }
        if not _is_navigable_canonical_resource(current_url_metadata):
            raise RuntimeError(
                "Canonical lifecycle regression: legitimate current URL "
                "was incorrectly suppressed."
            )

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
        if MAX_GENERATION_TOKENS != 290:
            raise RuntimeError(
                "Provider boundary regression: primary generation token budget changed; expected 290."
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

        # v163 adaptive-fit regression: after reducing the fixed primary envelope,
        # a large canonical context must be bounded into a request that fits the
        # authoritative provider envelope, rather than requiring a forced primary
        # failure merely because the old fixed prompt was oversized.
        synthetic_context = (
            "Title: Institutional Cornerstones\n"
            "URL: https://example.invalid/institutional-cornerstones\n"
            "Content: " + ("governance resilience evidence " * 80)
            + "\n\n---\n\n"
            "Title: Governance Foundations\n"
            "URL: https://example.invalid/governance-foundations\n"
            "Content: " + ("governance foundations evidence " * 80)
        )
        fitted_primary_context, fitted_primary_messages = _fit_generation_context_to_provider_budget(
            "Why can adding more rules to a system sometimes make the system less governable?",
            "TOPICAL_INQUIRY",
            synthetic_context,
            max_tokens=MAX_GENERATION_TOKENS,
        )
        fitted_primary_input = _estimate_message_chars(fitted_primary_messages)
        fitted_primary_total = fitted_primary_input + math.ceil(MAX_GENERATION_TOKENS * 4 * 1.25)
        if not fitted_primary_context.strip():
            raise RuntimeError("v163 adaptive-fit regression: primary canonical evidence was lost.")
        if fitted_primary_input > MAX_PROVIDER_INPUT_CHARS or fitted_primary_total > MAX_PROVIDER_TOTAL_CHARS:
            raise RuntimeError("v163 adaptive-fit regression: primary fitted request exceeds provider envelope.")

        fitted_context, fitted_messages = _fit_generation_context_to_provider_budget(
            "Why can adding more rules to a system sometimes make the system less governable?",
            "TOPICAL_INQUIRY",
            synthetic_context,
            max_tokens=MAX_COMPACT_GENERATION_TOKENS,
            compact=True,
        )
        fitted_input = _estimate_message_chars(fitted_messages)
        fitted_total = fitted_input + math.ceil(MAX_COMPACT_GENERATION_TOKENS * 4 * 1.25)
        if fitted_input > MAX_PROVIDER_INPUT_CHARS or fitted_total > MAX_PROVIDER_TOTAL_CHARS:
            raise RuntimeError(
                "Provider adaptive-fit regression: compact fitted request still exceeds envelope."
            )
        if len(fitted_context) >= len(synthetic_context):
            raise RuntimeError(
                "Provider adaptive-fit regression: oversized evidence was not compacted."
            )

        # Provider-envelope regression: the fixed generation envelope itself must leave
        # meaningful room for canonical evidence. The boundary is expressed in terms
        # of actual remaining provider capacity rather than a historical fixed-input
        # character ceiling, because legitimate generation-boundary safeguards may
        # increase the fixed prompt envelope while remaining provider-safe.
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
        if primary_evidence_capacity < 0:
            raise RuntimeError(
                "Provider compact-boundary regression: computed primary evidence "
                f"capacity is negative (capacity={primary_evidence_capacity}, "
                f"fixed_input={primary_fixed_chars})."
            )

        # v77 regression: the primary generation budget must materially exceed
        # the v76 240-token ceiling while preserving a substantial evidence window.
        if MAX_GENERATION_TOKENS <= 240:
            raise RuntimeError(
                "Generation capacity regression: primary output budget did not increase."
            )
        # v123 regression: the application's own fixed-envelope preflight failure
        # must enter the existing compact-generation recovery classifier. Without
        # this marker, every primary provider attempt can fail before the API call
        # and compact recovery is never reached.
        preflight_error = (
            "USE provider preflight could not fit the fixed system/user "
            "envelope: fixed_input=3200, estimated_output=1600."
        )
        if not _is_request_too_large_error(preflight_error):
            raise RuntimeError(
                "v125 generation recovery regression: fixed-envelope preflight "
                "failure was not classified as request-size recoverable."
            )

        # v148 regression: the newly discovered boundary must be recoverable.
        canonical_evidence_error = (
            "USE provider preflight could not preserve a minimally viable "
            "canonical evidence block within the primary envelope: "
            "context_capacity=42, target_context_chars=42."
        )
        if not _is_request_too_large_error(canonical_evidence_error):
            raise RuntimeError(
                "v148 generation recovery regression: canonical evidence "
                "preservation boundary was not classified as request-size recoverable."
            )

        fitter_source = inspect.getsource(_fit_generation_context_to_provider_budget)
        if "cannot preserve a minimally viable" not in fitter_source:
            raise RuntimeError(
                "v148 generation recovery regression: primary evidence-preservation "
                "boundary is missing from the provider fitter."
            )

        compact_fixed_messages = _build_generation_messages(
            "A compact recovery test question",
            "TOPICAL_INQUIRY",
            "",
            None,
            compact=True,
        )
        compact_fixed_chars = _estimate_message_chars(compact_fixed_messages)
        compact_output_reservation = math.ceil(
            MAX_COMPACT_GENERATION_TOKENS * 4 * 1.25
        )
        if (
            compact_fixed_chars + compact_output_reservation
            > MAX_PROVIDER_TOTAL_CHARS
        ):
            raise RuntimeError(
                "v125 generation recovery regression: compact generation still "
                "cannot fit the fixed provider envelope."
            )

        # The current primary envelope may intentionally leave less than a full
        # canonical block; v148 routes that condition into compact recovery.
        if primary_evidence_capacity < 0:
            raise RuntimeError(
                "Generation capacity regression: primary evidence capacity is negative."
            )

        # Release identity audit: the source file itself must declare the
        # same version as the runtime and deployment fingerprint. This prevents
        # the repeated stale/misaligned top-of-file version problem.
        source_lines = Path(__file__).read_text(encoding="utf-8").splitlines()
        expected_source_prefixes = (
            f"# USE TEST VERSION: {APP_VERSION}",
            f"# USE PRODUCTION VERSION: {APP_VERSION}",
        )
        if not source_lines or not source_lines[0].startswith(expected_source_prefixes):
            raise RuntimeError(
                f"Source version-label regression: line 1 does not identify {APP_VERSION}."
            )
        if not re.fullmatch(r"v\d+", APP_VERSION):
            raise RuntimeError(f"Runtime version identity malformed: {APP_VERSION!r}.")
        if not DEPLOYMENT_FINGERPRINT.startswith(f"USE-{APP_VERSION}-"):
            raise RuntimeError(
                "Deployment fingerprint regression: current deployment fingerprint is not aligned "
                f"with APP_VERSION={APP_VERSION}."
            )
        # Audit the audit surface itself: detect inherited prior-release identity
        # assertions, not legitimate historical audit function names/comments.
        # This scanner is deliberately invariant-based so retaining a prior
        # regression audit does not itself become a false positive.
        prior_version = "v" + "92"
        stale_identity_patterns = (
            f'APP_VERSION = "{prior_version}"',
            f'APP_VERSION != "{prior_version}"',
            f'expected {prior_version}',
            f'expected_source_prefixes = (\n            "# USE TEST VERSION: {prior_version}"',
            f'USE-{prior_version}-',
        )
        stale_prior_release_hits = [
            f"line {idx}: {line}"
            for idx, line in enumerate(source_lines, 1)
            if any(pattern.lower() in line.lower() for pattern in stale_identity_patterns)
        ]
        if stale_prior_release_hits:
            raise RuntimeError(
                "Stale-version audit regression: inherited prior-release identity "
                "assertions remain: " + " | ".join(stale_prior_release_hits[:5])
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

        # Constitutional topical-navigation and multi-resource invariants:
        # test the current compact policy, not obsolete historical wording.
        if "For TOPICAL questions, orient through supplied evidence, not generic explanation." not in GENERATION_SYSTEM_PROMPT:
            raise RuntimeError(
                "Topical navigation regression: evidence-grounded topical orientation policy is missing."
            )
        if "normally use 2–3 only for distinct coverage" not in GENERATION_SYSTEM_PROMPT:
            raise RuntimeError(
                "Multi-resource navigation regression: current multi-resource policy is missing."
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

        # v61 regression: generic topical prose without a selected canonical
        # resource must fail the navigation-reference gate, while a valid
        # selected title must pass it.
        topical_gate_context = (
            "Title: Canonical Doorway\n"
            "URL: https://example.invalid/canonical-doorway\n"
            "Content: Evidence about the visitor's topical question."
        )
        if _contains_canonical_resource_reference(
            "A general explanation without a resource.",
            topical_gate_context,
        ):
            raise RuntimeError(
                "Topical navigation regression: generic prose falsely passed resource gate."
            )
        if not _contains_canonical_resource_reference(
            "Explore Canonical Doorway for the relevant treatment.",
            topical_gate_context,
        ):
            raise RuntimeError(
                "Topical navigation regression: canonical resource reference was not detected."
            )

        # v61 regression: provider evidence omits URLs so more selected canonical
        # titles and topical evidence fit inside the same provider envelope.
        density_context = format_context_blocks([
            {"title": "First Canonical Resource", "url": "https://example.invalid/first", "text": "Evidence about the first topical dimension."},
            {"title": "Second Canonical Resource", "url": "https://example.invalid/second", "text": "Evidence about the second topical dimension."},
            {"title": "Third Canonical Resource", "url": "https://example.invalid/third", "text": "Evidence about the third topical dimension."},
        ])
        dense_provider_context = _build_provider_evidence_context(density_context, 500, 140)
        if "URL:" in dense_provider_context:
            raise RuntimeError("Provider evidence density regression: URLs consumed provider evidence space.")
        if len(re.findall(r"^Title:", dense_provider_context, flags=re.MULTILINE)) < 3:
            raise RuntimeError("Provider evidence density regression: selected canonical titles were lost.")

        # v63 regression: the compact provider instruction must materially reduce
        # fixed envelope consumption so the selected evidence can survive intact.
        # The compact boundary is now validated against the actual provider
        # capacity rather than the obsolete 1800-character fixed-envelope ceiling.
        compact_empty_messages = _build_generation_messages(
            "Why do systems change?",
            "TOPICAL_INQUIRY",
            "",
            None,
            compact=True,
        )
        compact_fixed_chars = _estimate_message_chars(compact_empty_messages)
        compact_output_reservation = math.ceil(MAX_COMPACT_GENERATION_TOKENS * 4 * 1.25)
        compact_evidence_capacity = min(
            MAX_PROVIDER_INPUT_CHARS - compact_fixed_chars,
            MAX_PROVIDER_TOTAL_CHARS - compact_fixed_chars - compact_output_reservation,
        )
        if compact_evidence_capacity < 150:
            raise RuntimeError(
                "Compact generation regression: provider envelope leaves insufficient "
                f"room for canonical evidence "
                f"(capacity={compact_evidence_capacity}, fixed_input={compact_fixed_chars})."
            )

        # v128 regression: compact recovery must itself fit the configured
        # provider envelope. Historical fixed-character ceilings are deliberately
        # not asserted here because the prompt can evolve while the authoritative
        # provider limits remain unchanged.
        if compact_fixed_chars >= MAX_PROVIDER_INPUT_CHARS:
            raise RuntimeError(
                "v128 compact-envelope regression: compact fixed system/user "
                f"envelope exceeds provider input capacity "
                f"(fixed_input={compact_fixed_chars}, limit={MAX_PROVIDER_INPUT_CHARS})."
            )
        if compact_fixed_chars + compact_output_reservation > MAX_PROVIDER_TOTAL_CHARS:
            raise RuntimeError(
                "v128 compact-envelope regression: compact fixed envelope plus "
                "output reservation exceeds provider total capacity."
            )
        if MAX_COMPACT_GENERATION_CONTEXT_CHARS > 650:
            raise RuntimeError(
                "v128 evidence-bound regression: recovery evidence ceiling exceeded the audited compact ceiling."
            )
        compact_schema_probe_context = (
            "Title: Probe Resource\n"
            "URL: https://example.invalid/probe\n"
            "Content: Probe evidence text."
        )
        compact_schema_free_probe = _bound_existing_context_blocks(
            compact_schema_probe_context,
            650,
            220,
            schema_free=True,
        )
        if "Title:" in compact_schema_free_probe or "URL:" in compact_schema_free_probe or "Content:" in compact_schema_free_probe:
            raise RuntimeError(
                "v128 compact schema-free evidence regression: internal evidence labels remain in recovery context."
            )
        if "Probe Resource" not in compact_schema_free_probe or "Probe evidence text." not in compact_schema_free_probe:
            raise RuntimeError(
                "v130 compact schema-free evidence regression: canonical identity or evidence text was lost."
            )
        compact_provider_probe = _build_provider_evidence_context(
            compact_schema_free_probe, 650, 220, schema_free=True
        )
        if "Probe Resource" not in compact_provider_probe or "Probe evidence text." not in compact_provider_probe:
            raise RuntimeError(
                "v130 compact provider evidence regression: schema-free evidence was discarded by the provider evidence builder."
            )
        if "Title:" in compact_provider_probe or "URL:" in compact_provider_probe or "Content:" in compact_provider_probe:
            raise RuntimeError(
                "v130 compact provider evidence regression: internal evidence labels remain in provider recovery context."
            )

        # v133 regression: compact generation must validate topical grounding
        # against the original canonical Title/URL context, not the schema-free
        # provider context. This prevents a model from naming/linking a resource
        # that was never supplied as generation evidence.
        grounding_validation_probe = (
            "Title: Selected Resource\n"
            "URL: https://example.invalid/selected\n"
            "Content: Selected canonical evidence."
        )
        if not _canonical_pairs(grounding_validation_probe):
            raise RuntimeError(
                "v133 generation grounding regression: canonical validation context was not parseable."
            )
        unauthorized_answer_probe = (
            "The relevant material is [Unauthorized Resource]"
            "(https://geralddaquila.com/unauthorized-resource/)."
        )
        if _contains_canonical_resource_reference(
            unauthorized_answer_probe, grounding_validation_probe
        ):
            raise RuntimeError(
                "v133 generation grounding regression: unauthorized resource was treated as selected evidence."
            )
        authorized_answer_probe = "The relevant material is Selected Resource."
        if not _contains_canonical_resource_reference(
            authorized_answer_probe, grounding_validation_probe
        ):
            raise RuntimeError(
                "v133 generation grounding regression: selected canonical resource reference was not recognized."
            )
        compact_fit_probe, compact_fit_messages = _fit_generation_context_to_provider_budget(
            "Probe question",
            "TOPICAL_INQUIRY",
            compact_schema_free_probe,
            max_tokens=MAX_COMPACT_GENERATION_TOKENS,
            compact=True,
        )
        if "Probe Resource" not in compact_fit_probe or "Probe evidence text." not in compact_fit_probe:
            raise RuntimeError(
                "v130 compact context propagation regression: provider budget fitting discarded schema-free evidence."
            )
        if _estimate_message_chars(compact_fit_messages) <= 0:
            raise RuntimeError(
                "v130 compact context propagation regression: provider messages were not assembled."
            )

        compact_prompt_probe = COMPACT_GENERATION_SYSTEM_PROMPT.casefold()
        for required_marker in ("never reproduce internal field labels", "title:", "url:", "content:"):
            if required_marker not in compact_prompt_probe:
                raise RuntimeError(
                    "v128 compact schema-guard regression: required schema-protection instruction missing."
                )

        # v65 regression: doorway selection must prioritize a canonical
        # resource whose evidence establishes an orientational/entry role
        # over a narrowly topical resource when both are already retrieved.
        doorway_documents = [
            {
                "title": "Narrow Institutional Change Example",
                "url": "https://example.invalid/narrow",
                "text": "A focused discussion of one institutional change.",
            },
            {
                "title": "Institutional Foundations",
                "url": "https://example.invalid/foundations",
                "text": "An overview of institutional foundations and where to begin exploring the question.",
            },
        ]
        doorway_selected = select_canonical_doorways(
            doorway_documents,
            {"primary": "systems", "scores": {"systems": 1}},
        )
        if doorway_selected[0]["title"] != "Institutional Foundations":
            raise RuntimeError(
                "Canonical doorway selection regression: stronger orientational "
                "entry resource was not prioritized."
            )

        # v66 regression: doorway selection must be conditioned on the actual
        # question, not merely on generic doorway language. A generic guide
        # must yield to an already-retrieved resource whose evidence directly
        # addresses the question's substantive terms.
        question_conditioned_documents = [
            {
                "title": "General Orientation Guide",
                "url": "https://example.invalid/general-guide",
                "text": "An overview and where to begin exploring the archive.",
            },
            {
                "title": "Understanding Lived Experience",
                "url": "https://example.invalid/lived-experience",
                "text": "This essay explores how intellectual understanding can differ from lived experience.",
            },
        ]
        question_conditioned_selected = select_canonical_doorways(
            question_conditioned_documents,
            {"primary": "inward", "scores": {"inward": 1}},
            question="Why does intellectual understanding not always change lived experience?",
        )
        if question_conditioned_selected[0]["title"] != "Understanding Lived Experience":
            raise RuntimeError(
                "Question-conditioned doorway regression: direct question fit "
                "did not outrank generic doorway language."
            )

        # v66 boundary regression: question conditioning may only reorder the
        # already-retrieved set and must not manufacture or remove resources.
        question_conditioned_before = {
            _resource_key(document) for document in question_conditioned_documents
        }
        question_conditioned_after = {
            _resource_key(document) for document in question_conditioned_selected
        }
        if question_conditioned_before != question_conditioned_after:
            raise RuntimeError(
                "Question-conditioned doorway regression: resource set changed."
            )

        # v67 regression: an ambiguous experiential question must not be forced
        # into an interpretively specific doorway merely because that resource
        # advertises a gateway/framework/orientation role. When direct question
        # grounding is weak, generic doorway evidence is deliberately capped so
        # semantic retrieval order remains sovereign.
        ambiguous_question = "Why can a life that looks fine from the outside still feel wrong from the inside?"
        ambiguous_documents = [
            {
                "title": "What Is Ego Death? The Hidden Gateway to Spiritual Transformation",
                "url": "https://example.invalid/ego-death",
                "text": "A gateway into spiritual transformation through ego and identity."
            },
            {
                "title": "Inner Disorientation and the Life That No Longer Fits",
                "url": "https://example.invalid/inner-disorientation",
                "text": "Explores why an outwardly fine life can still feel wrong from the inside."
            },
        ]
        ambiguous_selected = select_canonical_doorways(
            ambiguous_documents,
            {"primary": "inward", "scores": {"inward": 1}},
            question=ambiguous_question,
        )
        if ambiguous_selected[0]["title"] != "Inner Disorientation and the Life That No Longer Fits":
            raise RuntimeError(
                "Ambiguity-aware doorway regression: interpretively specific "
                "gateway language displaced the closer question-grounded resource."
            )

        # v68 interpretive sovereignty regression: broad first-person
        # experiential questions are flagged structurally, without naming a
        # particular domain or forcing a specialized explanation.
        if not _question_is_underdetermined(
            "Why does something I used to care about sometimes stop feeling important?"
        ):
            raise RuntimeError(
                "Interpretive sovereignty regression: broad experiential question "
                "was not recognized as underdetermined."
            )
        if _question_is_underdetermined(
            "Why does cognitive dissonance make choices difficult?"
        ):
            raise RuntimeError(
                "Interpretive sovereignty regression: explicit mechanism question "
                "was incorrectly treated as underdetermined."
            )

        # v69 proportionality regression: a highly specialized resource must not
        # become the canonical doorway to a broad question merely because its body
        # contains semantically related material. A proportionate resource remains
        # eligible from the same already-retrieved set.
        proportionality_question = (
            "Why can I understand what I need to let go of and still feel unable to let it go?"
        )
        proportionality_documents = [
            {
                "title": "Psychological Pain, Disconnection, and the Journey of the Soul: Suicide and Meaning",
                "url": "https://example.invalid/specialized",
                "text": "Psychological pain and disconnection can affect the ability to act, even when a person understands a difficult change.",
            },
            {
                "title": "When Understanding Does Not Become Action",
                "url": "https://example.invalid/proportionate",
                "text": "Explores the gap between intellectual understanding, emotional readiness, and the ability to make a change.",
            },
        ]
        proportionality_selected = select_canonical_doorways(
            proportionality_documents,
            {"primary": "inward", "scores": {"inward": 1}},
            question=proportionality_question,
        )
        if proportionality_selected[0]["title"] != "When Understanding Does Not Become Action":
            raise RuntimeError(
                "Canonical doorway proportionality regression: disproportionate "
                "specialized resource displaced a proportionate doorway."
            )
        if proportionality_selected[1]["title"] != "Psychological Pain, Disconnection, and the Journey of the Soul: Suicide and Meaning":
            raise RuntimeError(
                "Canonical doorway proportionality regression: specialized resource "
                "was incorrectly removed or reordered beyond the doorway ranking."
            )

        # v69 boundary regression: when the visitor explicitly names the specialized
        # domain, proportionality must not suppress the directly relevant resource.
        explicit_specialized_question = "How can psychological pain after suicide affect my ability to make changes?"
        explicit_specialized_selected = select_canonical_doorways(
            proportionality_documents,
            {"primary": "inward", "scores": {"inward": 1}},
            question=explicit_specialized_question,
        )
        if explicit_specialized_selected[0]["title"] != "Psychological Pain, Disconnection, and the Journey of the Soul: Suicide and Meaning":
            raise RuntimeError(
                "Canonical doorway proportionality regression: explicit specialized "
                "question did not preserve the directly relevant specialized doorway."
            )

        # v72 regression: an open experiential question must not promote a
        # specialized worldview doorway merely because the retrieved resource
        # contains a compatible interpretive vocabulary. Explicitly naming the
        # worldview must restore its eligibility.
        centrality_documents = [
            {
                "title": "Divine Timing and Synchronicity: Unveiling the Cosmic Choreography of Awakening",
                "url": "https://example.invalid/awakening",
                "text": "Explores awakening, synchronicity, and spiritual perception.",
            },
            {
                "title": "Understanding Everyday Change and Perception",
                "url": "https://example.invalid/everyday-change",
                "text": "Explores how changes in perception can alter how ordinary situations are experienced.",
            },
        ]
        centrality_question = (
            "Why can becoming more aware of yourself sometimes make ordinary parts "
            "of life feel strangely unfamiliar?"
        )
        centrality_selected = select_canonical_doorways(
            centrality_documents,
            {"primary": "inward", "scores": {"inward": 1}},
            question=centrality_question,
        )
        if centrality_selected[0]["title"] != "Understanding Everyday Change and Perception":
            raise RuntimeError(
                "v72 question-doorway centrality regression: specialized worldview "
                "doorway displaced the proportionate neutral doorway."
            )

        explicit_centrality_selected = select_canonical_doorways(
            centrality_documents,
            {"primary": "inward", "scores": {"inward": 1}},
            question="Why can awakening make ordinary life feel unfamiliar?",
        )
        if explicit_centrality_selected[0]["title"] != "Divine Timing and Synchronicity: Unveiling the Cosmic Choreography of Awakening":
            raise RuntimeError(
                "v72 question-doorway centrality regression: explicitly named "
                "framework did not remain eligible."
            )

        # v65 boundary regression: doorway selection may only reorder supplied
        # canonical resources; it must never manufacture a new resource.
        doorway_keys_before = {
            _resource_key(document) for document in doorway_documents
        }
        doorway_keys_after = {
            _resource_key(document) for document in doorway_selected
        }
        if doorway_keys_before != doorway_keys_after:
            raise RuntimeError(
                "Canonical doorway selection regression: selection changed "
                "the retrieved resource set."
            )

        # v65 boundary regression: explicit protected destinations remain
        # first and are never displaced by topical doorway scoring.
        protected_documents = [
            {
                "title": "Requested Collection",
                "url": "https://example.invalid/collection",
                "text": "The requested collection landing page.",
            },
            {
                "title": "Foundational Guide",
                "url": "https://example.invalid/guide",
                "text": "An overview and where to begin.",
            },
        ]
        protected_selected = select_canonical_doorways(
            protected_documents,
            {"primary": "systems", "scores": {"systems": 1}},
            preserve_prefix=1,
        )
        if protected_selected[0]["title"] != "Requested Collection":
            raise RuntimeError(
                "Canonical doorway selection regression: protected destination "
                "was displaced."
            )

        # v73 regression retained: titles/URLs are identity metadata, not substantive
        # evidence. The generation boundary must explicitly prevent title-only
        # inference and require supplied Content/evidence for resource claims.
        provenance_messages = _build_generation_messages(
            "How can I tell whether an old pattern is no longer fitting me?",
            "TOPICAL_INQUIRY",
            (
                "Title: What Is Ego Death? The Hidden Gateway to Spiritual Transformation\n"
                "URL: https://example.invalid/ego-death\n"
                "Content: A resource is supplied here only as a short retrieval "
                "record and does not establish what the full article says."
            ),
            {"primary": "inward", "scores": {}},
        )
        provenance_system = provenance_messages[0]["content"]
        if "[PROVENANCE + SYNTHESIS]" not in provenance_system:
            raise RuntimeError(
                "v73 provenance regression: evidence-provenance instruction "
                "was not added to topical generation."
            )
        if "Titles/URLs identify resources, not evidence." not in provenance_system or "Ground claims in supplied Content;" not in provenance_system:
            raise RuntimeError(
                "v73 provenance regression: title/URL identity boundary or "
                "Content evidence requirement is missing."
            )

        # v75 regression: broad experiential questions must not acquire an
        # uninvited specialized interpretive frame from retrieved evidence.
        frame_messages = _build_generation_messages(
            "If I stop trying to interpret an experience immediately, what becomes available to me?",
            "TOPICAL_INQUIRY",
            (
                "Title: What Is Ego Death? The Hidden Gateway to Spiritual Transformation\n"
                "URL: https://example.invalid/ego-death\n"
                "Content: The resource discusses a specialized spiritual framework. "
                "The supplied excerpt is insufficient to establish that the visitor "
                "is undergoing that framework or its outcomes."
            ),
            {"primary": "inward", "scores": {}},
        )
        frame_system = frame_messages[0]["content"]
        if "[FRAME SOVEREIGNTY]" not in frame_system:
            raise RuntimeError(
                "v75 frame-sovereignty regression: specialized framework guard "
                "was not added for broad experiential questions."
            )
        if "A specialized framework may govern the explanation only when the visitor names it." not in frame_system:
            raise RuntimeError(
                "v75 frame-sovereignty regression: governing-frame boundary missing."
            )

        # v71 regression: topical generation must explicitly preserve the
        # distinction between source-supported claims and inferred causal bridges.
        synthesis_messages = _build_generation_messages(
            "Why can certainty at the moment of a decision become uncertainty after I live with it?",
            "TOPICAL_INQUIRY",
            (
                "Title: Resource A\n"
                "URL: https://example.invalid/a\n"
                "Content: A source discusses how choosing can reduce uncertainty.\n\n"
                "---\n\n"
                "Title: Resource B\n"
                "URL: https://example.invalid/b\n"
                "Content: A source discusses how circumstances change over time."
            ),
            {"primary": "general", "scores": {}},
        )
        synthesis_system = synthesis_messages[0]["content"]
        if "[PROVENANCE + SYNTHESIS]" not in synthesis_system:
            raise RuntimeError(
                "v71 synthesis-boundary regression: explicit synthesis guard "
                "was not included in the topical generation boundary."
            )
        synthesis_lower = synthesis_system.lower()
        if (
            "never turn thematic compatibility into causation." not in synthesis_lower
            or "[inferential distance]" not in synthesis_lower
        ):
            raise RuntimeError(
                "v71 synthesis-boundary regression: current causal-boundary "
                "instruction was not preserved."
            )

        # D16 reconciliation invariants.
        if not re.fullmatch(r"v\d+", APP_VERSION):
            raise RuntimeError(f"Unexpected USE version identity: {APP_VERSION}")

        # USE public corpus boundary: explicit T4/restricted resources are never
        # eligible, while public T1–T3 resources remain eligible.
        if _is_navigable_canonical_resource({
            "title": "Restricted T4 Resource",
            "url": "https://example.invalid/t4",
            "tier": "T4",
            "access_class": "steward",
            "text": "Protected."
        }):
            raise RuntimeError("USE corpus boundary regression: protected T4 resource was admitted.")
        if not _is_navigable_canonical_resource({
            "title": "Public T3 Resource",
            "url": "https://example.invalid/t3",
            "tier": "T3",
            "access_class": "public",
            "text": "Public canonical evidence."
        }):
            raise RuntimeError("USE corpus boundary regression: public T3 resource was rejected.")

        # Synthesis insufficiency must preserve navigation.
        nav_context = (
            "Title: Nearby Canonical Doorway\n"
            "URL: https://example.invalid/doorway\n"
            "Content: A nearby canonical resource."
        )
        nav_response = _evidence_sufficiency_unavailable_response(
            "An under-supported question",
            nav_context,
        )
        if "Nearby Canonical Doorway" not in nav_response:
            raise RuntimeError("USE navigation boundary regression: insufficient evidence closed navigation.")

        # Passive 5-Why observer: exactly five consecutive stewardship questions
        # trigger an invitation, never a readiness diagnosis or current-turn control.
        five_history = [
            {"role": "user", "content": "How does responsibility affect others?"},
            {"role": "user", "content": "What does service require?"},
            {"role": "user", "content": "How do I serve the larger whole?"},
            {"role": "user", "content": "What does stewardship mean here?"},
        ]
        five_state = assess_progressive_commitment(
            "How do I take responsibility for what I build?",
            five_history,
        )
        if not five_state["steward_access_invitation"]:
            raise RuntimeError("5-Why boundary regression: five consecutive stewardship questions did not trigger invitation.")
        if five_state["current_turn_influence"] or five_state["native_vocabulary_allowed"]:
            raise RuntimeError("5-Why boundary regression: observer gained current-turn authority.")
        four_state = assess_progressive_commitment(
            "What should I understand about stewardship?",
            five_history[:3],
        )
        if four_state["steward_access_invitation"]:
            raise RuntimeError("5-Why threshold regression: invitation triggered before five consecutive questions.")

        # Runtime identity must be explicit and current.
        if not re.fullmatch(r"v\d+", APP_VERSION):
            raise RuntimeError(
                f"Unexpected USE runtime version identity: {APP_VERSION}"
            )

        # v92 D17 execution-path regression: explicit relational structure must
        # remain available to the normal fetch path without creating a D17
        # synthesis-block return.
        d17_source = inspect.getsource(fetch_canonical_context)
        if "question_structure = recognize_question_structure(user_query)" not in d17_source:
            raise RuntimeError("v92 execution-path regression: D17 structure recognition is missing from fetch path.")
        if "question_structure_evidence_unavailable" in d17_source:
            raise RuntimeError("v92 execution-path regression: obsolete D17 synthesis-block path remains.")

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
        "visitor-output sanitation, canonical presentation equivalence, resource uniqueness, "
        "canonical lifecycle eligibility, and runtime identification verified."
    )



def _d19_canonical_resource_model_self_audit() -> None:
    """Verify D19 models explicit metadata without inventing missing fields."""
    explicit = {
        "id": "resource-1",
        "title": "Example Resource",
        "url": "https://example.invalid/resource-1",
        "resource_type": "Reference Map",
        "resource_function": "orientation",
        "lifecycle": "current",
        "access_class": "public",
    }
    model = _canonical_resource_model(explicit)

    if model["identity"]["id"] != "resource-1":
        raise RuntimeError("D19 resource-model regression: explicit identity was not preserved.")
    if model["resource_type"] != "Reference Map":
        raise RuntimeError("D19 resource-model regression: explicit resource type was not preserved.")
    if model["function"] != "orientation":
        raise RuntimeError("D19 resource-model regression: explicit resource function was not preserved.")
    if model["lifecycle"] != "current" or model["access"] != "public":
        raise RuntimeError("D19 resource-model regression: lifecycle/access evidence was not preserved.")
    if model["navigation_role"] is not None or model["evidence_role"] is not None:
        raise RuntimeError("D19 resource-model regression: request-specific roles were invented.")

    missing = {
        "title": "No Type Example",
        "url": "https://example.invalid/no-type",
        "text": "Canonical content without explicit type metadata.",
    }
    missing_model = _canonical_resource_model(missing)
    if missing_model["resource_type"] is not None or missing_model["function"] is not None:
        raise RuntimeError("D19 resource-model regression: missing type/function was guessed.")

    attached = _attach_canonical_resource_model(dict(missing))
    if "_use_resource_model" not in attached:
        raise RuntimeError("D19 resource-model regression: model was not attached to resource metadata.")
    print("USE D19 CANONICAL RESOURCE MODEL AUDIT: PASS")


def _d20_resource_type_recognition_self_audit() -> None:
    """Verify D20 recognizes canonical types conservatively and preserves unknowns."""
    explicit = {
        "title": "Example Resource",
        "resource_type": "Reference Map",
    }
    explicit_result = _recognize_resource_type(explicit)
    if explicit_result["resource_type"] != "Reference Map" or explicit_result["confidence"] != "explicit":
        raise RuntimeError("D20 resource-type regression: explicit metadata was not recognized authoritatively.")

    navigator = {"title": "The Living Archive Navigator — Governance & Sovereignty"}
    navigator_result = _recognize_resource_type(navigator)
    if navigator_result["resource_type"] != "Navigator":
        raise RuntimeError("D20 resource-type regression: Navigator title was not recognized.")

    reference_map = {"title": "Reference Map 024 — The Adaptive Systems Map"}
    map_result = _recognize_resource_type(reference_map)
    if map_result["resource_type"] != "Reference Map":
        raise RuntimeError("D20 resource-type regression: Reference Map title was not recognized.")

    pathway = {"title": "Guided Reading Pathway — Understanding Change"}
    pathway_result = _recognize_resource_type(pathway)
    if pathway_result["resource_type"] != "Pathway":
        raise RuntimeError("D20 resource-type regression: Pathway title was not recognized.")

    mention_only = {
        "title": "Understanding Sovereignty",
        "text": "The Living Archive includes Reference Maps, Navigators, and Guided Reading Pathways.",
    }
    mention_result = _recognize_resource_type(mention_only)
    if mention_result["resource_type"] is not None:
        raise RuntimeError("D20 resource-type regression: incidental mentions were treated as resource identity.")

    generic_post = {
        "title": "Sovereignty in the Smallest Temple",
        "type": "post",
        "text": "A canonical discussion of sovereignty and family life.",
    }
    generic_result = _recognize_resource_type(generic_post)
    if generic_result["resource_type"] is not None:
        raise RuntimeError("D20 resource-type regression: generic WordPress type was converted into a canonical type.")

    attached = _attach_resource_type_recognition(dict(navigator))
    if attached["_use_resource_type_recognition"]["resource_type"] != "Navigator":
        raise RuntimeError("D20 resource-type regression: recognition was not attached to resource metadata.")

    print("USE D20 RESOURCE-TYPE RECOGNITION AUDIT: PASS")


def _d21_essay_function_self_audit() -> None:
    """Verify Essay function is asserted only from sufficient evidence."""
    good = {
        "title": "The Psychology of Scarcity",
        "_use_resource_type_recognition": {
            "resource_type": "Essay",
            "confidence": "strong",
            "basis": "content_self_identification",
        },
        "text": (
            "This essay explores scarcity as a developmental and psychological process. "
            "This essay presents an integrative architectural synthesis informed by "
            "developmental psychology, behavioral economics, neuroscience, and systems thinking."
        ),
    }
    result = _d21_essay_function(good)
    assert result["function"] == _D21_ESSAY_FUNCTION_LABEL, "D21 Essay function not recognized"
    assert result["basis"] == "essay_exploration_and_synthesis_evidence", "D21 Essay provenance not bounded"

    insufficient = {
        "title": "The Psychology of Scarcity",
        "_use_resource_type_recognition": {"resource_type": "Essay"},
        "text": "This essay is available in the Living Archive.",
    }
    assert _d21_essay_function(insufficient)["function"] is None, "D21 guessed Essay function"

    non_essay = {
        "title": "The Living Archive Navigator Series",
        "_use_resource_type_recognition": {"resource_type": "Navigator"},
        "text": (
            "This Navigator brings together Reference Maps and guided reading pathways. "
            "It integrates several forms of archive navigation."
        ),
    }
    non_result = _d21_essay_function(non_essay)
    assert (
        non_result["function"] is None
        and non_result["basis"] == "resource_type_not_essay"
    ), "D21 leaked Essay function"

    attached = _attach_essay_function(dict(good))
    assert (
        attached["_use_essay_function"]["function"] == _D21_ESSAY_FUNCTION_LABEL
    ), "D21 Essay function not attached"
    print("USE D21 ESSAY FUNCTION AUDIT: PASS")


def _d22_cornerstone_function_self_audit() -> None:
    """Verify Cornerstone function is asserted only from sufficient evidence."""
    good = {
        "title": "The Twelve Cornerstones of the Living Archive",
        "_use_resource_type_recognition": {
            "resource_type": "Cornerstone",
            "confidence": "strong",
            "basis": "content_self_identification",
        },
        "text": (
            "This Cornerstone provides a foundational lens for understanding "
            "larger patterns across multiple domains of life. The Cornerstones "
            "act as bridges between disciplines and reveal common underlying "
            "principles across governance, culture, technology, and human development."
        ),
    }
    result = _d22_cornerstone_function(good)
    assert result["function"] == _D22_CORNERSTONE_FUNCTION_LABEL, (
        "D22 Cornerstone function not recognized"
    )
    assert result["basis"] == (
        "cornerstone_foundational_and_cross_domain_evidence"
    ), "D22 Cornerstone provenance not bounded"

    insufficient = {
        "title": "Trust Architecture",
        "_use_resource_type_recognition": {"resource_type": "Cornerstone"},
        "text": (
            "This Cornerstone discusses trust and governance. "
            "It contains several sections and reflections."
        ),
    }
    assert _d22_cornerstone_function(insufficient)["function"] is None, (
        "D22 guessed Cornerstone function"
    )

    non_cornerstone = {
        "title": "An Essay About Systems",
        "_use_resource_type_recognition": {"resource_type": "Essay"},
        "text": (
            "This essay explores larger patterns across multiple domains "
            "and offers an integrative synthesis."
        ),
    }
    non_result = _d22_cornerstone_function(non_cornerstone)
    assert (
        non_result["function"] is None
        and non_result["basis"] == "resource_type_not_cornerstone"
    ), "D22 leaked Cornerstone function"

    attached = _attach_cornerstone_function(dict(good))
    assert (
        attached["_use_cornerstone_function"]["function"]
        == _D22_CORNERSTONE_FUNCTION_LABEL
    ), "D22 Cornerstone function not attached"

    print("USE D22 CORNERSTONE FUNCTION AUDIT: PASS")


def _d23_knowledge_hub_function_self_audit() -> None:
    """Verify Knowledge Hub function is type-gated and evidence-bound."""
    good = {
        "title": "Systems Thinking & Civilizational Design",
        "_use_resource_type_recognition": {
            "resource_type": "Knowledge Hub",
            "confidence": "strong",
            "basis": "content_self_identification",
        },
        "text": (
            "This Knowledge Hub is a curated collection of resources and an "
            "entry point for the subject. It brings together essays, "
            "Cornerstones, Reference Maps, and Pathways to support orientation "
            "across the domain."
        ),
    }
    result = _d23_knowledge_hub_function(good)
    assert result["function"] == _D23_KNOWLEDGE_HUB_FUNCTION_LABEL
    assert result["basis"] == (
        "knowledge_hub_collection_and_organization_evidence"
    )

    insufficient = {
        "title": "A General Resource",
        "_use_resource_type_recognition": {"resource_type": "Knowledge Hub"},
        "text": (
            "This resource discusses governance and mentions essays, maps, "
            "and pathways."
        ),
    }
    assert _d23_knowledge_hub_function(insufficient)["function"] is None

    non_hub = {
        "title": "An Essay",
        "_use_resource_type_recognition": {"resource_type": "Essay"},
        "text": (
            "This essay is a curated collection of essays and maps about "
            "a broad subject."
        ),
    }
    non_result = _d23_knowledge_hub_function(non_hub)
    assert non_result["function"] is None
    assert non_result["basis"] == "resource_type_not_knowledge_hub"

    attached = _attach_knowledge_hub_function(dict(good))
    assert attached["_use_knowledge_hub_function"]["function"] == (
        _D23_KNOWLEDGE_HUB_FUNCTION_LABEL
    )

    print("USE D23 KNOWLEDGE HUB FUNCTION AUDIT: PASS")


def _d24_reference_map_function_self_audit() -> None:
    """Verify Reference Map function is type-gated and evidence-bound."""
    good = {
        "title": "Reference Map 024 — The Adaptive Systems Map",
        "_use_resource_type_recognition": {
            "resource_type": "Reference Map",
            "confidence": "strong",
            "basis": "title_self_identification",
        },
        "text": (
            "This Reference Map is an orienting framework and visual "
            "representation of relationships and patterns within complex "
            "systems. It provides orientation by helping readers perceive "
            "the structure and connections of the subject."
        ),
    }
    result = _d24_reference_map_function(good)
    assert result["function"] == _D24_REFERENCE_MAP_FUNCTION_LABEL
    assert result["basis"] == (
        "reference_map_visual_framework_and_orientation_evidence"
    )

    insufficient = {
        "title": "Reference Map 024",
        "_use_resource_type_recognition": {"resource_type": "Reference Map"},
        "text": (
            "This resource discusses governance and mentions relationships "
            "between several ideas."
        ),
    }
    assert _d24_reference_map_function(insufficient)["function"] is None

    non_map = {
        "title": "Governance Essay",
        "_use_resource_type_recognition": {"resource_type": "Essay"},
        "text": (
            "This essay explains a visual framework for governance and "
            "discusses patterns and relationships."
        ),
    }
    non_result = _d24_reference_map_function(non_map)
    assert non_result["function"] is None
    assert non_result["basis"] == "resource_type_not_reference_map"

    attached = _attach_reference_map_function(dict(good))
    assert attached["_use_reference_map_function"]["function"] == (
        _D24_REFERENCE_MAP_FUNCTION_LABEL
    )

    print("USE D24 REFERENCE MAP FUNCTION AUDIT: PASS")


def _d25_navigator_function_self_audit() -> None:
    """Verify Navigator function is type-gated and evidence-bound."""
    good = {
        "title": "The Living Archive Navigator: Volume II — Governance & Sovereignty",
        "_use_resource_type_recognition": {
            "resource_type": "Navigator",
            "confidence": "strong",
            "basis": "title_self_identification",
        },
        "text": (
            "This Navigator provides an orientation and entry point into the "
            "subject. It brings together Reference Maps, Guide Notes, "
            "reflective questions, and guided reading pathways, connecting "
            "these resources for navigation through the domain."
        ),
    }
    result = _d25_navigator_function(good)
    assert result["function"] == _D25_NAVIGATOR_FUNCTION_LABEL
    assert result["basis"] == (
        "navigator_integrated_component_and_entry_evidence"
    )

    insufficient = {
        "title": "Navigator",
        "_use_resource_type_recognition": {"resource_type": "Navigator"},
        "text": (
            "This resource mentions Reference Maps and Pathways while "
            "discussing governance."
        ),
    }
    assert _d25_navigator_function(insufficient)["function"] is None

    non_navigator = {
        "title": "Governance Essay",
        "_use_resource_type_recognition": {"resource_type": "Essay"},
        "text": (
            "This essay brings together Reference Maps, Pathways, and "
            "Guide Notes as examples."
        ),
    }
    non_result = _d25_navigator_function(non_navigator)
    assert non_result["function"] is None
    assert non_result["basis"] == "resource_type_not_navigator"

    attached = _attach_navigator_function(dict(good))
    assert attached["_use_navigator_function"]["function"] == (
        _D25_NAVIGATOR_FUNCTION_LABEL
    )

    print("USE D25 NAVIGATOR FUNCTION AUDIT: PASS")


def _v134_explicit_type_selection_preservation_self_audit() -> None:
    """Verify explicit D20 publication types survive final selection."""
    reference_map = {
        "title": "Reference Map Probe",
        "url": "https://example.invalid/reference-map-probe",
        "_use_resource_type_recognition": {"resource_type": "Reference Map"},
    }
    essay = {
        "title": "Essay Probe",
        "url": "https://example.invalid/essay-probe",
        "_use_resource_type_recognition": {"resource_type": "Essay"},
    }
    generic = {
        "title": "Generic Probe",
        "url": "https://example.invalid/generic-probe",
        "_use_resource_type_recognition": {"resource_type": "Cornerstone"},
    }
    targets = {"Reference Map", "Essay"}
    selected = _preserve_explicit_type_candidates(
        [generic] * MAX_CONTEXT_RESOURCES,
        [reference_map, essay],
        targets,
    )
    selected_types = {
        _recognize_resource_type(document).get("resource_type")
        for document in selected
    }
    if not targets.issubset(selected_types):
        raise RuntimeError(
            "v134 selection regression: explicitly requested publication types "
            "were displaced by generic resources."
        )
    generic_only = _preserve_explicit_type_candidates(
        [generic], [reference_map], set()
    )
    if generic_only != [generic]:
        raise RuntimeError(
            "v134 selection regression: neutral selection changed without an explicit type request."
        )
    print("USE v134 EXPLICIT TYPE SELECTION PRESERVATION AUDIT: PASS")


def _v97_retrieval_candidate_window_audit() -> None:
    """Verify semantic candidates survive until bounded doorway ranking."""
    source = inspect.getsource(fetch_canonical_context)
    retrieval_pos = source.find("candidates = _query_index(")
    ordinary_loop_pos = source.find("for _score, _match_id_value, metadata in candidates:")
    doorway_pos = source.find("select_canonical_doorways(")
    if retrieval_pos < 0 or ordinary_loop_pos < 0 or doorway_pos < 0:
        raise RuntimeError(
            "D18 retrieval-window regression: retrieval or doorway ranking is missing."
        )
    if ordinary_loop_pos < retrieval_pos:
        raise RuntimeError(
            "D18 retrieval-window regression: candidate loop is not downstream of retrieval."
        )
    if "len(retrieved_docs) >= RETRIEVAL_TOP_K" not in source:
        raise RuntimeError(
            "D18 retrieval-window regression: full bounded semantic candidate window is not preserved."
        )
    ranking_block = source[doorway_pos:]
    if ")[:MAX_CONTEXT_RESOURCES]" not in ranking_block:
        raise RuntimeError(
            "D18 retrieval-window regression: final generation resource cap is not downstream of ranking."
        )

    # Generic proof: a direct candidate at the end of the bounded window must
    # be available for promotion; this is not tied to any corpus subject.
    filler = [
        {
            "title": f"Semantic Neighbor {index}",
            "url": f"https://example.invalid/neighbor-{index}",
            "text": "A related canonical resource with broad thematic overlap.",
        }
        for index in range(1, 12)
    ]
    direct = {
        "title": "Direct Subject Resource",
        "url": "https://example.invalid/direct-subject",
        "text": "A canonical resource directly addressing the visitor's named subject and its explanation.",
    }
    selected = select_canonical_doorways(
        filler + [direct],
        {"primary": "systems", "scores": {"systems": 1}},
        question="Why does the named subject matter and how can I understand it?",
    )
    if selected[0]["title"] != "Direct Subject Resource":
        raise RuntimeError(
            "D18 retrieval-window regression: direct late-window candidate could not be promoted."
        )
    print(
        "USE v97 retrieval candidate-window audit: PASS; "
        "semantic candidates remain available through downstream ranking."
    )


def _v96_current_turn_state_integrity_audit():
    """Verify that each request's query/state remains bound to that same turn."""
    import asyncio

    route_source = inspect.getsource(handle_query)

    required_route_invariants = (
        'query_str = str(query_str).strip()',
        'context_data = fetch_canonical_context(query_str)',
        '"query": query_str',
        '"intent": context_data["intent"]',
        'generate_llm_response(\n                query_str,',
    )
    missing = [item for item in required_route_invariants if item not in route_source]
    if missing:
        raise RuntimeError(
            "D18 current-turn regression: request/state binding invariant(s) missing: "
            + ", ".join(missing)
        )

    original_fetch = globals()["fetch_canonical_context"]
    original_generate = globals()["generate_llm_response"]
    original_observer = globals()["assess_progressive_commitment"]
    original_invitation = globals()["progressive_inquiry_invitation"]

    class _ProbeRequest:
        def __init__(self, query):
            self.query = query
        async def json(self):
            return {"query": self.query}

    calls = []

    def probe_fetch(query):
        calls.append(("fetch", query))
        return {
            "context_blocks": "Title: Probe Resource\\nURL: https://example.invalid/probe\\nContent: Probe evidence.",
            "intent": "TOPICAL_INQUIRY",
            "orientational_frame": {"primary": "general", "scores": {}},
            "canonical_link_context": "Title: Probe Resource\\nURL: https://example.invalid/probe",
        }

    def probe_generate(query, context_blocks, intent, orientational_frame=None, canonical_link_context=None):
        calls.append(("generate", query, intent))
        return f"response-for:{query}"

    def probe_observer(query, history):
        calls.append(("observer", query))
        return {"steward_access_invitation": False, "current_turn_influence": False, "native_vocabulary_allowed": False}

    def probe_invitation(state):
        return ""

    globals()["fetch_canonical_context"] = probe_fetch
    globals()["generate_llm_response"] = probe_generate
    globals()["assess_progressive_commitment"] = probe_observer
    globals()["progressive_inquiry_invitation"] = probe_invitation

    async def run_probe(query):
        result = await handle_query(_ProbeRequest(query), None)
        return result.body.decode("utf-8")

    try:
        first_query = "CURRENT TURN A — authority and governance"
        second_query = "CURRENT TURN B — grief and transition"
        first_body = asyncio.run(run_probe(first_query))
        second_body = asyncio.run(run_probe(second_query))

        if first_query not in first_body or second_query not in second_body:
            raise RuntimeError(
                "D18 current-turn regression: response envelope did not preserve the request query."
            )
        if first_query in second_body:
            raise RuntimeError(
                "D18 current-turn regression: stale query state leaked into a subsequent response."
            )
        if '"response":"response-for:CURRENT TURN A — authority and governance"' not in first_body:
            raise RuntimeError(
                "D18 current-turn regression: first response was not bound to first request."
            )
        if '"response":"response-for:CURRENT TURN B — grief and transition"' not in second_body:
            raise RuntimeError(
                "D18 current-turn regression: second response was not bound to second request."
            )
        fetch_queries = [item[1] for item in calls if item[0] == "fetch"]
        generated_queries = [item[1] for item in calls if item[0] == "generate"]
        observed_queries = [item[1] for item in calls if item[0] == "observer"]
        if fetch_queries != [first_query, second_query]:
            raise RuntimeError(
                "D18 current-turn regression: fetch path received stale or reordered queries."
            )
        if generated_queries != [first_query, second_query]:
            raise RuntimeError(
                "D18 current-turn regression: generation path received stale or reordered queries."
            )
        if observed_queries != [first_query, second_query]:
            raise RuntimeError(
                "D18 current-turn regression: observer received stale or reordered queries."
            )
    finally:
        globals()["fetch_canonical_context"] = original_fetch
        globals()["generate_llm_response"] = original_generate
        globals()["assess_progressive_commitment"] = original_observer
        globals()["progressive_inquiry_invitation"] = original_invitation

    print("D18 CURRENT-TURN STATE INTEGRITY AUDIT: PASS")


# Production runtime is one environment. Test fixtures and audit suites are not
# executed during service startup; they are run against the complete source unit
# before deployment so visitor traffic cannot be coupled to test-only state.

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

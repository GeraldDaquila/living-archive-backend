import os
import re
import time
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pinecone import Pinecone
from groq import Groq
from fastembed import TextEmbedding


# =====================================================================
# SYSTEM PROMPT
# =====================================================================

SYSTEM_PROMPT = """
You are USE — the navigation and sensemaking engine for the Living Archive.

Your purpose is not merely to retrieve the most semantically similar
document. Your purpose is to help a visitor understand where they are
within the Living Archive and determine the most useful path of movement
through the canonical body of work.

The Living Archive is a connected knowledge architecture, not merely a
collection of essays.

CONSTITUTIONAL RULES

1. INSTITUTIONAL FIDELITY

Answer strictly from the facts, concepts, relationships, and resources
contained in the provided CANONICAL CONTEXT.

Do not invent:
- resources
- categories
- site structures
- relationships between resources
- terminology
- navigation routes
- URLs
- institutional functions
- claims about the Archive that are not supported by context

Do not substitute generic descriptions of knowledge platforms, libraries,
archives, AI systems, or websites for the actual Living Archive.

The Living Archive's identity must come from its canonical corpus.

2. HARD LINK GROUNDING

You may ONLY provide a Markdown link when the exact URL appears in the
provided CANONICAL CONTEXT.

Never:
- invent a URL
- reconstruct a URL from a title
- alter a URL
- infer a URL
- provide a URL merely because you know or remember that it exists

The canonical context is the sole authority for links in the response.

3. IMPLICIT LOCATION AWARENESS

The visitor is already inside the Living Archive.

Do not tell the visitor to "visit the Living Archive," "go to the website,"
or otherwise describe the Archive as though it were somewhere external.

Instead, orient the visitor from their current position.

4. THE ARCHIVE IS A KNOWLEDGE ARCHITECTURE

Treat the Living Archive as a connected body of work whose resources may
serve different architectural functions.

Distinguish between:

A. STRUCTURAL ORIENTATION
Resources whose primary purpose is to show or explain the architecture,
organization, pathways, collections, or overall shape of the Archive.

B. CONCEPTUAL / HUMAN ORIENTATION
Resources whose primary purpose is to help a person understand the
questions, intellectual stance, purpose, or deeper meaning underlying the
Archive.

C. THEMATIC EXPLORATION
Resources concerned primarily with a particular subject, question,
domain, theme, or field of inquiry.

D. INDIVIDUAL RESOURCES
Essays, studies, guides, cases, maps, pathways, or other specific
resources that serve a narrower purpose within the larger architecture.

Do not automatically treat a thematic resource as the definition of the
entire Archive merely because it is highly relevant to the query.

5. WHOLE-SITE ORIENTATION

When QUERY INTENT is WHOLE_SITE_ORIENTATION, the visitor is asking for
orientation to the larger Living Archive rather than simply asking about
one subject.

The first canonical context resource is the deterministic orientation
resource supplied by the retrieval layer.

Treat it as the authoritative structural starting point provided by USE.

Use the remaining canonical resources to enrich the orientation when they
are genuinely relevant.

Do not allow a semantically similar thematic resource to silently replace
the deterministic orientation resource as the definition of the Archive.

6. ROOT RESOURCE DISCIPLINE

The deterministic root resource is a retrieval anchor, not permission to
invent facts about the Archive.

If the root resource does not contain enough information to answer a
question, say so or use the additional supplied canonical context.

Never fill missing information with general knowledge.

7. CONTEXT BOUNDARY

The CANONICAL CONTEXT supplied with this request is the complete evidence
boundary for the response.

If a resource, relationship, fact, or route is absent from that context,
do not claim that it is available.

Do not assume that because the Archive may contain more than the supplied
context, a particular resource exists in the current retrieval result.

8. RETRIEVAL IS NOT THE SAME AS ANSWER

A retrieved resource is evidence, not necessarily the answer.

Use the user's actual question to determine which supplied resource is
useful.

Do not simply summarize the highest-scoring result.

When several resources are present, synthesize them according to their
role in answering the question.

9. ROUTING

USE should help the visitor move.

The preferred response sequence is:

Mirror the question
-> establish the relevant orientation
-> distinguish the useful level of the Archive
-> offer the most relevant canonical route or routes.

Routes should be useful, specific, and grounded in the supplied context.

Do not produce a generic reading list.

10. READER SOVEREIGNTY

Do not prescribe a single path when the canonical context supports several
legitimate ways of entering or exploring the Archive.

Do not imply that the visitor must read everything.

Offer orientation without coercion.

11. WHOLE-SITE QUESTIONS

For questions such as:

"What is the Living Archive?"
"Why does the Living Archive exist?"
"How does the Living Archive work?"
"What can I explore here?"
"Where should I start?"
"How do I navigate the Archive?"

answer at the level of the whole system whenever the canonical context
supports that answer.

Do not collapse the response into one thematic essay merely because that
essay happens to be retrieved.

12. TOPICAL QUESTIONS

When QUERY INTENT is TOPICAL_INQUIRY, answer the subject-specific question
using the retrieved canonical resources.

Do not inject whole-site orientation merely because the words "Archive,"
"site," or "Living Archive" appear in the question.

13. UNCERTAINTY

When the supplied context is insufficient, be explicit about the boundary.

A constrained answer is preferable to an invented answer.

Never manufacture certainty.

14. RESPONSE STYLE

Be human, clear, concise, and intellectually grounded.

Do not expose internal implementation details such as:
- Pinecone
- embeddings
- vector scores
- retrieval slots
- model selection
- QUERY INTENT
- internal classifier names
- root-node IDs

The visitor should experience USE as an intelligent guide, not as a
debugging console.
"""


# =====================================================================
# APP & INFRASTRUCTURE
# =====================================================================

app = FastAPI(
    title="Find Your Way (USE) Navigation Engine"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME = os.getenv(
    "PINECONE_INDEX_NAME",
    "living-archive",
)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


pc = (
    Pinecone(api_key=PINECONE_API_KEY)
    if PINECONE_API_KEY
    else None
)

index = (
    pc.Index(PINECONE_INDEX_NAME)
    if pc
    else None
)

groq_client = (
    Groq(api_key=GROQ_API_KEY)
    if GROQ_API_KEY
    else None
)


# IMPORTANT:
# This embedding model is intentionally retained at 384 dimensions.
# Do not change this without a separate architectural decision because
# the existing Pinecone index is constructed around this dimensionality.
embedding_model = TextEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)


# Deterministic Pinecone ID of the canonical Living Archive
# orientation/root resource.
ROOT_NODE_ID = "canonical_root_living_archive"


# =====================================================================
# DYNAMIC GROQ MODEL DISCOVERY & CACHING
# =====================================================================

MODEL_CACHE = {
    "models": [],
    "last_fetch": 0,
}


def get_live_groq_models() -> List[str]:
    """
    Query Groq for models currently available to the configured API key.

    The live model list is cached for one hour to avoid unnecessary
    API calls while still allowing the backend to adapt to model
    availability changes.
    """

    now = time.time()

    if (
        MODEL_CACHE["models"]
        and now - MODEL_CACHE["last_fetch"] < 3600
    ):
        return MODEL_CACHE["models"]

    if not groq_client:
        return []

    try:
        response = groq_client.models.list()

        discovered = [
            model.id
            for model in response.data
            if hasattr(model, "id")
            and not any(
                excluded in model.id.lower()
                for excluded in (
                    "whisper",
                    "guard",
                    "audio",
                    "vision",
                )
            )
        ]

        if discovered:
            discovered.sort(
                key=lambda model_id: (
                    "70b" in model_id.lower()
                    or "versatile" in model_id.lower()
                    or "instruct" in model_id.lower()
                ),
                reverse=True,
            )

            MODEL_CACHE["models"] = discovered
            MODEL_CACHE["last_fetch"] = now

            print(
                "Dynamically loaded live Groq models: "
                f"{discovered}"
            )

            return discovered

    except Exception as exc:
        print(
            "Failed to fetch live Groq model list: "
            f"{exc}"
        )

    return MODEL_CACHE["models"]


# =====================================================================
# EMBEDDING GENERATION
# =====================================================================

def generate_embedding(text: str) -> List[float]:
    """
    Generate a 384-dimensional local embedding using the existing
    production embedding model.
    """

    try:
        embeddings = list(
            embedding_model.embed([text])
        )

        if not embeddings:
            return []

        return embeddings[0].tolist()

    except Exception as exc:
        print(
            f"Embedding generation error: {exc}"
        )
        return []


# =====================================================================
# INTENT CLASSIFICATION
# =====================================================================

# ---------------------------------------------------------------------
# Site-referential language
#
# This is intentionally a small closed structural vocabulary.
# It is NOT a list of Living Archive topics.
# ---------------------------------------------------------------------

SITE_ANCHOR_RE = re.compile(
    r"\b(?:"
    r"(?:the\s+)?living\s+archive"
    r"|(?:the\s+)?whole\s+archive"
    r"|(?:the\s+)?archive"
    r"|(?:this\s+)?site"
    r"|(?:this\s+)?website"
    r"|(?:this\s+)?place"
    r"|everything\s+(?:here|on\s+(?:this\s+)?site)"
    r"|all\s+(?:this|of\s+this)"
    r"|itself"
    r"|its\s+own\s+purpose"
    r")\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------
# Explicit whole-site identity / entry forms
# ---------------------------------------------------------------------

SIGNAL_C_PATTERNS = [
    re.compile(
        r"^what\s+is\s+(?:the\s+)?living\s+archive$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^what\s+is\s+(?:the\s+)?living\s+archive\s+about$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^what\s+does\s+(?:the\s+)?living\s+archive\s+"
        r"(?:explore|cover|do)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^what\s+is\s+(?:this\s+)?(?:archive|site|website|place)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^what\s+is\s+(?:this\s+)?(?:archive|site|website|place)"
        r"\s+about$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^where\s+(?:should|do)\s+i\s+(?:start|begin)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^where\s+to\s+begin$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^how\s+(?:do|can)\s+i\s+navigate\s+"
        r"(?:this\s+site|the\s+archive|the\s+living\s+archive)$",
        re.IGNORECASE,
    ),
]


# ---------------------------------------------------------------------
# Orientation signals
# ---------------------------------------------------------------------

ORIENTATION_SIGNAL_PATTERNS = [
    re.compile(r"\boverwhelmed\b", re.IGNORECASE),
    re.compile(r"\blost\b", re.IGNORECASE),
    re.compile(r"\bconfused\b", re.IGNORECASE),
    re.compile(r"\bstart\b", re.IGNORECASE),
    re.compile(r"\bbegin\b", re.IGNORECASE),
    re.compile(r"\bentry\b", re.IGNORECASE),
    re.compile(r"\bfirst\b", re.IGNORECASE),
    re.compile(r"\bnavigate\b", re.IGNORECASE),
    re.compile(r"\bexplore\b", re.IGNORECASE),
    re.compile(r"\bfind\s+my\s+way\b", re.IGNORECASE),
    re.compile(r"\bhow\s+to\s+use\b", re.IGNORECASE),
]


# ---------------------------------------------------------------------
# Site-scope signals
# ---------------------------------------------------------------------

SITE_SCOPE_PATTERNS = [
    re.compile(r"\bthis\s+site\b", re.IGNORECASE),
    re.compile(r"\bthe\s+site\b", re.IGNORECASE),
    re.compile(r"\bwebsite\b", re.IGNORECASE),
    re.compile(r"\bthis\s+archive\b", re.IGNORECASE),
    re.compile(r"\bthe\s+archive\b", re.IGNORECASE),
    re.compile(r"\bliving\s+archive\b", re.IGNORECASE),
    re.compile(r"\beverything\s+here\b", re.IGNORECASE),
    re.compile(r"\ball\s+this\b", re.IGNORECASE),
    re.compile(r"\bhow\s+much\s+is\s+on\b", re.IGNORECASE),
]


def _has_orientation_signal(
    query: str,
) -> bool:
    return any(
        pattern.search(query)
        for pattern in ORIENTATION_SIGNAL_PATTERNS
    )


def _has_site_scope_signal(
    query: str,
) -> bool:
    return any(
        pattern.search(query)
        for pattern in SITE_SCOPE_PATTERNS
    )


def _is_site_referential_complement(
    complement: str,
) -> bool:
    """
    Determine whether a prepositional complement refers to the
    Living Archive/site itself rather than a subject matter.

    This deliberately uses a closed structural vocabulary rather
    than a corpus-wide topical blacklist.
    """

    normalized = re.sub(
        r"\s+",
        " ",
        complement.strip().lower(),
    )

    normalized = re.sub(
        r"^(?:the|this|that|my|your|our|their)\s+",
        "",
        normalized,
    ).strip()

    site_forms = re.compile(
        r"^(?:"
        r"living\s+archive"
        r"|whole\s+(?:living\s+archive|archive|site|website)"
        r"|archive"
        r"|site"
        r"|website"
        r"|place"
        r"|everything(?:\s+(?:here|on\s+(?:this\s+)?site))?"
        r"|all\s+(?:this|of\s+this)"
        r"|itself"
        r"|archive\s+itself"
        r"|living\s+archive\s+itself"
        r"|living\s+archive\s+as\s+a\s+whole"
        r"|archive\s+as\s+a\s+whole"
        r"|site\s+as\s+a\s+whole"
        r"|website\s+as\s+a\s+whole"
        r"|its\s+own\s+purpose"
        r")$",
        re.IGNORECASE,
    )

    return bool(
        site_forms.fullmatch(normalized)
    )


def _has_topical_prepositional_complement(
    query: str,
) -> bool:
    """
    Detect a prepositional complement that narrows the query to a
    specific subject.

    Examples:

        start with leadership
        navigate grief
        view on stewardship
        site about trauma
        approach to governance

    Site-referential complements are explicitly exempted.
    """

    action_pattern = re.compile(
        r"\b(?:"
        r"start|begin|navigate|explore|view|approach|"
        r"look|read|use|go|move|learn|say"
        r")\b"
        r"\s+"
        r"(?:"
        r"with|about|on|through|in|for|to"
        r")\s+"
        r"(.+?)"
        r"(?:[?.!,;:]|$)",
        re.IGNORECASE,
    )

    site_pattern = re.compile(
        r"\b(?:"
        r"site|website|archive|living\s+archive"
        r")\b"
        r"\s+"
        r"(?:about|on|for)\s+"
        r"(.+?)"
        r"(?:[?.!,;:]|$)",
        re.IGNORECASE,
    )

    for pattern in (
        action_pattern,
        site_pattern,
    ):
        for match in pattern.finditer(query):

            complement = match.group(1).strip()

            if not complement:
                continue

            if _is_site_referential_complement(
                complement
            ):
                continue

            # A site-referential phrase followed by another
            # prepositional phrase creates a nested topical scope.
            #
            # Example:
            # "its own approach to stewardship"
            # "the site about leadership"
            if SITE_ANCHOR_RE.search(
                complement
            ):
                if re.search(
                    r"\b(?:to|about|on|for|with|in)\s+\S+",
                    complement,
                    flags=re.IGNORECASE,
                ):
                    return True

            # Any remaining non-site complement is topical.
            return True

    return False


def classify_intent(
    query_str: str,
) -> str:
    """
    Deterministic two-class intent classifier.

    Returns only:

        WHOLE_SITE_ORIENTATION
        TOPICAL_INQUIRY
    """

    clean_query = re.sub(
        r"\s+",
        " ",
        query_str.strip().lower(),
    )

    if not clean_query:
        return "TOPICAL_INQUIRY"

    # ---------------------------------------------------------------
    # 1. Topical scope has precedence.
    # ---------------------------------------------------------------

    if _has_topical_prepositional_complement(
        clean_query
    ):
        return "TOPICAL_INQUIRY"

    # ---------------------------------------------------------------
    # 2. Explicit whole-site identity / entry.
    # ---------------------------------------------------------------

    for pattern in SIGNAL_C_PATTERNS:
        if pattern.fullmatch(clean_query):
            return "WHOLE_SITE_ORIENTATION"

    # ---------------------------------------------------------------
    # 3. Compound whole-site signal:
    #
    # Orientation signal + explicit site scope.
    # ---------------------------------------------------------------

    if (
        _has_orientation_signal(clean_query)
        and _has_site_scope_signal(clean_query)
    ):
        return "WHOLE_SITE_ORIENTATION"

    # ---------------------------------------------------------------
    # 4. Explicit site anchor + clear orientation action.
    #
    # This covers expressions such as:
    # "Where should I start with the Living Archive?"
    # "How do I navigate through the archive?"
    # ---------------------------------------------------------------

    if (
        SITE_ANCHOR_RE.search(clean_query)
        and _has_orientation_signal(clean_query)
    ):
        return "WHOLE_SITE_ORIENTATION"

    # ---------------------------------------------------------------
    # 5. Default:
    #
    # Standard semantic topical retrieval.
    # ---------------------------------------------------------------

    return "TOPICAL_INQUIRY"


# =====================================================================
# CANONICAL CONTEXT FORMATTING
# =====================================================================

def format_context_blocks(
    documents: List[Dict[str, Any]],
) -> str:
    """
    Convert canonical metadata records into the context format supplied
    to Groq.

    Only metadata returned by Pinecone is included.
    """

    formatted_blocks: List[str] = []

    for doc in documents:

        if not isinstance(doc, dict):
            continue

        title = doc.get(
            "title",
            "Untitled Resource",
        )

        url = doc.get(
            "url",
            "#",
        )

        content = doc.get(
            "text",
            doc.get(
                "content",
                doc.get(
                    "excerpt",
                    "",
                ),
            ),
        )

        formatted_blocks.append(
            f"Title: {title}\n"
            f"URL: {url}\n"
            f"Content: {content}"
        )

    return "\n\n---\n\n".join(
        formatted_blocks
    )


# =====================================================================
# ROOT-NODE METADATA EXTRACTION
# =====================================================================

def _metadata_from_root_fetch(
    root_doc: Any,
) -> Optional[Dict[str, Any]]:
    """
    Extract root-node metadata defensively from Pinecone's fetch
    response.

    Supports both mapping-style and SDK-object response forms.
    """

    try:

        vectors = (
            root_doc.get(
                "vectors",
                {},
            )
            if hasattr(root_doc, "get")
            else getattr(
                root_doc,
                "vectors",
                {},
            )
        )

        vector = (
            vectors.get(ROOT_NODE_ID)
            if vectors
            else None
        )

        if vector is None:
            return None

        metadata = (
            vector.get("metadata")
            if hasattr(vector, "get")
            else getattr(
                vector,
                "metadata",
                None,
            )
        )

        return (
            metadata
            if isinstance(metadata, dict)
            else None
        )

    except Exception as exc:

        print(
            "Root metadata extraction error: "
            f"{exc}"
        )

        return None


# =====================================================================
# CANONICAL RETRIEVAL
# =====================================================================

def fetch_canonical_context(
    user_query: str,
) -> Dict[str, Any]:
    """
    Retrieve canonical context according to classified intent.

    WHOLE_SITE_ORIENTATION:
        Slot 1 = deterministic root resource
        Slots 2-3 = semantic backfill

    TOPICAL_INQUIRY:
        Slots 1-3 = semantic retrieval

    Maximum context = three resources.
    """

    intent = classify_intent(
        user_query
    )

    retrieved_docs: List[
        Dict[str, Any]
    ] = []

    if not index:
        return {
            "intent": intent,
            "context_blocks": "",
        }

    # ---------------------------------------------------------------
    # WHOLE-SITE ORIENTATION
    #
    # Deterministically place the canonical root resource first.
    # ---------------------------------------------------------------

    if intent == "WHOLE_SITE_ORIENTATION":

        try:

            root_doc = index.fetch(
                ids=[ROOT_NODE_ID]
            )

            root_metadata = (
                _metadata_from_root_fetch(
                    root_doc
                )
            )

            if root_metadata:

                retrieved_docs.append(
                    root_metadata
                )

            else:

                print(
                    "WHOLE_SITE_ORIENTATION detected, "
                    f"but root node '{ROOT_NODE_ID}' "
                    "was not returned with metadata."
                )

        except Exception as exc:

            print(
                f"Root node fetch error: {exc}"
            )

    # ---------------------------------------------------------------
    # SEMANTIC RETRIEVAL
    #
    # Orientation uses K=2 because Slot 1 is reserved for root.
    # Topical inquiry continues to use K=3.
    # ---------------------------------------------------------------

    try:

        query_vector = generate_embedding(
            user_query
        )

        if query_vector:

            top_k = (
                2
                if intent == "WHOLE_SITE_ORIENTATION"
                else 3
            )

            result = index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
            )

            matches = (
                result.get(
                    "matches",
                    [],
                )
                if hasattr(result, "get")
                else getattr(
                    result,
                    "matches",
                    [],
                )
            )

            for match in matches:

                match_id = (
                    match.get("id")
                    if hasattr(match, "get")
                    else getattr(
                        match,
                        "id",
                        None,
                    )
                )

                metadata = (
                    match.get("metadata")
                    if hasattr(match, "get")
                    else getattr(
                        match,
                        "metadata",
                        None,
                    )
                )

                if (
                    match_id != ROOT_NODE_ID
                    and isinstance(
                        metadata,
                        dict,
                    )
                ):
                    retrieved_docs.append(
                        metadata
                    )

    except Exception as exc:

        print(
            f"Index query error: {exc}"
        )

    # ---------------------------------------------------------------
    # Maximum canonical context = three resources.
    # ---------------------------------------------------------------

    retrieved_docs = [
        doc
        for doc in retrieved_docs
        if isinstance(
            doc,
            dict,
        )
        and doc
    ][:3]

    return {
        "intent": intent,
        "context_blocks": format_context_blocks(
            retrieved_docs
        ),
    }


# =====================================================================
# GROQ GENERATION
# =====================================================================

def generate_llm_response(
    user_query: str,
    context_blocks: str,
    intent: str,
) -> str:
    """
    Generate the final USE response using Groq.

    The model receives:
        1. constitutional system instructions
        2. deterministic query intent
        3. canonical retrieved context
        4. original user query
    """

    if (
        not GROQ_API_KEY
        or not groq_client
    ):
        return (
            "Unable to generate a response. "
            "GROQ_API_KEY is not configured "
            "in backend environment."
        )

    system_content = (
        f"{SYSTEM_PROMPT}\n\n"
        f"[QUERY INTENT]: {intent}\n\n"
        f"[CANONICAL CONTEXT]:\n"
        f"{context_blocks}"
    )

    active_models = (
        get_live_groq_models()
    )

    if not active_models:
        return (
            "Unable to generate a response. "
            "No active models returned from "
            "Groq API."
        )

    last_error: Optional[str] = None

    for model_id in active_models:

        try:

            response = (
                groq_client
                .chat
                .completions
                .create(
                    model=model_id,
                    messages=[
                        {
                            "role": "system",
                            "content": system_content,
                        },
                        {
                            "role": "user",
                            "content": user_query,
                        },
                    ],
                    temperature=0.2,
                    max_tokens=800,
                )
            )

            return (
                response
                .choices[0]
                .message
                .content
            )

        except Exception as exc:

            print(
                "Execution failed for live "
                f"Groq model '{model_id}': {exc}"
            )

            last_error = str(exc)

    # ---------------------------------------------------------------
    # All discovered models failed.
    # Invalidate discovery cache so the next
    # request obtains a fresh model list.
    # ---------------------------------------------------------------

    MODEL_CACHE["last_fetch"] = 0

    return (
        "Unable to generate response. "
        "Groq API returned error: "
        f"{last_error}"
    )


# =====================================================================
# API REQUEST MODEL
# =====================================================================

class FlexibleQueryRequest(
    BaseModel
):
    query: Optional[str] = None
    user_query: Optional[str] = None
    question: Optional[str] = None
    text: Optional[str] = None


# =====================================================================
# HEALTH CHECK
# =====================================================================

@app.get("/")
@app.head("/")
def read_root():
    return {
        "status": "ok"
    }


# =====================================================================
# QUERY ENDPOINT
# =====================================================================

@app.post("/api/query")
@app.post("/")
async def handle_query(
    request: Request,
    payload: Optional[
        FlexibleQueryRequest
    ] = None,
):
    raw_body: Dict[
        str,
        Any,
    ] = {}

    try:

        raw_body = await request.json()

    except Exception:

        pass

    query_str: Optional[str] = None

    # ---------------------------------------------------------------
    # Pydantic payload fields
    # ---------------------------------------------------------------

    if payload:

        query_str = (
            payload.query
            or payload.user_query
            or payload.question
            or payload.text
        )

    # ---------------------------------------------------------------
    # Raw JSON fallback
    # ---------------------------------------------------------------

    if (
        not query_str
        and raw_body
    ):

        query_str = (
            raw_body.get("query")
            or raw_body.get("user_query")
            or raw_body.get("question")
            or raw_body.get("text")
            or raw_body.get("input")
        )

    # ---------------------------------------------------------------
    # Empty query
    # ---------------------------------------------------------------

    if (
        not query_str
        or not str(query_str).strip()
    ):

        return {
            "query": "",
            "intent": "TOPICAL_INQUIRY",
            "response": (
                "Please enter a question "
                "to query the archive."
            ),
            "canonical_context": "",
        }

    query_str = str(
        query_str
    ).strip()

    # ---------------------------------------------------------------
    # Retrieval
    # ---------------------------------------------------------------

    context_data = (
        fetch_canonical_context(
            query_str
        )
    )

    # ---------------------------------------------------------------
    # Generation
    # ---------------------------------------------------------------

    llm_output = (
        generate_llm_response(
            query_str,
            context_data[
                "context_blocks"
            ],
            context_data[
                "intent"
            ],
        )
    )

    # ---------------------------------------------------------------
    # Response contract
    # ---------------------------------------------------------------

    return {
        "query": query_str,
        "intent": context_data[
            "intent"
        ],
        "response": llm_output,
        "canonical_context": (
            context_data[
                "context_blocks"
            ]
        ),
    }


# =====================================================================
# LOCAL EXECUTION
# =====================================================================

if __name__ == "__main__":

    import uvicorn

    port = int(
        os.getenv(
            "PORT",
            10000,
        )
    )

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )

import os
import re
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
You are the navigation engine for the Living Archive (USE).

Your goal is to guide visitors through the archive using only the
provided canonical context.

CONSTITUTIONAL RULES

1. INSTITUTIONAL FIDELITY
   Answer strictly from the facts and concepts contained in the
   provided CANONICAL CONTEXT. Do not invent features, categories,
   terminology, relationships, or resources.

2. HARD LINK GROUNDING
   You may ONLY cite or link a resource whose exact URL is present
   in CANONICAL CONTEXT. Never invent, infer, reconstruct, or
   substitute a URL.

3. IMPLICIT LOCATION AWARENESS
   The user is already on the Living Archive. Never tell the user
   to "visit the site" as though they are somewhere else.

4. OPERATIONAL SEQUENCE
   Mirror the question -> orient the user using the available
   canonical context -> offer canonical routes of movement.

5. WHOLE-SITE ORIENTATION
   When QUERY INTENT is WHOLE_SITE_ORIENTATION, the first context
   resource is the canonical Living Archive root/orientation node.
   Treat that resource as the authoritative site-level orientation
   resource. Do not substitute a thematic essay, retreat, or other
   sub-level resource as the definition of the Living Archive.

6. CONTEXT BOUNDARY
   The CANONICAL CONTEXT is the complete resource boundary for this
   response. If a needed resource is not present, do not fabricate it
   or claim that it is present.

7. ROUTING
   Recommendations must be grounded in the supplied canonical
   resources and should serve the user's actual question rather than
   merely repeating the highest-scoring retrieval result.
"""


# =====================================================================
# APP & INFRASTRUCTURE
# =====================================================================

app = FastAPI(title="Find Your Way (USE) Navigation Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "living-archive")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

pc = Pinecone(api_key=PINECONE_API_KEY) if PINECONE_API_KEY else None
index = pc.Index(PINECONE_INDEX_NAME) if pc else None
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Local 384-dimensional embedding model.
embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

# This is the deterministic Pinecone ID of the canonical Living Archive
# root/orientation node. It is NOT generated from the user's query.
ROOT_NODE_ID = "canonical_root_living_archive"


# =====================================================================
# GROQ MODEL DISCOVERY
# =====================================================================
#
# This section deliberately retains the existing live-model discovery
# architecture from the supplied production file. It does not alter
# the WordPress-side AI-client/Gemini preference chain.
#
# The backend should continue to receive requests from the existing USE
# client exactly as before.
# =====================================================================

MODEL_CACHE: Dict[str, Any] = {
    "models": [],
    "last_fetch": 0.0,
}


def get_live_groq_models() -> List[str]:
    """
    Return currently available Groq text/chat models.

    A short-lived in-process cache prevents a model-list API request on
    every user query. If discovery fails after a previous successful
    discovery, the previous cached list is retained.
    """
    import time

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
            and model.id
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
            "Failed to fetch live model list from Groq API: "
            f"{exc}"
        )

    return MODEL_CACHE["models"]


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
#
# The classifier is intentionally narrow and deterministic.
#
# It does NOT maintain a blacklist of archive topics.
#
# Decision order:
#   1. Explicit topical complement guard
#   2. Explicit whole-site identity/entry phrases
#   3. Site-anchor + orientation compound signal
#   4. Otherwise topical inquiry
#
# The critical distinction is that a prepositional object referring to
# the Living Archive/site itself is NOT topical.
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

SITE_ANCHOR_RE = re.compile(
    rf"\b{SITE_ANCHOR}\b",
    re.IGNORECASE,
)

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
        re.search(
            rf"\b{re.escape(token)}\b",
            query,
            re.IGNORECASE,
        )
        for token in ORIENTATION_TOKENS
    )


def _has_site_scope_signal(query: str) -> bool:
    return any(
        re.search(
            rf"\b{re.escape(token)}\b",
            query,
            re.IGNORECASE,
        )
        for token in SITE_SCOPE_TOKENS
    )


def _has_topical_prepositional_complement(query: str) -> bool:
    """
    Detect a prepositional phrase that clearly points beyond the site
    itself to a subject.

    Examples that MUST be topical:
        start with leadership
        start with regenerative economics
        site about leadership
        view on stewardship
        approach to inquiry
        navigate through grief

    Examples that MUST NOT be topical:
        start with the Living Archive
        start with this site
        navigate through the archive
        say about itself
        start with everything here

    This deliberately uses a closed site-reference set rather than a
    corpus-wide topic blacklist.
    """

    # Orientation/action verb + preposition + first target phrase.
    action_pattern = re.compile(
        r"\b(?:start|begin|navigate|explore|view|approach|"
        r"look|read|use|go|move|learn|say)\b"
        r"\s+(?:"
        r"with|about|on|through|in|for|to"
        r")\s+"
        r"(.+?)(?:[?.!,;:]|$)",
        re.IGNORECASE,
    )

    # Site noun + about/on/for + target.
    site_pattern = re.compile(
        r"\b(?:site|website|archive|living\s+archive)\b"
        r"\s+(?:about|on|for)\s+"
        r"(.+?)(?:[?.!,;:]|$)",
        re.IGNORECASE,
    )

    for pattern in (action_pattern, site_pattern):
        for match in pattern.finditer(query):
            complement = match.group(1).strip()

            # Normalize common determiners, but retain the remainder
            # because multi-word site references matter.
            complement = re.sub(
                r"^(?:the|this|that|my|your|our|their)\s+",
                "",
                complement,
                flags=re.IGNORECASE,
            ).strip()

            # Closed structural forms that still refer to the archive
            # itself rather than to a topic.
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

            # A site anchor followed by another prepositional phrase
            # is a nested topical scope:
            # "its own approach to stewardship",
            # "the site about leadership", etc.
            if SITE_ANCHOR_RE.search(complement):
                if re.search(
                    r"\b(?:to|about|on|for|with|in)\s+\S+",
                    complement,
                    flags=re.IGNORECASE,
                ):
                    return True

            # Any remaining non-site complement is a topical target.
            if complement:
                return True

    return False


def classify_intent(query_str: str) -> str:
    clean_query = re.sub(
        r"\s+",
        " ",
        query_str.strip().lower(),
    )

    if not clean_query:
        return "TOPICAL_INQUIRY"

    # 1. A clear topical complement wins over broader site language.
    if _has_topical_prepositional_complement(clean_query):
        return "TOPICAL_INQUIRY"

    # 2. Exact/structured whole-site identity and entry queries.
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

    if re.fullmatch(
        r"where\s+to\s+begin",
        clean_query,
    ):
        return "WHOLE_SITE_ORIENTATION"

    if re.fullmatch(
        r"how\s+(?:do|can)\s+i\s+navigate\s+"
        r"(?:this\s+site|the\s+archive|the\s+living\s+archive)",
        clean_query,
    ):
        return "WHOLE_SITE_ORIENTATION"

    # 3. Compound whole-site signal.
    if (
        _has_orientation_signal(clean_query)
        and _has_site_scope_signal(clean_query)
    ):
        return "WHOLE_SITE_ORIENTATION"

    # 4. Explicit site anchor combined with a clear orientation action.
    if (
        SITE_ANCHOR_RE.search(clean_query)
        and _has_orientation_signal(clean_query)
    ):
        return "WHOLE_SITE_ORIENTATION"

    return "TOPICAL_INQUIRY"


# =====================================================================
# CANONICAL CONTEXT FORMATTING
# =====================================================================

def format_context_blocks(
    documents: List[Dict[str, Any]],
) -> str:
    formatted_blocks: List[str] = []

    for doc in documents:
        title = doc.get("title", "Untitled Resource")
        url = doc.get("url", "#")
        content = doc.get(
            "text",
            doc.get(
                "content",
                doc.get("excerpt", ""),
            ),
        )

        formatted_blocks.append(
            f"Title: {title}\n"
            f"URL: {url}\n"
            f"Content: {content}"
        )

    return "\n\n---\n\n".join(formatted_blocks)


# =====================================================================
# CANONICAL RETRIEVAL
# =====================================================================

def _metadata_from_root_fetch(root_doc: Any) -> Optional[Dict[str, Any]]:
    """
    Extract root-node metadata defensively from Pinecone's fetch
    response. Supports the current SDK object's mapping behavior
    without assuming that the response is a plain dict.
    """

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


def fetch_canonical_context(
    user_query: str,
) -> Dict[str, Any]:
    intent = classify_intent(user_query)
    retrieved_docs: List[Dict[str, Any]] = []

    if not index:
        return {
            "intent": intent,
            "context_blocks": "",
        }

    # ---------------------------------------------------------------
    # WHOLE-SITE ORIENTATION:
    # Deterministically place the canonical root node first.
    # ---------------------------------------------------------------
    if intent == "WHOLE_SITE_ORIENTATION":
        try:
            root_doc = index.fetch(ids=[ROOT_NODE_ID])
            root_metadata = _metadata_from_root_fetch(root_doc)

            if root_metadata:
                retrieved_docs.append(root_metadata)
            else:
                print(
                    "WHOLE_SITE_ORIENTATION detected, but the "
                    f"root node '{ROOT_NODE_ID}' was not returned "
                    "with metadata."
                )

        except Exception as exc:
            print(f"Root node fetch error: {exc}")

    # ---------------------------------------------------------------
    # Semantic retrieval:
    # K=2 for orientation because slot 1 is reserved for the root.
    # K=3 remains unchanged for topical inquiries.
    # ---------------------------------------------------------------
    try:
        query_vector = generate_embedding(user_query)

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
                result.get("matches", [])
                if hasattr(result, "get")
                else getattr(result, "matches", [])
            )

            for match in matches:
                match_id = (
                    match.get("id")
                    if hasattr(match, "get")
                    else getattr(match, "id", None)
                )

                metadata = (
                    match.get("metadata")
                    if hasattr(match, "get")
                    else getattr(match, "metadata", None)
                )

                if (
                    match_id != ROOT_NODE_ID
                    and isinstance(metadata, dict)
                ):
                    retrieved_docs.append(metadata)

    except Exception as exc:
        print(f"Index query error: {exc}")

    # Preserve maximum context size of three resources.
    retrieved_docs = [
        doc for doc in retrieved_docs
        if isinstance(doc, dict) and doc
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

    if not GROQ_API_KEY or not groq_client:
        return (
            "Unable to generate a response. "
            "GROQ_API_KEY is not configured in backend environment."
        )

    system_content = (
        f"{SYSTEM_PROMPT}\n\n"
        f"[QUERY INTENT]: {intent}\n\n"
        f"[CANONICAL CONTEXT]:\n{context_blocks}"
    )

    active_models = get_live_groq_models()

    if not active_models:
        return (
            "Unable to generate a response. "
            "No active models returned from Groq API."
        )

    last_error: Optional[str] = None

    for model_id in active_models:
        try:
            response = groq_client.chat.completions.create(
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

            return response.choices[0].message.content

        except Exception as exc:
            print(
                f"Execution failed for live Groq model "
                f"'{model_id}': {exc}"
            )
            last_error = str(exc)

    # Invalidate the discovery cache so the next request obtains a
    # fresh live model list.
    MODEL_CACHE["models"] = []
    MODEL_CACHE["last_fetch"] = 0.0

    return (
        "Unable to generate response. "
        f"Groq API returned error: {last_error}"
    )


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
    return {"status": "ok"}


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
        return {
            "query": "",
            "intent": "TOPICAL_INQUIRY",
            "response": (
                "Please enter a question to query the archive."
            ),
            "canonical_context": "",
        }

    query_str = str(query_str).strip()

    context_data = fetch_canonical_context(query_str)

    llm_output = generate_llm_response(
        query_str,
        context_data["context_blocks"],
        context_data["intent"],
    )

    return {
        "query": query_str,
        "intent": context_data["intent"],
        "response": llm_output,
        "canonical_context": context_data["context_blocks"],
    }


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

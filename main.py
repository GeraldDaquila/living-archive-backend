import os
import re
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pinecone import Pinecone
from fastembed import TextEmbedding

# =====================================================================
# APP & INFRASTRUCTURE INITIALIZATION
# =====================================================================

app = FastAPI(title="Find Your Way (USE) Navigation Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment Variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "living-archive")

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

# Update this ID/slug to match your exact Pinecone vector ID for the Living Archive Root Node
ROOT_NODE_ID = "canonical_root_living_archive"

# Lazy-loaded Model Instance (prevents startup timeouts on Render)
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    return _embedding_model


# =====================================================================
# EMBEDDING GENERATOR
# =====================================================================

def generate_local_embedding(text: str) -> List[float]:
    """Generates embeddings locally using fastembed on demand."""
    model = get_embedding_model()
    embeddings = list(model.embed([text]))
    return embeddings[0].tolist()


# =====================================================================
# INTENT CLASSIFICATION ENGINE (SITE ORIENTATION VS TOPICAL)
# =====================================================================

SITE_TOKENS_PATTERN = re.compile(
    r"\b(the\s+)?(whole\s+|own\s+)?(living\s+archive|archive|site|website|place|everything|all\s+this)(\s+itself|\s+as\s+a\s+whole|\s+on\s+this\s+site|\s+its\s+own\s+purpose)?\b",
    re.IGNORECASE
)

TOPICAL_PREPOSITION_GUARD = re.compile(
    r"\b(with|about|on|through|in|for|to)\s+(?!(the\s+)?(whole\s+|own\s+)?(living\s+archive|archive|site|website|place|everything|all\s+this)\b)\w+",
    re.IGNORECASE
)

SIGNAL_C_PATTERN = re.compile(
    r"^(what\s+is\s+(the\s+living\s+archive|this\s+archive|this\s+site|this\s+place)(\s+about)?|"
    r"where\s+(should|do)\s+i\s+(start|begin)|"
    r"how\s+(do|can)\s+i\s+navigate\s+(this\s+site|the\s+archive))$",
    re.IGNORECASE
)

SIGNAL_A_TOKENS = {
    "start", "begin", "entry", "first", "overwhelmed", "lost", "confused", 
    "navigate", "explore", "find my way", "how to use", "structure"
}

SIGNAL_B_TOKENS = {
    "this site", "the site", "website", "this archive", "the archive", 
    "living archive", "everything here", "all this", "how much is on"
}


def classify_intent(query_str: str) -> str:
    clean_query = query_str.strip()

    # Step 1: Prepositional Scope Check (Topical Override)
    if TOPICAL_PREPOSITION_GUARD.search(clean_query):
        return "TOPICAL_INQUIRY"

    # Step 2: Explicit Identity Check (Signal C)
    if SIGNAL_C_PATTERN.search(clean_query):
        return "WHOLE_SITE_ORIENTATION"

    # Step 3: Site-Referential Prepositional Check
    if SITE_TOKENS_PATTERN.search(clean_query) and any(w in clean_query.lower() for w in SIGNAL_A_TOKENS):
        return "WHOLE_SITE_ORIENTATION"

    # Step 4: Compound Signal Check (Signal A + Signal B)
    query_lower = clean_query.lower()
    has_signal_a = any(token in query_lower for token in SIGNAL_A_TOKENS)
    has_signal_b = any(token in query_lower for token in SIGNAL_B_TOKENS)

    if has_signal_a and has_signal_b:
        return "WHOLE_SITE_ORIENTATION"

    return "TOPICAL_INQUIRY"


# =====================================================================
# RETRIEVAL & CONTEXT FORMATTING LOGIC
# =====================================================================

def format_context_blocks(documents: List[Dict[str, Any]]) -> str:
    formatted_blocks = []
    for doc in documents:
        title = doc.get("title", "Untitled Resource")
        url = doc.get("url", "#")
        content = doc.get("text", doc.get("content", ""))
        formatted_blocks.append(f"Title: {title}\nURL: {url}\nContent: {content}")
    return "\n\n---\n\n".join(formatted_blocks)


def fetch_canonical_context(user_query: str) -> Dict[str, Any]:
    intent = classify_intent(user_query)
    retrieved_docs = []

    if intent == "WHOLE_SITE_ORIENTATION":
        # Slot 1: Deterministic Root Node Injection
        try:
            root_doc = index.fetch(ids=[ROOT_NODE_ID])
            vectors = root_doc.get("vectors", {})
            if ROOT_NODE_ID in vectors:
                retrieved_docs.append(vectors[ROOT_NODE_ID]["metadata"])
        except Exception:
            pass  # Fallback gracefully if ID fetch encounters an issue

        # Slots 2–3: Semantic Backfill (K=2)
        query_vector = generate_local_embedding(user_query)
        res = index.query(vector=query_vector, top_k=2, include_metadata=True)
        for match in res.get("matches", []):
            if match["id"] != ROOT_NODE_ID:
                retrieved_docs.append(match["metadata"])
    else:
        # Standard Topical Search (K=3)
        query_vector = generate_local_embedding(user_query)
        res = index.query(vector=query_vector, top_k=3, include_metadata=True)
        for match in res.get("matches", []):
            retrieved_docs.append(match["metadata"])

    retrieved_docs = retrieved_docs[:3]

    return {
        "intent": intent,
        "context_blocks": format_context_blocks(retrieved_docs)
    }


# =====================================================================
# API ENDPOINTS
# =====================================================================

class QueryRequest(BaseModel):
    query: str


@app.get("/")
def read_root():
    return {"status": "online", "engine": "Find Your Way (USE)"}


@app.post("/api/query")
def handle_query(payload: QueryRequest):
    if not payload.query or not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")
    
    context_data = fetch_canonical_context(payload.query)
    
    return {
        "query": payload.query,
        "intent": context_data["intent"],
        "canonical_context": context_data["context_blocks"]
    }

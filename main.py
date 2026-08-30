import os
import re
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pinecone import Pinecone
from groq import Groq

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

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "living-archive")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PREFERRED_GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)
groq_client = Groq(api_key=GROQ_API_KEY)

# Pinecone vector ID/slug for the Living Archive Root Node
ROOT_NODE_ID = "canonical_root_living_archive"


# =====================================================================
# PINECONE INTEGRATED INFERENCE (EMBEDDING GENERATION)
# =====================================================================

def generate_embedding(text: str) -> List[float]:
    """Generates query embeddings using Pinecone's native integrated inference API."""
    response = pc.inference.embed(
        model="multilingual-e5-large",
        inputs=[text],
        parameters={"input_type": "query"}
    )
    return response[0]["values"]


# =====================================================================
# INTENT CLASSIFICATION ENGINE
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
    r"^(what\s+(is|does)\s+(the\s+living\s+archive|this\s+archive|this\s+site|this\s+place)(\s+about|\s+explore)?|"
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
    clean_query = query_str.strip().lower()

    # Step 1: Prepositional Scope Guard (Topical Override)
    if TOPICAL_PREPOSITION_GUARD.search(clean_query):
        return "TOPICAL_INQUIRY"

    # Step 2: Explicit Identity Check (Signal C)
    if SIGNAL_C_PATTERN.search(clean_query):
        return "WHOLE_SITE_ORIENTATION"

    # Step 3: Site-Referential Prepositional Check
    if SITE_TOKENS_PATTERN.search(clean_query) and any(w in clean_query for w in SIGNAL_A_TOKENS):
        return "WHOLE_SITE_ORIENTATION"

    # Step 4: Compound Signal Check (Signal A + Signal B)
    has_signal_a = any(token in clean_query for token in SIGNAL_A_TOKENS)
    has_signal_b = any(token in clean_query for token in SIGNAL_B_TOKENS)

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
        content = doc.get("text", doc.get("content", doc.get("excerpt", "")))
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
            if ROOT_NODE_ID in vectors and "metadata" in vectors[ROOT_NODE_ID]:
                retrieved_docs.append(vectors[ROOT_NODE_ID]["metadata"])
        except Exception:
            pass

        # Slots 2–3: Semantic Backfill (K=2) via Pinecone Integrated Inference
        try:
            query_vector = generate_embedding(user_query)
            res = index.query(vector=query_vector, top_k=2, include_metadata=True)
            for match in res.get("matches", []):
                if match["id"] != ROOT_NODE_ID:
                    retrieved_docs.append(match.get("metadata", {}))
        except Exception:
            pass
    else:
        # Standard Topical Search (K=3) via Pinecone Integrated Inference
        try:
            query_vector = generate_embedding(user_query)
            res = index.query(vector=query_vector, top_k=3, include_metadata=True)
            for match in res.get("matches", []):
                retrieved_docs.append(match.get("metadata", {}))
        except Exception:
            pass

    # Safety Fallback: Ensure context is populated if root node lookup is missing
    if not retrieved_docs:
        try:
            query_vector = generate_embedding(user_query)
            res = index.query(vector=query_vector, top_k=3, include_metadata=True)
            for match in res.get("matches", []):
                retrieved_docs.append(match.get("metadata", {}))
        except Exception:
            pass

    retrieved_docs = [doc for doc in retrieved_docs if doc][:3]

    return {
        "intent": intent,
        "context_blocks": format_context_blocks(retrieved_docs)
    }


# =====================================================================
# GROQ MODEL RESOLUTION & GENERATION
# =====================================================================

def get_candidate_models() -> List[str]:
    """Dynamically resolves available Groq models with fallback ordering."""
    candidates = [PREFERRED_GROQ_MODEL, "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    return list(dict.fromkeys(candidates))


def generate_llm_response(user_query: str, context_blocks: str, intent: str) -> str:
    # Embedded constitutional system prompt fallback
    try:
        from system_prompt import SYSTEM_PROMPT
    except ImportError:
        SYSTEM_PROMPT = (
            "You are the Living Archive Navigation Engine. Answer the user's question using "
            "only the provided context blocks. Do not invent links or outside information."
        )

    system_content = f"{SYSTEM_PROMPT}\n\n[QUERY INTENT]: {intent}\n\n[CANONICAL CONTEXT]:\n{context_blocks}"

    for model_id in get_candidate_models():
        try:
            response = groq_client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.2,
                max_tokens=800
            )
            return response.choices[0].message.content
        except Exception:
            continue
    
    raise HTTPException(status_code=500, detail="LLM generation failed across all available model backfalls.")


# =====================================================================
# API ENDPOINTS
# =====================================================================

class QueryRequest(BaseModel):
    query: str


@app.get("/")
def read_root():
    return {"status": "ok"}


@app.post("/api/query")
@app.post("/")
def handle_query(payload: QueryRequest):
    if not payload.query or not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")
    
    context_data = fetch_canonical_context(payload.query)
    llm_output = generate_llm_response(payload.query, context_data["context_blocks"], context_data["intent"])
    
    return {
        "query": payload.query,
        "intent": context_data["intent"],
        "response": llm_output,
        "canonical_context": context_data["context_blocks"]
    }


# =====================================================================
# PROGRAMMATIC ENTRY POINT & PORT BINDING
# =====================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

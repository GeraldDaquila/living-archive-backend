import os
import re
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pinecone import Pinecone
from groq import Groq

# =====================================================================
# SYSTEM PROMPT (INLINED TO PREVENT IMPORT ERRORS)
# =====================================================================

SYSTEM_PROMPT = """
You are the navigation engine for the Living Archive (USE).
Your goal is to guide visitors through the archive using only the provided canonical context.

Constitutional Rules:
1. Institutional Fidelity: Answer strictly using facts and concepts from the provided context. Never invent features or buzzwords.
2. Hard Link Grounding: Only use exact Markdown links [Title](URL) matching URLs present in the context metadata. Never invent URLs.
3. Implicit Location Awareness: Never ask the user to "visit the site" as they are already on it.
4. Operational Sequence: Mirror the Question -> Orient Context -> Offer Canonical Routes of Movement.
"""

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

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "living-archive")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
PREFERRED_GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

pc = Pinecone(api_key=PINECONE_API_KEY) if PINECONE_API_KEY else None
index = pc.Index(PINECONE_INDEX_NAME) if pc else None
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

ROOT_NODE_ID = "canonical_root_living_archive"


# =====================================================================
# PINECONE EMBEDDING GENERATION
# =====================================================================

def generate_embedding(text: str) -> List[float]:
    """Generates query embeddings via Pinecone native inference API."""
    if not pc:
        return []
    try:
        response = pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[text],
            parameters={"input_type": "query"}
        )
        if isinstance(response, list) and len(response) > 0:
            return response[0]["values"]
        elif hasattr(response, "data") and len(response.data) > 0:
            return response.data[0].values
    except Exception as e:
        print(f"Embedding generation error: {e}")
    return []


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

    if TOPICAL_PREPOSITION_GUARD.search(clean_query):
        return "TOPICAL_INQUIRY"

    if SIGNAL_C_PATTERN.search(clean_query):
        return "WHOLE_SITE_ORIENTATION"

    if SITE_TOKENS_PATTERN.search(clean_query) and any(w in clean_query for w in SIGNAL_A_TOKENS):
        return "WHOLE_SITE_ORIENTATION"

    has_signal_a = any(token in clean_query for token in SIGNAL_A_TOKENS)
    has_signal_b = any(token in clean_query for token in SIGNAL_B_TOKENS)

    if has_signal_a and has_signal_b:
        return "WHOLE_SITE_ORIENTATION"

    return "TOPICAL_INQUIRY"


# =====================================================================
# RETRIEVAL LOGIC
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

    if index:
        if intent == "WHOLE_SITE_ORIENTATION":
            # Attempt root node pre-fetch
            try:
                root_doc = index.fetch(ids=[ROOT_NODE_ID])
                vectors = root_doc.get("vectors", {})
                if ROOT_NODE_ID in vectors and "metadata" in vectors[ROOT_NODE_ID]:
                    retrieved_docs.append(vectors[ROOT_NODE_ID]["metadata"])
            except Exception as e:
                print(f"Root node fetch error: {e}")

        # Vector semantic backfill or topical search
        try:
            query_vector = generate_embedding(user_query)
            if query_vector:
                top_k_val = 2 if intent == "WHOLE_SITE_ORIENTATION" else 3
                res = index.query(vector=query_vector, top_k=top_k_val, include_metadata=True)
                for match in res.get("matches", []):
                    if match.get("id") != ROOT_NODE_ID and match.get("metadata"):
                        retrieved_docs.append(match["metadata"])
        except Exception as e:
            print(f"Index query error: {e}")

    retrieved_docs = [doc for doc in retrieved_docs if doc][:3]

    return {
        "intent": intent,
        "context_blocks": format_context_blocks(retrieved_docs)
    }


# =====================================================================
# GROQ MODEL RESOLUTION & GENERATION
# =====================================================================

def get_candidate_models() -> List[str]:
    candidates = [PREFERRED_GROQ_MODEL, "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    return list(dict.fromkeys(candidates))


def generate_llm_response(user_query: str, context_blocks: str, intent: str) -> str:
    if not groq_client:
        return "GROQ_API_KEY environment variable is missing on backend."

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
        except Exception as e:
            print(f"Groq generation failed for {model_id}: {e}")
            continue
    
    return "Unable to generate a response at this moment. Please check backend API configurations."


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
    
    try:
        context_data = fetch_canonical_context(payload.query)
        llm_output = generate_llm_response(payload.query, context_data["context_blocks"], context_data["intent"])
        
        return {
            "query": payload.query,
            "intent": context_data["intent"],
            "response": llm_output,
            "canonical_context": context_data["context_blocks"]
        }
    except Exception as e:
        print(f"Request handling exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

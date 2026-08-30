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

pc = Pinecone(api_key=PINECONE_API_KEY) if PINECONE_API_KEY else None
index = pc.Index(PINECONE_INDEX_NAME) if pc else None
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
ROOT_NODE_ID = "canonical_root_living_archive"

# =====================================================================
# DYNAMIC MODEL DISCOVERY & CACHING (LONG-TERM FIX)
# =====================================================================

MODEL_CACHE = {"models": [], "last_fetch": 0}

def get_dynamic_groq_models() -> List[str]:
    """Queries Groq's live API to discover active models automatically."""
    now = time.time()
    if MODEL_CACHE["models"] and (now - MODEL_CACHE["last_fetch"] < 3600):
        return MODEL_CACHE["models"]

    if not groq_client:
        return ["llama-3.3-70b-versatile", "llama3-8b-8192"]

    try:
        response = groq_client.models.list()
        # Extract active text models, excluding whisper, audio, or vision-only tools
        discovered = [
            m.id for m in response.data 
            if not any(x in m.id.lower() for x in ["whisper", "guard", "vision"])
        ]
        # Prioritize 70b/versatile models first
        discovered.sort(key=lambda x: ("70b" in x or "versatile" in x), reverse=True)
        
        if discovered:
            MODEL_CACHE["models"] = discovered
            MODEL_CACHE["last_fetch"] = now
            return discovered
    except Exception as e:
        print(f"Dynamic model resolution fallback due to error: {e}")

    return ["llama-3.3-70b-versatile", "llama3-70b-8192", "llama3-8b-8192"]

# =====================================================================
# EMBEDDING & RETRIEVAL LOGIC
# =====================================================================

def generate_embedding(text: str) -> List[float]:
    try:
        embeddings = list(embedding_model.embed([text]))
        return embeddings[0].tolist()
    except Exception as e:
        print(f"Embedding generation error: {e}")
        return []

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
    if any(token in clean_query for token in SIGNAL_A_TOKENS) and any(token in clean_query for token in SIGNAL_B_TOKENS):
        return "WHOLE_SITE_ORIENTATION"
    return "TOPICAL_INQUIRY"

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
            try:
                root_doc = index.fetch(ids=[ROOT_NODE_ID])
                vectors = root_doc.get("vectors", {})
                if ROOT_NODE_ID in vectors and "metadata" in vectors[ROOT_NODE_ID]:
                    retrieved_docs.append(vectors[ROOT_NODE_ID]["metadata"])
            except Exception as e:
                print(f"Root node fetch error: {e}")

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
# GENERATION ENGINE WITH AUTOMATIC RECOVERY
# =====================================================================

def generate_llm_response(user_query: str, context_blocks: str, intent: str) -> str:
    if not GROQ_API_KEY or not groq_client:
        return "Unable to generate a response. GROQ_API_KEY is missing."

    system_content = f"{SYSTEM_PROMPT}\n\n[QUERY INTENT]: {intent}\n\n[CANONICAL CONTEXT]:\n{context_blocks}"
    candidate_models = get_dynamic_groq_models()

    last_error = None
    for model_id in candidate_models:
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
            print(f"Groq execution failed for '{model_id}': {e}")
            last_error = str(e)
            continue
    
    # If all dynamic models fail, reset cache to force fresh fetch on next call
    MODEL_CACHE["last_fetch"] = 0
    return f"Unable to generate response. Groq API returned error: {last_error}"

# =====================================================================
# API ENDPOINTS
# =====================================================================

class FlexibleQueryRequest(BaseModel):
    query: Optional[str] = None
    user_query: Optional[str] = None
    question: Optional[str] = None
    text: Optional[str] = None

@app.get("/")
@app.head("/")
def read_root():
    return {"status": "ok"}

@app.post("/api/query")
@app.post("/")
async def handle_query(request: Request, payload: Optional[FlexibleQueryRequest] = None):
    raw_body = {}
    try:
        raw_body = await request.json()
    except Exception:
        pass

    query_str = None
    if payload:
        query_str = payload.query or payload.user_query or payload.question or payload.text
    
    if not query_str and raw_body:
        query_str = (
            raw_body.get("query") or 
            raw_body.get("user_query") or 
            raw_body.get("question") or 
            raw_body.get("text") or 
            raw_body.get("input")
        )

    if not query_str or not str(query_str).strip():
        return {
            "query": "",
            "intent": "TOPICAL_INQUIRY",
            "response": "Please enter a question to query the archive.",
            "canonical_context": ""
        }

    query_str = str(query_str).strip()
    context_data = fetch_canonical_context(query_str)
    llm_output = generate_llm_response(query_str, context_data["context_blocks"], context_data["intent"])
    
    return {
        "query": query_str,
        "intent": context_data["intent"],
        "response": llm_output,
        "canonical_context": context_data["context_blocks"]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

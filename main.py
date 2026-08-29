import os
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pinecone import Pinecone
from groq import Groq

app = FastAPI(title="Living Archive Backend")

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
PREFERRED_MODEL = os.getenv("GROQ_MODEL")

# 1. Initialize Pinecone Vector Store
pc = None
index = None
if PINECONE_API_KEY:
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX_NAME)
    except Exception as e:
        print(f"Pinecone init notice: {e}")

# 2. Initialize Groq Client
groq_client = None
if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"Groq init notice: {e}")

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str

def get_candidate_models() -> list[str]:
    """Dynamically builds a list of active Groq models."""
    candidates = []
    if PREFERRED_MODEL:
        candidates.append(PREFERRED_MODEL)

    if groq_client:
        try:
            models_page = groq_client.models.list()
            available = [m.id for m in models_page.data if getattr(m, 'active', True)]
            for m_id in available:
                if "llama-3.3" in m_id or "70b" in m_id or "versatile" in m_id:
                    if m_id not in candidates:
                        candidates.append(m_id)
            for m_id in available:
                if m_id not in candidates:
                    candidates.append(m_id)
        except Exception as e:
            print(f"Dynamic model fetch notice: {e}")

    known_fallbacks = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    for fb in known_fallbacks:
        if fb not in candidates:
            candidates.append(fb)

    return candidates

def fetch_archive_context(query: str, top_k: int = 4) -> str:
    """
    Queries Pinecone vector index for relevant corpus chunks, 
    returning text, title, and actual URL mappings.
    """
    if not index:
        return ""

    try:
        # Note: If using Pinecone integrated inference or sparse vectors, adjust query parameters accordingly
        results = index.query(
            vector=[0.0] * 1536, # Placeholder vector if using vector-search; replace with actual embedding client call if needed
            top_k=top_k,
            include_metadata=True
        )

        context_blocks = []
        for match in results.get("matches", []):
            meta = match.get("metadata", {})
            title = meta.get("title", "Untitled Reference")
            url = meta.get("url", "https://geralddaquila.com/")
            text = meta.get("text", "")
            
            context_blocks.append(f"### Title: {title}\nURL: {url}\nExcerpt: {text}\n")

        return "\n---\n".join(context_blocks)
    except Exception as e:
        print(f"Pinecone retrieval notice: {e}")
        return ""

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Living Archive API is online"}

@app.post("/")
@app.post("/api/query", response_model=QueryResponse)
async def query_archive(request: QueryRequest):
    user_query = request.query.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    if not GROQ_API_KEY or not groq_client:
        return QueryResponse(
            response="**Backend Configuration Issue:** Groq client is not initialized."
        )

    # 3. Retrieve grounding context and URL mappings from Pinecone
    retrieved_context = fetch_archive_context(user_query)

    # 4. Architectural System Prompt
    system_prompt = (
        "You are the Living Archive AI Guide at geralddaquila.com. "
        "Your task is to interpret user inquiries across subjects, themes, frameworks, "
        "and pathways in a grounding, thoughtful, and coherent tone.\n\n"
        "RULES FOR CROSS-LINKING & ORIENTATION:\n"
        "1. Never invent or hallucinate URLs. Use ONLY the exact URLs provided in the Archive Context below.\n"
        "2. When referencing essays, pathways, or reference maps, cite them using standard Markdown links formatted as: [Title](URL).\n"
        "3. Broaden topics thoughtfully to encompass Global South perspectives, systems thinking, and structural healing where appropriate.\n"
        "4. Synthesize the user's inquiry against the retrieved archive excerpts into an organized pathway."
    )

    user_payload = f"USER QUERY: {user_query}\n\nARCHIVE CONTEXT & METADATA:\n{retrieved_context}" if retrieved_context else user_query

    models_to_try = get_candidate_models()
    last_error = None

    for model_name in models_to_try:
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_payload}
                ],
                model=model_name,
                temperature=0.4,
                max_tokens=1200,
            )
            ai_response = chat_completion.choices[0].message.content
            return QueryResponse(response=ai_response)
        except Exception as err:
            print(f"Model '{model_name}' failed: {err}")
            last_error = err

    err_msg = str(last_error) if last_error else "All candidate models failed."
    return QueryResponse(response=f"**API Exception Encountered:** {err_msg}")

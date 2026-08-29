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

pc = None
index = None
if PINECONE_API_KEY:
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX_NAME)
    except Exception as e:
        print(f"Pinecone init notice: {e}")

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
            print(f"Dynamic model fetch warning: {e}")

    known_fallbacks = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    for fb in known_fallbacks:
        if fb not in candidates:
            candidates.append(fb)

    return candidates

def fetch_archive_context(query: str, top_k: int = 5) -> str:
    """
    Fetches matching excerpts, actual post titles, and exact URLs from Pinecone.
    """
    if not index or not pc:
        return ""

    try:
        # Use Pinecone's integrated inference or text search if available
        # If your index requires raw vector inputs, ensure text-embedding is configured
        query_response = index.query(
            namespace="",
            top_k=top_k,
            include_metadata=True,
            # If integrated embedding isn't enabled on index, metadata filter or text match applies
            vector=[0.0] * 1536  
        )

        context_blocks = []
        for match in query_response.get("matches", []):
            meta = match.get("metadata", {})
            title = meta.get("title", "")
            url = meta.get("url", "")
            text = meta.get("text", meta.get("chunk_text", ""))

            if title and url:
                context_blocks.append(f"ARTICLE TITLE: {title}\nURL: {url}\nEXCERPT: {text}\n")

        return "\n---\n".join(context_blocks)
    except Exception as e:
        print(f"Pinecone query notice: {e}")
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
        return QueryResponse(response="**Backend Configuration Issue:** Groq client is not initialized.")

    # 1. Retrieve Context & Live Metadata
    retrieved_context = fetch_archive_context(user_query)

    # 2. Architecturally Grounded Prompt
    system_prompt = (
        "You are the Living Archive AI Guide embedded directly inside geralddaquila.com.\n\n"
        "STRICT PRESENTATION RULES:\n"
        "1. DO NOT tell the user to 'visit geralddaquila.com' or 'navigate to the site'—they are ALREADY on the website.\n"
        "2. AUTOMATIC CROSSLINKS: When mentioning an essay, framework, or pathway, you MUST hyper-link it using the exact URLs provided in the ARCHIVE CONTEXT. Format as: [Essay Title](Exact_URL).\n"
        "3. TABLE FORMATTING: When generating tables, use clear columns (`Feature | What it means | Crosslink Pathway`).\n"
        "4. TONE & FRAMEWORK: Ground responses in systems-thinking, structural healing, and Global South perspectives where relevant."
    )

    user_payload = (
        f"USER INQUIRY: {user_query}\n\n"
        f"AVAILABLE ARCHIVE CONTEXT & LIVE METADATA:\n{retrieved_context}"
        if retrieved_context else user_query
    )

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
                temperature=0.3,
                max_tokens=1200,
            )
            ai_response = chat_completion.choices[0].message.content
            return QueryResponse(response=ai_response)
        except Exception as err:
            print(f"Model candidate '{model_name}' failed: {err}")
            last_error = err

    err_msg = str(last_error) if last_error else "All candidate models failed."
    return QueryResponse(response=f"**API Exception Encountered:** {err_msg}")

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pinecone import Pinecone
from groq import Groq

# 1. Initialize FastAPI Application Instance
app = FastAPI(title="Living Archive Backend")

# 2. CORS Configuration for geralddaquila.com
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Environment Variable Retrieval
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "living-archive")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PREFERRED_MODEL = os.getenv("GROQ_MODEL")

# 4. Client Initializations
pc = None
index = None
if PINECONE_API_KEY:
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX_NAME)
    except Exception as e:
        print(f"Pinecone initialization notice: {e}")

groq_client = None
if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"Groq initialization notice: {e}")

# 5. Data Schemas
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str

def get_candidate_models() -> list[str]:
    """Dynamically fetches active Groq model IDs to prevent 400/404 errors."""
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
    Retrieves matching document chunks along with exact post titles and URLs.
    """
    if not index or not pc:
        return ""

    try:
        # Use Pinecone's native inference to embed query text
        embeddings = pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[query],
            parameters={"input_type": "query"}
        )
        query_vector = embeddings[0].values

        query_response = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True
        )

        context_blocks = []
        for match in query_response.get("matches", []):
            meta = match.get("metadata", {})
            title = meta.get("title", "Archive Reference")
            url = meta.get("url", "")
            text = meta.get("text", meta.get("chunk_text", ""))

            if url:
                context_blocks.append(f"ARTICLE TITLE: {title}\nURL: {url}\nEXCERPT: {text}\n")

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
        return QueryResponse(response="**Backend Configuration Issue:** Groq client is not initialized.")

    # 1. Retrieve Context and Links from Pinecone
    retrieved_context = fetch_archive_context(user_query)

    # 2. Strict Link & Architectural Rules
    system_prompt = (
        "You are the Living Archive AI Guide embedded directly inside geralddaquila.com.\n\n"
        "STRICT NAVIGATION RULES:\n"
        "1. DO NOT tell the user to 'visit geralddaquila.com' or 'navigate to the site'—they are ALREADY on the website.\n"
        "2. AUTOMATIC HYPERLINKS: Every time you reference an article, essay, pathway, or reference map from the context, you MUST hyper-link it using the exact URL from the context metadata: [Article Title](Exact_URL).\n"
        "3. TABLE FORMATTING: When presenting structured concepts, use Markdown tables with clear column separation (`Feature | What it means | Related Pathway`).\n"
        "4. TONE & FRAMEWORK: Ground responses in systems thinking, structural healing, and Global South perspectives where relevant."
    )

    user_payload = (
        f"USER INQUIRY: {user_query}\n\n"
        f"RETRIEVED ARCHIVE CONTEXT & METADATA:\n{retrieved_context}"
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

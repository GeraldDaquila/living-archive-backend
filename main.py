import os
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pinecone import Pinecone
from groq import Groq

app = FastAPI(title="Living Archive Backend")

# 1. CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Environment Variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "living-archive")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PREFERRED_MODEL = os.getenv("GROQ_MODEL")  # Optional override in Render

# 3. Client Initializations
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

# 4. Request / Response Schemas
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str

def get_candidate_models() -> list[str]:
    """
    Dynamically builds a prioritized list of active Groq model IDs.
    Prevents breakage when upstream model IDs are decommissioned.
    """
    candidates = []

    # Priority 1: User Override via Render Environment Variable
    if PREFERRED_MODEL:
        candidates.append(PREFERRED_MODEL)

    # Priority 2: Live API Query to Groq's Active Models
    if groq_client:
        try:
            models_page = groq_client.models.list()
            available_models = [m.id for m in models_page.data if getattr(m, 'active', True)]
            
            # Prioritize flagship Llama models from live list
            for m_id in available_models:
                if "llama-3.3" in m_id or "70b" in m_id or "versatile" in m_id:
                    if m_id not in candidates:
                        candidates.append(m_id)

            # Append remaining active models
            for m_id in available_models:
                if m_id not in candidates:
                    candidates.append(m_id)
        except Exception as e:
            print(f"Dynamic model fetch warning: {e}")

    # Priority 3: Hardcoded Standard Groq Production Models
    known_fallbacks = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    for fb in known_fallbacks:
        if fb not in candidates:
            candidates.append(fb)

    return candidates

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
            response="**Backend Configuration Issue:** `GROQ_API_KEY` is missing or Groq client failed to initialize."
        )

    system_prompt = (
        "You are the Living Archive AI guide for geralddaquila.com. "
        "Interpret the user's inquiry across subjects, themes, frameworks, "
        "and pathways in a grounding, thoughtful tone. Keep responses clear, "
        "insightful, and structured."
    )

    models_to_try = get_candidate_models()
    last_error = None

    # Iterate through candidates until an active model completes successfully
    for model_name in models_to_try:
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                model=model_name,
                temperature=0.5,
                max_tokens=1024,
            )
            ai_response = chat_completion.choices[0].message.content
            return QueryResponse(response=ai_response)
        except Exception as err:
            print(f"Model candidate '{model_name}' failed: {err}")
            last_error = err

    # Fallback response if all candidates fail
    err_msg = str(last_error) if last_error else "All candidate models failed."
    return QueryResponse(
        response=f"**API Exception Encountered:** {err_msg}"
    )

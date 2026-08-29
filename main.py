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
# Optional env var: set a specific model in Render if you want to override auto-detection
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

def get_active_groq_model() -> str:
    """Dynamically fetches available models from Groq to prevent breaking on deprecations."""
    if PREFERRED_MODEL:
        return PREFERRED_MODEL

    try:
        models_page = groq_client.models.list()
        available_models = [m.id for m in models_page.data if getattr(m, 'active', True)]
        
        # Priority order for preferred model families
        for model_id in available_models:
            if "120b" in model_id or "70b" in model_id or "versatile" in model_id:
                return model_id
        
        # Fallback to the first active model listed by Groq
        if available_models:
            return available_models[0]
    except Exception as e:
        print(f"Failed to fetch dynamic models: {e}")

    # Ultimate fallback string
    return "openai/gpt-oss-120b"

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
            response="**Backend Configuration Issue:** Groq API client is not configured."
        )

    try:
        active_model = get_active_groq_model()

        system_prompt = (
            "You are the Living Archive AI guide for geralddaquila.com. "
            "Interpret the user's inquiry across subjects, themes, frameworks, "
            "and pathways in a grounding, thoughtful tone. Keep responses clear, "
            "insightful, and structured."
        )

        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            model=active_model,
            temperature=0.5,
            max_tokens=1024,
        )

        ai_response = chat_completion.choices[0].message.content
        return QueryResponse(response=ai_response)

    except Exception as e:
        err_msg = str(e)
        print(f"Error executing query: {err_msg}")
        traceback.print_exc()
        return QueryResponse(
            response=f"**API Exception Encountered:** {err_msg}"
        )

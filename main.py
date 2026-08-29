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

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Living Archive API is online"}

@app.post("/")
@app.post("/api/query", response_model=QueryResponse)
async def query_archive(request: QueryRequest):
    user_query = request.query.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    if not GROQ_API_KEY:
        return QueryResponse(
            response="**Backend Configuration Issue:** `GROQ_API_KEY` is not set in Render's Environment Variables."
        )

    if not groq_client:
        return QueryResponse(
            response="**Backend Configuration Issue:** Groq client failed to initialize."
        )

    try:
        system_prompt = (
            "You are the Living Archive AI guide for geralddaquila.com. "
            "Interpret the user's inquiry across subjects, themes, frameworks, "
            "and pathways in a grounding, thoughtful tone. Keep responses clear, "
            "insightful, and structured."
        )

        # Attempt Groq completion with active, supported model strings
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.5,
                max_tokens=1024,
            )
        except Exception:
            # Secondary fallback to Groq's specdec endpoint
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                model="llama-3.3-70b-specdec",
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

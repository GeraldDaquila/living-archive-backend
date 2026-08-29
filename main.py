import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

class QueryRequest(BaseModel):
    query: str

@app.get("/")
def read_root():
    return {"status": "Living Archive Engine Online"}

@app.post("/api/query")
async def query_archive(payload: QueryRequest):
    if not payload.query or not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")

    if not client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is missing from environment variables.")

    try:
        # Standard free-tier Flash model (1,500 requests/day)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"You are the Living Archive interface. Answer clearly: {payload.query}",
        )
        return {"response": response.text}

    except Exception as e:
        error_msg = str(e)
        print(f"Generation error: {error_msg}")
        
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return {"response": "Rate limit reached. Please wait a moment and try again."}
        
        return {"response": "An error occurred while connecting to the archive engine."}

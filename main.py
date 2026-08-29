import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

app = FastAPI()

# 1. Enable CORS for WordPress integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Initialize Groq Client
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# 3. Request Schema
class QueryRequest(BaseModel):
    query: str

# 4. Base Health Check (Cron-job target: zero AI tokens consumed)
@app.get("/")
def read_root():
    return {"status": "Living Archive Engine Online"}

# 5. Archive Search Endpoint
@app.post("/api/query")
async def query_archive(payload: QueryRequest):
    if not payload.query or not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")

    if not client:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is missing from environment variables.")

    try:
        # Utilizing Llama-3.1-8b-instant for 14,400 daily free requests
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are the Living Archive interface. Answer user inquiries clearly, accurately, and concisely."
                },
                {
                    "role": "user",
                    "content": payload.query
                }
            ],
            temperature=0.5,
            max_tokens=1024,
        )
        
        return {"response": completion.choices[0].message.content}

    except Exception as e:
        error_msg = str(e)
        print(f"Generation error: {error_msg}")
        
        if "429" in error_msg:
            return {"response": "Query rate limit reached temporarily. Please wait a minute and try again."}
        
        return {"response": "An error occurred while connecting to the archive engine."}

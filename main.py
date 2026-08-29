import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai

app = FastAPI()

# 1. Enable CORS for WordPress integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Initialize Gemini Client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# 3. Request Schema
class QueryRequest(BaseModel):
    query: str

# 4. Health Check Endpoint (Ping target for Cron-Job / UptimeRobot)
@app.get("/")
def read_root():
    return {"status": "Living Archive Engine Online"}

# 5. Query Endpoint
@app.post("/api/query")
async def query_archive(payload: QueryRequest):
    if not payload.query or not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")

    if not client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY environment variable is not configured.")

    try:
        prompt = f"You are the Living Archive interface. Answer the following inquiry clearly: {payload.query}"
        
        # Primary standard production model
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
        )
        
        return {"response": response.text}

    except Exception as e:
        error_msg = str(e)
        print(f"Generation error: {error_msg}")
        
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return {
                "response": "The Living Archive is currently receiving high traffic. Please wait 30 seconds and try your search again."
            }
        
        return {
            "response": "An error occurred while connecting to the archive engine. Please try your query again."
        }

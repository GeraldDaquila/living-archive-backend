import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()

# 1. Enable CORS for WordPress integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Configure Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# 3. Model Initialization (Explicit version string to avoid v1beta 404s)
model = genai.GenerativeModel("models/gemini-1.5-flash")

# 4. Request Schema
class QueryRequest(BaseModel):
    query: str

# 5. Health Check Endpoint
@app.get("/")
def read_root():
    return {"status": "Living Archive Engine Online"}

# 6. Query Endpoint with Fallbacks
@app.post("/api/query")
async def query_archive(payload: QueryRequest):
    if not payload.query or not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")

    try:
        prompt = f"You are the Living Archive interface. Answer the following inquiry clearly: {payload.query}"
        response = model.generate_content(prompt)
        return {"response": response.text}

    except Exception as e:
        error_msg = str(e)
        print(f"Generation error: {error_msg}")
        
        # Clean response on rate limits or errors
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return {
                "response": "The Living Archive is currently experiencing high query volume. Please wait 30 seconds and try your search again."
            }
        
        return {
            "response": "An error occurred while connecting to the archive engine. Please try your query again."
        }

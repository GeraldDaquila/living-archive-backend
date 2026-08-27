import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from google import genai
from pydantic import BaseModel

app = FastAPI(
    title="Living Archive Backend",
    description="API server for search and archive queries",
    version="0.1.0",
)


# 1. Health Check Endpoints (Fixes Render 404 & Auto-Shutdown)
@app.get("/")
@app.head("/")
async def root():
    return {"status": "ok", "message": "Living Archive Backend is running."}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


class SearchPayload(BaseModel):
    query: str
    clarification: Optional[str] = None


# 2. Search Endpoint using google-genai SDK
@app.post("/api/search")
async def search_endpoint(payload: SearchPayload):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY environment variable is not set on the server.",
        )

    try:
        client = genai.Client(api_key=api_key)

        prompt = payload.query
        if payload.clarification:
            prompt += f"\nContext/Clarification: {payload.clarification}"

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        return {
            "query": payload.query,
            "clarification": payload.clarification,
            "result": response.text,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Backend processing error: {str(e)}"
        )

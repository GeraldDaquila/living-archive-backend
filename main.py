import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pinecone import Pinecone

app = FastAPI(title="Living Archive API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "living-archive")

# Initialize Pinecone
index = None
if PINECONE_API_KEY:
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX_NAME)
    except Exception as e:
        print(f"Pinecone init warning: {e}")

class QueryRequest(BaseModel):
    query: str

def get_embedding(text: str):
    """Direct REST call for text embeddings."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={GEMINI_API_KEY}"
    payload = {
        "model": "models/text-embedding-004",
        "content": {"parts": [{"text": text}]}
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        data = res.json()
        if "embedding" in data and "values" in data["embedding"]:
            return data["embedding"]["values"]
        print(f"Embedding API error payload: {data}")
        return None
    except Exception as e:
        print(f"Embedding request failed: {e}")
        return None

def generate_text(prompt: str):
    """Direct REST call for Gemini text generation."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    res = requests.post(url, json=payload, timeout=15)
    data = res.json()
    
    if res.status_code != 200:
        raise Exception(f"Gemini API returned {res.status_code}: {data.get('error', {}).get('message', 'Unknown error')}")
        
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise Exception(f"Unexpected response structure: {data}")

@app.get("/")
def health_check():
    return {"status": "ok", "message": "API active"}

@app.post("/api/query")
async def handle_query(request: QueryRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is missing in Render environment variables.")

    query_text = request.query.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    context_chunks = []

    # 1. Pinecone Retrieval
    if index:
        vector = get_embedding(query_text)
        if vector:
            try:
                results = index.query(vector=vector, top_k=3, include_metadata=True)
                for match in results.get("matches", []):
                    meta = match.get("metadata", {})
                    if "text" in meta:
                        context_chunks.append(meta["text"])
            except Exception as e:
                print(f"Pinecone search error: {e}")

    # 2. Prompt Assembly
    if context_chunks:
        context_str = "\n\n".join(context_chunks)
        prompt = (
            f"You are the voice of the Living Archive.\n"
            f"Answer the user query based on this context:\n{context_str}\n\n"
            f"Query: {query_text}"
        )
    else:
        prompt = (
            f"You are the voice of the Living Archive.\n"
            f"Answer the user query directly and thoughtfully:\n\n"
            f"Query: {query_text}"
        )

    # 3. Direct HTTP REST Request
    try:
        answer = generate_text(prompt)
        return {"response": answer}
    except Exception as err:
        print(f"Generation error: {err}")
        raise HTTPException(status_code=500, detail=str(err))

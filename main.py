import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pinecone import Pinecone
from google import genai

app = FastAPI(title="Living Archive API")

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

# Initialize Gemini Client via official SDK
ai_client = None
if GEMINI_API_KEY:
    try:
        ai_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Gemini client init error: {e}")

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
    """Fetch embeddings safely using the official SDK."""
    if not ai_client:
        return None
    try:
        response = ai_client.models.embed_content(
            model="text-embedding-004",
            contents=text,
        )
        if hasattr(response, 'embedding') and response.embedding:
            return response.embedding.values
    except Exception as e:
        print(f"Embedding attempt failed: {e}")
    return None

def generate_text(prompt: str):
    """Generate content safely using gemini-2.5-flash."""
    if not ai_client:
        raise Exception("Gemini client is not initialized.")
    
    try:
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        if response.text:
            return response.text
        raise Exception("Empty response returned from Gemini.")
    except Exception as e:
        raise Exception(f"Gemini API Error: {e}")

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Living Archive API active"}

@app.post("/api/query")
async def handle_query(request: QueryRequest):
    if not GEMINI_API_KEY or not ai_client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is missing or invalid on Render.")

    query_text = request.query.strip() if request.query else ""
    if not query_text:
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")

    context_chunks = []

    # Safe Vector Search
    if index:
        try:
            vector = get_embedding(query_text)
            if vector:
                results = index.query(vector=vector, top_k=3, include_metadata=True)
                for match in results.get("matches", []):
                    meta = match.get("metadata", {})
                    if "text" in meta:
                        context_chunks.append(meta["text"])
        except Exception as e:
            print(f"Pinecone search bypassed due to error: {e}")

    # Build Prompt
    if context_chunks:
        context_str = "\n\n".join(context_chunks)
        prompt = (
            f"You are the assistant for the Living Archive.\n"
            f"Answer the query using the retrieved context below:\n\n"
            f"Context:\n{context_str}\n\n"
            f"Query: {query_text}"
        )
    else:
        prompt = (
            f"You are the assistant for the Living Archive.\n"
            f"Answer the query directly, thoughtfully, and clearly:\n\n"
            f"Query: {query_text}"
        )

    # Generate Response
    try:
        answer = generate_text(prompt)
        return {"response": answer}
    except Exception as err:
        print(f"Generation error: {err}")
        raise HTTPException(status_code=500, detail=str(err))

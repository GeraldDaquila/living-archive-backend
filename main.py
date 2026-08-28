import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pinecone import Pinecone
from google import genai

app = FastAPI(title="Living Archive API")

# Setup CORS for WordPress interaction
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

# Initialize Gemini Client
ai_client = None
if GEMINI_API_KEY:
    try:
        ai_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Gemini client init error: {e}")

# Initialize Pinecone Client
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
            model="embedding-001",
            contents=text,
        )
        if hasattr(response, 'embedding') and response.embedding:
            return response.embedding.values
    except Exception as e:
        print(f"Embedding notice (skipping vector lookup): {e}")
    return None

def generate_text(prompt: str):
    """Generate curated navigation guidance using gemini-3.6-flash."""
    if not ai_client:
        raise Exception("Gemini client is not initialized.")
    
    try:
        response = ai_client.models.generate_content(
            model="gemini-3.6-flash",
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
            print(f"Pinecone search bypassed: {e}")

    # Build Prompt with Navigation Blueprint
    context_str = "\n\n".join(context_chunks) if context_chunks else "No specific matches found in vector index."
    
    prompt = (
        "You are the Navigation Guide for the Living Archive.\n"
        "Your task is NOT to give generic advice or synthesize answers yourself. "
        "Your goal is to orient the user toward the Archive's existing body of thought.\n\n"
        "Follow this exact response structure using clean Markdown:\n\n"
        "**Start Here**\n"
        "[Primary Resource/Essay Title] — State in 1-2 sentences why this is the primary starting point relative to the query.\n\n"
        "**Complementary Pathways & Resources**\n"
        "• [Resource/Framework 1] — 1 sentence explaining its complementary connection.\n"
        "• [Resource/Framework 2] — 1 sentence explaining its complementary connection.\n\n"
        "**Why These Resources**\n"
        "A brief (2 sentence) synthesis explaining how these materials approach the inquiry from different levels of the system.\n\n"
        f"Retrieved Archive Context:\n{context_str}\n\n"
        f"User Query: {query_text}"
    )

    # Generate Output
    try:
        answer = generate_text(prompt)
        return {"response": answer}
    except Exception as err:
        print(f"Generation error: {err}")
        raise HTTPException(status_code=500, detail=str(err))

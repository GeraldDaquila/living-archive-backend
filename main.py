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

    context_str = "\n\n".join(context_chunks) if context_chunks else "Database context is currently expanding."

    # Prompt Setup with 70/30 Grounding and Sensemaking Focus
    prompt = (
        "You are the Navigation Guide and Sensemaking Interface for the Living Archive.\n"
        "Your role is to orient the user toward existing body of thought, framing their inquiry thoughtfully.\n\n"
        "BALANCE GUIDELINE:\n"
        "1. Primary Weight (70%): Base your orientation on the Archive Context provided below.\n"
        "2. Complementary Synthesis (30%): If the Archive context is sparse, draw upon established universal frameworks, systems thinking, and philosophical sensemaking to complete the guidance.\n\n"
        "RESPONSE STRUCTURE (Use clean Markdown):\n\n"
        "**The Question Beneath the Question**\n"
        "A brief (1-2 sentence) reflective re-framing of what the query is truly touching upon.\n\n"
        "**Start Here**\n"
        "• [Primary Concept/Resource] — State clearly why this serves as the foundational starting point.\n\n"
        "**Complementary Pathways**\n"
        "• [Pathway 1] — 1 sentence on its systemic or practical relation to the inquiry.\n"
        "• [Pathway 2] — 1 sentence on its systemic or practical relation to the inquiry.\n\n"
        "**Contextual Synthesis**\n"
        "A concise closing paragraph bridging the archive's core perspective with the practical reality of the user's inquiry.\n\n"
        f"Archive Corpus Context:\n{context_str}\n\n"
        f"User Query: {query_text}"
    )

    # Generate Output
    try:
        answer = generate_text(prompt)
        return {"response": answer}
    except Exception as err:
        print(f"Generation error: {err}")
        raise HTTPException(status_code=500, detail=str(err))

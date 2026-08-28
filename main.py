import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pinecone import Pinecone
from google import genai
from google.genai import types

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

# Initialize Gemini Client with 120-second Timeout Fix
ai_client = None
if GEMINI_API_KEY:
    try:
        ai_client = genai.Client(
            api_key=GEMINI_API_KEY,
            http_options=types.HttpOptions(timeout=120)
        )
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
    """Fetch embeddings safely using text-embedding-004."""
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
        print(f"Embedding notice (skipping vector lookup): {e}")
    return None

def generate_text(prompt: str):
    """Generate curated guidance using active gemini-3.6-flash model."""
    if not ai_client:
        raise Exception("Gemini client is not initialized.")
    
    try:
        response = ai_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
        )
        if response.text:
            return response.text
        raise Exception("Empty text returned from Gemini API.")
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

    # Vector Search
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

    context_str = "\n\n".join(context_chunks) if context_chunks else "Archive database context expanding."

    # Outer Courtyard EQ Sensemaking Prompt
    prompt = (
        "You are the Navigation and Sensemaking Guide for the Living Archive outer courtyard interface.\n"
        "Your goal is to guide an uninitiated visitor from confusion/depletion to clarity, balance, and self-sovereignty.\n\n"
        "STRICT TONE & LANGUAGE RULES:\n"
        "1. NO JARGON: Do NOT use technical, academic, or esoteric words (e.g., 'somatic', 'telemetry', 'coherence', 'resonance', 'frequency', 'corpus', 'oversoul', 'ecologies of capacity'). Use clean, warm, everyday human words.\n"
        "2. UNANNOUNCED EQ ARCHITECTURE: Do NOT label the first paragraph as 'Question Beneath the Question' or 'Contextual Synthesis'. Simply start directly with the re-framing.\n"
        "3. INTENTIONALLY CURATED DELTA: The suggested pathways must give the reader a feeling of regaining control over their situation.\n\n"
        "OUTPUT STRUCTURE (Use plain Markdown formatting):\n\n"
        "[Paragraph 1: Unlabeled Grounding & Re-framing]\n"
        "1-2 sentences that gently re-frame their situation. Shift the burden away from personal failure toward understanding the dynamics around them.\n\n"
        "**Start Here**\n"
        "• [Resource/Essay Title] — 1-2 plain, grounding sentences on why this helps them find their bearings right now.\n\n"
        "**Complementary Pathways**\n"
        "• [Resource/Pathway 1] — 1 sentence offering a practical or psychological perspective shift.\n"
        "• [Resource/Pathway 2] — 1 sentence offering a way to restore personal agency or boundaries.\n\n"
        "[Paragraph 2: Unlabeled Sensemaking Closing]\n"
        "2 sentences concluding with a steady, empowering realization that leaves the visitor feeling centered and in control.\n\n"
        f"Archive Reference Context:\n{context_str}\n\n"
        f"User Query: {query_text}"
    )

    try:
        answer = generate_text(prompt)
        return {"response": answer}
    except Exception as err:
        print(f"Generation error: {err}")
        raise HTTPException(status_code=500, detail=str(err))

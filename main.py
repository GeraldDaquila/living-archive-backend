import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qdrant_client import QdrantClient
from fastembed import TextEmbedding
import google.generativeai as genai

app = FastAPI()

# Enable CORS for WordPress HTTP requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Qdrant & Embedding initialization
# Note: Swap path to Qdrant Cloud URL/API Key for persistent cloud storage later
DB_PATH = "./qdrant_db"
qdrant = QdrantClient(path=DB_PATH)
embedding_model = TextEmbedding()

# Configure Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

class SearchPayload(BaseModel):
    query: str
    clarification: str = None

@app.post("/api/search")
async def search_endpoint(payload: SearchPayload):
    full_query = f"{payload.query} {payload.clarification}" if payload.clarification else payload.query
    query_vector = list(embedding_model.embed([full_query]))[0]

    response = qdrant.query_points(
        collection_name="documents",
        query=query_vector.tolist(),
        limit=3
    )
    
    hits = response.points
    docs = [hit.payload.get("text", "")[:300] for hit in hits]
    titles = [hit.payload.get("title", "Untitled") for hit in hits]
    context = "\n---\n".join(docs)

    # First Pass: Generate Socratic Clarifying Question
    if not payload.clarification:
        prompt = f"""
        You are the Living Archive Socratic Concierge.
        User Query: "{payload.query}"
        Retrieved Context Excerpts:
        {context}

        Formulate ONE short, reflective clarifying question to help the user specify their intent.
        Respect user sovereignty—keep it concise, grounded, and characteristically thoughtful.
        """
        ai_res = model.generate_content(prompt)
        return {
            "mode": "clarification",
            "question": ai_res.text.strip(),
            "matches": titles
        }

    # Second Pass: Synthesize Final Answer
    prompt = f"""
    Synthesize a helpful, precise response based on the living archive context and user clarification.
    User Query: {payload.query}
    Clarification Provided: {payload.clarification}
    Context: {context}
    """
    ai_res = model.generate_content(prompt)
    return {
        "mode": "final",
        "answer": ai_res.text.strip(),
        "sources": titles
    }
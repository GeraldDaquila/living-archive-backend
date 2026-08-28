import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pinecone import Pinecone
from google import genai

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

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY environment variable is missing.")

# Initialize new Google GenAI Client
client = genai.Client(api_key=GEMINI_API_KEY)

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
    """Generates embeddings using text-embedding-004 via the new SDK."""
    try:
        res = client.models.embed_content(
            model="text-embedding-004",
            contents=text,
        )
        return res.embedding.values
    except Exception as e:
        print(f"Embedding failed: {e}")
        return None

@app.get("/")
def health_check():
    return {"status": "ok", "message": "API active"}

@app.post("/api/query")
async def handle_query(request: QueryRequest):
    query_text = request.query.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    context_chunks = []

    # 1. Retrieve vectors from Pinecone
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

    # 2. Build Prompt
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

    # 3. Generate response using Gemini 2.5
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return {"response": response.text}
    except Exception as err:
        print(f"Generation error: {err}")
        raise HTTPException(status_code=500, detail=str(err))

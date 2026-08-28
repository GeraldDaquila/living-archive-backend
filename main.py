import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pinecone import Pinecone
import google.generativeai as genai

app = FastAPI(title="Living Archive API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "living-archive")

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Configure Pinecone
index = None
if PINECONE_API_KEY:
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX_NAME)
    except Exception as e:
        print(f"Warning: Pinecone initialization failed: {e}")

class QueryRequest(BaseModel):
    query: str

def get_text_embedding(text: str):
    """Generates vector embedding using text-embedding-004."""
    try:
        res = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_query"
        )
        return res['embedding']
    except Exception as e:
        print(f"Embedding error: {e}")
        return None

@app.get("/")
def read_root():
    return {"status": "ok", "message": "API is online"}

@app.post("/api/query")
async def handle_query(request: QueryRequest):
    query_text = request.query.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    context_chunks = []

    # 1. Try vector retrieval if Pinecone is configured
    if index:
        query_vector = get_text_embedding(query_text)
        if query_vector:
            try:
                results = index.query(
                    vector=query_vector,
                    top_k=3,
                    include_metadata=True
                )
                for match in results.get("matches", []):
                    meta = match.get("metadata", {})
                    if "text" in meta:
                        context_chunks.append(meta["text"])
            except Exception as e:
                print(f"Pinecone query bypassed due to error: {e}")

    # 2. Build Prompt based on available context
    if context_chunks:
        context_str = "\n\n".join(context_chunks)
        prompt = (
            f"You are the voice of the Living Archive. "
            f"Answer the user's question using the context below:\n\n"
            f"Context:\n{context_str}\n\n"
            f"Question: {query_text}"
        )
    else:
        prompt = (
            f"You are the voice of the Living Archive. "
            f"Answer the following question directly, thoughtfully, and clearly:\n\n"
            f"Question: {query_text}"
        )

    # 3. Generate Gemini Response
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        model_response = model.generate_content(prompt)
        return {"response": model_response.text}
    except Exception as e:
        print(f"Gemini generation error: {e}")
        # Secondary fallback if model naming varies
        try:
            model = genai.GenerativeModel("gemini-pro")
            model_response = model.generate_content(prompt)
            return {"response": model_response.text}
        except Exception as err:
            print(f"Fallback model failed: {err}")
            raise HTTPException(status_code=500, detail=f"Gemini generation failed: {str(e)}")

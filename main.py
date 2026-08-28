import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pinecone import Pinecone
import google.generativeai as genai

app = FastAPI(title="Living Archive API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fetch Environment Variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "living-archive")

# Configure Google AI
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Configure Pinecone
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
    """Generates 768-dim vector embedding using text-embedding-004."""
    try:
        res = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_query"
        )
        return res['embedding']
    except Exception as e:
        print(f"Embedding failed: {e}")
        return None

def generate_with_gemini(prompt: str) -> str:
    """Attempts generation using multiple fallback model identifiers."""
    candidate_models = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-pro"]
    
    last_error = None
    for model_name in candidate_models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            print(f"Model {model_name} failed: {e}")
            last_error = e
            
    raise Exception(f"All Gemini models failed. Last error: {str(last_error)}")

@app.get("/")
def health_check():
    return {"status": "ok", "message": "API active"}

@app.post("/api/query")
async def handle_query(request: QueryRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=500, 
            detail="GEMINI_API_KEY environment variable is missing on Render."
        )

    query_text = request.query.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    context_chunks = []

    # 1. Pinecone Vector Search
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

    # 2. Prompt Construction
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

    # 3. Dynamic Response Generation
    try:
        answer = generate_with_gemini(prompt)
        return {"response": answer}
    except Exception as err:
        print(f"Generation error: {err}")
        # Send exact python exception message back to browser for clear debugging
        raise HTTPException(status_code=500, detail=str(err))

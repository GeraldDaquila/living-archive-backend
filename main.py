import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pinecone import Pinecone
import google.generativeai as genai

# ==========================================
# 1. INITIALIZATION & CONFIGURATION
# ==========================================

app = FastAPI(title="Living Archive API")

# Enable CORS for WordPress frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fetch Environment Variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "living-archive")

if not GEMINI_API_KEY or not PINECONE_API_KEY:
    raise ValueError("Missing critical environment variables: GEMINI_API_KEY or PINECONE_API_KEY.")

# Configure Google Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
llm_model = genai.GenerativeModel("gemini-2.5-flash")

# Configure Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)


# Request Schema
class QueryRequest(BaseModel):
    query: str


# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def get_text_embedding(text: str):
    """Generates a 768-dim vector embedding using Google Generative AI."""
    try:
        response = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_query"
        )
        return response["embedding"]
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None


# ==========================================
# 3. API ENDPOINTS
# ==========================================

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Living Archive API is running"}


@app.post("/api/query")
async def query_archive(request: QueryRequest):
    query_text = request.query.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")

    # 1. Generate query vector
    vector = get_text_embedding(query_text)
    
    context_chunks = []
    
    # 2. Retrieve vectors from Pinecone if embedding succeeded
    if vector:
        try:
            results = index.query(
                vector=vector,
                top_k=3,
                include_metadata=True
            )
            matches = results.get("matches", [])
            for match in matches:
                metadata = match.get("metadata", {})
                if "text" in metadata:
                    context_chunks.append(metadata["text"])
        except Exception as e:
            print(f"Pinecone query error: {e}")

    # 3. Construct prompt dynamically (No static fallbacks)
    if context_chunks:
        context_str = "\n\n".join(context_chunks)
        prompt = (
            f"You are the voice of the Living Archive. "
            f"Use the following retrieved context to answer the question thoughtfully and directly.\n\n"
            f"--- CONTEXT ---\n{context_str}\n---------------\n\n"
            f"User Question: {query_text}\nAnswer:"
        )
    else:
        # Fallback to direct Gemini synthesis if Pinecone index is empty or unpopulated
        prompt = (
            f"You are the voice of the Living Archive. "
            f"Answer the following query thoughtfully, warmly, and concisely:\n\n"
            f"Query: {query_text}"
        )

    # 4. Generate answer using Gemini
    try:
        response = llm_model.generate_content(prompt)
        answer = response.text.strip()
        return {"response": answer}
    except Exception as e:
        print(f"Gemini generation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate response.")

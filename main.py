import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pinecone import Pinecone
from groq import Groq

# ------------------------------------------------------------------------------
# 1. Initialize FastAPI App & Enable CORS
# ------------------------------------------------------------------------------
app = FastAPI(title="Living Archive Backend")

# Allow requests from your WordPress frontend and local testing environments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows geralddaquila.com and all external origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# 2. Environment Variables & Client Initialization
# ------------------------------------------------------------------------------
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "living-archive")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Pinecone
pc = None
index = None
if PINECONE_API_KEY:
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX_NAME)
    except Exception as e:
        print(f"Warning: Failed to initialize Pinecone: {e}")

# Initialize Groq
groq_client = None
if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"Warning: Failed to initialize Groq client: {e}")

# ------------------------------------------------------------------------------
# 3. Request / Response Data Models
# ------------------------------------------------------------------------------
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str

# ------------------------------------------------------------------------------
# 4. API Endpoints
# ------------------------------------------------------------------------------
@app.get("/")
def read_root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Living Archive API is online"}

@app.post("/api/query", response_model=QueryResponse)
async def query_archive(request: QueryRequest):
    """
    Main endpoint queried by the WordPress front-end search interface.
    """
    user_query = request.query.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # Validate client initializations
    if not groq_client:
        raise HTTPException(status_code=500, detail="Groq client is not configured on the backend.")

    try:
        # Retrieve context from Pinecone vector database if available
        context_str = ""
        if index:
            # Query Pinecone (adjust embedding model/call if using Pinecone Inference API)
            try:
                # Basic context placeholder or vector search call
                # Expand this section if generating embeddings via Groq or Pinecone
                pass
            except Exception as pe:
                print(f"Pinecone query error: {pe}")

        # System prompt setting the context for the Living Archive
        system_prompt = (
            "You are the Living Archive AI guide for geralddaquila.com. "
            "Interpret the user's inquiry across subjects, themes, frameworks, "
            "and pathways in a grounding, thoughtful tone. Keep responses clear, "
            "insightful, and structured."
        )

        # Call Groq API (using llama-3.3-70b-versatile or your preferred model)
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context_str}\n\nQuestion: {user_query}" if context_str else user_query}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.5,
            max_tokens=1024,
        )

        ai_response = chat_completion.choices[0].message.content
        return QueryResponse(response=ai_response)

    except Exception as e:
        print(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

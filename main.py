import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Living Archive Backend",
    description="Backend API for Outer Courtyard Search",
    version="1.0.0"
)

# Enable CORS for all domains so WordPress can talk to Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Allows requests from any origin
    allow_credentials=True,
    allow_methods=["*"],        # Allows GET, POST, OPTIONS, etc.
    allow_headers=["*"],        # Allows all headers
)

class QueryRequest(BaseModel):
    query: str

@app.get("/")
def read_root():
    return {"status": "online", "message": "Living Archive API is running"}

@app.post("/api/query")
async def query_archive(request: QueryRequest):
    user_query = request.query.strip()
    
    if not user_query:
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")
    
    try:
        # Core archive response logic
        response_text = f"Stewardship is the intentional practice of holding, nurturing, and passing forward what has been entrusted to us across generations."

        return {
            "status": "success",
            "query": user_query,
            "response": response_text
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

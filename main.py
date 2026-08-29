from fastapi import FastAPI, Query
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
import os

app = FastAPI(title="Living Archive API")

# 1. Hardcoded API Key for local testing (or use os.getenv in production)
PINECONE_API_KEY = "pcsk_4L2SWH_FupPpwpwUrMQomv4YQsrpfLModrrCueDQ6ngiHqCQh7DgpvcetFEGjoHnYbZAkL"
INDEX_NAME = "living-archive"

# 2. Initialize local embedder (384-dim) & Pinecone
print("Loading local embedding model for API...")
embedder = SentenceTransformer("all-MiniLM-L6-v2")

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

@app.get("/")
def root():
    return {"status": "online", "system": "Living Archive Engine"}

@app.get("/search")
def search_archive(q: str = Query(..., description="Query string"), top_k: int = 5):
    # Vectorize search query locally
    query_vector = embedder.encode(q).tolist()
    
    # Perform vector search on Pinecone
    results = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True
    )
    
    matches = []
    for match in results.get("matches", []):
        matches.append({
            "id": match["id"],
            "score": round(match["score"], 4),
            "title": match["metadata"].get("title", ""),
            "text": match["metadata"].get("text", ""),
            "tier": match["metadata"].get("tier", "T1")
        })
        
    return {"query": q, "results": matches}

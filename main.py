import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pinecone import Pinecone
from groq import Groq

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "living-archive")

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

class QueryRequest(BaseModel):
    query: str

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Living Archive Backend Running"}

@app.post("/api/query")
async def query_archive(request: QueryRequest):
    try:
        # Embed via Pinecone hosted inference (0 local RAM usage)
        embeddings = pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[request.query],
            parameters={"input_type": "query"}
        )
        query_vector = embeddings.data[0].values

        search_response = index.query(
            vector=query_vector,
            top_k=5,
            include_metadata=True
        )

        matches = search_response.get("matches", [])
        retrieved_texts = []
        sources = []

        for match in matches:
            metadata = match.get("metadata", {})
            text = metadata.get("text") or metadata.get("content", "")
            title = metadata.get("title", "Untitled Document")
            if text:
                retrieved_texts.append(f"Source ({title}): {text}")
                sources.append({"title": title, "score": match.get("score")})

        if groq_client and retrieved_texts:
            context_block = "\n\n".join(retrieved_texts)
            system_prompt = (
                "You are the authoritative sensemaking guide for the Living Archive. "
                "Answer the user's inquiry strictly using the provided canonical context. "
                "Maintain a serious, professional, and authoritative tone suitable for thought leaders."
            )
            user_prompt = f"Context from Living Archive:\n{context_block}\n\nUser Question: {request.query}"

            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            synthesis = completion.choices[0].message.content
        else:
            synthesis = "\n\n".join(retrieved_texts) if retrieved_texts else "No direct matches found in the archive."

        return {
            "answer": synthesis,
            "sources": sources
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

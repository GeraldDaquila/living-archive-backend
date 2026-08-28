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

# Initialize Gemini Client with 120-Second Timeout (120,000 ms)
ai_client = None
if GEMINI_API_KEY:
    try:
        ai_client = genai.Client(
            api_key=GEMINI_API_KEY,
            http_options=types.HttpOptions(timeout=120000)
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
    """Fetch embeddings using gemini-embedding-001."""
    if not ai_client:
        return None
    try:
        response = ai_client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
        )
        if hasattr(response, 'embedding') and response.embedding:
            return response.embedding.values
    except Exception as e:
        print(f"Embedding notice (skipping vector lookup): {e}")
    return None

def generate_text(prompt: str):
    """Generate curated guidance using gemini-3.6-flash."""
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

    # Outer Courtyard EQ & Sensemaking Prompt
    prompt = (
        "You are the Navigation and Sensemaking Guide for the Living Archive outer courtyard interface.\n"
        "Your role is to deeply receive the visitor's question, mirror what they are holding, and uncover the unspoken context or pressure sitting beneath their words.\n\n"
        "EMPATHIC & SENSEMAKING GUIDELINES:\n"
        "1. MIRROR & DECODE BENEATH THE SURFACE: In the very first paragraph, directly reflect their inquiry and articulate the deeper dynamic or tension beneath it (e.g., the quiet exhaustion of carrying responsibility, the tension between expectations and real agency, or the burden of fix-it culture). Do NOT label this paragraph with section headers. Speak directly, warmly, and with deep insight.\n"
        "2. NO ACADEMIC JARGON: Avoid dry academic terms (e.g., 'somatic', 'telemetry', 'coherence', 'resonance', 'frequency', 'corpus', 'oversoul', 'ecologies of capacity'). Write with authentic human clarity, warmth, and depth.\n"
        "3. HIGH EQ PATHWAYS: Introduce recommended resources not as sterile lists, but as compassionate, insightful doorways that invite self-reflection and restore agency.\n"
        "4. HYBRID SYNTHESIS: Ground 70% of your guidance in the Archive reference context provided, while using 30% natural sensemaking to ensure the response meets the human right where they are.\n\n"
        "OUTPUT FORMAT (Use clean Markdown):\n\n"
        "[Paragraph 1: Warm, deeply intuitive mirroring of their question and the unspoken dynamic/question underneath it. No header text.]\n\n"
        "**Start Here**\n"
        "• [Essay / Resource Title] — A warm, insightful 1-2 sentence orientation that directly meets their current state and helps them catch their breath or reframe their situation.\n\n"
        "**Complementary Pathways**\n"
        "• [Resource Title 1] — 1 sentence inviting a practical perspective shift or psychological relief.\n"
        "• [Resource Title 2] — 1 sentence showing a way to recover personal sovereignty, boundaries, or clarity.\n\n"
        "[Paragraph 2: An empowering, grounding closing paragraph (2-3 sentences) that restores agency, reassuring them without being dismissive or cliché. No header text.]\n\n"
        f"Archive Reference Context:\n{context_str}\n\n"
        f"Visitor Query: {query_text}"
    )

    try:
        answer = generate_text(prompt)
        return {"response": answer}
    except Exception as err:
        print(f"Generation error: {err}")
        raise HTTPException(status_code=500, detail=str(err))

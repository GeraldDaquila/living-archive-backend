import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pinecone import Pinecone
from groq import Groq

app = FastAPI(title="Living Archive USE Engine")

# 1. CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "living-archive")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PREFERRED_MODEL = os.getenv("GROQ_MODEL")

pc = None
index = None
if PINECONE_API_KEY:
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX_NAME)
    except Exception as e:
        print(f"Pinecone Init Error: {e}")

groq_client = None
if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"Groq Init Error: {e}")

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str

def get_candidate_models() -> list[str]:
    candidates = []
    if PREFERRED_MODEL:
        candidates.append(PREFERRED_MODEL)

    if groq_client:
        try:
            models_page = groq_client.models.list()
            available = [m.id for m in models_page.data if getattr(m, 'active', True)]
            for m_id in available:
                if "llama-3.3" in m_id or "70b" in m_id or "versatile" in m_id:
                    if m_id not in candidates:
                        candidates.append(m_id)
            for m_id in available:
                if m_id not in candidates:
                    candidates.append(m_id)
        except Exception as e:
            print(f"Model Fetch Notice: {e}")

    for fb in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
        if fb not in candidates:
            candidates.append(fb)

    return candidates

def fetch_canonical_context(query: str, top_k: int = 5) -> str:
    """
    Embeds user query via Pinecone Inference and retrieves 
    ONLY verified canonical excerpts, exact titles, and live URLs.
    """
    if not index or not pc:
        return ""

    try:
        embeddings = pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[query],
            parameters={"input_type": "query"}
        )
        query_vector = embeddings[0].values

        query_response = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True
        )

        context_blocks = []
        for match in query_response.get("matches", []):
            meta = match.get("metadata", {})
            title = meta.get("title", "").strip()
            url = meta.get("url", "").strip()
            text = meta.get("text", meta.get("chunk_text", "")).strip()

            if title and url:
                context_blocks.append(f"CANONICAL TITLE: {title}\nEXACT URL: {url}\nEXCERPT: {text}\n")

        return "\n---\n".join(context_blocks)
    except Exception as e:
        print(f"Canonical Context Retrieval Notice: {e}")
        return ""

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Living Archive USE Sensemaking Engine Online"}

@app.post("/")
@app.post("/api/query", response_model=QueryResponse)
async def query_archive(request: QueryRequest):
    user_query = request.query.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    if not GROQ_API_KEY or not groq_client:
        return QueryResponse(response="**Configuration Notice:** Intelligence client uninitialized.")

    # 1. Retrieve Verified Canonical Context & URLs
    canonical_context = fetch_canonical_context(user_query)

    # 2. Sensemaking Navigator System Prompt
    system_prompt = (
        "You are USE (Universal Search & Entrance Engine), the sensemaking navigator and orienting guide for Life.Understood. / The Living Archive.\n\n"
        "CONSTITUTIONAL MANDATES:\n"
        "1. NO COSMOLOGICAL HALLUCINATION: Do not infer or construct an institutional worldview, political stance, or identity from general internet knowledge or semantic associations. Do not automatically frame neutral queries through 'colonial extraction', 'erasure of the Global South', 'restorative justice', or 'civic open knowledge' unless the query or retrieved canonical sources explicitly establish their relevance.\n"
        "2. DISTINGUISH IDENTITY FROM CONTENT: The archive may contain essays on specific topics (e.g., economics, systems, healing, colonialism), but those topics are NOT automatically the definition of the archive itself.\n"
        "3. EPISTEMIC HUMILITY: Treat your understanding of the user's underlying state as a tentative mirror, not a dogmatic diagnosis. Use open, respectful language (e.g., 'It may be that you are trying to...', 'If you are looking to get your bearings...').\n"
        "4. HARD RESOURCE CONSTRAINT: You may ONLY cite, reference, or link resources that exist in the CANONICAL CONTEXT provided below. NEVER synthesize, invent, rename, or extrapolate titles or URLs. If no canonical link exists for a step, offer a conceptual direction without inventing a fake link.\n"
        "5. NO WEBSITE INSTRUCTIONS: The user is ALREADY inside geralddaquila.com. Never tell them to 'visit the site' or 'navigate to geralddaquila.com'.\n"
        "6. CLEAR SENSEMAKING TONE: Avoid high-handed poetic personas ('priest at the threshold', 'deeper into the weave') and technical feature tables. Speak warmly, clearly, and purposefully as a perceptive guide.\n\n"
        "OPERATIONAL RESPONSE SEQUENCE:\n"
        "1. Tentative Mirror: Reflect what may be underneath the user's question with epistemic humility.\n"
        "2. Grounded Orientation: Offer a clear, grounded framing of how this topic or inquiry sits within the Archive.\n"
        "3. Three Movement Horizons (Offer up to 3 distinct ways forward):\n"
        "   - Immediate Horizon: Getting bearings / Start here.\n"
        "   - Medium-Term Horizon: Exploring a specific idea, framework, or essay.\n"
        "   - Developmental Horizon: Working with a deeper question or guided pathway.\n"
        "   * Ground each horizon in actual canonical links formatted strictly as: [Exact Article Title](Exact_URL)."
    )

    user_payload = (
        f"USER INQUIRY: {user_query}\n\n"
        f"CANONICAL RETRIEVED CONTEXT & METADATA:\n{canonical_context if canonical_context else 'No direct vector matches found in canonical index. Respond with epistemic humility and offer conceptual directions without fabricating fake titles or URLs.'}"
    )

    models_to_try = get_candidate_models()
    last_error = None

    for model_name in models_to_try:
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_payload}
                ],
                model=model_name,
                temperature=0.3,
                max_tokens=1200,
            )
            ai_response = chat_completion.choices[0].message.content
            return QueryResponse(response=ai_response)
        except Exception as err:
            print(f"Model Candidate '{model_name}' Failure: {err}")
            last_error = err

    err_msg = str(last_error) if last_error else "All candidate models failed."
    return QueryResponse(response=f"**API Exception Encountered:** {err_msg}")

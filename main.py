import os
import re
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pinecone import Pinecone
from groq import Groq
from fastembed import TextEmbedding

# ------------------------------------------------------------------
# 1. APPLICATION & SETUP
# ------------------------------------------------------------------
app = FastAPI(title="Living Archive USE Engine")

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

# Initialize local BAAI/bge-small-en-v1.5 embedding model to match index space
embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

def generate_local_embedding(text: str) -> list[float]:
    """Generates 384-dimensional embeddings matching the exact BAAI/bge-small-en-v1.5 corpus space."""
    embeddings = list(embedding_model.embed([text]))
    return embeddings[0].tolist()

def clean_title(raw_title: str) -> str:
    """Removes trailing chunk index numbers, emojis, and encoding artifacts from document titles."""
    clean = re.sub(r'[^\x00-\x7F]+', '', raw_title)
    clean = re.sub(r'\s+\d+$', '', clean).strip()
    return clean if clean else raw_title.strip()

def generate_canonical_url(clean_title_str: str) -> str:
    """Converts clean title into canonical website URL slug structure."""
    slug = clean_title_str.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug).strip('-')
    return f"https://geralddaquila.com/{slug}/"

def clean_excerpt(text: str) -> str:
    """Removes raw WordPress block comments and HTML tags from vector excerpts."""
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str

# ------------------------------------------------------------------
# 2. FROZEN PRODUCTION ENGINE (ACTIVE ON / AND /api/query)
# ------------------------------------------------------------------
def get_candidate_models() -> list[str]:
    candidates = []
    if PREFERRED_MODEL:
        candidates.append(PREFERRED_MODEL)

    default_chat_models = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768"
    ]

    if groq_client:
        try:
            models_page = groq_client.models.list()
            available = [m.id for m in models_page.data if getattr(m, 'active', True)]
            
            excluded_keywords = ["guard", "whisper", "orpheus", "vision", "safetensors"]
            
            for m_id in available:
                m_lower = m_id.lower()
                if not any(ex in m_lower for ex in excluded_keywords):
                    if m_id not in candidates:
                        candidates.append(m_id)
        except Exception as e:
            print(f"Model Fetch Notice: {e}")

    for fb in default_chat_models:
        if fb not in candidates:
            candidates.append(fb)

    return candidates

def fetch_canonical_context(query: str, top_k: int = 3) -> str:
    if not index or not pc:
        return ""

    try:
        query_vector = generate_local_embedding(query)

        query_response = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True
        )

        context_blocks = []
        for match in query_response.get("matches", []):
            meta = match.get("metadata", {})
            raw_title = meta.get("title", "").strip()
            raw_text = meta.get("text", meta.get("chunk_text", "")).strip()

            if raw_title:
                sanitized_title = clean_title(raw_title)
                canonical_url = generate_canonical_url(sanitized_title)
                
                sanitized_excerpt = clean_excerpt(raw_text)
                if len(sanitized_excerpt) > 600:
                    sanitized_excerpt = sanitized_excerpt[:600] + "..."

                context_blocks.append(
                    f"CANONICAL TITLE: {sanitized_title}\n"
                    f"EXACT CANONICAL URL: {canonical_url}\n"
                    f"EXCERPT: {sanitized_excerpt}\n"
                )

        return "\n---\n".join(context_blocks)
    except Exception as e:
        print(f"Canonical Context Retrieval Notice: {e}")
        return ""

@app.get("/")
@app.head("/")
def read_root():
    return {"status": "ok", "message": "Living Archive USE Engine Online"}

@app.post("/")
@app.post("/api/query", response_model=QueryResponse)
async def query_archive(request: QueryRequest):
    user_query = request.query.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    if not GROQ_API_KEY or not groq_client:
        return QueryResponse(response="**Configuration Notice:** Intelligence client uninitialized.")

    canonical_context = fetch_canonical_context(user_query)

    system_prompt = (
        "You are USE (Universal Search & Entrance Engine), the sensemaking guide for Life.Understood. / The Living Archive.\n\n"
        "CONSTITUTIONAL MANDATES:\n"
        "1. DIRECT IDENTITY ANSWER FIRST: When asked 'What is the Living Archive?', your very first paragraph MUST directly answer the question in plain, ordinary human language. State clearly:\n"
        "   - What it is (a growing body of work exploring how we live, build, and make sense of human experience).\n"
        "   - What it is for (to provide grounded clarity and orient readers toward deeper inquiry).\n"
        "   - How it differs from a conventional library, blog, or information repository (it is not a static database of facts or a stream of temporary posts, but an interconnected, evolving inquiry).\n"
        "   - Only AFTER establishing this identity, briefly explain its method of inquiry.\n"
        "2. NO PREMATURE TERMINOLOGY OR NAVIGATION: Do NOT lead with terms like 'living constitutional body of work' or 'disciplined multi-modal inquiry' unless immediately explained in simple terms. Do NOT turn the opening into a navigation directory; navigation comes AFTER the direct answer.\n"
        "3. NO COSMOLOGICAL HALLUCINATION: Do not infer or construct an institutional worldview or political stance from general internet knowledge unless retrieved canonical sources explicitly establish relevance.\n"
        "4. HARD RESOURCE CONSTRAINT: You may ONLY cite, reference, or link resources that exist in the CANONICAL CONTEXT provided below. NEVER synthesize or invent titles or URLs. Format hyperlinks using EXACT CANONICAL URL provided.\n"
        "5. NO WEBSITE INSTRUCTIONS: The user is ALREADY inside geralddaquila.com. Never tell them to 'visit the site' or 'navigate to geralddaquila.com'.\n"
        "6. CLEAR SENSEMAKING TONE: Speak warmly, clearly, and purposefully as a perceptive guide.\n\n"
        "OPERATIONAL RESPONSE SEQUENCE:\n"
        "1. Direct Identity Answer: Clear explanation of what the archive is, what it is for, and how it differs from a blog/library.\n"
        "2. Method of Inquiry: Brief explanation of how it operates.\n"
        "3. Grounded Orientation & Next Movement: Offer relevant next steps grounded strictly in canonical links formatted as: [Exact Article Title](EXACT_CANONICAL_URL)."
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


# ------------------------------------------------------------------
# 3. ISOLATED DIAGNOSTIC ROUTER (ACTIVE ON /api/diagnostic)
# ------------------------------------------------------------------
diagnostic_router = APIRouter(prefix="/api", tags=["Diagnostic"])

@diagnostic_router.post("/diagnostic")
async def run_diagnostic(request: QueryRequest):
    """
    USE TEST 001 Diagnostic Endpoint.
    Exposes cleaned titles, derived canonical URLs, scrubbed excerpts, and raw metadata.
    """
    user_query = request.query.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    embedding_model_used = "BAAI/bge-small-en-v1.5 (Local FastEmbed)"
    processed_matches = []
    index_dimension = "UNKNOWN"

    if index and pc:
        try:
            stats = index.describe_index_stats()
            index_dimension = stats.get("dimension", "UNKNOWN")
        except Exception as e:
            index_dimension = f"Error fetching stats: {str(e)}"

        try:
            query_vector = generate_local_embedding(user_query)

            query_response = index.query(
                vector=query_vector,
                top_k=3,
                include_metadata=True
            )

            for idx, match in enumerate(query_response.get("matches", [])):
                meta = match.get("metadata", {})
                raw_title = meta.get("title", "NO_TITLE_METADATA")
                raw_text = meta.get("text", meta.get("chunk_text", ""))

                clean_t = clean_title(raw_title)
                canonical_url = generate_canonical_url(clean_t)
                
                clean_exp = clean_excerpt(raw_text)
                if len(clean_exp) > 300:
                    clean_exp = clean_exp[:300] + "..."

                processed_matches.append({
                    "match_rank": idx + 1,
                    "score": match.get("score"),
                    "raw_title": raw_title,
                    "sanitized_title": clean_t,
                    "derived_canonical_url": canonical_url,
                    "scrubbed_excerpt_sample": clean_exp
                })
        except Exception as e:
            processed_matches.append({"error": f"Pinecone query exception: {str(e)}"})

    active_models = get_candidate_models()
    selected_model = active_models[0] if active_models else "UNKNOWN"

    return {
        "diagnostic_test": "USE TEST 001",
        "query": user_query,
        "configurations": {
            "query_embedding_model": embedding_model_used,
            "pinecone_index_dimension": index_dimension,
            "target_index_name": PINECONE_INDEX_NAME,
            "active_groq_model": selected_model,
            "all_candidate_models": active_models
        },
        "retrieved_matches_count": len(processed_matches),
        "processed_matches": processed_matches
    }

app.include_router(diagnostic_router)
